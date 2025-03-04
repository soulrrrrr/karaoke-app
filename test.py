import lrclib

video_id = "g_k3G7qMo8w"

try:
    lyrics = lrclib.get_lyrics(video_id)
    if lyrics:
        print("Lyrics found:\n", lyrics)
    else:
        print("No lyrics available for this video.")
except Exception as e:
    print("Error fetching lyrics:", str(e))