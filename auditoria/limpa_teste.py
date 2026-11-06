#!/usr/bin/env python3
"""05/11/2026 (pedido do Mario): limpar a versao de teste para testes reais.
Apaga as OS de teste, os eventos e avisos de teste, e os mecanicos de teste sem login.
So mexe em registros com prefixo teste/. Copia de antes em auditoria/limpa-teste-antes.json.
APLICAR=1 apaga; sem isso so lista."""
import json,os,urllib.request,urllib.parse,urllib.error
URL='https://uzpoaifuxwojiomxqukf.supabase.co';K=os.environ['SUPABASE_SERVICE_KEY'];H={'apikey':K,'Authorization':'Bearer '+K}
AP=os.environ.get('APLICAR')=='1'
def rq(m,p,data=None,prefer='return=representation'):
    h=dict(H);d=None
    if data is not None:d=json.dumps(data).encode();h['Content-Type']='application/json'
    h['Prefer']=prefer
    r=urllib.request.Request(URL+p,data=d,headers=h,method=m)
    with urllib.request.urlopen(r,timeout=60) as f:b=f.read();return f.status,json.loads(b) if b else None
def lista(pref):
    st,rows=rq('GET','/rest/v1/docs?select=path,data&path=like.'+urllib.parse.quote(pref+'*',safe='*'));return rows
os_=lista('teste/os/');ose=lista('teste/ose/');av=lista('teste/avisos/')
cm=lista('teste/config/mecanicos');mecs=(cm[0]['data'] or {}).get('lista',[]) if cm else []
fora=list(mecs);fica=[]  # 06/11: sai todos, inclusive os com login
out={'aplicado':AP,'os':len(os_),'eventos':len(ose),'avisos':len(av),
  'osNums':sorted((r['data'] or {}).get('num') or 0 for r in os_),
  'mecanicos_sai':[m.get('nome') for m in fora],'mecanicos_ficam':[m.get('nome') for m in fica]}
print(json.dumps(out,ensure_ascii=False,indent=1))
if AP:
    json.dump({'os':os_,'ose':ose,'avisos':av,'mecanicos':cm},open('auditoria/limpa-teste-antes.json','w'),ensure_ascii=False)
    for pref in ('teste/ose/','teste/os/','teste/avisos/'):
        st,_=rq('DELETE','/rest/v1/docs?path=like.'+urllib.parse.quote(pref+'*',safe='*'),prefer='return=minimal');print('apagou',pref,st)
    for m in fora:
        if m.get('real'):
            u=m['uid'];st,_=rq('DELETE','/rest/v1/perfis?user_id=eq.'+u,prefer='return=minimal');print('perfil',m.get('nome'),st)
            try:st,_=rq('DELETE','/auth/v1/admin/users/'+u,prefer='return=minimal');print('login apagado',m.get('nome'),st)
            except urllib.error.HTTPError as e:print('login',m.get('nome'),e.code,e.read()[:200])
    if cm:
        st,_=rq('PATCH','/rest/v1/docs?path=eq.'+urllib.parse.quote('teste/config/mecanicos',safe=''),{'data':{'lista':fica}});print('mecanicos',st)
    print('restam',len(lista('teste/os/')),len(lista('teste/ose/')))
json.dump(out,open('auditoria/limpa-teste.json','w'),ensure_ascii=False,indent=1)
