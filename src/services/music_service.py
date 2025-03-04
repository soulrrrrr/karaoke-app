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
        try:
            results = self.ytmusic.search(query, filter="songs", limit=limit)
            return [
                {
                    'name': song['title'],
                    'artists': [{'name': song['artists'][0]['name']}],
                    'videoId': song['videoId'],
                    'duration': song['duration']
                }
                for song in results
                if 'videoId' in song
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