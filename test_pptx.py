import pandas as pd
from dateutil import parser
from pathlib import Path

def safe_parse(x):
    try:
        return parser.parse(str(x), fuzzy=True)
    except Exception:
        return pd.NaT

def clean_file(input_file, output_file):
    encodings = ['utf-8', 'utf-8-sig', 'latin1', 'cp1252']
    df = None
    for enc in encodings:
        try:
            print(f"🔍 Trying to read {input_file} with encoding: {enc}")
            df = pd.read_csv(input_file, encoding=enc, dtype=str, low_memory=False)
            print(f"✅ Loaded {len(df)} rows with {enc}")
            break
        except Exception as e:
            print(f"❌ Failed with {enc}: {e}")
    
    if df is None:
        print("❌ All encoding attempts failed.")
        return

    if 'Created' not in df.columns:
        print("❌ 'Created' column not found in data.")
        return

    df["Created_raw"] = df["Created"]
    df["Created"] = df["Created"].apply(safe_parse)
    failed_count = df["Created"].isna().sum()
    print(f"✅ Parsed 'Created' for {len(df)} rows. Failed: {failed_count}")

    Path(output_file).parent.mkdir(exist_ok=True, parents=True)
    df.to_csv(output_file, index=False)
    print(f"📁 Cleaned file saved to: {output_file}")

if __name__ == "__main__":
    input_path = "data/raw/unlabeled_tickets__Start_2025_05_01_End_2025_05_31.csv"  # Change this
    output_path = "data/raw/cleaned_tickets.csv"
    clean_file(input_path, output_path)
