import socket
import re
import time
import os
import uuid
import openai
import pygame
from random import random
from google.cloud import texttospeech
from openai import OpenAI

HOST = ""  
PORT = 8888
BATCH_INTERVAL = 10  
log_batch = []
OPENAI_API_KEY = 'NO_USE_MY_API_KEY'
ASSISTANT_ID = "MAKE_YOUR_OWN_ASSISTANT_ID"
openai.api_key = OPENAI_API_KEY
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "GET_A_JSON_FROM_G_CLOUD"

client = OpenAI(api_key=openai.api_key)
client.beta.assistants.retrieve(ASSISTANT_ID)
thread = client.beta.threads.create()

# Function to generate TTS audio
def generate_tts_audio(text, output_filename):
    client = texttospeech.TextToSpeechClient()
    synthesis_input = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US",
        name="en-US-Wavenet-F",
        ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
    )

    # Configure the audio file type
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,
        pitch=-5.0,  # Lower pitch for sarcasm
        speaking_rate=1.0
    )
  
    response = client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )
    with open(output_filename, "wb") as out:
        out.write(response.audio_content)


# Function to process assistant's response
def filter_response(response):
    sentences = response.split(". ")
    filtered_sentences = []

    for sentence in sentences:
        if sentence.lower().startswith("oh,") or sentence.lower().startswith("ah,"):
            if random() < 0.2:
                filtered_sentences.append(sentence)
            else:
                filtered_sentences.append(sentence[3:].strip().capitalize())
        else:
            filtered_sentences.append(sentence)

    return ". ".join(filtered_sentences).strip()

# Function to check if logs are uninteresting
def is_uninteresting(log):
    patterns_to_remove = [
        r"Beacon",
        r"BA RA:",
        r"signal antenna",
        r"unknown 802.11 ctrl",
        r"Unhandled Management"
    ]
    for pattern in patterns_to_remove:
        if re.search(pattern, log, re.IGNORECASE):
            return True
    return False

# Function to process and enrich tcpdump logs
def process_log(log):
    """
    Process a single log line and decide whether to display it.
    """
    if not is_uninteresting(log):
        log_batch.append(log)

# Function to send logs to ChatGPT and get Karen's response
def send_batch():
    if log_batch:
        logs = "\n".join(log_batch)
        print(logs)

        try:
            client = OpenAI(api_key=openai.api_key)
            client.beta.assistants.retrieve(ASSISTANT_ID)
            thread = client.beta.threads.create()
          
            client.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=logs
            )

            run = client.beta.threads.runs.create_and_poll(
                thread_id=thread.id,
                assistant_id=ASSISTANT_ID,
            )

            if run.status == "completed":
                messages = client.beta.threads.messages.list(thread_id=thread.id)
                assistant_message = [
                    message for message in messages.data
                    if message.role == "assistant"
                ][0]  # Get the latest assistant message

                response_text = filter_response(assistant_message.content[0].text.value)
                print(f"KarenWiFi: {response_text}")
              
                unique_filename = f"karen_response_{uuid.uuid4().hex}.mp3"
                generate_tts_audio(response_text, unique_filename)
                play_audio_with_pygame(unique_filename)

                # Clean up the file after playback
                try:
                    os.remove(unique_filename)
                except Exception as e:
                    print(f"Error deleting file {unique_filename}: {e}")

            else:
                print(f"KarenWiFi: (Run failed with status {run.status})")
        except Exception as e:
            print(f"Error communicating with Assistant API: {e}")
        finally:
            # Reset the batch after sending
            log_batch.clear()
    else:
        print("No interesting logs to send.")


def play_audio_with_pygame(file_path):
    try:
        pygame.mixer.init()
        pygame.mixer.music.load(file_path)
        pygame.mixer.music.play()

        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)

        pygame.mixer.music.stop()
    except Exception as e:
            print(f"Error playing audio: {e}")
    finally:
        pygame.mixer.quit()


def main():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((HOST, PORT))
            s.listen(1)
            print(f"Listening for logs on port {PORT}...")

            conn, addr = s.accept()
            print(f"Connection established with {addr}")

            last_batch_time = time.time()

            with conn:
                while True:
                    data = conn.recv(1024).decode("utf-8").strip()
                    if not data:
                        print(f"Connection closed by {addr}")
                        break

                    # Split incoming data into individual lines
                    logs = data.split("\n")
                    for log in logs:
                        process_log(log)

                    # Check if it's time to send the batch
                    current_time = time.time()
                    if current_time - last_batch_time >= BATCH_INTERVAL:
                        send_batch()
                        last_batch_time = current_time

    except KeyboardInterrupt:
        print("Server shut down.")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
