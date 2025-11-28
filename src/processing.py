import pandas as pd
import os
import json

def run_processing():
    print("Processing data from Bronze to Silver...")
    
    bronze_dir = "data/bronze"
    silver_dir = "data/silver"
    
    if not os.path.exists(bronze_dir):
        print("Bronze directory not found.")
        return

    tickers = [d for d in os.listdir(bronze_dir) if os.path.isdir(os.path.join(bronze_dir, d))]
    
    for ticker in tickers:
        print(f"Processing {ticker}...")
        try:
            ticker_path = os.path.join(bronze_dir, ticker)
            
            # Read JSONs and convert to DataFrame
            dfs = []
            for file_name in ["balance_sheet.json", "income_statement.json", "cashflow.json"]:
                file_path = os.path.join(ticker_path, file_name)
                if os.path.exists(file_path):
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                    
                    if not data:
                        continue
                        
                    df = pd.DataFrame.from_dict(data, orient='index')
                    df.index = pd.to_datetime(df.index.astype(int), unit='ms')
                    dfs.append(df)
            
            if not dfs:
                print(f"No data found for {ticker}")
                continue
                
            # Merge, sort and save to Silver
            full_df = pd.concat(dfs, axis=1)
            full_df = full_df.sort_index()
            
            # Calculate aggregated "Other" accounts
            # These are needed for forecasting and cash flow calculations
            # Calculate aggregated "Other" accounts
            # These are needed for forecasting and cash flow calculations
            def get_safe(col):
                return full_df[col].fillna(0) if col in full_df.columns else 0

            if "Current Assets" in full_df.columns:
                full_df["OtherCurrentAssets_agg"] = (
                    get_safe("Current Assets") -
                    get_safe("Cash Cash Equivalents And Short Term Investments") -
                    get_safe("Accounts Receivable") -
                    get_safe("Inventory")
                )
            
            if "Total Non Current Assets" in full_df.columns:
                full_df["OtherNonCurrentAssets_agg"] = (
                    get_safe("Total Non Current Assets") -
                    get_safe("Net PPE") -
                    get_safe("Goodwill And Other Intangible Assets")
                )
            
            if "Current Liabilities" in full_df.columns:
                full_df["OtherCurrentLiabilities_agg"] = (
                    get_safe("Current Liabilities") -
                    get_safe("Accounts Payable")
                )
            
            if "Total Non Current Liabilities Net Minority Interest" in full_df.columns:
                full_df["OtherNonCurrentLiabilities_agg"] = (
                    get_safe("Total Non Current Liabilities Net Minority Interest") -
                    get_safe("Long Term Debt And Capital Lease Obligation")
                )
            
            output_path = os.path.join(silver_dir, f"{ticker}.parquet")
            full_df.to_parquet(output_path)
            print(f"Saved {ticker} to Silver layer")
            
        except Exception as e:
            print(f"Error processing {ticker}: {e}")

