import numpy as np
import sounddevice as sd
import threading
import time
import random


SAMPLE_RATE = 48000  # Audio sample rate
BEEP_DURATION = 0.5  # Duration of each beep in seconds
BUFFER_SIZE = int(SAMPLE_RATE * BEEP_DURATION)

# Frequency ranges for each genre
GENRE_BEEPS = {
    "PROBE": (400, 600),        # Probe requests
    "BANDWIDTH": (700, 900),    # Bandwidth-related logs
    "CONNECTION": (1000, 1200), # General connections
    "ATTACK": (1400, 1600),     # Suspicious activity
    "UNKNOWN": (200, 300),      # Unclassified logs
}

# Shared buffer for audio mixing
audio_buffer = np.zeros(BUFFER_SIZE)
buffer_lock = threading.Lock()



# Function to generate a sine wave
def generate_wave(frequency):
    t = np.linspace(0, BEEP_DURATION, BUFFER_SIZE, endpoint=False)
    wave = 0.5 * np.sin(2 * np.pi * frequency * t)
    return wave

# Function to add a sound to the shared buffer
def add_to_buffer(wave):
    global audio_buffer
    with buffer_lock:
        audio_buffer[:len(wave)] += wave
        audio_buffer = np.clip(audio_buffer, -1.0, 1.0)  # Avoid clipping

# Playback thread function
def playback_thread():
    global audio_buffer
    while True:
        with buffer_lock:
            playback_data = np.copy(audio_buffer)
            audio_buffer.fill(0)  # Clear the buffer
        sd.play(playback_data, samplerate=SAMPLE_RATE)
        sd.wait()

# Function to play a beep for a specific genre
def beep_for_genre(genre):
    if genre in GENRE_BEEPS:
        freq_range = GENRE_BEEPS[genre]
        frequency = random.randint(*freq_range)
        print(f"Playing {genre} sound at {frequency} Hz")
        wave = generate_wave(frequency)
        add_to_buffer(wave)
    else:
        print(f"Unknown genre: {genre}")

# Test function to simulate logs and play sounds
def test_beep_system():
    genres = list(GENRE_BEEPS.keys())
    print("Starting test beep system. Press Ctrl+C to exit.")

    try:
        while True:
            # Simulate a random log genre
            genre = random.choice(genres)
            beep_for_genre(genre)

            # Random delay between logs
            time.sleep(random.uniform(0.0, 0.5))
    except KeyboardInterrupt:
        print("\nTest ended.")

if __name__ == "__main__":
    # Start the playback thread
    threading.Thread(target=playback_thread, daemon=True).start()
    # Start the test system
    test_beep_system()
