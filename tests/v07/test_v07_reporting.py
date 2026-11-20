from __future__ import annotations

from pathlib import Path

import pytest

from industrialops.evaluation.v07.run_store import RunStoreError, create_run_directory


def test_run_store_never_overwrites_an_existing_run_directory(tmp_path: Path) -> None:
    create_run_directory(tmp_path, "before-001")

    with pytest.raises(RunStoreError, match="EVALUATION_RUN_ALREADY_EXISTS"):
        create_run_directory(tmp_path, "before-001")
