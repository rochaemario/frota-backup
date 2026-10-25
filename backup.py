#!/usr/bin/env python3
"""Backup noturno do app Controle de Frota (Supabase).
- dados/docs.json: todos os registros do app (tabela docs), um por linha, ordenados
- dados/perfis.json: usuarios e papeis (sem senhas; senhas ficam no Supabase Auth)
- fotos/: todas as fotos e documentos do bucket; so baixa o que ainda nao tem
Cada execucao vira um commit: o historico do git guarda todas as versoes dos dados.
A chave service_role vem do segredo SUPABASE_SERVICE_KEY e nunca e gravada."""
import json, os, sys, urllib.request, urllib.parse

URL = os.environ.get('SUPABASE_URL', 'https://uzpoaifuxwojiomxqukf.supabase.co').rstrip('/')
KEY = os.environ['SUPABASE_SERVICE_KEY']
BUCKET = os.environ.get('SUPABASE_BUCKET', 'arquivos')
BUCKET_DOC = 'documentos'  # documentos privados (veiculo, nota fiscal)
H = {'apikey': KEY, 'Authorization': 'Bearer ' + KEY}

def req(path, data=None, method=None, raw=False):
    r = urllib.request.Request(URL + path, headers=dict(H, **({'Content-Type': 'application/json'} if data is not None else {})),
                               data=json.dumps(data).encode() if data is not None else None, method=method)
    with urllib.request.urlopen(r, timeout=120) as f:
        b = f.read()
    return b if raw else json.loads(b)

def tabela(nome, ordem):
    out, off = [], 0
    while True:
        lote = req(f'/rest/v1/{nome}?select=*&order={ordem}&offset={off}&limit=1000')
        out += lote
        if len(lote) < 1000: return out
        off += 1000

def arquivos(prefix='', bucket=None):
    bucket = bucket or BUCKET
    out, off = [], 0
    while True:
        lote = req(f'/storage/v1/object/list/{bucket}', {'prefix': prefix, 'limit': 1000, 'offset': off, 'sortBy': {'column': 'name', 'order': 'asc'}})
        for o in lote:
            nome = (prefix + '/' if prefix else '') + o['name']
            if o.get('id') is None: out += arquivos(nome, bucket)      # pasta
            else: out.append(nome)
        if len(lote) < 1000: return out
        off += 1000

def main():
    os.makedirs('dados', exist_ok=True); os.makedirs('fotos', exist_ok=True)
    docs = tabela('docs', 'path')
    with open('dados/docs.json', 'w', encoding='utf-8') as f:
        f.write('[\n' + ',\n'.join(json.dumps(d, ensure_ascii=False, sort_keys=True) for d in docs) + '\n]\n')
    try:
        perfis = tabela('perfis', 'id')
        json.dump(perfis, open('dados/perfis.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1, sort_keys=True)
    except Exception as e:
        print('perfis: nao copiado:', e)
    nomes = arquivos()
    novos = 0
    for n in nomes:
        dst = os.path.join('fotos', n)
        if os.path.exists(dst): continue
        os.makedirs(os.path.dirname(dst) or 'fotos', exist_ok=True)
        b = req(f'/storage/v1/object/{BUCKET}/' + urllib.parse.quote(n), raw=True)
        open(dst, 'wb').write(b); novos += 1
    ndoc = 0
    try:
        for n in arquivos('', BUCKET_DOC):
            dst = os.path.join('documentos', n); ndoc += 1
            if os.path.exists(dst): continue
            os.makedirs(os.path.dirname(dst) or 'documentos', exist_ok=True)
            open(dst, 'wb').write(req(f'/storage/v1/object/{BUCKET_DOC}/' + urllib.parse.quote(n), raw=True))
    except Exception as e:
        print('documentos: nao copiado:', e)
    resumo = {'registros': len(docs), 'arquivos': len(nomes), 'arquivos_novos': novos, 'documentos': ndoc}
    json.dump(resumo, open('dados/resumo.json', 'w'), indent=1)
    print(resumo)
    if not docs: sys.exit('nenhum registro lido: backup suspeito, abortando')

if __name__ == '__main__':
    main()
