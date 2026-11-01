from dataclasses import dataclass


@dataclass(frozen=True, slots=True, kw_only=True)
class PipelineMetrics:
    """Instantánea hilo-segura del rendimiento del bot."""
    fps: float
    dropped_frames: int
    vision_latency_ns: int