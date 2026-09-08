import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {defaults,generate,normalize} from '../public/customize/model.js';
const base=readFileSync(new URL('../public/shadowrocket-rebuild.conf',import.meta.url),'utf8');
const build=patch=>generate(base,{...defaults(),...patch});
test('defaults preserve the known working configuration byte for byte',()=>assert.equal(build({}).config,base));
test('privacy DNS changes do not replace node bootstrap DNS or hosts',()=>{
 const c=build({dns:'privacy'}).config;
 assert.match(c,/^dns-server = https:\/\/1\.1\.1\.1\/dns-query#proxy&no-h3/m);
 assert.equal(c.match(/^proxy-dns-server = .*$/m)[0],base.match(/^proxy-dns-server = .*$/m)[0]);
 assert.equal(c.split('[Host]')[1],base.split('[Host]')[1]);
});
test('custom DNS accepts HTTPS only and blocks config injection',()=>{
 for(const customDns of ['http://dns.example.com/query','https://a.test/query#proxy','https://u:p@a.test/query','https://a.test/query,https://b.test/query','https://a.test/query\n[Rule]'])assert.throws(()=>build({dns:'custom',customDns}));
 assert.match(build({dns:'custom',customDns:'https://dns.example.com/dns-query',dnsViaProxy:true}).config,/dns-server = https:\/\/dns.example.com\/dns-query#proxy&no-h3/);
});
test('precise user overrides precede app routing and baseline, after bootstrap',()=>{
 const c=build({wechat:'PROXY',direct:'wx.qq.com',proxy:'api.example.com'}).config;
 assert.ok(c.indexOf('DOMAIN,wx.qq.com,DIRECT')<c.indexOf('DOMAIN-SUFFIX,wx.qq.com,PROXY'));
 assert.ok(c.indexOf('DOMAIN,doh.pub,DIRECT')<c.indexOf('DOMAIN,api.example.com,PROXY'));
 assert.ok(!c.includes('DOMAIN-SUFFIX,qq.com,PROXY'));
});
test('ads switch removes only explicit ad rules',()=>{
 const c=build({ads:false}).config;
 assert.equal(c.match(/^DOMAIN,.*REJECT$/gm),null);
 assert.match(c,/udp-policy-not-supported-behaviour = REJECT/);
 assert.match(c,/FINAL,PROXY/);
});
test('bad domains, reserved domains, conflicting routes cannot export',()=>{
 for(const direct of ['https://example.com','example.com,PROXY','dns.alidns.com','a.lan','example.com\n[General]'])assert.throws(()=>build({direct}));
 assert.throws(()=>build({direct:'Example.com',proxy:'example.com'}));
 assert.equal((build({direct:'example.com\nEXAMPLE.COM'}).config.match(/DOMAIN,example.com,DIRECT/g)||[]).length,1);
});
test('chain guide uses exit node proxy-through entry and never invents chain keys',()=>{
 const r=build({chain:true,entry:'香港入口',exit:'住宅出口',stun:true});
 assert.equal(r.config,base);
 assert.ok(r.steps.some(s=>s.includes('出口“住宅出口”右侧 ⓘ → 代理通过 → 选择入口“香港入口”')));
 assert.ok(r.steps.some(s=>s.includes('设置 → UDP → 禁用 STUN')));
 assert.throws(()=>build({chain:true,entry:'同一个',exit:'同一个'}));
 assert.throws(()=>build({chain:true,entry:'入口'}));
 assert.throws(()=>build({chain:true,entry:'入口\n[Rule]',exit:'出口'}));
});
test('settings round-trip and reject malformed versions/types',()=>{
 const s={...defaults(),chain:true,entry:'入口',exit:'出口',kugou:'PROXY',direct:'api.example.com'};
 assert.deepEqual(normalize(JSON.parse(JSON.stringify(s))),s);
 for(const v of [null,[],{version:2},{version:1,ads:'false'},{version:1,wechat:'REJECT'}])assert.throws(()=>normalize(v));
});
test('all offered app and DNS combinations generate with one General, Rule, Host and final rule',()=>{
 for(const dns of ['compatible','privacy','custom'])for(const wechat of ['default','DIRECT','PROXY'])for(const douyin of ['default','DIRECT','PROXY'])for(const kugou of ['default','DIRECT','PROXY'])for(const ads of [true,false]){
  const c=build({dns,wechat,douyin,kugou,ads,customDns:'https://dns.example.com/query'}).config;
  for(const section of ['General','Rule','Host'])assert.equal(c.split(`[${section}]`).length,2);
  assert.equal(c.split('FINAL,PROXY').length,2);
 }
});
