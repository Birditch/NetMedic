<!--
   NetMedic - Windows DNS 與網路醫生
   作者: Birditch  |  授權: MIT  |  版本: 1.0.0
   關鍵字: Windows DNS 修復, DoH, 加密 DNS, 分流 DNS, NRPT, 軟路由診斷,
           跨地區 DNS 路由, dnspython
-->

# NetMedic — Windows DNS 與網路醫生

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](netmedic/__init__.py)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/platform-Windows%2010%2F11-lightgrey.svg)](#環境需求)
[![CI](https://github.com/Birditch/NetMedic/actions/workflows/ci.yml/badge.svg)](https://github.com/Birditch/NetMedic/actions/workflows/ci.yml)
[![GitHub stars](https://img.shields.io/github/stars/Birditch/NetMedic?style=social)](https://github.com/Birditch/NetMedic/stargazers)

> **Windows 上的 DNS 與網路連通性健檢/修復工具，專為「不對稱出口」家庭網路（軟路由讓一部分流量從境外節點出，
> 另一部分維持本地直連）最佳化。這種拓樸下，樸素的 DNS 設定會導致莫名卡頓、第三方登入失敗、跨區域路由錯亂。**

**平台狀態**：目前**只支援 Windows**。Linux / macOS 支援在
[ROADMAP](ROADMAP.md) 上規劃中——跨平台抽象層 `netmedic/platform_adapter.py`
已就位，後端會陸續推出。

**語言**: [English](README.md) · [简体中文](README-zh-CN.md) · **繁體中文**

---

## 贊助 · Sponsor

穩定優質的網路環境，是重現並修復 NetMedic 這類問題的前提。本專案由
**[Pierlink](https://pierlink.net)** 贊助 ——
**優質、便宜、穩定**的網路服務，**註冊即送 30 天試用期**，
你可以親自比對啟用前後的 NetMedic 測速資料。

> *Pierlink 是作者維護本專案的支持來源；它不是 NetMedic 的相依套件，
> 只是一個推薦的、行為良好的網路路徑，用來測試與日常使用。*

---

## 它解決什麼問題

典型痛點：流量經軟路由（OpenWrt / iKuai / 愛快 / Padavan 等）從境外節點出口。大多數情況都能用，但是：

- 部分境外網頁時不時卡住，重新整理一下又秒開。
- 第三方帳號的快捷登入在已登入的客戶端裡看不到目前工作階段。
- 部分國內常用服務時不時被繞到境外節點上，反而變慢。
- DNS 悄悄外洩，繞過了你設定的隱私策略。

根因幾乎都是其中之一：

- **UDP/53 上的 DNS 投毒** —— 路徑上有人搶答，偽造回應跑贏真實回應。
- **軟路由 DNS 攔截** —— 強制把所有 53 埠查詢走它本地的解析器，你在 Windows 改任何 DNS 都不生效。
- **DNS 給錯地區** —— 國內服務被解析成境外邊緣 IP → 走境外節點 → 慢且觸發風控。

NetMedic 把這三類故障各自檢測出來，給出**誠實**的修復方案，
包括用 Windows 11 原生 **DoH (HTTPS:443)** 直接繞過對 53 埠的攔截。

## 功能

- **互動式啟動器**：第一次啟動會引導你選語言和國家/地區，然後進入數字選單。
  每個選單項都有目前語言的完整說明，並標註是否需要管理員權限。
- **依賴自動 bootstrap**：缺什麼 pip 套件，提示一下，自動安裝並重啟腳本。
- **整體網路健檢**：網路卡資訊、國內/境外 ping/丟包、MTU 健康度。
- **公共 DNS 速度排行**：UDP 延遲測速。
- **DNS 汙染檢測**：已知毒池 IP 表 + 亞毫秒回應啟發式判定。
- **DoH 真實測速 + 汙染檢測**：直接走 HTTPS:443，軟路由沒法在 53 埠造假。
- **範圍選擇器**：測速前選 *僅當前國家* / *當前國家 + 全球大廠* / *全部提供者*。
- **Top 5 互動選擇**：從最快的「乾淨」DoH 中按 1-5 選你要的（帶提供者、營運方、地區、IPs、說明）。
- **智慧分流 DNS**：地區敏感命名空間自動走對應地區的 DoH，透過 Windows 原生 NRPT 實現。
- **IPv6 自檢**：偵測到真實 v6 連通才會詢問要不要啟用 v6 DoH。
- **原子備份 + 一鍵還原**：每次 `apply` 都把原 DNS 寫到 `backups/latest.json`，`restore` 一鍵回滾。
- **hosts 檔案修復**：偵測重複條目、黑洞條目、格式錯誤並清理（絕不動其他工具的標記區塊）。
- **斷網診斷鏈路**：Loopback → 閘道 → 網際網路 → DNS → HTTPS 五層逐級測，定位故障點。
- **路由器攔截偵測**：境外 DNS 回應 < 5ms 是軟路由攔截的鐵證，工具會標紅並建議切 Force-DoH。
- **多語言**：簡體中文、繁體中文、English、日本語、한국어、Русский。

## 環境需求

| 元件 | 版本 |
|---|---|
| 作業系統 | **Windows 10 / 11**。Linux / macOS 規劃中——見 [ROADMAP](ROADMAP.md)。 |
| Python | **3.10+**（由 dnspython 2.8 與 typer 0.25 決定下限） |
| 權限 | `apply` / `restore` / `force-doh` / `hosts-fix` 需要管理員 |

依賴會在 CI 每次跑 `pip install --upgrade` 拉最新相容版本：
[dnspython](https://www.dnspython.org/)（含 [httpx](https://www.python-httpx.org/) +
[h2](https://github.com/python-hyper/h2) 用於 DoH）、
[rich](https://github.com/Textualize/rich)、[typer](https://typer.tiangolo.com/)。

## 安裝與第一次執行

```powershell
git clone https://github.com/Birditch/NetMedic.git
cd NetMedic
python run.py
```

就這樣。第一次執行 NetMedic 會：

1. 偵測 `dnspython / rich / typer / httpx / h2` 能否 import。
   有缺失就彈 y/n 提示，pip 安裝完成後**自動重啟腳本**。
2. 詢問 **UI 語言**（按 Enter 接受推薦預設）。
3. 詢問 **國家/地區**（按 Enter 接受 `AUTO`）。
4. 進入數字選單。

之後每次啟動都會沿用你儲存的選擇 —— 但選單頂部永遠有
「切換語言」和「切換國家」兩項，按 Enter 預設保持目前值，所以你可以隨時改。

## 使用方式

- **互動選單**：`python run.py`（無參數）→ 數字選單。
- **直接 CLI**：每個選單功能也是 typer 子命令，方便指令稿化：

  ```powershell
  python run.py status
  python run.py force-doh
  python run.py force-doh --scope country+majors
  python run.py force-doh --intl-dns 1.1.1.1,8.8.8.8
  python run.py restore
  python run.py --lang ja check
  ```

## NetMedic 怎麼挑「最佳 DNS」

```
1. UDP 測速           → 平均 / 中位 / 成功率
2. 汙染評分           → 已知毒池 IP、亞毫秒回應（< 5 ms）
3. DoH HTTPS 真實測速 → 軟路由干擾不了的黃金標準
4. 過濾乾淨集         → 剔除被汙染 / 可疑 / 逾時
5. 依平均延遲排序     → 列出 Top 5（帶營運方、地區、v4/v6 IP）
6. 由你來選           → 註冊 DoH 範本、設定網路卡 DNS、寫 NRPT 分流
```

## 多語言

語言檔在 [`locales/`](locales/) 下：
[`en`](locales/en.json)、[`zh-CN`](locales/zh-CN.json)、
[`zh-TW`](locales/zh-TW.json)、[`ja`](locales/ja.json)、
[`ko`](locales/ko.json)、[`ru`](locales/ru.json)。

優先順序：`--lang` 命令列參數 → 已儲存的設定 → `NETMEDIC_LANG` 環境變數 → 系統語言 → `en` 兜底。
歡迎 PR 新語種翻譯，參考 [CONTRIBUTING](CONTRIBUTING.md#adding-a-new-language)。

## 致謝

NetMedic 由以下三個出色的開發者工具協作完成，特此鳴謝：

- **[JetBrains PyCharm](https://www.jetbrains.com/pycharm/)** —— 主力 IDE。
  特別感謝 **JetBrains** 透過
  [開放原始碼開發授權](https://www.jetbrains.com/community/opensource/) 計畫
  為開源維護者免費提供專業版工具。
- **[Anthropic Claude Code](https://www.anthropic.com/claude-code)** ——
  在設計、重構、文件各階段作為 pair programmer 持續協作。
- **[OpenAI Codex](https://openai.com/index/openai-codex/)** ——
  用於二次程式碼審查和邊界情況建議。

如果本專案對你有幫助，請考慮試試這些產品來支援他們。

[<img src="https://resources.jetbrains.com/storage/products/company/brand/logos/jb_beam.png" width="120" alt="JetBrains Logo"/>](https://www.jetbrains.com/)
[<img src="https://resources.jetbrains.com/storage/products/company/brand/logos/PyCharm_icon.png" width="64" alt="PyCharm Logo"/>](https://www.jetbrains.com/pycharm/)

## 授權

MIT © 2026 **Birditch**. 完整內容見 [LICENSE](LICENSE)。
