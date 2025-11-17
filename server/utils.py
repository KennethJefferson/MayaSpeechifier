"""Utility functions for text processing and audio handling."""
import re
from typing import List, Tuple
import tiktoken
import numpy as np
import soundfile as sf
from pydub import AudioSegment
from io import BytesIO
import logging

logger = logging.getLogger(__name__)


class TextChunker:
    """Handles intelligent text chunking to stay within token limits."""

    def __init__(self, max_tokens: int = 1500, model: str = "gpt-3.5-turbo"):
        """
        Initialize text chunker.

        Args:
            max_tokens: Maximum tokens per chunk
            model: Tokenizer model name (using tiktoken for estimation)
        """
        self.max_tokens = max_tokens
        try:
            self.encoder = tiktoken.encoding_for_model(model)
        except KeyError:
            # Fallback to cl100k_base if model not found
            self.encoder = tiktoken.get_encoding("cl100k_base")

    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
        return len(self.encoder.encode(text))

    def split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences using regex."""
        # Split on sentence boundaries (., !, ?) followed by space and capital letter
        sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)
        return [s.strip() for s in sentences if s.strip()]

    def chunk_text(self, text: str, voice_description: str = "") -> List[str]:
        """
        Split text into chunks that fit within token limit.

        Args:
            text: Input text to chunk
            voice_description: Voice description to prepend to each chunk

        Returns:
            List of text chunks with voice descriptions
        """
        # Clean text
        text = text.strip()

        # Calculate overhead from voice description
        desc_prompt = f'<description="{voice_description}">' if voice_description else ""
        overhead_tokens = self.count_tokens(desc_prompt)
        available_tokens = self.max_tokens - overhead_tokens - 10  # Safety margin

        # If entire text fits, return as single chunk
        if self.count_tokens(text) <= available_tokens:
            return [f"{desc_prompt}{text}"]

        # Split into sentences
        sentences = self.split_into_sentences(text)

        chunks = []
        current_chunk = []
        current_tokens = 0

        for sentence in sentences:
            sentence_tokens = self.count_tokens(sentence)

            # If single sentence exceeds limit, split it further
            if sentence_tokens > available_tokens:
                # If we have accumulated sentences, add them as a chunk
                if current_chunk:
                    chunks.append(f"{desc_prompt}{' '.join(current_chunk)}")
                    current_chunk = []
                    current_tokens = 0

                # Split long sentence by words
                words = sentence.split()
                word_chunk = []
                word_tokens = 0

                for word in words:
                    word_token_count = self.count_tokens(word + " ")
                    if word_tokens + word_token_count > available_tokens:
                        if word_chunk:
                            chunks.append(f"{desc_prompt}{' '.join(word_chunk)}")
                        word_chunk = [word]
                        word_tokens = word_token_count
                    else:
                        word_chunk.append(word)
                        word_tokens += word_token_count

                if word_chunk:
                    chunks.append(f"{desc_prompt}{' '.join(word_chunk)}")

            # If adding sentence would exceed limit, start new chunk
            elif current_tokens + sentence_tokens > available_tokens:
                if current_chunk:
                    chunks.append(f"{desc_prompt}{' '.join(current_chunk)}")
                current_chunk = [sentence]
                current_tokens = sentence_tokens

            # Add sentence to current chunk
            else:
                current_chunk.append(sentence)
                current_tokens += sentence_tokens

        # Add remaining sentences
        if current_chunk:
            chunks.append(f"{desc_prompt}{' '.join(current_chunk)}")

        logger.info(f"Split text into {len(chunks)} chunks")
        return chunks


class AudioMerger:
    """Handles merging multiple audio chunks into a single file."""

    @staticmethod
    def merge_audio_arrays(audio_arrays: List[np.ndarray], sample_rate: int = 24000) -> np.ndarray:
        """
        Merge multiple audio arrays into one.

        Args:
            audio_arrays: List of audio numpy arrays
            sample_rate: Sample rate of audio

        Returns:
            Merged audio array
        """
        if not audio_arrays:
            raise ValueError("No audio arrays to merge")

        if len(audio_arrays) == 1:
            return audio_arrays[0]

        # Add small silence between chunks (100ms)
        silence_samples = int(sample_rate * 0.1)
        silence = np.zeros(silence_samples, dtype=audio_arrays[0].dtype)

        merged = []
        for i, audio in enumerate(audio_arrays):
            merged.append(audio)
            # Add silence between chunks (but not after the last one)
            if i < len(audio_arrays) - 1:
                merged.append(silence)

        return np.concatenate(merged)

    @staticmethod
    def numpy_to_mp3(audio_array: np.ndarray, sample_rate: int = 24000,
                     bitrate: str = "192k") -> bytes:
        """
        Convert numpy audio array to MP3 bytes.

        Args:
            audio_array: Audio data as numpy array
            sample_rate: Sample rate of audio
            bitrate: MP3 bitrate

        Returns:
            MP3 file as bytes
        """
        # First convert to WAV in memory
        wav_buffer = BytesIO()
        sf.write(wav_buffer, audio_array, sample_rate, format='WAV')
        wav_buffer.seek(0)

        # Load as AudioSegment and export as MP3
        audio_segment = AudioSegment.from_wav(wav_buffer)

        mp3_buffer = BytesIO()
        audio_segment.export(mp3_buffer, format="mp3", bitrate=bitrate)

        return mp3_buffer.getvalue()

    @staticmethod
    def save_mp3(audio_array: np.ndarray, output_path: str,
                 sample_rate: int = 24000, bitrate: str = "192k") -> None:
        """
        Save audio array as MP3 file.

        Args:
            audio_array: Audio data as numpy array
            output_path: Path to save MP3 file
            sample_rate: Sample rate of audio
            bitrate: MP3 bitrate
        """
        mp3_bytes = AudioMerger.numpy_to_mp3(audio_array, sample_rate, bitrate)

        with open(output_path, 'wb') as f:
            f.write(mp3_bytes)

        logger.info(f"Saved MP3 to {output_path}")
