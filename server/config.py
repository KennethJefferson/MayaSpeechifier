"""Server configuration for Maya1 Speechify API."""
import os
from typing import Optional


class Config:
    """Configuration class for Maya1 Speechify server."""

    # Model settings
    MODEL_NAME: str = "maya-research/maya1"
    DEVICE: str = "cuda"  # Use GPU
    MAX_MODEL_LEN: int = 2048  # Max tokens per generation
    CHUNK_SIZE: int = 1500  # Conservative chunk size to stay under limit

    # vLLM settings
    TENSOR_PARALLEL_SIZE: int = 1  # Number of GPUs for tensor parallelism
    GPU_MEMORY_UTILIZATION: float = 0.85  # Use up to 85% of GPU memory
    DTYPE: str = "bfloat16"  # BF16 for Maya1

    # Generation parameters
    TEMPERATURE: float = 0.4
    TOP_P: float = 0.9
    REPETITION_PENALTY: float = 1.1
    MAX_NEW_TOKENS: int = 2048

    # Audio settings
    SAMPLE_RATE: int = 24000  # 24kHz as per Maya1 spec
    AUDIO_FORMAT: str = "mp3"
    MP3_BITRATE: str = "192k"

    # API settings
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))

    # Default voice description
    DEFAULT_VOICE_DESCRIPTION: str = "neutral, conversational, clear"

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    @classmethod
    def get_voice_prompt(cls, description: Optional[str] = None) -> str:
        """Generate voice description prompt."""
        desc = description or cls.DEFAULT_VOICE_DESCRIPTION
        return f'<description="{desc}">'
