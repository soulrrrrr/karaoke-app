def search_songs(query):
    # This function simulates searching for songs based on a query.
    # In a real application, this would interface with a music database or API.
    
    # Sample data for demonstration purposes
    sample_songs = [
        {"id": 1, "title": "Song One", "artist": "Artist A"},
        {"id": 2, "title": "Song Two", "artist": "Artist B"},
        {"id": 3, "title": "Song Three", "artist": "Artist C"},
    ]
    
    # Filter songs that match the query
    matching_songs = [
        song for song in sample_songs 
        if query.lower() in song["title"].lower() or query.lower() in song["artist"].lower()
    ]
    
    return matching_songs