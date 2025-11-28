# Yahoo DCF Valuation Pipeline

This project implements a data pipeline to automate Discounted Cash Flow (DCF) valuation for various stock tickers using data from Yahoo Finance.

## Overview

The pipeline follows a Medallion Architecture (Bronze -> Silver -> Gold) to transform raw financial data into actionable valuation forecasts.

### Pipeline Stages

1.  **Bronze Layer (Ingestion)**:
    *   Fetches raw financial statements (Income Statement, Balance Sheet, Cash Flow) from Yahoo Finance using `yfinance`.
    *   Saves raw data as Parquet files in `data/bronze`.

2.  **Silver Layer (Processing)**:
    *   Cleans, standardizes, and aggregates the raw data.
    *   Calculates derived metrics and prepares the data for forecasting.
    *   Saves processed data in `data/silver`.

3.  **Gold Layer (Forecasting)**:
    *   Forecasts future financial performance (Revenue, Expenses, Assets, Liabilities, Cash Flows) based on historical trends and assumptions.
    *   Performs DCF valuation logic.
    *   Saves final forecasts in `data/gold`.

## Project Structure

```
.
├── data/               # Data storage (ignored by git)
│   ├── bronze/         # Raw data
│   ├── silver/         # Processed data
│   └── gold/           # Forecasted data
├── src/                # Source code
│   ├── ingestion.py    # Data fetching logic
│   ├── processing.py   # Data cleaning and transformation
│   └── forecasting.py  # Forecasting and valuation logic
├── main.py             # Entry point to run the full pipeline
├── requirements.txt    # Python dependencies
└── README.md           # Project documentation
```

## Setup & Usage

1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Run the Pipeline**:
    ```bash
    python main.py
    ```
    This will execute all stages of the pipeline for the configured tickers (default: GOOG, SOPH, PYPL, NOV, AMZN, NVDA, TGT).

## Configuration

*   **Tickers**: You can modify the list of tickers in `main.py` to analyze different companies.
