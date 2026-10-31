#!/usr/bin/env python3
"""Correcoes de 31/10/2026 (pedido do Mario):
 1) PC-01 preventiva de 30/10 (lancada com Ajuste): tira as 5 linhas repetidas (ja estao no KIT L60 Volvo). Estoque nao muda.
 2) EH-05 preventiva de 29/08 e plano da EH-05: Filtro de ar motor secundario 11110683 -> VOE11110176; Elemento filtro Racor 11110683 -> VOE11110683.
Guarda copia de tudo antes em auditoria/corrige-31out-antes.json. So altera se o dado estiver como esperado."""
import json, os, urllib.request, urllib.error, urllib.parse, unicodedata, datetime
URL='https://uzpoaifuxwojiomxqukf.supabase.co';K=os.environ['SUPABASE_SERVICE_KEY'];H={'apikey':K,'Authorization':'Bearer '+K}
def rq(m,p,data=None):
    h=dict(H);d=None
    if data is not None:d=json.dumps(data).encode();h['Content-Type']='application/json';h['Prefer']='return=representation'
    r=urllib.request.Request(URL+p,data=d,headers=h,method=m)
    try:
        with urllib.request.urlopen(r,timeout=60) as f:b=f.read();return f.status,json.loads(b) if b else None
    except urllib.error.HTTPError as e:return e.code,e.read()[:300]
na=lambda s:unicodedata.normalize('NFD',str(s or '')).encode('ascii','ignore').decode().lower().strip()
def get(path):
    st,b=rq('GET','/rest/v1/docs?select=path,data&path=eq.'+urllib.parse.quote(path,safe=''));assert st==200 and b,(path,st,b);return b[0]['data']
def put(path,data):
    st,b=rq('PATCH','/rest/v1/docs?path=eq.'+urllib.parse.quote(path,safe=''),{'data':data,'updated_at':datetime.datetime.utcnow().isoformat()+'Z'});assert st==200 and b,(path,st,b)
antes={};feito=[]
# 1) PC-01
P1='trocas/qtJ02GZIZ6CQqjVuRyW2';t=get(P1);antes[P1]=json.loads(json.dumps(t))
rep={'11110175','11110176','54315408','17535679','11110683'}
novo=[i for i in t['itens'] if not (str(i.get('espec','')).strip() in rep and not i.get('estoqueId'))]
if len(novo)==len(t['itens'])-5 and any(i.get('estoqueId')=='mIQxkCHvCFRzMD3rM1WY' for i in novo):t['itens']=novo;put(P1,t);feito.append('PC-01 30/10: 5 linhas repetidas retiradas')
else:feito.append('PC-01 30/10: nada alterado (dado diferente do esperado)')
# 2) EH-05
st,eqs=rq('GET','/rest/v1/docs?select=path,data&path=like.equipamentos/*');eh=[e for e in eqs if (e['data'] or {}).get('codigo')=='EH-05'][0]
alvo={'filtro de ar motor secundario':'VOE11110176','elemento filtro racor':'VOE11110683'}
def fix(itens):
    n=0
    for i in itens:
        k=na(i.get('desc'))
        if k in alvo and str(i.get('espec','')).strip()=='11110683':i['espec']=alvo[k];n+=1
    return n
P2='trocas/inf-EH-05-2026-08-29';t=get(P2);antes[P2]=json.loads(json.dumps(t));n=fix(t['itens'])
if n==2:put(P2,t);feito.append('EH-05 29/08: 2 codigos corrigidos')
else:feito.append(f'EH-05 29/08: nada alterado ({n} encontrados)')
P3=eh['path'];e=get(P3);antes[P3]=json.loads(json.dumps(e));n=fix(e.get('itens',[]))
if n==2:put(P3,e);feito.append('EH-05 plano: 2 codigos corrigidos')
else:feito.append(f'EH-05 plano: nada alterado ({n} encontrados)')
json.dump(antes,open('auditoria/corrige-31out-antes.json','w'),indent=1,ensure_ascii=False)
json.dump(feito,open('auditoria/corrige-31out.json','w'),indent=1,ensure_ascii=False);print(feito)
