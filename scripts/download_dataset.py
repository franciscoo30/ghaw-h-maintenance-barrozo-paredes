#!/usr/bin/env python3
"""Download the five public GHAW-H tables at an immutable Hugging Face commit.

Standard-library only; no credentials are required. Existing files are verified.
The manifest is created on the first download and must be preserved with results.
"""
import argparse
import hashlib
import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TABLES = ["lock_file_snapshot", "repository", "source_markdown_file_history",
          "source_markdown_file_snapshot", "source_markdown_file_version"]


def sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--revision", required=True, help="Full immutable Hugging Face commit SHA")
    args = parser.parse_args()
    if len(args.revision) != 40 or any(c not in "0123456789abcdef" for c in args.revision):
        parser.error("revision must be a full 40-character lowercase commit SHA")
    raw = ROOT / "data" / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    manifest_path = ROOT / "data" / "manifest.json"
    old = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    if old and old["revision"] != args.revision:
        raise RuntimeError("Existing manifest uses another revision; use a new package directory")
    manifest = {"dataset": "pavtch/GHAW-H", "revision": args.revision,
                "downloaded_at_utc": old.get("downloaded_at_utc", datetime.now(timezone.utc).isoformat()),
                "dataset_doi": "10.5281/zenodo.22084012", "files": {}}
    for table in TABLES:
        rel = f"data/{table}.parquet"
        url = f"https://huggingface.co/datasets/pavtch/GHAW-H/resolve/{args.revision}/{rel}"
        dest = raw / f"{table}.parquet"
        if not dest.exists():
            print(f"Downloading {table}", flush=True)
            temp = dest.with_suffix(".parquet.partial")
            with urllib.request.urlopen(url, timeout=180) as response, temp.open("wb") as f:
                while chunk := response.read(1024 * 1024):
                    f.write(chunk)
            temp.replace(dest)
        digest = sha256(dest)
        if table in old.get("files", {}) and digest != old["files"][table]["sha256"]:
            raise RuntimeError(f"Checksum mismatch for {table}")
        manifest["files"][table] = {"url": url, "bytes": dest.stat().st_size, "sha256": digest}
        print(f"{table}: {dest.stat().st_size:,} bytes, sha256 {digest}", flush=True)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    for rel, name in [("README.md", "dataset_card.md"), ("docs/table_dictionary.md", "table_dictionary.md")]:
        url = f"https://huggingface.co/datasets/pavtch/GHAW-H/resolve/{args.revision}/{rel}"
        dest = ROOT / "data" / name
        if not dest.exists():
            with urllib.request.urlopen(url, timeout=60) as response:
                dest.write_bytes(response.read())


if __name__ == "__main__":
    main()
