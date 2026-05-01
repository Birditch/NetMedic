"""Pretty-print detection results with rich tables/panels."""
from __future__ import annotations

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .detect.adapter import AdapterInfo
from .detect.connectivity import PingResult
from .detect.dns_pollution import PollutionResult
from .detect.dns_speed import DnsServerResult
from .detect.doh_speed import DohResult
from .detect.mtu import MtuInfo

console = Console()


def render_adapter(info: AdapterInfo | None) -> None:
    if info is None:
        console.print(Panel(
            "[red]未找到默认路由对应的活动网卡, 请检查网络是否已连通.[/red]",
            title="活动网卡", border_style="red",
        ))
        return
    body = (
        f"网卡:        [cyan]{info.alias}[/cyan]  (ifIndex={info.ifindex})\n"
        f"描述:        {info.description}\n"
        f"IPv4:        {info.ipv4 or '-'}\n"
        f"网关:        {info.gateway or '-'}\n"
        f"当前 DNS:    [yellow]"
        f"{', '.join(info.dns_servers) if info.dns_servers else '<DHCP / 自动获取>'}[/yellow]"
    )
    console.print(Panel(body, title="活动网卡", border_style="cyan"))


def render_connectivity(label: str, results: list[PingResult]) -> None:
    t = Table(title=f"连通性 — {label}", box=box.SIMPLE_HEAVY)
    t.add_column("目标")
    t.add_column("丢包率", justify="right")
    t.add_column("平均 ms", justify="right")
    t.add_column("最小/最大", justify="right")
    t.add_column("状态")
    for r in results:
        if r.loss_pct >= 100:
            status = "[red]全部超时[/red]"
        elif r.loss_pct > 0:
            status = f"[yellow]丢 {r.loss_pct:.0f}%[/yellow]"
        elif r.avg_ms is not None and r.avg_ms > 200:
            status = "[yellow]延迟偏高[/yellow]"
        else:
            status = "[green]OK[/green]"
        t.add_row(
            r.label,
            f"{r.loss_pct:.0f}%",
            f"{r.avg_ms:.1f}" if r.avg_ms is not None else "-",
            f"{r.min_ms}/{r.max_ms}" if r.min_ms is not None else "-",
            status,
        )
    console.print(t)


def render_dns_speed(results: list[DnsServerResult]) -> None:
    sorted_results = sorted(
        results, key=lambda r: (r.avg_ms is None, r.avg_ms or 9_999.0)
    )
    t = Table(title="公共 DNS 速度排行", box=box.SIMPLE_HEAVY)
    t.add_column("DNS")
    t.add_column("地区")
    t.add_column("主 IP")
    t.add_column("平均 ms", justify="right")
    t.add_column("中位 ms", justify="right")
    t.add_column("成功率", justify="right")
    t.add_column("说明", overflow="fold")
    for r in sorted_results:
        s = r.server
        avg = f"{r.avg_ms:.1f}" if r.avg_ms is not None else "[red]超时[/red]"
        med = f"{r.median_ms:.1f}" if r.median_ms is not None else "-"
        sr = f"{r.success_rate * 100:.0f}%"
        t.add_row(s.name, s.region.upper(), s.primary, avg, med, sr, s.description)
    console.print(t)


def render_pollution(results: list[PollutionResult]) -> None:
    t = Table(title="DNS 污染检测", box=box.SIMPLE_HEAVY)
    t.add_column("DNS")
    t.add_column("地区")
    t.add_column("被污染域名", overflow="fold")
    t.add_column("可疑域名", overflow="fold")
    t.add_column("失败")
    t.add_column("结论")
    for r in results:
        if r.polluted_domains:
            verdict = "[red]污染[/red]"
        elif r.suspicious_domains:
            verdict = "[yellow]可疑[/yellow]"
        elif r.failed_domains and not r.sample_results.get(
                next(iter(r.sample_results), ""), [],
        ):
            verdict = "[dim]不可达[/dim]"
        else:
            verdict = "[green]干净[/green]"
        t.add_row(
            r.server.name,
            r.server.region.upper(),
            ", ".join(r.polluted_domains) or "-",
            ", ".join(r.suspicious_domains) or "-",
            str(len(r.failed_domains)),
            verdict,
        )
    console.print(t)


def render_mtu(results: list[MtuInfo]) -> None:
    if not results:
        return
    t = Table(title="接口 MTU", box=box.SIMPLE_HEAVY)
    t.add_column("接口")
    t.add_column("MTU", justify="right")
    t.add_column("说明")
    for r in results:
        t.add_row(r.interface, str(r.current_mtu), r.notes)
    console.print(t)


