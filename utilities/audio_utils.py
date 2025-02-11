from speechbrain.pretrained import SpeakerRecognition
from transformers import Wav2Vec2Processor, Wav2Vec2ForCTC
import numpy as np
import librosa
import torch
import os
import subprocess 
# from scipy.signal import wiener

# Load models
speaker_model = SpeakerRecognition.from_hparams(source="speechbrain/spkrec-ecapa-voxceleb", savedir="tmp")
processor = Wav2Vec2Processor.from_pretrained("facebook/wav2vec2-base-960h")
stt_model = Wav2Vec2ForCTC.from_pretrained("facebook/wav2vec2-base-960h")

# Utility functions
def process_audio(audio_path):
    """
    Converts an input audio file to a PCM WAV file (if needed) using ffmpeg,
    then loads it using librosa.
    
    Parameters:
        audio_path (str): Path to the original audio file.
    
    Returns:
        np.ndarray: The audio signal.
    """
    try:
        # Create a new file path for the converted audio.
        # For example, if audio_path is ".../recording.wav", then use ".../recording_fixed.wav"
        base, ext = os.path.splitext(audio_path)
        converted_audio_path = base + "_fixed.wav"
        
        # Build the ffmpeg command to convert the audio file to PCM WAV
        # -acodec pcm_s16le  => PCM 16-bit little-endian encoding
        # -ar 16000           => Set sample rate to 16000 Hz
        # -ac 1               => Set audio channels to mono
        # -y                  => Overwrite output file if it exists
        command = (
            f"ffmpeg -i \"{audio_path}\" "
            f"-acodec pcm_s16le -ar 16000 -ac 1 \"{converted_audio_path}\" -y"
        )
        # Execute the command; stdout/stderr can be captured if needed.
        subprocess.run(command, shell=True, check=True)
        
        # Now load the converted file using librosa
        signal, sr = librosa.load(converted_audio_path, sr=16000, mono=True)
        return signal
    
    except Exception as e:
        print(f"Exception in processing audio: {e}")
        return None
    
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