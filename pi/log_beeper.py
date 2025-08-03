import socket
import threading
import numpy as np
import sounddevice as sd
import time
from concurrent.futures import ThreadPoolExecutor
import atexit

# Define port and buffer size
PORT = 8888
BUFFER_SIZE = 1024

# Set the default audio output device to the USB speaker
sd.default.device = 0  # Replace with your USB device index or name

# Frequency ranges for each genre
GENRE_BEEPS = {
    "PROBE": (400, 600),
    "BANDWIDTH": (700, 900),
    "CONNECTION": (1000, 1200),
    "ATTACK": (1400, 1600),
    "BEACON": (200, 300),
    "REQUEST_TO_SEND": (500, 700),
    "CLEAR_TO_SEND": (800, 1000),
    "UNHANDLED_MANAGEMENT": (1200, 1400),
    "UNKNOWN_CTRL": (150, 250),
    "UNKNOWN": (1600, 1800),
}

# Parameters for audio playback
SAMPLE_RATE = 48000
BUFFER_SIZE_SAMPLES = SAMPLE_RATE // 10  # Buffer size for 0.1 seconds of audio
BUFFER_LENGTH = SAMPLE_RATE * 2

# Shared audio buffer
audio_buffer = np.zeros(BUFFER_LENGTH, dtype=np.float32)
buffer_lock = threading.Lock()

# Thread pool for managing sound threads
thread_pool = ThreadPoolExecutor(max_workers=10)

# Ensure the thread pool shuts down gracefully on exit
@atexit.register
def cleanup_thread_pool():
    print("Shutting down thread pool...")
    thread_pool.shutdown(wait=True)

# Function to generate and mix a sound into the buffer
def mix_sound(frequency, duration=1.0):
    global audio_buffer
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
    wave = 0.5 * np.sin(2 * np.pi * frequency * t).astype(np.float32)

    with buffer_lock:
        # Append the new wave to the end of the buffer
        audio_buffer[:len(wave)] += wave
        # Prevent clipping
        audio_buffer = np.clip(audio_buffer, -1.0, 1.0)

# Audio playback thread
def audio_playback():
    global audio_buffer
    print(f"DEBUG: Starting audio playback with device: {sd.default.device}")
    with sd.OutputStream(samplerate=SAMPLE_RATE, channels=1, dtype='float32') as stream:
        while True:
            with buffer_lock:
                # Continuously play the audio buffer
                playback_data = np.copy(audio_buffer[:BUFFER_SIZE_SAMPLES])
                # Slide the buffer window forward
                audio_buffer = np.roll(audio_buffer, -BUFFER_SIZE_SAMPLES)
                # Zero out the new space at the end
                audio_buffer[-BUFFER_SIZE_SAMPLES:] = 0
            stream.write(playback_data)

# Categorize logs based on their content
def categorize_log(log):
    log_lower = log.lower()  # Case-insensitive matching
    if "probe" in log_lower:
        return "PROBE"
    elif "connection" in log_lower or "clear-to-send" in log_lower:
        return "CONNECTION"
    elif "data" in log_lower or "bandwidth" in log_lower:
        return "BANDWIDTH"
    elif "attack" in log_lower or "suspicious" in log_lower:
        return "ATTACK"
    elif "beacon" in log_lower:
        return "BEACON"
    elif "request-to-send" in log_lower:
        return "REQUEST_TO_SEND"
    elif "clear-to-send" in log_lower:
        return "CLEAR_TO_SEND"
    elif "unhandled management subtype" in log_lower:
        return "UNHANDLED_MANAGEMENT"
    elif "unknown 802.11 ctrl frame subtype" in log_lower:
        return "UNKNOWN_CTRL"
    else:
        return "UNKNOWN"

# Generate a random beep for a specific genre
def beep_for_genre(genre):
    if genre in GENRE_BEEPS:
        freq_range = GENRE_BEEPS[genre]
        frequency = np.random.randint(*freq_range)
        print(f"DEBUG: Adding {genre} sound at {frequency} Hz")
        thread_pool.submit(mix_sound, frequency)

def main():
    # Start audio playback thread
    threading.Thread(target=audio_playback, daemon=True).start()

    while True:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                # Enable socket reuse and keepalive options
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
                s.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 60)  # Idle time before sending keepalives
                s.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 10)  # Interval between keepalive probes
                s.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 5)    # Max failed probes before disconnect

                s.bind(("", PORT))
                s.listen(1)
                print(f"Listening for logs on port {PORT}...")

                conn, addr = s.accept()
                print(f"Connection from {addr}")

                with conn:
                    while True:
                        try:
                            data = conn.recv(BUFFER_SIZE).decode("utf-8").strip()
                            if not data:
                                print(f"Connection closed by client {addr}")
                                break
                            print(f"Received log: {data}")

                            # Categorize and play sound for the log
                            genre = categorize_log(data)
                            print(f"Genre: {genre}")
                            beep_for_genre(genre)
                        except ConnectionResetError as cre:
                            print(f"Connection reset by client: {addr}, error: {cre}")
                            break
                        except Exception as e:
                            print(f"Error during data processing: {e}")
                            break
        except OSError as os_error:
            print(f"Socket error: {os_error}")
        except Exception as e:
            print(f"Unexpected error in server: {e}")
        finally:
            print("Retrying in 5 seconds...")
            time.sleep(5)

if __name__ == "__main__":
    main()
