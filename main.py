import os
from src.ingestion import run_ingestion
from src.processing import run_processing
from src.forecasting import run_forecasting

TICKERS = ['GOOG', 'SOPH', 'PYPL', 'NOV', 'AMZN', 'NVDA', 'TGT']

def main():
    print("Starting Data Pipeline...")
    
    # Ensure directories exist
    os.makedirs('data/bronze', exist_ok=True)
    os.makedirs('data/silver', exist_ok=True)
    os.makedirs('data/gold', exist_ok=True)

    print("\n--- Bronze Layer: Ingestion ---")
    run_ingestion(TICKERS)

    print("\n--- Silver Layer: Processing ---")
    run_processing()

    print("\n--- Gold Layer: Forecasting ---")
    run_forecasting()

    print("\nPipeline Completed Successfully.")

if __name__ == "__main__":
    main()
