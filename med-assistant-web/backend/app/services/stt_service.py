import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Initialize the OpenAI client.
# It automatically picks up the OPENAI_API_KEY environment variable.
client = OpenAI()

def transcribe_audio(file_path: str) -> str:
    """
    Takes an audio file path, sends it to the OpenAI Whisper API,
    and returns the transcribed text.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Audio file not found at {file_path}")

    with open(file_path, "rb") as audio_file:
        transcription = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file
        )
    
    return transcription.text
