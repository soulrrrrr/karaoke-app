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
    query = request.args.get('q', '')
    title = request.args.get('title', '')
    artist = request.args.get('artist', '')
    
    if not query:
        return jsonify({'error': 'No search query provided'}), 400
    
    try:
        print(f"Fetching lyrics for: {title} by {artist}")
        
        # Get all matching songs
        songs = music_service.search_song(title, limit=5)
        
        if not songs:
            print(f"No songs found for: {title}")
            return jsonify({'error': 'Song not found'}), 404
        
        # Find best match considering both title and artist
        best_match = None
        for song in songs:
            result_title = song['name'].lower()
            result_artist = song['artists'][0]['name'].lower()
            search_title = title.lower()
            search_artist = artist.lower()
            
            print(f"Comparing: '{result_title} - {result_artist}' with '{search_title} - {search_artist}'")
            
            # Check for exact match
            if result_title == search_title and result_artist == search_artist:
                best_match = song
                print(f"Found exact match: {song['name']} by {song['artists'][0]['name']}")
                break
            
            # Check for partial match
            elif result_title in search_title or search_title in result_title:
                if result_artist in search_artist or search_artist in result_artist:
                    best_match = song
                    print(f"Found partial match: {song['name']} by {song['artists'][0]['name']}")
                    break
        
        if not best_match:
            best_match = songs[0]  # Fallback to first result
            print(f"No exact match found, using: {best_match['name']} by {best_match['artists'][0]['name']}")
        
        # Get lyrics using matched song
        lyrics_data = lyrics_service.fetch_lyrics(best_match['name'], best_match['artists'][0]['name'])
        if not lyrics_data:
            print(f"No lyrics found for: {best_match['name']}")
            return jsonify({'error': 'Lyrics not found'}), 404
        
        response = {
            'syncedLyrics': lyrics_data.get('syncedLyrics', []),
            'title': best_match['name'],
            'artist': best_match['artists'][0]['name'],
            'searchQuery': query
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

@app.route('/process/<video_id>')
def process_audio(video_id):
    try:
        result = music_service.process_audio(video_id)
        if result:
            return jsonify(result)
        return jsonify({'error': 'Processing failed'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)