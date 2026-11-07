"""Paragraph-preserving segmentation for candidate-level applicability review."""

from __future__ import annotations

import re


def segment_candidate(candidate: dict[str, object], max_characters: int) -> list[dict[str, object]]:
    """Split one page candidate into bounded paragraph groups without crossing pages."""
    text = str(candidate["text"])
    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", text) if part.strip()]
    separator = "\n\n"
    force_new_group_before: set[int] = set()
    if len(paragraphs) <= 1 and "\n" in text:
        paragraphs = [line.strip() for line in text.splitlines() if line.strip()]
        separator = "\n"
        sectioned_paragraphs: list[str] = []
        current_section: list[str] = []
        found_numbered_section = False
        for line in paragraphs:
            if re.match(r"^\d+(?:\.\d+)+\s", line) and current_section:
                sectioned_paragraphs.append("\n".join(current_section))
                force_new_group_before.add(len(sectioned_paragraphs))
                current_section = [line]
                found_numbered_section = True
            else:
                current_section.append(line)
        if current_section:
            sectioned_paragraphs.append("\n".join(current_section))
        if found_numbered_section:
            paragraphs = sectioned_paragraphs
    groups: list[str] = []
    current = ""
    for index, paragraph in enumerate(paragraphs):
        if current and index in force_new_group_before:
            groups.append(current)
            current = paragraph
            continue
        proposed = paragraph if not current else f"{current}{separator}{paragraph}"
        if current and len(proposed) > max_characters:
            groups.append(current)
            current = paragraph
        else:
            current = proposed
    if current:
        groups.append(current)

    base = {key: value for key, value in candidate.items() if key not in {"candidate_id", "text"}}
    parent_id = str(candidate["candidate_id"])
    return [
        {
            "chunk_id": f"{parent_id}:{index:02d}",
            "parent_candidate_id": parent_id,
            "chunk_index": index,
            **base,
            "text": text,
        }
        for index, text in enumerate(groups, start=1)
    ]
