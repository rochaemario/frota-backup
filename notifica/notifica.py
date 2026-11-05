#!/usr/bin/env python3
"""Notificacoes no celular do administrador (Web Push). Roda pela rotina do GitHub.
Eventos: aviso novo/resposta para o admin; preventiva a 100/75/50/25 h e vencida; item abaixo do minimo ou zerado;
lancamento feito por outra pessoa (preventiva, filtro de ar, saida/entrada de estoque, horimetro).
Estado guardado no Supabase em config/notif (na primeira vez so grava o estado, sem notificar).
A chave de envio (VAPID) e derivada da chave do servico: nao precisa de outro segredo. A chave publica vai para config/push."""
import json,os,math,hashlib,base64,datetime,urllib.request,urllib.error,urllib.parse
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
URL='https://uzpoaifuxwojiomxqukf.supabase.co';K=os.environ['SUPABASE_SERVICE_KEY'];H={'apikey':K,'Authorization':'Bearer '+K}
APP='https://rochaemario.github.io/frota-rondaflex/'
def rq(m,p,data=None,extra=None):
    h=dict(H);d=None
    if extra:h.update(extra)
    if data is not None:d=json.dumps(data).encode();h['Content-Type']='application/json'
    r=urllib.request.Request(URL+p,data=d,headers=h,method=m)
    with urllib.request.urlopen(r,timeout=60) as f:b=f.read();return json.loads(b) if b else None
def put(path,data):
    rq('POST','/rest/v1/docs?on_conflict=path',[{'path':path,'parent':path.rsplit('/',1)[0],'data':data,'updated_at':datetime.datetime.utcnow().isoformat()+'Z'}],{'Prefer':'resolution=merge-duplicates,return=minimal'})
def b64u(x):return base64.urlsafe_b64encode(x).decode().rstrip('=')
# ---- chave VAPID derivada da chave do servico
n=int('FFFFFFFF00000000FFFFFFFFFFFFFFFFBCE6FAADA7179E84F3B9CAC2FC632551',16)
pv=int(hashlib.sha256(b'frota-vapid:'+K.encode()).hexdigest(),16)%(n-1)+1
key=ec.derive_private_key(pv,ec.SECP256R1())
PUB=b64u(key.public_key().public_bytes(serialization.Encoding.X962,serialization.PublicFormat.UncompressedPoint))
PEM=key.private_bytes(serialization.Encoding.PEM,serialization.PrivateFormat.PKCS8,serialization.NoEncryption())
def VAP():
    from py_vapid import Vapid
    return Vapid.from_pem(PEM)
# ---- dados
rows=[]
off=0
while True:
    b=rq('GET',f'/rest/v1/docs?select=path,data&order=path&offset={off}&limit=1000');rows+=b
    if len(b)<1000:break
    off+=1000
D={r['path']:(r['data'] or {}) for r in rows}
def col(c):return {p.split('/',1)[1]:d for p,d in D.items() if p.startswith(c+'/') and p.count('/')==1}
perfis=rq('GET','/rest/v1/perfis?select=user_id,nome,email,papel') or []
NOME={p['user_id']:(p.get('nome') or (p.get('email') or '').split('@')[0] or 'Alguem') for p in perfis}
ADM={p['user_id'] for p in perfis if p.get('papel')=='admin'}
if (D.get('config/push') or {}).get('vapid')!=PUB:put('config/push',{'vapid':PUB})
subs={p:d for p,d in col('push').items() if d.get('uid') in ADM and d.get('sub')}
eqs={i:e for i,e in col('equipamentos').items() if e.get('status')!='inativo'}
trocas=col('trocas');est=col('estoque');movs=col('movs');avisos=col('avisos')
ST=D.get('config/notif') or None;primeira=ST is None;ST=ST or {}
agora=int(datetime.datetime.utcnow().timestamp()*1000)
ev=[]  # (titulo, texto, abrir, tag)
def nome(u):return NOME.get(u,'Alguem')
# ---- avisos
avts=ST.get('av_ts',agora)
for aid,a in avisos.items():
    part=set([a.get('de')]+list(a.get('para') or []))
    msgs=[{'de':a.get('de'),'texto':a.get('texto',''),'ts':a.get('ts',0)}]+list(a.get('resp') or [])
    for u in ADM & part:
        novas=[m for m in msgs if m.get('de')!=u and (m.get('ts') or 0)>avts]
        if novas:
            m=novas[-1];ev.append((f"Aviso de {nome(m.get('de'))}",(m.get('texto') or 'Anexo')[:120]+(f' (+{len(novas)-1})' if len(novas)>1 else ''),'av:'+aid,'av-'+aid))
