import json
from flask import render_template, g, redirect, request
import requests
from app import app
from urllib.parse import quote
import random
import os

# spotify api keys
SPOTIFY_CLIENT_ID = app.config['SPOTIFY_CLIENT_ID']
SPOTIFY_SECRET = app.config['SPOTIFY_SECRET']

# Spotify URLS
SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_API_BASE_URL = "https://api.spotify.com"
API_VERSION = "v1"
SPOTIFY_API_URL = "{}/{}".format(SPOTIFY_API_BASE_URL, API_VERSION)

# Server-side Parameters
CLIENT_SIDE_URL = "http://127.0.0.1"
PORT = 5000
REDIRECT_URI = "{}:{}/callback/q".format(CLIENT_SIDE_URL, PORT)
SCOPE = "user-modify-playback-state"

SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
json_url = os.path.join(SITE_ROOT, 'data', 'country_data.json')
country_data = json.load(open(json_url))


@app.route('/')
@app.route('/index')
def index():
    auth_query_parameters = {
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPE,
        "client_id": SPOTIFY_CLIENT_ID,
        "show_dialog": "true"
    }
    url_args = "&".join(["{}={}".format(key, quote(val)) for key, val in auth_query_parameters.items()])
    auth_url = "{}/?{}".format(SPOTIFY_AUTH_URL, url_args)
    return redirect(auth_url)


@app.route("/callback/q")
def callback():
    # Auth Step 4: Requests refresh and access tokens
    auth_token = request.args['code']
    code_payload = {
        "grant_type": "authorization_code",
        "code": str(auth_token),
        "redirect_uri": REDIRECT_URI,
        'client_id': SPOTIFY_CLIENT_ID,
        'client_secret': SPOTIFY_SECRET,
    }
    post_request = requests.post(SPOTIFY_TOKEN_URL, data=code_payload)

    # Auth Step 5: Tokens are Returned to Application
    response_data = json.loads(post_request.text)
    access_token = response_data["access_token"]
    refresh_token = response_data["refresh_token"]
    token_type = response_data["token_type"]
    expires_in = response_data["expires_in"]

    # Auth Step 6: Use the access token to access Spotify API
    authorization_header = {"Authorization": "Bearer {}".format(access_token)}

    # find lat and long of iss
    iss_endpoint = "https://api.wheretheiss.at/v1/satellites/25544"
    iss_response = requests.get(iss_endpoint)
    iss_data = json.loads(iss_response.text)

    iss_long = iss_data['longitude']
    iss_lat = iss_data['latitude']

    MAPQUEST_KEY = app.config['MAPQUEST_KEY']

    mapquest_endpoint = "http://www.mapquestapi.com/geocoding/v1/reverse?key={}&location={},{}".format(MAPQUEST_KEY, iss_lat, iss_long)
    map_response = requests.get(mapquest_endpoint)
    map_data = json.loads(map_response.text)

    country_code = map_data['results'][0]['locations'][0]['adminArea1']
    if country_code in country_data and country_data[country_code][0] != '*':
        country_name = country_data[country_code]
    else:
        country_name = "Global"
    # Get profile data
    if country_name == "XZ":
        playlist_api_endpoint = "{}/search?q=Ocean&type=playlist&limit=3".format(SPOTIFY_API_URL)
    else:
        playlist_api_endpoint = "{}/search?q={}%20Top%2050&type=playlist&limit=3".format(SPOTIFY_API_URL, country_name)
    playlist_response = requests.get(playlist_api_endpoint, headers=authorization_header)
    playlist_data = json.loads(playlist_response.text)

    # get song from playlist
    song_get_endpoint = "{}/playlists/{}/tracks".format(SPOTIFY_API_URL, playlist_data['playlists']['items'][0]["id"])

    songs_response = requests.get(song_get_endpoint, headers=authorization_header)
    songs_data = json.loads(songs_response.text)

    songIndex = random.randrange(0, len(songs_data['items']))

    # display selected song
    display_uri = [songs_data['items'][songIndex]['track']['uri']]
    display_name = songs_data['items'][songIndex]['track']['name']

    uri_data = {
        "uris": display_uri
    }

    # play the song
    play_endpoint = "{}/me/player/play".format(SPOTIFY_API_URL)
    post_play = requests.put(play_endpoint, data=json.dumps(uri_data), headers=authorization_header)
    #play_result = json.loads(post_play.text) # breaks everything

    return render_template("index.html", selected_song_id=display_name, uri=display_uri, iss_lat=iss_lat, iss_long=iss_long, country=country_name, code=country_code)
