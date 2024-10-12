# import wave
# import struct
# import math

# def create_test_audio():
#     # Audio parameters
#     duration = 3  # seconds
#     sample_rate = 44100  # Hz
#     frequency = 440  # Hz (A4 note)

#     # Generate samples
#     samples = []
#     for i in range(int(duration * sample_rate)):
#         sample = int(32767 * math.sin(2 * math.pi * frequency * i / sample_rate))
#         samples.append(sample)

#     # Write to WAV file
#     with wave.open('test_audio.wav', 'w') as wav_file:
#         wav_file.setnchannels(1)  # Mono
#         wav_file.setsampwidth(2)  # 2 bytes per sample
#         wav_file.setframerate(sample_rate)
        
#         for sample in samples:
#             wav_file.writeframes(struct.pack('h', sample))

#     print("Test audio file 'test_audio.wav' created successfully.")

# if __name__ == "__main__":
#     create_test_audio()


