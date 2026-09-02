from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DualPortRamOutput:
    rd_data: int


class DualPortRamReferenceModel:
    """Architecture-independent synchronous read-first memory model."""

    def __init__(self, *, data_width: int = 8, addr_width: int = 2) -> None:
        if data_width < 1 or addr_width < 1:
            raise ValueError("data_width and addr_width must be positive")
        self.data_width = data_width
        self.depth = 1 << addr_width
        self.mask = (1 << data_width) - 1
        self.memory = [0] * self.depth
        self.rd_data = 0

    def step(
        self,
        *,
        rst: bool = False,
        wr_en: bool = False,
        wr_addr: int = 0,
        wr_data: int = 0,
        rd_en: bool = False,
        rd_addr: int = 0,
    ) -> DualPortRamOutput:
        if rst:
            self.memory = [0] * self.depth
            self.rd_data = 0
        else:
            old_read_value = self.memory[rd_addr % self.depth]
            if wr_en:
                self.memory[wr_addr % self.depth] = wr_data & self.mask
            if rd_en:
                self.rd_data = old_read_value
        return DualPortRamOutput(self.rd_data)
