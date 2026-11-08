"""Build translation-aware corpus records without replacing source evidence."""

from __future__ import annotations

import argparse
from collections.abc import Callable
import hashlib
import json
from pathlib import Path
import re


def split_text_for_translation(text: str, max_characters: int) -> list[str]:
    """Split source text into bounded, lossless chunks for a local translator."""
    if max_characters <= 0:
        raise ValueError("max_characters must be positive")
    pieces: list[str] = []
    current = ""
    for token in re.findall(r"\s+|\S+", text):
        if current and len(current) + len(token) > max_characters:
            pieces.append(current)
            current = token
        else:
            current += token
    if current:
        pieces.append(current)
    return pieces


def build_bilingual_records(
    records: list[dict[str, object]],
    translate: Callable[[str], str],
    on_record_completed: Callable[[int, int], None] | None = None,
) -> list[dict[str, object]]:
    """Attach project Chinese text while retaining every source record unchanged."""
    bilingual: list[dict[str, object]] = []
    for index, record in enumerate(records, start=1):
        text = str(record["text"])
        language = str(record["language"])
        updated = dict(record)
        updated["original_text"] = text
        if language in {"zh-CN", "multi_zh-CN"}:
            updated["text_zh"] = text
            updated["translation_status"] = "source_zh"
        else:
            translated_text = translate(text)
            if not translated_text.strip():
                raise ValueError(f"empty Chinese translation for {_record_identifier(record)}")
            updated["text_zh"] = translated_text
            updated["translation_status"] = "machine_translated_project_zh"
        bilingual.append(updated)
        if on_record_completed is not None:
            on_record_completed(index, len(records))
    return bilingual


def _record_identifier(record: dict[str, object]) -> str:
    return str(record.get("candidate_id", record.get("unit_id", "<unknown>")))


def validate_bilingual_records(records: list[dict[str, object]]) -> dict[str, int]:
    """Validate that the bilingual corpus retains source text and traceable evidence."""
    required_evidence = ("source_id", "source_file", "source_sha256", "page_number", "evidence_locator")
    source_zh = 0
    machine_translated = 0
    for record in records:
        missing = [field for field in required_evidence if not str(record.get(field, "")).strip()]
        if missing:
            raise ValueError(f"missing evidence fields {missing} for {_record_identifier(record)}")
        text = str(record.get("text", ""))
        original = str(record.get("original_text", ""))
        text_zh = str(record.get("text_zh", ""))
        language = str(record.get("language", ""))
        status = str(record.get("translation_status", ""))
        if not text or original != text or not text_zh.strip():
            raise ValueError(f"source or Chinese text is invalid for {_record_identifier(record)}")
        if language in {"zh-CN", "multi_zh-CN"}:
            if text_zh != text or status != "source_zh":
                raise ValueError(f"source Chinese record changed for {_record_identifier(record)}")
            source_zh += 1
        elif language == "en":
            if status != "machine_translated_project_zh":
                raise ValueError(f"English record is missing translation provenance for {_record_identifier(record)}")
            machine_translated += 1
        else:
            raise ValueError(f"unsupported language {language!r} for {_record_identifier(record)}")
    return {"total": len(records), "source_zh": source_zh, "machine_translated": machine_translated}


class LocalMarianTranslator:
    """Offline English-to-Chinese translator that never sends source text to a service."""

    def __init__(self, model_path: Path, *, batch_size: int = 8, max_characters: int = 350) -> None:
        import torch
        from transformers import MarianMTModel, MarianTokenizer

        self.tokenizer = MarianTokenizer.from_pretrained(model_path, local_files_only=True)
        self.model = MarianMTModel.from_pretrained(model_path, local_files_only=True)
        self.model.eval()
        self.model.generation_config.max_length = None
        self.torch = torch
        self.batch_size = batch_size
        self.max_characters = max_characters

    def __call__(self, text: str) -> str:
        pieces = split_text_for_translation(text, self.max_characters)
        translated: list[str] = []
        for start in range(0, len(pieces), self.batch_size):
            batch = pieces[start : start + self.batch_size]
            encoded = self.tokenizer(batch, return_tensors="pt", padding=True, truncation=True, max_length=512)
            with self.torch.inference_mode():
                generated = self.model.generate(**encoded, max_new_tokens=256)
            translated.extend(self.tokenizer.batch_decode(generated, skip_special_tokens=True))
        return "".join(translated)


def _read_jsonl(path: Path) -> list[dict[str, object]]:
    with path.open(encoding="utf-8") as file:
        return [json.loads(line) for line in file if line.strip()]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _write_jsonl(path: Path, records: list[dict[str, object]]) -> None:
    temporary = path.with_name(f"{path.name}.partial")
    with temporary.open("w", encoding="utf-8", newline="\n") as file:
        for record in records:
            file.write(json.dumps(record, ensure_ascii=False, sort_keys=True))
            file.write("\n")
    temporary.replace(path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build an offline bilingual IndustrialOps corpus.")
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model-path", type=Path, required=True)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--max-characters", type=int, default=350)
    arguments = parser.parse_args()

    records = _read_jsonl(arguments.input)
    translator = LocalMarianTranslator(
        arguments.model_path,
        batch_size=arguments.batch_size,
        max_characters=arguments.max_characters,
    )
    def report_progress(done: int, total: int) -> None:
        if done == total or done % 20 == 0:
            print(f"PROGRESS {done}/{total}", flush=True)

    bilingual = build_bilingual_records(records, translator, on_record_completed=report_progress)
    summary = validate_bilingual_records(bilingual)
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    _write_jsonl(arguments.output, bilingual)
    print(json.dumps({**summary, "model_sha256": _sha256(arguments.model_path / "pytorch_model.bin")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
