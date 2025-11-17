"""FastAPI server for Maya1 TTS service."""
import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel, Field
import uvicorn

from config import config
from model_pool import ModelPool
from utils import TextChunker, AudioMerger

# Configure logging
logging.basicConfig(
    level=getattr(logging, config.server.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global instances
model_pool: Optional[ModelPool] = None
text_chunker: Optional[TextChunker] = None
audio_merger: AudioMerger = AudioMerger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for model initialization and cleanup."""
    global model_pool, text_chunker

    logger.info("Starting Maya1 Speechify API server...")
    logger.info(f"Configuration: {config.model_pool.num_instances} model instance(s)")

    # Initialize model pool and utilities
    try:
        model_pool = ModelPool(config)
        text_chunker = TextChunker(max_tokens=config.text_processing.chunk_size)
        logger.info("Server initialization complete")
    except Exception as e:
        logger.error(f"Failed to initialize server: {e}")
        raise

    yield

    # Cleanup
    logger.info("Shutting down server...")


# Initialize FastAPI app
app = FastAPI(
    title="Maya1 Speechify API",
    description="Text-to-Speech API using Maya1 model with parallel processing",
    version="2.0.0",
    lifespan=lifespan
)

# Add CORS middleware if enabled
if config.cors.enabled:
    logger.info("CORS enabled with origins: " + str(config.cors.allowed_origins))
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors.allowed_origins,
        allow_credentials=config.cors.allow_credentials,
        allow_methods=config.cors.allowed_methods,
        allow_headers=config.cors.allowed_headers,
    )


class SynthesizeRequest(BaseModel):
    """Request model for text synthesis."""
    text: str = Field(..., description="Text to synthesize", min_length=1)
    voice_description: Optional[str] = Field(
        None,
        description="Voice characteristics (e.g., 'warm, low pitch, conversational')"
    )


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str
    model: str
    device: str
    num_instances: int
    healthy_instances: int
    gpu_memory_per_instance: str


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint with model pool status."""
    if model_pool is None:
        return HealthResponse(
            status="initializing",
            model=config.model.name,
            device=config.model.device,
            num_instances=0,
            healthy_instances=0,
            gpu_memory_per_instance="N/A"
        )

    health_info = model_pool.health_check()

    return HealthResponse(
        status=health_info["status"],
        model=config.model.name,
        device=config.model.device,
        num_instances=health_info["total_instances"],
        healthy_instances=health_info["healthy_instances"],
        gpu_memory_per_instance=health_info["gpu_memory_per_instance"]
    )


@app.post("/synthesize")
async def synthesize(request: SynthesizeRequest):
    """
    Synthesize speech from text using model pool with round-robin load balancing.

    Args:
        request: SynthesizeRequest containing text and optional voice description

    Returns:
        MP3 audio file
    """
    if model_pool is None:
        raise HTTPException(status_code=503, detail="Model pool not initialized")

    try:
        logger.info(f"Received synthesis request: {len(request.text)} characters")

        # Chunk text if needed
        chunks = text_chunker.chunk_text(
            request.text,
            voice_description=request.voice_description or config.voice.default_description
        )

        logger.info(f"Text split into {len(chunks)} chunk(s)")

        # Generate audio for each chunk (distributed across model instances)
        audio_arrays = model_pool.generate_audio_batch(
            chunks,
            voice_description=request.voice_description
        )

        if not audio_arrays:
            raise HTTPException(
                status_code=500,
                detail="Failed to generate audio for any chunks"
            )

        # Merge audio chunks
        if len(audio_arrays) > 1:
            logger.info(f"Merging {len(audio_arrays)} audio chunk(s)")
            merged_audio = audio_merger.merge_audio_arrays(
                audio_arrays,
                sample_rate=config.audio.sample_rate
            )
        else:
            merged_audio = audio_arrays[0]

        # Convert to MP3
        logger.info("Converting to MP3")
        mp3_bytes = audio_merger.numpy_to_mp3(
            merged_audio,
            sample_rate=config.audio.sample_rate,
            bitrate=config.audio.bitrate
        )

        logger.info(f"Successfully generated {len(mp3_bytes)} bytes of MP3 audio")

        # Return MP3 file
        return Response(
            content=mp3_bytes,
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": "attachment; filename=output.mp3"
            }
        )

    except Exception as e:
        logger.error(f"Synthesis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/synthesize_file")
async def synthesize_file(
    file: UploadFile = File(...),
    voice_description: Optional[str] = None
):
    """
    Synthesize speech from uploaded text file.

    Args:
        file: Uploaded text file
        voice_description: Optional voice characteristics

    Returns:
        MP3 audio file
    """
    if model_pool is None:
        raise HTTPException(status_code=503, detail="Model pool not initialized")

    try:
        # Read file contents
        contents = await file.read()
        text = contents.decode('utf-8')

        # Check file size limit
        file_size_mb = len(text) / (1024 * 1024)
        if file_size_mb > config.text_processing.max_file_size_mb:
            raise HTTPException(
                status_code=413,
                detail=f"File size ({file_size_mb:.2f}MB) exceeds limit "
                       f"({config.text_processing.max_file_size_mb}MB)"
            )

        logger.info(f"Processing uploaded file: {file.filename} ({len(text)} characters)")

        # Use the synthesize logic
        request = SynthesizeRequest(
            text=text,
            voice_description=voice_description
        )

        return await synthesize(request)

    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400,
            detail="File must be valid UTF-8 encoded text"
        )
    except Exception as e:
        logger.error(f"File synthesis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def root():
    """Root endpoint with API information."""
    pool_status = model_pool.health_check() if model_pool else {"total_instances": 0}

    return {
        "service": "Maya1 Speechify API",
        "version": "2.0.0",
        "model_instances": pool_status["total_instances"],
        "endpoints": {
            "/health": "Health check with model pool status",
            "/synthesize": "Synthesize speech from JSON (POST)",
            "/synthesize_file": "Synthesize speech from uploaded file (POST)"
        },
        "features": [
            "Parallel processing with model pool",
            "Round-robin load balancing",
            "Automatic text chunking",
            "MP3 audio output",
            "CORS support"
        ]
    }


@app.get("/config")
async def get_config():
    """Get current server configuration (non-sensitive fields)."""
    return {
        "model": {
            "name": config.model.name,
            "dtype": config.model.dtype,
            "max_model_len": config.model.max_model_len
        },
        "model_pool": {
            "num_instances": config.model_pool.num_instances,
            "gpu_memory_per_instance": config.model_pool.gpu_memory_per_instance
        },
        "generation": {
            "temperature": config.generation.temperature,
            "top_p": config.generation.top_p,
            "max_new_tokens": config.generation.max_new_tokens
        },
        "audio": {
            "sample_rate": config.audio.sample_rate,
            "format": config.audio.format,
            "bitrate": config.audio.bitrate
        },
        "text_processing": {
            "chunk_size": config.text_processing.chunk_size,
            "max_file_size_mb": config.text_processing.max_file_size_mb
        }
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=config.server.host,
        port=config.server.port,
        log_level=config.server.log_level.lower(),
        reload=False  # Disable reload in production
    )
