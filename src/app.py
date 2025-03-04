from flask import Flask, render_template, request, jsonify
from services.music_service import MusicService
from services.lyrics_service import LyricsService

app = Flask(__name__)
music_service = MusicService()
lyrics_service = LyricsService()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search')
def search():
    query = request.args.get('q', '')
    if not query:
        return jsonify([])
    
    try:
        # Use the full query for search
        results = music_service.search_song(query)
        return jsonify(results)
    except Exception as e:
        print(f"Search error: {e}")
        return jsonify({"error": "Search failed"}), 500

@app.route('/lyrics')
def get_lyrics():
    # Get user's search query
    query = request.args.get('q', '')
    if not query:
        return jsonify({'error': 'No search query provided'}), 400
    
    try:
        print(f"Fetching lyrics for query: {query}")
        
        # Search for song to get metadata
        songs = music_service.search_song(query, limit=1)
        if not songs:
            print(f"No song found for query: {query}")
            return jsonify({'error': 'Song not found'}), 404
        
        song = songs[0]
        print(f"Found song: {song['name']} by {song['artists'][0]['name']}")
        
        # Get lyrics using the search query directly
        lyrics_data = lyrics_service.fetch_lyrics(query, song['artists'][0]['name'])
        if not lyrics_data:
            print(f"No lyrics found for: {query}")
            return jsonify({'error': 'Lyrics not found'}), 404
        
        # Return formatted response
        response = {
            'syncedLyrics': lyrics_data.get('syncedLyrics', []),
            'title': song['name'],
            'artist': song['artists'][0]['name'],
            'searchQuery': query  # Include original search query
        }
        
        print(f"Successfully found lyrics with {len(response['syncedLyrics'])} lines")
        return jsonify(response)
        
    except Exception as e:
        print(f"Error fetching lyrics: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/audio/<video_id>')
def get_audio(video_id):
    audio_url = music_service.get_audio_url(video_id)
    if not audio_url:
        return jsonify({'error': 'Audio not found'})
    return jsonify({'url': audio_url})

if __name__ == '__main__':
    app.run(debug=True)