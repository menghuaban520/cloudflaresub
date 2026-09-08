# Shadowrocket Pro v3 使用说明

目标：**国内尽量 DIRECT，国外统一走 Shadowrocket 首页当前节点；住宅/普通 Reality 与 Hysteria2 全部手动切换；不自动换 IP；避免中国移动系统 DNS 出现在外国流量的 DNS 路径里。**

## 主配置

推荐使用 GitHub Raw：

`https://raw.githubusercontent.com/menghuaban520/cloudflaresub/main/configs/shadowrocket-pro.conf`

Cloudflare 只保留为可选静态镜像：

`https://091329.xyz/shadowrocket-pro.conf`

主逻辑不依赖 Cloudflare Worker 动态代理规则。

Shadowrocket：`配置 -> 右上角 + -> 粘贴 URL -> 下载 -> 点配置使其出现 ✓`

首页 **全局路由** 选择 **配置**。

## 节点

`FINAL,PROXY` 永远跟随首页当前选中的节点，没有 url-test / fallback / load-balance。

推荐手动顺序：

1. 日常住宅：`住宅IP | 搬瓦工 | 主节点 (Reality)`
2. 住宅主节点不稳：`住宅IP | 搬瓦工 | 移动网络备用 (Hysteria2)`
3. 要最高速度：`搬瓦工 | 主节点 (Reality)`
4. 普通主节点不稳：`搬瓦工 | 移动网络备用 (Hysteria2)`

不要打开 **全局路由 -> 启用回退**，否则节点失败后 Shadowrocket 可能自行换出口。

## 为什么 v3 国内会更快

旧版为了 DNS 隐私，把默认 DNS 也经代理发到 Google / Cloudflare；同时只使用 ChinaMax 的 Domain 版本。这样一旦国内长尾域名没有及时命中，体验容易出现“国内 App 好像绕住宅出口”的感觉。

v3 改成：

1. 高频国内服务先命中 `china-core.list` -> `DIRECT`
2. 再按 ChinaMax 维护者建议同时加载 `ChinaMax.list` + `ChinaMax_Domain.list` -> `DIRECT`
3. 中国 IP -> `GEOIP,CN,DIRECT,no-resolve`
4. 剩余 -> `FINAL,PROXY`

`ChinaMax.list` 还能补 USER-AGENT / IP 等规则；其 IP 类规则带 `no-resolve`，减少为了规则判断额外触发 DNS。

## DNS 设计

Shadowrocket 对已经判定为代理的域名，正常情况下会让代理端处理域名解析。因此 v3 不再让“默认本地 DNS”绕到美国代理出口。

本地需要解析的 DIRECT 流量统一使用：

- AliDNS DoH
- DNSPod / doh.pub DoH

并设置：

- `dns-direct-system = false`
- `dns-fallback-system = false`
- `dns-direct-fallback-proxy = false`

也就是说国内域名解析失败时，不会突然改走住宅代理；同时也不会回退到 iOS / 中国移动系统 DNS。

节点服务器自己的域名也使用国内加密 DNS 做 bootstrap。

常见 `8.8.8.8 / 1.1.1.1 / 9.9.9.9` 的 53 端口请求仍会被接管，但没有使用暴力 `*:53`。

## 广告

v3 为了减少规则重复和分流副作用，去掉了“OFF= DIRECT”的广告/隐私代理组。

原因：一个外国 tracker 如果匹配广告/隐私组，而该组被切成 `DIRECT`，它就会绕过 `FINAL,PROXY`，反而破坏“国外统一代理”。

现在使用较轻的固定 `REJECT`：

- AdvertisingLite 的 Domain 规则
- ACL4SSR BanProgramAD

不加载重复的完整 AdvertisingLite + Privacy 大表，也不默认 MITM。

## 国外服务防误判

`configs/rules/user-proxy.list` 位于 ChinaMax 之前，里面明确包含 OpenAI、Google、YouTube、GitHub、X、Instagram、Reddit、Discord、Telegram、PayPal、Steam 等常见国外服务。

如果以后发现某个国外站被误直连，把它加到 `user-proxy.list`。

如果某个国内域名误走代理，把它加到：

`configs/rules/user-direct.list`

## UDP / Hysteria2

建议：`设置 -> UDP -> 启用转发 -> 开启`

主配置不设置 `block-quic`，也不设置 `udp-policy-not-supported-behaviour = REJECT`，避免移动网络下出现 App 半连接、视频/游戏卡顿。

## WebRTC / STUN

如果做严格隐私测试，可临时：

`设置 -> UDP -> 禁用 STUN -> 开启`

但可能影响网页语音/视频，所以日常不建议一直开。

## 验收

更新配置后，断开再连接。

1. 首页选住宅 Reality。
2. 打开淘宝、B站、抖音、微信等国内 App。
3. `数据 -> 代理日志`：应大量看到 `DIRECT`。
4. 打开 ChatGPT / Google / GitHub：应看到 `PROXY`。
5. 打开 `dnsleaktest.com` 或 `ipleak.net`：测试站本身应命中 `PROXY`；外国流量不应出现本地 China Mobile / China Unicom / China Telecom 系统递归 DNS。

注意：AliDNS / DNSPod 出现在 **国内 DIRECT 的 DNS 日志** 是设计如此，不等于国外代理流量 DNS 泄漏。

如果国内 App 仍慢，最有价值的是截一张 **数据 -> 代理日志**，看具体哪个域名落到了 `PROXY`；把那个域名补进 `user-direct.list` 会比盲目继续加大规则更准确。
