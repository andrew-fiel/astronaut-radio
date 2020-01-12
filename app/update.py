from app import app
import requests
import json
import os
import random

SITE_ROOT = os.path.realpath(os.path.dirname(__file__))
json_url = os.path.join(SITE_ROOT, 'data', 'country_data.json')
country_data = json.load(open(json_url))


def tuneIn(spotify_refresh, device_id):
    # ------- Find latitude and longitude -----------------
    iss_endpoint = "https://api.wheretheiss.at/v1/satellites/25544"
    iss_request = requests.get(iss_endpoint)
    if iss_request.status_code // 100 != 2:
        # Error
        return
    iss_data = json.loads(iss_request.text)

    iss_long = iss_data['longitude']
    iss_lat = iss_data['latitude']

    # ------- Find country name ---------------------------
    MAPQUEST_KEY = app.config['MAPQUEST_KEY']

    MAPQURL = "http://www.mapquestapi.com/geocoding/v1/reverse?key"
    mapquest_endpoint = "{}={}&location={},{}".format(MAPQURL,
                                                      MAPQUEST_KEY,
                                                      iss_lat,
                                                      iss_long)
    map_request = requests.get(mapquest_endpoint)
    map_data = json.loads(map_request.text)
    if map_data['info']['statuscode'] != 0:
        # Error
        return

    # assigned two letter country code
    country_code = map_data['results'][0]['locations'][0]['adminArea1']

    # convert code to name of playlist spotify has
    if country_code in country_data and country_data[country_code][0] != '*':
        country_name = country_data[country_code]
    else:
        country_name = "Global"

    # --------- Find playlist --------------------------------

    body = {
        'grant_type': 'refresh_token',
        'refresh_token': spotify_refresh
    }
    SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
    SPOTIFY_CLIENT_ID = app.config['SPOTIFY_CLIENT_ID']
    SPOTIFY_SECRET = app.config['SPOTIFY_SECRET']
    SPOTIFY_API_URL = "https://api.spotify.com/v1"

    refresh_request = requests.post(SPOTIFY_TOKEN_URL,
                                    data=body,
                                    auth=(SPOTIFY_CLIENT_ID, SPOTIFY_SECRET))
    if refresh_request.status_code // 100 != 2:
        # Error
        return

    refresh_data = json.loads(refresh_request.text)
    access_token = refresh_data['access_token']
    authorization_header = {"Authorization": "Bearer {}".format(access_token)}

    if country_name == "XZ":
        playlist_api_endpoint = "{}/search?q=Ocean&type=playlist&limit=1".format(SPOTIFY_API_URL)
    else:
        playlist_api_endpoint = "{}/search?q={}%20Viral%2050&type=playlist&limit=1".format(SPOTIFY_API_URL,
                                                                                           country_name)
    playlist_response = requests.get(playlist_api_endpoint, headers=authorization_header)
    playlist_data = json.loads(playlist_response.text)

    # get song from playlist
    song_get_endpoint = "{}/playlists/{}/tracks".format(SPOTIFY_API_URL,
                                                        playlist_data['playlists']['items'][0]["id"])

    songs_request = requests.get(song_get_endpoint, headers=authorization_header)
    if songs_request.status_code // 100 != 2:
        # Error
        return

    songs_data = json.loads(songs_request.text)

    songIndex = random.randrange(0, len(songs_data['items']))

    # display selected song
    display_uri = [songs_data['items'][songIndex]['track']['uri']]
    display_name = songs_data['items'][songIndex]['track']['name']

    uri_data = {
        "uris": display_uri
    }

    # play the song
    play_endpoint = "{}/me/player/play?device_id={}".format(SPOTIFY_API_URL, device_id)
    post_play = requests.put(play_endpoint,
                             data=json.dumps(uri_data),
                             headers=authorization_header)
    if post_play.status_code == 404:
        # Error no device currently playing
        return
    if post_play.status_code == 403:
        # Error user not premium
        return

    playstate = {
        'name': display_name,
        'cc': country_code,
        'country_name': country_name,
        'iss_lat': iss_lat,
        'iss_long': iss_long
    }
    return playstate
