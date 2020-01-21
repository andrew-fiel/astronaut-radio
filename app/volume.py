import requests


def changeVolume(authCode, device, newVolume):
    authorization_header = {"Authorization": "Bearer {}".format(authCode)}
    base = "https://api.spotify.com/v1/me/player/volume?"
    volume_endpoint = "{}volume_percent={}&device_id={}".format(base, newVolume, device)

    post_change = requests.put(volume_endpoint, headers=authorization_header)
    if post_change.status_code != 204:
        return {
            'success': 0
        }
    else:
        return {
            'success': 1
        }
