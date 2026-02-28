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
                # Basic check for empty files
                if os.path.getsize(file_path) < 1000: # Less than 1KB is likely just a header
                    return None
                return client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="verbose_json",
                    timestamp_granularities=["word"],
                    language="en",
                    prompt="Medical consultation transcript.",
                    temperature=0
                )
        transcript = await asyncio.to_thread(_transcribe)
        if transcript is None:
            return []
    except Exception as e:
        # If it's a known 'no audio' error or similar, just return empty segments
        if "no audio" in str(e).lower() or "too short" in str(e).lower():
            return []
        print(f"Whisper Error (ignored for live stream): {str(e)}")
        return []
            
    # Process the audio by discrete segments for proper chronological interleaving
    segments_output = []
    
    # Common Whisper Hallucinations to filter out
    BLACKLIST = [
        "for more un videos", "un.org", "subscribe to", "thanks for watching",
        "please like", "thank you for", "i'm sorry", "watching!", "you!"
    ]

    # Use word-level data for precise sentence/pause grouping
    if hasattr(transcript, 'words') and transcript.words:
        current_segment_words = []
        segment_start = None
        last_word_end = None

        for word_info in transcript.words:
            # Whisper verbose_json stores words as objects with 'word', 'start', 'end', 'probability'
            word_text = word_info.word
            start = word_info.start
            end = word_info.end
            
            # 1. Detect natural pauses or sentence ends
            # We break segments if:
            # - There's a gap of > 1.2 seconds between words
            # - The previous word ended a sentence (., ?, !)
            if current_segment_words:
                pause_duration = start - last_word_end
                last_text = current_segment_words[-1]
                
                if pause_duration > 1.2 or last_text.strip().endswith(('.', '?', '!')):
                    # Combine current words into a segment
                    text = " ".join(current_segment_words).strip()
                    
                    # Filter hallucinations
                    if not any(phrase in text.lower() for phrase in BLACKLIST):
                        segments_output.append({
                            "speaker": speaker_name or "Speaker A",
                            "text": text,
                            "start_time": segment_start,
                            "end_time": last_word_end
                        })
                    
                    # Reset trackers
                    current_segment_words = []
                    segment_start = None

            if segment_start is None:
                segment_start = start
            
            current_segment_words.append(word_text)
            last_word_end = end

        # Final segment
        if current_segment_words:
            text = " ".join(current_segment_words).strip()
            if not any(phrase in text.lower() for phrase in BLACKLIST):
                segments_output.append({
                    "speaker": speaker_name or "Speaker A",
                    "text": text,
                    "start_time": segment_start,
                    "end_time": last_word_end
                })

    elif hasattr(transcript, 'text') and transcript.text.strip():
        # Fallback if words are missing
        text = transcript.text.strip()
        if not any(phrase in text.lower() for phrase in BLACKLIST):
            segments_output.append({
                "speaker": speaker_name or "Speaker A",
                "text": text,
                "start_time": 0.0,
                "end_time": getattr(transcript, 'duration', 0.0)
            })
        
    return segments_output
