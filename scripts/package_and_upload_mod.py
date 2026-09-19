#!/usr/bin/env python3
"""Package one Unciv Mod folder and optionally upload it to the iOS app receiver."""

from __future__ import annotations

import argparse
import hashlib
import ipaddress
import os
import sys
import zipfile
from http.client import HTTPConnection, HTTPException
from pathlib import Path
from urllib.parse import quote, urlsplit


MAX_UPLOAD_BYTES = 256 * 1024 * 1024
CHUNK_SIZE = 1024 * 1024
PRIVATE_NETWORKS = tuple(
    ipaddress.ip_network(network)
    for network in ("10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16")
)
ZIP_TIMESTAMP = (1980, 1, 1, 0, 0, 0)
EXCLUDED_NAMES = {".DS_Store", "Thumbs.db", "desktop.ini"}
EXCLUDED_DIRECTORIES = {".git", "__MACOSX", "__pycache__"}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(CHUNK_SIZE), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _zip_info(name: str, is_directory: bool = False) -> zipfile.ZipInfo:
    if is_directory and not name.endswith("/"):
        name += "/"
    info = zipfile.ZipInfo(name, ZIP_TIMESTAMP)
    info.create_system = 3
    info.compress_type = zipfile.ZIP_STORED if is_directory else zipfile.ZIP_DEFLATED
    mode = 0o40755 if is_directory else 0o100644
    info.external_attr = (mode << 16) | (0x10 if is_directory else 0)
    return info


def package_mod(mod_dir: Path, archive_path: Path) -> None:
    if mod_dir.is_symlink() or not mod_dir.is_dir():
        raise ValueError(f"Mod folder does not exist or is a symlink: {mod_dir}")
    mod_dir = mod_dir.resolve()
    archive_path = archive_path.resolve()
    try:
        archive_path.relative_to(mod_dir)
    except ValueError:
        pass
    else:
        raise ValueError("ZIP output must be outside the Mod folder")
    if archive_path.exists():
        raise ValueError(f"ZIP output already exists: {archive_path}; choose another --output path")

    files: list[Path] = []
    for root, directories, filenames in os.walk(mod_dir, followlinks=False):
        root_path = Path(root)
        for name in directories + filenames:
            entry = root_path / name
            if entry.is_symlink():
                raise ValueError(f"Mod folder contains a symlink: {entry}")
        directories[:] = sorted(name for name in directories if name not in EXCLUDED_DIRECTORIES)
        files.extend(
            root_path / name
            for name in sorted(filenames)
            if name not in EXCLUDED_NAMES and not name.endswith((".pyc", ".pyo"))
        )

    if not files:
        raise ValueError(f"Mod folder contains no files: {mod_dir}")

    archive_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive_path, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        archive.writestr(_zip_info(f"{mod_dir.name}/", is_directory=True), b"")
        for file_path in files:
            relative_path = file_path.relative_to(mod_dir).as_posix()
            archive.writestr(_zip_info(f"{mod_dir.name}/{relative_path}"), file_path.read_bytes(), compresslevel=9)

    if archive_path.stat().st_size > MAX_UPLOAD_BYTES:
        archive_path.unlink()
        raise ValueError("Packaged ZIP exceeds the receiver's 256 MiB limit")


def receiver_target(receiver_url: str) -> tuple[str, int]:
    try:
        parsed = urlsplit(receiver_url)
        address = ipaddress.IPv4Address(parsed.hostname or "")
        port = parsed.port
    except ValueError as error:
        raise ValueError("Use the HTTP IPv4 address and port displayed by Unciv") from error

    if parsed.scheme != "http" or parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError("Receiver URL must be the plain HTTP address displayed by Unciv")
    if parsed.path not in ("", "/") or port is None:
        raise ValueError("Use the receiver's base URL, including its port")
    if not address.is_loopback and not any(address in network for network in PRIVATE_NETWORKS):
        raise ValueError("Receiver must be on a private IPv4 network or localhost")
    return str(address), port


def upload_mod(archive_path: Path, receiver_url: str, access_code: str) -> tuple[int, str]:
    if len(access_code) != 6 or not access_code.isascii() or not access_code.isdigit():
        raise ValueError("Access code must contain exactly 6 digits")
    if not archive_path.is_file() or archive_path.stat().st_size <= 0:
        raise ValueError(f"ZIP file does not exist or is empty: {archive_path}")
    size = archive_path.stat().st_size
    if size > MAX_UPLOAD_BYTES:
        raise ValueError("ZIP file exceeds the receiver's 256 MiB limit")

    host, port = receiver_target(receiver_url)
    connection = HTTPConnection(host, port, timeout=120)
    try:
        connection.putrequest("POST", "/upload")
        connection.putheader("Content-Type", "application/zip")
        connection.putheader("Content-Length", str(size))
        connection.putheader("X-Unciv-Access-Code", access_code)
        connection.putheader("X-Mod-Name", quote(archive_path.name, safe=""))
        connection.putheader("Connection", "close")
        connection.endheaders()
        with archive_path.open("rb") as archive:
            while chunk := archive.read(CHUNK_SIZE):
                connection.send(chunk)
        response = connection.getresponse()
        body = response.read(64 * 1024).decode("utf-8", errors="replace")
        return response.status, body
    finally:
        connection.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mod_dir", type=Path, help="path to the Mod folder")
    parser.add_argument("--receiver-url", help="HTTP base URL displayed by Unciv; requires --access-code")
    parser.add_argument("--access-code", help="6-digit code displayed by Unciv; requires --receiver-url")
    parser.add_argument("--output", type=Path, help="ZIP output path (defaults beside the Mod folder)")
    args = parser.parse_args()
    if (args.receiver_url is None) != (args.access_code is None):
        parser.error("--receiver-url and --access-code must be supplied together")

    mod_dir = args.mod_dir.expanduser()
    archive_path = args.output.expanduser() if args.output else mod_dir.parent / f"{mod_dir.name}.zip"
    try:
        package_mod(mod_dir, archive_path)
        print(f"Packaged Mod: {archive_path.absolute()}")
        print(f"SHA-256: {sha256_file(archive_path)}")
        if args.receiver_url is None:
            return 0
        status, body = upload_mod(archive_path, args.receiver_url, args.access_code)
    except (HTTPException, OSError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    print(f"Receiver response ({status}): {body.strip()}")
    if status != 200:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
