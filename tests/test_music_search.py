import unittest
from src.api.music_search import search_songs

class TestMusicSearch(unittest.TestCase):

    def test_search_songs_valid_query(self):
        query = "Imagine"
        expected_result = [{"title": "Imagine", "artist": "John Lennon", "id": 1}]
        result = search_songs(query)
        self.assertEqual(result, expected_result)

    def test_search_songs_empty_query(self):
        query = ""
        expected_result = []
        result = search_songs(query)
        self.assertEqual(result, expected_result)

    def test_search_songs_no_results(self):
        query = "Nonexistent Song"
        expected_result = []
        result = search_songs(query)
        self.assertEqual(result, expected_result)

if __name__ == '__main__':
    unittest.main()