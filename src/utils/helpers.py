def format_song_data(song):
    """Format song data for display."""
    return f"{song['title']} by {song['artist']} (ID: {song['id']})"

def validate_song_data(song):
    """Validate the song data structure."""
    required_keys = ['title', 'artist', 'id']
    return all(key in song for key in required_keys)