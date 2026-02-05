import sqlite3
from typing import Iterable, List, Tuple

import pandas as pd


def load_reviews_json(path: str) -> pd.DataFrame:
    return pd.read_json(path, lines=True)


def normalize_ratings(df_raw: pd.DataFrame) -> pd.DataFrame:
    ratings_df = pd.json_normalize(df_raw["ratings"])
    ratings_df = ratings_df.rename(
        columns={
            "check_in_front_desk": "check_in_service",
            "business_service_(e_g_internet_access)": "business_service",
        }
    )
    ratings_df.columns = [f"{c}_rating" for c in ratings_df.columns]
    return ratings_df


def build_reviews(df_raw: pd.DataFrame) -> pd.DataFrame:
    ratings_df = normalize_ratings(df_raw)
    flattened_review_df = df_raw.join(ratings_df)
    flattened_review_df = flattened_review_df.drop(columns=["ratings"])
    flattened_review_df = flattened_review_df.rename(
        columns={"id": "review_id", "offering_id": "hotel_id"}
    )
    return flattened_review_df


def build_authors(df_raw: pd.DataFrame) -> pd.DataFrame:
    author_df = pd.json_normalize(df_raw["author"])
    author_df["author_key"] = (
        author_df["id"].astype(str) + "|" + author_df["username"].astype(str)
    )
    return author_df


def attach_author_key(
    reviews_df: pd.DataFrame, author_df: pd.DataFrame
) -> pd.DataFrame:
    out = reviews_df.join(author_df["author_key"])
    if "author" in out.columns:
        out = out.drop(columns=["author"])
    return out


def drop_missing_reviews(
    reviews_df: pd.DataFrame, required_cols: Iterable[str]
) -> pd.DataFrame:
    return reviews_df.dropna(subset=list(required_cols))


def filter_recent_reviews(
    reviews_df: pd.DataFrame, years: int = 5, date_col: str = "review_date"
) -> pd.DataFrame:
    latest_year = reviews_df[date_col].max().year
    return reviews_df[reviews_df[date_col].dt.year >= latest_year - (years - 1)]


def pct(x: int, n: int) -> str:
    return f"{(x / n * 100):.2f}%"


def dedupe_reviews_by_content(
    reviews_df: pd.DataFrame,
    subset: List[str],
    date_col: str = "review_date",
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    sorted_df = reviews_df.sort_values(date_col, na_position="last")
    deduped_df = sorted_df.drop_duplicates(subset=subset, keep="first")
    return deduped_df, sorted_df


def build_hotels_agg(
    review_df: pd.DataFrame,
    review_cols: Iterable[str],
    hotel_id_col: str = "hotel_id",
    review_id_col: str = "review_id",
) -> pd.DataFrame:
    return (
        review_df.copy()
        .groupby(hotel_id_col)
        .agg(
            num_reviews=(review_id_col, "nunique"),
            **{f"avg_{col}": (col, "mean") for col in review_cols},
        )
        .sort_values("num_reviews", ascending=False)
        .reset_index()
    )


def write_db(
    db_path: str,
    reviews_df: pd.DataFrame,
    author_df: pd.DataFrame,
    hotels_df: pd.DataFrame,
) -> None:
    reviews_out = reviews_df.copy()

    if "review_date" in reviews_out.columns:
        reviews_out["review_date"] = pd.to_datetime(
            reviews_out["review_date"], errors="coerce"
        ).dt.strftime("%Y-%m-%d")

    if "hotel_id" in reviews_out.columns and "hotel_id" in hotels_df.columns:
        hotels_out = hotels_df[
            hotels_df["hotel_id"].isin(reviews_out["hotel_id"].dropna().unique())
        ].copy()
    else:
        hotels_out = hotels_df.copy()

    if "author_key" in reviews_out.columns and "author_key" in author_df.columns:
        authors_out = author_df[
            author_df["author_key"].isin(reviews_out["author_key"].dropna().unique())
        ].copy()
    else:
        authors_out = author_df.copy()

    conn = sqlite3.connect(db_path)
    reviews_out.to_sql("reviews", conn, if_exists="replace", index=False)
    authors_out.to_sql("authors", conn, if_exists="replace", index=False)
    hotels_out.to_sql("hotels", conn, if_exists="replace", index=False)

    cur = conn.cursor()

    cur.execute("CREATE INDEX IF NOT EXISTS idx_reviews_hotel ON reviews(hotel_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_reviews_date ON reviews(review_date)")
    cur.execute(
        "CREATE INDEX IF NOT EXISTS idx_reviews_hotel_date ON reviews(hotel_id, review_date)"
    )

    if "review_id" in reviews_out.columns:
        cur.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS ux_reviews_review_id ON reviews(review_id)"
        )
    if "hotel_id" in hotels_out.columns:
        cur.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS ux_hotels_hotel_id ON hotels(hotel_id)"
        )

    if "author_key" in authors_out.columns:
        cur.execute("CREATE INDEX IF NOT EXISTS idx_authors_author_key ON authors(author_key)")
        cur.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS ux_authors_author_key ON authors(author_key)"
        )

    cur.execute("CREATE INDEX IF NOT EXISTS idx_hotels_hotel_id ON hotels(hotel_id)")

    conn.commit()
    conn.close()
