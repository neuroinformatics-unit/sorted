"""Download the pinned test datasets using only the Python standard library."""

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
import shutil
import stat
import time
from urllib.parse import quote, urlsplit, urlunsplit
from urllib.request import Request, urlopen
import zipfile
import zlib


DATA = Path(__file__).resolve().parents[1] / "tests" / "data"
CHUNK = 1024 * 1024


def inside(root, relative):
    target = (root / relative).resolve()
    if not target.is_relative_to(root.resolve()):
        raise ValueError(f"Path escapes data directory: {relative}")
    return target


def checksum(path, algorithm):
    digest = hashlib.new("sha1" if algorithm == "git-sha1" else algorithm)
    if algorithm == "git-sha1":
        digest.update(f"blob {path.stat().st_size}\0".encode())
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(CHUNK), b""):
            digest.update(chunk)
    return digest.hexdigest()


def valid(path, entry):
    if not path.is_file() or path.stat().st_size != entry["size"]:
        return False
    algorithm, expected = entry["checksum"].split(":", 1)
    return checksum(path, algorithm) == expected


def fetch(entry, verify_only):
    path = inside(DATA, entry["path"])
    if valid(path, entry):
        return
    if verify_only:
        raise ValueError(f"Missing or corrupt file: {entry['path']}")
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_name(path.name + ".part")
    for attempt in range(3):
        try:
            url = urlsplit(entry["url"])
            url = urlunsplit(url._replace(path=quote(url.path, safe="/%")))
            request = Request(url, headers={"User-Agent": "allsorted-test-data/1"})
            with urlopen(request, timeout=60) as response, partial.open("wb") as out:
                shutil.copyfileobj(response, out, CHUNK)
            if not valid(partial, entry):
                raise ValueError(f"Checksum or size mismatch: {entry['path']}")
            partial.replace(path)
            return
        except Exception:
            if attempt == 2:
                raise
            time.sleep(attempt + 1)


def extract(entry, verify_only):
    """Keep the upstream hierarchy; verify every extracted member against its CRC."""
    root = inside(DATA, entry["extract_to"])
    records = []
    with zipfile.ZipFile(inside(DATA, entry["path"])) as archive:
        for member in archive.infolist():
            relative = member.filename
            prefix = entry.get("strip_prefix", "")
            if prefix:
                if not relative.startswith(prefix):
                    raise ValueError(f"Unexpected archive member: {relative}")
                relative = relative[len(prefix):]
            path = inside(root, relative)
            if member.is_dir():
                continue
            if stat.S_ISLNK(member.external_attr >> 16):
                raise ValueError(f"Archive contains a symlink: {member.filename}")
            matches = path.is_file() and path.stat().st_size == member.file_size
            if matches:
                crc = 0
                with path.open("rb") as stream:
                    for chunk in iter(lambda: stream.read(CHUNK), b""):
                        crc = zlib.crc32(chunk, crc)
                matches = crc == member.CRC
            if not matches:
                if verify_only:
                    raise ValueError(f"Missing or corrupt extracted file: {path}")
                path.parent.mkdir(parents=True, exist_ok=True)
                partial = path.with_name(path.name + ".part")
                # ZipExtFile checks the CRC when the member has been read in full.
                with archive.open(member) as source, partial.open("wb") as target:
                    shutil.copyfileobj(source, target, CHUNK)
                partial.replace(path)
            records.append({
                "path": path.relative_to(DATA).as_posix(),
                "size": path.stat().st_size,
                "sha256": checksum(path, "sha256"),
                "archive": entry["path"],
                "member": member.filename,
            })
    return records


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-only", action="store_true",
                        help="Check downloads and extracted files without network access.")
    args = parser.parse_args()
    if args.verify_only:
        inventory = json.loads((DATA / "inventory.json").read_text(encoding="utf-8-sig"))
        verified = 0
        for entry in inventory["files"]:
            path = inside(DATA, entry["path"])
            # Archive caches may be removed after extraction.
            if entry["path"].startswith(".archives/") and not path.exists():
                continue
            if not valid(path, {"size": entry["size"], "checksum": "sha256:" + entry["sha256"]}):
                raise ValueError(f"Missing or corrupt file: {entry['path']}")
            verified += 1
        print(f"Verified {verified} local files against the SHA-256 inventory.")
        return
    manifest = json.loads((DATA / "manifest.json").read_text(encoding="utf-8-sig"))
    entries = manifest["files"]
    total = sum(entry["size"] for entry in entries)
    print(f"{len(entries)} source files, {total / 1_000_000:.1f} MB", flush=True)
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = [pool.submit(fetch, entry, args.verify_only) for entry in entries]
        for number, future in enumerate(as_completed(futures), 1):
            future.result()
            if number % 10 == 0 or number == len(entries):
                print(f"Verified {number}/{len(entries)} source files", flush=True)
    inventory = []
    for entry in entries:
        path = inside(DATA, entry["path"])
        inventory.append({
            "path": entry["path"],
            "size": entry["size"],
            "sha256": checksum(path, "sha256"),
            "url": entry["url"],
        })
        if "extract_to" in entry:
            inventory.extend(extract(entry, args.verify_only))
    inventory_path = DATA / "inventory.json"
    if args.verify_only:
        saved = json.loads(inventory_path.read_text(encoding="utf-8"))["files"]
        if saved != inventory:
            raise ValueError("Local files differ from the saved SHA-256 inventory")
    else:
        inventory_path.write_text(
            json.dumps({"schema_version": 1, "files": inventory}, indent=2) + "\n",
            encoding="utf-8",
        )
    print(f"All {len(inventory)} downloaded/extracted files verified.", flush=True)


if __name__ == "__main__":
    main()

