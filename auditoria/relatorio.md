# Auditoria 2026-10-25 12:54 UTC

3 problema(s)

|Quem|Teste|Resultado|Detalhe|
|-|-|-|-|
|Configuracao|cadastro aberto desligado|ok|disable_signup=True · autoconfirm=False|
|Configuracao|login por terceiros desligado|ok|nenhum|
|Estranho|criar conta sozinho pela API|ok|status 422 {'code': 422, 'error_code': 'signup_disabled', 'msg': 'Signups not allowed for this instance'}|
|Estranho (so chave publica)|ler registros do app|ok|nao conseguiu ler (status 401)|
|Estranho (so chave publica)|ler lista de usuarios (perfis)|ok|nao conseguiu (status 401)|
|Estranho (so chave publica)|gravar registro novo|ok|bloqueado (status 401 {'code': '42501', 'details': None, 'hint': 'Grant the required privileges to the current r)|
|Estranho (so chave publica)|alterar registro (doc_update)|ok|bloqueado (status 401 {'code': '42501', 'details': None, 'hint': None, 'message': 'permission denied for functio)|
|Estranho (so chave publica)|listar fotos|ok|nao listou (status 200)|
|Estranho (so chave publica)|enviar arquivo|ok|bloqueado (status 400 {'statusCode': '403', 'error': 'Unauthorized', 'message': 'new row violates row-level secu)|
|Preparo|perfil criado sozinho para conta nova|ok|[{'user_id': 'c5647e0e-5418-41e0-8ce1-edd63a9f5540', 'email': 'auditoria+ded2b55a@example.com', 'nome': 'auditoria+ded2b55a', 'papel': 'consulta', 'criado': '2026-10-25T12:54:24.917787+00:00'}]|
|Conta sem papel|ler registros do app|**PROBLEMA**|conseguiu ler (status 200)|
|Conta sem papel|ler lista de usuarios (perfis)|**PROBLEMA**|conseguiu (status 200)|
|Conta sem papel|gravar registro novo|ok|bloqueado (status 403 {'code': '42501', 'details': None, 'hint': None, 'message': 'new row violates row-level se)|
|Conta sem papel|alterar registro (doc_update)|ok|bloqueado (status 500 {'code': 'P0002', 'details': None, 'hint': None, 'message': 'not_found'})|
|Conta sem papel|listar fotos|**PROBLEMA**|conseguiu listar (status 200)|
|Conta sem papel|enviar arquivo|ok|bloqueado (status 400 {'statusCode': '403', 'error': 'Unauthorized', 'message': 'new row violates row-level secu)|
|Preparo|perfil de teste consulta|ok|200 |
|Papel consulta|ler registros do app|ok|conseguiu ler (status 200)|
|Papel consulta|ler lista de usuarios (perfis)|ok|conseguiu (status 200)|
|Papel consulta|gravar registro novo|ok|bloqueado (status 403 {'code': '42501', 'details': None, 'hint': None, 'message': 'new row violates row-level se)|
|Papel consulta|alterar registro (doc_update)|ok|bloqueado (status 500 {'code': 'P0002', 'details': None, 'hint': None, 'message': 'not_found'})|
|Papel consulta|mudar o proprio papel para admin|ok|bloqueado|
|Papel consulta|listar fotos|ok|conseguiu listar (status 200)|
|Papel consulta|enviar arquivo|ok|bloqueado (status 400 {'statusCode': '403', 'error': 'Unauthorized', 'message': 'new row violates row-level secu)|
|Preparo|perfil de teste editor|ok|200 |
|Papel editor|ler registros do app|ok|conseguiu ler (status 200)|
|Papel editor|ler lista de usuarios (perfis)|ok|conseguiu (status 200)|
|Papel editor|gravar registro novo|ok|conseguiu (status 201 )|
|Papel editor|alterar registro (doc_update)|ok|conseguiu (status 200 )|
|Papel editor|mudar o proprio papel para admin|ok|bloqueado|
|Papel editor|listar fotos|ok|conseguiu listar (status 200)|
|Papel editor|enviar arquivo|ok|conseguiu (status 200 )|
|Geral|ninguem conseguiu virar admin|ok|0|
