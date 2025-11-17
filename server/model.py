"""Maya1 model wrapper using vLLM for efficient inference."""
import logging
from typing import Optional, List
import numpy as np
import torch
from vllm import LLM, SamplingParams
from snac import SNAC

from config_schema import AppConfig

logger = logging.getLogger(__name__)


class Maya1Model:
    """Wrapper for Maya1 TTS model using vLLM."""

    def __init__(self, instance_id: int = 0, config: Optional[AppConfig] = None):
        """
        Initialize Maya1 model with vLLM and SNAC decoder.

        Args:
            instance_id: Unique identifier for this model instance
            config: Application configuration. If None, uses default config.
        """
        self.instance_id = instance_id

        # Import here to avoid circular dependency
        if config is None:
            from config import config as default_config
            config = default_config

        self.config = config

        logger.info(f"[Instance {instance_id}] Initializing Maya1 model with vLLM...")

        # Initialize vLLM model
        try:
            self.llm = LLM(
                model=config.model.name,
                tensor_parallel_size=config.model_pool.tensor_parallel_size,
                gpu_memory_utilization=config.model_pool.gpu_memory_per_instance,
                dtype=config.model.dtype,
                max_model_len=config.model.max_model_len,
                trust_remote_code=config.model.trust_remote_code,
            )
            logger.info(f"[Instance {instance_id}] vLLM model loaded successfully")
        except Exception as e:
            logger.error(f"[Instance {instance_id}] Failed to load vLLM model: {e}")
            raise

        # Initialize SNAC decoder for audio generation
        try:
            self.snac_model = SNAC.from_pretrained("hubertsiuzdak/snac_24khz").eval()
            self.snac_model = self.snac_model.to(config.model.device)
            logger.info(f"[Instance {instance_id}] SNAC decoder loaded successfully")
        except Exception as e:
            logger.error(f"[Instance {instance_id}] Failed to load SNAC decoder: {e}")
            raise

        # Set up sampling parameters
        self.sampling_params = SamplingParams(
            temperature=config.generation.temperature,
            top_p=config.generation.top_p,
            repetition_penalty=config.generation.repetition_penalty,
            max_tokens=config.generation.max_new_tokens,
        )

        logger.info(f"[Instance {instance_id}] Maya1 model initialized and ready")

    def generate_audio(self, text: str, voice_description: Optional[str] = None) -> np.ndarray:
        """
        Generate audio from text.

        Args:
            text: Input text to synthesize
            voice_description: Optional voice characteristics

        Returns:
            Audio data as numpy array (24kHz mono)
        """
        # Prepare prompt with voice description
        if voice_description:
            prompt = f'<description="{voice_description}">{text}'
        else:
            prompt = f'{self.config.get_voice_prompt()}{text}'

        logger.debug(
            f"[Instance {self.instance_id}] Generating audio for prompt "
            f"(length: {len(prompt)} chars)"
        )

        try:
            # Generate SNAC tokens using vLLM
            outputs = self.llm.generate([prompt], self.sampling_params)

            if not outputs or len(outputs) == 0:
                raise ValueError("No output generated from model")

            output = outputs[0]
            generated_text = output.outputs[0].text

            logger.debug(f"Generated {len(generated_text)} characters of SNAC tokens")

            # Parse SNAC tokens from generated text
            snac_codes = self._parse_snac_tokens(generated_text)

            # Decode SNAC codes to audio
            audio_array = self._decode_snac_to_audio(snac_codes)

            logger.debug(
                f"[Instance {self.instance_id}] Generated audio: "
                f"{audio_array.shape[0]} samples, "
                f"{audio_array.shape[0] / self.config.audio.sample_rate:.2f} seconds"
            )

            return audio_array

        except Exception as e:
            logger.error(f"Audio generation failed: {e}")
            raise

    def _parse_snac_tokens(self, generated_text: str) -> torch.Tensor:
        """
        Parse SNAC tokens from generated text.

        Args:
            generated_text: Text output from model containing SNAC codes

        Returns:
            Tensor of SNAC codes
        """
        try:
            # Maya1 generates SNAC codes as sequences of integers
            # Format: space-separated integers or special format
            # This is a simplified parser - adjust based on actual model output format

            # Remove any special tokens or markers
            clean_text = generated_text.strip()

            # Try to parse as space-separated integers
            tokens = []
            for line in clean_text.split('\n'):
                line = line.strip()
                if line:
                    # Try to extract numbers
                    numbers = []
                    for part in line.split():
                        try:
                            num = int(part)
                            numbers.append(num)
                        except ValueError:
                            # Skip non-numeric parts
                            continue
                    tokens.extend(numbers)

            if not tokens:
                # Fallback: try to parse entire text as comma or space separated
                import re
                numbers = re.findall(r'-?\d+', clean_text)
                tokens = [int(n) for n in numbers]

            if not tokens:
                raise ValueError("No valid SNAC tokens found in generated text")

            # Convert to tensor and reshape for SNAC decoder
            # SNAC expects shape (batch, num_codebooks, time)
            # Maya1 generates 7 tokens per frame
            codes_array = np.array(tokens, dtype=np.int64)

            # Reshape to (1, 7, num_frames) if possible
            if len(codes_array) % 7 == 0:
                num_frames = len(codes_array) // 7
                codes_array = codes_array.reshape(1, num_frames, 7).transpose(0, 2, 1)
            else:
                # Pad if necessary
                remainder = len(codes_array) % 7
                if remainder != 0:
                    padding = 7 - remainder
                    codes_array = np.pad(codes_array, (0, padding), constant_values=0)
                num_frames = len(codes_array) // 7
                codes_array = codes_array.reshape(1, num_frames, 7).transpose(0, 2, 1)

            return torch.from_numpy(codes_array).to(self.config.model.device)

        except Exception as e:
            logger.error(f"Failed to parse SNAC tokens: {e}")
            logger.debug(f"Generated text sample: {generated_text[:200]}...")
            raise

    def _decode_snac_to_audio(self, snac_codes: torch.Tensor) -> np.ndarray:
        """
        Decode SNAC codes to audio waveform.

        Args:
            snac_codes: Tensor of SNAC codes (batch, num_codebooks, time)

        Returns:
            Audio waveform as numpy array
        """
        try:
            with torch.no_grad():
                # SNAC decoder converts codes to audio
                audio_tensor = self.snac_model.decode(snac_codes)

                # Convert to numpy and squeeze batch dimension
                audio_array = audio_tensor.cpu().numpy().squeeze()

                # Ensure mono output
                if audio_array.ndim > 1:
                    audio_array = audio_array[0]

                # Normalize to [-1, 1] range if needed
                if audio_array.max() > 1.0 or audio_array.min() < -1.0:
                    max_val = max(abs(audio_array.max()), abs(audio_array.min()))
                    audio_array = audio_array / max_val

                return audio_array

        except Exception as e:
            logger.error(f"Failed to decode SNAC to audio: {e}")
            raise

    def generate_audio_batch(self, texts: List[str],
                            voice_description: Optional[str] = None) -> List[np.ndarray]:
        """
        Generate audio for multiple text chunks.

        Args:
            texts: List of text strings to synthesize
            voice_description: Optional voice characteristics (applied to all)

        Returns:
            List of audio arrays
        """
        audio_arrays = []

        for i, text in enumerate(texts):
            logger.info(
                f"[Instance {self.instance_id}] "
                f"Generating audio for chunk {i + 1}/{len(texts)}"
            )
            try:
                audio = self.generate_audio(text, voice_description)
                audio_arrays.append(audio)
            except Exception as e:
                logger.error(
                    f"[Instance {self.instance_id}] "
                    f"Failed to generate audio for chunk {i + 1}: {e}"
                )
                # Continue with other chunks rather than failing completely
                continue

        return audio_arrays
