from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AsyncSourceOutput:
    accept: bool
    busy: bool


class AsyncHandshakeReferenceModel:
    """Digital two-clock model; callers schedule source and destination steps."""

    def __init__(self) -> None:
        self.req_toggle = False
        self.ack_toggle = False
        self.req_sync_1 = False
        self.req_sync_2 = False
        self.req_seen = False
        self.ack_sync_1 = False
        self.ack_sync_2 = False

    def source_step(self, *, rst: bool, send: bool) -> AsyncSourceOutput:
        busy = not rst and self.req_toggle != self.ack_sync_2
        accept = not rst and send and not busy
        if rst:
            self.req_toggle = False
            self.ack_sync_1 = False
            self.ack_sync_2 = False
        else:
            self.ack_sync_2 = self.ack_sync_1
            self.ack_sync_1 = self.ack_toggle
            if accept:
                self.req_toggle = not self.req_toggle
        return AsyncSourceOutput(accept=accept, busy=busy)

    def destination_step(self, *, rst: bool) -> bool:
        if rst:
            self.req_sync_1 = False
            self.req_sync_2 = False
            self.req_seen = False
            self.ack_toggle = False
            return False
        pulse = self.req_sync_2 != self.req_seen
        old_sync_1 = self.req_sync_1
        self.req_sync_1 = self.req_toggle
        self.req_sync_2 = old_sync_1
        if pulse:
            self.req_seen = self.req_sync_2
            self.ack_toggle = self.req_sync_2
        return pulse
