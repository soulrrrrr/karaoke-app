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

    def format_time(self, seconds: float) -> str:
        """Format seconds to MM:SS.xx"""
        minutes = int(seconds // 60)
        seconds_remainder = seconds % 60
        return f"{minutes:02d}:{seconds_remainder:05.2f}"

    def fetch_lyrics(self, song_title: str, artist_name: str) -> Optional[Dict[str, Any]]:
        """Fetch lyrics directly using song title"""
        try:
            # Clean and decode input parameters
            original_title = song_title  # Keep original search query
            song_title = self._clean_query_param(song_title)
            artist_name = self._clean_query_param(artist_name)
            
            print(f"\nFetching lyrics for: {original_title}")
            
            # Search using original query
            search_params = {
                "q": original_title  # Use original search query
            }
            
            print(f"Searching with exact query: {original_title}")
            search_response = requests.get(
                f"{self.base_url}/search",
                params=search_params,
                headers=self.headers
            )
            print(f"Search response status: {search_response.status_code}")

            if search_response.status_code == 200:
                results = search_response.json()
                if results and len(results) > 0:
                    # Find exact match with original query
                    best_match = None
                    for result in results:
                        result_title = result.get('trackName', '')
                        print(f"Comparing: '{result_title}' with '{original_title}'")
                        
                        # Check for exact match first
                        if result_title == original_title:
                            best_match = result
                            print(f"Found exact match: {result_title}")
                            break
                        # Then check if titles contain each other
                        elif (original_title in result_title or 
                              result_title in original_title):
                            best_match = result
                            print(f"Found partial match: {result_title}")
                            break
                    
                    if best_match:
                        # Get detailed lyrics
                        detail_response = requests.get(
                            f"{self.base_url}/get/{best_match['id']}",
                            headers=self.headers
                        )
                        print(f"Detail response status: {detail_response.status_code}")
                        
                        if detail_response.status_code == 200:
                            processed_data = self._process_lyrics_data(detail_response.json())
                            if processed_data:
                                print(f"Successfully processed lyrics with {len(processed_data['syncedLyrics'])} lines")
                            return processed_data

            print(f"No lyrics found for: {original_title}")
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

    def format_lyrics(self, lyrics_data: Dict[str, Any], show_timestamps: bool = True) -> str:
        if not lyrics_data:
            return "No lyrics available"

        synced_lyrics = lyrics_data.get("syncedLyrics")
        if not synced_lyrics:
            return lyrics_data.get("plainLyrics", "No lyrics available")

        if not show_timestamps:
            return re.sub(r'\[\d{2}:\d{2}\.\d{2}\]', '', synced_lyrics).strip()

        # Parse and format synced lyrics with readable timestamps
        parsed_lyrics = self.parse_synced_lyrics(synced_lyrics)
        formatted_lyrics = []
        for timestamp, text in parsed_lyrics:
            time_str = self.format_time(timestamp)
            formatted_lyrics.append(f"{time_str} | {text}")

        return "\n".join(formatted_lyrics)