from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AxiStreamPacketCounterOutput:
    beat_count: int
    packet_count: int


class AxiStreamPacketCounterReferenceModel:
    """Observable transfer-counting model with independent saturation."""

    def __init__(self, count_width: int = 8) -> None:
        if count_width < 1:
            raise ValueError("count_width must be positive")
        self.maximum = (1 << count_width) - 1
        self.beat_count = 0
        self.packet_count = 0

    def step(
        self,
        *,
        rst: bool = False,
        clear: bool = False,
        tvalid: bool = False,
        tready: bool = False,
        tlast: bool = False,
    ) -> AxiStreamPacketCounterOutput:
        if rst or clear:
            self.beat_count = 0
            self.packet_count = 0
        elif tvalid and tready:
            self.beat_count = min(self.beat_count + 1, self.maximum)
            if tlast:
                self.packet_count = min(self.packet_count + 1, self.maximum)
        return AxiStreamPacketCounterOutput(self.beat_count, self.packet_count)
