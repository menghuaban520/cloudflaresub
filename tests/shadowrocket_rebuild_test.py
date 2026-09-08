"""Static policy checks only; does not reproduce iPhone connectivity."""
from pathlib import Path
import unittest
from urllib.parse import urlparse
from shadowrocket_config_test import parse, properties, inline_route

ROOT = Path(__file__).resolve().parents[1]


class RebuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = (ROOT / 'configs/shadowrocket-rebuild.conf').read_bytes()
        cls.sections = parse(cls.data.decode())
        cls.general = properties(cls.sections['General'])
        cls.rules = cls.sections['Rule']

    def test_self_contained_and_no_credentials(self):
        self.assertEqual(set(self.sections), {'General', 'Rule', 'Host'})
        self.assertEqual(self.data, (ROOT / 'public/shadowrocket-rebuild.conf').read_bytes())
        self.assertNotIn('update-url', self.general)
        self.assertNotIn('tun-included-routes', self.general)
        self.assertFalse(any(r.startswith(('RULE-SET,', 'DOMAIN-SET,')) for r in self.rules))

    def test_encrypted_bootstrap_without_proxy_dependency(self):
        hosts = properties(self.sections['Host'])
        for key in ('dns-server', 'fallback-dns-server', 'proxy-dns-server'):
            for raw in self.general[key].split(','):
                url = urlparse(raw)
                self.assertEqual(url.scheme, 'https')
                self.assertEqual(url.fragment, 'no-h3')
                self.assertIn(url.hostname, hosts)
                self.assertEqual(inline_route(self.rules, url.hostname), 'DIRECT')

    def test_failure_guards(self):
        for key in ('dns-direct-system', 'dns-fallback-system', 'dns-direct-fallback-proxy', 'always-ip-address'):
            self.assertEqual(self.general[key], 'false')
        self.assertEqual(self.general['udp-policy-not-supported-behaviour'], 'REJECT')
        self.assertEqual(self.general['close-if-proxy-chain-missing'], 'true')
        self.assertEqual(self.rules[-1], 'FINAL,PROXY')
        self.assertEqual(sum(r.startswith('FINAL,') for r in self.rules), 1)

    def test_routes_and_boundaries(self):
        for domain in ('www.baidu.com', 'www.taobao.com', 'wx.qq.com', 'www.bilibili.com', 'api.douyin.com', 'www.jd.com', 'www.12306.com'):
            self.assertEqual(inline_route(self.rules, domain), 'DIRECT', domain)
        for domain in ('chatgpt.com', 'api.openai.com', 'claude.ai', 'google.cn', 'raw.githubusercontent.com', 'x.com', 'tiktok.com', 'notbaidu.com', 'qq.com.evil.example', 'unknown.example', 'unknown.cn', 'unknown.aliyuncs.com'):
            self.assertEqual(inline_route(self.rules, domain), 'PROXY', domain)
        self.assertEqual(inline_route(self.rules, 'ad.toutiao.com'), 'REJECT')

    def test_domestic_apps_and_shared_cdn_boundaries(self):
        for domain in ('wx.qlogo.cn', 'servicewechat.com', 'www.wechatpay.com',
                       'www.weixinbridge.com', 'video.idouyinvod.com',
                       'video.ixiguavideo.com', 'lf3-static.bytednsdoc.com',
                       'v5-dy-o-abtest.zjcdn.com', 'www.kugou.com',
                       'img.kgimg.com', 'www.kugou.net', 'www.kugoo.com',
                       'kglink.cn', 'www.kugouipv6.com', 'www.kuwo.cn',
                       'www.koowo.com', 'www.koowo.cn'):
            with self.subTest(domain=domain):
                self.assertEqual(inline_route(self.rules, domain), 'DIRECT')
                self.assertEqual(inline_route(self.rules, domain + '.evil.example'), 'PROXY')
        for domain in ('unknown.zjcdn.com', 'unknown.bytednsdoc.com', 'tiktokcdn.com'):
            self.assertEqual(inline_route(self.rules, domain), 'PROXY')


if __name__ == '__main__':
    unittest.main()
