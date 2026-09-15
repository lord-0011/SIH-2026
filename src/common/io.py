"""IO helpers for reading and writing pipeline data (interim, processed).

Ensures directory creation and supports parquet and csv.
"""

from pathlib import Path

import pandas as pd


def ensure_dir(path: Path | str) -> Path:
    """Ensure parent directory exists for a file or directory path."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def save_dataframe(df: pd.DataFrame, path: Path | str, **kwargs) -> Path:
    """Save dataframe to parquet or csv based on file extension."""
    target_path = ensure_dir(path)
    ext = target_path.suffix.lower()
    if ext == ".parquet":
        df.to_parquet(target_path, index=False, **kwargs)
    elif ext == ".csv":
        df.to_csv(target_path, index=False, **kwargs)
    else:
        raise ValueError(f"Unsupported format: {ext}. Use .parquet or .csv")
    return target_path


def load_dataframe(path: Path | str, **kwargs) -> pd.DataFrame:
    """Load dataframe from parquet or csv based on file extension."""
    src_path = Path(path)
    if not src_path.exists():
        raise FileNotFoundError(f"File not found: {src_path}")
    ext = src_path.suffix.lower()
    if ext == ".parquet":
        return pd.read_parquet(src_path, **kwargs)
    elif ext == ".csv":
        return pd.read_csv(src_path, **kwargs)
    else:
        raise ValueError(f"Unsupported format: {ext}. Use .parquet or .csv")
