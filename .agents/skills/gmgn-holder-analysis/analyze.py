#!/usr/bin/env python3
import json, re, subprocess, sys, time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor

if len(sys.argv) < 3:
    sys.exit('Usage: analyze.py <token_address> <chain|auto> [lang]')
TOKEN_ADDR = sys.argv[1]
CHAIN      = sys.argv[2]
LANG       = sys.argv[3] if len(sys.argv) > 3 else 'zh'
if not (re.fullmatch(r'0x[0-9a-fA-F]{40}', TOKEN_ADDR) or re.fullmatch(r'[1-9A-HJ-NP-Za-km-z]{32,44}', TOKEN_ADDR)):
    sys.exit(f'ERROR: not a valid EVM or Solana address: {TOKEN_ADDR}')

# EVM 地址自动探测链（0x... 且 chain 传入 'auto' 或未明确指定时）
KNOWN_CHAINS = ('bsc', 'eth', 'base', 'sol', 'robinhood', 'arc', 'stable')
if CHAIN == 'auto' or (TOKEN_ADDR.startswith('0x') and CHAIN not in KNOWN_CHAINS):
    for _c in ('bsc', 'eth', 'base'):
        _r = subprocess.run(['gmgn-cli', 'token', 'holders', '--chain', _c,
                             '--address', TOKEN_ADDR, '--limit', '5', '--raw'],
                            capture_output=True, text=True, timeout=15)
        if _r.returncode == 0:
            _data = json.loads(_r.stdout)
            if _data.get('list'):
                CHAIN = _c
                break
    else:
        sys.exit(f'ERROR: no chain found for {TOKEN_ADDR} on bsc/eth/base; pass the chain explicitly')
WINDOW     = 300   # 同步注资滑窗（秒）—— 文档要求"极短时间"，取 5 分钟
TIGHT      = 60    # 秒级同步注资，基本可判定为脚本批量打款
now_ts     = int(time.time())

# 原生代币的包装地址，用于查询实时价格来估算持仓者购买力。
# 未列出的链（arc / stable / robinhood）拿不到价格，购买力改用原生单位展示。
WNATIVE = {
    'sol':  'So11111111111111111111111111111111111111112',
    'bsc':  '0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c',
    'eth':  '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2',
    'base': '0x4200000000000000000000000000000000000006',
}
NATIVE_SYM = {'sol': 'SOL', 'bsc': 'BNB', 'eth': 'ETH', 'base': 'ETH'}

ZH = (LANG == 'zh')
def _(zh, en): return zh if ZH else en

def run_cli(args, timeout=30):
    r = subprocess.run(['gmgn-cli'] + args + ['--raw'],
                       capture_output=True, text=True, timeout=timeout)
    if r.returncode != 0:
        raise RuntimeError(f'gmgn-cli {" ".join(args[:2])} failed: {(r.stderr or r.stdout).strip()}')
    return json.loads(r.stdout)

try:
    with ThreadPoolExecutor(max_workers=4) as ex:
        f_holders = ex.submit(run_cli, ['token', 'holders', '--chain', CHAIN, '--address', TOKEN_ADDR, '--limit', '100'])
        f_devs    = ex.submit(run_cli, ['token', 'holders', '--chain', CHAIN, '--address', TOKEN_ADDR, '--tag', 'dev', '--limit', '20'])
        # 原生代币价格与 holders 无依赖，和上面两个请求并发，不额外增加耗时
        f_price   = (ex.submit(run_cli, ['token', 'info', '--chain', CHAIN, '--address', WNATIVE[CHAIN]])
                     if CHAIN in WNATIVE else None)

        # dev 结果一到，立即发起 created-tokens，不等 holders
        devs = f_devs.result()['list']
        creator = next((d for d in devs if 'creator' in (d.get('maker_token_tags') or [])), None)
        f_created = None
        if creator:
            f_created = ex.submit(run_cli, ['portfolio', 'created-tokens', '--chain', CHAIN,
                                            '--wallet', creator['address'],
                                            '--order-by', 'token_ath_mc', '--direction', 'desc'])

        holders      = f_holders.result()['list']
        created_data = f_created.result() if f_created else None

        # 价格取不到就降级为 None —— 宁可只显示原生数量，也不编造美元金额
        NATIVE_PRICE = None
        if f_price:
            try:
                NATIVE_PRICE = float(((f_price.result() or {}).get('price') or {}).get('price') or 0) or None
            except Exception:
                NATIVE_PRICE = None
except RuntimeError as e:
    sys.exit(f'ERROR: {e}')

normal = sorted((h for h in holders if h.get('addr_type', 0) == 0), key=lambda h: -h['amount_percentage'])
burn   = [h for h in holders if h.get('addr_type', 0) == 1]
dex    = [h for h in holders if h.get('addr_type', 0) == 2]

def pct(v):  return v * 100
def pct_s(v):
    """退化流通盘只有 0.0035% 这种量级，固定两位小数会打成 "0.00%"，读起来就是真零 ——
    而"零"和"极小但非零"在这里是两个不同结论。低于 0.01% 时切成有效数字。"""
    p = pct(v)
    if p <= 0:   return "0%"
    if p < 0.01: return f"{p:.2g}%"
    return f"{p:.2f}%"
def usd(v):
    if v is None: return "$0"
    if abs(v) >= 1_000_000: return f"${v/1_000_000:.2f}M"
    if abs(v) >= 1_000:     return f"${v/1_000:.1f}K"
    return f"${v:.0f}"
def fmt_amt(v):
    if v >= 1_000_000: return f"{v/1_000_000:.1f}M"
    if v >= 1_000:     return f"{v/1_000:.0f}K"
    return f"{v:.0f}"
def addr_short(addr):
    return f"{addr[:4]}...{addr[-4:]}"

