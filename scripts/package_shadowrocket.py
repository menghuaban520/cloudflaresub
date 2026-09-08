"""Package the current Rebuild config and portable guides, without legacy configs."""
import argparse
import hashlib
import re
import subprocess
from pathlib import Path, PurePosixPath
from urllib.parse import urlsplit
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

ROOT = Path(__file__).resolve().parents[1]
FILES = ['configs/shadowrocket-rebuild.conf', 'LICENSE'] + [
    'docs/shadowrocket/' + name + '.md' for name in
    ('README', 'CUSTOMIZE', 'TROUBLESHOOTING', 'VALIDATION', 'MAINTAINING', 'REBUILD', 'CHANGELOG')
]


def prepare(root, revision):
    if not re.fullmatch(r'[0-9a-f]{40}', revision):
        raise ValueError('Expected a full Git commit SHA')
    payload = {name: (root / name).read_bytes() for name in FILES}
    for name in FILES:
        if not name.endswith('.md'):
            continue

        def fix_link(match):
            target = match.group(1)
            parsed = urlsplit(target)
            if parsed.scheme or target.startswith(('#', '//')):
                return match.group(0)
            path = (root / name).parent.joinpath(parsed.path).resolve()
            relative = path.relative_to(root.resolve()).as_posix()
            if not path.is_file():
                raise ValueError(f'Broken source link: {name}: {target}')
            if relative in payload:
                return match.group(0)
            url = f'https://github.com/menghuaban520/cloudflaresub/blob/{revision}/{relative}'
            if parsed.fragment:
                url += '#' + parsed.fragment
            return '](' + url + ')'

        text = payload[name].decode('utf-8')
        payload[name] = re.sub(r'\]\(([^)]+)\)', fix_link, text).encode('utf-8')
    payload['START-HERE.txt'] = (
        '花瓣 Rebuild：先阅读 docs/shadowrocket/README.md\n'
        '导入 configs/shadowrocket-rebuild.conf；这不是节点订阅。\n'
        '未打包的维护资料链接指向 GitHub，需要联网。\n'
        f'Source commit: {revision}\n'
        'SHA256SUMS 用于检查文件是否变化，不是签名或安全认证。\n'
    ).encode('utf-8')
    payload['SHA256SUMS'] = ''.join(
        f'{hashlib.sha256(data).hexdigest()}  {name}\n'
        for name, data in sorted(payload.items())
    ).encode('utf-8')
    return payload


def write_zip(payload, destination):
    destination.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(destination, 'w') as archive:
        for name, content in sorted(payload.items()):
            if PurePosixPath(name).is_absolute() or '..' in PurePosixPath(name).parts:
                raise ValueError('Unsafe archive path')
            info = ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, content)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'dist/huaban-rebuild-beta.zip')
    args = parser.parse_args()
    revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    # Keep provenance accurate: users should commit packaged inputs first.
    changed = subprocess.check_output(['git', 'status', '--porcelain', '--', *FILES], cwd=ROOT, text=True)
    if changed.strip():
        parser.exit(1, 'Commit package inputs before packaging.\n')
    write_zip(prepare(ROOT, revision), args.output)
    print(args.output)


if __name__ == '__main__':
    main()
