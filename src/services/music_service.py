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
        self.ytmusic = YTMusic()
        # Simplified options since we're using separate
        self.ydl_opts = {
            'format': 'bestaudio',
            'noplaylist': True,
            'outtmpl': 'src/static/cache/%(id)s.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',
            }],
            'postprocessor_args': [
                '-ar', '44100',  # Standard sample rate
                '-ac', '2',      # Stereo
            ],
        }
        # Create cache directory
        os.makedirs('src/static/cache', exist_ok=True)
        
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
            # Define paths
            audio_path = f"src/static/cache/{video_id}.wav"
            work_dir = "src/static/cache"
            separated_path = os.path.join(work_dir, "htdemucs", os.path.splitext(os.path.basename(audio_path))[0])
            instrumental_path = os.path.join(separated_path, "no_vocals.wav")
            
            # Check if instrumental already exists
            if os.path.exists(instrumental_path):
                print(f"Using cached instrumental for {video_id}")
                return {
                    'original': f"/static/cache/{video_id}.wav",
                    'instrumental': f"/static/cache/htdemucs/{video_id}/no_vocals.wav",
                    'should_play_instrumental': True
                }
            
            # Check if original audio needs downloading
            if not os.path.exists(audio_path):
                print(f"Downloading audio for {video_id}")
                with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                    url = f"https://music.youtube.com/watch?v={video_id}"
                    info = ydl.extract_info(url, download=True)
            else:
                print(f"Using cached audio for {video_id}")
            
            # Run two-stem separation if instrumental doesn't exist
            print(f"Applying Demucs separation for {video_id}")
            demucs_separate([
                "--two-stems", "vocals",
                "-n", "htdemucs",
                "-d", "mps",
                audio_path,
                "-o", work_dir
            ])
            
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
            cache_dir = 'src/static/cache'
            current_time = time.time()
            for filename in os.listdir(cache_dir):
                file_path = os.path.join(cache_dir, filename)
                if os.path.getmtime(file_path) < current_time - (max_age_hours * 3600):
                    os.remove(file_path)
        except Exception as e:
            print(f"Error cleaning cache: {e}")