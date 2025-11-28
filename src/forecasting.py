import pandas as pd
import os
import numpy as np

def calculate_cagr(series, periods=4):
    """
    Calculate Compound Annual Growth Rate (CAGR).
    Defaults to using the last 4 years (5 data points) if available.
    """
    if len(series) < 2:
        return 0.05
    
    start_idx = max(0, len(series) - 1 - periods)
    end_val = series.iloc[-1]
    start_val = series.iloc[start_idx]
    num_years = len(series) - 1 - start_idx
    
    if start_val == 0 or num_years == 0:
        return 0.05
        
    if start_val < 0: 
        return 0.05
        
    cagr = (end_val / start_val) ** (1 / num_years) - 1
    return cagr

def forecasting_income_statement(df, forecast_years=5):
    """
    Forecasts the Income Statement positions using 3-year historical averages and vectorization.
    """
    # Identify columns
    col_revenue = 'Total Revenue'
    col_cost_revenue = 'Cost Of Revenue'
    col_opex = 'Operating Expense'
    col_depreciation = 'Reconciled Depreciation' if 'Reconciled Depreciation' in df.columns else 'Depreciation And Amortization'
    col_interest = 'Net Interest Income'
    col_other_income = 'Other Income Expense'
    col_tax = 'Tax Provision'
    
    # Forecast Revenue using CAGR
    if col_revenue in df.columns:
        revenue_series = df[col_revenue].dropna()
        cagr = calculate_cagr(revenue_series)
    else:
        return pd.DataFrame()

    # Calculate Ratios (Average of last 3 years)
    recent_df = df.tail(3).copy()
    avg_ratios = {}
    expense_cols = [col_cost_revenue, col_opex, col_depreciation, col_interest, col_other_income]
    
    for col in expense_cols:
        if col in df.columns:
            total_expense = recent_df[col].sum()
            total_revenue = recent_df[col_revenue].sum()
            
            if total_revenue != 0:
                avg_ratios[col] = total_expense / total_revenue
            else:
                avg_ratios[col] = 0.0
        else:
            avg_ratios[col] = 0.0
            
    # Tax Rate relative to EBT
    col_ebt = "Pretax Income"
    col_tax_rate = "Tax Rate For Calcs"
    
    if col_tax_rate in df.columns:
        tax_rate = df[col_tax_rate].iloc[-1]
    else:
        tax_rate = 0.20

    # Generate Forecast
    last_date = df.index.max()
    future_dates = [last_date + pd.DateOffset(years=i) for i in range(1, forecast_years + 1)]
    
    forecast_df = pd.DataFrame(index=future_dates)
    
    # Forecast Revenue and Expenses
    last_revenue = df[col_revenue].iloc[-1]
    growth_factors = (1 + cagr) ** np.arange(1, forecast_years + 1)
    forecast_df[col_revenue] = last_revenue * growth_factors
    
    for col in expense_cols:
        if col in df.columns:
            forecast_df[col] = forecast_df[col_revenue] * avg_ratios[col]
        else:
            forecast_df[col] = 0.0
            
    # Calculate Derived Metrics and Net Income
    forecast_df['Gross Profit'] = forecast_df[col_revenue] - forecast_df[col_cost_revenue]
    forecast_df['EBIT'] = forecast_df['Gross Profit'] - forecast_df[col_opex]
    forecast_df['EBITDA'] = forecast_df['EBIT'] + forecast_df[col_depreciation]
    forecast_df['EBT'] = forecast_df['EBIT'] + forecast_df[col_interest] + forecast_df[col_other_income]
    
    forecast_df[col_tax] = forecast_df['EBT'] * tax_rate
    forecast_df['Net Income'] = forecast_df['EBT'] - forecast_df[col_tax]
    forecast_df[col_tax_rate] = tax_rate
    
    return forecast_df

