#!/usr/bin/env python3
"""Tiny DSES v0.1 helper for an existing Python application.

The emitted event is I1. It records what the application wrote; it does not
claim cryptographic integrity or a pre-AI state.
"""
from __future__ import annotations

import hashlib
import json
import uuid

import jcs


def sha256_commit(payload: object) -> str:
    """Commit to JSON with the repository's pinned RFC 8785 implementation."""
    return "sha256:" + hashlib.sha256(jcs.canonicalize(payload)).hexdigest()


def passive_presentation(
    *, case_ref: str, actor_ref: str, occurred_at: str, sequence: int,
    ai_name: str, model_id: str, model_version: str,
    exposure_classes: list[str], modality: str,
) -> dict:
    return {
        "event_id": f"evt-{uuid.uuid4()}",
        "event_type": "ai_result_presented",
        "sequence": sequence,
        "ordering": "determinate",
        "occurred_at": occurred_at,
        "recorded_at": occurred_at,
        "case_ref": case_ref,
        "actor": {"actor_ref": actor_ref, "actor_type": "human"},
        "ai_system": {
            "name": ai_name,
            "model_id": model_id,
            "model_version": model_version,
        },
        "exposure": {"classes": exposure_classes, "modality": modality},
        "integrity": {"class": "I1"},
        "source_system": {"system_type": "viewer"},
    }


if __name__ == "__main__":
    event = passive_presentation(
        case_ref="case-synthetic-001",
        actor_ref="actor-synthetic-001",
        occurred_at="2026-08-23T16:00:00Z",
        sequence=2,
        ai_name="Synthetic Classifier",
        model_id="synthetic-classifier",
        model_version="1.2.0",
        exposure_classes=["CATEGORICAL"],
        modality="inline_text",
    )
    print(json.dumps(event, indent=2))
