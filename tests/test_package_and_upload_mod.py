import io
import hashlib
import sys
import tempfile
import threading
import unittest
import zipfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch


SKILL_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL_DIR / "scripts"))
import package_and_upload_mod as transfer


class PackageAndUploadModTests(unittest.TestCase):
    def test_cli_can_package_without_uploading(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            mod_dir = root / "Package Only"
            (mod_dir / "jsons").mkdir(parents=True)
            (mod_dir / "jsons" / "Nations.json").write_text("[]\n", encoding="utf-8")
            archive_path = root / "package-only.zip"

            with patch.object(sys, "argv", [
                "package_and_upload_mod.py", str(mod_dir), "--output", str(archive_path),
            ]):
                result = transfer.main()

            self.assertEqual(result, 0)
            self.assertTrue(archive_path.is_file())
            with zipfile.ZipFile(archive_path) as archive:
                self.assertEqual(archive.namelist(), ["Package Only/", "Package Only/jsons/Nations.json"])

    def test_package_and_upload_to_receiver(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            mod_dir = root / "Example Mod"
            (mod_dir / "rules").mkdir(parents=True)
            (mod_dir / "modOptions.json").write_text("{}\n")
            (mod_dir / "rules" / "Example.json").write_text("{}\n")
            archive_path = root / "Example Mod.zip"
            transfer.package_mod(mod_dir, archive_path)

            received = {}

            class Receiver(BaseHTTPRequestHandler):
                def do_POST(self):
                    size = int(self.headers["Content-Length"])
                    received["headers"] = self.headers
                    received["path"] = self.path
                    received["body"] = self.rfile.read(size)
                    self.send_response(200)
                    self.end_headers()
                    self.wfile.write(b"Mod installed.")

                def log_message(self, *_args):
                    pass

            server = ThreadingHTTPServer(("127.0.0.1", 0), Receiver)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                status, response = transfer.upload_mod(
                    archive_path,
                    f"http://127.0.0.1:{server.server_port}/",
                    "012345",
                )
            finally:
                server.shutdown()
                thread.join()
                server.server_close()

            self.assertEqual(status, 200)
            self.assertEqual(response, "Mod installed.")
            self.assertEqual(received["path"], "/upload")
            self.assertEqual(received["headers"]["Content-Type"], "application/zip")
            self.assertEqual(received["headers"]["X-Unciv-Access-Code"], "012345")
            self.assertEqual(received["headers"]["X-Mod-Name"], "Example%20Mod.zip")
            self.assertEqual(int(received["headers"]["Content-Length"]), len(received["body"]))
            with zipfile.ZipFile(io.BytesIO(received["body"])) as archive:
                self.assertIn("Example Mod/modOptions.json", archive.namelist())

    def test_refuses_public_receiver_address(self):
        with self.assertRaises(ValueError):
            transfer.receiver_target("http://8.8.8.8:1234/")

    def test_refuses_invalid_access_code(self):
        for invalid_code in ("1234", "01234567"):
            with self.subTest(code=invalid_code):
                with self.assertRaisesRegex(ValueError, "exactly 6 digits"):
                    transfer.upload_mod(Path("unused.zip"), "http://127.0.0.1:1234/", invalid_code)

    def test_does_not_overwrite_existing_zip(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            mod_dir = root / "Example Mod"
            mod_dir.mkdir()
            (mod_dir / "modOptions.json").write_text("{}\n")
            archive_path = root / "Example Mod.zip"
            archive_path.write_text("keep this file")

            with self.assertRaisesRegex(ValueError, "already exists"):
                transfer.package_mod(mod_dir, archive_path)

            self.assertEqual(archive_path.read_text(), "keep this file")

    def test_package_is_reproducible_and_excludes_platform_metadata(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            mod_dir = root / "Example Mod"
            (mod_dir / "jsons").mkdir(parents=True)
            (mod_dir / "jsons" / "Nations.json").write_text("[]\n", encoding="utf-8")
            (mod_dir / ".DS_Store").write_bytes(b"metadata")
            (mod_dir / "__MACOSX").mkdir()
            (mod_dir / "__MACOSX" / "junk").write_bytes(b"metadata")
            first = root / "first.zip"
            second = root / "second.zip"

            transfer.package_mod(mod_dir, first)
            transfer.package_mod(mod_dir, second)

            self.assertEqual(first.read_bytes(), second.read_bytes())
            self.assertEqual(transfer.sha256_file(first), hashlib.sha256(first.read_bytes()).hexdigest())
            with zipfile.ZipFile(first) as archive:
                self.assertEqual(archive.namelist(), ["Example Mod/", "Example Mod/jsons/Nations.json"])
                self.assertEqual({item.date_time for item in archive.infolist()}, {(1980, 1, 1, 0, 0, 0)})


if __name__ == "__main__":
    unittest.main()
