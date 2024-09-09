import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
from flask import Flask, render_template, redirect, url_for, session, request

CLIENT_ID = os.environ.get('CLIENT_ID')
CLIENT_SECRET = os.environ.get('CLIENT_SECRET')
REDIRECT_URI = 'http://localhost:5000/callback'


def create_spotify_oauth():
    return SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope='user-top-read user-read-email',
        show_dialog=True,
        cache_path=None,
    )


app = Flask(__name__)
app.secret_key = "mmj6k2JT5D9u6S5zq5Mt19xUc1IXxAr5"


@app.route('/')
def login():
    session.clear()
    try:
        if os.path.exists('.cache'):
            os.remove('.cache')
            print("Cache file deleted.")
    except Exception as e:
        print(f"Error deleting cache file: {e}")
    sp_oauth = create_spotify_oauth()
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)


@app.route('/callback')
def callback():
    session.clear()
    sp_oauth = create_spotify_oauth()
    code = request.args.get('code')
    try:
        token_info = sp_oauth.get_access_token(code)
        session['token_info'] = token_info
        print(session)
    except spotipy.oauth2.SpotifyOauthError as e:
        session.clear()
        return redirect(url_for('login'))
    return redirect(url_for('dashboard'))


@app.route("/dashboard")
def dashboard():
    token_info = get_token()
    if not token_info:
        return redirect(url_for('login'))

    try:
        session.clear()
        sp = spotipy.Spotify(auth_manager=create_spotify_oauth())
        user_profile = sp.current_user()
        display_name = user_profile['display_name']
        profile_img = user_profile['images'][1]['url']

        top_tracks = sp.current_user_top_tracks(limit=10, time_range='short_term')
        # track_ids = [track['id'] for track in top_tracks['items']]
        track_titles = [track['name'] for track in top_tracks['items']]
        track_popularity = [track['popularity'] for track in top_tracks['items']]
        image_links = []
        for item in top_tracks['items']:
            images = item['album']['images']
            if images:
                image_links.append(images[0]['url'])
        artist_names = []
        for item in top_tracks['items']:
            x = item["artists"]
            if len(x) > 1:
                artists = ""
                for y in range(len(x)):
                    if y == 0:
                        artists += f"{(x[y]['name'])}"
                    else:
                        artists += f" & {(x[y]['name'])}"
                artist_names.append(artists)
            else:
                artist_names.append(x[0]['name'])

    except spotipy.SpotifyException as e:
        print(f"Spotify Exception {e}")
        session.clear()
        return redirect(url_for('login'))

    return render_template("dashboard.html",
                           song_title=track_titles,
                           cover_images=image_links,
                           song_artist=artist_names,
                           song_popularity=track_popularity,
                           user_display_name=display_name,
                           user_profile_img=profile_img,
                           )


@app.route("/logout")
def logout():
    session.clear()
    try:
        if os.path.exists('.cache'):
            os.remove('.cache')
            print("Cache file deleted.")
    except Exception as e:
        print(f"Error deleting cache file: {e}")
    return redirect(url_for('login'))


def get_token():
    token_info = session.get('token_info', None)
    if not token_info:
        return None

    sp_oauth = create_spotify_oauth()
    try:
        if sp_oauth.is_token_expired(token_info):
            token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
            session['token_info'] = token_info
    except spotipy.oauth2.SpotifyOauthError as e:
        print(f"Error refreshing token: {e}")
        session.clear()
        return None
    return token_info


if __name__ == "__main__":
    app.run()

