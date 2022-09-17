import os
from setuptools import setup


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name="dogo - bot",
    version="1",
    author="Gal Grayzer",
    author_email="galgrayzer@gmail.com",
    description=("A media bot for discord"),
    license="BSD",
    url="https://github.com/galgrayzer/dogo-bot",
    packages=['discord.py', 'youtube_dl', 'youtube-search-python',
              'gtts', 'spotipy', 'lyricsgenius'],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Utilities",
        "License :: OSI Approved :: BSD License",
    ],
)