supply_list  = [h['balance']/h['amount_percentage'] for h in normal
                if h.get('amount_percentage',0)>0 and h.get('balance',0)>0]
total_supply = sorted(supply_list)[len(supply_list)//2] if supply_list else 1_000_000_000
price_list   = [h['usd_value']/h['balance'] for h in normal
                if h.get('balance',0)>0 and h.get('usd_value',0)>0]
cur_price    = sorted(price_list)[len(price_list)//2] if price_list else 0
cur_mc       = total_supply * cur_price

burn_pct = sum(h['amount_percentage'] for h in burn)
dex_pct  = sum(h['amount_percentage'] for h in dex)

# ── 流通盘基准 ──────────────────────────────────────────────────────────
# 下方所有"持仓占比"都除以 float_share，即以可流通盘为分母而非总供应。
# 理由：报告要回答的是"能砸盘的筹码占多少"，锁在 DEX 池和销毁地址里的份额
# 砸不动，把它们算进分母会把真实抛压系统性稀释（LP 占 56% 时会低估 2.3 倍）。
# burn_pct / dex_pct 本身保持总供应基准 —— 它们定义了流通盘，再用流通盘做分母会循环。
float_raw   = 1.0 - burn_pct - dex_pct
float_share = max(float_raw, 1e-9)

# ── 流通盘退化保护 ──────────────────────────────────────────────────────
# DEX 池（或销毁地址）吃掉几乎全部供应时 float_share 趋零，于是每个 `/ float_share`
# 都把尘埃钱包放大成两位数甚至 100%：实测过一个未迁移的盘，LP 占 99.9%，一个只握着
# 约 $2 代币的钱包被判成"最大单钱包持仓 100%，筹码极度集中"，评级直接给到 🔴 不建议买。
# 那个 100% 是除零噪声，不是集中度。这类币的正确结论是"此刻无法评估筹码结构"。
# 阈值取 2%：低于这个比例，Top100 里任何一个尘埃钱包都能占到"流通盘"的两位数百分比。
FLOAT_MIN        = 0.02
float_degenerate = float_raw < FLOAT_MIN

# ── 空持仓表保护 ────────────────────────────────────────────────────────
# 上游 token holders 会返回 {"list":[]}（币彻底凉了、或索引里已经没有这个盘）。
# 此时每个占比都是 0，dangers/warns 一条都不触发，级联会一路落到"🟢 集中度正常，
# 没发现明显砸盘风险"和"✅ 正常参与"—— 对一份零数据的报告给出正面结论，
# 比不给结论危险得多。"没有数据"必须显式说出来。
no_holders   = len(normal) == 0
unassessable = float_degenerate or no_holders

# 无法评估时百分比一律不上色 —— "0.00% 🔴" 或 "0.0% 🟢" 读起来像结论，其实只是除零/空集
def pf(f): return "⚪" if unassessable else f

# 无法评估时干脆不打印这个占比数字。分母趋零时同一份报告里会同时出现 "hold 100.00%"
# 和 "hold 0.00%"，两个都是除零产物而不是持仓事实。顶部横幅只解释了一次，读者扫到
# "KOL 1 hold 0.00%" 仍然会读成"KOL 没拿货"。钱包个数不经过 float_share，照常打印。
def fpct(v, dec=2): return _("无法评估", "n/a") if unassessable else f"{pct(v):.{dec}f}%"

# ── 流通盘换算只走这两个函数 ─────────────────────────────────────────────
# 不要再手写 `/ float_share`。漏掉一次除法就退回总供应基准，数字看上去仍然合理、
# 也不会报错 —— 正是本次迁移要修掉的那类 bug。集中成两个函数后，漏除法就是漏调用，
# 一眼能看出来。
# fs 故意用下标 h['amount_percentage'] 取字段：字段缺失时直接 KeyError 而不是静默算 0。
def fs(ws): return sum(h['amount_percentage'] for h in ws) / float_share  # 一组钱包的合计占比
def f1(v):  return v / float_share                                        # 单个已取出的占比值

# 集中度只数钱包地址（addr_type==0），排除 DEX 池和销毁地址。
# holders 按 amount_percentage 降序返回，normal 保持该顺序。
top10    = fs(normal[:10])
top20    = fs(normal[:20])

airdrop  = [h for h in normal if h.get('buy_tx_count_cur', 0)==0 and h.get('balance', 0)>0]
bundlers = [h for h in normal if 'bundler'      in (h.get('maker_token_tags') or [])]
rats     = [h for h in normal if 'rat_trader'   in (h.get('maker_token_tags') or [])]
snipers  = [h for h in normal if 'sniper'       in (h.get('maker_token_tags') or [])]
fresh    = [h for h in normal if 'fresh_wallet' in (h.get('tags') or [])]
wash     = [h for h in normal if 'wash_trader'  in (h.get('tags') or [])]

# ── 风险标签的唯一定义处 ────────────────────────────────────────────────
# 去重合计（risk_all）、重叠计数（risk_tag_hits）、§1 的分类明细渲染，三处都从这里派生。
# 之前这五类各自写成三份字面量列表：加第六类标签要改三个地方，漏掉 risk_all 会让
# "合计"少算而明细照常打印，输出自相矛盾且不报错。列表顺序即输出顺序。
RISK_GROUPS = [
    (_("老鼠仓",   "Rat Trader"), rats,     "🚨"),
    (_("捆绑交易", "Bundler"),    bundlers, "⚠️"),
    (_("狙击者",   "Sniper"),     snipers,  "⚠️"),
    (_("新钱包",   "Fresh"),      fresh,    ""),
    (_("刷量",     "Wash"),       wash,     ""),
]
risk_all = set(h['address'] for _lb, g, _fl in RISK_GROUPS for h in g)
risk_pct = fs(h for h in normal if h['address'] in risk_all)

airdrop_pct  = fs(airdrop)
rats_pct     = fs(rats)


# ── 关联资金 ────────────────────────────────────────────────────────────
# 文档要的是"团伙作案"。只看"共用同一个转入地址"会把交易所热钱包判成团伙 ——
# 一个 CEX 热钱包给 30 个互不相关的散户打款，特征和 30 个小号一模一样。
# 硬编码 CEX 地址名单在 skill 里无法维护，改用 payload 里已有的一致性信号：
# 同一批小号通常在很短时间内、以几乎相同的金额被打款。
nonwallet_addrs = set(h['address'] for h in burn) | set(h['address'] for h in dex)

def _tr(h, k, d=0): return (h.get('native_transfer') or {}).get(k, d)

def coherent(ws):
    """时间集中 或 金额高度一致 —— 任一成立即判为强关联"""
    ts    = [t for t in (_tr(w, 'timestamp', 0) for w in ws) if t]
    am    = [float(_tr(w, 'amount', 0) or 0) for w in ws]
    tight = bool(ts) and (max(ts) - min(ts)) <= 6 * 3600
    mean  = (sum(am) / len(am)) if am else 0
    uniform = mean > 0 and (max(am) - min(am)) / mean <= 0.15
    return tight or uniform

from_map = defaultdict(list)
for h in normal:
    fa = _tr(h, 'from_address', '')
    if fa and fa not in nonwallet_addrs:
        from_map[fa].append(h)
# ≥3 个钱包才成组：2 个钱包共用转入地址的证据太弱，噪声远大于信号
_cand = [(fa, ws) for fa, ws in from_map.items() if len(ws) >= 3]
same_src_groups  = sorted([(fa, ws) for fa, ws in _cand if coherent(ws)],     key=lambda x: -len(x[1]))
weak_src_groups  = sorted([(fa, ws) for fa, ws in _cand if not coherent(ws)], key=lambda x: -len(x[1]))
# 丢弃项命名为 _src（来源地址）而不是 __ —— 单下划线 `_` 是本文件的 i18n 函数，
# `__` 看起来像与它相关的东西，容易误读
same_src_wallets = sum(len(ws) for _src, ws in same_src_groups)
weak_src_wallets = sum(len(ws) for _src, ws in weak_src_groups)
same_src_pct     = fs(h for _src, ws in same_src_groups for h in ws)

# 同步注资改用滑动窗口。原先的固定分桶 (ts//WINDOW)*WINDOW 漏掉跨桶边界的相邻注资：
# 两笔相隔 60 秒但落在不同桶里就检测不到。
# key 必须显式取 p[0]：默认的元组比较在 timestamp 相同时会继续比较第二项，
# 也就是拿两个 dict 相比 → TypeError，整个脚本崩掉、一行输出都没有。
# 而"同一秒被批量注资"正是本段要找的信号，时间戳撞车是常态而非边缘情况。
funded     = sorted(((_tr(h, 'timestamp', 0), h) for h in normal if _tr(h, 'timestamp', 0)),
                    key=lambda p: p[0])
win_groups = []
_cur       = []
for ts, h in funded:
    if _cur and ts - _cur[0][0] > WINDOW:
        if len(_cur) >= 2: win_groups.append([x[1] for x in _cur])
        _cur = []
    _cur.append((ts, h))
if len(_cur) >= 2: win_groups.append([x[1] for x in _cur])
win_groups.sort(key=lambda v: -len(v))
win_pct = fs(h for v in win_groups for h in v)

def _span(v):
    ts = [t for t in (_tr(h, 'timestamp', 0) for h in v) if t]
    return (max(ts) - min(ts)) if ts else 0
tight_groups  = [v for v in win_groups if _span(v) <= TIGHT]

related = set()
for _src, ws in same_src_groups:
    for h in ws: related.add(h['address'])
for v in win_groups:
    for h in v: related.add(h['address'])
related_pct = fs(h for h in normal if h['address'] in related)

smart   = [h for h in normal if any(t in (h.get('tags') or []) for t in ['smart_degen','pump_smart'])]
kol     = [h for h in normal if 'kol' in (h.get('tags') or []) or 'renowned' in (h.get('tags') or [])]
whales  = [h for h in normal if 'whale' in (h.get('maker_token_tags') or [])]

# ── 钻石手必须自己买过 ──────────────────────────────────────────────────
# 旧定义只要 sell_tx==0 且 balance>0，于是零成本空降钱包全被算进钻石手：空投分发的币
# 会同时打印"空降筹码 79% 🔴"和"钻石手持仓 80% ✅ 筹码稳定"，同一批钱包被数了两次、
# 结论还相反。"钻石手"的含义是扛住了浮亏没卖 —— 没花钱买入的地址无所谓扛，
# 它不卖可能只是私钥在分发方手里。所以要求 buy_tx>0。
# 空降且未动的那批不丢弃，单独列成 idle_airdrop：它们仍是随时可能出货的零成本筹码。
diamond      = [h for h in normal if (h.get('buy_tx_count_cur') or 0)>0
                                 and (h.get('sell_tx_count_cur') or 0)==0
                                 and (h.get('balance') or 0)>0]
idle_airdrop = [h for h in normal if (h.get('buy_tx_count_cur') or 0)==0
                                 and (h.get('sell_tx_count_cur') or 0)==0
                                 and (h.get('balance') or 0)>0]

smart_pct        = fs(smart)
kol_pct          = fs(kol)
whale_pct        = fs(whales)
diamond_pct      = fs(diamond)
idle_airdrop_pct = fs(idle_airdrop)


top100_map   = {h['address']: h for h in holders}
sub_devs     = [d for d in devs if 'creator' not in (d.get('maker_token_tags') or [])]
dev_realized = sum(d.get('realized_profit') or 0 for d in devs)
dev_holding  = [d for d in devs if (d.get('balance') or 0)>=1]

durations     = [now_ts-h['start_holding_at'] for h in normal
                 if (h.get('start_holding_at') or 0)>0 and now_ts>h['start_holding_at']]
avg_hold_days = (sum(durations)/len(durations)/86400) if durations else 0


# 只列已确认精度的链。arc / stable / robinhood 的原生精度未确认，套 1e18 会把余额
# 算成 0.000，读起来像"这些钱包没有 gas"—— 错的数字比没有数字更危险。
NATIVE_DENOM = {'sol': 1e9, 'bsc': 1e18, 'eth': 1e18, 'base': 1e18}.get(CHAIN)
NSYM         = NATIVE_SYM.get(CHAIN, 'NATIVE')
HAS_NATIVE   = NATIVE_DENOM is not None
HAS_PRICE    = HAS_NATIVE and NATIVE_PRICE is not None
def native_amt(h):
    if not HAS_NATIVE: return 0.0
    try:    return float(h.get('native_balance') or 0) / NATIVE_DENOM
    except (TypeError, ValueError): return 0.0
def native_usd(h): return native_amt(h) * NATIVE_PRICE if HAS_PRICE else 0.0
def fmt_native(v): return f"{v:.3f} {NSYM}"

if not HAS_NATIVE:
    # 精度未知，native_balance 无法换算 —— 一个钱包都不归档，整节改为"无法评估"
    zero_wallets, low_wallets, mid_wallets, high_wallets = [], [], [], []
elif HAS_PRICE:
    zero_wallets = [h for h in normal if native_amt(h) <= 0]
    low_wallets  = [h for h in normal if 0 < native_usd(h) <= 200]
    mid_wallets  = [h for h in normal if 200 < native_usd(h) <= 1200]
    high_wallets = [h for h in normal if native_usd(h) > 1200]
else:
    # 拿不到原生代币价格就不虚构美元档位，只分"零余额 / 有余额"
    zero_wallets = [h for h in normal if native_amt(h) <= 0]
    low_wallets, mid_wallets = [], []
    high_wallets = [h for h in normal if native_amt(h) > 0]
zero_pct_val = fs(zero_wallets)
low_pct_val  = fs(low_wallets)
mid_pct_val  = fs(mid_wallets)
high_pct_val = fs(high_wallets)
high_total   = sum(native_usd(h) for h in high_wallets)
high_native  = sum(native_amt(h) for h in high_wallets)

ROLE_MAP = {
    'rat_trader':   _('老鼠仓', 'Rat Trader'),
    'sniper':       _('狙击',   'Sniper'),
    'bundler':      _('捆绑',   'Bundler'),
    'whale':        _('鲸鱼',   'Whale'),
    'smart_degen':  _('聪明钱', 'Smart'),
    'pump_smart':   _('聪明钱', 'Smart'),
    'renowned':     'KOL',
    'kol':          'KOL',
    'fresh_wallet': _('新钱包', 'Fresh'),
    'wash_trader':  _('刷量',   'Wash'),
    'creator':      'Dev',
    'dev_team':     'Dev',
}
def wallet_roles(h):
    roles = []
    for t in (h.get('maker_token_tags') or [])+(h.get('tags') or []):
        if t in ROLE_MAP: roles.append(ROLE_MAP[t])
    return list(dict.fromkeys(roles))




def trend_str(wlist):
    """文档问的是"持续加仓中还是出货中"。按累计买卖笔数分桶会把绝大多数活跃钱包
    归进"买卖都有"，两个分支都答不上。改用 sell_amount_percentage（已卖出量占已买入量
    的比例）判净方向 —— 和 holding_status 用的是同一个字段。"""
    cleared, dumping, trimming, adding, holding, idle = [], [], [], [], [], []
    for h in wlist:
        sp  = h.get('sell_amount_percentage') or 0
        buy = h.get('buy_tx_count_cur') or 0
        sell = h.get('sell_tx_count_cur') or 0
        if buy == 0 and sell == 0: idle.append(h)      # 转账获得，链上无交易
        elif sp >= 0.8:  cleared.append(h)
        elif sp >= 0.3:  dumping.append(h)
        elif sp > 0:     trimming.append(h)
        elif buy >= 2:   adding.append(h)              # 多次买入且未卖出
        else:            holding.append(h)
    parts = []
    if adding:   parts.append(f"📈 {_('加仓中', 'Accumulating')} {len(adding)}")
    if holding:  parts.append(f"🤝 {_('持仓未动', 'Holding')} {len(holding)}")
    if trimming: parts.append(f"🟡 {_('少量减持', 'Trimming')} {len(trimming)}")
    if dumping:  parts.append(f"📉 {_('出货中', 'Distributing')} {len(dumping)}")
    if cleared:  parts.append(f"🔴 {_('清仓中', 'Exiting')} {len(cleared)}")
    if idle:     parts.append(f"⚪ {_('无交易', 'Idle')} {len(idle)}")
    return "  ".join(parts) if parts else "—"

def is_selling(h):     return (h.get('sell_tx_count_cur') or 0)>0 and (h.get('balance') or 0)>=1
def is_buying_only(h): return (h.get('buy_tx_count_cur') or 0)>0 and (h.get('sell_tx_count_cur') or 0)==0

biggest     = max(normal, key=lambda h: h['amount_percentage']) if normal else None
biggest_pct = f1(biggest['amount_percentage']) if biggest else 0
# 以下所有阈值都已按流通盘基准重新校准（旧值是总供应基准，直接沿用会让每条都亮红）
# 流通盘退化时这些阈值判的全是除零噪声（详见 float_degenerate），一条都不能计入评级 ——
# 不依赖百分比的判据（Dev 马甲）不受影响，照常检查。
dangers = []
if not float_degenerate:
    if rats and rats_pct > 0.05:
        dangers.append(_( f"老鼠仓持仓 {pct(rats_pct):.1f}%，出货即砸盘",
                          f"Rat traders hold {pct(rats_pct):.1f}% — instant dump risk"))
    if biggest_pct > 0.10:
        dangers.append(_( f"最大单钱包持仓 {pct(biggest_pct):.1f}%，筹码极度集中",
                          f"Largest wallet holds {pct(biggest_pct):.1f}% — extreme concentration"))
if creator:
    to_out = creator.get('token_transfer_out') or {}
    if (to_out.get('address') or '') in top100_map:
        dangers.append(_("Dev 筹码转给内部马甲，换手控盘",
                         "Dev transferred chips to internal wallet — covert control"))

warns = []
if no_holders:
    warns.append(_( "上游未返回任何持仓地址，筹码结构无法评估（本报告所有占比均为空集，不是 0%）",
                    "Upstream returned no holder addresses — chip structure not assessable (every percentage here is an empty set, not a real 0%)"))
elif float_degenerate:
    # 唯一还成立的结论就是"这盘子还没放开，没法评"。给出的是绝对值而不是百分比。
    warns.append(_( f"流通盘仅占总供应 {pct_s(float_raw)}（DEX {pct(dex_pct):.1f}% + 销毁 {pct(burn_pct):.1f}%），筹码结构无法评估",
                    f"Float is only {pct_s(float_raw)} of supply (DEX {pct(dex_pct):.1f}% + burn {pct(burn_pct):.1f}%) — chip structure not assessable"))
else:
    if dev_holding:
        # dev 来自另一个 endpoint，字段可能缺失，所以先用 .get 求和再交给 f1 换算，
        # 不走 fs（fs 用下标取字段）
        hold_pct_val = f1(sum(d.get('amount_percentage',0) for d in dev_holding))
        if hold_pct_val > 0.01:
            warns.append(_( f"Dev 仍持仓 {pct(hold_pct_val):.2f}%",
                            f"Dev still holds {pct(hold_pct_val):.2f}%"))
    if airdrop_pct > 0.2:
        warns.append(_( f"空降筹码 {pct(airdrop_pct):.1f}%，来源不透明",
                        f"Airdrop supply {pct(airdrop_pct):.1f}% — opaque origin"))
    if risk_pct > 0.35:
        warns.append(_( f"风险钱包持仓 {pct(risk_pct):.1f}%，筹码质量差",
                        f"Risk wallets hold {pct(risk_pct):.1f}% — low chip quality"))
    if related_pct > 0.15:
        warns.append(_( f"关联钱包 {len(related)} 个持仓 {pct(related_pct):.1f}%",
                        f"Linked wallets ({len(related)}) hold {pct(related_pct):.1f}%"))

if unassessable and not dangers:
    # Dev 马甲那条（唯一不依赖百分比的 danger）若成立就照常给 🔴；否则不下结论。
    # 退化 / 空数据时"没发现问题"和"评级正常"是两件事，不能让它落到 ✅ 正常参与。
    rating_em, rating_text = "⚪", _("无法评估", "Cannot Assess")
elif dangers:
    rating_em, rating_text = "🔴", _("不建议买", "Not Recommended")
elif len(warns) >= 2:
    rating_em, rating_text = "⚠️", _("谨慎参与", "Caution")
elif len(warns) == 1:
    rating_em, rating_text = "🟡", _("可轻仓",   "Light Position")
else:
    rating_em, rating_text = "✅", _("正常参与", "Normal")

goods = []
if burn_pct > 0.05:
    goods.append(_( f"销毁 {pct(burn_pct):.1f}% 永久锁仓，流通减少",
                    f"Burned {pct(burn_pct):.1f}% permanently — reduced supply"))
if whales:
    buying_w = [h for h in whales if is_buying_only(h)]
    if buying_w:
        goods.append(_( f"鲸鱼 {len(buying_w)} 个持续买入，尚未出货",
                        f"{len(buying_w)} whale(s) still accumulating, not sold"))
if kol:
    # 钱包个数是实打实的；退化时占比是噪声，就只报个数
    goods.append(_( f"KOL {len(kol)} 个在场" + ("" if float_degenerate else f"（{pct(kol_pct):.2f}%）"),
                    f"{len(kol)} KOL(s) holding" + ("" if float_degenerate else f" ({pct(kol_pct):.2f}%)")))
if diamond_pct > 0.5 and not float_degenerate:
    goods.append(_( f"钻石手持仓 {pct(diamond_pct):.1f}%，筹码稳定",
                    f"Diamond hands hold {pct(diamond_pct):.1f}% — stable chips"))

exit_signals = []
if rats:
    exit_signals.append(_("老鼠仓钱包出现卖出操作", "Rat trader wallets start selling"))
if dev_holding:
    exit_signals.append(_("Dev 钱包开始出货", "Dev wallets start dumping"))
if airdrop_pct>0.2:
    exit_signals.append(_("空降大户出现集中卖出", "Airdrop whales start concentrated selling"))
if not exit_signals:
    exit_signals = [_("Top5 大户出现集中出货", "Top 5 holders start concentrated selling"),
                    _("价格跌破建仓均价支撑", "Price breaks below average entry cost")]
exit_signals = exit_signals[:3]

top5_holders = sorted(normal, key=lambda h: -h['amount_percentage'])[:5]


title = _("Holder 筹码分析", "Holder Chip Analysis")
print(f"┌{'─'*56}┐")
print(f"│{('  '+title):^56}│")
print(f"│{('  '+TOKEN_ADDR[:10]+'...'+TOKEN_ADDR[-4:]+'  ·  Top100  ·  '+CHAIN.upper()):^56}│")
print(f"│{('  MC '+usd(cur_mc)):^56}│")
print(f"└{'─'*56}┘")
print()

if no_holders:
    print(f"  ⚠️  {_('上游未返回任何持仓地址 —— 筹码结构无法评估', 'Upstream returned no holder addresses — chip structure not assessable')}")
    print(_( "      下方所有占比与计数都是空集的渲染结果，不是“该项为 0”；评级已置为“无法评估”。",
             "      Every percentage and count below renders an empty set, not a measured zero. Rating is set to \"Cannot Assess\"."))
    print(_( "      常见原因：代币已无活跃持仓、或上游索引里已不再收录该盘。可稍后重试确认。",
             "      Usual causes: the token has no active holders left, or upstream no longer indexes it. Retry later to confirm."))
    print()

if float_degenerate:
    _fl_tok   = total_supply * max(float_raw, 0)
    _fl_usd   = _fl_tok * cur_price
    _fl_usd_s = "<$1" if 0 < _fl_usd < 1 else usd(_fl_usd)
    print(f"  ⚠️  {_('流通盘退化 —— 筹码结构此刻无法评估', 'Degenerate float — chip structure not assessable right now')}")
    print(_( f"      DEX 池 {pct(dex_pct):.1f}% + 销毁 {pct(burn_pct):.1f}% 占掉几乎全部供应，可流通部分只剩 {pct_s(float_raw)}",
             f"      DEX {pct(dex_pct):.1f}% + burn {pct(burn_pct):.1f}% hold nearly all supply; only {pct_s(float_raw)} is tradeable"))
    print(_( f"      （通常是还没迁移的 launchpad 盘）实际可流通约 {fmt_amt(_fl_tok)} 个代币 ≈ {_fl_usd_s}",
             f"      (typically a launchpad token pre-migration) tradeable ≈ {fmt_amt(_fl_tok)} tokens ≈ {_fl_usd_s}"))
    print(_( "      下方“占流通盘”的百分比分母趋零，会把尘埃钱包放大成两位数甚至 100%，",
             "      Float percentages below divide by a near-zero denominator, inflating dust wallets to double digits or 100%,"))
    print(_( "      不能当作集中度结论；评级已置为“无法评估”，颜色标记一律显示 ⚪。",
             "      so they are not concentration findings. Rating is set to \"Cannot Assess\" and flags show ⚪."))
    print()

# ══════════════════════════════════════════════════════════
# §1  🚨 砸盘风险
# ══════════════════════════════════════════════════════════
sec1 = _("🚨 砸盘风险", "🚨 Dump Risk")
print(f"━━  {sec1}  {'━'*(54-len(sec1))}")
print()

c10f = pf("🔴" if top10>0.6 else ("🟡" if top10>0.4 else "🟢"))
c20f = pf("🔴" if top20>0.75 else ("🟡" if top20>0.55 else "🟢"))
print(f"  Top10 {fpct(top10, 1)} {c10f} · Top20 {fpct(top20, 1)} {c20f} · {_('平均持仓', 'Avg hold')} {avg_hold_days:.1f}{_('天', 'd')}")

airf  = pf("🔴" if airdrop_pct>0.25 else ("🟡" if airdrop_pct>0.1 else "🟢"))
riskf = pf("🔴" if risk_pct>0.35 else ("🟡" if risk_pct>0.15 else "🟢"))
print(f"  {_('转入筹码', 'Airdrop')} {len(airdrop)}{_('个', '')}({fpct(airdrop_pct)}) {airf} · {_('风险钱包', 'Risk')} {len(risk_all)}{_('个', '')}({fpct(risk_pct)}) {riskf}")

any_risk = any(g for _lb, g, _fl in RISK_GROUPS)
if any_risk:
    for label, group, flag in RISK_GROUPS:
        if group:
            gp = fpct(fs(group))
            print(f"    · {label} {len(group)}{_('个', '')}({gp}) {flag}")
elif not no_holders:
    print(f"    ✅ {_('未发现风险标签钱包', 'No risk-tagged wallets found')}")
print()

# Top5 出货风险
top5_airdrop_n = sum(1 for h in top5_holders if h.get('buy_tx_count_cur', 0) == 0)
top5_trapped_n = sum(1 for h in top5_holders
                     if (h.get('unrealized_pnl') or 0) < -0.1 and (h.get('buy_tx_count_cur') or 0) > 0)
top5_profit_n  = sum(1 for h in top5_holders
                     if (h.get('unrealized_pnl') or 0) > 0.1 and (h.get('buy_tx_count_cur') or 0) > 0)
top5_selling_n = sum(1 for h in top5_holders if is_selling(h))

top5_parts = []
if top5_airdrop_n: top5_parts.append(f"{_('转入筹码', 'Airdrop')}×{top5_airdrop_n}")
if top5_trapped_n: top5_parts.append(f"{_('套牢', 'Trapped')}×{top5_trapped_n}")
if top5_profit_n:  top5_parts.append(f"{_('浮盈', 'Profit')}×{top5_profit_n}")
if top5_selling_n: top5_parts.append(f"{top5_selling_n}{_('人出货中', ' selling')}")
top5_label   = _("Top5 出货风险", "Top5 Sell Risk")
top5_summary = "  ".join(top5_parts) if top5_parts else _("暂无明显出货压力", "No obvious sell pressure")
print(f"  {top5_label}  {top5_summary}")

# 单个最危险钱包（优先级：零成本最大 > 高浮盈最大 > 出货最大）
danger_wallet  = None
danger_reason  = ""
zero_cost_top5 = [h for h in top5_holders if h.get('buy_tx_count_cur', 0) == 0]
if zero_cost_top5:
    danger_wallet = max(zero_cost_top5, key=lambda h: h['amount_percentage'])
    danger_reason = _("零成本转入，可随时出货", "Zero-cost airdrop — can dump anytime")
if not danger_wallet:
    high_profit_top5 = [h for h in top5_holders
                        if (h.get('unrealized_pnl') or 0) > 1.0 and (h.get('buy_tx_count_cur') or 0) > 0]
    if high_profit_top5:
        danger_wallet = max(high_profit_top5, key=lambda h: h['amount_percentage'])
        mult          = (danger_wallet.get('unrealized_pnl') or 0) + 1
        danger_reason = _(f"浮盈 {mult:.1f}x，已获利了结压力强", f"{mult:.1f}x gain — strong take-profit pressure")
if not danger_wallet:
    selling_top5 = [h for h in top5_holders if is_selling(h)]
    if selling_top5:
        danger_wallet = max(selling_top5, key=lambda h: h['amount_percentage'])
        sp            = (danger_wallet.get('sell_amount_percentage') or 0)
        danger_reason = _(f"出货中（已卖 {pct(sp):.0f}%）", f"Selling ({pct(sp):.0f}% sold)")

if danger_wallet:
    roles    = wallet_roles(danger_wallet)
    role_tag = "[" + "·".join(roles) + "] " if roles else ""
    dname    = (danger_wallet.get('twitter_name') or '') or addr_short(danger_wallet['address'])
    dhp      = fpct(f1(danger_wallet['amount_percentage']))
    print(f"  ⚠️ {role_tag}{dname}  {dhp}  {danger_reason}")
print()

# ══════════════════════════════════════════════════════════
# §2  👨‍💻 Dev
# ══════════════════════════════════════════════════════════
sec2 = _("👨‍💻 Dev", "👨‍💻 Dev")
print(f"━━  {sec2}  {'━'*(54-len(sec2))}")
print()

if not devs:
    print(f"  {_('— 未查到 Dev 钱包', '— no dev wallets found')}")
elif not creator:
    print(f"  {_('— 未找到 Creator 信息', '— creator wallet not found')}")
else:
    c_bal   = creator.get('balance') or 0
    c_pct   = f1(creator.get('amount_percentage') or 0)
    to_out  = creator.get('token_transfer_out') or {}
    to_addr = to_out.get('address') or ''
    sock    = bool(to_addr and to_addr in top100_map)

    sub_holding     = [d for d in sub_devs if (d.get('balance') or 0) >= 1]
    sub_holding_pct = f1(sum(d.get('amount_percentage', 0) for d in sub_holding))

    if sock:
        dev_line = f"🔴 {_('筹码已转至内部马甲，换手控盘', 'Chips routed to internal puppet — covert control')}"
    elif c_bal >= 1:
        if sub_holding:
            dev_line = (f"⚠️ {_('持仓', 'Holding')} {fpct(c_pct)}"
                        f"（{_('含', 'incl.')} {len(sub_holding)}{_('个小号', ' sub-wallets')}）")
        else:
            dev_line = f"⚠️ {_('持仓', 'Holding')} {fpct(c_pct)}"
    else:
        if sub_holding:
            dev_line = (f"⚠️ {_('主号已清仓', 'Main cleared')}，"
                        f"{len(sub_holding)}{_('个关联小号持仓', ' sub-wallet(s) holding')} {fpct(sub_holding_pct)}")
        else:
            dev_line = f"✅ {_('已清仓', 'Cleared')}"
    print(f"  {dev_line}")

    if sock:
        target  = top100_map[to_addr]
        t_mtags = [t for t in (target.get('maker_token_tags') or []) if t not in ('top_holder', 'transfer_in')]
        sock_hp = fpct(f1(target.get('amount_percentage') or 0))
        print(f"    ↳ {_('马甲', 'Puppet')} {addr_short(to_addr)}  {_('持仓', 'hold')} {sock_hp}"
              f"  {_('标签', 'tags')}: {' '.join(t_mtags) or _('无', 'none')}")

    hist_str = ""
    if created_data:
        total_cnt = (created_data.get('inner_count') or 0) + (created_data.get('open_count') or 0)
        mig_cnt   = created_data.get('open_count') or 0
        hist_str  = (f" · {_('历史发币', 'Token history')} {total_cnt}{_('个', '')}，"
                     f"{_('成功迁移', 'migrated')} {mig_cnt}{_('个', '')}")
    print(f"  {_('已获利', 'Realized')} {usd(dev_realized)}{hist_str}")

    if created_data:
        ath_info = created_data.get('creator_ath_info') or {}
        if ath_info and ath_info.get('ath_mc'):
            ath_mc    = float(ath_info.get('ath_mc') or 0)
            is_curr   = ath_info.get('ath_token', '').lower() == TOKEN_ADDR.lower()
            curr_tag  = _('（本币）', ' (this)') if is_curr else ''
            stale     = ath_mc > 0 and cur_mc > 0 and ath_mc < cur_mc * 0.95
            stale_tag = (_(f"  ⚠️ ATH可能滞后（低于当前MC {usd(cur_mc)}）",
                           f"  ⚠️ ATH may be stale (below current MC {usd(cur_mc)})") if stale else "")
            print(f"  ↳ {_('历史最高市值', 'All-time high MC')}: {ath_info.get('token_symbol', '?')}{curr_tag} {usd(ath_mc)}{stale_tag}")
print()

# ══════════════════════════════════════════════════════════
# §3  🔗 关联资金
# ══════════════════════════════════════════════════════════
sec3 = _("🔗 关联资金", "🔗 Related Funds")
print(f"━━  {sec3}  {'━'*(54-len(sec3))}")
print()

has_related = bool(same_src_groups or win_groups)
if has_related:
    if same_src_groups:
        relf_src = pf("🔴" if same_src_pct>0.25 else ("🟡" if same_src_pct>0.1 else "🟢"))
        print(f"  {_('相同资金来源', 'Same source'):10s}  {same_src_wallets}{_('个钱包', ' wallets')}  "
              f"{_('持仓', 'hold')} {fpct(same_src_pct)} {relf_src}")
    else:
        print(f"  {_('相同资金来源', 'Same source'):10s}  {_('✅ 未发现', '✅ None detected')}")
    if win_groups:
        win_n    = sum(len(v) for v in win_groups)
        relf_win = pf("🔴" if win_pct>0.25 else ("🟡" if win_pct>0.1 else "🟢"))
        if tight_groups and relf_win in ("🟢", "⚪"): relf_win = pf("🟡")
        tight_note = f"  {_('（含秒级批量注资）', '(incl. scripted batch)')}" if tight_groups else ""
        print(f"  {_('同一时间段注资', 'Same-window'):10s}  {win_n}{_('个钱包', ' wallets')}  "
              f"{_('持仓', 'hold')} {fpct(win_pct)} {relf_win}{tight_note}")
    else:
        print(f"  {_('同一时间段注资', 'Same-window'):10s}  {_('✅ 未发现', '✅ None detected')}")
else:
    if no_holders:
        print(f"  ⚪ {_('没有钱包可供检查', 'No wallets available to check')}")
    else:
        print(f"  ✅ {_('未发现同源/同期资金，筹码来源分散', 'No linked funds — dispersed origins')}")
    if weak_src_groups:
        print(f"  ({_(f'{weak_src_wallets} 个钱包共用转入地址，时间金额不一致，判为交易所出金',f'{weak_src_wallets} wallets share a source but differ in timing/amount — likely CEX withdrawals')})")
print()

# ══════════════════════════════════════════════════════════
# §4  🧠 优质信号
# ══════════════════════════════════════════════════════════
sec4 = _("🧠 优质信号", "🧠 Quality Signals")
print(f"━━  {sec4}  {'━'*(54-len(sec4))}")
print()

if not smart and not kol and not whales:
    print(f"  {_('聪明钱/KOL/鲸鱼 均无', 'No smart money / KOL / whale found')}")
else:
    if smart:
        s_trend = trend_str(smart)
        print(f"  {_('聪明钱', 'Smart')} {len(smart)}{_('个', '')}({fpct(smart_pct)})  {s_trend}")
    if kol:
        k_trend = trend_str(kol)
        print(f"  KOL {len(kol)}{_('个', '')}({fpct(kol_pct)})  {k_trend}")
    if whales:
        w_trend = trend_str(whales)
        print(f"  {_('鲸鱼', 'Whale')} {len(whales)}{_('个', '')}({fpct(whale_pct)})  {w_trend}")

if diamond:
    df = pf("✅" if diamond_pct>0.6 else ("🟡" if diamond_pct>0.35 else "⚠️"))
    print(f"  {_('钻石手', 'Diamond')} {len(diamond)}{_('个', '')}({fpct(diamond_pct, 1)}) {df}")
if idle_airdrop:
    print(f"  {_('转入筹码未动', 'Idle airdrop')} {len(idle_airdrop)}{_('个', '')}({fpct(idle_airdrop_pct, 1)})"
          f"  {_('零成本，未计入钻石手', 'zero cost, not counted as diamond')}")
print()

# ══════════════════════════════════════════════════════════
# §5  💰 持仓购买力
# ══════════════════════════════════════════════════════════
sec5 = _("💰 持仓购买力", "💰 Buying Power")
print(f"━━  {sec5}  {'━'*(54-len(sec5))}")
print()

if not HAS_NATIVE:
    print(f"  ⚠️  {_(f'{CHAIN} 链原生代币精度未确认，购买力无法评估', f'Native decimals unconfirmed for {CHAIN} — not assessed')}")
else:
    if high_wallets:
        if HAS_PRICE:
            print(f"  {_('高余额大户', 'High balance')}  {len(high_wallets)}{_('个', '')}({fpct(high_pct_val, 1)})  "
                  f"{_('可用', 'avail.')} {usd(high_total)}")
        else:
            print(f"  {_('高余额大户', 'High balance')}  {len(high_wallets)}{_('个', '')}({fpct(high_pct_val, 1)})  "
                  f"{fmt_native(high_native)}")
    else:
        print(f"  {_('高余额大户', 'High balance')}  {_('0个（暂无强加仓力量）', '0 (no strong buying power)')}")
    lz_n     = len(zero_wallets) + len(low_wallets) + len(mid_wallets)
    lz_pct_v = zero_pct_val + low_pct_val + mid_pct_val
    if lz_n > 0:
        print(f"  {_('低/零余额', 'Low/zero')}   {lz_n}{_('个', '')}({fpct(lz_pct_v, 1)})  "
              f"{_('基本无加仓能力', 'Limited buying power')}")
print()

# ══════════════════════════════════════════════════════════
# §6  🤖 建议
# ══════════════════════════════════════════════════════════
sec6 = _("🤖 建议", "🤖 Advice")
print(f"━━  {sec6}  {'━'*(54-len(sec6))}")
print()

print(f"  {rating_em} {rating_text}")
print()

if dangers:
    core = _("⚠️ 高风险：", "⚠️ High risk: ") + dangers[0]
elif warns:
    core = warns[0]
elif goods:
    core = goods[0]
elif unassessable:
    core = _("当前无法判断筹码质量，建议稍后重试", "Cannot assess chip quality right now — retry later")
else:
    core = _("筹码结构正常，未发现明显风险信号", "Chip structure normal — no obvious risk signals")
print(f"  {core}")
print()

print(f"  💡 {_('离场信号：', 'Exit signals: ')}{' / '.join(exit_signals)}")
print()

print("=" * 58)
print("  [OUTPUT COMPLETE — COPY ABOVE VERBATIM, DO NOT SUMMARIZE]")
print("=" * 58)
