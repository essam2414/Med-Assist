import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Initialize the OpenAI Client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

import asyncio

async def transcribe_audio_async(file_path: str, speaker_name: str = None) -> list[dict]:
    """
    Takes an audio file path, sends it to OpenAI Whisper asynchronously for fast and accurate transcription,
    and returns a list of dictionaries containing speaker labels, text, and timestamps.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Audio file not found at {file_path}")

    # Use Whisper to transcribe the audio asynchronously 
    try:
        def _transcribe():
            with open(file_path, "rb") as audio_file:
                return client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="verbose_json",
                    timestamp_granularities=["word"]
                )
        transcript = await asyncio.to_thread(_transcribe)
    except Exception as e:
        raise Exception(f"OpenAI Whisper Transcription failed: {str(e)}")
            
    # Process the audio by discrete segments for proper chronological interleaving
    segments_output = []
    
    if hasattr(transcript, 'words') and transcript.words:
        current_sentence = []
        current_start = None
        last_end = None
        
        for word_info in transcript.words:
            # Type hinting mapping for standard OpenAI word object structure
            word = word_info.word
            start = word_info.start
            end = word_info.end
            
            if current_start is None:
                current_start = start
                
            # If there's a significant pause (e.g. > 0.8 seconds) between words,
            # or the previous word ended in a sentence terminating punctuation, 
            # we consider it a new sentence boundary.
            if last_end is not None and (start - last_end > 0.8 or current_sentence[-1].endswith(('.', '?', '!'))):
                segments_output.append({
                    "speaker": speaker_name or "Speaker A",
                    "text": " ".join(current_sentence).strip(),
                    "start_time": current_start,
                    "end_time": last_end
                })
                current_sentence = []
                current_start = start
                
            current_sentence.append(word.strip())
            last_end = end
            
        # Append the final sentence if it exists
        if current_sentence:
            segments_output.append({
                "speaker": speaker_name or "Speaker A",
                "text": " ".join(current_sentence).strip(),
                "start_time": current_start,
                "end_time": last_end
            })
    else:
        # Fallback if no specific segments are detected
        segments_output.append({
            "speaker": speaker_name or "Speaker A",
            "text": transcript.text,
            "start_time": 0.0,
            "end_time": transcript.duration if hasattr(transcript, 'duration') else 0.0
        })
        
    return segments_output
