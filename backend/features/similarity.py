"""Cosine similarity helpers."""
from __future__ import annotations

from typing import Dict, List, Tuple

import numpy as np


def cosine_similarity(matrix: np.ndarray, target_index: int) -> np.ndarray:
    if matrix.size == 0:
        return np.array([])
    target = matrix[target_index]
    scores = matrix @ target
    return scores


def top_similar(
    member_id: str,
    member_ids: List[str],
    matrix: np.ndarray,
    top: int = 5,
) -> List[Tuple[str, float]]:
    if member_id not in member_ids or matrix.size == 0:
        return []
    idx = member_ids.index(member_id)
    scores = cosine_similarity(matrix, idx)
    results: List[Tuple[str, float]] = []
    for mid, score in zip(member_ids, scores):
        if mid == member_id:
            continue
        results.append((mid, float(score)))
    results.sort(key=lambda item: item[1], reverse=True)
    return results[:top]
