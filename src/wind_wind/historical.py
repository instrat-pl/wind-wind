import pandas as pd
from wind_wind.paths import INPUT_DIR

def remove_duplicate_timestamp(df):
    # dup_mask = df.index.duplicated(keep=False)
    first_dup_mask = df.index.duplicated(keep='last')
    df.index = df.index.where(~first_dup_mask, df.index - pd.Timedelta(hours=1))
    return df


def get_capacities(df: pd.DataFrame, year=2025) -> pd.DataFrame:
    df.index = pd.to_datetime(df.index)
    hourly_index = pd.date_range(
        start=df.index.min(),
        end=df.index.max(),
        freq="h"
    )
    df = df.reindex(hourly_index)
    df.index.name = "snapshot"
    df = df["wind"].interpolate(method="linear")
    df = df[df.index.year == year]
    # df.rename(columns={"wind": "wind historical"}, inplace=True)
    # print(df)
    return df


def get_ARE_capacities(year: int = 2025) -> pd.DataFrame:
    filedir = INPUT_DIR / "historical_capacity"
    filename = "PL_ARE.csv"
    df = pd.read_csv(filedir / filename, index_col="date")
    # print(df)
    return get_capacities(df, year=year)


def get_generation(year: int = 2025) -> pd.DataFrame:
    filedir = INPUT_DIR / "historical_generation"
    filename = "PL_entsoe.csv"
    df = pd.read_csv(filedir / filename, index_col="index_utc")
    df.index = pd.to_datetime(df.index)#, format="%d.%m.%Y %H:%M")
    df = df[df.index.year == year]
    df = remove_duplicate_timestamp(df)
    df = df.drop(columns="index_tz_pl")
    df = df.resample('1h').mean()
    df = df.sort_index()
    df.index.name = "snapshot"
    df = df["wind"]
    # print(df)
    return df


