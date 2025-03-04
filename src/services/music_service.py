from ytmusicapi import YTMusic
import yt_dlp

class MusicService:
    def __init__(self):
        self.ytmusic = YTMusic()
        self.ydl_opts = {
            'format': 'bestaudio/best',
            'extractaudio': True,
            'audioformat': 'mp3',
            'noplaylist': True,
        }

    def search_song(self, query, limit=5):
        """Search for songs with better error handling"""
        if not query:
            print("Empty search query")
            return []
            
        try:
            results = self.ytmusic.search(query, filter="songs", limit=limit)
            return [
                {
                    'name': song['title'],
                    'artists': [{'name': artist['name']} for artist in song.get('artists', [])[:1]],
                    'videoId': song['videoId'],
                    'duration': song.get('duration', '0:00')
                }
                for song in results
                if 'videoId' in song and song.get('artists')
            ]
        except Exception as e:
            print(f"Error searching: {e}")
            return []

    def get_audio_url(self, video_id):
        try:
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                url = f"https://music.youtube.com/watch?v={video_id}"
                info = ydl.extract_info(url, download=False)
                return info['url']
        except Exception as e:
            print(f"Error getting audio URL: {e}")
            return None