"""NetMedic CLI — 检测并修复网络/DNS 环境.

子命令:
    check      全面体检 (无须管理员)
    recommend  根据测速 / 污染检测推荐配置, 但不动系统
    apply      把推荐配置写入网卡 + NRPT 分流 (需管理员)
    restore    从最近一次备份还原 (需管理员)
    flush      只刷新 DNS 缓存
    status     查看当前 DNS 与 NRPT 规则
"""
import sys

# Force UTF-8 stdout/stderr so emojis and 中文 render correctly even when
# launched from cmd.exe with codepage 936.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except (AttributeError, ValueError):
        pass

import typer
from rich.panel import Panel
from rich.prompt import IntPrompt
from rich.table import Table
from rich import box

from .config import CONNECTIVITY_TARGETS
from . import user_config
from .data.cn_domains import CN_NAMESPACES
from .data.dns_scope import SCOPE_VALUES, filter_providers
from .data.public_dns import ALL_SERVERS, CN_SERVERS, INTL_SERVERS
from .detect.adapter import get_active_adapter
from .detect.connectivity import ping_many
from .detect.dns_pollution import check_pollution_all
from .detect.dns_speed import benchmark_all
from .detect.doh_speed import benchmark_all_doh
from .detect.ipv6 import has_ipv6
from .detect.mtu import analyze_mtu
from .fix.backup import backup_dns, latest_backup
from .fix.dns_apply import reset_dns, set_dns
from .fix.doh import (
    DOH_PROVIDERS,
    DOH_TEMPLATES,
    doh_supported,
    filter_doh_capable,
    register_doh,
)
from .fix.flush import flush_dns
from .fix.nrpt import add_rules, list_rules, remove_our_rules
from .i18n import SUPPORTED, set_lang
from .reporter import (
    console,
    render_adapter,
    render_connectivity,
    render_dns_speed,
    render_doh_bench,
    render_mtu,
    render_nrpt_rules,
    render_pollution,
)
from .utils import is_admin

app = typer.Typer(
    add_completion=False,
    help="NetMedic — Network Doctor / 网络医生",
    no_args_is_help=True,
)


@app.callback()
def _root(
    lang: str = typer.Option(
        None, "--lang",
        help=f"UI language. Supported: {', '.join(SUPPORTED)}. Defaults to OS locale.",
    ),
):
    if lang:
        set_lang(lang)


def _need_admin() -> None:
    if not is_admin():
        console.print(
            "[red]此命令需要管理员权限. 请用管理员身份打开 PowerShell, 然后再运行.[/red]"
        )
        raise typer.Exit(code=2)


def _pick_best(results, region=None):
    eligible = [
        r for r in results
        if r.avg_ms is not None
        and r.success_rate >= 0.9
        and (region is None or r.server.region == region)
    ]
    eligible.sort(key=lambda r: r.avg_ms)
    return eligible[0] if eligible else None


def _pick_best_intl(speed_results, pollution_map):
    """Choose the fastest *uncontaminated* foreign DNS.

    Skips any server that:
    - is_polluted (returned a known GFW poison IP), OR
    - has any suspicious_domains (sub-floor RTT, almost certainly injected
      or pulled from a local cache and therefore unreliable), OR
    - has avg_ms < 5ms (physically impossible from China via Japan; means
      the result we measured is not coming from the real foreign server).
    """
    clean = []
    for r in speed_results:
        if r.server.region != "intl":
            continue
        if r.avg_ms is None or r.success_rate < 0.9:
            continue
        if r.avg_ms < 5.0:
            continue
        poll = pollution_map.get(r.server.name)
        if poll is not None and (poll.is_polluted or poll.suspicious_domains):
            continue
        clean.append(r)
    clean.sort(key=lambda r: r.avg_ms)
    return clean[0] if clean else None