def forecasting_balance_sheet(df, is_forecast_df):
    """
    Forecasts the Balance Sheet positions.
    Depends on the historical dataframe and the forecasted Income Statement.
    """
    if is_forecast_df.empty:
        return pd.DataFrame()

    # Identify columns
    col_revenue = 'Total Revenue'
    col_cost_revenue = 'Cost Of Revenue'
    col_net_income = 'Net Income'
    
    col_receivables = "Accounts Receivable"
    col_payables = "Accounts Payable"
    col_inventory = "Inventory"
    col_ppe = "Net PPE"
    col_fin_liab = "Long Term Debt And Capital Lease Obligation"
    col_intangible = "Goodwill And Other Intangible Assets"
    col_equity = "Total Equity Gross Minority Interest"
    col_cash = "Cash Cash Equivalents And Short Term Investments"
    col_current_assets = "Current Assets"
    col_non_current_assets = "Total Non Current Assets"
    col_current_liab = "Current Liabilities"
    col_non_current_liab = "Total Non Current Liabilities Net Minority Interest"
    
    col_other_current_assets = "OtherCurrentAssets_agg"
    col_other_non_current_assets = "OtherNonCurrentAssets_agg"
    col_other_current_liab = "OtherCurrentLiabilities_agg"
    col_other_non_current_liab = "OtherNonCurrentLiabilities_agg"

    last_date = df.index.max()
    last_row = df.loc[last_date]
    
    def get_last_val(col):
        return last_row.get(col, 0)

    last_revenue = get_last_val(col_revenue)
    last_cogs = get_last_val(col_cost_revenue)

    # Calculate Historical DIO, DPO, DSO
    val_inventory = get_last_val(col_inventory)
    val_payables = get_last_val(col_payables)
    val_receivables = get_last_val(col_receivables)
    
    dio_2024 = (val_inventory / last_cogs * 360) if last_cogs != 0 else 0
    dpo_2024 = (val_payables / last_cogs * 360) if last_cogs != 0 else 0
    dso_2024 = (val_receivables / last_revenue * 360) if last_revenue != 0 else 0
    
    # Calculate Ratios for other items (% of Sales)
    recent_df = df.tail(3).copy()
    sum_revenue = recent_df[col_revenue].sum()
    
    def get_sum(col):
        return recent_df[col].sum() if col in recent_df.columns else 0

    bs_items_sums = {
        col_ppe: get_sum(col_ppe),
        col_current_assets: get_sum(col_current_assets),
        col_non_current_assets: get_sum(col_non_current_assets),
        col_current_liab: get_sum(col_current_liab),
        col_non_current_liab: get_sum(col_non_current_liab),
        
        col_other_current_assets: get_sum(col_current_assets) - get_sum(col_cash) - get_sum(col_receivables) - get_sum(col_inventory),
        col_other_non_current_assets: get_sum(col_non_current_assets) - get_sum(col_ppe) - get_sum(col_intangible),
        col_other_current_liab: get_sum(col_current_liab) - get_sum(col_payables),
        col_other_non_current_liab: get_sum(col_non_current_liab) - get_sum(col_fin_liab)
    }

    bs_ratios = {k: v / sum_revenue if sum_revenue != 0 else 0 for k, v in bs_items_sums.items()}

    # Flat items and Equity Start
    fin_liab_flat = get_last_val(col_fin_liab)
    intangible_flat = get_last_val(col_intangible)
    running_equity = get_last_val(col_equity)
    
    forecast_rows = []
    
    for index, row in is_forecast_df.iterrows():
        next_revenue = row.get(col_revenue, 0)
        next_cogs = row.get(col_cost_revenue, 0)
        net_income = row.get(col_net_income, 0)
        
        row_data = {}
        
        # Working Capital (Days Method)
        row_data[col_receivables] = dso_2024 / 360 * next_revenue
        row_data[col_payables] = dpo_2024 / 360 * next_cogs
        row_data[col_inventory] = dio_2024 / 360 * next_cogs
        
        # Sales Driven Assets/Liabilities
        row_data[col_ppe] = next_revenue * bs_ratios[col_ppe]
        row_data[col_current_assets] = next_revenue * bs_ratios[col_current_assets]
        row_data[col_non_current_assets] = next_revenue * bs_ratios[col_non_current_assets]
        row_data[col_current_liab] = next_revenue * bs_ratios[col_current_liab]
        row_data[col_non_current_liab] = next_revenue * bs_ratios[col_non_current_liab]
        
        # Residuals / Aggregates Forecast
        row_data[col_other_current_assets] = next_revenue * bs_ratios[col_other_current_assets]
        row_data[col_other_non_current_assets] = next_revenue * bs_ratios[col_other_non_current_assets]
        row_data[col_other_current_liab] = next_revenue * bs_ratios[col_other_current_liab]
        row_data[col_other_non_current_liab] = next_revenue * bs_ratios[col_other_non_current_liab]
        
        # Flat Items
        row_data[col_fin_liab] = fin_liab_flat
        row_data[col_intangible] = intangible_flat
        
        # Equity Roll Forward
        running_equity = running_equity + net_income
        row_data[col_equity] = running_equity
        
        forecast_rows.append(pd.Series(row_data, name=index))
        
    return pd.DataFrame(forecast_rows)

