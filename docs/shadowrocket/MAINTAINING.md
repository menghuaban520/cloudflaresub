# 维护 Rebuild

Python 3.9+，仅标准库，不需要部署订阅器或安装 Node 依赖。

| 文件 | 用途 |
| --- | --- |
| `configs/rebuild/base.conf` | Rebuild 源模板：参数、规则顺序、App 补充和注释 |
| `configs/rules/user-proxy.list` | 用户代理覆盖，优先于普通分类 |
| `configs/rules/user-direct.list` | 用户直连覆盖，优先于广告 |
| `configs/rules/china-core.list` | 国内核心域名数据；构建时过滤宽泛后缀 |
| `scripts/build_shadowrocket_rebuild.py` | 生成配置与静态镜像 |
| `configs/shadowrocket-rebuild.conf` | 给用户导入的生成文件，不直接维护 |
| `public/shadowrocket-rebuild.conf` | 相同内容的静态镜像，不代表站点已部署 |

```sh
python3 scripts/build_shadowrocket_rebuild.py
python3 scripts/build_shadowrocket_rebuild.py --check
python3 scripts/build_shadowrocket.py --check
python3 -m unittest discover -s tests -p 'shadowrocket*_test.py' -v
```

Rebuild 不读取 v5 配置，只复用本地域名列表与规则校验函数。共享规则表也会影响历史生成器，改共享表后须运行两个构建器并检查差异。

发布前：重建、核对差异、运行检查、更新版本记录与入门页固定 URL。公开试用版保留 beta 标记；没有实测的项目继续写“未验证”。CI 的 Rebuild artifact 只包含当前配置和新手文档，不把历史 v5 配置装进新手下载包。

当前固定下载 URL 指向含用户覆盖区域注释的新手说明版，与自定义指南对应。其运行参数和规则仍与 beta.2 相同。后续修改任何生效规则都应更新版本与固定链接。

试用链接可公开分享，正式稳定版仍需补充设备版本、网络切换、DNS/IPv6 和失败行为证据。旧 v5 URL 保留历史兼容，不自动重定向到新版本。

## 下载包

提交改动后运行 `python3 scripts/package_shadowrocket.py`，生成 `dist/huaban-rebuild-beta.zip`。CI 上传相同 ZIP。包内只有一份可导入的 Rebuild 配置，附入门、编辑、排障文档和 `SHA256SUMS`；不包含历史失败配置。

打包时校验文档引用，未包含的历史或维护资料链接改为指向对应提交的 GitHub 地址。包内文档可以本地阅读，GitHub 外链仍需要网络。构建器拒绝未提交的输入，确保记录的来源提交准确；SHA-256 校验和不是签名。
