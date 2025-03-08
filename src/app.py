from flask import Flask, render_template, request, jsonify
from services.music_service import MusicService
from services.lyrics_service import LyricsService
import os

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
        
        # Modify song titles to match the search query
        results[0]['name'] = query
        
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
        print(f"APP Fetching lyrics for: {title} by {artist}")
        
        # Get all matching songs
        songs = music_service.search_song(title, limit=5)
        
        if not songs:
            print(f"No songs found for: {title}")
            return jsonify({'error': 'Song not found'}), 404
        
        best_match = songs[0]  # Fallback to first result
        
        # Get lyrics using matched song
        lyrics_data = lyrics_service.fetch_lyrics(title, best_match['artists'][0]['name'])
        if not lyrics_data:
            print(f"No lyrics found for: {best_match['name']}")
            return jsonify({'error': 'Lyrics not found'}), 404
        
        response = {
            'syncedLyrics': lyrics_data.get('syncedLyrics', []),
            'title': title,
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

@app.route('/status/<video_id>')
def check_status(video_id):
    try:
        # Check if instrumental exists
        instrumental_path = f"src/static/cache/htdemucs/{video_id}/no_vocals.wav"
        original_path = f"src/static/cache/{video_id}.wav"
        
        status = {
            'ready': False,
            'instrumental': None,
            'original': None
        }
        
        if os.path.exists(instrumental_path):
            status['ready'] = True
            status['instrumental'] = f"/static/cache/htdemucs/{video_id}/no_vocals.wav"
            status['original'] = f"/static/cache/{video_id}.wav"
            
        return jsonify(status)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)