def forecast_cashflow(df, is_forecast_df, bs_forecast_df):
    """
    Forecasts the Cash Flow Statement positions using user-specified formulas.
    """
    if is_forecast_df.empty or bs_forecast_df.empty:
        return pd.DataFrame()

    # Combine Historical and Forecast for easy delta calculation
    last_hist_date = df.index.max()
    historical_last_row = df.loc[[last_hist_date]]
    
    # We only need relevant columns for deltas
    relevant_cols = [
        "Inventory", "Accounts Receivable", "Accounts Payable", 
        "Net PPE", "Goodwill And Other Intangible Assets",
        "OtherCurrentAssets_agg", "OtherNonCurrentAssets_agg",
        "OtherCurrentLiabilities_agg", "OtherNonCurrentLiabilities_agg",
        "Long Term Debt And Capital Lease Obligation",
        "Total Equity Gross Minority Interest"
    ]
    
    # Ensure all columns exist in historical (fill 0 if not)
    for col in relevant_cols:
        if col not in historical_last_row.columns:
            historical_last_row[col] = 0.0
            
    # Combine BS forecast with last historical row to compute deltas
    bs_combined = pd.concat([historical_last_row, bs_forecast_df])
    
    # We need to compute values for each forecast year.
    # Since we need Y and Y-1, we can just shift the combined dataframe.
    bs_shifted = bs_combined.shift(1) # This gives Y-1 values at index Y
    
    # We only care about the forecast rows (excluding the first historical row)
    target_index = is_forecast_df.index
    
    # Initialize Cash Flow DataFrame
    cf_df = pd.DataFrame(index=target_index)
    
    # Calculate Income Statement derived metrics
    cf_df['Operating Taxes'] = is_forecast_df['EBIT'] * is_forecast_df['Tax Rate For Calcs']
    cf_df['NOPAT'] = is_forecast_df['EBIT'] - cf_df['Operating Taxes']
    
    depreciation = is_forecast_df['Reconciled Depreciation'] if 'Reconciled Depreciation' in is_forecast_df.columns else is_forecast_df.get('Depreciation And Amortization', 0)
    cf_df['Gross Cash Flow'] = cf_df['NOPAT'] + depreciation
    
    # Calculate Working Capital Investment
    def get_safe_delta(col):
        return bs_shifted.loc[target_index, col].fillna(0) - bs_combined.loc[target_index, col].fillna(0)

    delta_inventory = get_safe_delta("Inventory")
    delta_ar = get_safe_delta("Accounts Receivable")
    delta_ap = -get_safe_delta("Accounts Payable")
    
    cf_df['Investment in Working Capital'] = delta_inventory + delta_ar + delta_ap
    
    # Calculate Investment in Other Assets/Liabilities
    cf_df['Investment in Other Assets'] = ((bs_shifted.loc[target_index, "OtherCurrentAssets_agg"] + bs_shifted.loc[target_index, "OtherNonCurrentAssets_agg"]) - 
                                            (bs_combined.loc[target_index, "OtherCurrentAssets_agg"] + bs_combined.loc[target_index, "OtherNonCurrentAssets_agg"]))
    
    cf_df['Investment in Other Liabilities'] = -((bs_shifted.loc[target_index, "OtherCurrentLiabilities_agg"] + bs_shifted.loc[target_index, "OtherNonCurrentLiabilities_agg"]) - 
                                                 (bs_combined.loc[target_index, "OtherCurrentLiabilities_agg"] + bs_combined.loc[target_index, "OtherNonCurrentLiabilities_agg"]))
    
    # Calculate Capex and Other Investments
    cf_df['Capex'] = (bs_shifted.loc[target_index, "Net PPE"] - bs_combined.loc[target_index, "Net PPE"])
    cf_df['Other Investment'] = (bs_shifted.loc[target_index, "Goodwill And Other Intangible Assets"] - bs_combined.loc[target_index, "Goodwill And Other Intangible Assets"])
    
    # Calculate UFCF and Net Cash Flow
    cf_df['UFCF'] = cf_df['Gross Cash Flow'] + cf_df['Investment in Working Capital'] + cf_df['Investment in Other Assets'] + cf_df['Investment in Other Liabilities'] + cf_df['Capex'] + cf_df['Other Investment']
    
    interest_expenses = is_forecast_df['Net Interest Income']
    other_income = is_forecast_df['Other Income Expense']
    delta_taxes = cf_df['Operating Taxes'] - is_forecast_df['Tax Provision']
    delta_fin_liab = bs_combined.loc[target_index, "Long Term Debt And Capital Lease Obligation"] - bs_shifted.loc[target_index, "Long Term Debt And Capital Lease Obligation"]
    delta_equity = bs_combined.loc[target_index, "Total Equity Gross Minority Interest"] - bs_shifted.loc[target_index, "Total Equity Gross Minority Interest"] - is_forecast_df['Net Income']
    
    cf_df['Net Cash Flow'] = cf_df['UFCF'] + interest_expenses + other_income + delta_taxes + delta_fin_liab + delta_equity
    
    return cf_df

