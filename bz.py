#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bz.py — 八字流时 / 刑冲合会 计算内核 (复古框线盘面)。无解读、无装饰。
  定柱(立春分年·节令分月)交给 lunar-python；其余按子平规则本程序计算。
依赖:  pip install lunar_python
用法:  bz.py 出生 [--sex 男|女] [--at 时刻] [--lon 经度E] [--tz 8]
"""
import argparse, math, sys
from datetime import datetime, timedelta

GAN = '甲乙丙丁戊己庚辛壬癸'
ZHI = '子丑寅卯辰巳午未申酉戌亥'
GAN_WX = dict(zip(GAN, '木木火火土土金金水水'))
GAN_YIN = set('乙丁己辛癸')
SHENG = {'木':'火','火':'土','土':'金','金':'水','水':'木'}
KE    = {'木':'土','土':'水','水':'火','火':'金','金':'木'}
ZHI_HIDE = {'子':'癸','丑':'己癸辛','寅':'甲丙戊','卯':'乙','辰':'戊乙癸','巳':'丙庚戊',
            '午':'丁己','未':'己乙丁','申':'庚壬戊','酉':'辛','戌':'戊辛丁','亥':'壬甲'}
CHONG = [set(p) for p in ('子午','丑未','寅申','卯酉','辰戌','巳亥')]
LIUHE = {frozenset('子丑'):'土',frozenset('寅亥'):'木',frozenset('卯戌'):'火',
         frozenset('辰酉'):'金',frozenset('巳申'):'水',frozenset('午未'):'土'}
HAI   = [set(p) for p in ('子未','丑午','寅巳','卯辰','申亥','酉戌')]
PO    = [set(p) for p in ('子酉','午卯','辰丑','戌未','寅亥','巳申')]
BANHE = {frozenset('申子'):'水',frozenset('子辰'):'水',frozenset('亥卯'):'木',frozenset('卯未'):'木',
         frozenset('寅午'):'火',frozenset('午戌'):'火',frozenset('巳酉'):'金',frozenset('酉丑'):'金'}
SANHE = {'申子辰':'水','亥卯未':'木','寅午戌':'火','巳酉丑':'金'}
SANHUI= {'寅卯辰':'木','巳午未':'火','申酉戌':'金','亥子丑':'水'}
XING3 = {'寅巳申':'无恩','丑戌未':'恃势'}
XING_PAIR = [set('子卯')] + [set(p) for p in ('寅巳','巳申','丑戌','戌未')]
ZIXING = set('辰午酉亥')
TG_HE = {frozenset('甲己'):'土',frozenset('乙庚'):'金',frozenset('丙辛'):'水',
         frozenset('丁壬'):'木',frozenset('戊癸'):'火'}
TG_CHONG = [set(p) for p in ('甲庚','乙辛','丙壬','丁癸')]

def ten_god(dm, g):
    we, wx = GAN_WX[dm], GAN_WX[g]
    same = (dm in GAN_YIN) == (g in GAN_YIN)
    if wx == we:        return '比肩' if same else '劫财'
    if SHENG[we] == wx: return '食神' if same else '伤官'
    if KE[we] == wx:    return '偏财' if same else '正财'
    if KE[wx] == we:    return '七杀' if same else '正官'
    return                 '偏印' if same else '正印'

def pair_rel(a, b):
    s = {a, b}; fs = frozenset(s); out = []
    if a != b:
        if s in CHONG: out.append('冲')
        if fs in LIUHE: out.append('合·'+LIUHE[fs])
        if fs in BANHE: out.append('半合·'+BANHE[fs])
        if s in HAI: out.append('害')
        if s in PO: out.append('破')
        if any(s == p for p in XING_PAIR): out.append('刑')
    elif a in ZIXING:
        out.append('自刑')
    return out

def glyph(rels):
    o = ''
    for r in rels:
        o += '半' if r.startswith('半') else '合' if r.startswith('合') else \
             {'冲':'冲','害':'害','破':'破','刑':'刑','自刑':'自'}[r]
    return o

def xunkong(gz):
    g, z = GAN.index(gz[0]), ZHI.index(gz[1])
    s = (z - g) % 12
    return ZHI[(s+10) % 12] + ZHI[(s+11) % 12]

def gz_index(gz):
    for i in range(60):
        if GAN[i % 10] == gz[0] and ZHI[i % 12] == gz[1]: return i
    raise ValueError(gz)

def dayun_gz(month_gz, step, fwd):
    i = (gz_index(month_gz) + (step if fwd else -step)) % 60
    return GAN[i % 10] + ZHI[i % 12]

def eot_minutes(dt):
    n = dt.timetuple().tm_yday; b = 2*math.pi*(n-81)/364
    return 9.87*math.sin(2*b) - 7.53*math.cos(b) - 1.5*math.sin(b)

def true_solar(dt, lon, tz):
    d = (lon - 15.0*tz)*4 + eot_minutes(dt)
    return dt + timedelta(minutes=d), d

try:
    from lunar_python import Solar
except ImportError:
    sys.exit("缺少依赖：pip install lunar_python")

def pillars(dt):
    ec = Solar.fromYmdHms(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second).getLunar().getEightChar()
    return ec.getYear(), ec.getMonth(), ec.getDay(), ec.getTime()

def _sol_dt(s): return datetime(s.getYear(), s.getMonth(), s.getDay(), s.getHour(), s.getMinute(), s.getSecond())
JIE = {'立春','惊蛰','清明','立夏','芒种','小暑','立秋','白露','寒露','立冬','大雪','小寒'}
def jie_times(dt):
    ts = set()
    for yr in (dt.year-1, dt.year, dt.year+1):
        for name, sol in Solar.fromYmdHms(yr,6,1,12,0,0).getLunar().getJieQiTable().items():
            if name in JIE: ts.add(_sol_dt(sol))
    return sorted(ts)

# ───────── 框线渲染 (按汉字双宽对齐) ─────────
def dw(s): return sum(2 if ord(c) > 0x2E80 else 1 for c in s)
def cp(s, w, a='c'):
    p = w - dw(s)
    if p <= 0: return s
    if a == 'l': return ' ' + s + ' '*(p-1)
    if a == 'r': return ' '*(p-1) + s + ' '
    l = p//2; return ' '*l + s + ' '*(p-l)
def rule(ws, l, m, r): return l + m.join('─'*w for w in ws) + r
def trow(cells, ws, al=None):
    return '│' + '│'.join(cp(c, ws[i], (al[i] if al else 'c')) for i, c in enumerate(cells)) + '│'
def grid(header, rows, ws, al=None):
    out = [rule(ws, '┌', '┬', '┐'), trow(header, ws), rule(ws, '├', '┼', '┤')]
    out += [trow(r, ws, al) for r in rows]
    out.append(rule(ws, '└', '┴', '┘'))
    return out
def banner(lines, w):
    out = ['╔' + '═'*w + '╗']
    out += ['║' + cp(t, w, 'l') + '║' for t in lines]
    out.append('╚' + '═'*w + '╝')
    return out

def col_block(labels, gzs, dm, w=12):
    """命盘/流盘网格: 标签列 + 各柱(主星/天干/地支/藏干副星×3)。"""
    ws = [6] + [w]*len(gzs)
    hdr = [''] + list(labels)
    hides = [[h + ' ' + ten_god(dm, h) for h in ZHI_HIDE[gz[1]]] for gz in gzs]
    h = max(len(x) for x in hides)
    rows = []
    rows.append(['主星'] + [('日主' if lb == '日' else ten_god(dm, gz[0])) for lb, gz in zip(labels, gzs)])
    rows.append(['天干'] + [gz[0] for gz in gzs])
    rows.append(['地支'] + [gz[1] for gz in gzs])
    for k in range(h):
        rows.append([('藏干' if k == 0 else '')] + [(hd[k] if k < len(hd) else '') for hd in hides])
    rows.append(['空亡'] + [(xunkong(gz) if lb in ('日', '年') else '') for lb, gz in zip(labels, gzs)])
    return grid(hdr, rows, ws, ['c'] + ['c']*len(gzs))

def aspect_tri(chart):
    ws = [6] + [8]*len(chart)
    hdr = [''] + [lb for lb, _ in chart]
    rows = []
    for i, (li, gi) in enumerate(chart):
        c = [li]
        for j, (lj, gj) in enumerate(chart):
            c.append(gi[1] if i == j else ('' if j > i else glyph(pair_rel(gi[1], gj[1]))))
        rows.append(c)
    return grid(hdr, rows, ws)

def transit_grid(chart, trans):
    ws = [8] + [8]*len(chart)
    hdr = [''] + [lb+gz[1] for lb, gz in chart]
    rows = []
    for tl, tz in trans:
        rows.append([tl+tz] + [(glyph(pair_rel(tz, gz[1])) or '·') for _, gz in chart])
    return grid(hdr, rows, ws)

def parse_dt(s):
    for f in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M'):
        try: return datetime.strptime(s, f)
        except ValueError: pass
    sys.exit("时间格式应为 'YYYY-MM-DD HH:MM[:SS]'：" + s)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('birth'); ap.add_argument('--sex', default='男', choices=['男','女','M','F'])
    ap.add_argument('--at', default=None); ap.add_argument('--lon', type=float, default=None)
    ap.add_argument('--tz', type=float, default=8.0)
    a = ap.parse_args()
    male = a.sex in ('男', 'M')
    birth = parse_dt(a.birth)
    target = parse_dt(a.at) if a.at else datetime.now().replace(microsecond=0)
    nb = nt = '钟表时'
    if a.lon is not None:
        birth, db = true_solar(birth, a.lon, a.tz)
        target, dt_ = true_solar(target, a.lon, a.tz)
        nb = '真太阳时 +%.1f′' % db if db >= 0 else '真太阳时 %.1f′' % db
        nt = '真太阳时 +%.1f′' % dt_ if dt_ >= 0 else '真太阳时 %.1f′' % dt_

    ny, nm, nd, nh = pillars(birth); dm = nd[0]
    chart = [('年', ny), ('月', nm), ('日', nd), ('时', nh)]
    W = 56
    L = ['八字  %s  %s  %s' % ('乾造' if male else '坤造', birth.strftime('%Y-%m-%d %H:%M:%S'), nb),
         '日主  %s %s     节气定柱·立春分年' % (dm, GAN_WX[dm])]
    print('\n'.join(banner(L, W)))
    if birth.hour >= 23 or birth.hour == 0:
        print('  ⚠ 子时区间：本盘按子初换日(23:00)定日柱')

    print('\n  〔命盘〕')
    print('\n'.join('  ' + x for x in col_block(['年','月','日','时'], [ny,nm,nd,nh], dm)))

    # 大运
    fwd = (ny[0] not in GAN_YIN) == male; seg = None
    try:
        ts = jie_times(birth)
        bnd = min(t for t in ts if t > birth) if fwd else max(t for t in ts if t < birth)
        age0 = abs((bnd - birth).total_seconds())/86400.0/3.0
        qy = birth + timedelta(days=age0*365.2422); TENY = 3652.42
        chain = []
        for s in range(1, 9):
            seg_s = qy + timedelta(days=(s-1)*TENY)
            cur = seg_s <= target < qy + timedelta(days=s*TENY)
            g = dayun_gz(nm, s, fwd)
            if cur: seg = (g, seg_s.year)
            chain.append(('▶' if cur else ' ') + '%s%02d' % (g, seg_s.year % 100))
        print('\n  〔大运〕 起运 %s 周岁%.1f %s行' % (qy.strftime('%Y-%m'), age0, '顺' if fwd else '逆'))
        print('   ' + ' '.join(chain))
    except Exception as e:
        print('\n  〔大运〕未计算 (%s)' % e)

    # 流盘
    ly, lm, ld, lh = pillars(target)
    print('\n  〔流盘〕 %s  %s' % (target.strftime('%Y-%m-%d %H:%M'), nt))
    print('\n'.join('  ' + x for x in col_block(['流年','流月','流日','流时'], [ly,lm,ld,lh], dm, 12)))

    # 关系矩阵
    print('\n  〔本命·地支关系矩阵〕   合=六合 半=半合 冲 刑 害 破 自=自刑')
    print('\n'.join('  ' + x for x in aspect_tri(chart)))

    trans = ([('运', seg[0][1])] if seg else []) + [('流年', ly[1]), ('流月', lm[1]), ('流日', ld[1]), ('流时', lh[1])]
    print('\n  〔流运 × 本命 引动矩阵〕')
    print('\n'.join('  ' + x for x in transit_grid(chart, trans)))

    # 三合三会三刑 + 天干 + 多值清单
    pos = [(lb, gz[1]) for lb, gz in chart]
    if seg: pos.append(('运', seg[0][1]))
    pos += [('流年', ly[1]), ('流月', lm[1]), ('流日', ld[1]), ('流时', lh[1])]
    br = {}
    for lb, z in pos: br.setdefault(z, []).append(lb)
    mem = lambda nm_: ' '.join('%s%s' % (br[c][0], c) for c in nm_ if c in br)
    tri = []
    for n, e in SANHE.items():
        if set(n) <= br.keys(): tri.append('三合%s局·%s [%s]' % (n, e, mem(n)))
    for n, e in SANHUI.items():
        if set(n) <= br.keys(): tri.append('三会%s·%s [%s]' % (n, e, mem(n)))
    for n, k in XING3.items():
        if set(n) <= br.keys(): tri.append('三刑%s(%s) [%s]' % (n, k, mem(n)))
    print('\n  〔三合/三会/三刑〕  ' + ('；'.join(tri) if tri else '无'))

    stems = [(lb, gz[0]) for lb, gz in chart] + ([('运', seg[0][0])] if seg else []) + \
            [('流年', ly[0]), ('流月', lm[0]), ('流日', ld[0]), ('流时', lh[0])]
    tg = []
    for i in range(len(stems)):
        for j in range(i+1, len(stems)):
            s = {stems[i][1], stems[j][1]}; fs = frozenset(s)
            t = ('合·'+TG_HE[fs]) if fs in TG_HE else ('冲' if s in TG_CHONG else None)
            if t: tg.append('%s%s%s%s%s' % (stems[i][0], stems[i][1], t, stems[j][0], stems[j][1]))
    print('  〔天干合冲〕      ' + ('；'.join(tg) if tg else '无'))
    print()

if __name__ == '__main__':
    main()
