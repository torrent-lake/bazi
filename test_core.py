# -*- coding: utf-8 -*-
# 纯逻辑内核自检：十神 / 刑冲合会 / 空亡 / 大运步进。无外部依赖。
import math

GAN = '甲乙丙丁戊己庚辛壬癸'
ZHI = '子丑寅卯辰巳午未申酉戌亥'
GAN_WX = dict(zip(GAN, '木木火火土土金金水水'))
ZHI_WX = dict(zip(ZHI, '水土木木土火火土金金土水'))
GAN_YIN = set('乙丁己辛癸')          # 阴干
SHENG = {'木':'火','火':'土','土':'金','金':'水','水':'木'}
KE    = {'木':'土','土':'水','水':'火','火':'金','金':'木'}

# 地支藏干（本气/中气/余气），与通行子平表一致
ZHI_HIDE = {
 '子':'癸','丑':'己癸辛','寅':'甲丙戊','卯':'乙','辰':'戊乙癸','巳':'丙庚戊',
 '午':'丁己','未':'己乙丁','申':'庚壬戊','酉':'辛','戌':'戊辛丁','亥':'壬甲'}

def ten_god(dm, g):
    """日主 dm 对天干 g 的十神。"""
    we, wx = GAN_WX[dm], GAN_WX[g]
    same = (dm in GAN_YIN) == (g in GAN_YIN)
    if wx == we:        return '比肩' if same else '劫财'
    if SHENG[we] == wx: return '食神' if same else '伤官'   # 我生
    if KE[we] == wx:    return '偏财' if same else '正财'   # 我克
    if KE[wx] == we:    return '七杀' if same else '正官'   # 克我
    if SHENG[wx] == we: return '偏印' if same else '正印'   # 生我

# ── 地支关系表 ──
CHONG = [set(p) for p in ('子午','丑未','寅申','卯酉','辰戌','巳亥')]
LIUHE = {frozenset('子丑'):'土',frozenset('寅亥'):'木',frozenset('卯戌'):'火',
         frozenset('辰酉'):'金',frozenset('巳申'):'水',frozenset('午未'):'土'}
HAI   = [set(p) for p in ('子未','丑午','寅巳','卯辰','申亥','酉戌')]
PO    = [set(p) for p in ('子酉','午卯','辰丑','戌未','寅亥','巳申')]
SANHE = {'申子辰':'水','亥卯未':'木','寅午戌':'火','巳酉丑':'金'}
SANHUI= {'寅卯辰':'木','巳午未':'火','申酉戌':'金','亥子丑':'水'}
BANHE = {frozenset('申子'):'水',frozenset('子辰'):'水',frozenset('亥卯'):'木',
         frozenset('卯未'):'木',frozenset('寅午'):'火',frozenset('午戌'):'火',
         frozenset('巳酉'):'金',frozenset('酉丑'):'金'}   # 半三合(含旺支)
XING3 = [frozenset('寅巳申'),frozenset('丑戌未')]          # 三刑全
XING_PAIR = [set('子卯')] + [set(p) for p in ('寅巳','巳申','丑戌','戌未')]  # 互刑/部分刑
ZIXING = set('辰午酉亥')                                   # 自刑(需重复)

def pair_rel(a, b):
    """返回 a,b 两地支间所有关系标签(可并存)。"""
    s = {a, b}; fs = frozenset(s); out = []
    if a != b:
        if s in CHONG: out.append('冲')
        if fs in LIUHE: out.append('六合化'+LIUHE[fs])
        if fs in BANHE: out.append('半合'+BANHE[fs])
        if s in HAI: out.append('害')
        if s in PO: out.append('破')
        if any(s == p for p in XING_PAIR): out.append('刑')
    else:
        if a in ZIXING: out.append('自刑')
    return out

def xunkong(gz):
    g, z = GAN.index(gz[0]), ZHI.index(gz[1])
    start = (z - g) % 12
    return ZHI[(start+10) % 12] + ZHI[(start+11) % 12]

def gz_index(gz):
    for i in range(60):
        if GAN[i%10]==gz[0] and ZHI[i%12]==gz[1]: return i
    raise ValueError(gz)

def dayun_gz(month_gz, step, forward):
    i = gz_index(month_gz) + (step if forward else -step)
    i %= 60
    return GAN[i%10] + ZHI[i%12]

def eot_minutes(yday):
    B = 2*math.pi*(yday-81)/364
    return 9.87*math.sin(2*B) - 7.53*math.cos(B) - 1.5*math.sin(B)

# ───────────────── 自检 ─────────────────
print('## 十神 (日主 乙):')
for g in '甲乙丙丁戊己庚辛壬癸':
    print(' ', g, ten_god('乙', g))
assert ten_god('乙','庚')=='正官' and ten_god('乙','甲')=='劫财'
assert ten_god('乙','癸')=='偏印' and ten_god('乙','丙')=='伤官' and ten_god('乙','戊')=='正财'
assert ten_god('甲','甲')=='比肩' and ten_god('甲','辛')=='正官' and ten_god('甲','戊')=='偏财'

print('\n## 关系多值校验:')
for a,b in [('巳','申'),('寅','亥'),('子','午'),('卯','辰'),('戌','未'),('子','丑')]:
    print('  %s%s -> %s' % (a,b, pair_rel(a,b)))
assert set(pair_rel('巳','申')) == {'六合化水','破','刑'}      # 巳申 同时 合/破/刑
assert set(pair_rel('寅','亥')) == {'六合化木','破'}
assert pair_rel('子','午') == ['冲']
assert pair_rel('卯','辰') == ['害']
assert pair_rel('辰','辰') == ['自刑']

print('\n## 三合/三会 检测:')
def triples(branches, table):
    pres=set(branches); hits=[]
    for name,el in table.items():
        if set(name) <= pres: hits.append((name, el))
    return hits
print('  申子辰 三合:', triples('申子辰卯', SANHE))
print('  亥子丑 三会:', triples('亥子丑', SANHUI))
assert triples('申子辰', SANHE)==[('申子辰','水')]
assert triples('巳午未', SANHUI)==[('巳午未','火')]

print('\n## 空亡:')
for d in ['甲子','乙卯','庚午','癸未']:
    print('  %s 旬空 %s' % (d, xunkong(d)))
assert xunkong('甲子')=='戌亥'      # 甲子旬空戌亥
assert xunkong('甲戌')=='申酉'

print('\n## 大运步进 (月柱 甲申, 顺行):')
print('  ', [dayun_gz('甲申', s, True) for s in range(1,6)])
assert dayun_gz('甲申',1,True)=='乙酉' and dayun_gz('甲申',1,False)=='癸未'

print('\n## 均时差(分) 抽样:', round(eot_minutes(45),1), round(eot_minutes(300),1))
print('\nALL ASSERTS PASSED')
