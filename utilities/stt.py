import subprocess
import os

audio_file = "../Data/Keshab.m4a"
output_file = "KOut.txt"
model_paths = ["../Models/vosk-model-small-en-in-0.4/"]

transcription = ""

def speechToText():
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