def forecast_cash(df, bs_forecast_df, cf_forecast_df):
    """
    Forecasts Cash positions using the formula: Cash Y = Cash Y-1 + Net Cash Flow
    """
    if bs_forecast_df.empty or cf_forecast_df.empty:
        return bs_forecast_df
    
    col_cash = "Cash Cash Equivalents And Short Term Investments"
    
    # Get starting cash from last historical year
    last_hist_date = df.index.max()
    last_cash = df.loc[last_hist_date, col_cash] if col_cash in df.columns else 0.0
    
    # Calculate cash for each forecast year
    running_cash = last_cash
    
    for index in bs_forecast_df.index:
        net_cash_flow = cf_forecast_df.loc[index, 'Net Cash Flow']
        running_cash = running_cash + net_cash_flow
        bs_forecast_df.loc[index, col_cash] = running_cash
    
    return bs_forecast_df

def check_balance_sheet(bs_forecast_df, ticker):
    """
    Checks if the balance sheet balances for every forecasted year.
    Asset = Liabilities + Equity
    """
    if bs_forecast_df.empty:
        return True
    
    all_balanced = True
    
    for index, row in bs_forecast_df.iterrows():
        # Calculate Assets
        assets = (
            row.get("Goodwill And Other Intangible Assets", 0) +
            row.get("Net PPE", 0) +
            row.get("OtherCurrentAssets_agg", 0) +
            row.get("OtherNonCurrentAssets_agg", 0) +
            row.get("Accounts Receivable", 0) +
            row.get("Inventory", 0) +
            row.get("Cash Cash Equivalents And Short Term Investments", 0)
        )
        
        # Calculate Liabilities
        liabilities = (
            row.get("Accounts Payable", 0) +
            row.get("OtherCurrentLiabilities_agg", 0) +
            row.get("OtherNonCurrentLiabilities_agg", 0) +
            row.get("Long Term Debt And Capital Lease Obligation", 0)
        )
        
        # Get Equity
        equity = row.get("Total Equity Gross Minority Interest", 0)
        
        # Check if balanced
        liab_plus_equity = liabilities + equity
        difference = abs(assets - liab_plus_equity)
        
        # Allow small rounding errors (tolerance of 0.01)
        if difference > 0.01:
            print(f"  WARNING [{ticker}] Year {index.year}: Balance sheet does NOT balance!")
            print(f"    Assets: {assets:,.2f}")
            print(f"    Liabilities + Equity: {liab_plus_equity:,.2f}")
            print(f"    Difference: {difference:,.2f}")
            all_balanced = False
        else:
            print(f"  ✓ [{ticker}] Year {index.year}: Balance sheet balances (Assets: {assets:,.2f})")
    
    return all_balanced

def run_forecasting():
    print("Forecasting data from Silver to Gold...")
    
    silver_dir = "data/silver"
    gold_dir = "data/gold"
    
    if not os.path.exists(silver_dir):
        print("Silver directory not found.")
        return
        
    if not os.path.exists(gold_dir):
        os.makedirs(gold_dir)

    files = [f for f in os.listdir(silver_dir) if f.endswith(".parquet")]
    
    for file_name in files:
        ticker = file_name.replace(".parquet", "")
        print(f"Forecasting {ticker}...")
        
        try:
            # Read Silver data
            df = pd.read_parquet(os.path.join(silver_dir, file_name))
            
            if df.empty:
                print(f"No data for {ticker}")
                continue
            
            df = df.sort_index()
            
            # Forecast Income Statement, Balance Sheet, and Cash Flow
            is_forecast = forecasting_income_statement(df)
            if is_forecast.empty:
                print(f"  Could not forecast IS for {ticker}")
                continue
                
            bs_forecast = forecasting_balance_sheet(df, is_forecast)
            cf_forecast = forecast_cashflow(df, is_forecast, bs_forecast)
            
            # Forecast Cash (updates bs_forecast in place)
            bs_forecast = forecast_cash(df, bs_forecast, cf_forecast)
            
            # Check if balance sheet balances
            print(f"  Checking balance sheet for {ticker}...")
            check_balance_sheet(bs_forecast, ticker)
            
            # Combine Forecasts and Historical
            forecast_df = pd.concat([is_forecast, bs_forecast, cf_forecast], axis=1)
            
            df['Type'] = 'Historical'
            forecast_df['Type'] = 'Forecast'
            
            combined_df = pd.concat([df, forecast_df])
            
            # Save to Gold
            output_path = os.path.join(gold_dir, f"{ticker}_forecast.parquet")
            combined_df.to_parquet(output_path)
            print(f"  Saved forecast for {ticker} to Gold layer")
            
        except Exception as e:
            print(f"Error forecasting {ticker}: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    run_forecasting()
