import lyricsgenius


def get_lyrics(song):
    genius = lyricsgenius.Genius(
        "XOjjMIaTD9VwiACzTXFMm03Aw2hPF7EXfJ_SLfcBYaZ12nW4AUi-ke1-1Gl5sGQB")
    song = genius.search_song(song)
    if song:
        return song.lyrics
    else:
        return "No lyrics found"


def main():
    print(get_lyrics("I'm a Believer"))


if __name__ == '__main__':
    main()