def _detect_dns_hijack(speed_results) -> bool:
    """All overseas DNS responding < 5ms means the local network (soft router,
    captive portal, ISP) is intercepting port 53 — Windows DNS settings won't
    take effect.
    """
    intl = [r for r in speed_results
            if r.server.region == "intl" and r.avg_ms is not None]
    if len(intl) < 3:
        return False
    fake_fast = sum(1 for r in intl if r.avg_ms < 5.0)
    return fake_fast >= len(intl) * 0.6


@app.command()
def check(
    skip_pollution: bool = typer.Option(False, "--skip-pollution", help="跳过污染检测"),
    skip_speed: bool = typer.Option(False, "--skip-speed", help="跳过 DNS 速度测试"),
):
    """全面体检 (无须管理员)."""
    console.rule("[bold cyan]NetMedic 网络体检[/bold cyan]")
    render_adapter(get_active_adapter())

    console.print()
    render_connectivity("国内", ping_many(CONNECTIVITY_TARGETS["domestic"]))
    console.print()
    render_connectivity("境外", ping_many(CONNECTIVITY_TARGETS["international"]))

    if not skip_speed:
        console.print()
        with console.status(f"[cyan]正在测试 {len(ALL_SERVERS)} 个公共 DNS..."):
            speed_results = benchmark_all(ALL_SERVERS)
        render_dns_speed(speed_results)

    if not skip_pollution:
        console.print()
        with console.status("[cyan]正在做 DNS 污染检测..."):
            poll_results = check_pollution_all(ALL_SERVERS)
        render_pollution(poll_results)

    console.print()
    render_mtu(analyze_mtu())


@app.command()
def recommend():
    """根据测速 + 污染检测给出推荐配置, 不动系统."""
    console.rule("[bold cyan]推荐配置[/bold cyan]")
    with console.status("[cyan]测速 + 污染检测中..."):
        speed = benchmark_all(ALL_SERVERS)
        pollution_map = {p.server.name: p for p in check_pollution_all(ALL_SERVERS)}

    cn_best = _pick_best(speed, region="cn")
    intl_best = _pick_best_intl(speed, pollution_map)

    if _detect_dns_hijack(speed):
        console.print(Panel(
            "[yellow]检测到几乎所有境外 DNS 响应都 < 5ms — 物理上不可能.\n"
            "你所在的网络 (大概率是软路由) 在 UDP 53 端口拦截/缓存了 DNS 流量.\n\n"
            "这意味着:\n"
            "  • 改 Windows DNS [bold]不会真正生效[/bold], 请求依然被软路由处理\n"
            "  • NRPT 分流也只是改变 [bold]Windows 询问哪台 DNS[/bold], 数据包依旧被劫持\n\n"
            "建议按优先级处理:\n"
            "  1. 去软路由后台 (OpenWrt/iKuai/...) 关掉强制 DNS 劫持, "
            "或在 mosdns/AdGuardHome 里配好分流, 然后回来再跑本工具\n"
            "  2. 或在 Windows 11 启用 DoH (设置 → 网络和 Internet → "
            "以太网 → DNS 服务器分配 → 编辑, DNS 加密改为 [bold]仅加密[/bold]),\n"
            "     DoH 走 443 端口, 软路由的 53 劫持就管不着了\n"
            "  3. 如果你本来就信任软路由的 DNS, 那就 [bold]什么也别做[/bold], "
            "本工具的 apply 帮不到你[/yellow]",
            title="⚠ 检测到 DNS 被本地劫持",
            border_style="yellow",
        ))
        console.print(
            "\n如果你 [bold]确认[/bold] 软路由没劫持 (例如它只是个透明转发), "
            "可以用:\n"
            "  [cyan]python run.py apply --intl-dns 1.1.1.1,8.8.8.8 "
            "--cn-dns 223.5.5.5,119.29.29.29[/cyan]\n"
            "强制写入指定的 DNS, 跳过自动选优.\n"
        )
        raise typer.Exit(code=0)

    if not cn_best or not intl_best:
        console.print("[red]测试失败, 没有任何可用 DNS. 请先排查网络连通性.[/red]")
        raise typer.Exit(code=1)

    body = (
        f"国内域名走:    [green]{cn_best.server.name} ({cn_best.server.primary})[/green]\n"
        f"               平均 {cn_best.avg_ms:.1f}ms — {cn_best.server.description}\n\n"
        f"境外域名走:    [green]{intl_best.server.name} ({intl_best.server.primary})[/green]\n"
        f"               平均 {intl_best.avg_ms:.1f}ms — {intl_best.server.description}\n\n"
        f"分流命名空间:  共 [cyan]{len(CN_NAMESPACES)}[/cyan] 条 "
        f"(qq.com / weixin.qq.com / taobao.com / bilibili.com / ...)"
    )
    console.print(Panel(body, title="推荐分流策略", border_style="green"))
    console.print(
        "\n执行 [cyan]python run.py apply[/cyan] (需管理员) 一键写入. "
        "稍后可用 [cyan]python run.py restore[/cyan] 一键还原."
    )


