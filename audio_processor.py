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
    def create_spectrogram_xc(audio_buffer: io.BytesIO) -> plt.Figure:
        try:
            # 1) Read WAV
            sample_rate, samples = wavfile.read(audio_buffer)
            if samples.ndim > 1:
                samples = samples[:, 0]  # mono
            # Cast to float32 in [-1,1] if PCM ints
            if np.issubdtype(samples.dtype, np.integer):
                max_val = np.iinfo(samples.dtype).max
                samples = samples.astype(np.float32) / max_val

            # 2) STFT params (XC-like for birdsong)
            # Hann window, relatively long window for better freq detail on whistles
            nperseg = 1024  # try 1024–2048 for more freq resolution
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

            # 3) Convert to dB and clamp dynamic range (XC/Audacity/Praat often ~70–80 dB)
            eps = 1e-12
            Sxx_db = 10 * np.log10(Sxx + eps)
            vmax = np.max(Sxx_db)
            dyn_range = 80.0  # try 60–80 dB
            vmin = vmax - dyn_range
            Sxx_db = np.clip(Sxx_db, vmin, vmax)

            # 4) Limit frequency axis to ~12 kHz (most passerine content)
            fmax = 12000  # Hz
            fmask = freqs <= fmax
            freqs_plot = freqs[fmask]
            Sxx_db_plot = Sxx_db[fmask, :]

            # 5) Plot: grayscale reversed (bright = strong), clean axes
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
            ax.set_title("Spectrogram")
            cbar = plt.colorbar(im, ax=ax, pad=0.01)
            cbar.ax.invert_yaxis()
            cbar.set_label("Power (dB)")

            # Aesthetic tweaks like XC: tight layout, minimal spines
            for spine in ["top", "right"]:
                ax.spines[spine].set_visible(False)
            fig.tight_layout()
            return fig
        except Exception as e:
            logger.error(f"Error while creating spectrogram: {e}")
            raise
