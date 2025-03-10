from ytmusicapi import YTMusic
import yt_dlp
import torch
import numpy as np
import soundfile as sf
import os
import time
from demucs.separate import main as demucs_separate

class MusicService:
    def __init__(self):
        # Get the absolute path to the src directory (where app.py is)
        self.src_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.cache_dir = os.path.join(self.src_dir, 'static', 'cache')
        
        self.ytmusic = YTMusic()
        # Update paths to use absolute paths
        self.ydl_opts = {
            'format': 'bestaudio',
            'noplaylist': True,
            'outtmpl': os.path.join(self.cache_dir, '%(id)s.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',
            }],
            'postprocessor_args': [
                '-ar', '44100',
                '-ac', '2',
            ],
        }
        # Create cache directory using absolute path
        os.makedirs(self.cache_dir, exist_ok=True)
        
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
        """Get direct audio URL without post-processing"""
        try:
            # Use separate options for URL extraction
            url_opts = {
                'format': 'bestaudio',
                'noplaylist': True,
                'extract_flat': True,
                'quiet': True
            }
            
            with yt_dlp.YoutubeDL(url_opts) as ydl:
                url = f"https://music.youtube.com/watch?v={video_id}"
                info = ydl.extract_info(url, download=False)
                # Get best audio format URL
                if 'url' in info:
                    return info['url']
                elif 'formats' in info:
                    # Find best audio-only format
                    audio_formats = [f for f in info['formats'] 
                                   if f.get('vcodec') == 'none' and f.get('acodec') != 'none']
                    if audio_formats:
                        return audio_formats[0]['url']
                return None
        except Exception as e:
            print(f"Error getting audio URL: {e}")
            return None

    def process_audio(self, video_id):
        """Download and process audio with Demucs two-stem separation"""
        try:
            # Use absolute paths for file operations
            audio_path = os.path.join(self.cache_dir, f"{video_id}.wav")
            separated_path = os.path.join(self.cache_dir, "htdemucs", video_id)
            instrumental_path = os.path.join(separated_path, "no_vocals.wav")
            
            if os.path.exists(instrumental_path):
                print(f"Using cached instrumental for {video_id}")
                return {
                    # Return relative paths for Flask static files
                    'original': f"/static/cache/{video_id}.wav",
                    'instrumental': f"/static/cache/htdemucs/{video_id}/no_vocals.wav",
                    'should_play_instrumental': True
                }
            
            if not os.path.exists(audio_path):
                print(f"Downloading audio for {video_id}")
                with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                    url = f"https://music.youtube.com/watch?v={video_id}"
                    info = ydl.extract_info(url, download=True)
            
            print(f"Applying Demucs separation for {video_id}")
            demucs_separate([
                "--two-stems", "vocals",
                "-n", "htdemucs",
                "-d", "mps",
                audio_path,
                "-o", self.cache_dir
            ])
            
            # Return relative paths for Flask static files
            return {
                'original': f"/static/cache/{video_id}.wav",
                'instrumental': f"/static/cache/htdemucs/{video_id}/no_vocals.wav",
                'should_play_instrumental': True
            }
                
        except Exception as e:
            print(f"Error processing audio: {e}")
            return None

    def cleanup_cache(self, max_age_hours=24):
        """Remove old cached files"""
        try:
            current_time = time.time()
            for filename in os.listdir(self.cache_dir):
                file_path = os.path.join(self.cache_dir, filename)
                if os.path.getmtime(file_path) < current_time - (max_age_hours * 3600):
                    os.remove(file_path)
        except Exception as e:
            print(f"Error cleaning cache: {e}")