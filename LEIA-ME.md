# Backup do Controle de Frota

Repositorio **privado**. Todo dia as 02:17 (Manaus) a rotina `Backup noturno` copia do Supabase:
- `dados/docs.json` — todos os registros do app (equipamentos, preventivas, estoque, abastecimentos, avisos...)
- `dados/perfis.json` — usuarios e papeis
- `fotos/` — fotos e documentos (so baixa os novos)

Cada copia e um commit: o historico guarda todas as versoes (qualquer dia pode ser recuperado).
Para rodar agora: aba **Actions** › Backup noturno › **Run workflow**.
A chave fica no segredo `SUPABASE_SERVICE_KEY` (Settings › Secrets and variables › Actions) e nunca aparece no codigo.
