// Controle de Frota · acesso do mecanico sem e-mail e sem senha.
// acoes do mecanico: "pin_entrar" (matricula + senha de 6 numeros), "pin_def" (cria/troca a senha, ja conectado).
// acao "entrar": o mecanico abre o link (uid + codigo de uso unico) e recebe uma senha nova so para entrar; o codigo deixa de valer.
// acoes do administrador: "criar" (novo mecanico + codigo), "codigo" (novo codigo; o anterior deixa de valer), "ativo" (ativar/desativar),
// "estado" (ja entrou? QR esperando?), "apagar" (excluir o acesso; o app so oferece para quem nao tem lancamentos).
import { createClient } from "jsr:@supabase/supabase-js@2";
const U = Deno.env.get("SUPABASE_URL")!, K = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;
const cors = { "Access-Control-Allow-Origin": "*", "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type", "Access-Control-Allow-Methods": "POST, OPTIONS" };
const J = (b: unknown, s = 200) => new Response(JSON.stringify(b), { status: s, headers: { ...cors, "Content-Type": "application/json" } });
const sha = async (t: string) => [...new Uint8Array(await crypto.subtle.digest("SHA-256", new TextEncoder().encode(t)))].map((b) => b.toString(16).padStart(2, "0")).join("");
const rnd = (n: number) => { const a = new Uint8Array(n); crypto.getRandomValues(a); return [...a].map((b) => "abcdefghijkmnpqrstuvwxyz23456789"[b % 32]).join(""); };
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
Deno.serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: cors });
  try { return await trata(req); } catch (e) { return J({ erro: "falha", msg: String((e as Error)?.message || e) }, 500); }
});
async function trata(req: Request): Promise<Response> {
  const adm = createClient(U, K, { auth: { persistSession: false, autoRefreshToken: false } });
  let b: Record<string, unknown> = {};
  try { b = await req.json(); } catch { /* vazio */ }
  const acao = String(b.acao || "");
  if (acao === "entrar") {
    const uid = String(b.uid || ""), codigo = String(b.codigo || "");
    if (!UUID.test(uid) || !codigo) return J({ erro: "codigo" }, 403);
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
  // entrar com matricula + senha de 6 numeros (o mecanico cria a senha depois de entrar pelo QR)
  if (acao === "pin_entrar") {
    const ns = b.ns === "teste/" ? "teste/" : "", mat = String(b.mat || "").trim(), pin = String(b.pin || "");
    if (!mat || !/^\d{6}$/.test(pin)) return J({ erro: "senha" }, 403);
    const { data: dc } = await adm.from("docs").select("data").eq("path", ns + "config/mecanicos").maybeSingle();
    const lista = ((dc?.data as Record<string, unknown>)?.lista || []) as Record<string, unknown>[];
    const nz = (x: unknown) => String(x || "").trim().replace(/^0+(?=.)/, "").toLowerCase();
    const mm = lista.filter((m) => m.real && nz(m.mat) === nz(mat));
    if (mm.length !== 1) return J({ erro: "senha" }, 403);
    const uid = String(mm[0].uid || "");
    if (!UUID.test(uid)) return J({ erro: "senha" }, 403);
    const { data } = await adm.auth.admin.getUserById(uid);
    const u = data?.user;
    if (!u) return J({ erro: "senha" }, 403);
    const m = (u.app_metadata || {}) as Record<string, unknown>;
    if (!m.mec || m.mec_off || mm[0].ativo === false) return J({ erro: "off" }, 403);
    if (!m.mec_pin) return J({ erro: "sem_senha" }, 403);
    const agora = Date.now();
    if (Number(m.mec_trava || 0) > agora) return J({ erro: "trava", min: Math.ceil((Number(m.mec_trava) - agora) / 60000) }, 429);
    if (m.mec_pin !== await sha(uid + ":" + pin)) {
      const f = Number(m.mec_falha || 0) + 1;
      await adm.auth.admin.updateUserById(uid, { app_metadata: { ...m, mec_falha: f >= 5 ? 0 : f, mec_trava: f >= 5 ? agora + 15 * 60000 : 0 } });
      return J(f >= 5 ? { erro: "trava", min: 15 } : { erro: "senha", resta: 5 - f }, 403);
    }
    const senha = rnd(40);
    const r = await adm.auth.admin.updateUserById(uid, { password: senha, app_metadata: { ...m, mec_falha: 0, mec_trava: 0, mec_usado: agora } });
    if (r.error) return J({ erro: "falha" }, 500);
    return J({ email: u.email, senha });
  }
  // daqui para baixo, so quem esta conectado
  const tok = (req.headers.get("Authorization") || "").replace(/^Bearer\s+/i, "");
  const { data: eu } = await adm.auth.getUser(tok);
  if (!eu?.user) return J({ erro: "login" }, 401);
  // o proprio mecanico cria ou troca a senha de 6 numeros
  if (acao === "pin_def") {
    const pin = String(b.pin || ""), me = eu.user, m = (me.app_metadata || {}) as Record<string, unknown>;
    if (!m.mec || m.mec_off) return J({ erro: "mecanico" }, 403);
    if (!/^\d{6}$/.test(pin) || /^(\d)\1{5}$/.test(pin) || "0123456789".includes(pin) || "9876543210".includes(pin)) return J({ erro: "fraca" }, 400);
    const r = await adm.auth.admin.updateUserById(me.id, { app_metadata: { ...m, mec_pin: await sha(me.id + ":" + pin), mec_falha: 0, mec_trava: 0 } });
    if (r.error) return J({ erro: "falha" }, 500);
    return J({ ok: true });
  }
  // daqui para baixo, so o administrador
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
  if (!UUID.test(uid)) return J({ erro: "mecanico" }, 404);
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
  if (acao === "estado") {
    return J({ usado: !!am.mec_usado, pendente: !!am.mec_hash, off: !!am.mec_off, pin: !!am.mec_pin });
  }
  if (acao === "apagar") {
    await adm.from("perfis").delete().eq("user_id", uid);
    const r = await adm.auth.admin.deleteUser(uid);
    if (r.error) return J({ erro: "falha", msg: r.error.message }, 500);
    return J({ ok: true });
  }
  return J({ erro: "acao" }, 400);
}
