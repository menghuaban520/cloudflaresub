"""Check the user-visible archive, including links after extraction."""
import hashlib
import importlib.util
from pathlib import Path
import re
import tempfile
import unittest
from urllib.parse import urlsplit
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('packager', ROOT / 'scripts/package_shadowrocket.py')
packager = importlib.util.module_from_spec(spec)
spec.loader.exec_module(packager)


class PackageTests(unittest.TestCase):
    def test_archive_is_complete_and_reproducible(self):
        payload = packager.prepare(ROOT, '0' * 40)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            a, b = root / 'a.zip', root / 'b.zip'
            packager.write_zip(payload, a)
            packager.write_zip(payload, b)
            self.assertEqual(a.read_bytes(), b.read_bytes())
            with ZipFile(a) as archive:
                self.assertEqual([n for n in archive.namelist() if n.endswith('.conf')],
                                 ['configs/shadowrocket-rebuild.conf'])
                archive.extractall(root / 'unpacked')
            unpacked = root / 'unpacked'
            self.assertEqual((unpacked / 'configs/shadowrocket-rebuild.conf').read_bytes(),
                             (ROOT / 'configs/shadowrocket-rebuild.conf').read_bytes())
            for line in (unpacked / 'SHA256SUMS').read_text().splitlines():
                digest, name = line.split('  ', 1)
                self.assertEqual(hashlib.sha256((unpacked / name).read_bytes()).hexdigest(), digest)
            for file in unpacked.rglob('*.md'):
                for target in re.findall(r'\]\(([^)]+)\)', file.read_text()):
                    parsed = urlsplit(target)
                    if parsed.scheme or target.startswith(('#', '//')):
                        continue
                    self.assertTrue((file.parent / parsed.path).is_file(), (file.name, target))

    def test_missing_source_link_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in packager.FILES:
                p = root / name
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_bytes((ROOT / name).read_bytes())
            # Source-only links must exist, not be hidden by rewriting them.
            with self.assertRaises(ValueError):
                packager.prepare(root, '0' * 40)


if __name__ == '__main__':
    unittest.main()
