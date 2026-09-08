"""Offline regression checks, NOT the Shadowrocket parser or an iOS leak test.
Run: python3 tests/shadowrocket_config_test.py
Remote lists, GEOIP databases, and live DNS/packet routing are not simulated.
"""
import ipaddress
from pathlib import Path
import unittest
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / 'configs/shadowrocket-pro.conf'


def parse(text):
    sections, section = {}, None
    for number, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith(('#', ';')):
            continue
        if line.startswith('[') and line.endswith(']'):
            section = line[1:-1]
            if section in sections:
                raise ValueError(f'duplicate section on line {number}')
            sections[section] = []
        elif section is None:
            raise ValueError(f'content outside a section on line {number}')
        else:
            sections[section].append(line)
    return sections


def properties(lines):
    result = {}
    for line in lines:
        key, value = (s.strip() for s in line.split('=', 1))
        if key in result:
            raise ValueError(f'duplicate key: {key}')
        result[key] = value
    return result


def inline_route(rules, domain):
    """Conservative offline check: skip all remote rules and GEOIP lookups."""
    for line in rules:
        parts = [s.strip() for s in line.split(',')]
        kind = parts[0]
        if kind == 'FINAL':
            return parts[1]
        if kind == 'DOMAIN' and domain == parts[1]:
            return parts[2]
        if kind == 'DOMAIN-SUFFIX':
            suffix = parts[1]
            if domain == suffix or domain.endswith('.' + suffix):
                return parts[2]
    return None


class ConfigTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = CONFIG.read_text(encoding='utf-8')
        cls.sections = parse(cls.text)
        cls.general = properties(cls.sections['General'])
        cls.hosts = properties(cls.sections['Host'])
        cls.rules = cls.sections['Rule']

    def test_mirror_identical(self):
        self.assertEqual(CONFIG.read_bytes(), (ROOT / 'public/shadowrocket-pro.conf').read_bytes())

    def test_only_expected_sections(self):
        self.assertEqual(set(self.sections), {'General', 'Proxy', 'Proxy Group', 'Rule', 'Host'})

    def test_manual_node_and_no_credentials(self):
        self.assertEqual(self.sections['Proxy'], [])
        self.assertEqual(self.sections['Proxy Group'], [])
        self.assertNotIn('skip-cert-verify = true', self.text)

    def test_encrypted_dns_only(self):
        for key in ('dns-server', 'direct-dns-server', 'fallback-dns-server', 'proxy-dns-server'):
            values = self.general[key].split(',')
            self.assertTrue(values)
            for value in values:
                parsed = urlparse(value.strip())
                self.assertEqual(parsed.scheme, 'https', (key, value))
                self.assertEqual(parsed.path, '/dns-query', (key, value))

    def test_general_and_fallback_dns_use_proxy(self):
        for key in ('dns-server', 'fallback-dns-server'):
            for value in self.general[key].split(','):
                self.assertIn('proxy', urlparse(value.strip()).fragment.split('&'), key)

    def test_proxy_doh_does_not_probe_http3(self):
        for key in ('dns-server', 'fallback-dns-server'):
            for value in self.general[key].split(','):
                options = urlparse(value.strip()).fragment.split('&')
                self.assertIn('proxy', options)
                self.assertIn('no-h3', options)

    def test_bootstrap_has_no_proxy_dependency(self):
        for key in ('proxy-dns-server', 'direct-dns-server'):
            for value in self.general[key].split(','):
                host = urlparse(value.strip()).hostname
                self.assertNotIn('proxy', urlparse(value.strip()).fragment)
                self.assertIn(host, self.hosts)
                ipaddress.ip_address(self.hosts[host])

    def test_no_system_or_direct_connection_fallback(self):
        for key in ('dns-direct-system', 'dns-fallback-system', 'dns-direct-fallback-proxy'):
            self.assertEqual(self.general[key], 'false', key)
        self.assertEqual(self.general.get('udp-policy-not-supported-behaviour'), 'REJECT')
        self.assertEqual(self.general.get('close-if-proxy-chain-missing'), 'true')

    def test_capture_both_ip_families(self):
        self.assertEqual(self.general['bypass-system'], 'false')
        self.assertEqual(self.general['ipv6'], 'true')
        self.assertEqual(self.general['prefer-ipv6'], 'false')
        self.assertEqual(self.general['hijack-dns'], ':53')
        included = set(self.general['tun-included-routes'].split(','))
        self.assertTrue({'0.0.0.0/1', '128.0.0.0/1', '::/1', '8000::/1',
                         '192.168.1.1/32', 'fe80::1/128'} <= included)

    def test_no_router_dns_exclusions(self):
        networks = [ipaddress.ip_network(x) for x in self.general['tun-excluded-routes'].split(',')]
        for raw in ('192.168.1.1', '192.168.31.1', '10.0.0.1', '100.64.0.1', 'fe80::1'):
            address = ipaddress.ip_address(raw)
            self.assertFalse(any(address in n for n in networks if n.version == address.version), raw)

    def test_no_unconditional_quic_block(self):
        self.assertNotIn('block-quic', self.general)
        self.assertFalse(any('DST-PORT,443,REJECT' in x for x in self.rules))

    def test_domain_routing_without_forced_dns(self):
        self.assertEqual(self.general['always-ip-address'], 'false')
        for rule in self.rules:
            if rule.split(',')[0] in ('IP-CIDR', 'IP-CIDR6', 'GEOIP'):
                self.assertIn('no-resolve', rule.split(','), rule)

    def test_final_is_proxy_and_last(self):
        self.assertEqual(self.rules[-1], 'FINAL,PROXY')
        self.assertEqual(sum(x.startswith('FINAL,') for x in self.rules), 1)

    def test_ad_overrides_work(self):
        direct_override = next(i for i, r in enumerate(self.rules) if '/user-direct.list,' in r)
        first_ad = next(i for i, r in enumerate(self.rules) if ',REJECT' in r)
        self.assertLess(direct_override, first_ad)
        self.assertFalse(any('pre-matching' in r for r in self.rules))
        self.assertEqual(inline_route(self.rules, 'ad.toutiao.com'), 'REJECT')
        self.assertEqual(inline_route(self.rules, 'ads-img-al.xhscdn.com'), 'REJECT')

    def test_core_routes_survive_missing_remote_lists(self):
        domestic = ('www.baidu.com', 'www.taobao.com', 'api.alipay.com', 'wx.qq.com',
                    'www.bilibili.com', 'api.douyin.com', 'www.jd.com', 'www.zhihu.com',
                    'www.xiaohongshu.com', 'www.12306.cn', 'www.mi.com', 'www.mihoyo.com')
        foreign = ('chatgpt.com', 'api.openai.com', 'claude.ai', 'api.anthropic.com',
                   'grok.com', 'api.x.ai', 'www.google.com', 'www.google.cn',
                   'www.google.com.hk', 'www.youtube.com', 'github.com',
                   'raw.githubusercontent.com', 'x.com', 'video.twimg.com',
                   'www.tiktok.com', 'dnsleaktest.com', 'browserleaks.com',
                   'ipleak.net', 'telegram.org', 'www.paypal.com')
        for domain in domestic:
            with self.subTest(domain=domain):
                self.assertEqual(inline_route(self.rules, domain), 'DIRECT')
        for domain in foreign:
            with self.subTest(domain=domain):
                self.assertEqual(inline_route(self.rules, domain), 'PROXY')

    def test_foreign_guards_before_domestic_lists(self):
        boundary = next(i for i, r in enumerate(self.rules) if '/china-core.list,' in r)
        for domain in ('chatgpt.com', 'openai.com', 'claude.ai', 'x.ai', 'grok.com',
                       'google.cn', 'githubusercontent.com', 'tiktok.com', 'twimg.com'):
            self.assertIn(f'DOMAIN-SUFFIX,{domain},PROXY', self.rules[:boundary])

    def test_domain_boundary_and_unknown_fail_closed(self):
        for domain in ('notbaidu.com', 'taobao.com.evil.example', 'unknown.example'):
            self.assertEqual(inline_route(self.rules, domain), 'PROXY')

    def test_no_broad_user_agent_direct_list(self):
        self.assertFalse(any('/ChinaMax/ChinaMax.list,' in r for r in self.rules))
        self.assertFalse(any(r.startswith('USER-AGENT,') for r in self.rules))

    def test_remote_sources_and_update_url(self):
        for rule in self.rules:
            parts = rule.split(',')
            if parts[0] in ('RULE-SET', 'DOMAIN-SET') and parts[1].startswith('https:'):
                url = urlparse(parts[1])
                self.assertEqual(url.hostname, 'raw.githubusercontent.com')
                self.assertTrue(url.path.startswith(('/menghuaban520/cloudflaresub/', '/blackmatrix7/ios_rule_script/')))
                interval = next(x for x in parts if x.startswith('update-interval='))
                self.assertGreaterEqual(int(interval.split('=')[1]), 3600)
        self.assertEqual(self.general['update-url'],
                         'https://raw.githubusercontent.com/menghuaban520/cloudflaresub/main/configs/shadowrocket-pro.conf')


if __name__ == '__main__':
    unittest.main(verbosity=2)