@app.command()
def apply(
    cn_dns: str = typer.Option(
        None, "--cn-dns", help="覆盖国内 DNS, 用逗号分隔, 如 223.5.5.5,119.29.29.29"
    ),
    intl_dns: str = typer.Option(
        None, "--intl-dns", help="覆盖境外 DNS, 用逗号分隔, 如 1.1.1.1,8.8.8.8"
    ),
    no_nrpt: bool = typer.Option(False, "--no-nrpt", help="不写 NRPT 分流规则"),
):
    """应用推荐配置: 网卡 DNS + NRPT 分流 (需管理员)."""
    _need_admin()
    adapter = get_active_adapter()
    if adapter is None:
        console.print("[red]找不到活动网卡, 中止.[/red]")
        raise typer.Exit(code=1)

    console.rule("[bold cyan]应用配置[/bold cyan]")
    render_adapter(adapter)

    if cn_dns:
        cn_servers = [s.strip() for s in cn_dns.split(",") if s.strip()]
        cn_label = "用户自定义"
    else:
        with console.status("[cyan]测试国内 DNS..."):
            speed_cn = benchmark_all(CN_SERVERS)
        best = _pick_best(speed_cn, region="cn")
        if not best:
            console.print("[red]国内 DNS 全部不可达, 中止.[/red]")
            raise typer.Exit(code=1)
        s = best.server
        cn_servers = [s.primary] + ([s.secondary] if s.secondary else [])
        cn_label = f"{s.name} ({best.avg_ms:.0f}ms)"

    if intl_dns:
        intl_servers = [s.strip() for s in intl_dns.split(",") if s.strip()]
        intl_label = "用户自定义"
    else:
        with console.status("[cyan]测试境外 DNS + 污染检测..."):
            speed_intl = benchmark_all(INTL_SERVERS)
            poll_intl = {p.server.name: p for p in check_pollution_all(INTL_SERVERS)}
        if _detect_dns_hijack(speed_intl):
            console.print(
                "[yellow]检测到本地网络在劫持 53 端口, 自动选优不可信.\n"
                "请手动指定: --intl-dns 1.1.1.1,8.8.8.8\n"
                "或先跑 [cyan]python run.py recommend[/cyan] 看完整诊断.[/yellow]"
            )
            raise typer.Exit(code=1)
        best = _pick_best_intl(speed_intl, poll_intl)
        if not best:
            console.print("[red]没有合格的无污染境外 DNS, 中止.[/red]")
            raise typer.Exit(code=1)
        s = best.server
        intl_servers = [s.primary] + ([s.secondary] if s.secondary else [])
        intl_label = f"{s.name} ({best.avg_ms:.0f}ms)"

    console.print(f"[cyan]国内 DNS:[/cyan] {cn_label} -> {cn_servers}")
    console.print(f"[cyan]境外 DNS:[/cyan] {intl_label} -> {intl_servers}")

    backup_path = backup_dns(adapter.ifindex)
    console.print(f"[green]✓ 已备份原配置 ->[/green] {backup_path}")

    set_dns(adapter.ifindex, intl_servers)
    console.print("[green]✓ 网卡默认 DNS 已设为境外 DNS[/green]")

    if not no_nrpt:
        cleared = remove_our_rules()
        if cleared:
            console.print(f"[dim]清理旧 NetMedic NRPT 规则: {cleared} 条[/dim]")
        added = add_rules(CN_NAMESPACES, cn_servers)
        console.print(
            f"[green]✓ 已写入 {added} 条 NRPT 分流规则 (国内域名 -> 国内 DNS)[/green]"
        )

    rc, out = flush_dns()
    if rc == 0:
        console.print("[green]✓ DNS 缓存已刷新[/green]")
    else:
        console.print(f"[yellow]flush 警告: {out}[/yellow]")

    console.rule("[bold green]完成[/bold green]")
    console.print(
        "如需:\n"
        "  - 重新体检:  [cyan]python run.py check[/cyan]\n"
        "  - 一键还原:  [cyan]python run.py restore[/cyan]\n"
        "  - 查看现状:  [cyan]python run.py status[/cyan]\n"
    )


