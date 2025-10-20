import mysql.connector
import os
from dotenv import load_dotenv
from spotipy_client import get_spotify_client
from datetime import datetime

load_dotenv()

conn = mysql.connector.connect(
    host=os.getenv("MYSQL_HOST"),
    user=os.getenv("MYSQL_USER"),
    password=os.getenv("MYSQL_PASSWORD"),
    database=os.getenv("MYSQL_DATABASE")
)

cursor = conn.cursor()

def insert_user(spotify_id, name):
    cursor = conn.cursor()
    query = "INSERT IGNORE INTO Users (spotify_id, name) VALUES (%s, %s)"
    cursor.execute(query, (spotify_id, name))
    conn.commit()
    cursor.close()
    print(f"Inserted user {name} with Spotify ID {spotify_id} into the database.")

def insert_song(title, artist, genre, popularity):
    cursor = conn.cursor(buffered=True)

    # Check if the song already exists
    cursor.execute("SELECT song_id FROM Songs WHERE title = %s AND artist = %s", (title, artist))
    existing = cursor.fetchone()

    if existing:
        print(f"Song '{title}' by {artist} already exists. Skipping insert.")
    else:
        query = """
            INSERT INTO Songs (title, artist, genre, popularity)
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(query, (title, artist, genre, popularity))
        conn.commit()
        print(f" Inserted song '{title}' by {artist}' into the database.")

    cursor.close()

def insert_history(user_id, song_id, timestamp):
    cursor = conn.cursor()
    query = """
        INSERT INTO ListeningHistory (user_id, song_id, timestamp)
        VALUES (%s, %s, %s)
    """
    cursor.execute(query, (user_id, song_id, timestamp))
    conn.commit()
    cursor.close()
    print(f"Inserted listening history for user ID {user_id} and song ID {song_id} at {timestamp}.")


def get_user_id(key: str):
    cur = conn.cursor()
    cur.execute("SELECT user_id FROM Users WHERE spotify_id = %s", (key,))
    row = cur.fetchone()
    if row:
        cur.close()
        return row[0]

    cur.execute("SELECT user_id FROM Users WHERE name = %s", (key,))
    row = cur.fetchone()
    cur.close()
    return row[0] if row else None



def get_song_id(title, artist):
    cursor = conn.cursor()
    cursor.execute("SELECT song_id FROM Songs WHERE title = %s AND artist = %s", (title, artist))
    result = cursor.fetchone()
    cursor.close()
    print(f"Fetched song ID {result[0]} for title '{title}' by {artist}.") if result else print(f"No song found for title '{title}' by {artist}.")
    return result[0] if result else None


def clear_recommendations(user_id: int):
    """
    Delete any existing recommendations for this user.
    """
    cur = conn.cursor()
    cur.execute(
        "DELETE FROM Recommendations WHERE user_id = %s",
        (user_id,)
    )
    conn.commit()
    cur.close()


def insert_recommendations(user_id: int, recs: list[tuple[int, float]]):
    """
    Bulk‑insert a list of (song_id, score) into Recommendations.
    """
    if not recs:
        return

    cur = conn.cursor()
    sql = """
      INSERT INTO Recommendations (user_id, song_id, score)
      VALUES (%s, %s, %s)
    """
    data = [(user_id, song_id, score) for song_id, score in recs]
    cur.executemany(sql, data)
    conn.commit()
    cur.close()


def fetch_recommendations(user_id: int, limit: int = 20) -> list[dict]:
    """
    Read back up to `limit` recommendations for a user,
    ordered by lowest score first.
    Returns a list of {"song_id":…, "score":…}.
    """
    cur = conn.cursor()
    cur.execute(
        """
        SELECT song_id, score
          FROM Recommendations
         WHERE user_id = %s
         ORDER BY score ASC
         LIMIT %s
        """,
        (user_id, limit)
    )
    rows = cur.fetchall()
    cur.close()
    return [{"song_id": r[0], "score": r[1]} for r in rows]

def add_user(spotify_id: str):
    """
    1) Fetches the Spotify profile,
    2) INSERT IGNORE into Users (via insert_user),
    3) pulls up to 50 recent plays, and for each track:
       – insert_song, get_song_id, insert_history.
    """
    sp = get_spotify_client(spotify_id)
    user = sp.current_user()
    if not user or not user.get("id"):
        raise RuntimeError(f"Could not fetch Spotify profile for {spotify_id}")

    # 1) upsert the user
    insert_user(user["id"], user.get("display_name", spotify_id))
    uid = get_user_id(user["id"])
    if uid is None:
        raise RuntimeError(f"Failed to lookup user_id for {spotify_id}")

    # 2) fetch & store up to 50 recent tracks
    recent = sp.current_user_recently_played(limit=50).get("items", [])
    for item in recent:
        track = item["track"]
        # grab full track info for popularity
        full = sp.track(track["id"])
        popularity = full.get("popularity")

        # grab genre from first artist
        artist_id = track["artists"][0]["id"]
        genres = sp.artist(artist_id).get("genres", [])
        genre = genres[0] if genres else None

        played_at = datetime.strptime(
            item["played_at"], "%Y-%m-%dT%H:%M:%S.%fZ"
        )

        # insert song + history
        insert_song(
            title=track["name"],
            artist=track["artists"][0]["name"],
            genre=genre,
            popularity=popularity,
        )
        sid = get_song_id(track["name"], track["artists"][0]["name"])
        insert_history(uid, sid, played_at)