# Auditoria 2026-10-25 12:46 UTC

7 problema(s)

|Quem|Teste|Resultado|Detalhe|
|-|-|-|-|
|Configuracao|cadastro aberto desligado|**PROBLEMA**|disable_signup=False · autoconfirm=False|
|Configuracao|login por terceiros desligado|ok|nenhum|
|Estranho|criar conta sozinho pela API|ok|status 400|
|Estranho (so chave publica)|ler registros do app|ok|nao conseguiu ler (status 401)|
|Estranho (so chave publica)|ler lista de usuarios (perfis)|ok|nao conseguiu (status 401)|
|Estranho (so chave publica)|gravar registro novo|ok|bloqueado (status 401)|
|Estranho (so chave publica)|alterar registro (doc_update)|ok|bloqueado (status 401)|
|Estranho (so chave publica)|listar fotos|ok|nao listou (status 200)|
|Estranho (so chave publica)|enviar arquivo|ok|bloqueado (status 400)|
|Conta sem papel|ler registros do app|**PROBLEMA**|conseguiu ler (status 200)|
|Conta sem papel|ler lista de usuarios (perfis)|**PROBLEMA**|conseguiu (status 200)|
|Conta sem papel|gravar registro novo|ok|bloqueado (status 403)|
|Conta sem papel|alterar registro (doc_update)|ok|bloqueado (status 500)|
|Conta sem papel|listar fotos|**PROBLEMA**|conseguiu listar (status 200)|
|Conta sem papel|enviar arquivo|ok|bloqueado (status 400)|
|Papel consulta|ler registros do app|ok|conseguiu ler (status 200)|
|Papel consulta|ler lista de usuarios (perfis)|ok|conseguiu (status 200)|
|Papel consulta|gravar registro novo|ok|bloqueado (status 403)|
|Papel consulta|alterar registro (doc_update)|ok|bloqueado (status 500)|
|Papel consulta|mudar o proprio papel para admin|ok|bloqueado|
|Papel consulta|listar fotos|ok|conseguiu listar (status 200)|
|Papel consulta|enviar arquivo|ok|bloqueado (status 400)|
|Papel editor|ler registros do app|ok|conseguiu ler (status 200)|
|Papel editor|ler lista de usuarios (perfis)|ok|conseguiu (status 200)|
|Papel editor|gravar registro novo|**PROBLEMA**|bloqueado (status 403)|
|Papel editor|alterar registro (doc_update)|**PROBLEMA**|bloqueado (status 500)|
|Papel editor|mudar o proprio papel para admin|ok|bloqueado|
|Papel editor|listar fotos|ok|conseguiu listar (status 200)|
|Papel editor|enviar arquivo|**PROBLEMA**|bloqueado (status 400)|
|Geral|ninguem conseguiu virar admin|ok|0|
