"""Offline build/routing regression checks; not an iOS networking emulator."""
import importlib.util
from pathlib import Path
import unittest
from shadowrocket_config_test import parse, properties, inline_route

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('builder', ROOT / 'scripts/build_shadowrocket.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class BuildTests(unittest.TestCase):
    def setUp(self):
        self.source = (ROOT / 'configs/shadowrocket-pro.conf').read_text()
        self.lists = {name: (ROOT / 'configs/rules' / name).read_text() for name in builder.LOCAL}

    def rules(self, ads=True):
        return parse(builder.render(self.source, self.lists, ads))['Rule']

    def test_reproducible_committed_outputs(self):
        self.assertEqual(builder.artifacts(), builder.artifacts())
        for name, content in builder.artifacts().items():
            self.assertEqual((ROOT / name).read_bytes(), content, name)

    def test_no_remote_resources_or_auto_update(self):
        for ads in (True, False):
            sections = parse(builder.render(self.source, self.lists, ads))
            self.assertNotIn('update-url', properties(sections['General']))
            self.assertFalse(any(r.startswith(('RULE-SET,', 'DOMAIN-SET,')) for r in sections['Rule']))
            self.assertEqual(sections['Proxy'], [])
            self.assertEqual(sections['Proxy Group'], [])

    def test_long_tail_and_foreign_priority(self):
        for ads in (True, False):
            rules = self.rules(ads)
            for domain in ('img.pddpic.com', 'api.qpic.cn', 'www.alipan.com', 'www.1688.com'):
                self.assertEqual(inline_route(rules, domain), 'DIRECT')
            for domain in ('google.cn', 'chatgpt.com', 'raw.githubusercontent.com', 'unknown.example', 'notbaidu.com', 'qq.com.evil.example'):
                self.assertEqual(inline_route(rules, domain), 'PROXY')
            self.assertEqual(rules[-1], 'FINAL,PROXY')

    def test_user_override_precedes_ads_and_domestic(self):
        self.lists['user-direct.list'] += '\nDOMAIN,ad.toutiao.com\n'
        self.lists['user-proxy.list'] += '\nDOMAIN,api.qq.com\n'
        rules = self.rules()
        self.assertEqual(inline_route(rules, 'ad.toutiao.com'), 'DIRECT')
        self.assertEqual(inline_route(rules, 'api.qq.com'), 'PROXY')

    def test_noads_only_removes_domain_rejection(self):
        normal = parse(builder.render(self.source, self.lists))
        clean = parse(builder.render(self.source, self.lists, False))
        for section in ('General', 'Host'):
            self.assertEqual(normal[section], clean[section])
        self.assertEqual(clean['Rule'], [r for r in normal['Rule'] if r.split(',')[-1] != 'REJECT'])
        self.assertEqual(inline_route(normal['Rule'], 'ad.toutiao.com'), 'REJECT')
        self.assertEqual(inline_route(clean['Rule'], 'ad.toutiao.com'), 'DIRECT')

    def test_bad_rule_and_injection_rejected(self):
        for line in ('DOMAIN,example.com,DIRECT', 'FINAL,DIRECT', 'DOMAIN,https://example.com', 'DOMAIN,*.com', 'DOMAIN,-bad.com', 'DOMAIN,example..com', '[Proxy]', 'DOMAIN,example.com\npassword = secret'):
            with self.subTest(line=line), self.assertRaises(ValueError):
                builder.read_rules(line, 'DIRECT')

    def test_new_remote_dependency_rejected(self):
        with self.assertRaises(ValueError):
            builder.render(self.source.replace('FINAL,PROXY', 'RULE-SET,https://example.com/unknown.list,DIRECT\nFINAL,PROXY'), self.lists)

    def test_missing_or_wrong_policy_list_rejected(self):
        for source in (self.source.replace('user-direct.list', 'missing.list'), self.source.replace('user-direct.list,DIRECT', 'user-direct.list,PROXY')):
            with self.assertRaises(ValueError):
                builder.render(source, self.lists)

    def test_nodes_and_unexpected_sections_rejected(self):
        for source in (self.source.replace('[Proxy]\n', '[Proxy]\nsecret-node = ss, example.com, 443\n'), self.source + '\n[MITM]\n'):
            with self.assertRaises(ValueError):
                builder.render(source, self.lists)


if __name__ == '__main__':
    unittest.main(verbosity=2)
