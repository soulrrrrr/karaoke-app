# README.md

# Karaoke App

A modern web-based karaoke application that combines YouTube Music with synchronized lyrics. Features instrumental track separation and real-time lyric synchronization.

## Features

- 🎵 Search and play songs from YouTube Music
- 📝 Display synchronized lyrics from multiple sources (LRCLib & YouTube Music)
- 🎸 AI-powered instrumental track separation using Demucs
- 🎼 Real-time lyric highlighting and auto-scroll
- 📋 Song queue management with persistent storage
- 🎚️ Audio controls (play/pause, seek, volume)
- 💾 Local caching for audio and lyrics

## Tech Stack

- **Backend**: Python/Flask
- **Frontend**: Vanilla JavaScript, HTML5, CSS3
- **Music Processing**: Demucs (two-stem separation)
- **APIs**: 
  - YouTube Music API (via ytmusicapi)
  - LRCLib API (lyrics)
  - yt-dlp (audio extraction)

## Prerequisites

- Python 3.8+
- ffmpeg (for audio processing)
- PyTorch (for Demucs model)

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd karaoke-app
   ```
2. Navigate to the project directory:
   ```
   cd karaoke-app
   ```
3. Install the required dependencies:
   ```
   # On Linux/macOS
   chmod +x install.sh
   ./install.sh

   # On Windows (using Git Bash or similar)
   bash install.sh
   ```

## Usage

To run the application, execute the following command:
```
python src/main.py
```

Enjoy your karaoke experience!