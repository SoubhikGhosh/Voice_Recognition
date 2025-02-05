import AVFoundation

def text_to_speech(text):
    # Initialize the speech synthesizer
    synthesizer = AVFoundation.AVSpeechSynthesizer.alloc().init()

    # Choose voice with Indian English accent
    voice = AVFoundation.AVSpeechSynthesisVoice.voiceWithLanguage_("en-IN")

    # Prepare the speech utterance with the text and set the voice
    utterance = AVFoundation.AVSpeechUtterance.alloc().initWithString_(text)
    utterance.setValue_forKey_(voice, "voice")  # Correct way to set the voice
    utterance.setValue_forKey_(0.5, "rate")  # Adjust speech rate

    # Speak the utterance
    synthesizer.speakUtterance_(utterance)

# Example usage
text_to_speech("Hello! This is a sample text being spoken in Indian English.")
