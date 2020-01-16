import json
from flask import render_template, redirect, request, jsonify
import requests
from app import app
from urllib.parse import quote
from app.update import tuneIn
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
SCOPE = "user-modify-playback-state streaming user-read-email user-read-private"

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
        "client_id": SPOTIFY_CLIENT_ID
    }
    url_args = "&".join(["{}={}".format(key, quote(val)) for key, val in auth_query_parameters.items()])
    auth_url = "{}/?{}".format(SPOTIFY_AUTH_URL, url_args)
    return render_template("index.html", auth_url=auth_url)


@app.route("/callback/q")
def callback():
    # Request refresh
    auth_token = request.args['code']
    code_payload = {
        "grant_type": "authorization_code",
        "code": str(auth_token),
        "redirect_uri": REDIRECT_URI,
        'client_id': SPOTIFY_CLIENT_ID,
        'client_secret': SPOTIFY_SECRET,
    }
    post_request = requests.post(SPOTIFY_TOKEN_URL, data=code_payload)

    # Use refresh
    response_data = json.loads(post_request.text)
    refresh_token = response_data["refresh_token"]
    access_token = response_data['access_token']

    return render_template("player.html",
                           refresh=refresh_token,
                           token=access_token)


@app.route("/refresh", methods=['POST'])
def refresh_and_tune():
    dict = tuneIn(request.form['refresh_key'], request.form['device_id'])
    return jsonify({'name': dict['name'],
                    'cc': dict['cc'],
                   'country_name': dict['country_name'],
                    'iss_lat': dict['iss_lat'],
                    'iss_long': dict['iss_long']
                    })