def render_doh_bench(results: list[DohResult]) -> None:
    sorted_results = sorted(
        results, key=lambda r: (r.avg_ms is None, r.avg_ms or 9_999.0)
    )
    t = Table(
        title="DoH 真实测速 + 污染检测 (走 HTTPS:443, 软路由无法干扰)",
        box=box.SIMPLE_HEAVY,
    )
    t.add_column("提供商")
    t.add_column("运营方")
    t.add_column("地区")
    t.add_column("最快 ms", justify="right")
    t.add_column("中位 ms", justify="right")
    t.add_column("平均 ms", justify="right")
    t.add_column("成功率", justify="right")
    t.add_column("污染")
    for r in sorted_results:
        if r.avg_ms is None:
            mn = med = avg = "[red]超时[/red]"
        else:
            mn = f"{r.min_ms:.0f}"
            med = f"{r.median_ms:.0f}"
            avg = f"{r.avg_ms:.0f}"
        sr = f"{r.success_rate * 100:.0f}%"
        if r.pollution_failed:
            poll = "[dim]测不到[/dim]"
        elif r.polluted_domains:
            poll = f"[red]污染 ({len(r.polluted_domains)})[/red]"
        else:
            poll = "[green]干净[/green]"
        t.add_row(r.name, r.operator, r.region.upper(), mn, med, avg, sr, poll)
    console.print(t)


def _ns_list(rule: dict) -> list[str]:
    ns = rule.get("Namespace")
    if isinstance(ns, list):
        return [str(x) for x in ns]
    if ns:
        return [str(ns)]
    return []


def _srv_tuple(rule: dict) -> tuple[str, ...]:
    srv = rule.get("NameServers")
    if isinstance(srv, list):
        return tuple(str(x) for x in srv)
    if srv:
        return (str(srv),)
    return ()


def render_nrpt_summary(rules: list[dict]) -> None:
    """Render a *meaningful* summary instead of dumping every rule.

    Groups rules by their (NameServers, Comment) pair so the user can
    immediately see what each policy block is doing instead of staring
    at 90 identical-looking rows.
    """
    if not rules:
        console.print("[dim]当前没有 NRPT 分流规则.[/dim]")
        return

    from collections import defaultdict
    groups: dict[tuple[tuple[str, ...], str], list[str]] = defaultdict(list)
    for r in rules:
        key = (_srv_tuple(r), str(r.get("Comment") or ""))
        groups[key].extend(_ns_list(r))

    tbl = Table(
        title=f"NRPT 分流规则 — 共 {len(rules)} 条 / {len(groups)} 组策略",
        box=box.SIMPLE_HEAVY,
    )
    tbl.add_column("DNS 目标", overflow="fold")
    tbl.add_column("命名空间数", justify="right")
    tbl.add_column("策略标签", style="dim")
    tbl.add_column("命名空间样例", overflow="fold")
    for (servers, comment), namespaces in groups.items():
        sample_n = 4
        sample = ", ".join(sorted(namespaces)[:sample_n])
        if len(namespaces) > sample_n:
            sample += f", ... +{len(namespaces) - sample_n}"
        tbl.add_row(
            ", ".join(servers) or "-",
            str(len(namespaces)),
            comment or "-",
            sample,
        )
    console.print(tbl)
    console.print(
        "[dim]含义: 当系统解析这些命名空间下的域名时, 会跳过网卡默认 DNS, "
        "直接走 NRPT 指定的 DNS。常见用途是「国内域名走国内 DNS, 境外域名走境外 DoH」"
        "的智能分流, 避免国内服务被解析成境外 IP 而绕路。\n"
        "  • 用 [cyan]python run.py status --verbose[/cyan] 查看每条命名空间.\n"
        "  • 用 [cyan]python run.py restore[/cyan] 清掉本工具写入的 NRPT.[/dim]"
    )


def render_nrpt_rules(rules: list[dict]) -> None:
    """Detailed (verbose) listing — one row per namespace."""
    if not rules:
        console.print("[dim]当前没有 NRPT 分流规则.[/dim]")
        return
    t = Table(title=f"NRPT 规则 — 详细 ({len(rules)} 条)", box=box.SIMPLE_HEAVY)
    t.add_column("命名空间", overflow="fold")
    t.add_column("DNS 服务器", overflow="fold")
    t.add_column("Comment")
    for r in rules:
        ns_text = ", ".join(_ns_list(r)) or "-"
        srv_text = ", ".join(_srv_tuple(r)) or "-"
        t.add_row(ns_text, srv_text, str(r.get("Comment") or ""))
    console.print(t)
