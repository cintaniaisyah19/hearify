"""
Full Music Crawler:
1. Fetch tracks from Spotify (e.g. playlist, artist, charts)
2. Find lyrics using Genius API
3. Save results to local DB
"""

import os
import time
from dotenv import load_dotenv
from lyricsgenius import Genius
from spotipy import Spotify
from spotipy.oauth2 import SpotifyClientCredentials
from tqdm import tqdm
from db import Session, Song, init_db

# === Load tokens from .env ===
load_dotenv()
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
GENIUS_API_TOKEN = os.getenv('GENIUS_API_TOKEN')

if not all([SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, GENIUS_API_TOKEN]):
    raise RuntimeError("Missing API keys in .env (check SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, GENIUS_API_TOKEN)")

# === Initialize APIs ===
sp = Spotify(client_credentials_manager=SpotifyClientCredentials(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET
))
genius = Genius(GENIUS_API_TOKEN, timeout=15, retries=3, remove_section_headers=True)

# === Init DB ===
init_db()
session = Session()

# === Configuration ===
# Global Top 50 playlist (Spotify ID)
PLAYLIST_ID = '37i9dQZEVXbMDoHDwVN2tF'  # "Top 50 - Global"
LIMIT_TRACKS = 500  # batas berapa lagu yang mau diambil

print("🎧 Fetching top songs from Spotify...")

tracks_data = sp.playlist_tracks(PLAYLIST_ID, limit=LIMIT_TRACKS)
tracks = tracks_data['items']

print(f"✅ Got {len(tracks)} tracks. Searching lyrics on Genius...\n")

# === Crawl and Save ===
for item in tqdm(tracks, desc='Fetching lyrics'):
    track = item['track']
    if not track:
        continue

    title = track['name']
    artist_name = track['artists'][0]['name']
    spotify_url = track['external_urls']['spotify']

    # Skip if already exists
    exists = session.query(Song).filter(
        Song.title == title,
        Song.artist == artist_name
    ).first()
    if exists:
        continue

    try:
        # Search lyrics on Genius
        song = genius.search_song(title, artist_name)
        lyrics = song.lyrics if song else None

        if lyrics:
            new_song = Song(
                title=title,
                artist=artist_name,
                lyrics=lyrics,
                url=spotify_url
            )
            session.add(new_song)
            session.commit()
            time.sleep(1)  # avoid rate limit
        else:
            print(f"❌ No lyrics found for: {title} - {artist_name}")

    except Exception as e:
        print(f"⚠️ Error for {title} - {artist_name}: {e}")
        session.rollback()

session.close()
print("\n✅ Done! All available songs and lyrics have been saved.")
