import pyaudio
import wave
import subprocess

def record_audio(filename, duration=5, sample_rate=44100, channels=1, chunk=1024):
    # Initialize PyAudio
    audio = pyaudio.PyAudio()

    # Open stream
    stream = audio.open(format=pyaudio.paInt16,
                        channels=channels,
                        rate=sample_rate,
                        input=True,
                        frames_per_buffer=chunk)

    print(f"Recording for {duration} seconds...")

    frames = []

    # Record audio
    for _ in range(0, int(sample_rate / chunk * duration)):
        data = stream.read(chunk)
        frames.append(data)

    print("Recording finished.")

    # Stop and close the stream
    stream.stop_stream()
    stream.close()
    audio.terminate()

    # Save the recorded data as a WAV file
    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(audio.get_sample_size(pyaudio.paInt16))
        wf.setframerate(sample_rate)
        wf.writeframes(b''.join(frames))

    print(f"Audio saved to {filename}")
    
    # Play the recorded audio using aplay
    subprocess.call(["aplay", filename])

if __name__ == "__main__":
    record_audio("recorded_audio.wav")
