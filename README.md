# 🦜 Bird Detection Monitor

A real-time bird detection monitoring system built with Streamlit that connects to a Raspberry Pi running BirdNET for automated bird species identification from audio recordings.

## 📋 Features

- **Real-time Monitoring**: Live bird detection data from Raspberry Pi
- **Audio Analysis**: Play and analyze detected bird calls with spectrograms
- **System Metrics**: Monitor Raspberry Pi system health (CPU, RAM, disk, temperature)
- **Date Filtering**: Browse detections by specific dates
- **Audio Caching**: Efficient local caching of audio files
- **Species Statistics**: View detection counts and unique species per day
- **Interactive UI**: Select detections to view corresponding audio segments

## 🏗️ System Architecture

```
┌─────────────────┐    HTTP API     ┌──────────────────┐
│   Streamlit     │◄────────────────┤  Raspberry Pi    │
│   Dashboard     │                 │   (BirdNET)      │
└─────────────────┘                 └──────────────────┘
        │                                    │
        ▼                                    ▼
┌─────────────────┐                 ┌──────────────────┐
│ Audio Cache     │                 │ Audio Files      │
│ (local storage) │                 │ (HDF5 database)  │
└─────────────────┘                 └──────────────────┘
```

## 📁 Project Structure

```
bird_detection_monitor/
├── app.py                      # Main Streamlit application
├── config.py                   # Configuration settings
├── api_client.py              # Raspberry Pi API client
├── audio_processor.py         # Audio processing and caching
├── data_processor.py          # Data transformation and analysis
├── ui_components.py           # Reusable UI components
├── utils.py                   # Generic utility functions
├── requirements.txt           # Python dependencies
├── README.md                  # This file
│
├── data/                      # Data directory
│   ├── downloaded_audio/      # Cached audio files
│   └── species_confidence.csv # Species confidence thresholds│
```

## 🚀 Installation

### Prerequisites

- Python 3.8+
- Raspberry Pi with BirdNET running
- Network access to the Raspberry Pi

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd bird_detection_monitor
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure settings**
   Edit `config.py` to match your Raspberry Pi IP address:
   ```python
   RASPBERRY_PI_IP = "YOUR_PI_IP_ADDRESS"
   ```

5. **Run the application**
   ```bash
   streamlit run app.py
   ```

## 🔧 Configuration

### Main Settings (`config.py`)

| Setting | Description | Default |
|---------|-------------|---------|
| `RASPBERRY_IP` | IP address of your Raspberry Pi | `"YOUR_PI_IP_ADDRESS"` |
| `REQUEST_TIMEOUT` | API request timeout in seconds | `5` |
| `CACHE_TTL_DETECTIONS` | Detection cache TTL in seconds | `15` |
| `CACHE_TTL_METRICS` | Metrics cache TTL in seconds | `5` |
| `AUDIO_CACHE_DIR` | Local audio cache directory | `"data/downloaded_audio"` |

### Custom Confidence Thresholds

Create a `species_confidence.csv` file to set custom confidence thresholds per species:

```csv
species,threshold
Fringilla coelebs_Common Chaffinch,0.308
Phylloscopus collybita_Common Chiffchaff,0.109
Sylvia atricapilla_Eurasian Blackcap,0.142
```

## 📊 API Endpoints

The application expects these endpoints on your Raspberry Pi:

### GET `/api/system_metrics`
Returns system health metrics:
```json
{
  "cpu_usage": 15.2,
  "ram_usage": 45.8,
  "disk_usage": 32.1,
  "temperature": 42.5
}
```

### GET `/api/birds/classifications?since={timestamp}`
Returns bird detections since timestamp:
```json
[
  {
    "timestamp": 1634567890,
    "offset": 3.0,
    "species": "Fringilla coelebs_Common Chaffinch",
    "confidence": 0.89
  }
]
```

### GET `/api/birds/audio/{timestamp}`
Returns WAV audio file for the given timestamp.

## 🖥️ Usage

1. **Launch the application**: `streamlit run app.py`
2. **Select a date**: Use the sidebar date picker
3. **View detections**: Browse the detection table
4. **Analyze audio**: Click on any detection to hear audio and view spectrogram
5. **Monitor system**: Check Raspberry Pi health in the metrics section

## 🔧 Features Details

### Audio Processing
- Automatic download and caching of audio files
- 3-second audio segment extraction around detection
- Spectrogram generation using SciPy
- Memory-efficient audio handling

### Data Processing
- Real-time data transformation from API
- Date/time conversion with timezone support
- Confidence threshold filtering
- Species statistics and aggregation

### Caching Strategy
- Audio files cached locally to reduce Pi load
- Streamlit data caching for API responses
- Configurable cache TTL values
- Manual cache clearing functionality

## 🐛 Troubleshooting

### Common Issues

**Connection Error**: `Error fetching detections`
- Check Raspberry Pi IP address in `config.py`
- Ensure Pi is on the same network
- Verify BirdNET service is running on Pi

**Audio Not Playing**: `Error processing audio`
- Check audio cache directory permissions
- Verify WAV file format on Pi
- Try clearing audio cache

**High Memory Usage**
- Clear audio cache regularly
- Reduce cache TTL values
- Limit date range for large datasets

### Logging

Enable debug logging by setting:
```python
logging.basicConfig(level=logging.DEBUG)
```

## 🙏 Acknowledgments

- [BirdNET-Analyzer](https://github.com/birdnet-team/BirdNET-Analyzer) for bird detection
- [Streamlit](https://streamlit.io/) for the web framework
- [SciPy](https://scipy.org/) for audio processing

---