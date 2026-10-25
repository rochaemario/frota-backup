#!/usr/bin/env python3
"""Move os documentos dos equipamentos (veiculo e nota fiscal, com as paginas) do armazenamento publico
'arquivos' para o privado 'documentos'. Mesmo nome de arquivo; so apaga do publico depois de conferir a copia.
Pode rodar mais de uma vez: o que ja foi movido e pulado."""
import json, os, urllib.request, urllib.error, urllib.parse
URL='https://uzpoaifuxwojiomxqukf.supabase.co';K=os.environ['SUPABASE_SERVICE_KEY'];H={'apikey':K,'Authorization':'Bearer '+K}
def rq(m,p,data=None,ct=None,raw=False):
    h=dict(H);d=None
    if data is not None:
        if isinstance(data,(bytes,bytearray)):d=data;h['Content-Type']=ct or 'application/octet-stream'
        else:d=json.dumps(data).encode();h['Content-Type']='application/json'
    if m=='POST' and ct:h['x-upsert']='true'
    r=urllib.request.Request(URL+p,data=d,headers=h,method=m)
    try:
        with urllib.request.urlopen(r,timeout=120) as f:b=f.read();return f.status,(b if raw else (json.loads(b) if b[:1] in b'[{' else b)),f.headers.get('Content-Type')
    except urllib.error.HTTPError as e:return e.code,e.read()[:200],None
ids=set()
st,docs,_=rq('GET','/rest/v1/docs?select=path,data&path=like.equipamentos/*')
for d in docs:
    for k in ('docVeiculo','notaFiscal'):
        v=(d['data'] or {}).get(k)
        if isinstance(v,dict) and v.get('id'):ids.add(v['id']);ids.update(x for x in (v.get('pages') or []) if x)
movidos=pulados=erros=0
for i in sorted(ids):
    q=urllib.parse.quote(i)
    st,b,ct=rq('GET',f'/storage/v1/object/arquivos/{q}',raw=True)
    if st!=200:pulados+=1;continue
    st2,_,_=rq('POST',f'/storage/v1/object/documentos/{q}',b,ct or 'application/octet-stream')
    st3,b3,_=rq('GET',f'/storage/v1/object/documentos/{q}',raw=True)
    if st2 in(200,201) and st3==200 and len(b3)==len(b):
        rq('DELETE',f'/storage/v1/object/arquivos/{q}');movidos+=1
    else:erros+=1;print('erro',i,st2,st3)
res={'documentos':len(ids),'movidos':movidos,'ja_estavam_no_privado':pulados,'erros':erros};print(res)
json.dump(res,open('auditoria/migracao.json','w'),indent=1)
if erros:raise SystemExit(1)
