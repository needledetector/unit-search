"""Feature matrix generation for similarity search."""
from __future__ import annotations

import numpy as np
import pandas as pd
from typing import List, Tuple


def build_member_unit_matrix(unit_members: pd.DataFrame) -> Tuple[List[str], List[str], np.ndarray]:
    """Create a member x unit matrix weighted by unit_members.weight."""

    if unit_members.empty:
        return [], [], np.zeros((0, 0))

    unit_members = unit_members.copy()
    unit_members["unit_id"] = unit_members["unit_id"].astype(str)
    unit_members["member_id"] = unit_members["member_id"].astype(str)

    member_ids = sorted(unit_members["member_id"].unique())
    unit_ids = sorted(unit_members["unit_id"].unique())

    member_index = {mid: idx for idx, mid in enumerate(member_ids)}
    unit_index = {uid: idx for idx, uid in enumerate(unit_ids)}

    mat = np.zeros((len(member_ids), len(unit_ids)))
    for _, row in unit_members.iterrows():
        mid = row["member_id"]
        uid = row["unit_id"]
        weight = float(row.get("weight", 1) or 1)
        value = 1.0 / (1.0 + weight)  # smaller weight -> bigger contribution
        mat[member_index[mid], unit_index[uid]] = value

    # L2 normalize rows
    norms = np.linalg.norm(mat, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    mat = mat / norms
    return member_ids, unit_ids, mat
