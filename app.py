import os
from flask import Flask, request, jsonify
from flask_cors import cross_origin, CORS
from utilities.audio_utils import process_audio, generate_embedding, transcribe_audio
from utilities.dbUtils import find_most_similar_embedding, verify_transcription_and_get_user_info, register_user_in_db
from utilities.testDbConnection import test_connection
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
    Registers a user by storing voice embeddings and transcription in the database.
    """
    audio_file = request.files.get("audio")
    person_name = request.form.get("name")
    phone_number = request.form.get("phone_number")
    feedback_type = request.form.get("feedback_type")

    if not audio_file or not person_name or not phone_number or not feedback_type:
        return jsonify({"error": "Missing required parameters."}), 400
    
    audio_path = f"audit/registration/{audio_file.filename}"
    audio_file.save(audio_path)
    if feedback_type == "correct":
        try:
            # Process audio
            signal = process_audio(audio_path)

            # Generate embedding
            embedding = generate_embedding(signal)

            # Transcribe audio
            transcription = transcribe_audio(audio_path)

            # Register the user (storing both embedding and transcription)
            register_user_in_db(person_name, phone_number, embedding, transcription)

            return jsonify({"message": "User feedback registered successfully."}), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500
        
    else:
        return jsonify({"message": "Thank you for helping us improve."}), 204

    
@app.route("/register", methods=["POST"])
@cross_origin(origins=['*'])
def register_user():
    """
    Registers a user by storing voice embeddings and transcription in the database.
    """
    audio_file = request.files.get("audio")
    person_name = request.form.get("name")
    phone_number = request.form.get("phone_number")

    if not audio_file or not person_name or not phone_number:
        return jsonify({"error": "Missing required parameters."}), 400

    audio_path = f"audit/registration/{audio_file.filename}"
    audio_file.save(audio_path)

    try:
        # Process audio
        signal = process_audio(audio_path)

        # Generate embedding
        embedding = generate_embedding(signal)

        # Transcribe audio
        transcription = transcribe_audio(audio_path)

        # Register the user (storing both embedding and transcription)
        register_user_in_db(person_name, phone_number, embedding, transcription)

        return jsonify({"message": "User registered successfully.", "transcription": transcription}), 200
    except Exception as e:
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

    audio_path = f"audit/recognition/{audio_file.filename}"
    audio_file.save(audio_path)

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
# Run Flask app
if __name__ == "__main__":
    cert_file = './certificates/backend.crt'
    key_file = './certificates/backend.key'
    app.run(host="0.0.0.0", port=5002, debug=False, ssl_context=(cert_file, key_file))
