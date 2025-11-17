"""FastAPI server for Maya1 TTS service."""
import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel, Field
import uvicorn

from config import Config
from model import Maya1Model
from utils import TextChunker, AudioMerger

# Configure logging
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global model instance
model: Optional[Maya1Model] = None
text_chunker: Optional[TextChunker] = None
audio_merger: AudioMerger = AudioMerger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for model initialization and cleanup."""
    global model, text_chunker

    logger.info("Starting Maya1 Speechify API server...")

    # Initialize model and utilities
    try:
        model = Maya1Model()
        text_chunker = TextChunker(max_tokens=Config.CHUNK_SIZE)
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
    description="Text-to-Speech API using Maya1 model",
    version="1.0.0",
    lifespan=lifespan
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


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy" if model is not None else "initializing",
        model=Config.MODEL_NAME,
        device=Config.DEVICE
    )


@app.post("/synthesize")
async def synthesize(request: SynthesizeRequest):
    """
    Synthesize speech from text.

    Args:
        request: SynthesizeRequest containing text and optional voice description

    Returns:
        MP3 audio file
    """
    if model is None:
        raise HTTPException(status_code=503, detail="Model not initialized")

    try:
        logger.info(f"Received synthesis request: {len(request.text)} characters")

        # Chunk text if needed
        chunks = text_chunker.chunk_text(
            request.text,
            voice_description=request.voice_description or Config.DEFAULT_VOICE_DESCRIPTION
        )

        logger.info(f"Text split into {len(chunks)} chunks")

        # Generate audio for each chunk
        audio_arrays = model.generate_audio_batch(
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
            logger.info(f"Merging {len(audio_arrays)} audio chunks")
            merged_audio = audio_merger.merge_audio_arrays(
                audio_arrays,
                sample_rate=Config.SAMPLE_RATE
            )
        else:
            merged_audio = audio_arrays[0]

        # Convert to MP3
        logger.info("Converting to MP3")
        mp3_bytes = audio_merger.numpy_to_mp3(
            merged_audio,
            sample_rate=Config.SAMPLE_RATE,
            bitrate=Config.MP3_BITRATE
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
    if model is None:
        raise HTTPException(status_code=503, detail="Model not initialized")

    try:
        # Read file contents
        contents = await file.read()
        text = contents.decode('utf-8')

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
    return {
        "service": "Maya1 Speechify API",
        "version": "1.0.0",
        "endpoints": {
            "/health": "Health check",
            "/synthesize": "Synthesize speech from JSON",
            "/synthesize_file": "Synthesize speech from uploaded file"
        }
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=Config.HOST,
        port=Config.PORT,
        log_level=Config.LOG_LEVEL.lower(),
        reload=False  # Disable reload in production
    )
