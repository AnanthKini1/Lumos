"""
WS-A utility — validate all JSON data files against Pydantic models.

Run after writing or editing any file in backend/data/. Exits with code 1
if any file fails validation so it can be used as a pre-commit check.

Usage:
    cd backend
    python validate_data.py
"""

import json
import sys
from pathlib import Path

from config import PERSONAS_DIR, STRATEGIES_DIR, TOPICS_DIR
from models import PersonaProfile, StrategyDefinition, TopicProfile

VALIDATORS: list[tuple[Path, type]] = [
    (PERSONAS_DIR, PersonaProfile),
    (STRATEGIES_DIR, StrategyDefinition),
    (TOPICS_DIR, TopicProfile),
]


def validate_dir(directory: Path, model: type) -> tuple[int, int]:
    """Validate all JSON files in a directory. Returns (passed, failed)."""
    passed = failed = 0
    files = sorted(directory.glob("*.json"))

    if not files:
        print(f"  (no files yet in {directory.name}/)")
        return 0, 0

    for path in files:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            model.model_validate(data)
            print(f"  PASS  {path.name}")
            passed += 1
        except Exception as exc:
            print(f"  FAIL  {path.name}")
            print(f"        {exc}")
            failed += 1

    return passed, failed


def main() -> None:
    total_passed = total_failed = 0

    for directory, model in VALIDATORS:
        print(f"\n{model.__name__} ({directory.name}/):")
        p, f = validate_dir(directory, model)
        total_passed += p
        total_failed += f

    print(f"\n{'='*40}")
    print(f"Total: {total_passed} passed, {total_failed} failed")

    if total_failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
