from flask import Flask, render_template, request, flash
from dotenv import load_dotenv
from db import Song, init_db
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import os

# Load environment variables
load_dotenv()

# Inisialisasi Flask
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET", "your_secret_key")

# Inisialisasi database dan Spotify API
Session = init_db()
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=os.getenv("SPOTIFY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIFY_CLIENT_SECRET")
))


@app.route('/', methods=['GET', 'POST'])
def index():
    recognized_text = ''
    results = []

    if request.method == 'POST':
        lyrics_input = request.form.get('lyrics', '').strip()
        recognized_text = lyrics_input

        if lyrics_input:
            session = Session()
            try:
                # Cari di database lokal dulu
                matches = (
                    session.query(Song)
                    .filter(Song.lyrics.like(f"%{lyrics_input}%"))
                    .limit(20)
                    .all()
                )

                for m in matches:
                    results.append({
                        'title': m.title,
                        'artist': m.artist,
                        'url': getattr(m, 'url', '#'),
                        'album_cover': None,
                        'preview_url': None,
                        'source': 'local'
                    })

            finally:
                session.close()

            # Kalau tidak ketemu di database → cari di Spotify
            if not results:
                try:
                    tracks = sp.search(q=lyrics_input, type='track', limit=20)

                    for t in tracks['tracks']['items']:
                        results.append({
                            'title': t['name'],
                            'artist': t['artists'][0]['name'],
                            'url': t['external_urls']['spotify'],
                            'album_cover': t['album']['images'][0]['url'] if t['album']['images'] else None,
                            'preview_url': t['preview_url'],  # 🎵 ini penting!
                            'source': 'spotify'
                        })
                except Exception as e:
                    flash('Spotify search error: ' + str(e), 'danger')

    return render_template('index.html', results=results, recognized_text=recognized_text)


if __name__ == '__main__':
    app.run(debug=True)