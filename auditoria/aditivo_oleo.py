#!/usr/bin/env python3
"""05/11/2026 (pedido do Mario): B12 vira Aditivo / Oleo lubrificante (estoque e planos); oleo do plano com tipo errado vira Oleo;
oleos de mesma referencia no plano: fica o mais recente, o anterior sai. Copia de antes em auditoria/aditivo-oleo-antes.json."""
import json,os,re,re,unicodedata,urllib.request,urllib.error,urllib.parse,datetime
URL='https://uzpoaifuxwojiomxqukf.supabase.co';K=os.environ['SUPABASE_SERVICE_KEY'];H={'apikey':K,'Authorization':'Bearer '+K}
def rq(m,p,data=None):
    h=dict(H);d=None
    if data is not None:d=json.dumps(data).encode();h['Content-Type']='application/json';h['Prefer']='return=representation'
    r=urllib.request.Request(URL+p,data=d,headers=h,method=m)
    with urllib.request.urlopen(r,timeout=60) as f:b=f.read();return f.status,json.loads(b) if b else None
na=lambda s:unicodedata.normalize('NFD',str(s or '')).encode('ascii','ignore').decode().lower()
ar=lambda n:(lambda s:'respiro' not in s and re.search(r'filtro (de |do |da )?ar\b|ar condicionado',s))(na(n))
na=lambda v:unicodedata.normalize('NFD',str(v or '')).encode('ascii','ignore').decode().upper()
nz=lambda v:re.sub(r'[^A-Z0-9]','',na(v))
bard=lambda x:'BARDAHL' in na(x.get('desc'))+' '+na(x.get('ref'))
st,est=rq('GET','/rest/v1/docs?select=path,data&path=like.estoque/*')
S={r['path'].split('/',1)[1]:r['data'] or {} for r in est}
antes={};feito=[]
def patch(path,d):
    st2,b=rq('PATCH','/rest/v1/docs?path=eq.'+urllib.parse.quote(path,safe=''),{'data':d,'updated_at':datetime.datetime.utcnow().isoformat()+'Z'});return st2==200
for r in est:
    d=r['data'] or {}
    if bard(d) and not (d.get('tipo')=='Aditivo' and d.get('sub')=='Oleo lubrificante'):
        antes[r['path']]=json.loads(json.dumps(d));d['tipo']='Aditivo';d['sub']='Oleo lubrificante';S[r['path'].split('/',1)[1]]=d
        feito.append({'estoque':d.get('desc'),'tipo':'Aditivo / Oleo lubrificante','ok':patch(r['path'],d)})
def sk(i):return S.get(i.get('estoqueId') or '') or {}
def ehAd(i):return i.get('tipo')=='Aditivo' or sk(i).get('tipo')=='Aditivo'
def ehOl(i):return not ehAd(i) and (i.get('tipo')=='oleo' or sk(i).get('tipo')=='oleo')
def ref(i):
    k=sk(i);t=na(' '.join(str(x or '') for x in [i.get('desc'),i.get('espec'),k.get('desc'),k.get('ref'),k.get('codigo')]))
    m=re.search(r'\b(\d{1,2})\s*W\s*-?\s*(\d{2,3})\b',t)
    if m:return m.group(1)+'W'+m.group(2)
    m=re.search(r'\bSAE\s*-?\s*(\d{2,3})\b',t)
    if m:return 'SAE'+m.group(1)
    c=nz(k.get('codigo') or k.get('ref') or '');return 'C:'+c if c else ''
st,rows=rq('GET','/rest/v1/docs?select=path,data&path=like.equipamentos/*')
for r in rows:
    d=r['data'] or {};its=d.get('itens') or [];o=json.loads(json.dumps(d));log=[]
    for i in its:
        if bard(i) and not (i.get('tipo')=='Aditivo' and i.get('sub')=='Oleo lubrificante'):i['tipo']='Aditivo';i['sub']='Oleo lubrificante';log.append(i.get('desc')+' -> Aditivo / Oleo lubrificante')
        if i.get('tipo')!='oleo' and not ehAd(i) and sk(i).get('tipo')=='oleo':
            i['tipo']='oleo';log.append(i.get('desc')+' -> tipo Oleo')
            if na(i.get('espec')).strip()=='OLEO':
                m=re.search(r'\b(\d{1,2})\s*W\s*-?\s*(\d{2,3})\b',na(i.get('desc')))
                if m:i['espec']=m.group(1)+'W-'+m.group(2);log.append(i.get('desc')+' -> espec '+i['espec'])
    g={}
    for i in its:
        if ehOl(i) and ref(i):g.setdefault(ref(i),[]).append(i)
    fora=[]
    for rf,l in g.items():
        if len(l)<2:continue
        l.sort(key=lambda i:((i.get('ultimaData') or ''),float(i.get('ultimaH') or 0)))
        novo=l[-1]
        for v in l[:-1]:
            if novo.get('ivSel') in ('',None) and v.get('ivSel') not in ('',None):novo['ivSel']=v['ivSel'];novo['ivDef']=True
            fora.append(v);log.append(v.get('desc')+' sai do plano (substituido por '+novo.get('desc')+')')
    if not log:continue
    d['itens']=[i for i in its if i not in fora]
    antes[r['path']]=o;feito.append({'equip':d.get('codigo'),'mud':log,'ok':patch(r['path'],d)})
json.dump(antes,open('auditoria/aditivo-oleo-antes.json','w'),indent=1,ensure_ascii=False)
json.dump(feito,open('auditoria/aditivo-oleo.json','w'),indent=1,ensure_ascii=False);print(json.dumps(feito,ensure_ascii=False,indent=1))
