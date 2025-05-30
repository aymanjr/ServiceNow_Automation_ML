# src/processing/split_services_only.py

import pandas as pd
from pathlib import Path

class ServiceFileSplitter:
    def __init__(self, input_file: str, output_dir: str = "data/processed/by_service"):
        self.input_file = input_file
        self.output_dir = Path(output_dir)

    def split_by_service(self):
        df = pd.read_csv(self.input_file)

        if 'Predicted_Service_Tag' not in df.columns:
            raise ValueError("Missing 'Predicted_Service_Tag' column in the input file")

        self.output_dir.mkdir(parents=True, exist_ok=True)

        service_tags = df['Predicted_Service_Tag'].dropna().unique()
        for tag in service_tags:
            tag_safe = self._make_filename_safe(tag)
            df_filtered = df[df['Predicted_Service_Tag'] == tag]
            file_path = self.output_dir / f"{tag_safe}.csv"
            df_filtered.to_csv(file_path, index=False)
            print(f"✅ Saved {len(df_filtered)} rows to {file_path}")

    def _make_filename_safe(self, name: str) -> str:
        return "".join(c if c.isalnum() else "_" for c in str(name))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Split predictions.csv into service-specific files")
    parser.add_argument("--input", required=True, help="Path to predictions.csv file")
    parser.add_argument("--output", default="data/processed/by_service", help="Output directory path")
    args = parser.parse_args()

    splitter = ServiceFileSplitter(input_file=args.input, output_dir=args.output)
    splitter.split_by_service()
