import pyttsx3
import os

# def text_to_speech(text, output_file="./output.wav"):
#     # Ensure the output directory exists
#     os.makedirs(os.path.dirname(output_file), exist_ok=True)

#     # Initialize the TTS engine
#     engine = pyttsx3.init()

#     # Set properties
#     engine.setProperty("voice", "com.apple.speech.synthesis.voice.rishi")  # Indian English voice
#     engine.setProperty("rate", 170)  # Adjust speech rate

#     # Save the speech to a file
#     engine.save_to_file(text, output_file)

#     # Stop the engine
#     engine.stop()

#     return output_file

# Dictionary mapping language and gender to specific voice IDs
voice_mapping = {
    "en-US": {
        "male": "com.apple.speech.synthesis.voice.Albert",  # Example male voice for US English
        "female": "com.apple.speech.synthesis.voice.Samantha"  # Example female voice for US English
    },
    "en-UK": {
        "male": "com.apple.voice.compact.en-GB.Daniel",  # Example male voice for UK English
        "female": "com.apple.eloquence.en-GB.Shelley"  # Example female voice for UK English
    },
    "en-IN": {
        "male": "com.apple.voice.compact.en-IN.Rishi",  # Indian English male
        "female": "com.apple.voice.compact.en-IN.Veena"  # Indian English female
    },
    "hi-IN": {
        "male": "com.apple.voice.compact.hi-IN.Lekha",  # Hindi male
        "female": "com.apple.voice.compact.hi-IN.Neel"  # Hindi female 
    },
    "ta-IN": {
        "female": "com.apple.voice.compact.ta-IN.Vani"  # Example Tamil female voice
    },
    "te-IN": {
        "female": "com.apple.voice.compact.te-IN.Geeta"  # Example Telugu female voice
    },
    "kn-IN": {
        "female": "com.apple.voice.compact.kn-IN.Alpana"  # Example Kannada female voice
    },
    "bn-IN": {
        "female": "com.apple.voice.compact.bn-IN.Paya"  # Example Bengali female voice
    },
    "bh-IN": {
        "female": "com.apple.voice.compact.bho-IN.Jaya"  # Example Bhojpuri female voice
    },
    "mr-IN": {
        "female": "com.apple.voice.compact.mr-IN.Ananya"  # Example Marathi female voice
    }
}

# Text-to-speech function
def text_to_speech(text, voice, language, output_file="./output.wav"):
    # Ensure the output directory exists
    # os.makedirs(os.path.dirname(output_file), exist_ok=True)

    # Initialize the TTS engine
    engine = pyttsx3.init()

    # Get the selected voice based on language and gender
    selected_voice = voice_mapping.get(language, {}).get(voice, None)
    if not selected_voice:
        raise ValueError(f"Voice not found for language {language} and gender {voice}")

    print(selected_voice)
    # Set the voice
    engine.setProperty("voice", selected_voice)
    engine.setProperty("rate", 170)  # Adjust speech rate

    # Save the speech to a file
    engine.save_to_file(text, output_file)
    # engine.stop()
    engine.runAndWait()

    return output_file
