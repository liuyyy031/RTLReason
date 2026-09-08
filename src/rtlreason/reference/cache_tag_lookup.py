from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CacheLookupOutput:
    hit: bool
    hit_way: int
    hit_data: int


class CacheTagLookupReferenceModel:
    @staticmethod
    def evaluate(
        lookup_tag: int,
        valid: list[bool],
        tags: list[int],
        data: list[int],
    ) -> CacheLookupOutput:
        if not (len(valid) == len(tags) == len(data)):
            raise ValueError("way arrays must have equal lengths")
        for way, (is_valid, tag, value) in enumerate(zip(valid, tags, data)):
            if is_valid and tag == lookup_tag:
                return CacheLookupOutput(True, way, value)
        return CacheLookupOutput(False, 0, 0)
