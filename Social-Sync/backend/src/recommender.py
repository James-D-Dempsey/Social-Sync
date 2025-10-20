import pandas as pd
import mysql.connector

from db_connector import (
    get_user_id,
    clear_recommendations,
    insert_recommendations,
)

from config import (
    MYSQL_HOST,
    MYSQL_USER,
    MYSQL_PASSWORD,
    MYSQL_DATABASE
)


def get_db_connection():
    return mysql.connector.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DATABASE,
    )


def recommend_unpopular_tracks(user_id: int,
                               popularity_cutoff: int = 30,
                               top_n: int = 20) -> pd.DataFrame:
    """
    Returns up to top_n songs by:
      1) unpopular, out-of-genre, in others' history, never heard by this user
      2) then unpopular globally, never heard by this user
      3) then any least-popular, never heard by this user
    """
    conn = get_db_connection()

    # genres the user has already heard
    sql_user_genres = """
    SELECT DISTINCT s.genre
      FROM ListeningHistory lh
      JOIN Songs s USING (song_id)
     WHERE lh.user_id = %s
    """
    user_genres = (
        pd.read_sql(sql_user_genres, conn, params=(user_id,))
          .genre.dropna().tolist()
    )

    # build NOT IN clause for those genres
    genre_condition = ""
    genre_params = []
    if user_genres:
        ph = ",".join(["%s"] * len(user_genres))
        genre_condition = f"AND (s.genre IS NULL OR s.genre NOT IN ({ph}))"
        genre_params = user_genres

    # unpopular, out-of-genre, in others' history, never heard
    sql_primary = f"""
    SELECT DISTINCT
           s.song_id,
           s.title,
           s.artist,
           s.genre,
           s.popularity,
           s.popularity AS score
      FROM ListeningHistory lh_other
      JOIN Songs s ON lh_other.song_id = s.song_id
     WHERE lh_other.user_id <> %s
       {genre_condition}
       AND s.popularity <= %s
       AND s.song_id NOT IN (
           SELECT song_id FROM ListeningHistory WHERE user_id = %s
       )
     ORDER BY s.popularity ASC
     LIMIT %s
    """
    params_primary = [user_id] + genre_params + [popularity_cutoff, user_id, top_n]
    df = pd.read_sql(sql_primary, conn, params=params_primary)

    needed = top_n - len(df)

    # unpopular globally, never heard
    if needed > 0:
        sql_fb1 = """
        SELECT s.song_id,
               s.title,
               s.artist,
               s.genre,
               s.popularity,
               s.popularity AS score
          FROM Songs s
         WHERE s.popularity <= %s
           AND s.song_id NOT IN (
             SELECT song_id FROM ListeningHistory WHERE user_id = %s
           )
         ORDER BY s.popularity ASC
         LIMIT %s
        """
        df_fb1 = pd.read_sql(
            sql_fb1,
            conn,
            params=(popularity_cutoff, user_id, needed)
        )
        df = pd.concat([df, df_fb1], ignore_index=True)
        needed = top_n - len(df)

    # any least-popular, never heard
    if needed > 0:
        sql_fb2 = """
        SELECT s.song_id,
               s.title,
               s.artist,
               s.genre,
               s.popularity,
               s.popularity AS score
          FROM Songs s
         WHERE s.song_id NOT IN (
           SELECT song_id FROM ListeningHistory WHERE user_id = %s
         )
         ORDER BY s.popularity ASC
         LIMIT %s
        """
        df_fb2 = pd.read_sql(
            sql_fb2,
            conn,
            params=(user_id, needed)
        )
        df = pd.concat([df, df_fb2], ignore_index=True)

    conn.close()
    return df.head(top_n)


def store_recommendations(user_id: int, recs: pd.DataFrame):
    """
    Deletes any old recs for this user and inserts the new ones,
    using the helpers in db_connector.py.
    """
    # turn your DataFrame into a simple list of (song_id, score)
    rec_list = [
        (int(row.song_id), float(row.score))
        for row in recs.itertuples(index=False)
    ]

    # clear out the old rows
    clear_recommendations(user_id)

    # bulk‑insert the new ones (no-op if rec_list is empty)
    insert_recommendations(user_id, rec_list)


def get_recommendations(spotify_id: str,
                        popularity_cutoff: int = 30,
                        top_n: int = 20) -> list[dict]:
    """
    1) Look up internal user_id from spotify_id
    2) Generate the DataFrame of recs
    3) Store them in Recommendations
    4) Return JSON‑serializable dicts
    """
    uid = get_user_id(spotify_id)
    recs_df = recommend_unpopular_tracks(
        user_id=uid,
        popularity_cutoff=popularity_cutoff,
        top_n=top_n
    )
    store_recommendations(uid, recs_df)
    return recs_df.to_dict(orient="records")


if __name__ == '__main__':
    # CLI test: pass numeric user_id
    import sys
    uid = int(sys.argv[1])
    df = recommend_unpopular_tracks(uid)
    print(df.to_string(index=False) if not df.empty else "No recommendations!")