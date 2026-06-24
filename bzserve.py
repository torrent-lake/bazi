#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""八字地支关系盘 — 本地应用 (浏览器即窗口)。渲染走 bzwheel 的 PIL 栅格引擎。
流时可接实时(at=now),自动重画 = Astrolog animation 走盘。
运行:  python bzserve.py [--port 8765]   然后浏览器开 http://127.0.0.1:8765"""
import argparse, http.server, urllib.parse
from datetime import datetime
import bz, bzwheel

PAGE = """<!doctype html><html lang="zh"><meta charset="utf-8">
<title>八字地支关系盘</title>
<style>
 html,body{margin:0;height:100%;background:#000;color:#cdd6e6;
   font-family:"Songti SC","STSong",serif;-webkit-font-smoothing:antialiased}
 #wrap{display:flex;height:100%}
 #side{width:272px;flex:none;padding:18px 16px;border-right:1px solid #3a4156;box-sizing:border-box}
 #main{flex:1;display:flex;align-items:center;justify-content:center;overflow:auto;background:#000}
 #main img{max-width:100%;max-height:100%}
 h1{font-size:17px;letter-spacing:3px;font-weight:500;margin:0 0 14px;color:#e6ecf7}
 label{display:block;font-size:12px;color:#8a93aa;margin:12px 0 4px}
 input,select{width:100%;box-sizing:border-box;background:#0b0e16;color:#dde4f2;
   border:1px solid #3a4156;border-radius:3px;padding:6px 7px;font:13px/1.3 monospace}
 .row{display:flex;gap:8px}.row>*{flex:1}
 .btns{display:flex;flex-wrap:wrap;gap:6px;margin-top:10px}
 button{background:#121726;color:#cdd6e6;border:1px solid #3a4156;border-radius:3px;
   padding:6px 9px;font-size:12px;cursor:pointer;font-family:inherit}
 button:hover{border-color:#5a6b8e} button.on{background:#26324a;border-color:#6f86b8}
 #clock{margin-top:14px;font:13px monospace;color:#8a93aa;min-height:16px}
 #liwrap{display:flex;align-items:center;gap:7px;margin-top:14px;font-size:13px}
 hr{border:none;border-top:1px solid #2a3043;margin:16px 0}
 .hint{font-size:11px;color:#667085;margin-top:16px;line-height:1.7}
</style>
<div id="wrap">
 <div id="side">
  <h1>八字 地支盘</h1>
  <label>出生 (阳历)</label>
  <input id="birth" type="datetime-local" value="1990-06-15T10:30" step="60">
  <div class="row">
   <div><label>性别</label><select id="sex"><option>男</option><option>女</option></select></div>
   <div><label>经度E</label><input id="lon" value="121.47"></div>
   <div><label>时区</label><input id="tz" value="8"></div>
  </div>
  <hr>
  <label>流盘时刻</label>
  <input id="at" type="datetime-local" step="60">
  <div class="btns">
   <button onclick="step(-2)">−时辰</button>
   <button onclick="step(2)">＋时辰</button>
   <button onclick="stepD(-1)">−日</button>
   <button onclick="stepD(1)">＋日</button>
   <button id="play" onclick="anim()">▶ 走盘</button>
  </div>
  <div id="liwrap"><input type="checkbox" id="live" onchange="toggleLive()"><label for="live" style="margin:0">实时流时 (此刻)</label></div>
  <div id="clock"></div>
  <div class="hint">内环 命局四柱 · 外环 大运/流盘<br>实线 本命相位 · 虚线 流运引动<br>逐字五行着色 · 真太阳时已校正</div>
 </div>
 <div id="main"><img id="im"></div>
</div>
<script>
const $=id=>document.getElementById(id);
function pad(n){return String(n).padStart(2,'0')}
function fmt(d){return d.getFullYear()+'-'+pad(d.getMonth()+1)+'-'+pad(d.getDate())+'T'+pad(d.getHours())+':'+pad(d.getMinutes())}
function nowLocal(){return fmt(new Date())}
function draw(){
  let live=$('live').checked;
  let at = live ? 'now' : ($('at').value||'now');
  let q=new URLSearchParams({birth:$('birth').value,sex:$('sex').value,lon:$('lon').value,tz:$('tz').value,at:at,_:Date.now()});
  $('im').src='/wheel.png?'+q.toString();
}
function step(h){let v=$('at').value||nowLocal();let d=new Date(v);d.setHours(d.getHours()+h);$('at').value=fmt(d);$('live').checked=false;clearInterval(liveT);draw()}
function stepD(n){step(n*24)}
let liveT=null;
function toggleLive(){
  if($('live').checked){draw();liveT=setInterval(()=>{$('clock').textContent='此刻 '+new Date().toLocaleString('zh-CN');if(Math.floor(Date.now()/1000)%15===0)draw();},1000);}
  else{clearInterval(liveT);$('clock').textContent='';}
}
let animT=null;
function anim(){
  if(animT){clearInterval(animT);animT=null;$('play').classList.remove('on');return;}
  $('live').checked=false;clearInterval(liveT);$('play').classList.add('on');
  if(!$('at').value)$('at').value=nowLocal();
  animT=setInterval(()=>step(2),700);
}
['birth','sex','lon','tz','at'].forEach(id=>$(id).addEventListener('change',()=>{if(!$('live').checked)draw()}));
$('at').value=nowLocal();draw();
</script></html>"""

def norm(sv):
    return bz.parse_dt(sv.strip().replace('T', ' '))

class H(http.server.BaseHTTPRequestHandler):
    def _send(self, code, ctype, body):
        self.send_response(code); self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(body))); self.send_header('Cache-Control', 'no-store')
        self.end_headers(); self.wfile.write(body)
    def do_GET(self):
        u = urllib.parse.urlparse(self.path); q = urllib.parse.parse_qs(u.query)
        g = lambda k, d=None: q.get(k, [d])[0]
        if u.path in ('/', '/index.html'):
            self._send(200, 'text/html; charset=utf-8', PAGE.encode('utf-8')); return
        if u.path == '/wheel.png':
            try:
                birth = norm(g('birth', '1990-06-15 10:30'))
                atv = g('at', 'now')
                target = datetime.now() if atv in (None, '', 'now') else norm(atv)
                male = g('sex', '男') in ('男', 'M', 'm')
                lon = g('lon', ''); lon = float(lon) if lon not in ('', None) else None
                tz = float(g('tz', '8') or 8)
                self._send(200, 'image/png', bzwheel.chart_png(birth, target, male, lon, tz))
            except Exception as e:
                self._send(500, 'text/plain; charset=utf-8', ('render error: %r' % e).encode())
            return
        self._send(404, 'text/plain', b'404')
    def log_message(self, *a): pass

def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--port', type=int, default=8765)
    a = ap.parse_args()
    print('八字盘 app: http://127.0.0.1:%d  (Ctrl-C 退出)' % a.port)
    http.server.HTTPServer(('127.0.0.1', a.port), H).serve_forever()

if __name__ == '__main__':
    main()