@app.command()
def restore():
    """从最近一次备份还原网卡 DNS, 并清除本工具写入的 NRPT 规则 (需管理员)."""
    _need_admin()
    backup = latest_backup()
    if not backup:
        console.print(
            "[red]没找到备份 (backups/latest.json). 没什么可还原的.[/red]"
        )
        raise typer.Exit(code=1)

    ifindex = int(backup["ifindex"])
    dns_data = backup.get("dns")
    if isinstance(dns_data, dict):
        dns_data = [dns_data]
    elif dns_data is None:
        dns_data = []

    addresses: list[str] = []
    for entry in dns_data:
        af = entry.get("AddressFamily")
        if af in (2, "IPv4", "InterNetwork"):
            servers = entry.get("ServerAddresses") or []
            if isinstance(servers, str):
                servers = [servers]
            addresses = [a for a in servers if a]
            break

    if addresses:
        set_dns(ifindex, addresses)
        console.print(f"[green]✓ 已恢复网卡 DNS -> {addresses}[/green]")
    else:
        reset_dns(ifindex)
        console.print("[green]✓ 已恢复网卡 DNS -> DHCP / 自动获取[/green]")

    removed = remove_our_rules()
    console.print(f"[green]✓ 已清除 {removed} 条 NetMedic NRPT 规则[/green]")

    rc, _ = flush_dns()
    if rc == 0:
        console.print("[green]✓ DNS 缓存已刷新[/green]")


def _pick_top5(results, ipv6_ok: bool):
    """Filter to clean+responsive, then return top 5 sorted by avg_ms."""
    pool = []
    for r in results:
        if r.avg_ms is None or r.success_rate < 0.66:
            continue
        if r.polluted_domains:  # explicit non-empty -> exclude
            continue
        # If pollution test totally failed but speed worked, still include but penalise
        pool.append(r)
    pool.sort(key=lambda r: r.avg_ms)
    return pool[:5]


def _ips_for(provider, ipv6_ok: bool) -> list[str]:
    ips = list(provider.v4_ips)
    if ipv6_ok:
        ips += list(provider.v6_ips)
    return ips


