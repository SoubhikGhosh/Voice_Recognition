from flask import Flask, request, jsonify, send_file
from flask_cors import cross_origin, CORS
from utilities.audio_utils import process_audio, generate_embedding, transcribe_audio
from utilities.dbUtils import find_most_similar_embedding, verify_transcription_and_get_user_info, register_user_in_db, check_if_registered, insert_feedback
from utilities.testDbConnection import test_connection
from utilities.tts import text_to_speech
import subprocess

# Flask app
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": ["https://172.20.10.2:3000"]}})

@app.before_request
def log_request():
    print(f"Incoming request from {request.remote_addr}")

@app.route('/', methods=['GET'])
@cross_origin(origins=['*'])
def root_call():
    return jsonify("Voice Recognition Backend"), 200

# Flask endpoints
@app.route('/test-db-connection', methods=['GET'])
@cross_origin(origins=['*'])
def test_db_connection():
    if test_connection() == "Connection successful!":
        return jsonify(test_connection()), 200
    else:
        return jsonify(test_connection()), 500
    
@app.route("/feedback", methods=["POST"])
@cross_origin(origins=['*'])
def register_feedback():
    """
    Handles user feedback by storing voice embeddings, transcription, and other details in the database.
    """
    try:
        audio_file = request.files.get("audio")
        person_name = request.form.get("name")
        predicted_phone_number = request.form.get("predicted_phone_number")
        feedback_type = request.form.get("feedback_type", "correct").lower()
        confidence = request.form.get("confidence")

        print("request :", request.form)

        # Validate required parameters
        if not audio_file or not person_name or not predicted_phone_number:
            return jsonify({"error": "Missing required parameters."}), 400

        # Determine actual phone number
        actual_phone_number = request.form.get('actual_phone_number', predicted_phone_number)

        # Validate phone number format
        if not actual_phone_number.isdigit() or len(actual_phone_number) != 10:
            return jsonify({"error": "Phone number must be exactly 10 digits."}), 400

        # Check if user is registered
        if not check_if_registered(actual_phone_number):
            return jsonify({"error": "Please register your phone number before giving feedback."}), 408

        # Save audio file
        temp_path = f"audit/Feedback/{audio_file.filename}"
        print(f"temp: {temp_path}")

        try:
            print("CP4")
            audio_file.save(temp_path)

        except Exception as e:
            print(f"Exception during saving sound: {e}")

        audio_path = f"audit/Feedback/conv_{audio_file.filename}"

        # Convert to standard WAV format
        try:
            subprocess.run(["/usr/bin/ffmpeg", "-i", temp_path, "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", audio_path], check=True)
        except subprocess.CalledProcessError as e:
            return f"Conversion failed: {e}", 500

        

        if feedback_type == "correct":
            try:
                # Process audio
                signal = process_audio(audio_path)

                # Generate embedding
                embedding = generate_embedding(signal)

                # Transcribe audio
                transcription = transcribe_audio(audio_path)

                print(f"person_name, predicted_phone_number, embedding, transcription, confidence: {person_name}, {predicted_phone_number}, {embedding}, {transcription}, {confidence}")

                # Register user in database
                register_user_in_db(person_name, predicted_phone_number, embedding, transcription)
            except Exception as e:
                return jsonify({"error": f"Audio processing error: {str(e)}"}), 500

        # Insert feedback into the database
        try:
            insert_feedback(embedding, actual_phone_number, predicted_phone_number, confidence, feedback_type)
        except Exception as e:
            return jsonify({"error": f"Error inserting feedback: {str(e)}"}), 500

        return (jsonify({"message": "Feedback received successfully."}), 200) if feedback_type == "correct" else (jsonify({"message": "Thank you for helping us improve."}), 204)

    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500

    
