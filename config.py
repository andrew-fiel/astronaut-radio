import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))


class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'secrets-and-whatnot'
    SPOTIFY_CLIENT_ID = os.environ.get('SPOTIFY_CLIENT_ID')
    SPOTIFY_SECRET = os.environ.get('SPOTIFY_SECRET')
    MAPQUEST_KEY = os.environ.get('MAPQUEST_KEY')
    LOCAL_FOR_DEV = os.environ.get('LOCAL_FOR_DEV') or "False"
