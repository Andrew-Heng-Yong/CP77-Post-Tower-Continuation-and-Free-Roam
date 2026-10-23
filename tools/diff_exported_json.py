"""Print bounded structural differences between two WolvenKit JSON exports."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def differences(left: object, right: object, path: str = "$", limit: int = 20):
    if limit <= 0:
        return
    if type(left) is not type(right):
        yield path, left, right
    elif isinstance(left, dict):
        for key in sorted(left.keys() | right.keys()):
            child = f"{path}.{key}"
            if key not in left or key not in right:
                yield child, left.get(key, "<missing>"), right.get(key, "<missing>")
            else:
                yield from differences(left[key], right[key], child, limit)
    elif isinstance(left, list):
        if len(left) != len(right):
            yield f"{path}.length", len(left), len(right)
        for index, (old, new) in enumerate(zip(left, right)):
            yield from differences(old, new, f"{path}[{index}]", limit)
    elif left != right:
        yield path, left, right


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("original", type=Path)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args()
    original = json.loads(args.original.read_text(encoding="utf-8-sig"))
    candidate = json.loads(args.candidate.read_text(encoding="utf-8-sig"))
    count = 0
    for path, old, new in differences(original, candidate):
        if count < args.limit:
            print(f"{path}: {old!r} -> {new!r}")
        count += 1
    print(f"differences={count}")


if __name__ == "__main__":
    main()
