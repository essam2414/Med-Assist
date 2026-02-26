import os
import assemblyai as aai
from dotenv import load_dotenv

load_dotenv()
aai.settings.api_key = os.getenv("ASSEMBLYAI_API_KEY")

try:
    config = aai.TranscriptionConfig(
        speaker_labels=True,
        speakers_expected=2,
        speech_models=["universal-2"]
    )
    print("SUCCESS: speech_models accepted.")
except Exception as e:
    print(f"FAILED with speech_models: {e}")
    try:
        config = aai.TranscriptionConfig(
            speaker_labels=True,
            speakers_expected=2,
            speech_model=aai.SpeechModel.universal
        )
        print("SUCCESS: speech_model accepted.")
    except Exception as e2:
        print(f"FAILED with speech_model: {e2}")
