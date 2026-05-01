<!--
   NetMedic - DNS 与网络医生
   作者: Birditch  |  许可: MIT  |  版本: 1.0.1b1
   关键词: 跨平台 DNS 修复, DoH, 加密 DNS, 分流 DNS, NRPT, 软路由诊断,
           跨地区 DNS 路由, dnspython
-->

# NetMedic — DNS 与网络医生

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-1.0.1b1-blue.svg)](netmedic/__init__.py)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)](#环境要求)
[![CI](https://github.com/Birditch/NetMedic/actions/workflows/ci.yml/badge.svg)](https://github.com/Birditch/NetMedic/actions/workflows/ci.yml)
[![GitHub stars](https://img.shields.io/github/stars/Birditch/NetMedic?style=social)](https://github.com/Birditch/NetMedic/stargazers)

> **跨平台 DNS 与网络连通性体检/修复工具。Windows 目前具备完整修复后端，
> 包括原生 DoH 与 NRPT 分流；macOS / Linux 的包安装和运行时支持已进入预览，
> DNS 写入后端会继续增量落地。NetMedic 专为「非对称出口」家庭网络调优，
> 这种拓扑下朴素的 DNS 配置会导致莫名卡顿、第三方登录失败、跨区域路由错乱。**

**平台状态**：

| 平台 | 状态 |
|---|---|
| Windows 10 / 11 | 完整诊断与修复支持。Windows 11 推荐用于系统级原生 DoH。 |
| macOS 12+ | 纯 Python 包安装/运行时预览；DNS 写入后端在 [ROADMAP](ROADMAP.md) 跟踪。 |
| Linux | 纯 Python 包安装/运行时预览；resolver 后端在 [ROADMAP](ROADMAP.md) 跟踪。 |

**语言**: [English](README.md) · **简体中文** · [繁體中文](README-zh-TW.md)

---

## 赞助 · Sponsor

稳定优质的网络环境，是复现并修复 NetMedic 这类问题的前提。本项目由
**[Pierlink](https://pierlink.net)** 赞助 ——
**优质、便宜、稳定**的网络服务，**注册即送 30 天试用期**，
你可以亲自对比启用前后的 NetMedic 测速数据。

> *Pierlink 是作者维护本项目的支持来源；它不是 NetMedic 的依赖，
> 只是一个推荐的、行为良好的网络路径，用来做测试与日常使用。*

---

## 它解决什么问题

典型痛点：流量经软路由（OpenWrt / iKuai / 爱快 / Padavan 等）从境外节点出口。大多数情况都能用，但是：

- 部分境外网页时不时卡住，刷新一下又秒开。
- 第三方账号的快捷登录在已登录客户端里看不到当前会话。
- 部分国内常用服务时不时被绕到境外节点上，反而变慢。
- DNS 悄悄外泄，绕过了你设置的隐私策略。

根因几乎都是其中之一：

- **UDP/53 上的 DNS 投毒** —— 路径上有人抢答，伪造响应跑赢真实响应。
- **软路由 DNS 劫持** —— 强制把所有 53 端口查询走它本地的解析器，你在 Windows 改任何 DNS 都不生效。
- **DNS 给错地区** —— 国内服务被解析成境外边缘 IP → 走境外节点 → 慢且触发风控。

NetMedic 把这三类故障各自检测出来，给出**诚实**的修复方案，
包括用 Windows 11 原生 **DoH (HTTPS:443)** 直接绕过对 53 端口的拦截。

## 功能

- **交互式启动器**：第一次启动会引导你选语言和国家/地区，然后进入数字菜单。
  每个菜单项都有当前语言的完整说明，并标注是否需要管理员权限。
- **依赖自动 bootstrap**：缺什么 pip 包，提示一下，自动安装并重启脚本。
- **整体网络体检**：网卡信息、国内/境外 ping/丢包、MTU 健康度。
- **公共 DNS 速度排行**：UDP 延迟测速。
- **DNS 污染检测**：已知毒池 IP 表 + 亚毫秒应答启发式判定。
- **DoH 真实测速 + 污染检测**：直接走 HTTPS:443，软路由没法在 53 端口造假。
- **范围选择器**：测速前选 *仅当前国家* / *当前国家 + 全球大厂* / *全部提供商*。
- **Top 5 交互选择**：从最快的「干净」DoH 中按 1-5 选你要的（带提供商、运营方、地区、IPs、说明）。
- **智能分流 DNS**：地区敏感命名空间自动走对应地区的 DoH，通过 Windows 原生 NRPT 实现。
- **IPv6 自检**：检测到真实 v6 连通才会询问要不要启用 v6 DoH。
- **原子备份 + 一键还原**：每次 `apply` 都把原 DNS 写到 `backups/latest.json`，`restore` 一键回滚。
- **hosts 文件修复**：检测重复条目、黑洞条目、格式错误并清理（绝不动其他工具的标记块）。
- **断网诊断链路**：Loopback → 网关 → 互联网 → DNS → HTTPS 五层逐级测，定位故障点。
- **路由器劫持检测**：境外 DNS 应答 < 5ms 是软路由劫持的铁证，工具会标红并建议切 Force-DoH。
- **多语言**：简体中文、繁體中文、English、日本語、한국어、Русский。

## 环境要求

| 组件 | 版本 |
|---|---|
| 操作系统 | **Windows 10 / 11**、**macOS 12+**、**Linux**。完整 DNS 修复后端目前在 Windows；macOS / Linux 后端进行中。 |
| Python | **3.10+**（由 dnspython 2.8 与 typer 0.25 决定下限） |
| 权限 | `apply` / `restore` / `force-doh` / `hosts-fix` 需要管理员 |

依赖会在 CI 每次跑 `pip install --upgrade` 拿最新兼容版本：
[dnspython](https://www.dnspython.org/)（含 [httpx](https://www.python-httpx.org/) +
[h2](https://github.com/python-hyper/h2) 用于 DoH）、
[rich](https://github.com/Textualize/rich)、[typer](https://typer.tiangolo.com/)。

## 安装与第一次运行

```powershell
git clone https://github.com/Birditch/NetMedic.git
cd NetMedic
python run.py
```

完事。第一次运行 NetMedic 会：

1. 检测 `dnspython / rich / typer / httpx / h2` 是否能 import。
   如果有缺失，弹出 y/n 提示，pip 安装完成后**自动重启脚本**。
2. 询问 **UI 语言**（按 Enter 接受推荐默认）。
3. 询问 **国家/地区**（按 Enter 接受 `AUTO`）。
4. 进入数字菜单。

之后每次启动都会沿用你保存的选择 —— 但菜单顶部永远有
"切换语言"和"切换国家"两项，按 Enter 默认保持当前值，所以你可以随时改。

## 使用方式

- **交互菜单**：`python run.py`（无参数）→ 数字菜单。
- **直接 CLI**：每个菜单功能也是 typer 子命令，方便脚本化：

  ```powershell
  python run.py status
  python run.py force-doh
  python run.py force-doh --scope country+majors
  python run.py force-doh --intl-dns 1.1.1.1,8.8.8.8
  python run.py restore
  python run.py --lang ja check
  ```

## NetMedic 怎么挑「最优 DNS」

```
1. UDP 测速           → 平均 / 中位 / 成功率
2. 污染评分           → 已知毒池 IP、亚毫秒应答（< 5 ms）
3. DoH HTTPS 真实测速 → 软路由干扰不了的金标准
4. 过滤干净集         → 剔除被污染 / 可疑 / 超时
5. 按平均延迟排序     → 列出 Top 5（带运营方、地区、v4/v6 IP）
6. 你来选             → 注册 DoH 模板、设置网卡 DNS、写 NRPT 分流
```

## 多语言

语言文件在 [`netmedic/locales/`](netmedic/locales/) 下：
[`en`](netmedic/locales/en.json)、[`zh-CN`](netmedic/locales/zh-CN.json)、
[`zh-TW`](netmedic/locales/zh-TW.json)、[`ja`](netmedic/locales/ja.json)、
[`ko`](netmedic/locales/ko.json)、[`ru`](netmedic/locales/ru.json)。

优先级：`--lang` 命令行参数 → 保存的配置 → `NETMEDIC_LANG` 环境变量 → 系统语言 → `en` 兜底。
欢迎 PR 新语种翻译，参考 [CONTRIBUTING](CONTRIBUTING.md#adding-a-new-language)。

## 致谢

NetMedic 由以下三个出色的开发者工具协作完成，特此鸣谢：

- **[JetBrains PyCharm](https://www.jetbrains.com/pycharm/)** —— 主力 IDE。
  特别感谢 **JetBrains** 透过
  [开源开发许可证](https://www.jetbrains.com/community/opensource/) 计划
  为开源维护者免费提供专业版工具。
- **[Anthropic Claude Code](https://www.anthropic.com/claude-code)** ——
  在设计、重构、文档各阶段作为 pair programmer 持续协作。
- **[OpenAI Codex](https://openai.com/index/openai-codex/)** ——
  用于二次代码评审和边界情况建议。

如果本项目对你有帮助，请考虑用一下这些产品来支持他们。

[<img src="https://resources.jetbrains.com/storage/products/company/brand/logos/jb_beam.png" width="120" alt="JetBrains Logo"/>](https://www.jetbrains.com/)
[<img src="https://resources.jetbrains.com/storage/products/company/brand/logos/PyCharm_icon.png" width="64" alt="PyCharm Logo"/>](https://www.jetbrains.com/pycharm/)

## 许可

MIT © 2026 **Birditch**. 完整文本见 [LICENSE](LICENSE)。
