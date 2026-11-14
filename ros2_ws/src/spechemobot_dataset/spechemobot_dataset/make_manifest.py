import argparse
import json
import random
from pathlib import Path


def load_records(session_dir):
    metadata = session_dir / "metadata.jsonl"
    if not metadata.is_file():
        return []
    records = []
    with metadata.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def discover_sessions(root):
    root = Path(root)
    if not root.is_dir():
        return []
    return sorted(path for path in root.iterdir() if path.is_dir())


def collect_samples(root, session=""):
    root = Path(root)
    sessions = [root / session] if session else discover_sessions(root)
    samples = []
    for session_dir in sessions:
        for record in load_records(session_dir):
            if record.get("rgb") or record.get("thermal"):
                record = dict(record)
                record["session"] = session_dir.name
                record["session_dir"] = str(session_dir)
                samples.append(record)
    return sessions, samples


def build_manifest(root, val_fraction=0.2, seed=7, session=""):
    root = Path(root)
    sessions, samples = collect_samples(root, session=session)

    random.Random(seed).shuffle(samples)
    split_index = int(len(samples) * (1.0 - val_fraction))
    return {
        "version": 1,
        "root": str(root),
        "sessions": [path.name for path in sessions if path.is_dir()],
        "count": len(samples),
        "train": samples[:split_index],
        "val": samples[split_index:],
    }


def main():
    parser = argparse.ArgumentParser(description="Build a Spechemobot dataset manifest")
    parser.add_argument("--root", default="datasets/raw", help="Directory containing session folders")
    parser.add_argument("--output", default="datasets/processed/manifest.json", help="Manifest output file")
    parser.add_argument("--val-fraction", type=float, default=0.2, help="Validation split fraction")
    parser.add_argument("--seed", type=int, default=7, help="Shuffle seed")
    parser.add_argument("--session", default="", help="Only include a named session")
    args = parser.parse_args()

    manifest = build_manifest(
        args.root, val_fraction=args.val_fraction, seed=args.seed, session=args.session)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(
        f"Wrote {manifest['count']} samples to {output} "
        f"(train={len(manifest['train'])}, val={len(manifest['val'])})")


if __name__ == "__main__":
    main()
