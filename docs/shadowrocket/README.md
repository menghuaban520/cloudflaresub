# 花瓣 · Shadowrocket Standalone

**5.1.0-rc.2 · 国内已识别服务直连，国外及未知服务代理。**

面向希望保持手动选节点、减少远程规则依赖的用户。规则随配置一起交付，构建只读仓库内文件，无需下载第三方规则。它是 CloudflareSub 仓库中的独立配置子项目，使用配置不需要部署 Worker。

当前是候选版，自动检查通过不代表已在 Shadowrocket 内核或 iPhone 上验证。尚无可宣称兼容的实测 iOS / Shadowrocket 版本范围。正式标记稳定版前，必须完成 [验收记录](VALIDATION.md)。

## 选择文件

| 文件 | 用途 |
| --- | --- |
| [shadowrocket-standalone.conf](../../configs/shadowrocket-standalone.conf) | 默认：内嵌自有分流与少量明确广告域名拦截 |
| [shadowrocket-standalone-noads.conf](../../configs/shadowrocket-standalone-noads.conf) | 广告拦截关闭：用于排查广告误拦，保留同样 DNS 与代理失败策略 |
| [原 v5 配置](../../configs/shadowrocket-pro.conf) | 历史远程规则方案，仍需下载外部列表 |

独立版没有远程 RULE-SET / DOMAIN-SET，也没有 update-url。这里的“独立”指规则文件自足，DNS、节点连接和首次获取配置仍需要网络，GEOIP 仍依赖客户端数据库。

未打包 ChinaMax / AdvertisingLite 外部规则，因此长尾国内域名覆盖和广告拦截范围小于原在线方案。未知域名走代理，不自动猜测它属于国内。保留原有 `.cn` 分类及共享云域名分类，海外运营的 `.cn` 网站和共享 CDN 可能需要精确覆盖；这不是服务器地理位置保证。

## iPhone 安装

1. 保留当前可用配置副本。下载上表中的 `.conf` 文件，使用 iOS 分享或 Shadowrocket 的本地导入功能导入；菜单名称依安装版本而定。GitHub 下载失败时，可从电脑传送文件到手机。
2. 在配置页选中新导入的独立版，首页全局路由选“配置”。保留自己的节点与订阅，先选一个已知能正常打开国外网页的节点，然后断开重连。
3. 按 [原 DNS 与隧道说明](../../configs/shadowrocket-pro-guide.md) 核对客户端开关，并执行 [验收记录](VALIDATION.md)。这份文件不会自动改变所有 App 设置。
4. 如果仍超时，按 [排障步骤](TROUBLESHOOTING.md) 定位。不要连续覆盖唯一可用副本。

日常可手动选择住宅节点；失效时手动切换自己已配置好的住宅 HY2 / 其他备用节点。没有自动换 IP、负载均衡或不可用时 DIRECT 兜底。实际节点名称与协议由用户本地配置决定。

## 分流顺序

DNS 出站规则 → 局域网 → 用户代理覆盖 → 用户直连覆盖 → 可选广告拒绝 → 国外核心域名 → 国内核心域名 → 已知中国 IP → 未知代理。

DNS / 局域网保护规则优先于用户覆盖。若同一域名同时被两份用户覆盖匹配，代理覆盖优先。只去除完全重复的规则，不重排，避免改变优先级。

## DNS 与隐私边界

沿用 v5 的加密 DNS、节点域名独立引导、关闭系统解析回退和双栈规则参数。rc.2 为经代理的两条 DoH 增加 `no-h3`，隔离 HTTP/3 / UDP 兼容性假设；其他 DNS 与路由参数不变。此假设尚待手机验证，没有声称已修复节点超时。

国内已匹配请求使用国内 DoH；客户端需要解析的其他请求和备用 DNS 使用经代理的 DoH。普通代理请求可能交由节点解析，节点端 DNS 不由本项目控制。DoH 上游能看到其处理的查询；加密不等于没有日志或匿名。

[Cloudflare 官方文档](https://developers.cloudflare.com/1.1.1.1/encryption/dns-over-https/make-api-requests/) 确认了当前使用的 Cloudflare DoH 端点。Shadowrocket 参数含义参考仓库原有配置与 [社区手册](https://github.com/LOWERTOP/Shadowrocket)，社区说明不能代替实际客户端验收。

不提供 MITM、证书安装、TLS 校验绕过或检测结果伪装。不承诺系统级零泄漏、所有广告去除或稳定提速。真实出口、WebRTC、网络切换和断线行为必须实机验证。

## 维护和构建

Python 3.9+，仅标准库。在仓库根目录执行：

```sh
python3 scripts/build_shadowrocket.py
python3 scripts/build_shadowrocket.py --check
python3 -m unittest discover -s tests -p 'shadowrocket*_test.py' -v
```

源文件：`configs/shadowrocket-pro.conf` 提供 DNS / 路由与基础规则；`configs/rules/user-proxy.list`、`user-direct.list`、`china-core.list` 提供本地域名表。不要手改生成的 standalone 文件。

覆盖表每行只接受 `DOMAIN,api.example.com` 或 `DOMAIN-SUFFIX,example.com`，域名用小写 ASCII / Punycode，不写策略。修改源文件、重建并通过测试后，重新导入整个独立配置；它不会自动更新覆盖表。

构建器只展开审核过的三份本地列表，明确排除原配置中的三项外部规则依赖；新增未知远程引用、节点内容或不支持的覆盖语法将导致构建失败。SHA-256 清单记录输入和输出，支持重复构建核对；清单不是数字签名。

## 发布与回退

GitHub Actions 在推送、PR 和手动触发时检查构建一致性与离线回归，上传候选文件供下载，不自动部署或创建正式 Release。正式发布时先完成验收记录，再建立不可变版本 tag，附上两份配置、构建清单、文档及 LICENSE。

旧的主配置 URL 不指向候选版，已有用户不会因本次候选文件而自动升级。回退时重新选中手机里保存的已知可用配置；候选版不含自动更新 URL，不会自行跳回 main。不要把“历史版本存在”写成“历史版本在所有网络可用”。

公开提交只放配置模板和规则，节点凭证留在客户端。报告问题只附已打码片段，不提交订阅地址、口令或完整访问日志。

项目沿用根目录 [MIT License](../../LICENSE)。没有重新分发外部大规则表；未来若引入第三方快照，须保留来源、版本和适用许可。
