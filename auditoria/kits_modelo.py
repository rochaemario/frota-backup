#!/usr/bin/env python3
"""05/11/2026 (pedido do Mario): kits por modelo e intervalo; nomes de modelos padronizados; RE-05 e MT-01 com marca/modelo.
Copia de antes em auditoria/kits-modelo-antes.json."""
import json,os,re,unicodedata,urllib.request,urllib.error,urllib.parse,datetime
URL='https://uzpoaifuxwojiomxqukf.supabase.co';K=os.environ['SUPABASE_SERVICE_KEY'];H={'apikey':K,'Authorization':'Bearer '+K}
def rq(m,p,data=None):
    h=dict(H);d=None
    if data is not None:d=json.dumps(data).encode();h['Content-Type']='application/json';h['Prefer']='return=representation'
    r=urllib.request.Request(URL+p,data=d,headers=h,method=m)
    with urllib.request.urlopen(r,timeout=60) as f:b=f.read();return f.status,json.loads(b) if b else None
na=lambda s:unicodedata.normalize('NFD',str(s or '')).encode('ascii','ignore').decode().lower()
ar=lambda n:(lambda s:'respiro' not in s and re.search(r'filtro (de |do |da )?ar\b|ar condicionado',s))(na(n))
MOD={'CONSTELATION 31280':'CONSTELLATION 31.280','CONSTELATION 31320':'CONSTELLATION 31.320','CONSTELATION 21280':'CONSTELLATION 21.280',
 'CONSTELATION 15180':'CONSTELLATION 15.180','EURO 3 WORKER 13180':'WORKER 13.180','AXOR 2831 6X4':'AXOR 2831','FM 540 6X4T':'FM 540'}
EQ={'RE-05':{'marca':'Caterpillar','modelo':'416'},'MT-01':{'marca':'JCB','modelo':'540-170'}}
KIT={'KIT-1000':{'kMarca':'Volvo','kModelo':'L60','kIv':1000,'desc':'KIT VOLVO L60 - 1000H'},'KIT-500':{'kMarca':'Caterpillar','kModelo':'416','kIv':500,'desc':'KIT CATERPILLAR 416 - 500H'}}
antes={};feito=[]
def patch(path,d):
    st2,b=rq('PATCH','/rest/v1/docs?path=eq.'+urllib.parse.quote(path,safe=''),{'data':d,'updated_at':datetime.datetime.utcnow().isoformat()+'Z'});return st2==200
st,rows=rq('GET','/rest/v1/docs?select=path,data&path=like.equipamentos/*')
for r in rows:
    d=r['data'] or {};o=json.loads(json.dumps(d));m=[]
    mo=str(d.get('modelo') or '').strip().upper()
    if mo in MOD:d['modelo']=MOD[mo];m.append(f"modelo {o.get('modelo')} -> {d['modelo']}")
    c=d.get('codigo')
    if c in EQ:
        for k,v in EQ[c].items():
            if not d.get(k):d[k]=v;m.append(f'{k} -> {v}')
    if m:antes[r['path']]=o;feito.append({'equip':c,'mud':m,'ok':patch(r['path'],d)})
st,rows=rq('GET','/rest/v1/docs?select=path,data&path=like.estoque/*')
for r in rows:
    d=r['data'] or {}
    if d.get('kit') and d.get('codigo') in KIT:
        antes[r['path']]=json.loads(json.dumps(d));d.update(KIT[d['codigo']]);d['encaixe']=[];d['qtd']=d.get('qtd') or 0
        feito.append({'kit':d['codigo'],'nome':d['desc'],'ok':patch(r['path'],d)})
json.dump(antes,open('auditoria/kits-modelo-antes.json','w'),indent=1,ensure_ascii=False)
json.dump(feito,open('auditoria/kits-modelo.json','w'),indent=1,ensure_ascii=False);print(json.dumps(feito,ensure_ascii=False,indent=1))
