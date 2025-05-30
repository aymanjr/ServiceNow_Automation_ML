import pandas as pd
import numpy as np
import re
import joblib
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import argparse

class ServiceTagClassifier:
    def __init__(self):
        self.model = None
        self.features = [
            'Short description',
            'Assignment group',
            'Configuration item',
            'Business Unit',
            'Item'
        ]
        self.target = 'Service_Tag'
        self.model_path = Path('models/service_tag_model.pkl')
        
    def _clean_text(self, text):
        """Clean and standardize text data"""
        if pd.isna(text):
            return ""
        text = str(text).lower().strip()
        text = re.sub(r'[^\w\s-]', '', text)  # Remove special chars
        return text

    def _load_csv_with_fallback(self, filepath):
        """Load CSV with robust encoding handling"""
        import chardet
        # Try common encodings first
        encodings_to_try = ['utf-8', 'latin1', 'iso-8859-1', 'cp1252']
        
        for encoding in encodings_to_try:
            try:
                df = pd.read_csv(filepath, dtype=str, encoding=encoding, low_memory=False)
                print(f"Successfully read with {encoding} encoding")
                return df
            except UnicodeDecodeError:
                continue
        
        # If none of the common encodings worked, try chardet
        try:
            with open(filepath, 'rb') as f:
                rawdata = f.read(100000)  # Read more bytes for better detection
                result = chardet.detect(rawdata)
                encoding = result['encoding'] or 'latin1'
                print(f"Detected encoding: {encoding} (confidence: {result['confidence']})")
                return pd.read_csv(filepath, dtype=str, encoding=encoding, low_memory=False)
        except Exception as e:
            print(f"Failed to detect encoding: {e}")
            raise
        
    def preprocess_data(self, df):
        """Preprocess the input dataframe"""
        # Clean text features
        for col in self.features:
            if col in df.columns:
                df[col] = df[col].apply(self._clean_text)
        
        # Handle missing values
        for col in self.features:
            if col in df.columns:
                df[col] = df[col].fillna('missing')
        
        return df
    
    def train(self, data_path, test_size=0.2, save_model=True):
        """Train the classifier model"""
        try:
            df = self._load_csv_with_fallback(data_path)
        except Exception as e:
            print(f"Error loading data: {e}")
            return None
        
        df = self.preprocess_data(df)
        
        # Verify target column exists
        if self.target not in df.columns:
            print(f"Error: Target column '{self.target}' not found in data")
            return None
        
        # Remove 'IPR' service tags if present
        if 'IPR' in df[self.target].unique():
            df = df[df[self.target] != 'IPR']
        
        # Split data
        X = df[self.features]
        y = df[self.target]
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42
        )
        
        # Define preprocessing pipeline
        preprocessor = ColumnTransformer(
            transformers=[
                ('desc', TfidfVectorizer(
                    max_features=500,
                    ngram_range=(1, 2),
                    stop_words='english'),
                 'Short description'),
                ('cat', OneHotEncoder(
                    handle_unknown='ignore',
                    sparse_output=False),
                 ['Assignment group', 'Configuration item', 'Business Unit', 'Item'])
            ],
            remainder='drop'
        )
        
        # Create model pipeline
        self.model = Pipeline([
            ('preprocessor', preprocessor),
            ('classifier', RandomForestClassifier(
                n_estimators=200,
                class_weight='balanced',
                random_state=42,
                verbose=1
            ))
        ])
        
        # Train model
        print("Training model...")
        try:
            self.model.fit(X_train, y_train)
        except Exception as e:
            print(f"Error during training: {e}")
            return None
        
        # Evaluate
        print("\nModel evaluation:")
        y_pred = self.model.predict(X_test)
        print(classification_report(y_test, y_pred))
        
        # Save model
        if save_model:
            try:
                self.model_path.parent.mkdir(exist_ok=True)
                joblib.dump(self.model, self.model_path)
                print(f"\nModel saved to {self.model_path}")
            except Exception as e:
                print(f"Error saving model: {e}")
        
        return self.model
    
    def predict(self, new_data_path, output_path=None):
        """Predict service tags for new tickets"""
        # Load model if not already loaded
        if self.model is None:
            if not self.model_path.exists():
                raise FileNotFoundError(
                    f"Model not found at {self.model_path}. Please train first."
                )
            try:
                self.model = joblib.load(self.model_path)
            except Exception as e:
                print(f"Error loading model: {e}")
                return None
        
        # Load and preprocess new data
        try:
            new_data = self._load_csv_with_fallback(new_data_path)
        except Exception as e:
            print(f"Error loading new data: {e}")
            return None
        
        new_data = self.preprocess_data(new_data)
        
        # Verify all required columns exist
        missing_cols = [col for col in self.features if col not in new_data.columns]
        if missing_cols:
            print(f"Error: Missing required columns: {missing_cols}")
            return None
        
        # Predict service tags
        print("\nPredicting service tags...")
        try:
            X_new = new_data[self.features]
            new_data['Predicted_Service_Tag'] = self.model.predict(X_new)
        except Exception as e:
            print(f"Error during prediction: {e}")
            return None
        
        # Apply business rules
        self._apply_business_rules(new_data)
        
        # Save results
        if output_path:
            try:
                Path(output_path).parent.mkdir(exist_ok=True)
                new_data.to_csv(output_path, index=False, encoding='utf-8')
                print(f"Predictions saved to {output_path}")
            except Exception as e:
                print(f"Error saving predictions: {e}")
        
        return new_data
    
    def _apply_business_rules(self, df):
        """Apply specific business rules to predictions"""
        try:
            # Rule: Jumphost password reset -> SIP
            mask_jumphost = df['Short description'].str.contains('jumphost password reset', case=False, na=False)
            df.loc[mask_jumphost, 'Predicted_Service_Tag'] = 'SIP'
            
            # Rule: TEST tag only if 'test' in short description
            mask_test = df['Predicted_Service_Tag'] == 'TEST'
            test_desc_mask = df['Short description'].str.contains('test', case=False, na=False)
            # Set to TEST only if 'test' in description, else leave as original prediction
            df.loc[mask_test & ~test_desc_mask, 'Predicted_Service_Tag'] = df.loc[mask_test & ~test_desc_mask, 'Predicted_Service_Tag'].apply(lambda x: x if x != 'TEST' else 'missing')
            
            # Rule: Tickets containing 'IFS' anywhere -> IFS tag
            mask_ifs = (
                df['Short description'].str.contains('ifs', case=False, na=False) |
                df['Assignment group'].str.contains('ifs', case=False, na=False) |
                df['Configuration item'].str.contains('ifs', case=False, na=False) |
                df['Business Unit'].str.contains('ifs', case=False, na=False) |
                df['Item'].str.contains('ifs', case=False, na=False)
            )
            df.loc[mask_ifs, 'Predicted_Service_Tag'] = 'IFS'
            
            # Rule: Confluence related tickets -> CF
            mask_cf = (
                df['Short description'].str.contains('confluence', case=False, na=False) |
                df['Assignment group'].str.contains('confluence', case=False, na=False) |
                df['Configuration item'].str.contains('confluence', case=False, na=False) |
                df['Business Unit'].str.contains('confluence', case=False, na=False) |
                df['Item'].str.contains('confluence', case=False, na=False)
            )
            df.loc[mask_cf, 'Predicted_Service_Tag'] = 'CF'
            
            # Rule: MAVIM related tickets -> MVM
            mask_mvm = (
                df['Short description'].str.contains('mavim', case=False, na=False) |
                df['Assignment group'].str.contains('mavim', case=False, na=False) |
                df['Configuration item'].str.contains('mavim', case=False, na=False) |
                df['Business Unit'].str.contains('mavim', case=False, na=False) |
                df['Item'].str.contains('mavim', case=False, na=False)
            )
            df.loc[mask_mvm, 'Predicted_Service_Tag'] = 'MVM'
            
            # Rule: Assignment group containing 'Automation' -> AUTO
            mask_auto = df['Assignment group'].str.contains('automation', case=False, na=False)
            df.loc[mask_auto, 'Predicted_Service_Tag'] = 'AUTO'
            
            # Rule: Configuration item containing 'Mavim' -> MVM (already covered above, but keeping for clarity)
            mask_mvm_ci = df['Configuration item'].str.contains('mavim', case=False, na=False)
            df.loc[mask_mvm_ci, 'Predicted_Service_Tag'] = 'MVM'
            
        except Exception as e:
            print(f"Error applying business rules: {e}")
        
        return df

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Service Ticket Tag Classifier')
    parser.add_argument('--train', help='Path to labeled training data')
    parser.add_argument('--predict', help='Path to new unlabeled data')
    parser.add_argument('--output', help='Output path for predictions')
    parser.add_argument('--encoding', help='Force specific encoding (optional)')
    args = parser.parse_args()
    
    classifier = ServiceTagClassifier()
    
    if args.train:
        classifier.train(args.train)
    if args.predict:
        classifier.predict(args.predict, args.output)
    