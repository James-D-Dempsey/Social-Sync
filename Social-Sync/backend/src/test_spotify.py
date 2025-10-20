from spotipy_client import get_spotify_client
from db_connector import insert_user, get_user_id, insert_song, get_song_id, insert_history
from datetime import datetime

def main():
    user_tag = input("Enter user tag (e.g. 'james', 'victoria'): ")
    sp = get_spotify_client(user_tag)

    # Fetch the current user’s profile
    user = sp.current_user()
    print(f"Authenticated as: {user['display_name']} ({user['id']})")

    print("✅ Connected to Spotify!")
    print(f"Display Name:  {user.get('display_name')}")
    print(f"User ID:       {user.get('id')}")
    print(f"Email:         {user.get('email')}")

    # Insert user into database
    insert_user(user['id'], user['display_name'])
    user_id = get_user_id(user['id'])

    # Fetch up to 50 recently played tracks
    recent = sp.current_user_recently_played(limit=50)
    if recent and recent.get('items'):
        for item in recent['items']:
            track = item['track']

            track_id = track['id']
            full_track = sp.track(track_id)
            popularity = full_track['popularity']

            # 🔄 New: Fetch artist info and extract genre
            artist_id = track['artists'][0]['id']
            artist_info = sp.artist(artist_id)
            genres = artist_info.get('genres', [])
            genre = genres[0] if genres else None

            played_at_raw = item['played_at']
            played_at = datetime.strptime(played_at_raw, "%Y-%m-%dT%H:%M:%S.%fZ")

            print(f"🎶 {track['name']} by {track['artists'][0]['name']} at {played_at}")

            # Insert track into database
            insert_song(
                title=track['name'],
                artist=track['artists'][0]['name'],
                genre=genre,  
                popularity=popularity 
            )

            song_id = get_song_id(track['name'], track['artists'][0]['name'])

            # Insert listening history
            insert_history(user_id, song_id, played_at)

        print("✅ All recently played tracks inserted successfully.")
    else:
        print("⚠️ No recently played tracks found.")

if __name__ == "__main__":
    main()