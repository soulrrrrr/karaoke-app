class Song:
    def __init__(self, title, artist, lyrics=None, spotify_id=None):
        self.title = title
        self.artist = artist
        self.lyrics = lyrics
        self.spotify_id = spotify_id

    def __str__(self):
        return f"{self.title} - {self.artist}"