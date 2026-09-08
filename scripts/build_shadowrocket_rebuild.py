"""Build the fresh baseline without reading any v5 configuration."""
import argparse
from pathlib import Path
from build_shadowrocket import read_rules

ROOT = Path(__file__).resolve().parents[1]
SOURCES = {
    '# @USER_PROXY@': ('user-proxy.list', 'PROXY'),
    '# @USER_DIRECT@': ('user-direct.list', 'DIRECT'),
    '# @CHINA_CORE@': ('china-core.list', 'DIRECT'),
}
# Shared clouds and country suffixes are not proof a service is domestic.
EXCLUDED_CORE = {'cn', 'xn--fiqs8s', 'xn--55qx5d', 'xn--io0a7i',
                 'aliyuncs.com', 'myqcloud.com', 'qcloud.com', 'bytedns.net',
                 'bytetos.com', 'bcebos.com'}


def build():
    text = (ROOT / 'configs/rebuild/base.conf').read_text()
    for marker, (name, policy) in SOURCES.items():
        if text.count(marker) != 1:
            raise ValueError(f'Missing or duplicate template marker: {marker}')
        rules = read_rules((ROOT / 'configs/rules' / name).read_text(), policy)
        if name == 'china-core.list':
            rules = [r for r in rules if r.split(',')[1] not in EXCLUDED_CORE]
        text = text.replace(marker, '\n'.join(rules))
    return text.encode()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    data = build()
    for name in ('configs/shadowrocket-rebuild.conf', 'public/shadowrocket-rebuild.conf'):
        path = ROOT / name
        if args.check:
            if not path.exists() or path.read_bytes() != data:
                parser.exit(1, f'Stale artifact: {name}\n')
        else:
            path.write_bytes(data)
    print('Rebuild 1.0-beta.2: ' + ('verified' if args.check else 'built'))


if __name__ == '__main__':
    main()
