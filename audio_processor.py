from config import Config
import logging
from pathlib import Path
from api_client import APIClient
import io
from pydub import AudioSegment
import streamlit as st
import matplotlib.pyplot as plt
from scipy.io import wavfile
from scipy import signal
import numpy as np


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AudioProcessor:
    
    @staticmethod
    def get_cached_audio_path(timestamp: int) -> Path:
        return Config.AUDIO_CACHE_DIR / f"{timestamp}.wav"

    @staticmethod
    def download_and_cache_audio(timestamp: int) -> bool:
        file_path = AudioProcessor.get_cached_audio_path(timestamp)
        if file_path.exists():
            return True
        with st.spinner("Downloading audio..."):
            audio_data = APIClient.fetch_audio(timestamp)
            if audio_data:
                try:
                    file_path.write_bytes(audio_data)
                    logger.info(f"Audio {timestamp}.wav has been saved.")
                    return True
                except Exception as e:
                    logger.error(f"Error while downloading data: {e}")
                    return False
                
    @staticmethod
    def extract_audio_segment(audio_data: bytes, offset: float, duration: float = 3.0) -> io.BytesIO:
        try:
            audio_buffer = io.BytesIO(audio_data)
            full_audio = AudioSegment.from_wav(audio_buffer)

            start_time = int(offset * 1000)
            end_time = int(start_time + duration * 1000)
            trimmed_audio = full_audio[start_time:end_time]

            output_buffer = io.BytesIO()
            trimmed_audio.export(output_buffer, format="wav")
            output_buffer.seek(0)
            return output_buffer
        except Exception as e:
            logging.error("Error while trying to extract segment from audio: {e}")
            raise

class SpectrogramGenerator:

    @staticmethod
    def create_spectrogram(audio_buffer: io.BytesIO) -> plt.Figure:
        try:
            sample_rate, samples = wavfile.read(audio_buffer)
            if len(samples.shape) > 1:
                samples = samples[:, 0]     # prendi un solo canale se stereo

            frequencies, times, Sxx = signal.spectrogram(samples, fs=sample_rate)
            
            fig, ax = plt.subplots(figsize=(12,6))
            im = ax.pcolormesh(times, frequencies, 10 * np.log10(Sxx + 1e-10), shading='gouraud')
            ax.set_ylabel('Frequency (Hz)')
            ax.set_xlabel('Time (s)')
            ax.set_title('Spectrogram')
            plt.colorbar(im, ax=ax, label="Power (dB)")
            return fig
        except Exception as e:
            logger.error("Error while creating spectrogram: {e}")
            raise