ST['av_ts']=max([avts]+[m.get('ts') or 0 for a in avisos.values() for m in [{'ts':a.get('ts',0)}]+list(a.get('resp') or [])])
# ---- preventivas (item que vence primeiro, como o cronograma)
def eh_vl(e):
    import unicodedata;t=unicodedata.normalize('NFD',str(e.get('tipo') or '')).encode('ascii','ignore').decode().lower().strip();return t=='veiculo leve'
def base(eid):
    ts=[t for t in trocas.values() if t.get('equipId')==eid and t.get('tipo') not in ('reprog','hmtroca','filtro_ar')]
    if not ts:return 0.0
    t=max(ts,key=lambda x:((x.get('data') or ''),float(x.get('horimetro') or 0)))
    d=sum(float(x.get('delta') or 0) for x in trocas.values() if x.get('equipId')==eid and x.get('tipo')=='hmtroca' and (x.get('data') or '')>(t.get('data') or ''))
    return float(t.get('horimetro') or 0)+d
# valor lancado: como foi digitado (4.9 -> 4,9; 2534 -> 2.534)
def nl(v):
    try:v=float(v)
    except (TypeError,ValueError):return str(v or '')
    t=f'{v:,.2f}'.rstrip('0').rstrip('.');return t.replace(',','_').replace('.',',').replace('_','.')
def fnum(x):
    try:return float(x) if x not in ('',None) else None
    except (TypeError,ValueError):return None
def dlt(eid,dt):return sum(float(x.get('delta') or 0) for x in trocas.values() if x.get('equipId')==eid and x.get('tipo')=='hmtroca' and (x.get('data') or '')>(dt or ''))
def inf_ult(eid):
    ts=[t for t in trocas.values() if t.get('equipId')==eid and t.get('tipo')=='informada']
    return max(ts,key=lambda x:x.get('data') or '') if ts else None
# como o app: cada item vence pelo proprio intervalo (sem intervalo proprio, o da ficha), contado da ultima troca dele
def prox_eq(eid,e,iv):
    its=e.get('itens') or []
    if not its:return round(base(eid)+iv,1) if iv>0 else None
    i0=inf_ult(eid);ps=[]
    for it in its:
        s=it.get('ivSel')
        if s=='aval':continue
        ivI=fnum(s) or iv
        u=fnum(it.get('ultimaH'))
        if i0 and (u is None or (i0.get('data') or '')>(it.get('ultimaData') or '')):u=float(i0.get('horimetro') or 0)+dlt(eid,i0.get('data'))
        if u is None:u=base(eid)
        pH=fnum(it.get('proxH'))
        p=pH if it.get('reprog') and pH is not None else (u+ivI if ivI else pH)
        if p is not None:ps.append(p)
    return round(min(ps),1) if ps else None
ORD=['', '100','75','50','25','V']
pst=ST.get('prev',{});novo_prev={}
for eid,e in eqs.items():
    try:iv=float(e.get('intervaloPrev') or 0);hm=float(e.get('horimetro'))
    except (TypeError,ValueError):continue
    if eh_vl(e) and e.get('soCad') is not False:continue
    prox=prox_eq(eid,e,iv)
    if prox is None:continue
    falta=round(prox-hm,1)
    lvl='V' if falta<=0 else (str(int(math.ceil(falta/25)*25)) if falta<=100 else '')
    old=pst.get(eid) or {}
    if old.get('prox')!=prox:old={'prox':prox,'lvl':''}
    if lvl and ORD.index(lvl)>ORD.index(old.get('lvl','')):
        cod=e.get('codigo') or eid
        ev.append((f'{cod} · preventiva vencida' if lvl=='V' else f'{cod} · faltam {int(falta) if falta==int(falta) else falta} h',
                   f"Proxima com {prox:,.0f} h".replace(',', '.')+f" · horimetro {nl(hm)} h",'eq:'+eid,'pv-'+eid))
        old['lvl']=lvl
    novo_prev[eid]=old
