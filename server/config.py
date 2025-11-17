"""Server configuration for Maya1 Speechify API."""
import os
import logging
from pathlib import Path
from typing import Optional

from config_schema import AppConfig

logger = logging.getLogger(__name__)


class ConfigLoader:
    """Configuration loader singleton."""

    _instance: Optional[AppConfig] = None
    _loaded: bool = False

    @classmethod
    def load(cls, config_path: Optional[str] = None) -> AppConfig:
        """
        Load configuration from JSON file.

        Args:
            config_path: Path to config.json file. If None, searches in:
                1. CONFIG_PATH environment variable
                2. ./config.json (current directory)
                3. Uses default values from schema

        Returns:
            AppConfig instance
        """
        if cls._loaded and cls._instance is not None:
            return cls._instance

        # Determine config path
        if config_path is None:
            config_path = os.getenv("CONFIG_PATH")

        if config_path is None:
            # Try current directory
            default_path = Path(__file__).parent / "config.json"
            if default_path.exists():
                config_path = str(default_path)

        # Load configuration
        if config_path and Path(config_path).exists():
            logger.info(f"Loading configuration from {config_path}")
            try:
                cls._instance = AppConfig.from_json(config_path)
                logger.info("Configuration loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load config from {config_path}: {e}")
                logger.info("Using default configuration")
                cls._instance = AppConfig()
        else:
            if config_path:
                logger.warning(f"Config file not found: {config_path}")
            logger.info("Using default configuration")
            cls._instance = AppConfig()

        # Override with environment variables
        cls._apply_env_overrides()

        cls._loaded = True
        return cls._instance

    @classmethod
    def _apply_env_overrides(cls):
        """Apply environment variable overrides to configuration."""
        if cls._instance is None:
            return

        # Server overrides
        if "HOST" in os.environ:
            cls._instance.server.host = os.environ["HOST"]
        if "PORT" in os.environ:
            cls._instance.server.port = int(os.environ["PORT"])
        if "LOG_LEVEL" in os.environ:
            cls._instance.server.log_level = os.environ["LOG_LEVEL"]

        # Model pool overrides
        if "NUM_INSTANCES" in os.environ:
            cls._instance.model_pool.num_instances = int(os.environ["NUM_INSTANCES"])
        if "GPU_MEMORY_PER_INSTANCE" in os.environ:
            cls._instance.model_pool.gpu_memory_per_instance = float(
                os.environ["GPU_MEMORY_PER_INSTANCE"]
            )

        logger.debug("Applied environment variable overrides")

    @classmethod
    def get(cls) -> AppConfig:
        """Get the current configuration instance."""
        if not cls._loaded or cls._instance is None:
            return cls.load()
        return cls._instance

    @classmethod
    def reload(cls, config_path: Optional[str] = None) -> AppConfig:
        """Reload configuration from file."""
        cls._loaded = False
        cls._instance = None
        return cls.load(config_path)


# Global config instance
# Usage: from config import config
config: AppConfig = ConfigLoader.load()


# Backward compatibility: Expose as class attributes for existing code
class Config:
    """
    Backward-compatible configuration class.

    DEPRECATED: Use the 'config' instance directly instead.
    This class is provided for backward compatibility only.
    """

    @classmethod
    def _get_config(cls) -> AppConfig:
        """Get current config instance."""
        return ConfigLoader.get()

    # Model settings
    @property
    def MODEL_NAME(cls) -> str:
        return cls._get_config().model.name

    @property
    def DEVICE(cls) -> str:
        return cls._get_config().model.device

    @property
    def MAX_MODEL_LEN(cls) -> int:
        return cls._get_config().model.max_model_len

    @property
    def CHUNK_SIZE(cls) -> int:
        return cls._get_config().text_processing.chunk_size

    # vLLM settings
    @property
    def TENSOR_PARALLEL_SIZE(cls) -> int:
        return cls._get_config().model_pool.tensor_parallel_size

    @property
    def GPU_MEMORY_UTILIZATION(cls) -> float:
        return cls._get_config().model_pool.gpu_memory_per_instance

    @property
    def DTYPE(cls) -> str:
        return cls._get_config().model.dtype

    # Generation parameters
    @property
    def TEMPERATURE(cls) -> float:
        return cls._get_config().generation.temperature

    @property
    def TOP_P(cls) -> float:
        return cls._get_config().generation.top_p

    @property
    def REPETITION_PENALTY(cls) -> float:
        return cls._get_config().generation.repetition_penalty

    @property
    def MAX_NEW_TOKENS(cls) -> int:
        return cls._get_config().generation.max_new_tokens

    # Audio settings
    @property
    def SAMPLE_RATE(cls) -> int:
        return cls._get_config().audio.sample_rate

    @property
    def AUDIO_FORMAT(cls) -> str:
        return cls._get_config().audio.format

    @property
    def MP3_BITRATE(cls) -> str:
        return cls._get_config().audio.bitrate

    # API settings
    @property
    def HOST(cls) -> str:
        return cls._get_config().server.host

    @property
    def PORT(cls) -> int:
        return cls._get_config().server.port

    # Default voice description
    @property
    def DEFAULT_VOICE_DESCRIPTION(cls) -> str:
        return cls._get_config().voice.default_description

    # Logging
    @property
    def LOG_LEVEL(cls) -> str:
        return cls._get_config().server.log_level

    @classmethod
    def get_voice_prompt(cls, description: Optional[str] = None) -> str:
        """Generate voice description prompt."""
        return cls._get_config().get_voice_prompt(description)
