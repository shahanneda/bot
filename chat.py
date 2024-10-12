import os
import asyncio
import websockets
import json
import base64
import pyaudio
import wave
import keyboard
from dotenv import load_dotenv

# Load the .env file into memory so the code has access to the key
load_dotenv()

# Function to start recording audio
def start_recording():
    print("Speak to send a message to the assistant. Press Enter when done.")
    
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000

    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)

    frames = []

    try:
        while True:
            data = stream.read(CHUNK)
            frames.append(data)
            if keyboard.is_pressed('enter'):
                break
    finally:
        print("Recording stopped.")
        stream.stop_stream()
        stream.close()
        p.terminate()

    # Convert audio data to base64
    audio_data = b''.join(frames)
    base64_audio = base64.b64encode(audio_data).decode('utf-8')
    return base64_audio

# Function to play audio
def play_audio(audio_data):
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 24000

    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    output=True)

    stream.write(audio_data)
    stream.stop_stream()
    stream.close()
    p.terminate()

async def main():
    # Connect to the API
    url = "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-10-01"
    headers = {
        "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}",
        "OpenAI-Beta": "realtime=v1"
    }

    async with websockets.connect(url, extra_headers=headers) as ws:
        base64_audio_data = start_recording()

        # Create conversation event
        create_conversation_event = {
            "type": "conversation.item.create",
            "item": {
                "type": "message",
                "role": "user",
                "content": [
                    {
                        "type": "input_audio",
                        "audio": base64_audio_data
                    }
                ]
            }
        }
        await ws.send(json.dumps(create_conversation_event))

        # Create response event
        create_response_event = {
            "type": "response.create",
            "response": {
                "modalities": ["text", "audio"],
                "instructions": "Please assist the user."
            }
        }
        await ws.send(json.dumps(create_response_event))

        # Handle incoming messages
        audio_chunks = []
        async for message in ws:
            data = json.loads(message)
            if data["type"] == "response.audio.delta":
                audio_chunk = base64.b64decode(data["delta"])
                audio_chunks.append(audio_chunk)
            elif data["type"] == "response.audio.done":
                full_audio = b''.join(audio_chunks)
                play_audio(full_audio)
                break

if __name__ == "__main__":
    asyncio.run(main())