# Shadowrocket Pro v5.0 使用与验收

更新时间：2026-09-08。目标：**国内已识别服务直连，国外及未匹配服务使用首页当前节点；DNS 路径加固；失败不擅自改走直连；兼顾移动网络与 Hysteria2。**

这不是“完全匿名”或“绝对零泄漏”保证。保留 v4.1 的手动选节点决定，不增加自动测速、负载均衡或随机回退。节点、订阅、账号和密码均未改动。

## 先让新版生效

主配置地址不变：

```text
https://raw.githubusercontent.com/menghuaban520/cloudflaresub/main/configs/shadowrocket-pro.conf
```

先保留原配置副本。Shadowrocket 中更新此配置，确认文件开头为 `Shadowrocket Pro v5.0`；选择它使其显示勾选，首页“全局路由”选择“配置”。更新/编译规则集后断开重连。下载或编译出错时，先使用原来的可用配置，不能把“没有报错截图”当作已生效。

`public/shadowrocket-pro.conf` 与主配置保持逐字节相同；这只是仓库中的静态镜像文件，**不代表 Cloudflare 站点已经重新部署**。以 GitHub 主配置为准。

## 手机上必须核对的开关

这些是 App / iOS 设置，不能假设下载一个 `.conf` 就全部设置好了。名称以当前版本界面为准。

| 位置 | 本方案要求 / 注意事项 |
| --- | --- |
| 设置 → 隧道 | 开启“包括所有网络”和其中的“包括本地网络”，让路由器 DNS 也进入隧道处理。包括本地网络不等于局域网必须走远端节点：配置内的私网 DIRECT 规则仍保留。 |
| 设置 → UDP | 开启“启用转发”。节点本身也必须支持 UDP；本方案只拒绝无法通过目标代理转发的 UDP。 |
| 设置 → 按需求连接 | 需要持续保护时使用“始终开启”，关闭“睡眠时断开”；它是自动连接措施，不是已经验证的永久断网锁。 |
| 首页 → 全局路由 | 使用“配置”，不要选“直连”；保持“启用回退”关闭，避免意外改变出口。 |
| 节点 TLS 设置 | 不为解决报错而打开“跳过证书验证”。本配置不安装根证书、不启用 MITM。 |

“强制路由”是另一项路由优先级设置，不等价于“包括所有网络”，不能用它替代上面的验收。不要在没有测试时随意叠加所有选项。

追求更严格的浏览器 IP 隐私时，可另开“禁用 STUN”，然后检查网页通话是否正常；它可能破坏 WebRTC 语音、视频及点对点功能。本配置不伪造 STUN 地址或靠修改检测结果“过关”。“包括 APNs”“包括蜂窝服务”涉及通知、电话等兼容性，不作为默认全开项；即便开启，iOS 仍存在必要系统流量例外。

## 节点策略：保留手动与住宅优先习惯

日常手动选住宅 Reality；它不稳定时换住宅 Hysteria2。更重视速度时再选普通 Reality，移动网络不稳时换普通 Hysteria2。配置的 `PROXY` 始终跟随首页选择，不替你决定何时换 IP。

两项失败保护已经写入：

- `udp-policy-not-supported-behaviour = REJECT`：应代理的 UDP 遇到不支持 UDP 的策略时拒绝转发，而非借本地网络直连；不会一刀切禁止正常 HY2 / QUIC。
- `close-if-proxy-chain-missing = true`：代理链的中转条目缺失时拒绝连接，而非跳过中转。这不是对每一种节点宕机、App 崩溃或系统断开情形都有效的总开关。

## DNS：把三种不同用途分开

| 用途 | 配置 | 预期路径 |
| --- | --- | --- |
| 国内已匹配域名解析 | `direct-dns-server` | AliDNS / DNSPod 的 HTTPS DNS，本地直连上游，保留国内 CDN 调度。 |
| 客户端需要解析的其余请求与备用解析 | `dns-server` / `fallback-dns-server` | Cloudflare / Quad9 DoH，使用 `#proxy` 明确经首页当前节点。 |
| 代理服务器自身的域名引导 | `proxy-dns-server` | 国内加密 DNS；必须能在代理尚未建立时工作，不能依赖自身代理。 |

