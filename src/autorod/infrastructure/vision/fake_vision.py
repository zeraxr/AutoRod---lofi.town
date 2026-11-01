from autorod.domain.ports.vision import IVisionStrategy
from autorod.domain.models.image_payload import ImagePayload
from autorod.domain.models.match_result import MatchResult


class FakeVisionStrategy(IVisionStrategy):
    @property
    def strategy_id(self) -> str: return "fake_vision"

    def analyze(self, frame: ImagePayload, template_ref: str | None = None) -> MatchResult:
        return MatchResult(
            found=False, confidence=0.0, region=None,
            center=None, strategy_id=self.strategy_id, frame_id=frame.frame_id
        )