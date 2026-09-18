import pandas as pd
import numpy as np


def detect_date_columns(df):
    df = df.copy()
    date_columns = []

    for column in df.columns:
        column_name = str(column).lower()

        if not any(
            keyword in column_name
            for keyword in ["date", "time", "timestamp"]
        ):
            continue

        converted = pd.to_datetime(
            df[column],
            errors="coerce"
        )

        valid_ratio = converted.notna().mean()

        if valid_ratio >= 0.8:
            df[column] = converted
            date_columns.append(column)

    return df, date_columns


def detect_numeric_columns(df):
    return df.select_dtypes(
        include=np.number
    ).columns.tolist()


def detect_categorical_columns(df):
    return df.select_dtypes(
        include=["object", "category", "string"]
    ).columns.tolist()


def analyze_missing_values(df):
    missing = df.isna().sum()
    missing = missing[missing > 0].sort_values(
        ascending=False
    )
    return missing


def analyze_duplicates(df):
    return df.duplicated().sum()


def detect_outliers(df, numeric_columns):
    outlier_summary = {}

    for column in numeric_columns:

        series = df[column].dropna()

        if len(series) < 5:
            continue

        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        iqr = q3 - q1

        if iqr == 0:
            continue

        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr

        outliers = df[
            (df[column] < lower_bound)
            |
            (df[column] > upper_bound)
        ]

        if len(outliers) > 0:
            outlier_summary[column] = {
                "count": int(len(outliers)),
                "lower_bound": float(lower_bound),
                "upper_bound": float(upper_bound)
            }

    return outlier_summary


def analyze_categories(
    df,
    categorical_columns
):
    category_summary = {}

    for column in categorical_columns:

        values = (
            df[column]
            .dropna()
            .astype(str)
            .str.strip()
        )

        category_summary[column] = {
            "unique_values": int(
                values.nunique()
            ),
            "sample_values": (
                values.unique()[:10].tolist()
            )
        }

    return category_summary


def run_data_quality_check(df):

    report = {}

    report["rows"] = len(df)

    report["columns"] = len(df.columns)

    report["missing_values"] = (
        analyze_missing_values(df)
    )

    report["duplicate_rows"] = (
        analyze_duplicates(df)
    )

    df, date_columns = (
        detect_date_columns(df)
    )

    report["date_columns"] = date_columns

    numeric_columns = (
        detect_numeric_columns(df)
    )

    report["numeric_columns"] = (
        numeric_columns
    )

    categorical_columns = (
        detect_categorical_columns(df)
    )

    report["categorical_columns"] = (
        categorical_columns
    )

    report["outliers"] = (
        detect_outliers(
            df,
            numeric_columns
        )
    )

    report["category_summary"] = (
        analyze_categories(
            df,
            categorical_columns
        )
    )

    return df, report


def preprocess_data(df):

    df = df.copy()

    # Remove completely empty rows
    df = df.dropna(
        how="all"
    )

    # Remove exact duplicate rows
    df = df.drop_duplicates()

    # Strip whitespace while preserving NULLs
    text_columns = df.select_dtypes(
        include=[
            "object",
            "category",
            "string"
        ]
    ).columns

    for column in text_columns:

        df[column] = (
            df[column]
            .where(
                df[column].isna(),
                df[column].astype(str).str.strip()
            )
        )

    # Detect and convert dates
    df, date_columns = (
        detect_date_columns(df)
    )

    return df, date_columns


# ============================================================
# BUILD AI DATA PROFILE
# ============================================================

def build_data_profile(
    df,
    quality_report
):
    """
    Build a structured summary of the preprocessed
    dataset for the AI agents.

    IMPORTANT:
    This function does NOT modify the dataset.
    """

    profile = {}

    profile["dataset"] = {
        "rows": int(len(df)),
        "columns": int(len(df.columns))
    }

    # --------------------------------------------------------
    # Column information
    # --------------------------------------------------------

    columns = []

    for column in df.columns:

        column_info = {
            "name": str(column),
            "dtype": str(df[column].dtype),
            "missing_count": int(
                df[column].isna().sum()
            ),
            "missing_percentage": round(
                float(
                    df[column].isna().mean() * 100
                ),
                2
            ),
            "unique_values": int(
                df[column].nunique()
            )
        }

        columns.append(
            column_info
        )

    profile["columns"] = columns

    # --------------------------------------------------------
    # Data types
    # --------------------------------------------------------

    profile["numeric_columns"] = (
        quality_report.get(
            "numeric_columns",
            []
        )
    )

    profile["categorical_columns"] = (
        quality_report.get(
            "categorical_columns",
            []
        )
    )

    profile["date_columns"] = (
        quality_report.get(
            "date_columns",
            []
        )
    )

    # --------------------------------------------------------
    # Missing values
    # --------------------------------------------------------

    missing_values = (
        quality_report.get(
            "missing_values"
        )
    )

    profile["missing_values"] = {}

    if missing_values is not None:

        for column, count in (
            missing_values.items()
        ):

            profile["missing_values"][
                str(column)
            ] = {
                "count": int(count),
                "percentage": round(
                    float(
                        count / len(df) * 100
                    ),
                    2
                )
            }

    # --------------------------------------------------------
    # Duplicate rows
    # --------------------------------------------------------

    profile["duplicate_rows"] = int(
        quality_report.get(
            "duplicate_rows",
            0
        )
    )

    # --------------------------------------------------------
    # Outliers
    # --------------------------------------------------------

    profile["potential_outliers"] = (
        quality_report.get(
            "outliers",
            {}
        )
    )

    # --------------------------------------------------------
    # Categories
    # --------------------------------------------------------

    profile["categories"] = (
        quality_report.get(
            "category_summary",
            {}
        )
    )

    # --------------------------------------------------------
    # Numeric statistics
    # --------------------------------------------------------

    numeric_columns = (
        quality_report.get(
            "numeric_columns",
            []
        )
    )

    numeric_statistics = {}

    if numeric_columns:

        summary = (
            df[numeric_columns]
            .describe()
            .T
        )

        for column in summary.index:

            numeric_statistics[
                str(column)
            ] = {
                "min": float(
                    summary.loc[
                        column,
                        "min"
                    ]
                ),
                "max": float(
                    summary.loc[
                        column,
                        "max"
                    ]
                ),
                "mean": float(
                    summary.loc[
                        column,
                        "mean"
                    ]
                ),
                "median": float(
                    df[column].median()
                )
            }

    profile["numeric_statistics"] = (
        numeric_statistics
    )

    return profile