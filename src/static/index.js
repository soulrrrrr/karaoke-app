let audioPlayer;
let currentLyrics = [];
let playPauseBtn, progressBar, progress, currentTimeDisplay, durationDisplay;
let isDragging = false;
let songTitleElement, artistNameElement;
let wasPlaying = false;  // Add this with other global variables
let songQueue = [];
let currentSongIndex = -1;

// Add audio player controls
const audioPlayers = {
    original: document.createElement('audio'),
    instrumental: document.createElement('audio')
};

// Add this new class for managing queue items
class QueueItem {
    constructor(videoId, title, artist) {
        this.videoId = videoId;
        this.title = title;
        this.artist = artist;
        this.status = 'queued'; // queued, loading, ready
        this.instrumental = null;
        this.lyrics = null;
    }
}

// Add these functions after the global variables
function saveQueueToLocalStorage() {
    localStorage.setItem('songQueue', JSON.stringify(songQueue));
    localStorage.setItem('currentSongIndex', currentSongIndex);
}

async function loadQueueFromLocalStorage() {
    try {
        const savedQueue = localStorage.getItem('songQueue');
        const savedIndex = localStorage.getItem('currentSongIndex');

        if (savedQueue) {
            songQueue = JSON.parse(savedQueue);
            currentSongIndex = parseInt(savedIndex) || -1;

            // Check status for all songs in queue
            await Promise.all(songQueue.map(async (item, index) => {
                const statusResponse = await fetch(`/status/${item.videoId}`);
                const statusData = await statusResponse.json();

                if (statusData.ready) {
                    item.status = 'ready';
                    item.instrumental = statusData;
                } else {
                    // Start preparing if not ready
                    prepareSong(index);
                }
            }));

            // Update UI
            updateQueueDisplay();

            // If there was a playing song, restore it
            if (currentSongIndex >= 0 && currentSongIndex < songQueue.length) {
                loadQueuedSong(currentSongIndex);
            }
        }
    } catch (error) {
        console.error('Error loading queue from storage:', error);
    }
}

document.addEventListener('DOMContentLoaded', function () {
    audioPlayer = document.getElementById('audioPlayer');
    playPauseBtn = document.getElementById('playPauseBtn');
    progressBar = document.getElementById('progressBar');
    progress = document.getElementById('progress');
    currentTimeDisplay = document.getElementById('currentTime');
    durationDisplay = document.getElementById('duration');
    songTitleElement = document.getElementById('songTitle');
    artistNameElement = document.getElementById('artistName');

    // Play/Pause button handler
    playPauseBtn.addEventListener('click', togglePlay);

    // Progress bar click handler
    progressBar.addEventListener('click', seek);

    // Audio player event listeners
    audioPlayer.addEventListener('play', updatePlayPauseButton);
    audioPlayer.addEventListener('pause', updatePlayPauseButton);
    audioPlayer.addEventListener('timeupdate', updateProgress);
    audioPlayer.addEventListener('loadedmetadata', updateDuration);

    audioPlayer.addEventListener('play', startLyricSync);
    audioPlayer.addEventListener('pause', stopLyricSync);
    audioPlayer.addEventListener('seeking', updateLyrics);

    // Add drag functionality to progress bar
    progressBar.addEventListener('mousedown', (e) => {
        isDragging = true;
        seek(e);
    });

    document.addEventListener('mousemove', (e) => {
        if (isDragging) {
            seek(e);
        }
    });

    document.addEventListener('mouseup', () => {
        isDragging = false;
    });

    // Add keyboard controls
    document.addEventListener('keydown', (e) => {
        // Skip if we're typing in the search input
        if (e.target === searchInput) {
            return;
        }

        switch (e.code) {
            case 'Space':
                e.preventDefault();
                togglePlay();
                break;
            case 'ArrowLeft':
                e.preventDefault();
                audioPlayer.currentTime = Math.max(0, audioPlayer.currentTime - 5);
                break;
            case 'ArrowRight':
                e.preventDefault();
                audioPlayer.currentTime = Math.min(audioPlayer.duration, audioPlayer.currentTime + 5);
                break;
        }
    });

    // Add this to your DOMContentLoaded event listener
    loadQueueFromLocalStorage();

    const volumeBtn = document.getElementById('volumeBtn');
    const volumeSlider = document.getElementById('volumeSlider');

    // Load saved volume or set default
    const savedVolume = localStorage.getItem('volume') || 1;
    audioPlayer.volume = savedVolume;
    volumeSlider.value = savedVolume;
    updateVolumeIcon(savedVolume);

    // Volume slider change handler
    volumeSlider.addEventListener('input', (e) => {
        const volume = parseFloat(e.target.value);
        audioPlayer.volume = volume;
        localStorage.setItem('volume', volume);
        updateVolumeIcon(volume);
    });

    // Volume button click handler (mute/unmute)
    volumeBtn.addEventListener('click', () => {
        if (audioPlayer.volume > 0) {
            // Store current volume before muting
            volumeBtn.dataset.lastVolume = audioPlayer.volume;
            audioPlayer.volume = 0;
            volumeSlider.value = 0;
        } else {
            // Restore last volume
            const lastVolume = parseFloat(volumeBtn.dataset.lastVolume || 1);
            audioPlayer.volume = lastVolume;
            volumeSlider.value = lastVolume;
        }
        updateVolumeIcon(audioPlayer.volume);
    });

    // Add ended event listener for audio player
    audioPlayer.addEventListener('ended', () => {
        playNextSong();
    });

    // Clean up old cached lyrics
    cleanupLyricsCache();
});

