# spotify_client.py
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from config import SPOTIPY_CLIENT_ID, SPOTIPY_CLIENT_SECRET, SPOTIPY_REDIRECT_URI
import os

def get_spotify_client(user_tag: str):
    scope = "user-read-recently-played user-read-email"
    auth_manager = SpotifyOAuth(
        client_id=SPOTIPY_CLIENT_ID,
        client_secret=SPOTIPY_CLIENT_SECRET,
        redirect_uri=SPOTIPY_REDIRECT_URI,
        scope=scope,
        cache_path=f".cache-{user_tag}",
        show_dialog=True
    )

    print(f"Redirect URI in use: {SPOTIPY_REDIRECT_URI}")

    auth_url = auth_manager.get_authorize_url()
    print(f"\n Launching incognito login for user tag: {user_tag}")
    print(f"If the browser doesn't open, paste this manually:\n{auth_url}\n")

    os.system(f'start chrome "{auth_url}"')

    return spotipy.Spotify(auth_manager=auth_manager)