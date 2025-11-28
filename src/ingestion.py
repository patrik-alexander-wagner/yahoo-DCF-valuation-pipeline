import yfinance as yf
import json
import os

def run_ingestion(tickers):
    print(f"Ingesting data for: {tickers}")
    for ticker in tickers:
        try:
            print(f"Fetching data for {ticker}...")
            stock = yf.Ticker(ticker)
            
            # Fetch data and save to Bronze
            balance_sheet = stock.balance_sheet.to_json() if not stock.balance_sheet.empty else "{}"
            income_statement = stock.financials.to_json() if not stock.financials.empty else "{}"
            cashflow = stock.cashflow.to_json() if not stock.cashflow.empty else "{}"
            
            base_path = f"data/bronze/{ticker}"
            os.makedirs(base_path, exist_ok=True)
            
            with open(f"{base_path}/balance_sheet.json", "w") as f:
                f.write(balance_sheet)
            with open(f"{base_path}/income_statement.json", "w") as f:
                f.write(income_statement)
            with open(f"{base_path}/cashflow.json", "w") as f:
                f.write(cashflow)
                
            print(f"Saved raw data for {ticker}")
            
        except Exception as e:
            print(f"Error ingesting {ticker}: {e}")
