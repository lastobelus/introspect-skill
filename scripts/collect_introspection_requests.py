#!/usr/bin/env python3

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from introspect_skill.cli import collect_introspection_requests_main


if __name__ == "__main__":
    collect_introspection_requests_main()
