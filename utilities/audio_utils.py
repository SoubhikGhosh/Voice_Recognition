from speechbrain.pretrained import SpeakerRecognition
from transformers import Wav2Vec2Processor, Wav2Vec2ForCTC
import numpy as np
import librosa
import torch
import os
import subprocess 
from scipy.signal import wiener
# Load models
speaker_model = SpeakerRecognition.from_hparams(source="speechbrain/spkrec-ecapa-voxceleb", savedir="tmp")
processor = Wav2Vec2Processor.from_pretrained("facebook/wav2vec2-base-960h")
stt_model = Wav2Vec2ForCTC.from_pretrained("facebook/wav2vec2-base-960h")

# Utility functions
def process_audio(audio_path):
    signal, sr = librosa.load(audio_path, sr=16000, mono=True)
    # Noise Reduction (Wiener filtering for residual noise)
    signal = wiener(signal)
    #trimming 
    # signal = librosa.effects.trim(signal)
    
    # Voice Activity Detection (VAD)
    energy = np.array([np.sum(np.abs(signal[i:i + 512])**2) for i in range(0, len(signal), 256)])
    mask = energy > 0.02 * np.max(energy)
    vad_signal = np.concatenate([signal[i * 256:(i + 1) * 256] for i in range(len(mask)) if mask[i]])
    signal = vad_signal

    return signal

def generate_embedding(signal, model=speaker_model):
    # Convert the signal to a numpy array and then to a tensor in a more efficient way
    signal = np.array(signal)  # Ensure signal is a numpy array
    embedding = model.encode_batch(torch.tensor(signal)).squeeze().tolist()
    return embedding


def transcribe_audio(audio_path, mode="wave2vec2"):
    if mode == "wave2vec2":
        signal, sr = librosa.load(audio_path, sr=16000, mono=True)
        input_values = processor(signal, sampling_rate=sr, return_tensors="pt", padding=True).input_values
        logits = stt_model(input_values).logits
        predicted_ids = torch.argmax(logits, dim=-1)
        transcription = processor.batch_decode(predicted_ids)[0]
        print(transcription)

    ## TODO
    if mode == "vosk":
                # Define paths
        audio_file = "../Data/Keshab.m4a"
        output_file = "KOut.txt"
        model_paths = ["../Models/vosk-model-small-en-in-0.4/"]

        for model_path in model_paths:
            # Run vosk-transcriber using subprocess
            command = f"vosk-transcriber -i {audio_file} -o {output_file} -m {model_path}"
            print(command)
            subprocess.run(command, shell=True, check=True)

            # Read the output transcription from the text file
            if os.path.exists(output_file):
                with open(output_file, 'r') as file:
                    transcription = file.read()
                    print("Transcription:")
                    print(transcription)

                # Delete the output text file after reading
                os.remove(output_file)
            else:
                print(f"Error: {output_file} not found!")
    return transcription