普通代理目标默认仍把 hostname 交给代理服务器解析。**节点端用什么递归 DNS、是否记录查询、住宅代理是否自行转发 DNS，不能由这份客户端配置证明或完全控制。** `proxy-dns-server` 不是“所有国外网站的 DNS”。

已关闭系统 DNS 回退、直连 DNS 使用系统解析以及直连解析失败后改变目标连接策略。国内 DNS 失败时仍可能使用经代理的备用 DoH，目标连接仍按 DIRECT；这是解析上游回退，不是把国内网站全部改走国外。

`[Host]` 为 DNS 服务域名提供固定引导 IP，但 DoH URL 保留域名和 TLS 证书校验。DNSPod 使用 `https://doh.pub/dns-query`，不是已不再推荐的字面 IP URL。固定地址未来可能变动，需要维护；两家国内上游用于互备。不要为绕过地址失效而关闭 TLS 校验。

### Wi-Fi、移动网络与 IPv6

旧版只补 `192.168.1.1:53`，没有解决所有网络中的 DNS 路径。新版不再把整片私网从 TUN 排除；使用 `hijack-dns = :53` 接管进入隧道的标准 DNS，补入双栈路由以及已知路由器的 `192.168.1.1/32`、`fe80::1/128`。

开启 IPv6 并优先 IPv4，是让双栈进入规则体系；`ipv6=false` 不等于关闭 iOS 的所有 IPv6 通信。更具体的本地路由仍可能影响实际接管，因此手机侧开关和实测不能省略。节点不支持某种转发时，应失败，而不是暴露本地出口来“保连通”。

标准 853 端口的非指定 DNS 连接优先使用 PROXY。任意 App 的内置 DoH、DoQ、自建端口，以及 iOS 例外流量不可能靠一条 53 端口规则全部识别。这里不宣称覆盖了它们。

## 分流与广告改进

内嵌常用国内、国外域名作为远程列表不可用时的基础规则；增加 Google 中国域名、Grok/X、Twitter 图片、TikTok 国际域名等保护，避免它们先落入国内大表。用户覆盖表优先于普通广告拦截，DNS 安全路由与局域网规则在其前面。

国内使用内嵌规则、自有 `china-core.list` 与 ChinaMax 域名集；IP 流量由 `GEOIP,CN,DIRECT,no-resolve` 补充。移除整个 ChinaMax 规则表，减少重复和 USER-AGENT 类广泛直连。未知域名不会为了匹配 GEOIP 额外触发本地解析，最终策略仍是 PROXY。

域名分类不等同于每个实际服务器的物理国家；跨国服务、共享云域名、CDN 和 GEOIP 数据都可能有误差。国内服务故意直连时显示本地公网 IP 是预期行为，不叫“代理泄漏”。

保留明确广告域名和 AdvertisingLite 域名集/补充规则；去掉 `pre-matching`，允许用户覆盖纠正误拦；去掉额外重叠的 BanProgramAD。没有证书、脚本或 HTTPS 解密，因此不承诺去掉所有开屏或共域名广告。上游列表仍可能误拦，且内容随上游更新。

规则源统一使用 GitHub Raw，减少第三方分发依赖。这不是所有网络下的速度保证；大规则集首次下载可能较慢，主配置更新与规则集更新都需检查。不要用“更新间隔越短”换取频繁唤醒与重复下载。

纠错文件保持原位置：

```text
configs/rules/user-proxy.list   # 国外服务误直连时加入
configs/rules/user-direct.list  # 国内服务误代理或明确正常域名被拦时加入
```

每行使用 `DOMAIN,完整域名` 或 `DOMAIN-SUFFIX,域名后缀`，不带策略。不要为修一个广告误拦就把整家 CDN 或所有域名放行。修改后更新对应规则集。

## 高标准验收：目标与已经做过的检查分开

**已做：** 18 项离线结构/策略回归测试，覆盖 DNS 路径设置、禁止危险回退、双栈路由字段、规则顺序、域名边界、核心域名缺少远程列表时的匹配，以及两份配置一致性。测试不调用 Shadowrocket 内核，不模拟远程列表、GEOIP 或真实 DNS。运行命令：

```sh
python3 tests/shadowrocket_config_test.py
```

