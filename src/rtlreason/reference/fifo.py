from __future__ import annotations

from collections import deque
from dataclasses import dataclass


@dataclass(frozen=True)
class FifoObservation:
    """Expected observable state immediately after one sampled rising edge."""

    cycle: int
    pre_occupancy: int
    write_accepted: bool
    read_accepted: bool
    read_data_valid: bool
    dout: int
    occupancy: int
    full: bool
    empty: bool


class FifoReferenceModel:
    """Architecture-independent executable model for ``fifo_sync_v1``.

    The model owns its queue and derives acceptance from that queue.  DUT status
    outputs are deliberately absent from ``step`` so they cannot contaminate the
    oracle.  Inputs are sampled immediately before a rising edge and the returned
    observation describes outputs immediately after it.
    """

    def __init__(self, *, depth: int = 4, data_width: int = 8) -> None:
        if depth < 2:
            raise ValueError("depth must be at least two")
        if data_width < 1:
            raise ValueError("data_width must be positive")
        self.depth = depth
        self.data_width = data_width
        self._mask = (1 << data_width) - 1
        self._queue: deque[int] = deque()
        self._dout = 0
        self._cycle = -1

    @property
    def occupancy(self) -> int:
        return len(self._queue)

    @property
    def dout(self) -> int:
        return self._dout

    def step(
        self,
        *,
        rst: bool = False,
        wr_en: bool = False,
        rd_en: bool = False,
        din: int = 0,
    ) -> FifoObservation:
        self._cycle += 1
        pre_occupancy = len(self._queue)

        if rst:
            self._queue.clear()
            self._dout = 0
            return FifoObservation(
                cycle=self._cycle,
                pre_occupancy=pre_occupancy,
                write_accepted=False,
                read_accepted=False,
                read_data_valid=False,
                dout=0,
                occupancy=0,
                full=False,
                empty=True,
            )

        was_empty = pre_occupancy == 0
        was_full = pre_occupancy == self.depth
        read_accepted = bool(rd_en and not was_empty)
        write_accepted = bool(wr_en and (not was_full or read_accepted))

        if read_accepted:
            self._dout = self._queue.popleft()
        if write_accepted:
            self._queue.append(int(din) & self._mask)

        occupancy = len(self._queue)
        if not 0 <= occupancy <= self.depth:
            raise AssertionError("reference-model occupancy invariant violated")
        return FifoObservation(
            cycle=self._cycle,
            pre_occupancy=pre_occupancy,
            write_accepted=write_accepted,
            read_accepted=read_accepted,
            read_data_valid=read_accepted,
            dout=self._dout,
            occupancy=occupancy,
            full=occupancy == self.depth,
            empty=occupancy == 0,
        )
