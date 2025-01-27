from speechbrain.pretrained import SpeakerRecognition
from transformers import Wav2Vec2Processor, Wav2Vec2ForCTC
import numpy as np
import librosa
import torch

# Load models
speaker_model = SpeakerRecognition.from_hparams(source="speechbrain/spkrec-ecapa-voxceleb", savedir="tmp")
processor = Wav2Vec2Processor.from_pretrained("facebook/wav2vec2-base-960h")
stt_model = Wav2Vec2ForCTC.from_pretrained("facebook/wav2vec2-base-960h")

# Utility functions
def process_audio(audio_path):
    signal, sr = librosa.load(audio_path, sr=16000, mono=True)
    return signal

def generate_embedding(signal, model=speaker_model):
    # Convert the signal to a numpy array and then to a tensor in a more efficient way
    signal = np.array(signal)  # Ensure signal is a numpy array
    embedding = model.encode_batch(torch.tensor(signal)).squeeze().tolist()
    return embedding


def transcribe_audio(audio_path):
    signal, sr = librosa.load(audio_path, sr=16000, mono=True)
    input_values = processor(signal, sampling_rate=sr, return_tensors="pt", padding=True).input_values
    logits = stt_model(input_values).logits
    predicted_ids = torch.argmax(logits, dim=-1)
    transcription = processor.batch_decode(predicted_ids)[0]
    return transcription
