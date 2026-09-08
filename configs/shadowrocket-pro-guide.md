# Shadowrocket Pro v4 使用说明

目标：**国内尽量 DIRECT，国外统一走 Shadowrocket 首页当前节点；住宅/普通 Reality 与 Hysteria2 全部手动切换；不自动换 IP；加强开屏广告拦截，但不启用 MITM。**

## 主配置

推荐使用 GitHub Raw：

`https://raw.githubusercontent.com/menghuaban520/cloudflaresub/main/configs/shadowrocket-pro.conf`

Cloudflare 只保留为可选静态镜像：

`https://091329.xyz/shadowrocket-pro.conf`

Shadowrocket：`配置 -> 右上角 + -> 粘贴 URL -> 下载 -> 点配置使其出现 ✓`，首页 **全局路由** 选择 **配置**。

## 节点

`FINAL,PROXY` 永远跟随首页当前选中的节点，没有 url-test / fallback / load-balance。

推荐手动顺序：

1. 日常住宅：`住宅IP | 搬瓦工 | 主节点 (Reality)`
2. 住宅主节点不稳：`住宅IP | 搬瓦工 | 移动网络备用 (Hysteria2)`
3. 要最高速度：`搬瓦工 | 主节点 (Reality)`
4. 普通主节点不稳：`搬瓦工 | 移动网络备用 (Hysteria2)`

不要打开 **全局路由 -> 启用回退**，否则节点失败后 Shadowrocket 可能自行换出口。

## v4 的开屏广告策略

v4 选择的是“稳妥加强”，不是 MITM 暴力模式。

第一层是少量高置信度的开屏/广告专用域名，例如头条、快手、微博、喜马拉雅、腾讯音乐、小红书、小米、Vivo、HeyTap 等广告接口。它们使用：

`REJECT,pre-matching`

`pre-matching` 会在普通规则匹配之前快速拒绝请求，适合这种用途明确的广告域名，能减少开屏广告请求傻等超时的时间。因为预匹配优先级很高，所以这里只放非常明确的广告端点，不拿模糊关键词乱杀。

第二层按 Blackmatrix7 对 Shadowrocket 的建议，同时使用：

- `AdvertisingLite_Domain.list`（DOMAIN-SET）
- `AdvertisingLite.list`（RULE-SET）

Domain Set 先处理大量域名规则，完整 Rule Set 再补关键词/IP等条目。最后再用 ACL4SSR `BanProgramAD` 补一层 App 内广告。

**没有 `[MITM]`、没有证书、没有 HTTPS 解密。** 所以如果某个 App 把广告内容和正常接口放在同一个第一方域名、只靠 URL 路径区分，v4 不会冒险去拆 HTTPS；这类广告可能仍然存在。这是 A 方案为了稳定性刻意留下的边界。

也没有使用 `REJECT-DROP`：静默丢包容易让 App 等超时，开屏场景反而可能更慢；这里继续使用能快速失败的普通 `REJECT`。

## 国内分流优化

顺序现在是：

1. `china-core.list` 高频国内服务 -> `DIRECT`
2. `ChinaMax_Domain.list` -> `DIRECT`
3. `ChinaMax.list` 补 USER-AGENT / IP 等 -> `DIRECT`
4. `GEOIP,CN,DIRECT,no-resolve`
5. 其余 -> `FINAL,PROXY`

v4 把专用的 ChinaMax Domain Set 放在完整 Rule Set 前面，让普通域名请求优先走更直接的域名匹配；完整列表只负责补长尾类型。

## DNS

本地需要解析的 DIRECT 流量统一使用：

- AliDNS DoH
- DNSPod / doh.pub DoH

并保持：

- `dns-direct-system = false`
- `dns-fallback-system = false`
- `dns-direct-fallback-proxy = false`

国内解析失败不会突然绕住宅代理，也不会主动回退到 iOS / 中国移动系统 DNS。代理类域名保留 hostname，正常交给代理端处理。

只接管常见境外公共 DNS 的 53 端口，不使用暴力 `*:53`。IPv6 暂时关闭，减少双栈出口变量。

## 自定义纠错

国外服务被 ChinaMax 误判直连：加到

`configs/rules/user-proxy.list`

国内正常服务误走代理：加到

`configs/rules/user-direct.list`

如果某个 App 因普通 AdvertisingLite 规则误拦，可以把需要放行的正常域名加进 `user-direct.list`；但那 15 条 `pre-matching` 高置信广告规则优先级更高，需要直接修改主配置才能放行。

## UDP / Hysteria2

建议：`设置 -> UDP -> 启用转发 -> 开启`。

主配置不设置 `block-quic`，也不设置 `udp-policy-not-supported-behaviour = REJECT`，优先保证移动网络、Hysteria2、视频和游戏兼容性。

## WebRTC / STUN

做严格隐私测试时，可以临时：`设置 -> UDP -> 禁用 STUN -> 开启`。

它可能影响网页语音/视频，所以日常不建议一直开。

## 验收

更新配置后断开再连接：

1. 首页选择住宅 Reality。
2. 打开淘宝/B站/抖音/微信，代理日志应大量是 `DIRECT`。
3. 冷启动几个以前有开屏广告的 App，广告请求应出现 `REJECT`，部分 App 会直接跳过开屏。
4. 打开 ChatGPT/Google/GitHub，应走 `PROXY`。
5. 用 `dnsleaktest.com` 或 `ipleak.net` 检查外国流量，不应出现本地 China Mobile / China Unicom / China Telecom 系统递归 DNS。

如果某个 App 依然有开屏广告，截 **开 App 那几秒的代理日志** 最有用：能看到它究竟是独立广告域名（可以继续稳妥补规则），还是和正常 API 共域名（A 方案就不建议硬拦）。
