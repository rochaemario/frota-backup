#!/usr/bin/env python3
"""Auditoria de seguranca do app Controle de Frota (somente teste; tudo que cria, apaga no fim).
Testa o que conseguiria: (1) um estranho so com a chave publica; (2) uma conta nova criada por fora;
(3) um usuario com papel 'consulta'; (4) um usuario 'editor'. Gera auditoria/relatorio.md."""
import json, os, uuid, urllib.request, urllib.error, datetime
URL='https://uzpoaifuxwojiomxqukf.supabase.co'
ANON=os.environ['ANON_KEY']; SVC=os.environ['SUPABASE_SERVICE_KEY']; B='arquivos'
R=[];LIXO={'docs':set(),'users':set(),'files':set()}
def call(method,path,key,token=None,body=None,raw=None,ctype='application/json',extra=None):
    h={'apikey':key,'Authorization':'Bearer '+(token or key)}
    if extra:h.update(extra)
    data=None
    if raw is not None:data=raw;h['Content-Type']=ctype
    elif body is not None:data=json.dumps(body).encode();h['Content-Type']='application/json'
    rq=urllib.request.Request(URL+path,data=data,headers=h,method=method)
    try:
        with urllib.request.urlopen(rq,timeout=60) as f:t=f.read();return f.status,(json.loads(t) if t and t[:1] in b'[{' else t.decode(errors='ignore'))
    except urllib.error.HTTPError as e:
        t=e.read();
        try:return e.code,json.loads(t)
        except Exception:return e.code,t.decode(errors='ignore')[:200]
def item(grupo,teste,ok,detalhe=''):R.append((grupo,teste,ok,detalhe));print(('OK  ' if ok else 'FALHA ')+grupo+' | '+teste+' | '+detalhe)
def bateria(nome,key,token,pode_ler,pode_gravar,uid=None):
    st,b=call('GET','/rest/v1/docs?select=path&limit=5',key,token);leu=st==200 and isinstance(b,list) and len(b)>0
    item(nome,'ler registros do app',leu==pode_ler,f'{"conseguiu" if leu else "nao conseguiu"} ler (status {st})')
    st,b=call('GET','/rest/v1/perfis?select=email,papel&limit=5',key,token);lp=st==200 and isinstance(b,list) and len(b)>0
    item(nome,'ler lista de usuarios (perfis)',lp==pode_ler,f'{"conseguiu" if lp else "nao conseguiu"} (status {st})')
    p='zz_auditoria/'+uuid.uuid4().hex[:8];LIXO['docs'].add(p)
    st,b=call('POST','/rest/v1/docs',key,token,body={'path':p,'parent':'zz_auditoria','data':{'teste':1}},extra={'Prefer':'return=minimal'})
    gr=st in(200,201,204);item(nome,'gravar registro novo',gr==pode_gravar,f'{"conseguiu" if gr else "bloqueado"} (status {st})')
    st,b=call('POST','/rest/v1/rpc/doc_update',key,token,body={'p_path':'config/equipe','p_patch':{}})
    up=st in(200,204);item(nome,'alterar registro (doc_update)',up==pode_gravar,f'{"conseguiu" if up else "bloqueado"} (status {st})')
    if uid:
        call('PATCH','/rest/v1/perfis?user_id=eq.'+uid,key,token,body={'papel':'admin'},extra={'Prefer':'return=minimal'})
        st,b=call('GET','/rest/v1/perfis?select=papel&user_id=eq.'+uid,SVC);virou=isinstance(b,list) and b and b[0].get('papel')=='admin'
        item(nome,'mudar o proprio papel para admin',not virou,'conseguiu' if virou else 'bloqueado')
    st,b=call('POST',f'/storage/v1/object/list/{B}',key,token,body={'prefix':'','limit':3});lf=st==200 and isinstance(b,list) and len(b)>0
    item(nome,'listar fotos',not lf or pode_ler,f'{"conseguiu listar" if lf else "nao listou"} (status {st})')
    fn='zz_auditoria_'+uuid.uuid4().hex[:8]+'.txt';LIXO['files'].add(fn)
    st,b=call('POST',f'/storage/v1/object/{B}/{fn}',key,token,raw=b'teste',ctype='text/plain')
    su=st in(200,201);item(nome,'enviar arquivo',su==pode_gravar,f'{"conseguiu" if su else "bloqueado"} (status {st})')
