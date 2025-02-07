import psycopg2
import numpy as np
from utilities.testDbConnection import DB_CONFIG
from psycopg2.extras import RealDictCursor
from utilities.audio_utils import transcribe_audio
from difflib import SequenceMatcher
from psycopg2.extras import DictCursor  # Import DictCursor



def connect_db():
    return psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)

def register_user_in_db(person_name, phone_number, embedding, transcription):
    """
    Registers the user by inserting both the voice embedding and transcription into the database.
    """
    conn = connect_db()
    cur = conn.cursor()
    
    # Insert person data (if not already exists)
    cur.execute(
        "INSERT INTO person_phone_mapping (person_name, phone_number) VALUES (%s, %s) ON CONFLICT DO NOTHING",
        (person_name, phone_number),
    )
    
    # Insert the voice embedding along with transcription into the voice_embeddings table
    cur.execute(
        """
        INSERT INTO voice_embeddings (embedding, transcription, phone_number)
        VALUES (%s, %s, %s)
        """,
        (embedding, transcription, phone_number),
    )
    
    conn.commit()
    conn.close()


def find_most_similar_embedding(query_embedding, phone_number=None):
    conn = connect_db()
    cur = conn.cursor(cursor_factory=DictCursor)

    try:
        if isinstance(query_embedding, np.ndarray):
            query_embedding = query_embedding.tolist()

        query_embedding = f'[{",".join(map(str, query_embedding))}]'

        if phone_number:
            query = """
                SELECT 
                    phone_number, 
                    embedding <=> %s::vector AS distance  
                FROM 
                    voice_embeddings
                WHERE 
                    phone_number = %s
                ORDER BY 
                    distance ASC;
            """
            cur.execute(query, (query_embedding, phone_number))
        else:
            query = """
                SELECT 
                    phone_number,
                    embedding <=> %s::vector AS distance  
                FROM 
                    voice_embeddings
                ORDER BY 
                    distance ASC;
            """
            cur.execute(query, (query_embedding,))

        results = cur.fetchall()
        conn.close()

        print("Closest:", results[0])
        print("Farthest:", results[-1])
        
        if results:
            first_result = results[0]
            return first_result['phone_number'], 1 - first_result['distance']
        else:
            return None, None, []

    except Exception as e:
        conn.close()
        print(f"Error details: {str(e)}")
        raise


def verify_transcription_and_get_user_info(input_audio_path, recognized_phone):
    """
    Verifies the transcription of the input audio against the stored transcriptions 
    and fetches user information from the database.
    
    Returns a tuple (transcription_match, max_similarity_percentage, person_name).
    """
    # Transcribe the input audio
    input_transcription = transcribe_audio(input_audio_path)

    # Fetch stored transcriptions and user details from the database
    conn = connect_db()
    cur = conn.cursor()

    # Fetch all stored transcriptions for the recognized phone number
    try:
        cur.execute(
            "SELECT transcription FROM voice_embeddings WHERE phone_number = %s",
            (recognized_phone,)
        )
        stored_transcriptions = cur.fetchall()

    except Exception as e:
        conn.close()
        print(f"Error details: {str(e)}")
        print(f"Exception type: {type(e)}")
        raise 

    # Calculate similarity for each stored transcription
    max_similarity_percentage = 0.0
    transcription_match = False
    for stored_transcription_row in stored_transcriptions:
        stored_transcription = stored_transcription_row['transcription']
        similarity_percentage = SequenceMatcher(None, input_transcription, stored_transcription).ratio() * 100

        # Track the highest similarity percentage
        if similarity_percentage > max_similarity_percentage:
            max_similarity_percentage = similarity_percentage
        
        # If similarity is above the threshold, we consider it a match
        if similarity_percentage >= 5:
            transcription_match = True
    print(similarity_percentage)
    # Fetch the person's name from the phone number
    try:
        cur.execute(
            "SELECT person_name FROM person_phone_mapping WHERE phone_number = %s",
            (recognized_phone,)
        )
        user_info = cur.fetchone()
        print(user_info)

    except Exception as e:
        conn.close()
        print(f"Error details: {str(e)}")
        print(f"Exception type: {type(e)}")
        raise 

    finally:
        conn.close()

    return transcription_match, max_similarity_percentage, user_info["person_name"] if user_info else None

def check_if_registered(phone_number):
    try:
        conn = connect_db()
        cursor = conn.cursor()
        sql_get_name = f"""
            SELECT person_name 
            FROM person_phone_mapping 
            WHERE phone_number = '{phone_number}';
        """

        print(sql_get_name)  # Print the final query before execution

        cursor.execute(sql_get_name)

        results = cursor.fetchall()
        conn.close()

        print(results[0])
        if results:
            first = results[0]  # If a name is found, use it
            print (first['person_name'])
            return first['person_name']
        else:
            print(f"Error: No name found for phone number {phone_number}.")
            return None
        
    except Exception as e:
        print(f"Error while checking if user is registered: {e}")
        return None

def insert_feedback (embedding, actual_phone_number, predicted_phone_number, confidence_score, feedback_type):
    conn = connect_db()
    cursor = conn.cursor()

    if confidence_score=="" and predicted_phone_number=="":
        confidence_score=0
        predicted_phone_number="Unpredicted"

    # Convert embedding to the pgvector format
    embedding_str = f"[{','.join(map(str, embedding))}]"

    try:

        # Insert feedback record
        cursor.execute("""
            INSERT INTO feedback (actual_phone_number, predicted_phone_number, confidence_score, embedding, feedback_type)
            VALUES (%s, %s, %s, %s, %s);
        """, (actual_phone_number, predicted_phone_number, confidence_score, embedding_str, feedback_type))
        
        conn.commit()
        print("Feedback successfully inserted.")
    
    except Exception as e:
        print(f"Error inserting feedback: {e}")
        conn.rollback()
        raise
    
    finally:
        cursor.close()
        conn.close()

