import requests
import re
from typing import Optional, Dict, Any, List, Tuple

class LyricsService:
    def __init__(self):
        self.base_url = "https://lrclib.net/api"
        self.headers = {
            "User-Agent": "KaraokeApp v0.1.0 (https://github.com/yourusername/karaoke-app)"
        }

    def parse_timestamp(self, timestamp: str) -> float:
        """Convert [MM:SS.xx] format to seconds"""
        match = re.match(r'\[(\d{2}):(\d{2})\.(\d{2})\]', timestamp)
        if match:
            minutes, seconds, centiseconds = map(int, match.groups())
            return minutes * 60 + seconds + centiseconds / 100
        return 0

    def parse_synced_lyrics(self, synced_lyrics: str) -> List[Tuple[float, str]]:
        """Parse synced lyrics with improved timestamp handling"""
        if not synced_lyrics:
            return []

        parsed_lyrics = []
        for line in synced_lyrics.split('\n'):
            if not line.strip():
                continue
            
            # Handle multiple timestamps per line
            timestamps = re.findall(r'\[\d{2}:\d{2}\.\d{2}\]', line)
            text = re.sub(r'\[\d{2}:\d{2}\.\d{2}\]', '', line).strip()
            
            if timestamps and text:
                for timestamp in timestamps:
                    time_seconds = self.parse_timestamp(timestamp)
                    parsed_lyrics.append((time_seconds, text))
        
        return sorted(parsed_lyrics, key=lambda x: x[0])

    def fetch_lyrics(self, song_title: str, artist_name: str, duration: str = None) -> Optional[Dict[str, Any]]:
        """Fetch lyrics using song title, artist name, and duration"""
        try:
            original_title = song_title
            song_title = self._clean_query_param(song_title)
            artist_name = self._clean_query_param(artist_name)
            
            print(f"\nFetching lyrics for: {original_title} by {artist_name} (duration: {duration})")
            
            search_params = {
                "q": f"{original_title}".strip()
            }
            
            search_response = requests.get(
                f"{self.base_url}/search",
                params=search_params,
                headers=self.headers
            )

            if search_response.status_code == 200:
                results = search_response.json()
                if results and len(results) > 0:
                    # Find best match considering duration
                    selected_result = self._find_best_match(results, song_title, artist_name, duration)
                    
                    if not selected_result:
                        selected_result = results[0]
                    
                    # Print selected result details with duration comparison
                    print("\nSelected result details:")
                    print(f"ID: {selected_result.get('id', 'N/A')}")
                    print(f"Track: {selected_result.get('trackName', 'N/A')}")
                    print(f"Artist: {selected_result.get('artistName', 'N/A')}")
                    print(f"Result Duration: {selected_result.get('duration', 'N/A')} seconds")
                    print(f"Input Duration: {duration}")
                    print(f"Has synced lyrics: {bool(selected_result.get('syncedLyrics'))}")
                    
                    detail_response = requests.get(
                        f"{self.base_url}/get/{selected_result['id']}",
                        headers=self.headers
                    )
                    
                    if detail_response.status_code == 200:
                        processed_data = self._process_lyrics_data(detail_response.json(), duration)
                        if processed_data:
                            print(f"Successfully processed lyrics with {len(processed_data['syncedLyrics'])} lines")
                        return processed_data

        except Exception as e:
            print(f"Error fetching lyrics: {e}")
            return None

    def _find_best_match(self, results: List[Dict], title: str, artist: str, duration: str = None) -> Optional[Dict]:
        """Find best matching lyrics considering title, artist, and duration"""
        best_match = None
        min_duration_diff = float('inf')
        target_duration = self._parse_duration(duration) if duration else None

        for result in results:
            result_title = result.get('trackName', '').lower()
            result_artist = result.get('artistName', '').lower()
            result_duration = result.get('duration', 0)
            
            # Skip live versions
            if 'live' in result_title:
                continue

            # Check title and artist match
            title_match = title.lower() in result_title or result_title in title.lower()
            artist_match = artist.lower() in result_artist or result_artist in artist.lower()

            # only check title match because artist sometimes shows in English
            if title_match:
                # If we have duration info, use it to find better match
                if target_duration and result_duration:
                    duration_diff = abs(target_duration - result_duration)
                    if duration_diff < min_duration_diff:
                        min_duration_diff = duration_diff
                        best_match = result
                    if duration_diff < 1.0:
                        return result
                else:
                    # Without duration, use first matching result
                    return result

        return best_match or results[0]

    def _parse_duration(self, duration: str) -> float:
        """Convert duration string (MM:SS) to seconds"""
        try:
            if not duration:
                return 0
            parts = duration.split(':')
            if len(parts) == 2:
                minutes, seconds = map(int, parts)
                return minutes * 60 + seconds
            return 0
        except:
            return 0

    def _clean_query_param(self, param: str) -> str:
        """Clean and decode query parameters"""
        if not param:
            return ""
        
        # Handle URL encoded spaces and special characters
        try:
            # First try to decode URL-encoded strings
            from urllib.parse import unquote
            decoded = unquote(param)
            print(f"Decoded '{param}' to '{decoded}'")
            
            # Remove multiple spaces
            cleaned = ' '.join(decoded.split())
            return cleaned
        except Exception as e:
            print(f"Error cleaning parameter: {e}")
            return param

    def _process_lyrics_data(self, lyrics_data: Dict[str, Any], duration: str = None) -> Dict[str, Any]:
        """Process lyrics data with duration information"""
        if not lyrics_data:
            return None

        target_duration = self._parse_duration(duration) if duration else None
        
        result = {
            "title": lyrics_data.get("trackName", "Unknown Title"),
            "artist": lyrics_data.get("artistName", "Unknown Artist"),
            "syncedLyrics": [],
            "duration": target_duration,
            "should_play": False
        }

        synced_lyrics = lyrics_data.get("syncedLyrics", "")
        
        if synced_lyrics:
            parsed_lyrics = self.parse_synced_lyrics(synced_lyrics)
            result["syncedLyrics"] = [
                {
                    "time": time,
                    "text": text.strip()
                }
                for time, text in parsed_lyrics
                if text.strip()
            ]
            
            # Adjust timing if duration is provided
            if target_duration:
                result["syncedLyrics"] = self._adjust_lyrics_timing(
                    result["syncedLyrics"], 
                    target_duration
                )
                
            return result
        
        # Handle plain lyrics with duration-based timing
        plain_lyrics = lyrics_data.get("plainLyrics", "")
        if plain_lyrics:
            lines = [line.strip() for line in plain_lyrics.split('\n') if line.strip()]
            if target_duration and lines:
                interval = target_duration / len(lines)
                result["syncedLyrics"] = [
                    {
                        "time": i * interval,
                        "text": line
                    }
                    for i, line in enumerate(lines)
                ]
            else:
                # Fallback to default timing
                result["syncedLyrics"] = [
                    {
                        "time": i * 2.0,
                        "text": line
                    }
                    for i, line in enumerate(lines)
                ]
        
        return result

    def _adjust_lyrics_timing(self, lyrics: List[Dict], target_duration: float) -> List[Dict]:
        """Adjust lyrics timing to match the target duration"""
        if not lyrics:
            return lyrics

        # Get current duration from last lyric time
        current_duration = lyrics[-1]["time"]
        
        if current_duration == 0:
            return lyrics

        # Calculate scaling factor
        scale = target_duration / current_duration

        # Adjust timing
        return [
            {
                "time": lyric["time"] * scale,
                "text": lyric["text"]
            }
            for lyric in lyrics
        ]