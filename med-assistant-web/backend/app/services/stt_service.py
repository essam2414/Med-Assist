import os
import assemblyai as aai
from dotenv import load_dotenv

load_dotenv()

# Set up AssemblyAI client with the API key from environment
aai.settings.api_key = os.getenv("ASSEMBLYAI_API_KEY")

def transcribe_audio(file_path: str) -> list[dict]:
    """
    Takes an audio file path, sends it to AssemblyAI for transcription with 
    speaker diarization enabled (max 2 speakers), and returns a list of dictionaries 
    containing speaker labels, text, and timestamps.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Audio file not found at {file_path}")

    # Configure transcription options for diarization
    config = aai.TranscriptionConfig(
        speaker_labels=True,
        speakers_expected=2,
        speech_models=["universal-2"]
    )
    
    transcriber = aai.Transcriber()
    transcript = transcriber.transcribe(file_path, config=config)
    
    if transcript.status == aai.TranscriptStatus.error:
        raise Exception(f"AssemblyAI Transcription failed: {transcript.error}")
        
    # Process the utterances (speaker segments)
    segments = []
    if transcript.utterances:
        for utterance in transcript.utterances:
            segments.append({
                "speaker": f"Speaker {utterance.speaker}", # 'Speaker A', 'Speaker B'
                "text": utterance.text,
                "start_time": utterance.start / 1000.0, # Convert ms to seconds
                "end_time": utterance.end / 1000.0
            })
    else:
        # Fallback if no specific utterances are detected
        segments.append({
            "speaker": "Speaker A",
            "text": transcript.text,
            "start_time": 0.0,
            "end_time": getattr(transcript, 'audio_duration', 0.0)
        })
        
    return segments