ST['prev']=novo_prev
# ---- estoque
sst=ST.get('est',{});novo_est={}
for sid,s in est.items():
    if s.get('kit') or s.get('inativo'):continue
    try:mi=float(s.get('minimo') or 0);q=float(s.get('qtd') or 0)
    except (TypeError,ValueError):continue
    if mi<=0:continue
    lv=2 if q<=0 else (1 if q<=mi else 0)
    if lv>sst.get(sid,0):
        un=s.get('un') or 'un'
        ev.append(('Estoque zerado' if lv==2 else 'Estoque abaixo do minimo',f"{s.get('desc','Item')} · saldo {q:g} {un} · minimo {mi:g}",'mv:'+sid,'es-'+sid))
    novo_est[sid]=lv
ST['est']=novo_est
# ---- lancamentos de outras pessoas
lts=ST.get('lanc_ts',agora);mx=lts
for tid,t in trocas.items():
    em=t.get('_em') or 0;por=t.get('_por')
    if em>lts and por and por not in ADM:
        cod=(eqs.get(t.get('equipId')) or {}).get('codigo') or t.get('equipId','')
        tp='filtro de ar' if t.get('tipo')=='filtro_ar' else 'preventiva informada' if t.get('tipo')=='informada' else 'troca de horimetro' if t.get('tipo')=='hmtroca' else 'preventiva'
        ev.append((f'{nome(por)} registrou {tp}',f"{cod} · {len(t.get('itens') or [])} itens · {nl(t.get('horimetro',''))} h",'tr:'+tid,'tr-'+tid))
    mx=max(mx,em)
for mid,m in movs.items():
    em=m.get('_em') or 0;por=m.get('_por')
    if em>lts and por and por not in ADM and m.get('origem') not in ('preventiva','estorno'):
        s=est.get(m.get('estoqueId')) or {}
        ev.append((f"{nome(por)} lancou {'saida' if m.get('tipo')=='saida' else 'entrada'} no estoque",f"{s.get('desc','Item')} · {m.get('qtd','')} {s.get('un','un')}",'mv:'+str(m.get('estoqueId','')),'mv-'+mid))
    mx=max(mx,em)
hm=[]
for eid,e in eqs.items():
    em=e.get('horimetroEm') or 0;por=e.get('horimetroPor')
    if em>lts and por and por not in ADM:hm.append((por,e.get('codigo') or eid,e.get('horimetro')))
    mx=max(mx,em)
if hm:
    quem=sorted({nome(p) for p,_,_ in hm})
    ev.append((f"{', '.join(quem)} lancou horimetro",'; '.join(f'{c} {nl(h)} h' for _,c,h in hm[:6])+(f' (+{len(hm)-6})' if len(hm)>6 else ''),'leit','hm'))
ST['lanc_ts']=mx
# ---- envio
ST['ultima']=agora
if primeira:ev=[]
enviados=0;erros=[]
if ev and subs:
    from pywebpush import webpush,WebPushException
    if len(ev)>5:ev=ev[:4]+[(f'+{len(ev)-4} outras notificacoes','Abra o app para ver','', 'mais')]
    for p,sd in list(subs.items()):
        for t,b,ab,tag in ev:
            try:
                webpush(subscription_info=sd['sub'],data=json.dumps({'t':t,'b':b,'u':ab,'tag':tag}),vapid_private_key=VAP(),vapid_claims={'sub':'mailto:frota@rondaflex.app'},ttl=86400)
                enviados+=1
            except WebPushException as x:
                code=getattr(x.response,'status_code',0)
                if code in (404,410):
                    rq('DELETE','/rest/v1/docs?path=eq.'+urllib.parse.quote('push/'+p,safe=''));erros.append(f'inscricao vencida removida: {p}');break
                erros.append(f'{code} {str(x)[:120]}')
# teste manual: TESTE=1 manda uma notificacao de teste
if os.environ.get('TESTE')=='1' and subs:
    from pywebpush import webpush
    for p,sd in subs.items():
        webpush(subscription_info=sd['sub'],data=json.dumps({'t':'Controle de Frota','b':'Notificacoes ativadas neste celular','u':'','tag':'teste'}),vapid_private_key=VAP(),vapid_claims={'sub':'mailto:frota@rondaflex.app'},ttl=3600);enviados+=1
put('config/notif',ST)
print(json.dumps({'primeira':primeira,'eventos':len(ev),'inscricoes':len(subs),'enviados':enviados,'erros':erros},ensure_ascii=False))
