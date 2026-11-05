#!/usr/bin/env python3
"""05/11/2026 (pedido do Mario): cada item do plano passa a ter o proprio intervalo. Itens sem intervalo recebem o intervalo atual do equipamento.
Sob avaliacao e intervalos ja escolhidos ficam. Copia de antes em auditoria/iv-itens-antes.json."""
import json,os,re,unicodedata,urllib.request,urllib.error,urllib.parse,datetime
URL='https://uzpoaifuxwojiomxqukf.supabase.co';K=os.environ['SUPABASE_SERVICE_KEY'];H={'apikey':K,'Authorization':'Bearer '+K}
def rq(m,p,data=None):
    h=dict(H);d=None
    if data is not None:d=json.dumps(data).encode();h['Content-Type']='application/json';h['Prefer']='return=representation'
    r=urllib.request.Request(URL+p,data=d,headers=h,method=m)
    with urllib.request.urlopen(r,timeout=60) as f:b=f.read();return f.status,json.loads(b) if b else None
na=lambda s:unicodedata.normalize('NFD',str(s or '')).encode('ascii','ignore').decode().lower()
ar=lambda n:(lambda s:'respiro' not in s and re.search(r'filtro (de |do |da )?ar\b|ar condicionado',s))(na(n))
st,rows=rq('GET','/rest/v1/docs?select=path,data&path=like.equipamentos/*')
antes={};feito=[]
for r in rows:
    d=r['data'] or {};its=d.get('itens') or [];iv=d.get('intervaloPrev')
    try:iv=float(iv)
    except Exception:iv=0
    if not iv:continue
    iv=int(iv) if iv==int(iv) else iv
    mud=[i for i in its if i.get('ivSel') in ('',None)]
    if not mud:continue
    antes[r['path']]=json.loads(json.dumps(d))
    for i in mud:i['ivSel']=iv;i['ivDef']=True
    st2,b=rq('PATCH','/rest/v1/docs?path=eq.'+urllib.parse.quote(r['path'],safe=''),{'data':d,'updated_at':datetime.datetime.utcnow().isoformat()+'Z'})
    feito.append({'equip':d.get('codigo'),'intervalo':iv,'itens':len(mud),'ok':st2==200})
json.dump(antes,open('auditoria/iv-itens-antes.json','w'),indent=1,ensure_ascii=False)
json.dump(feito,open('auditoria/iv-itens.json','w'),indent=1,ensure_ascii=False);print(json.dumps(feito,ensure_ascii=False))