**未做：** 你的 iPhone 导入/编译、节点连通性、真实出口抓包、吞吐量、延迟、耗电及断线泄漏测试。以下是上线验收要求，不是已取得的成绩：

| 项目 | 验收要求 |
| --- | --- |
| 分流 | 国内常用 App 日志应为 DIRECT；ChatGPT、Google、GitHub、X、TikTok 为 PROXY。广告专用请求为 REJECT。抽查 IPv4、IPv6、域名与直接 IP 请求。 |
| DNS | Wi-Fi DNS 恢复“自动”，在 `dnsleaktest.com` 做 Extended test，并在 `browserleaks.com/dns` 交叉检查；切换蜂窝网络后重复。国外测试不应出现本地运营商路径；出现时必须按日志/抓包定位，不能仅凭解析器国旗判断。 |
| WebRTC | 使用 `browserleaks.com/webrtc` 检查公开地址，不应暴露本地真实公网 IPv4/IPv6。局域网地址、mDNS 名称与公网泄漏不是同一概念。 |
| 失败行为 | 保持 VPN 隧道开启，测试一个不可用的代理：国外请求应失败，而非改用本地公网出口。代理链丢失、UDP 不支持也分别测试。手动关掉 VPN 是不同场景。 |
| 网络切换 | 在两种网络间切换、锁屏唤醒、App 重启及设备重启后重复 DNS/IP 检查。建议至少完成 10 次切换；每次均不得把国外连接变成本地直连。 |
| 速度与稳定 | 同一节点、同一网络与旧版对照，记录真实 HTTPS 首包、成功率和下载；建议抽测 100 次连接并连续使用 30 分钟，连接成功率目标不低于 99%，持续流量无异常断流。延迟/吞吐不能由配置文件凭空保证。 |
| 日常兼容 | 检查支付、验证码、视频通话、推送、AirPlay/CarPlay 和热点认证。失败时记录对应规则与设置，逐项调整，不用全局直连掩盖问题。 |

检测网页只能覆盖网页触发的流量。更严格的结论还需要在可信 Wi-Fi 路由器/网关抓包检查 DNS 出站，并结合代理服务器日志核对；没有这一层证据，不宣称整台设备已“零泄漏”。诊断日志可能含访问域名和节点信息，分享前先打码，不把完整原始日志提交到公开仓库。

## 能力边界与回退

Apple 明确说明，包括所有网络仍保留 DHCP、热点认证、部分蜂窝服务、配对设备等例外。VPN 停止或系统重启的空窗不能靠本文件作绝对保证。账号、Cookie、定位权限、浏览器指纹与代理服务商日志也不受这份配置消除。

v4.1 历史版本可在下面的固定提交读取，**仅供兼容性回退，不具备 v5.0 的完整加固**：

```text
https://raw.githubusercontent.com/menghuaban520/cloudflaresub/b07a04f674f09660ba1e7351b342ea7a82360582/configs/shadowrocket-pro.conf
```

下载为独立配置后，删除或注释其中的 `update-url`，避免更新时又切回 main 新版。不要为了回退去重写整个仓库历史。

## 核对依据

- LOWERTOP 的 Shadowrocket 使用手册与实际示例配置（社区维护、非官方说明）：https://github.com/LOWERTOP/Shadowrocket
- `hijack-dns = :53` 配置实例：https://github.com/haritos90/shadowrocket-config-files
- Apple 对 includeAllNetworks 与例外流量的定义：https://developer.apple.com/documentation/networkextension/nevpnprotocol/includeallnetworks
- Cloudflare DoH 端点说明：https://developers.cloudflare.com/1.1.1.1/encryption/dns-over-https/make-api-requests/
- Quad9 DoH 服务说明：https://quad9.net/support/faq/
- DNSPod 的域名接入调整公告：https://docs.dnspod.cn/notices/mian-fei-ban-dot-dohbu-zai-gong-kai-ipjie-ru-de-gong-gao/
- ChinaMax / AdvertisingLite 作者规则：https://github.com/blackmatrix7/ios_rule_script/tree/master/rule/Shadowrocket

参数说明和在线规则是可变化的依赖。后续升级客户端或更换节点后，应重新执行手机侧验收，而不是沿用本次离线检查的结论。
