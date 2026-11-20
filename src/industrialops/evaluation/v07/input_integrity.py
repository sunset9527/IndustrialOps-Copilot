"""Byte-level integrity checks for frozen evaluation inputs."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from pathlib import Path


class FrozenInputChanged(ValueError):
    """A v0.7 run observed a frozen input that changed after baseline capture."""


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@dataclass(frozen=True)
class FrozenInputVerifier:
    """Verify that v0.7 never mutates the inputs it claims to evaluate."""

    expected_hashes: dict[str, str]

    @classmethod
    def capture(cls, paths: tuple[Path, ...]) -> "FrozenInputVerifier":
        return cls({str(path): _sha256(path) for path in paths})

    def verify(self) -> dict[str, str]:
        actual = {path: _sha256(Path(path)) for path in self.expected_hashes}
        for path, expected in self.expected_hashes.items():
            if actual[path] != expected:
                raise FrozenInputChanged(f"FROZEN_INPUT_SHA256_MISMATCH: {path}")
        return actual
