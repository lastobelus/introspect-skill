from __future__ import annotations

import re
from pathlib import Path


ROLLOUT_NAME_RE = re.compile(r"^rollout-\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}-(?P<session_id>.+)$")


def codex_session_id_from_path(path: str | Path) -> str:
    stem = Path(path).stem
    match = ROLLOUT_NAME_RE.match(stem)
    if match:
        return match.group("session_id")
    return stem
