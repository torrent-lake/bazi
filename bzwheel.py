#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""八字地支关系盘 渲染引擎 (Astrolog 画法: 栅格位图+细线原语+逐度刻度环+穿心相位网,
3× 超采样柔边)。逐字五行着色; 宋体(明体); 纯黑。配色照 Astrolog v8 kElemA/kAspB。
chart_png(...) 返回 PNG bytes 供 app 调用; 也可命令行出图。"""
import argparse, math
from io import BytesIO
from datetime import timedelta, datetime
from PIL import Image, ImageDraw, ImageFont
import bz

SS = 3
Wc, Hc = 1160, 900
CX, CY = 730, 460
R_OUT, R_BIN, R_GLY, R_POS = 384, 348, 366, 344
R_FL, R_NA = 290, 216
FCJK = '/System/Library/Fonts/Supplemental/Songti.ttc'   # 宋体/明体
FMONO = '/System/Library/Fonts/Menlo.ttc'

ECOL = {'木':(76,192,116),'火':(234,84,76),'土':(220,178,86),'金':(228,230,238),'水':(96,154,252)}
ELEM = {'子':'水','丑':'土','寅':'木','卯':'木','辰':'土','巳':'火','午':'火','未':'土','申':'金','酉':'金','戌':'土','亥':'水'}
ACOL = {'冲':(96,142,250),'合':(228,198,92),'会':(82,206,206),'三合':(74,196,118),
        '半':(44,150,84),'刑':(232,84,78),'害':(206,108,214),'破':(226,160,78),'自':(232,84,78)}
PRIO = ['冲','刑','合','会','半','害','破','自']
RING, RDIM, TKMAJ, TKMIN, BORDER = (62,70,90),(38,44,58),(116,126,154),(52,59,78),(84,92,114)
TXT, SUB, RULE = (216,222,236),(128,136,158),(54,61,80)

img = None; D = None; _fc = {}
def fnt(size, mono=False):
    k = (size, mono)
    if k not in _fc:
        try: _fc[k] = ImageFont.truetype(FMONO if mono else FCJK, size*SS)
        except Exception: _fc[k] = ImageFont.truetype('/System/Library/Fonts/STHeiti Medium.ttc', size*SS)
    return _fc[k]
def s(v): return int(round(v*SS))
def ang(d): return math.radians(d-90)
def P(r,d): return (CX+r*math.cos(ang(d)), CY+r*math.sin(ang(d)))
def wxof(ch): return bz.GAN_WX[ch] if ch in bz.GAN else ELEM[ch]
def col(ch): return ECOL[wxof(ch)]
def line(x1,y1,x2,y2,c,w=1): D.line([(s(x1),s(y1)),(s(x2),s(y2))], fill=c, width=max(1,s(w)))
def dash(x1,y1,x2,y2,c,w=1,on=8,off=7):
    Ln=math.hypot(x2-x1,y2-y1)
    if Ln<1: return
    ux,uy=(x2-x1)/Ln,(y2-y1)/Ln; p=0
    while p<Ln:
        b=min(p+on,Ln); line(x1+ux*p,y1+uy*p,x1+ux*b,y1+uy*b,c,w); p+=on+off
def circle(r,c,w=1): D.ellipse([s(CX-r),s(CY-r),s(CX+r),s(CY+r)], outline=c, width=max(1,s(w)))
def dot(x,y,r,c): D.ellipse([s(x-r),s(y-r),s(x+r),s(y+r)], fill=c)
def txt(x,y,t,c,sz,an='lm',mono=False): D.text((s(x),s(y)),t,font=fnt(sz,mono),fill=c,anchor=an)
def chars_c(xc,y,chars,sz):
    f=fnt(sz); ws=[D.textlength(ch,font=f) for ch in chars]; cx=s(xc)-sum(ws)/2
    for ch,w in zip(chars,ws): D.text((cx,s(y)),ch,font=f,fill=col(ch),anchor='lm'); cx+=w
def node(x,y,gan,zhi,sz):
    f=fnt(sz); wg=D.textlength(gan,font=f); wz=D.textlength(zhi,font=f); tot=wg+wz; left=s(x)-tot/2
    h=f.size*0.62; D.rectangle([left-s(3),s(y)-h,left+tot+s(3),s(y)+h], fill=(0,0,0))
    D.text((left,s(y)),gan,font=f,fill=col(gan),anchor='lm'); D.text((left+wg,s(y)),zhi,font=f,fill=col(zhi),anchor='lm')
def dom(rels):
    g=bz.glyph(rels)
    for k in PRIO:
        if k in g: return k
def covering_arc(idxs):
    a=sorted(30*i for i in idxs); gp=[(a[(k+1)%len(a)]-a[k])%360 for k in range(len(a))]
    km=gp.index(max(gp)); st=a[(km+1)%len(a)]; return st, st+(360-max(gp))
def dayun_at(birth,target,male,ny,nm):
    fwd=(ny[0] not in bz.GAN_YIN)==male
    try:
        ts=bz.jie_times(birth); bnd=min(t for t in ts if t>birth) if fwd else max(t for t in ts if t<birth)
        qy=birth+timedelta(days=abs((bnd-birth).total_seconds())/86400.0/3.0*365.2422)
        for st in range(1,12):
            if qy+timedelta(days=(st-1)*3652.42)<=target<qy+timedelta(days=st*3652.42): return bz.dayun_gz(nm,st,fwd)
    except Exception: pass

def panel(natal,dayun,dm,birth,nb,male):
    px,py,pw=18,94,318; cols=natal+([('大运',dayun)] if dayun else [])
    xc=[px+78+k*48 for k in range(len(cols))]; bottom=py+266
    D.rectangle([s(px),s(py),s(px+pw),s(bottom)], outline=BORDER, width=max(1,s(1)))
    line(px,py+52,px+pw,py+52,RULE,1)
    txt(px+12,py+26,'乾造' if male else '坤造',TXT,17,'lm')
    txt(px+58,py+22,birth.strftime('%Y-%m-%d'),SUB,12,'lm',True); txt(px+58,py+40,birth.strftime('%H:%M:%S'),SUB,12,'lm',True)
    txt(px+150,py+22,nb,SUB,11,'lm'); txt(px+150,py+40,'日主',SUB,11,'lm')
    txt(px+186,py+40,dm,col(dm),14,'lm'); txt(px+204,py+40,bz.GAN_WX[dm],SUB,11,'lm')
    for k,(lab,_) in enumerate(cols): txt(xc[k],py+68,lab,SUB,12,'mm')
    line(px,py+82,px+pw,py+82,RULE,1)
    for k in range(len(cols)-1):
        mx=(xc[k]+xc[k+1])/2; line(mx,py+60,mx,bottom-8,RDIM,0.6)
    for lab,yy in (('主星',104),('天干',134),('地支',164),('藏干',200)): txt(px+10,py+yy,lab,SUB,10,'lm')
    for k,(lab,gz) in enumerate(cols):
        sg='日主' if lab=='日' else bz.ten_god(dm,gz[0])
        txt(xc[k],py+104,sg,(210,180,90) if lab=='日' else SUB,11,'mm')
        chars_c(xc[k],py+136,gz[0],21); chars_c(xc[k],py+166,gz[1],21)
        for r,h in enumerate(bz.ZHI_HIDE[gz[1]]): txt(xc[k],py+192+r*17,h,col(h),11,'mm')
    line(px,py+182,px+pw,py+182,RULE,1)
    kong=' '.join('%s%s'%(l,bz.xunkong(gz)) for l,gz in [('日',natal[2][1]),('年',natal[0][1])])
    txt(px+12,bottom-14,'旬空 '+kong,SUB,11,'lm')
    return bottom

def render(birth,target,male,nb,nt,dayun):
    global img, D
    img = Image.new('RGB',(Wc*SS,Hc*SS),(0,0,0)); D = ImageDraw.Draw(img)
    ny,nm,nd,nh=bz.pillars(birth); dm=nd[0]
    ly,lm,ld,lh=bz.pillars(target)
    natal=[('年',ny),('月',nm),('日',nd),('时',nh)]
    flows=([('运',dayun)] if dayun else [])+[('流年',ly),('流月',lm),('流日',ld),('流时',lh)]
    D.rectangle([s(8),s(8),s(Wc-8),s(Hc-8)], outline=BORDER, width=max(1,s(1)))
    txt(26,30,'八  字  地  支  关  系  盘',TXT,19,'lm'); line(26,46,300,46,RULE,1)
    circle(R_OUT,RING,1); circle(R_OUT-4,RDIM,0.8); circle(R_BIN,RING,1); circle(R_FL,RDIM,0.8); circle(R_NA,RDIM,0.8)
    for d in range(360):
        ln=15 if d%30==0 else (10 if d%10==0 else (7 if d%5==0 else 4))
        c=TKMAJ if d%30==0 else (TKMIN if d%5==0 else RDIM)
        a,b=P(R_OUT,d),P(R_OUT-ln,d); line(a[0],a[1],b[0],b[1],c,1)
        if d%30==0: p1,p2=P(R_NA,d),P(R_BIN,d); line(p1[0],p1[1],p2[0],p2[1],RDIM,0.6)
    for i in range(12): g=P(R_GLY,i*30); txt(g[0],g[1],bz.ZHI[i],col(bz.ZHI[i]),22,'mm')
    occ=set(gz[1] for _,gz in natal)|set(gz[1] for _,gz in flows)
    for name in bz.SANHE:
        if set(name)<=occ:
            ps=[P(R_NA,bz.ZHI.index(c)*30) for c in name]
            D.line([(s(x),s(y)) for x,y in ps]+[(s(ps[0][0]),s(ps[0][1]))],fill=ACOL['三合'],width=max(1,s(1)))
    for name in bz.SANHUI:
        if set(name)<=occ:
            st,en=covering_arc([bz.ZHI.index(c) for c in name]); rr=R_OUT+13
            D.arc([s(CX-rr),s(CY-rr),s(CX+rr),s(CY+rr)],st-90,en-90,fill=ACOL['会'],width=max(1,s(2)))
    for _,gz in flows:
        for _,ng in natal:
            d=dom(bz.pair_rel(gz[1],ng[1]))
            if d: p1,p2=P(R_FL,bz.ZHI.index(gz[1])*30),P(R_NA,bz.ZHI.index(ng[1])*30); dash(p1[0],p1[1],p2[0],p2[1],ACOL[d],0.8,7,8)
    nbz=[gz[1] for _,gz in natal]
    for i in range(len(nbz)):
        for j in range(i+1,len(nbz)):
            d=dom(bz.pair_rel(nbz[i],nbz[j]))
            if d: p1,p2=P(R_NA,bz.ZHI.index(nbz[i])*30),P(R_NA,bz.ZHI.index(nbz[j])*30); line(p1[0],p1[1],p2[0],p2[1],ACOL[d],1.5)
    def place(items,r,ring):
        by={}
        for lab,gz in items: by.setdefault(gz[1],[]).append((lab,gz[0]))
        for b,lst in by.items():
            deg=bz.ZHI.index(b)*30; pd=P(ring,deg); dot(pd[0],pd[1],2.0,col(b))
            x,y=P(r,deg); node(x,y,lst[0][1],b,15)
            ox,oy=P(r+(19 if r==R_FL else -21),deg); txt(ox,oy,'·'.join(l for l,_ in lst),(SUB if r==R_NA else (210,164,96)),11,'mm')
    place(natal,R_NA,R_POS); place(flows,R_FL,R_BIN-6); dot(CX,CY,2.2,SUB)
    bottom=panel(natal,dayun,dm,birth,nb,male)
    ly2=bottom+22; txt(20,ly2,'相  位',SUB,12,'lm'); line(70,ly2,330,ly2,RULE,1)
    leg=[('冲','六冲 对'),('三合','三合 拱'),('会','三会 方'),('合','六合'),('半','半三合'),('刑','三刑'),('害','六害'),('破','六破')]
    for k,(g,nme) in enumerate(leg):
        c=k//4; yy=ly2+24*((k%4)+1); xx=20+c*160; line(xx,yy,xx+30,yy,ACOL[g],2); txt(xx+38,yy,nme,TXT,11,'lm')
    txt(20,Hc-44,'内环 命局四柱 · 外环 大运/流盘',SUB,11,'lm')
    txt(20,Hc-26,'流盘 %s  %s'%(target.strftime('%Y-%m-%d %H:%M'),nt),SUB,11,'lm')
    return img.resize((Wc,Hc),Image.LANCZOS)

def prep(birth,target,lon,tz):
    nb=nt='钟表时'
    if lon is not None:
        birth,db=bz.true_solar(birth,lon,tz); target,d2=bz.true_solar(target,lon,tz)
        nb='真太阳时%+.1f′'%db; nt='真太阳时%+.1f′'%d2
    return birth,target,nb,nt

def chart_png(birth,target,male,lon=None,tz=8.0):
    b,t,nb,nt=prep(birth,target,lon,tz)
    ny,nm,nd,nh=bz.pillars(b)
    im=render(b,t,male,nb,nt,dayun_at(b,t,male,ny,nm))
    buf=BytesIO(); im.save(buf,'PNG'); return buf.getvalue()

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('birth'); ap.add_argument('--sex',default='男',choices=['男','女','M','F'])
    ap.add_argument('--at',default=None); ap.add_argument('--lon',type=float,default=None)
    ap.add_argument('--tz',type=float,default=8.0); ap.add_argument('--out',default='wheel.png')
    a=ap.parse_args()
    birth=bz.parse_dt(a.birth); target=bz.parse_dt(a.at) if a.at else datetime.now().replace(microsecond=0)
    png=chart_png(birth,target,a.sex in ('男','M'),a.lon,a.tz)
    open(a.out,'wb').write(png); print('written',a.out)

if __name__=='__main__': main()
