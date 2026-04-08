import pandas as pd
import numpy as np

def check_mape_threshold(actual, predicted, threshold=15.0):
    actual = np.array(actual)
    predicted = np.array(predicted)
    mape = np.mean(np.abs((actual - predicted) / (actual + 1e-10))) * 100
    status = "PASS" if mape <= threshold else "WARN"
    print(f"[{status}] MAPE: {mape:.2f}% (Threshold: {threshold}%)")
    return mape

def check_missing_date_gaps(df, date_col):
    df[date_col] = pd.to_datetime(df[date_col])
    all_months = pd.date_range(df[date_col].min(), df[date_col].max(), freq='MS')
    actual_months = df[date_col].dt.to_period('M').unique()
    missing = [str(m) for m in all_months.to_period('M') if m not in actual_months]
    if missing:
        print(f"[WARN] Missing date gaps detected: {missing}")
    else:
        print("[PASS] No missing date gaps found.")
    return missing

def check_zero_demand(df, demand_col):
    zero_count = (df[demand_col] == 0).sum()
    status = "WARN" if zero_count > 0 else "PASS"
    print(f"[{status}] Zero demand rows: {zero_count}")
    return zero_count

def check_negative_inventory(df, inventory_col):
    neg_count = (df[inventory_col] < 0).sum()
    status = "WARN" if neg_count > 0 else "PASS"
    print(f"[{status}] Negative inventory rows: {neg_count}")
    return neg_count

def run_all_checks(df, date_col, demand_col, inventory_col, actual=None, predicted=None):
    print("=" * 50)
    print("FORECASTING QUALITY CHECKS")
    print("=" * 50)
    check_missing_date_gaps(df, date_col)
    check_zero_demand(df, demand_col)
    check_negative_inventory(df, inventory_col)
    if actual is not None and predicted is not None:
        check_mape_threshold(actual, predicted)
    print("=" * 50)
    print("All checks complete.")

if __name__ == "__main__":
    df = pd.DataFrame({
        'order_date': pd.date_range('2023-01-01', periods=24, freq='MS'),
        'demand_units': [100, 120, 0, 90, 110, 130, 105, 95, 115, 125, 0, 100,
                        108, 122, 98, 112, 118, 135, 102, 97, 119, 128, 111, 104],
        'inventory_units': [50, 60, 40, -5, 55, 65, 48, 52, 58, 62, 45, 50,
                           53, 61, 44, 56, 59, 67, 49, 51, 57, 63, 46, 52]
    })
    actual = [100, 120, 90, 110, 130]
    predicted = [105, 115, 95, 108, 125]
    run_all_checks(df, 'order_date', 'demand_units', 'inventory_units', actual, predicted)