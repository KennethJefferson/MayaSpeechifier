"""Configuration schema using Pydantic for validation."""
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class ServerConfig(BaseModel):
    """Server networking configuration."""
    host: str = Field(default="0.0.0.0", description="Server host address")
    port: int = Field(default=8000, ge=1, le=65535, description="Server port")
    workers: int = Field(default=1, ge=1, description="Number of Uvicorn workers")
    log_level: str = Field(default="INFO", description="Logging level")

    @field_validator('log_level')
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        allowed = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        v_upper = v.upper()
        if v_upper not in allowed:
            raise ValueError(f"log_level must be one of {allowed}")
        return v_upper


class CORSConfig(BaseModel):
    """CORS configuration."""
    enabled: bool = Field(default=True, description="Enable CORS")
    allowed_origins: List[str] = Field(default=["*"], description="Allowed origins")
    allowed_methods: List[str] = Field(default=["GET", "POST"], description="Allowed HTTP methods")
    allowed_headers: List[str] = Field(default=["*"], description="Allowed headers")
    allow_credentials: bool = Field(default=False, description="Allow credentials")


class ModelConfig(BaseModel):
    """Model configuration."""
    name: str = Field(default="maya-research/maya1", description="Model name or path")
    device: str = Field(default="cuda", description="Device to run model on")
    dtype: str = Field(default="bfloat16", description="Model data type")
    max_model_len: int = Field(default=2048, ge=512, description="Maximum model sequence length")
    trust_remote_code: bool = Field(default=True, description="Trust remote code for model")

    @field_validator('dtype')
    @classmethod
    def validate_dtype(cls, v: str) -> str:
        """Validate dtype."""
        allowed = ['float16', 'bfloat16', 'float32']
        if v not in allowed:
            raise ValueError(f"dtype must be one of {allowed}")
        return v


class ModelPoolConfig(BaseModel):
    """Model pool configuration for parallel processing."""
    num_instances: int = Field(
        default=3,
        ge=1,
        le=8,
        description="Number of model instances to run in parallel"
    )
    gpu_memory_per_instance: float = Field(
        default=0.28,
        ge=0.1,
        le=0.9,
        description="GPU memory fraction per instance (e.g., 0.28 = 28%)"
    )
    tensor_parallel_size: int = Field(
        default=1,
        ge=1,
        description="Number of GPUs for tensor parallelism per instance"
    )

    @field_validator('num_instances')
    @classmethod
    def validate_instances(cls, v: int) -> int:
        """Validate number of instances."""
        if v > 4:
            import warnings
            warnings.warn(
                f"Running {v} instances may exceed GPU memory. "
                "Recommended: 1-3 instances for single RTX 4090."
            )
        return v


class GenerationConfig(BaseModel):
    """Text generation parameters."""
    temperature: float = Field(default=0.4, ge=0.0, le=2.0, description="Sampling temperature")
    top_p: float = Field(default=0.9, ge=0.0, le=1.0, description="Nucleus sampling probability")
    repetition_penalty: float = Field(default=1.1, ge=1.0, le=2.0, description="Repetition penalty")
    max_new_tokens: int = Field(default=2048, ge=128, description="Maximum tokens to generate")


class AudioConfig(BaseModel):
    """Audio output configuration."""
    sample_rate: int = Field(default=24000, description="Audio sample rate (Hz)")
    format: str = Field(default="mp3", description="Audio output format")
    bitrate: str = Field(default="192k", description="MP3 bitrate")

    @field_validator('format')
    @classmethod
    def validate_format(cls, v: str) -> str:
        """Validate audio format."""
        allowed = ['mp3', 'wav']
        if v.lower() not in allowed:
            raise ValueError(f"format must be one of {allowed}")
        return v.lower()

    @field_validator('sample_rate')
    @classmethod
    def validate_sample_rate(cls, v: int) -> int:
        """Validate sample rate."""
        allowed = [16000, 22050, 24000, 44100, 48000]
        if v not in allowed:
            raise ValueError(f"sample_rate must be one of {allowed}")
        return v


class TextProcessingConfig(BaseModel):
    """Text processing configuration."""
    chunk_size: int = Field(
        default=1500,
        ge=500,
        le=4000,
        description="Maximum tokens per text chunk"
    )
    max_file_size_mb: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Maximum file size in MB"
    )


class VoiceConfig(BaseModel):
    """Voice configuration."""
    default_description: str = Field(
        default="neutral, conversational, clear",
        description="Default voice description"
    )


class RunPodConfig(BaseModel):
    """RunPod deployment configuration."""
    pod_name: str = Field(default="", description="RunPod pod name")
    pod_id: str = Field(default="", description="RunPod pod ID")
    ssh_host: str = Field(default="", description="SSH hostname for RunPod")
    ssh_user: str = Field(default="", description="SSH username for RunPod")
    ssh_tcp_host: str = Field(default="", description="Direct TCP SSH host IP")
    ssh_tcp_port: int = Field(default=22, description="Direct TCP SSH port")
    ssh_tcp_user: str = Field(default="root", description="Direct TCP SSH username")
    direct_tcp_address: str = Field(default="", description="Direct TCP connection address")
    direct_tcp_port: int = Field(default=22, description="Direct TCP port")
    http_proxy_url: str = Field(default="", description="HTTP proxy URL for services")
    jupyter_port: int = Field(default=8888, description="Jupyter Lab port")
    service_port: int = Field(default=7777, description="Main service port")


class AppConfig(BaseModel):
    """Root application configuration."""
    server: ServerConfig = Field(default_factory=ServerConfig)
    cors: CORSConfig = Field(default_factory=CORSConfig)
    model: ModelConfig = Field(default_factory=ModelConfig)
    model_pool: ModelPoolConfig = Field(default_factory=ModelPoolConfig)
    generation: GenerationConfig = Field(default_factory=GenerationConfig)
    audio: AudioConfig = Field(default_factory=AudioConfig)
    text_processing: TextProcessingConfig = Field(default_factory=TextProcessingConfig)
    voice: VoiceConfig = Field(default_factory=VoiceConfig)
    runpod: RunPodConfig = Field(default_factory=RunPodConfig)

    @classmethod
    def from_json(cls, path: str) -> "AppConfig":
        """Load configuration from JSON file."""
        import json
        with open(path, 'r') as f:
            data = json.load(f)
        return cls(**data)

    def get_voice_prompt(self, description: Optional[str] = None) -> str:
        """Generate voice description prompt."""
        desc = description or self.voice.default_description
        return f'<description="{desc}">'
