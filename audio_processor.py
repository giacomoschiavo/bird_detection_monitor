from config import Config
import logging
from pathlib import Path
from api_client import APIClient
from pydub import AudioSegment
import streamlit as st
import matplotlib.pyplot as plt
from scipy.io import wavfile
from scipy import signal
import numpy as np
import io
from scipy.signal import spectrogram
from scipy.io import wavfile
from scipy import signal
import logging

import matplotlib.patches as patches


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AudioProcessor:
    
    @staticmethod
    def get_cached_audio_path(filename: int) -> Path:
        return Config.AUDIO_CACHE_DIR / f"{filename}.wav"

    @staticmethod
    def download_and_cache_audio(filename: int) -> bool:
        file_path = AudioProcessor.get_cached_audio_path(filename)
        if file_path.exists():
            return True
        with st.spinner("Downloading audio..."):
            audio_data = APIClient.fetch_audio(filename)
            if audio_data:
                try:
                    file_path.write_bytes(audio_data)
                    logger.info(f"Audio {filename}.wav has been saved.")
                    return True
                except Exception as e:
                    logger.error(f"Error while downloading data: {e}")
                    return False
                
    @staticmethod
    def extract_audio_segment(audio_data: bytes) -> io.BytesIO:
        try:
            audio_buffer = io.BytesIO(audio_data)
            full_audio = AudioSegment.from_wav(audio_buffer)

            # start_time = int(offset * 1000)
            # end_time = int(start_time + duration * 1000)
            # trimmed_audio = full_audio[start_time:end_time]
            trimmed_audio = full_audio[:]

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
            im = ax.pcolormesh(times, frequencies, 10 * np.log10(Sxx + 1e-10), shading='gouraud', cmap="gray_r")
            ax.set_ylabel('Frequency (Hz)')
            ax.set_xlabel('Time (s)')
            ax.set_title('Spectrogram')
            plt.colorbar(im, ax=ax, label="Power (dB)")
            return fig
        except Exception as e:
            logger.error("Error while creating spectrogram: {e}")
            raise

    @staticmethod
    def create_spectrogram_xc(audio_buffer: io.BytesIO, prediction_time: float, prediction_duration: float) -> plt.Figure:
        try:
            sample_rate, samples = wavfile.read(audio_buffer)
            if samples.ndim > 1:
                samples = samples[:, 0]  # mono
            # Cast to float32 in [-1,1] if PCM ints
            # if np.issubdtype(samples.dtype, np.integer):
            #     max_val = np.iinfo(samples.dtype).max
            #     samples = samples.astype(np.float32) / max_val

            # STFT params
            # Hann window, relatively long window for better freq detail on whistles
            nperseg = 1024 
            noverlap = int(nperseg * 0.75)
            window = "hann"

            freqs, times, Sxx = signal.spectrogram(
                samples,
                fs=sample_rate,
                window=window,
                nperseg=nperseg,
                noverlap=noverlap,
                nfft=nperseg,
                mode="psd",
                scaling="density"
            )

            # convert to dB and clamp dynamic range (70–80 dB)
            eps = 1e-12
            Sxx_db = 10 * np.log10(Sxx + eps)
            vmax = np.max(Sxx_db)
            dyn_range = 80.0  # try 60–80 dB
            vmin = vmax - dyn_range
            Sxx_db = np.clip(Sxx_db, vmin, vmax)

            # limit frequency 12 kHz
            fmax = 12000  # Hz
            fmask = freqs <= fmax
            freqs_plot = freqs[fmask]
            Sxx_db_plot = Sxx_db[fmask, :]

            fig, ax = plt.subplots(figsize=(12, 6))
            im = ax.pcolormesh(
                times,
                freqs_plot,
                Sxx_db_plot,
                # shading="gouraud",
                cmap="gray_r",
                vmin=vmin,
                vmax=vmax
            )
            ax.set_ylabel("Frequency (Hz)")
            ax.set_xlabel("Time (s)")
            rect = patches.Rectangle(
                (prediction_time, freqs_plot.min()),
                prediction_duration,
                freqs_plot.max() - freqs_plot.min(),
                linewidth=1,
                edgecolor='blue',
                facecolor='none'
            )
            ax.add_patch(rect)


            fig.tight_layout()
            return fig
        except Exception as e:
            logger.error(f"Error while creating spectrogram: {e}")
            raise