function togglePlay() {
    if (audioPlayer.paused) {
        audioPlayer.play();
    } else {
        audioPlayer.pause();
    }
}

function updatePlayPauseButton() {
    playPauseBtn.textContent = audioPlayer.paused ? 'Play' : 'Pause';
}

function seek(e) {
    const rect = progressBar.getBoundingClientRect();
    const pos = Math.min(Math.max(0, (e.clientX - rect.left)), rect.width);
    const percentage = pos / rect.width;
    const seekTime = percentage * audioPlayer.duration;

    // Update UI immediately
    progress.style.width = `${percentage * 100}%`;
    currentTimeDisplay.textContent = formatTime(seekTime);

    // Set the new time
    audioPlayer.currentTime = seekTime;
}

function updateProgress() {
    const percent = (audioPlayer.currentTime / audioPlayer.duration) * 100;
    progress.style.width = `${percent}%`;
    currentTimeDisplay.textContent = formatTime(audioPlayer.currentTime);
    updateLyrics();
}

function updateDuration() {
    durationDisplay.textContent = formatTime(audioPlayer.duration);
}

function formatTime(seconds) {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.floor(seconds % 60);
    return `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;
}

let syncInterval;
function startLyricSync() {
    syncInterval = setInterval(updateLyrics, 100);
}

function stopLyricSync() {
    clearInterval(syncInterval);
}

// Replace the existing updateLyrics function with this enhanced version
function updateLyrics() {
    const currentTime = audioPlayer.currentTime;
    const lyrics = document.querySelectorAll('.lyric-line');

    lyrics.forEach((line, index) => {
        const timestamp = parseFloat(line.dataset.time);
        const nextTimestamp = parseFloat(lyrics[index + 1]?.dataset.time || Infinity);

        // Remove all classes first
        line.classList.remove('active', 'upcoming', 'passed');

        // Remove existing progress indicator
        const existingIndicator = line.querySelector('.progress-indicator');
        if (existingIndicator) {
            existingIndicator.remove();
        }

        if (currentTime >= timestamp && currentTime < nextTimestamp) {
            // Current line
            line.classList.add('active');

            // Calculate progress through current line
            const lineDuration = nextTimestamp - timestamp;
            const lineProgress = ((currentTime - timestamp) / lineDuration) * 100;

            // Add progress indicator
            const progressIndicator = document.createElement('div');
            progressIndicator.className = 'progress-indicator';
            progressIndicator.style.width = `${lineProgress}%`;
            line.appendChild(progressIndicator);

            // Smooth scroll
            line.scrollIntoView({
                behavior: 'smooth',
                block: 'center'
            });

            // Mark next few lines as upcoming
            for (let i = 1; i <= 3; i++) {
                if (lyrics[index + i]) {
                    lyrics[index + i].classList.add('upcoming');
                }
            }
        } else if (currentTime < timestamp) {
            // Future lines
            line.classList.add('upcoming');
        } else {
            // Past lines
            line.classList.add('passed');
        }
    });
}

// Search functionality
const searchInput = document.getElementById('searchInput');
const searchResults = document.getElementById('searchResults');

// Remove the keydown event listener and add button click handler
const searchButton = document.getElementById('searchButton');

searchButton.addEventListener('click', async () => {
    const query = searchInput.value.trim();
    if (!query) return;

    try {
        const searchResponse = await fetch(`/search?q=${encodeURIComponent(query)}`);
        const results = await searchResponse.json();

        if (!results || results.length === 0) {
            alert('No songs found');
            return;
        }

        // Add first result to queue
        const song = results[0];
        await addToQueue(song.videoId, song.name, song.artists[0].name);
        searchInput.value = '';

    } catch (error) {
        console.error('Search error:', error);
        alert('Error performing search');
    }
});

// Add these new functions
function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

// Update loadSong function to be simpler
async function loadSong(videoId, title, artist) {
    try {
        // Store current playback state
        wasPlaying = !audioPlayer.paused;
        audioPlayer.pause();

        // Get lyrics using the title directly
        const lyricsResponse = await fetch(`/lyrics?q=${encodeURIComponent(title)}&title=${encodeURIComponent(title)}&artist=${encodeURIComponent(artist)}`);
        const lyricsData = await lyricsResponse.json();

        if (lyricsData.error) {
            throw new Error(lyricsData.error);
        }

        // Update song info and display lyrics
        songTitleElement.textContent = lyricsData.title;
        artistNameElement.textContent = lyricsData.artist;

        if (lyricsData.syncedLyrics) {
            displayLyrics(lyricsData.syncedLyrics);
        }

        // Get and play audio
        const audioResponse = await fetch(`/audio/${videoId}`);
        const audioData = await audioResponse.json();

        // Set new audio source and load
        audioPlayer.src = audioData.url;
        await audioPlayer.load();

        // Process audio with Demucs
        const processResponse = await fetch(`/process/${videoId}`);
        const processData = await processResponse.json();

        if (processData.error) {
            throw new Error(processData.error);
        }

        // Update audio source to instrumental version
        if (processData.should_play_instrumental) {
            audioPlayer.src = processData.instrumental;
            await audioPlayer.load();
        }

        // Clear search input
        searchInput.value = '';

        // Only play if it was playing before
        if (wasPlaying) {
            await audioPlayer.play();
        }

    } catch (error) {
        console.error('Error loading song:', error);
        alert(`Error loading song: ${error.message}`);
    }
}

function parseSyncedLyrics(syncedLyrics) {
    if (typeof syncedLyrics === 'string') {
        // Parse LRC format
        return syncedLyrics.split('\n')
            .map(line => {
                const match = line.match(/\[(\d{2}):(\d{2}\.\d{2})\](.*)/);
                if (match) {
                    const minutes = parseInt(match[1]);
                    const seconds = parseFloat(match[2]);
                    const time = minutes * 60 + seconds;
                    return {
                        time: time,
                        text: match[3].trim()
                    };
                }
                return null;
            })
            .filter(item => item !== null);
    }
    // Already parsed format
    return syncedLyrics;
}

function displayLyrics(parsedLyrics) {
    const lyricsContainer = document.getElementById('lyrics');
    lyricsContainer.innerHTML = '';

    parsedLyrics.forEach((lyric, index) => {
        const lyricDiv = document.createElement('div');
        lyricDiv.className = 'lyric-line';
        lyricDiv.dataset.time = lyric.time;
        lyricDiv.dataset.index = index;
        lyricDiv.textContent = lyric.text || '♪';
        lyricsContainer.appendChild(lyricDiv);
    });

    // Store lyrics for synchronization
    currentLyrics = parsedLyrics;
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Add this function to handle adding songs to queue
async function addToQueue(videoId, title, artist) {
    const queueItem = new QueueItem(videoId, title, artist);
    songQueue.push(queueItem);
    updateQueueDisplay();
    saveQueueToLocalStorage();  // Add this line

    // If this is the first song, start playing it
    if (songQueue.length === 1) {
        currentSongIndex = 0;
        await loadQueuedSong(0);
    }

    // Start preparing the song in the background
    prepareSong(songQueue.length - 1);
}

// Add function to update queue display
function updateQueueDisplay() {
    const queueContainer = document.getElementById('songQueue');
    queueContainer.innerHTML = songQueue.map((item, index) => `
                <div class="queue-item ${index === currentSongIndex ? 'active' : ''}" 
                    onclick="switchToSong(${index})">
                    <div class="queue-item-info">
                        <div class="queue-item-title">${escapeHtml(item.title.split(' ')[0])}</div>
                        <div class="queue-item-artist">${escapeHtml(item.artist)}</div>
                    </div>
                    <span class="queue-status status-${item.status}">${item.status}</span>
                    <button class="remove-btn" onclick="removeFromQueue(${index}, event)">Remove</button>
                </div>
            `).join('');

    // Scroll to keep current song visible in second position
    if (currentSongIndex >= 0) {
        const activeItem = queueContainer.children[currentSongIndex];
        if (activeItem) {
            const itemHeight = activeItem.offsetHeight;
            queueContainer.scrollTop = Math.max(0, currentSongIndex * itemHeight - itemHeight);
        }
    }
}

// Add function to prepare song assets
async function prepareSong(index) {
    const item = songQueue[index];
    item.status = 'loading';
    updateQueueDisplay();

    try {
        // Check cache first
        const cachedLyrics = getLyricsFromCache(item.videoId);
        if (cachedLyrics) {
            console.log('Using cached lyrics for:', item.title);
            item.lyrics = cachedLyrics;
        } else {
            // Fetch lyrics if not in cache
            const lyricsResponse = await fetch(`/lyrics?q=${encodeURIComponent(item.title)}&title=${encodeURIComponent(item.title)}&artist=${encodeURIComponent(item.artist)}`);
            item.lyrics = await lyricsResponse.json();

            // Store in cache
            if (item.lyrics && !item.lyrics.error) {
                storeLyricsInCache(item.videoId, item.lyrics);
            }
        }

        // Process audio
        const processResponse = await fetch(`/process/${item.videoId}`);
        item.instrumental = await processResponse.json();

        item.status = 'ready';
    } catch (error) {
        console.error('Error preparing song:', error);
        item.status = 'error';
    }

    updateQueueDisplay();
}

// Add function to switch between songs
async function switchToSong(index) {
    if (index === currentSongIndex || index >= songQueue.length) return;

    const item = songQueue[index];

    // Check current status before switching
    const statusResponse = await fetch(`/status/${item.videoId}`);
    const statusData = await statusResponse.json();

    if (statusData.ready) {
        item.status = 'ready';
        item.instrumental = statusData;
    }

    // Store current playback state (but ignore if coming from ended event)
    const wasPlaying = !audioPlayer.paused && !audioPlayer.ended;
    audioPlayer.pause();

    currentSongIndex = index;
    await loadQueuedSong(index);
    updateQueueDisplay();
    saveQueueToLocalStorage();

    // Reset playback position
    audioPlayer.currentTime = 0;
    progress.style.width = '0%';
    currentTimeDisplay.textContent = '00:00';

    // Restore playback state if it was playing or if auto-playing next song
    if ((wasPlaying || audioPlayer.ended) && item.status === 'ready') {
        await audioPlayer.play();
    }
}

// Update loadQueuedSong function
async function loadQueuedSong(index) {
    const item = songQueue[index];

    try {
        // Update UI
        songTitleElement.textContent = item.title;
        artistNameElement.textContent = item.artist;

        // Check current status
        const statusResponse = await fetch(`/status/${item.videoId}`);
        const statusData = await statusResponse.json();

        if (statusData.ready) {
            item.status = 'ready';
            item.instrumental = statusData;
        }

        // Reset playback position indicators
        progress.style.width = '0%';
        currentTimeDisplay.textContent = '00:00';

        // If lyrics are already fetched, display them
        if (item.lyrics && item.lyrics.syncedLyrics) {
            console.log('Displaying lyrics:', item.lyrics.syncedLyrics);
            displayLyrics(item.lyrics.syncedLyrics);
        } else {
            // Fetch lyrics if not available
            const lyricsResponse = await fetch(`/lyrics?q=${encodeURIComponent(item.title)}&title=${encodeURIComponent(item.title)}&artist=${encodeURIComponent(item.artist)}`);
            item.lyrics = await lyricsResponse.json();

            if (item.lyrics && item.lyrics.syncedLyrics) {
                displayLyrics(item.lyrics.syncedLyrics);
            } else {
                document.getElementById('lyrics').innerHTML = '<div class="lyric-line">No lyrics available</div>';
            }
        }

        // If instrumental is ready, use it
        if (item.status === 'ready' && item.instrumental) {
            audioPlayer.src = item.instrumental.instrumental;
            await audioPlayer.load();
            audioPlayer.currentTime = 0;
        } else {
            // Fall back to regular audio URL
            const audioResponse = await fetch(`/audio/${item.videoId}`);
            const audioData = await audioResponse.json();
            audioPlayer.src = audioData.url;
            await audioPlayer.load();
            audioPlayer.currentTime = 0;
        }

    } catch (error) {
        console.error('Error loading queued song:', error);
        alert(`Error loading song: ${error.message}`);
    }
}

async function removeFromQueue(index, event) {
    // Prevent the click from triggering the song switch
    event.stopPropagation();

    // If removing currently playing song
    if (index === currentSongIndex) {
        audioPlayer.pause();
        // If there are songs after this one, play the next song
        if (index < songQueue.length - 1) {
            songQueue.splice(index, 1);
            await loadQueuedSong(index);
        } else if (index > 0) {
            // If there are songs before this one, play the previous song
            songQueue.splice(index, 1);
            currentSongIndex--;
            await loadQueuedSong(currentSongIndex);
        } else {
            // If this is the only song
            songQueue.splice(index, 1);
            currentSongIndex = -1;
            audioPlayer.src = '';
            songTitleElement.textContent = 'No song selected';
            artistNameElement.textContent = 'Select a song to begin';
            document.getElementById('lyrics').innerHTML = '';
        }
    } else {
        // If removing a different song
        if (index < currentSongIndex) {
            currentSongIndex--;
        }
        songQueue.splice(index, 1);
    }

    updateQueueDisplay();
    saveQueueToLocalStorage();
}

// Add this new function for updating volume icon
function updateVolumeIcon(volume) {
    const volumeBtn = document.getElementById('volumeBtn');
    const icon = volumeBtn.querySelector('.volume-icon');

    if (volume === 0) {
        icon.textContent = '🔇';
    } else if (volume < 0.5) {
        icon.textContent = '🔈';
    } else {
        icon.textContent = '🔊';
    }
}

// Add this new function to handle playing next song
async function playNextSong() {
    // If there's no next song in queue, return
    if (currentSongIndex >= songQueue.length - 1) {
        return;
    }

    // Move to next song
    await switchToSong(currentSongIndex + 1);

    // Force play the next song
    try {
        await audioPlayer.play();
    } catch (error) {
        console.error('Error auto-playing next song:', error);
    }
}

// Add new function to handle lyrics caching
function storeLyricsInCache(videoId, lyrics) {
    try {
        const cache = JSON.parse(localStorage.getItem('lyricsCache') || '{}');
        cache[videoId] = {
            lyrics: lyrics,
            timestamp: Date.now()
        };
        localStorage.setItem('lyricsCache', JSON.stringify(cache));
    } catch (error) {
        console.error('Error caching lyrics:', error);
    }
}

function getLyricsFromCache(videoId) {
    try {
        const cache = JSON.parse(localStorage.getItem('lyricsCache') || '{}');
        const cachedData = cache[videoId];

        // Check if cache exists and is not older than 24 hours
        if (cachedData && Date.now() - cachedData.timestamp < 24 * 60 * 60 * 1000) {
            return cachedData.lyrics;
        }
        return null;
    } catch (error) {
        console.error('Error reading lyrics cache:', error);
        return null;
    }
}

// Add cache cleanup function
function cleanupLyricsCache() {
    try {
        const cache = JSON.parse(localStorage.getItem('lyricsCache') || '{}');
        const now = Date.now();
        const maxAge = 24 * 60 * 60 * 1000; // 24 hours

        // Remove entries older than 24 hours
        const cleaned = Object.entries(cache).reduce((acc, [key, value]) => {
            if (now - value.timestamp < maxAge) {
                acc[key] = value;
            }
            return acc;
        }, {});

        localStorage.setItem('lyricsCache', JSON.stringify(cleaned));
    } catch (error) {
        console.error('Error cleaning lyrics cache:', error);
    }
}