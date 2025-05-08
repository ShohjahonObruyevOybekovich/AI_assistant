
from aiogram import Bot, Dispatcher, types
from aiogram.types import FSInputFile
import requests
import os
from decouple import config

STT_API_KEY = config("STT_API_KEY")
# STT function
def stt( file_path):
    api_key = STT_API_KEY
    url = 'https://uzbekvoice.ai/api/v1/stt'
    headers = {
        "Authorization": api_key
    }
    files = {
        "file": ("audio.mp3", open(file_path, "rb")),
    }
    data = {
        "return_offsets": "true",
        "run_diarization": "false",
        "language": "uz",
        "blocking": "true",
    }

    try:
        response = requests.post(url, headers=headers, files=files, data=data)
        if response.status_code == 200:
            return response.json()
        else:
            return f"STT failed: {response.status_code} - {response.text}"
    except requests.exceptions.Timeout:
        return "STT request timed out."