from pathlib import Path

import pandas as pd
from pytest import fixture


@fixture(scope="session")
def search_csv() -> Path:
    return Path(__file__).parent / "four_rivers_search_test.csv"


@fixture(scope="session")
def search_df(search_csv) -> pd.DataFrame:
    return pd.read_csv(search_csv)
