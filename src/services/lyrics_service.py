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

    def fetch_lyrics(self, song_title: str, artist_name: str) -> Optional[Dict[str, Any]]:
        """Fetch lyrics using both song title and artist name"""
        try:
            # Clean and decode input parameters
            original_title = song_title
            song_title = self._clean_query_param(song_title)
            artist_name = self._clean_query_param(artist_name)
            
            print(f"\nFetching lyrics for: {original_title} by {artist_name}")
            
            # Search using both title and artist
            search_params = {
                "q": f"{original_title} {artist_name}".strip()
            }
            
            print(f"Searching with query: {search_params['q']}")
            search_response = requests.get(
                f"{self.base_url}/search",
                params=search_params,
                headers=self.headers
            )
            print(f"Search response status: {search_response.status_code}")

            if search_response.status_code == 200:
                results = search_response.json()
                if results and len(results) > 0:
                    # Find best match considering both title and artist
                    best_match = None
                    for result in results:
                        result_title = result.get('trackName', '').lower()
                        result_artist = result.get('artistName', '').lower()
                        search_title = song_title.lower()
                        search_artist = artist_name.lower()
                        
                        print(f"Comparing: '{result_title} - {result_artist}' with '{search_title} - {search_artist}'")
                        
                        # Skip live versions
                        if any(live_indicator in result_title for live_indicator in 
                              ['live', 'concert', 'tour', 'unplugged', 'acoustic']):
                            print(f"Skipping live version: {result_title}")
                            continue
                        
                        # Check for exact match
                        if result_title == search_title and result_artist == search_artist:
                            best_match = result
                            print(f"Found exact match: {result['trackName']} by {result['artistName']}")
                            break
                        
                        # Check for partial match with both title and artist
                        title_match = (search_title in result_title or result_title in search_title)
                        artist_match = (search_artist in result_artist or result_artist in search_artist)
                        
                        if title_match and artist_match:
                            best_match = result
                            print(f"Found partial match: {result['trackName']} by {result['artistName']}")
                            if not best_match:  # Take first match only
                                break
                    
                    if best_match:
                        # Get detailed lyrics
                        detail_response = requests.get(
                            f"{self.base_url}/get/{best_match['id']}",
                            headers=self.headers
                        )
                        
                        if detail_response.status_code == 200:
                            processed_data = self._process_lyrics_data(detail_response.json())
                            if processed_data:
                                print(f"Successfully processed lyrics with {len(processed_data['syncedLyrics'])} lines")
                            return processed_data

            print(f"No lyrics found for: {original_title} by {artist_name}")
            return None

        except Exception as e:
            print(f"Error fetching lyrics: {e}")
            return None

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

    def _process_lyrics_data(self, lyrics_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process and validate lyrics data"""
        if not lyrics_data:
            print("No lyrics data to process")
            return None

        result = {
            "title": lyrics_data.get("trackName", "Unknown Title"),
            "artist": lyrics_data.get("artistName", "Unknown Artist"),
            "syncedLyrics": [],
            "should_play": False  # Default to not playing
        }

        print(f"\nProcessing lyrics for: {lyrics_data.get('trackName')} - {lyrics_data.get('artistName')}")
        
        synced_lyrics = lyrics_data.get("syncedLyrics", "")
        
        if synced_lyrics:
            print("Found synced lyrics")
            parsed_lyrics = self.parse_synced_lyrics(synced_lyrics)
            result["syncedLyrics"] = [
                {
                    "time": time,
                    "text": text.strip()
                }
                for time, text in parsed_lyrics
                if text.strip()
            ]
            print(f"Processed {len(result['syncedLyrics'])} synced lyric lines")
            return result
        
        print("No synced lyrics, checking plain lyrics")
        plain_lyrics = lyrics_data.get("plainLyrics", "")
        if plain_lyrics:
            print("Found plain lyrics")
            lines = [line.strip() for line in plain_lyrics.split('\n') if line.strip()]
            result["syncedLyrics"] = [
                {
                    "time": i * 2.0,
                    "text": line
                }
                for i, line in enumerate(lines)
            ]
            print(f"Created {len(result['syncedLyrics'])} timed lyric lines from plain lyrics")
        else:
            print("No lyrics found in data")
        
        return result