// Controle de Frota · acesso do mecanico sem e-mail e sem senha.
// acao "entrar": o mecanico abre o link (uid + codigo de uso unico) e recebe uma senha nova so para entrar; o codigo deixa de valer.
// acoes do administrador: "criar" (novo mecanico + codigo), "codigo" (novo codigo; o anterior deixa de valer), "ativo" (ativar/desativar).
import { createClient } from "jsr:@supabase/supabase-js@2";
const U = Deno.env.get("SUPABASE_URL")!, K = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
const cors = { "Access-Control-Allow-Origin": "*", "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type", "Access-Control-Allow-Methods": "POST, OPTIONS" };
const J = (b: unknown, s = 200) => new Response(JSON.stringify(b), { status: s, headers: { ...cors, "Content-Type": "application/json" } });
const sha = async (t: string) => [...new Uint8Array(await crypto.subtle.digest("SHA-256", new TextEncoder().encode(t)))].map((b) => b.toString(16).padStart(2, "0")).join("");
const rnd = (n: number) => { const a = new Uint8Array(n); crypto.getRandomValues(a); return [...a].map((b) => "abcdefghijkmnpqrstuvwxyz23456789"[b % 32]).join(""); };
Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: cors });
  const adm = createClient(U, K, { auth: { persistSession: false, autoRefreshToken: false } });
  let b: Record<string, unknown> = {};
  try { b = await req.json(); } catch { /* vazio */ }
  const acao = String(b.acao || "");
  if (acao === "entrar") {
    const uid = String(b.uid || ""), codigo = String(b.codigo || "");
    if (!uid || !codigo) return J({ erro: "codigo" }, 400);
    const { data, error } = await adm.auth.admin.getUserById(uid);
    const u = data?.user;
    if (error || !u) return J({ erro: "codigo" }, 403);
    const m = (u.app_metadata || {}) as Record<string, unknown>;
    if (!m.mec || m.mec_off || !m.mec_hash || m.mec_hash !== await sha(codigo)) return J({ erro: "codigo" }, 403);
    const senha = rnd(40);
    const r = await adm.auth.admin.updateUserById(uid, { password: senha, app_metadata: { ...m, mec_hash: null, mec_usado: Date.now() } });
    if (r.error) return J({ erro: "falha" }, 500);
    return J({ email: u.email, senha });
  }
  // daqui para baixo, so o administrador
  const tok = (req.headers.get("Authorization") || "").replace(/^Bearer\s+/i, "");
  const { data: eu } = await adm.auth.getUser(tok);
  if (!eu?.user) return J({ erro: "login" }, 401);
  const { data: pf } = await adm.from("perfis").select("papel").eq("user_id", eu.user.id).maybeSingle();
  if (!pf || pf.papel !== "admin") return J({ erro: "admin" }, 403);
  if (acao === "criar") {
    const nome = String(b.nome || "").trim().slice(0, 60);
    if (!nome) return J({ erro: "nome" }, 400);
    const email = `mec-${rnd(10)}@mecanico.frota`, codigo = rnd(24);
    const { data, error } = await adm.auth.admin.createUser({ email, password: rnd(40), email_confirm: true, app_metadata: { mec: true, mec_hash: await sha(codigo) }, user_metadata: { nome } });
    if (error || !data?.user) return J({ erro: error?.message || "falha" }, 500);
    const e2 = await adm.from("perfis").upsert({ user_id: data.user.id, email, nome, papel: "mecanico" });
    if (e2.error) return J({ erro: e2.error.message }, 500);
    return J({ uid: data.user.id, codigo });
  }
  const uid = String(b.uid || "");
  const { data: alvo } = await adm.auth.admin.getUserById(uid);
  const am = (alvo?.user?.app_metadata || {}) as Record<string, unknown>;
  if (!alvo?.user || !am.mec) return J({ erro: "mecanico" }, 404);
  if (acao === "codigo") {
    const codigo = rnd(24);
    const r = await adm.auth.admin.updateUserById(uid, { app_metadata: { ...am, mec_hash: await sha(codigo) } });
    if (r.error) return J({ erro: "falha" }, 500);
    return J({ uid, codigo });
  }
  if (acao === "ativo") {
    const on = !!b.ativo;
    const r = await adm.auth.admin.updateUserById(uid, { ban_duration: on ? "none" : "876000h", app_metadata: { ...am, mec_off: !on, ...(on ? {} : { mec_hash: null }) } });
    if (r.error) return J({ erro: "falha" }, 500);
    await adm.from("perfis").update({ papel: on ? "mecanico" : null }).eq("user_id", uid);
    return J({ ok: true });
  }
  return J({ erro: "acao" }, 400);
});
