"""
Maya1 TTS model wrapper with proper SNAC token handling.
Based on official Maya1 documentation.
"""
import logging
from typing import Optional, List
import numpy as np
import torch
from vllm import LLM, SamplingParams
import snac
from config import config

logger = logging.getLogger(__name__)

# Maya1 special token IDs
CODE_START_TOKEN_ID = 128257
CODE_END_TOKEN_ID = 128258
CODE_TOKEN_OFFSET = 128266
SNAC_MIN_ID = 128266
SNAC_MAX_ID = 156937
SNAC_TOKENS_PER_FRAME = 7

SOH_ID = 128259
EOH_ID = 128260
SOA_ID = 128261
BOS_ID = 128000
TEXT_EOT_ID = 128009


class Maya1Model:
    """Wrapper for Maya1 TTS model with vLLM optimization."""

    def __init__(self, instance_id: int = 0):
        """
        Initialize Maya1 model instance.

        Args:
            instance_id: Instance identifier for logging
        """
        self.instance_id = instance_id
        self.config = config
        self.llm = None
        self.snac_model = None
        self.tokenizer = None
        self._initialize_model()

    def _initialize_model(self):
        """Initialize vLLM model and SNAC decoder."""
        logger.info(f"[Instance {self.instance_id}] Initializing Maya1 model with vLLM...")

        try:
            # Initialize vLLM with Maya1
            self.llm = LLM(
                model=self.config.model.name,
                trust_remote_code=self.config.model.trust_remote_code,
                dtype=self.config.model.dtype,
                max_model_len=self.config.model.max_model_len,
                gpu_memory_utilization=self.config.model_pool.gpu_memory_per_instance,
                tensor_parallel_size=self.config.model_pool.tensor_parallel_size,
                disable_log_stats=True,
            )

            # Get tokenizer from the LLM
            from transformers import AutoTokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.config.model.name,
                trust_remote_code=True
            )

            logger.info(f"[Instance {self.instance_id}] vLLM model loaded successfully")

            # Load SNAC decoder
            logger.debug(f"[Instance {self.instance_id}] Loading SNAC decoder...")
            self.snac_model = snac.SNAC.from_pretrained("hubertsiuzdak/snac_24khz").eval()

            if torch.cuda.is_available() and self.config.model.device == "cuda":
                self.snac_model = self.snac_model.to("cuda")

            logger.info(f"[Instance {self.instance_id}] SNAC decoder loaded successfully")
            logger.info(f"[Instance {self.instance_id}] Maya1 model initialized and ready")

        except Exception as e:
            logger.error(f"[Instance {self.instance_id}] Failed to load model: {e}")
            raise

    def build_prompt(self, text: str, voice_description: Optional[str] = None) -> str:
        """
        Build formatted prompt for Maya1.

        Args:
            text: Text to synthesize
            voice_description: Voice characteristics description

        Returns:
            Formatted prompt string
        """
        if voice_description is None:
            voice_description = self.config.voice.default_description

        # Get special tokens
        soh_token = self.tokenizer.decode([SOH_ID])
        eoh_token = self.tokenizer.decode([EOH_ID])
        soa_token = self.tokenizer.decode([SOA_ID])
        sos_token = self.tokenizer.decode([CODE_START_TOKEN_ID])
        eot_token = self.tokenizer.decode([TEXT_EOT_ID])
        bos_token = self.tokenizer.bos_token

        formatted_text = f'<description="{voice_description}"> {text}'

        prompt = (
            soh_token + bos_token + formatted_text + eot_token +
            eoh_token + soa_token + sos_token
        )

        return prompt

    def extract_snac_codes(self, token_ids: List[int]) -> List[int]:
        """
        Extract SNAC codes from generated tokens.

        Args:
            token_ids: List of generated token IDs

        Returns:
            List of SNAC token codes
        """
        try:
            eos_idx = token_ids.index(CODE_END_TOKEN_ID)
        except ValueError:
            eos_idx = len(token_ids)

        snac_codes = [
            token_id for token_id in token_ids[:eos_idx]
            if SNAC_MIN_ID <= token_id <= SNAC_MAX_ID
        ]

        return snac_codes

    def unpack_snac_from_7(self, snac_tokens: List[int]) -> List[List[int]]:
        """
        Unpack 7-token SNAC frames to 3 hierarchical levels.

        Args:
            snac_tokens: List of SNAC tokens

        Returns:
            List of 3 levels of unpacked codes
        """
        if snac_tokens and snac_tokens[-1] == CODE_END_TOKEN_ID:
            snac_tokens = snac_tokens[:-1]

        frames = len(snac_tokens) // SNAC_TOKENS_PER_FRAME
        snac_tokens = snac_tokens[:frames * SNAC_TOKENS_PER_FRAME]

        if frames == 0:
            return [[], [], []]

        l1, l2, l3 = [], [], []

        for i in range(frames):
            slots = snac_tokens[i*7:(i+1)*7]
            l1.append((slots[0] - CODE_TOKEN_OFFSET) % 4096)
            l2.extend([
                (slots[1] - CODE_TOKEN_OFFSET) % 4096,
                (slots[4] - CODE_TOKEN_OFFSET) % 4096,
            ])
            l3.extend([
                (slots[2] - CODE_TOKEN_OFFSET) % 4096,
                (slots[3] - CODE_TOKEN_OFFSET) % 4096,
                (slots[5] - CODE_TOKEN_OFFSET) % 4096,
                (slots[6] - CODE_TOKEN_OFFSET) % 4096,
            ])

        return [l1, l2, l3]

    def generate_audio(self, text: str, voice_description: Optional[str] = None) -> np.ndarray:
        """
        Generate audio from text.

        Args:
            text: Input text to synthesize
            voice_description: Optional voice characteristics

        Returns:
            Audio data as numpy array (24kHz mono)
        """
        try:
            # Build the prompt with proper formatting
            prompt = self.build_prompt(text, voice_description)

            logger.debug(
                f"[Instance {self.instance_id}] Generating audio for prompt "
                f"(length: {len(prompt)} chars)"
            )

            # Create sampling parameters
            sampling_params = SamplingParams(
                temperature=self.config.generation.temperature,
                top_p=self.config.generation.top_p,
                repetition_penalty=self.config.generation.repetition_penalty,
                max_tokens=self.config.generation.max_new_tokens,
                min_tokens=28,  # At least 4 SNAC frames
                stop_token_ids=[CODE_END_TOKEN_ID],
                skip_special_tokens=False,  # Keep special tokens for extraction
            )

            # Generate with vLLM
            outputs = self.llm.generate([prompt], sampling_params)

            # Get the output tokens (not text!)
            output = outputs[0]
            generated_ids = output.outputs[0].token_ids

            logger.debug(f"Generated {len(generated_ids)} tokens")

            # Extract SNAC audio tokens
            snac_tokens = self.extract_snac_codes(generated_ids)

            logger.debug(f"Extracted {len(snac_tokens)} SNAC tokens")

            if len(snac_tokens) < SNAC_TOKENS_PER_FRAME:
                raise ValueError(f"Not enough SNAC tokens generated: {len(snac_tokens)}")

            # Unpack SNAC tokens to 3 hierarchical levels
            levels = self.unpack_snac_from_7(snac_tokens)
            frames = len(levels[0])

            logger.debug(f"Unpacked to {frames} frames")

            # Convert to tensors for SNAC decoder
            device = self.config.model.device
            codes_tensor = [
                torch.tensor(level, dtype=torch.long, device=device).unsqueeze(0)
                for level in levels
            ]

            # Generate audio with SNAC decoder
            with torch.inference_mode():
                z_q = self.snac_model.quantizer.from_codes(codes_tensor)
                audio_tensor = self.snac_model.decoder(z_q)[0, 0]
                audio_array = audio_tensor.cpu().numpy()

            # Trim warmup samples (first 2048 samples)
            if len(audio_array) > 2048:
                audio_array = audio_array[2048:]

            # Normalize to [-1, 1] range if needed
            if audio_array.max() > 1.0 or audio_array.min() < -1.0:
                max_val = max(abs(audio_array.max()), abs(audio_array.min()))
                audio_array = audio_array / max_val

            duration = len(audio_array) / self.config.audio.sample_rate
            logger.debug(
                f"[Instance {self.instance_id}] Generated audio: "
                f"{len(audio_array)} samples, {duration:.2f} seconds"
            )

            return audio_array

        except Exception as e:
            logger.error(f"[Instance {self.instance_id}] Audio generation failed: {e}")
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