@app.route("/register", methods=["POST"])
@cross_origin(origins=['*'])
def register_user():
    """
    Registers a user by storing voice embeddings and transcription in the database.
    """
    print("CP1")
    audio_file = request.files.get("audio")
    person_name = request.form.get("name")
    phone_number = request.form.get("phone_number")
    print("CP2")

    if not audio_file or not person_name or not phone_number:
        return jsonify({"error": "Missing required parameters."}), 400
    print("CP3")


    temp_path = f"audit/Registration/{audio_file.filename}"
    print(f"temp: {temp_path}")

    try:
        print("CP4")
        audio_file.save(temp_path)

    except Exception as e:
        print(f"Exception during saving sound: {e}")

    audio_path = f"audit/Registration/conv_{audio_file.filename}"

    # Convert to standard WAV format
    try:
        subprocess.run(["/usr/bin/ffmpeg", "-i", temp_path, "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", audio_path], check=True)
    except subprocess.CalledProcessError as e:
        return f"Conversion failed: {e}", 500

    try:
        # Process audio
        signal = process_audio(audio_path)
        print("processing done")
        print("signal", signal)

        # Generate embedding
        embedding = generate_embedding(signal)
        print("embedding generation done")

        # Transcribe audio
        transcription = transcribe_audio(audio_path)
        print("transcription done")


        # Register the user (storing both embedding and transcription)
        register_user_in_db(person_name, phone_number, embedding, transcription)

        print("User registration in db done")

        return jsonify({"message": "User registered successfully.", "transcription": transcription}), 200
    except Exception as e:
        print(e)
        return jsonify({"error": str(e)}), 500

@app.route("/recognize", methods=["POST"])
@cross_origin(origins=['*'])
def recognize_user():
    """
    Recognizes a user by comparing their voice embedding using pgvector
    and verifying transcription.
    """
    audio_file = request.files.get("audio")
    phone_number = request.form.get("phone_number")  # Optional

    if not audio_file:
        return jsonify({"error": "Missing required parameters."}), 400

    temp_path = f"audit/Registration/{audio_file.filename}"
    print(f"temp: {temp_path}")

    try:
        print("CP4")
        audio_file.save(temp_path)

    except Exception as e:
        print(f"Exception during saving sound: {e}")

    audio_path = f"audit/Recognition/conv_{audio_file.filename}"

    # Convert to standard WAV format
    try:
        subprocess.run(["/usr/bin/ffmpeg", "-i", temp_path, "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", audio_path], check=True)
    except subprocess.CalledProcessError as e:
        return f"Conversion failed: {e}", 500

    try:
        # Process audio
        signal = process_audio(audio_path)

        # Generate embedding
        input_embedding = generate_embedding(signal)

        # Find most similar embedding in the database
        recognized_phone, similarity_score = find_most_similar_embedding(
            input_embedding, phone_number=phone_number
        )

        print(recognized_phone, similarity_score)

        if not recognized_phone:
            return jsonify({"message": "Authentication Failed: No match found."}), 401

        # Verify transcription and get user info
        transcription_match, similarity_percentage, person_name = verify_transcription_and_get_user_info(
            audio_path, recognized_phone
        )

        print(transcription_match, similarity_percentage, person_name)

        if transcription_match:
            return jsonify({
                "message": "Authentication Successful",
                "similarity_score": similarity_score,
                "transcription_similarity": similarity_percentage,
                "phone_number": recognized_phone,
                "person_name": person_name,
            }), 200
        else:
            return jsonify({"message": "Authentication Failed: Transcription does not match."}), 401

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route("/tts", methods=["POST"])
def speak():
    data = request.json
    if not data or "text" not in data:
        return {"error": "Please provide 'text' in JSON body"}, 400
    
    text = data["text"]
    print(text)
    voice = data["voice"]
    language = data["language"]
    output_file = text_to_speech(text, voice, language)
    return send_file(output_file, as_attachment=True)

@app.route("/tts-options", methods=["GET"])
def speechOptions():
    options = {
        "languages": {
            "en-US": {"name": "English (US)", "voices": ["male", "female"]},
            "en-UK": {"name": "English (UK)", "voices": ["male", "female"]},
            "en-IN": {"name": "English (India)", "voices": ["male", "female"]},
            "hi-IN": {"name": "Hindi", "voices": ["male", "female"]},
            "ta-IN": {"name": "Tamil", "voices": ["female"]},
            "te-IN": {"name": "Telugu", "voices": ["female"]},
            "kn-IN": {"name": "Kannada", "voices": ["female"]},
            "mr-IN": {"name": "Marathi", "voices": ["female"]},
            "bh-IN": {"name": "Bhojpuri", "voices": ["female"]},
            "bn-IN": {"name": "Bengali", "voices": ["female"]},
        }
    }
    return jsonify(options), 200
    
# Run Flask app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
