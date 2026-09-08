# Shadowrocket Pro 使用说明

这份配置针对当前需求设计：**国内常用服务直连、其他流量统一走首页当前节点、住宅节点日常默认使用、Reality/Hysteria2 全部手动切换、广告可开关、尽量减少 DNS / WebRTC 身份泄漏。**

## 导入

配置直链：

`https://raw.githubusercontent.com/menghuaban520/cloudflaresub/main/configs/shadowrocket-pro.conf`

Shadowrocket：`配置 -> 右上角 + -> 粘贴 URL -> 下载 -> 点配置使其出现 ✓`

首页把 **全局路由** 设为 **配置**。

## 节点怎么选

这版故意不再创建自动测速/国家分组，`FINAL,PROXY` 永远使用 **Shadowrocket 首页当前选中的节点**。

推荐顺序：

1. 日常：`住宅IP | 搬瓦工 | 主节点 (Reality)`
2. 住宅 Reality 抽风：切 `住宅IP | 搬瓦工 | 移动网络备用 (Hysteria2)`
3. 想要最高速度、不需要住宅属性：切 `搬瓦工 | 主节点 (Reality)`
4. 普通 Reality 抽风：切 `搬瓦工 | 移动网络备用 (Hysteria2)`

Shadowrocket 通常会记住首页最后选择的节点，因此只要第一次选住宅主节点，日常就会继续用它。

**不要打开“全局路由 -> 启用回退”**，否则节点失败后 Shadowrocket 可能自行换到其他节点，出口 IP 会改变。

## DNS 设计

配置使用 Split DNS：

- 已经明确匹配 `DIRECT` 的国内域名：AliDNS + DNSPod 的 DoH，用来保持国内 CDN 调度和速度。
- 其他需要本地 DNS 的请求：Google DNS + Cloudflare DNS 的 DoH，并用 `#proxy` 通过首页当前节点发送。
- 正常的代理域名：不强制在本地解析，交给代理端远程解析。
- `GEOIP,CN` 使用 `no-resolve`，不会为了判断一个未知外国域名是不是中国 IP 而先调用本地 DNS。
- fallback 不允许回到 iOS/System DNS。
- 节点服务器自己的域名通过国内加密 DNS 解析，避免“代理还没连上，却为了连接代理先用运营商系统 DNS”的启动问题。
- 仅劫持常见的境外硬编码 53 端口 DNS，不使用暴力 `*:53`，避免之前那种卡顿/部分 App 无法连接。

**DNS 泄漏检测里，DNS 服务器 IP 不需要和代理出口 IP 完全相同。** Google/Cloudflare/代理机房附近递归 DNS 都可能是正常结果。真正需要警惕的是：测试外国站点时仍出现本地运营商的 China Mobile / China Unicom / China Telecom DNS。

## UDP / Hysteria2

建议：

`设置 -> UDP -> 启用转发 -> 开启`

如果订阅或单个节点有独立的 UDP 转发开关，也保持开启。Hysteria2 本身依赖 UDP；Reality 节点的 UDP 转发也能避免部分 DNS、游戏、QUIC 流量在节点策略不完整时出现异常。

主配置**没有**设置 `udp-policy-not-supported-behaviour = REJECT`，也没有屏蔽 QUIC，因为这两个严格选项在移动网络上更容易造成“能打开但卡卡的”或 App 部分连接失败。

## WebRTC / STUN（可选严格隐私）

如果你非常在意浏览器/WebRTC 暴露真实公网 IP：

`设置 -> UDP -> 禁用 STUN -> 开启`

代价是某些语音、视频、WebRTC 通话可能失效。所以日常需要语音/视频时建议保持关闭，只在做严格隐私测试时打开。

配置没有写死 `stun-response-ip`，原因也是为了不默认破坏语音/视频功能。

## 广告开关

进入当前配置的 **代理分组**：

- `🛑 广告拦截`：`REJECT` = 开；`DIRECT` = 关
- `🍃 应用净化`：`REJECT` = 开；`DIRECT` = 关
- `🛡️ 隐私跟踪`：默认 `DIRECT`（关）；需要更严格时切 `REJECT`

隐私跟踪表比较激进，如果某个 App 登录、验证码、埋点相关功能突然异常，先把它切回 `DIRECT`。

不建议开启 HTTPS 解密/MITM 来追求多拦那一点广告；它会增加证书、兼容性和隐私复杂度。

## 为什么没有直接用 China / ChinaMax 巨型规则

研究后发现这些“国内直连”规则并不等于“地理上属于中国”。例如部分列表会把 AMD、Sony、TeamViewer、BrowserLeaks 等境外服务也归入直连候选，和本需求的 **“国外统一代理”** 冲突。

因此 Pro 版使用：

- `.cn` / 中国 IDN TLD
- 常见国内 App / 厂商的精简 `china-core.list`
- `GEOIP,CN,DIRECT,no-resolve`
- 其余统一 `FINAL,PROXY`

这样比“大而全的直连表”更符合当前需求。

## 自定义例外

强制某域名直连：编辑

`configs/rules/user-direct.list`

例如：

`DOMAIN-SUFFIX,example.cn`

强制某域名代理：编辑

`configs/rules/user-proxy.list`

例如：

`DOMAIN-SUFFIX,example.com`

规则每小时自动重新拉取一次；需要立刻生效时，在 Shadowrocket 更新当前配置/规则并重新连接。

## 怎么验收

1. 首页选住宅主节点。
2. 访问 `ipinfo.io`：应该看到住宅出口 IP。
3. 打开国内 App/网站：在 Shadowrocket 代理日志里应该显示 `DIRECT`。
4. 打开 `dnsleaktest.com` Extended Test 或 `ipleak.net`：测试流量应为 `PROXY`，DNS 列表不应出现你当前本地运营商的递归 DNS。
5. 切换到普通 Reality，再重复 2/4：出口应跟着普通节点变化；外国 DNS 路径也会使用当前默认节点。

如果 DNS 测试仍出现 China Mobile / China Unicom / China Telecom：

- 先确认测试站日志命中 `PROXY`；
- 确认没有叠加其他 DNS 模块；
- 确认全局路由是“配置”；
- 确认系统没有同时运行另一个 VPN/DNS Profile；
- 把 DNS 日志与代理日志截图出来再定位。

## 回退

如果 Pro 版在某个网络环境出现异常，旧的实验版仍保留在：

`https://raw.githubusercontent.com/menghuaban520/cloudflaresub/main/configs/shadowrocket-cn-direct.conf`