def usuario(papel):
    em=f'auditoria+{uuid.uuid4().hex[:8]}@example.com';pw=uuid.uuid4().hex+'Aa1!'
    st,u=call('POST','/auth/v1/admin/users',SVC,body={'email':em,'password':pw,'email_confirm':True});uid=u.get('id') if isinstance(u,dict) else None
    if not uid:return None,None
    LIXO['users'].add(uid)
    if papel:call('POST','/rest/v1/perfis',SVC,body={'user_id':uid,'email':em,'nome':'Auditoria','papel':papel},extra={'Prefer':'return=minimal'})
    st,t=call('POST','/auth/v1/token?grant_type=password',ANON,body={'email':em,'password':pw})
    return (t.get('access_token') if isinstance(t,dict) else None),uid
def main():
    st,s=call('GET','/auth/v1/settings',ANON)
    if isinstance(s,dict):
        item('Configuracao','cadastro aberto desligado',bool(s.get('disable_signup')),f"disable_signup={s.get('disable_signup')} · autoconfirm={s.get('mailer_autoconfirm')}")
        ext=[k for k,v in (s.get('external') or {}).items() if v and k!='email'];item('Configuracao','login por terceiros desligado',not ext,', '.join(ext) or 'nenhum')
    # cadastro de verdade por fora (o que um estranho tentaria)
    em=f'auditoria+{uuid.uuid4().hex[:8]}@example.com'
    st,b=call('POST','/auth/v1/signup',ANON,body={'email':em,'password':uuid.uuid4().hex+'Aa1!'})
    criou=st==200 and isinstance(b,dict) and (b.get('id') or (b.get('user') or {}).get('id'))
    if criou:LIXO['users'].add(b.get('id') or b['user']['id'])
    item('Estranho','criar conta sozinho pela API',not criou,f'status {st}')
    tok_est=b.get('access_token') if criou and isinstance(b,dict) else None
    bateria('Estranho (so chave publica)',ANON,None,False,False)
    if tok_est:bateria('Estranho com conta criada por fora',ANON,tok_est,False,False)
    t,u=usuario(None)
    if t:bateria('Conta sem papel',ANON,t,False,False)
    t,u=usuario('consulta')
    if t:bateria('Papel consulta',ANON,t,True,False,u)
    t,u=usuario('editor')
    if t:bateria('Papel editor',ANON,t,True,True,u)
    # promocao de papel: confere se alguma conta de teste virou admin
    st,b=call('GET','/rest/v1/perfis?select=papel,email&email=like.auditoria*',SVC)
    adm=[x for x in (b if isinstance(b,list) else []) if x.get('papel')=='admin'];item('Geral','ninguem conseguiu virar admin',not adm,str(len(adm)))
    # limpeza
    for p in LIXO['docs']:call('DELETE','/rest/v1/docs?path=eq.'+urllib.parse.quote(p),SVC)
    for fn in LIXO['files']:call('DELETE',f'/storage/v1/object/{B}/{fn}',SVC)
    call('DELETE','/rest/v1/perfis?email=like.auditoria*',SVC)
    for u in LIXO['users']:call('DELETE','/auth/v1/admin/users/'+u,SVC)
    falhas=[r for r in R if not r[2]]
    with open('auditoria/relatorio.md','w') as f:
        f.write(f'# Auditoria {datetime.datetime.utcnow():%Y-%m-%d %H:%M} UTC\n\n{len(falhas)} problema(s)\n\n|Quem|Teste|Resultado|Detalhe|\n|-|-|-|-|\n')
        for g,t,o,d in R:f.write(f'|{g}|{t}|{"ok" if o else "**PROBLEMA**"}|{d}|\n')
import urllib.parse
if __name__=='__main__':main()
