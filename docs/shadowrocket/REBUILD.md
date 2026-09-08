# 花瓣 Rebuild 1.0-beta.2

2026-09-08：用户已确认 beta.1 能连接。beta.2 仅追加微信、抖音、酷狗和酷我的 19 条域名分流，General / Host 与 beta.1 完全一致；新增 App 功能尚待手机验证。

微信 qq.com、weixin.com、wechat.com、qpic.cn、gtimg.com 和抖音主域名原已覆盖，本次补充漏项。酷狗此前缺少明确主域名规则，现补齐。QQ 音乐与网易云仅有核心域名覆盖，不宣称覆盖所有 CDN。新增条目放在用户覆盖、广告和国外保护之后；TikTok 仍走代理，不新增 ASN、User-Agent 或共享 CDN 大范围直连。

域名分类交叉核对（2026-09-08，社区列表，不代表服务商保证）：[WeChat](https://github.com/blackmatrix7/ios_rule_script/blob/master/rule/Shadowrocket/WeChat/WeChat.list)、[DouYin](https://github.com/blackmatrix7/ios_rule_script/blob/master/rule/Shadowrocket/DouYin/DouYin.list)、[酷狗与酷我](https://github.com/LM-Firefly/Rules/blob/master/Domestic-Services/Kugou%26Kuwo.list)。仅选取少量域名事实重新组织，不加载外部列表。

本次是国内直连优化，没有增加 App 去广告规则，也不承诺去除微信朋友圈、抖音信息流或酷狗开屏广告。

## beta.1 设计与限制（保留）

用户反馈 v5.1 rc.1 和 rc.2 均出现测速超时，实际网页也打不开。节点被用户确认可用，但没有客户端错误日志，不能确定具体根因。此版本是重新设计的兼容性基线，不是已确认根因的补丁，也不是稳定发布版。

## 安装

导入 `configs/shadowrocket-rebuild.conf`，确认首行是 `花瓣 Rebuild 1.0-beta.2`；选中该配置，全局路由用“配置”，选择原节点，断开重连。配置没有自动更新 URL，不会自动切换到原 v5。没有更改、添加或删除用户节点。

如之前手动修改过“包括所有网络”等 App 开关，这些不会因换文件自动复原；不要以为导入新文件已重置客户端。若新基线仍失败，需要客户端日志与实际设置截图才能继续，不能承诺靠换配置解决所有情况。

## 重新设计的范围

- 新源文件 `configs/rebuild/base.conf`，不继承 v5 的 General / Host / 路由设置。
- 不强塞半网段默认路由、不指定家中路由器、不使用全端口 DNS 劫持，不强制 DNS-over-PROXY。
- 保留加密 DNS、禁用系统 DNS 回退、禁用直连解析失败改走代理、UDP 不支持时拒绝，以及代理链缺中转时拒绝。
- 不支持的 UDP 拒绝属于隐私保护。如果节点的代理链确实缺失，需要修复本地节点引用，本配置不会通过跳过中转掩盖问题。
- 国内已知域名直连，国外及未知代理；排除国内表中宽泛国家后缀及部分共享云后缀。未知国内服务可能暂时走代理，可精确补充。
- 使用仓库自有域名数据，内嵌输出。复用的只有域名列表与语法校验函数，不读取任何 v5 配置文件。
- 少量广告域名拒绝；无远程规则、自动更新、节点组、测速切换、MITM、证书或脚本。

## DNS 和 IPv6 的真实边界

本地 DNS 与节点引导使用 AliDNS / DNSPod DoH，关闭 HTTP/3 尝试。两者不依赖节点先连通，使用 Host 引导地址且不关闭 TLS 校验。固定地址仍需维护。

默认代理域名尽量保留 hostname，由节点解析；客户端若仍触发本地查询，则使用上述国内 DoH。因此**不能保证所有国外查询只在境外解析，也不能保证系统级零泄漏**。DNS 服务商仍可看见查询。节点端解析器及客户端自身 DoH 不受此文件完全控制。

`ipv6=false` 只关闭此配置中的 IPv6 支持，不等于关闭 iPhone 的 IPv6，也不能据此声称 IPv6 不泄漏。当前优先建立可用基线，严格 DNS 隔离和双栈隐私目标仍待实测，不作为已完成项目卖点。

参数语义参考 [LOWERTOP 社区手册](https://github.com/LOWERTOP/Shadowrocket)，不是客户端内核验证。特别是其 DNS 说明：普通代理类域名由代理侧解析，本地 DNS 覆写用于直连类解析。实际行为仍需客户端日志确认。

## 维护

```sh
python3 scripts/build_shadowrocket_rebuild.py
python3 scripts/build_shadowrocket_rebuild.py --check
python3 -m unittest discover -s tests -p 'shadowrocket*_test.py' -v
```

源模板和三份 `configs/rules/` 本地表是维护入口。脚本展开覆盖与国内核心表，输出配置与 public 镜像。两份必须逐字节一致。CI 验证两套独立构建，分别保留历史候选与新基线，避免旧链接悄然改变。

## 验收状态

静态检查只能验证文件结构和预设规则；不能验证 Shadowrocket 导入、连接、真实 DNS、延迟或吞吐。

| 实机项目 | 当前结果 |
| --- | --- |
| 导入/编译 | 待验证 |
| 同节点下测速与实际国外网页 | 待验证 |
| 国内支付/聊天/视频 | 待验证 |
| Wi-Fi 与移动网络切换 | 待验证 |
| DNS / WebRTC / IPv6 出口 | 待验证 |
| 断线不意外直连 | 待验证 |

请先只确认同一节点下实际网页是否恢复。若失败，保留错误日志，不再盲目叠加功能或把离线测试通过说成网络修复成功。