@app.command(name="force-doh")
def force_doh(
    intl_dns: str = typer.Option(
        None, "--intl-dns",
        help="跳过交互, 手动指定主 DoH IP (逗号分隔)",
    ),
    cn_dns: str = typer.Option(
        None, "--cn-dns",
        help="跳过交互, 手动指定 NRPT 分流给国内域名用的 DoH IP (逗号分隔)",
    ),
    no_nrpt: bool = typer.Option(False, "--no-nrpt", help="不写 NRPT 分流规则"),
    no_ipv6: bool = typer.Option(False, "--no-ipv6", help="即使 IPv6 可用也跳过"),
    scope: str = typer.Option(
        None, "--scope",
        help=f"DoH 候选范围: {' / '.join(SCOPE_VALUES)} (默认读 user_config)",
    ),
):
    """自动测速 + 污染检测 → top 5 选优 → 切到 DoH (HTTPS:443) 绕过软路由 53 劫持."""
    _need_admin()
    if not doh_supported():
        console.print("[red]当前系统不支持 DoH cmdlets, 需要 Windows 11. 中止.[/red]")
        raise typer.Exit(code=1)

    adapter = get_active_adapter()
    if adapter is None:
        console.print("[red]找不到活动网卡, 中止.[/red]")
        raise typer.Exit(code=1)

    console.rule("[bold cyan]DoH 强制模式[/bold cyan]")
    render_adapter(adapter)

    if intl_dns or cn_dns:
        # Manual override path.
        intl_in = [s.strip() for s in (intl_dns or "1.1.1.1,8.8.8.8").split(",") if s.strip()]
        cn_in = [s.strip() for s in (cn_dns or "223.5.5.5,119.29.29.29").split(",") if s.strip()]
        primary_doh = filter_doh_capable(intl_in)
        cn_doh = filter_doh_capable(cn_in)
        if not primary_doh:
            console.print(
                f"[red]给定的 DoH IP 没有任何一个有已知模板.[/red]\n"
                f"已知支持 DoH 的 IP: {', '.join(sorted(DOH_TEMPLATES))}"
            )
            raise typer.Exit(code=1)
        primary_label = "用户自定义"
        cn_label = "用户自定义" if cn_doh else "(空)"
    else:
        # IPv6 check first
        ipv6_ok = (not no_ipv6) and has_ipv6()
        console.print(
            f"\nIPv6 连通性: {'[green]可用 ✓[/green]' if ipv6_ok else '[dim]不可用[/dim]'}"
        )

        # Resolve scope: explicit flag > user_config > sensible default.
        cfg = user_config.load()
        effective_scope = scope or cfg.get("scope") or "country+majors"
        if effective_scope not in SCOPE_VALUES:
            effective_scope = "country+majors"
        country = cfg.get("country", "AUTO")
        candidates = filter_providers(DOH_PROVIDERS, effective_scope, country)
        console.print(
            f"[dim]Scope:[/dim] [cyan]{effective_scope}[/cyan]   "
            f"[dim]Country:[/dim] [cyan]{country}[/cyan]   "
            f"[dim]Candidates:[/dim] [cyan]{len(candidates)}[/cyan] "
            f"of {len(DOH_PROVIDERS)}"
        )

        # Bench scoped providers
        with console.status(
            "[cyan]正在对每个 DoH 提供商做真实 HTTPS 测速 + 污染检测 (15-40 秒)..."
        ):
            doh_results = benchmark_all_doh(candidates)
        console.print()
        render_doh_bench(doh_results)

        top5 = _pick_top5(doh_results, ipv6_ok)
        if not top5:
            console.print(
                "\n[red]没有任何 DoH 通过 (全部超时或检出污染).[/red]\n"
                "请检查网络连通性, 或用 --intl-dns/--cn-dns 手动指定."
            )
            raise typer.Exit(code=1)

        # Render selection menu
        console.print()
        menu = Table(title="速度 + 干净 综合排名 Top 5", box=box.SIMPLE_HEAVY)
        menu.add_column("#", justify="right")
        menu.add_column("提供商")
        menu.add_column("运营方")
        menu.add_column("地区")
        menu.add_column("平均 ms", justify="right")
        menu.add_column("v4 IPs")
        if ipv6_ok:
            menu.add_column("v6 IPs")
        menu.add_column("说明", overflow="fold")
        for i, r in enumerate(top5, 1):
            row = [
                str(i),
                r.name,
                r.operator,
                r.region.upper(),
                f"{r.avg_ms:.0f}",
                ", ".join(r.v4_ips),
            ]
            if ipv6_ok:
                row.append(", ".join(r.v6_ips) or "-")
            row.append(r.notes)
            menu.add_row(*row)
        console.print(menu)

        choice = IntPrompt.ask(
            "\n[bold]请选择主 DoH (1 = 最快)[/bold]",
            default=1,
            choices=[str(i) for i in range(1, len(top5) + 1)],
            show_choices=True,
        )
        chosen = top5[choice - 1]
        primary_doh = _ips_for(chosen, ipv6_ok)
        primary_label = f"{chosen.name} ({chosen.operator}, {chosen.avg_ms:.0f}ms)"

        # NRPT split: always use the fastest CN provider for *.qq.com etc.
        # so QQ/淘宝 always拿到国内最优 IP, 不受主 DoH 影响.
        cn_only = [r for r in top5 if r.region == "cn"]
        if not cn_only:
            cn_only = [r for r in doh_results
                       if r.region == "cn" and r.avg_ms is not None
                       and not r.polluted_domains]
        if cn_only:
            cn_only.sort(key=lambda r: r.avg_ms)
            cn_pick = cn_only[0]
            cn_doh = _ips_for(cn_pick, ipv6_ok)
            cn_label = f"{cn_pick.name} ({cn_pick.operator}, {cn_pick.avg_ms:.0f}ms)"
        else:
            cn_doh = []
            cn_label = "[yellow](无可用国内 DoH)[/yellow]"

    console.print(
        f"\n[cyan]主 DoH:[/cyan]    {primary_label} -> {primary_doh}\n"
        f"[cyan]CN 分流:[/cyan]   {cn_label} -> {cn_doh}\n"
    )

    backup_path = backup_dns(adapter.ifindex)
    console.print(f"[green]✓ 已备份原配置 ->[/green] {backup_path}")

    registered = register_doh(primary_doh + cn_doh)
    console.print(f"[green]✓ 已注册 {registered} 条 DoH 模板 (HTTPS:443, 软路由拦不住)[/green]")

    set_dns(adapter.ifindex, primary_doh)
    console.print(f"[green]✓ 网卡默认 DNS -> {primary_doh}, Windows 自动升级到 DoH[/green]")

    if not no_nrpt and cn_doh:
        cleared = remove_our_rules()
        if cleared:
            console.print(f"[dim]清理旧 NetMedic NRPT 规则: {cleared} 条[/dim]")
        added = add_rules(CN_NAMESPACES, cn_doh)
        console.print(f"[green]✓ 已写入 {added} 条 NRPT 分流 (国内域名 -> 国内 DoH)[/green]")

    rc, _ = flush_dns()
    if rc == 0:
        console.print("[green]✓ DNS 缓存已刷新[/green]")

    console.rule("[bold green]完成[/bold green]")
    console.print(
        "验证:\n"
        "  1. 浏览器开 https://1.1.1.1/help → \"Using DNS over HTTPS (DoH): Yes\"\n"
        "  2. QQ 快捷登录 / Google 复测\n\n"
        "还原: [cyan]python run.py restore[/cyan]"
    )


@app.command(name="bench-doh")
def bench_doh():
    """只跑 DoH 测速 + 污染检测, 不动系统 (无须管理员)."""
    console.rule("[bold cyan]DoH 速度 + 污染榜[/bold cyan]")
    ipv6_ok = has_ipv6()
    console.print(
        f"IPv6 连通性: {'[green]可用 ✓[/green]' if ipv6_ok else '[dim]不可用[/dim]'}\n"
    )
    with console.status("[cyan]正在对每个 DoH 提供商做 HTTPS 测速 + 污染检测..."):
        results = benchmark_all_doh(DOH_PROVIDERS)
    render_doh_bench(results)


@app.command()
def flush():
    """仅刷新 DNS 缓存."""
    rc, out = flush_dns()
    if rc == 0:
        console.print("[green]✓ DNS 缓存已刷新[/green]")
    else:
        console.print(f"[red]flush 失败:[/red]\n{out}")
        raise typer.Exit(code=rc)


@app.command()
def status():
    """查看当前活动网卡 / NRPT 规则."""
    render_adapter(get_active_adapter())
    console.print()
    render_nrpt_rules(list_rules())


def main() -> None:
    app()


if __name__ == "__main__":
    main()
