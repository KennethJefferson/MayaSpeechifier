"""Model pool manager for parallel processing with round-robin load balancing."""
import logging
import threading
from typing import List, Optional
import numpy as np

from config_schema import AppConfig
from model import Maya1Model

logger = logging.getLogger(__name__)


class ModelPool:
    """
    Manages multiple Maya1 model instances with round-robin load balancing.

    This class maintains a pool of model instances and distributes requests
    across them using a simple round-robin strategy for load balancing.
    """

    def __init__(self, config: AppConfig):
        """
        Initialize model pool.

        Args:
            config: Application configuration
        """
        self.config = config
        self.num_instances = config.model_pool.num_instances
        self.instances: List[Maya1Model] = []
        self.current_index = 0
        self.lock = threading.Lock()  # Thread-safe instance selection

        logger.info(f"Initializing model pool with {self.num_instances} instance(s)...")

        # Validate GPU memory configuration
        total_gpu_memory = config.model_pool.gpu_memory_per_instance * self.num_instances
        if total_gpu_memory > 0.95:
            logger.warning(
                f"Total GPU memory allocation ({total_gpu_memory:.1%}) exceeds 95%. "
                f"This may cause OOM errors. Consider reducing num_instances or "
                f"gpu_memory_per_instance in config.json"
            )

        # Initialize all model instances
        self._initialize_instances()

        logger.info(f"Model pool initialized with {len(self.instances)} instance(s)")

    def _initialize_instances(self):
        """Initialize all model instances in the pool."""
        for i in range(self.num_instances):
            try:
                logger.info(f"Loading model instance {i + 1}/{self.num_instances}...")

                # Create model instance with pool-specific config
                instance = Maya1Model(
                    instance_id=i,
                    config=self.config
                )

                self.instances.append(instance)
                logger.info(f"Instance {i} loaded successfully")

            except Exception as e:
                logger.error(f"Failed to load model instance {i}: {e}")
                # Continue trying to load other instances
                continue

        if len(self.instances) == 0:
            raise RuntimeError("Failed to initialize any model instances")

        if len(self.instances) < self.num_instances:
            logger.warning(
                f"Only {len(self.instances)}/{self.num_instances} instances loaded successfully"
            )

    def get_instance(self) -> Maya1Model:
        """
        Get next available model instance using round-robin strategy.

        Returns:
            Maya1Model instance

        Raises:
            RuntimeError: If no instances are available
        """
        if not self.instances:
            raise RuntimeError("No model instances available")

        with self.lock:
            instance = self.instances[self.current_index]
            self.current_index = (self.current_index + 1) % len(self.instances)

        return instance

    def generate_audio(
        self,
        text: str,
        voice_description: Optional[str] = None
    ) -> np.ndarray:
        """
        Generate audio from text using an available model instance.

        Args:
            text: Input text to synthesize
            voice_description: Optional voice characteristics

        Returns:
            Audio data as numpy array (24kHz mono)
        """
        instance = self.get_instance()
        logger.debug(f"Routing request to instance {instance.instance_id}")

        return instance.generate_audio(text, voice_description)

    def generate_audio_batch(
        self,
        texts: List[str],
        voice_description: Optional[str] = None
    ) -> List[np.ndarray]:
        """
        Generate audio for multiple text chunks.

        Note: This distributes chunks across instances but processes
        sequentially. For true parallel processing, use async requests.

        Args:
            texts: List of text strings to synthesize
            voice_description: Optional voice characteristics (applied to all)

        Returns:
            List of audio arrays
        """
        audio_arrays = []

        for i, text in enumerate(texts):
            logger.info(f"Generating audio for chunk {i + 1}/{len(texts)}")
            try:
                # Each chunk goes to the next instance (round-robin)
                audio = self.generate_audio(text, voice_description)
                audio_arrays.append(audio)
            except Exception as e:
                logger.error(f"Failed to generate audio for chunk {i + 1}: {e}")
                # Continue with other chunks rather than failing completely
                continue

        return audio_arrays

    def health_check(self) -> dict:
        """
        Check health status of all instances.

        Returns:
            Dictionary with health status information
        """
        total_instances = len(self.instances)
        healthy_instances = 0

        for instance in self.instances:
            try:
                # Simple check - verify model and decoder are loaded
                if instance.llm is not None and instance.snac_model is not None:
                    healthy_instances += 1
            except Exception as e:
                logger.error(f"Health check failed for instance {instance.instance_id}: {e}")

        return {
            "total_instances": total_instances,
            "healthy_instances": healthy_instances,
            "configured_instances": self.num_instances,
            "status": "healthy" if healthy_instances == total_instances else "degraded",
            "gpu_memory_per_instance": f"{self.config.model_pool.gpu_memory_per_instance:.1%}"
        }

    def __len__(self) -> int:
        """Return number of active instances."""
        return len(self.instances)

    def __repr__(self) -> str:
        """String representation of model pool."""
        return (
            f"ModelPool(instances={len(self.instances)}/{self.num_instances}, "
            f"current_index={self.current_index})"
        )
