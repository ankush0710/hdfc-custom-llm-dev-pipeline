import pandas as pd

def calculate_quality_metrics(df: pd.DataFrame, duplicate_rows: int=0):

    total_rows = len(df)

    total_columns = len(df.columns)

    missing_values = int(
        df.isna().sum().sum()
    )

    empty_rows = int(
        df.isna().all(axis=1).sum()
    )

    # calculate quality score
    total_cells = total_rows * total_columns

    if total_cells == 0:
        quality_score = 0.0

    else:
        missing_ratio = missing_values / total_cells
        quality_score = (100 * (1 - missing_ratio))
        quality_score = round(max(0.0, min(100.0, float(quality_score))), 2)

    return {
        "total_rows": total_rows,
        "total_columns": total_columns,
        "duplicate_rows": duplicate_rows,
        "missing_values": missing_values,
        "empty_rows": empty_rows,
        "quality_score": quality_score
    }






