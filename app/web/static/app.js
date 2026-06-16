"use strict";

let TOKEN = "dev-token";
let USUARIO = { email: "dev@local", papel: "curador" };
let TIPOS = [];
let SELECTED_TIPO = null;
let CURRENT_FILE = null;
let CURRENT_ANALYSIS = null;

const EMOJI = {
  saas_mensalidade: "🖥️", marketplace_privado: "🏪",
  compras_free: "🛒", fornecedores: "📦", nda: "🔒",
};

const $ = (s) => document.querySelector(s);
const show = (el) => el && el.classList.remove("hidden");
const hide = (el) => el && el.classList.add("hidden");
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const sevClass = (s) => (s === "média" ? "media" : s);
function fmtTempo(seg) {
  if (seg < 60) return seg.toFixed(1).replace(".", ",") + " s";
  const m = Math.floor(seg / 60), s = Math.round(seg % 60);
  return `${m} min ${s} s`;
}

// ── API ──
async function api(path, opts = {}) {
  const headers = opts.headers || {};
  headers["Authorization"] = "Bearer " + TOKEN;
  const resp = await fetch(path, { ...opts, headers });
  if (!resp.ok) {
    let d = resp.statusText;
    try { d = (await resp.json()).detail || d; } catch (_) {}
    throw new Error(d);
  }
  return resp;
}
const apiJSON = async (p, o) => (await api(p, o)).json();
const jsonBody = (obj) => ({ method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(obj) });
const linhas = (ta) => ta.value.split("\n").map((s) => s.trim()).filter(Boolean);
const tipoNome = (id) => (TIPOS.find((t) => t.id === id) || {}).nome || id;

// ── NAVEGAÇÃO ──
const PAGES = ["nova", "relatorios", "aprendizados", "config"];
function navegar(page) {
  PAGES.forEach((p) => $("#page-" + p).classList.toggle("hidden", p !== page));
  document.querySelectorAll(".nav-item").forEach((el) => el.classList.toggle("active", el.dataset.page === page));
  if (page === "nova") { atualizarStatsERecentes(); }
  if (page === "relatorios") { listarTodas(); }
  if (page === "aprendizados") { carregarTiposApr(); }
}

// ── TIPOS ──
async function carregarTipos() {
  TIPOS = await apiJSON("/tipos");
  const grid = $("#type-grid");
  grid.innerHTML = "";
  TIPOS.forEach((t) => {
    const div = document.createElement("div");
    div.className = "type-option" + (t.ativo ? "" : " disabled");
    div.innerHTML =
      `<div class="type-radio"></div><div class="type-emoji">${EMOJI[t.id] || "📄"}</div>` +
      `<div class="type-text"><div class="type-name">${t.nome}</div><div class="type-desc">${t.descricao}</div></div>` +
      `<span class="type-badge ${t.ativo ? "available" : "soon"}">${t.ativo ? "Disponível" : "Em breve"}</span>`;
    if (t.ativo) div.addEventListener("click", () => selecionarTipo(t.id, div));
    grid.appendChild(div);
  });
  const ativo = TIPOS.find((t) => t.ativo);
  if (ativo) selecionarTipo(ativo.id, grid.querySelector(".type-option:not(.disabled)"));
}

async function selecionarTipo(id, el) {
  SELECTED_TIPO = id;
  document.querySelectorAll("#type-grid .type-option").forEach((e) => e.classList.remove("selected"));
  if (el) el.classList.add("selected");
  try {
    const base = await apiJSON("/tipos/" + id + "/conhecimento");
    const ativas = base.regras.filter((r) => r.ativo);
    $("#checklist-analise").innerHTML = ativas.length
      ? ativas.map((r) => `<li><span class="check-icon">⚖️</span> ${r.topico}</li>`).join("")
      : "<li>—</li>";
    const enriquecidas = ativas.filter((r) => (r.limites||[]).length || (r.flexibilidades||[]).length || (r.correcoes||[]).length);
    $("#checklist-aprendizados").innerHTML = enriquecidas.length
      ? enriquecidas.map((r) => {
          const det = (r.limites[0] || r.flexibilidades[0] || r.correcoes[0] || "");
          return `<li><span class="check-icon">✔️</span> <b>${r.topico}</b>${det ? " — " + det : ""}</li>`;
        }).join("")
      : "<li>Nenhum aprendizado enriquecido ainda.</li>";
  } catch (_) {}
}

// ── UPLOAD ──
function aplicarArquivo(file) {
  const ext = "." + file.name.split(".").pop().toLowerCase();
  if (![".pdf", ".docx"].includes(ext)) { alert("Formato não suportado. Use PDF ou DOCX."); return; }
  CURRENT_FILE = file;
  $("#uploadZone").style.display = "none";
  $("#fileSelected").classList.add("visible");
  $("#fileNameText").textContent = file.name;
  $("#fileSizeText").textContent = (file.size / 1024).toFixed(0) + " KB";
  $("#analyzeBtn").disabled = false;
  hide($("#resultPanel"));
}
function removerArquivo() {
  CURRENT_FILE = null;
  $("#uploadZone").style.display = "";
  $("#fileSelected").classList.remove("visible");
  $("#analyzeBtn").disabled = true;
  $("#fileInput").value = "";
}

// ── ANÁLISE ──
async function analisar() {
  if (!CURRENT_FILE || !SELECTED_TIPO) return;
  const btn = $("#analyzeBtn");
  btn.disabled = true; btn.classList.add("loading"); btn.textContent = "⏳ Analisando…";
  hide($("#resultPanel"));
  $("#progressWrap").classList.add("visible");

  const fd = new FormData();
  fd.append("tipo_id", SELECTED_TIPO);
  fd.append("arquivo", CURRENT_FILE);

  let criada;
  try { criada = await apiJSON("/analises", { method: "POST", body: fd }); }
  catch (e) { return finalizarErro("Erro ao enviar: " + e.message); }

  const id = criada.id;
  const labels = [
    "Extraindo texto do contrato…", "Carregando a base de conhecimento…",
    "Comparando com o padrão Wort…", "Identificando riscos e severidades…", "Gerando relatório…",
  ];
  let i = 0, pct = 12;
  while (true) {
    setProgresso(labels[i % labels.length], Math.min(pct, 92));
    i++; pct += 10;
    await sleep(3000);
    let a;
    try { a = await apiJSON("/analises/" + id); } catch (_) { continue; }
    if (a.status === "concluida") { setProgresso("Concluído!", 100); await sleep(350); return finalizarOk(a); }
    if (a.status === "erro") { return finalizarErro("Falha na análise: " + (a.erro || "")); }
  }
}
function setProgresso(label, pct) { $("#progressLabel").textContent = label; $("#progressFill").style.width = pct + "%"; }
function finalizarOk(a) {
  $("#progressWrap").classList.remove("visible"); $("#progressFill").style.width = "0%";
  const btn = $("#analyzeBtn"); btn.classList.remove("loading"); btn.classList.add("success"); btn.textContent = "✅ Análise concluída";
  renderResultado(a);
  atualizarStatsERecentes();
}
function finalizarErro(msg) {
  $("#progressWrap").classList.remove("visible"); $("#progressFill").style.width = "0%";
  const btn = $("#analyzeBtn"); btn.classList.remove("loading"); btn.disabled = false; btn.textContent = "🔍 Analisar contrato";
  alert(msg);
}

function renderResultado(a) {
  CURRENT_ANALYSIS = a;
  const r = (a.resultado || {});
  const resumo = r.resumo || {};
  const riscos = r.riscos || [];
  $("#resultTitle").textContent = "Análise — " + a.nome_arquivo;
  $("#resultDate").textContent = new Date().toLocaleString("pt-BR", { day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit" });

  const cont = (s) => riscos.filter((x) => x.severidade === s).length;
  $("#cnt-alta").textContent = cont("alta");
  $("#cnt-media").textContent = cont("média");
  $("#cnt-baixa").textContent = cont("baixa");

  const metrics = [];
  if (a.duracao_seg != null) metrics.push(`<span class="metric">⏱ <b>${fmtTempo(a.duracao_seg)}</b> de análise</span>`);
  if (a.tokens_total != null) metrics.push(`<span class="metric">🔢 <b>${a.tokens_total.toLocaleString("pt-BR")}</b> tokens</span>`);
  metrics.push(`<span class="metric">💲 <b>${a.custo_usd != null ? "US$ " + a.custo_usd.toFixed(4).replace(".", ",") : "n/d"}</b></span>`);
  $("#resultMetrics").innerHTML = metrics.join("");

  const campo = (lbl, val) => val && (Array.isArray(val) ? val.length : true)
    ? `<div class="resumo-field"><span class="lbl">${lbl}</span><span class="val">${Array.isArray(val) ? val.join("; ") : val}</span></div>` : "";
  let html = `<div class="result-section"><div class="result-section-title">📄 Resumo</div>` +
    `<div class="resumo-grid">${campo("Título", resumo.titulo)}${campo("Cliente", resumo.cliente)}${campo("Objeto", resumo.objeto)}${campo("Partes", resumo.partes)}${campo("Valores", resumo.valores)}${campo("Prazos", resumo.prazos)}</div>` +
    (resumo.sintese ? `<div class="result-item-body">${resumo.sintese}</div>` : "") + `</div>`;

  [["alta", "🔴 Riscos altos"], ["média", "🟠 Riscos médios"], ["baixa", "🟢 Riscos baixos"]].forEach(([sev, titulo]) => {
    const itens = riscos.filter((x) => x.severidade === sev);
    if (!itens.length) return;
    html += `<div class="result-section"><div class="result-section-title ${sevClass(sev)}">${titulo}</div>` +
      itens.map((x) =>
        `<div class="result-item ${sevClass(x.severidade)}">` +
        (x.clausula ? `<div class="result-item-clause">${x.clausula}</div>` : "") +
        `<div class="result-item-desc">${x.descricao}</div>` +
        (x.recomendacao ? `<div class="result-item-body"><b>Recomendação:</b> ${x.recomendacao}</div>` : "") +
        `</div>`).join("") + `</div>`;
  });
  if (!riscos.length) html += `<div class="empty-state"><p>Nenhum risco relevante identificado.</p></div>`;

  $("#resultBody").innerHTML = html;
  show($("#resultPanel"));
  $("#resultPanel").scrollIntoView({ behavior: "smooth", block: "nearest" });
}

function nomeDoCabecalho(resp, fallback) {
  const cd = resp.headers.get("content-disposition") || "";
  let m = cd.match(/filename\*=UTF-8''([^;]+)/i);
  if (m) return decodeURIComponent(m[1]);
  m = cd.match(/filename="?([^";]+)"?/i);
  return m ? m[1] : fallback;
}

async function baixar(id) {
  const resp = await api("/analises/" + id + "/relatorio");
  const nome = nomeDoCabecalho(resp, "Relatorio.docx");
  const blob = await resp.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a"); a.href = url; a.download = nome; a.click();
  URL.revokeObjectURL(url);
}

// ── LISTAS / STATS ──
function pontoSeveridade(a) {
  const r = (a.resultado || {}).riscos || [];
  if (a.status !== "concluida") return "dot-gray";
  if (r.some((x) => x.severidade === "alta")) return "dot-red";
  if (r.some((x) => x.severidade === "média")) return "dot-orange";
  return "dot-green";
}
function tagSeveridade(a) {
  if (a.status === "erro") return `<span class="report-tag tag-warning">erro</span>`;
  if (a.status !== "concluida") return `<span class="report-tag tag-neutral">${a.status}</span>`;
  const r = (a.resultado || {}).riscos || [];
  const altos = r.filter((x) => x.severidade === "alta").length;
  if (altos) return `<span class="report-tag tag-critical">${altos} alto(s)</span>`;
  const med = r.filter((x) => x.severidade === "média").length;
  if (med) return `<span class="report-tag tag-warning">${med} médio(s)</span>`;
  return `<span class="report-tag tag-ok">sem riscos altos</span>`;
}
function linhaRelatorio(a) {
  const div = document.createElement("div");
  div.className = "report-row";
  div.innerHTML =
    `<div class="report-severity-dot ${pontoSeveridade(a)}"></div>` +
    `<div class="report-body"><div class="report-client-name">${a.nome_arquivo}</div>` +
    `<div class="report-meta-row">${tipoNome(a.tipo_id)} • ${a.status}</div></div>` +
    tagSeveridade(a) +
    (a.tem_relatorio ? `<span class="report-link" data-dl="${a.id}">⬇️ Baixar</span>` : "");
  const dl = div.querySelector("[data-dl]");
  if (dl) dl.addEventListener("click", () => baixar(dl.dataset.dl));
  return div;
}

async function atualizarStatsERecentes() {
  let lista = [];
  try { lista = await apiJSON("/analises"); } catch (_) { return; }
  $("#stat-total").textContent = lista.length;
  const altos = lista.reduce((s, a) => s + (((a.resultado || {}).riscos || []).filter((x) => x.severidade === "alta").length), 0);
  $("#stat-criticos").textContent = altos;
  try {
    const ativo = TIPOS.find((t) => t.ativo);
    if (ativo) {
      const base = await apiJSON("/tipos/" + ativo.id + "/conhecimento");
      $("#stat-aprendizados").textContent = base.regras.filter((r) => r.ativo).length;
    }
  } catch (_) {}
  const badge = $("#badge-relatorios");
  if (lista.length) { badge.textContent = lista.length; show(badge); } else hide(badge);
  const rec = $("#recent-list"); rec.innerHTML = "";
  if (!lista.length) { rec.innerHTML = `<div class="empty-state"><div class="empty-icon">📭</div><p>Nenhuma análise ainda.</p></div>`; return; }
  lista.slice(0, 4).forEach((a) => rec.appendChild(linhaRelatorio(a)));
}

async function listarTodas() {
  const cont = $("#all-list"); cont.innerHTML = "";
  let lista = [];
  try { lista = await apiJSON("/analises"); } catch (_) {}
  if (!lista.length) { cont.innerHTML = `<div class="empty-state"><div class="empty-icon">📭</div><p>Nenhuma análise ainda.</p></div>`; return; }
  lista.forEach((a) => cont.appendChild(linhaRelatorio(a)));
}

// ── APRENDIZADOS ──
async function carregarTiposApr() {
  const sel = $("#apr-tipo");
  if (!sel.options.length) {
    TIPOS.filter((t) => t.ativo).forEach((t) => {
      const o = document.createElement("option"); o.value = t.id; o.textContent = t.nome; sel.appendChild(o);
    });
  }
  if (sel.value) carregarBase();
}
let BASE_REGRAS = [];
let EDITANDO_ID = null;

async function carregarBase() {
  const tipo = $("#apr-tipo").value;
  if (!tipo) return;
  const base = await apiJSON("/tipos/" + tipo + "/conhecimento");
  const ativas = base.regras.filter((r) => r.ativo);
  BASE_REGRAS = ativas;
  $("#apr-info").textContent = `${ativas.length} regra(s) ativa(s) · versão ${base.versao}` + (base.contrato_padrao ? " · contrato padrão definido" : "");
  const cont = $("#regras-list"); cont.innerHTML = "";
  ativas.forEach((r) => {
    const row = document.createElement("div");
    row.className = "rule-row";
    row.innerHTML =
      `<div class="rule-topico">${r.topico}</div>` +
      `<span class="sev-pill ${sevClass(r.severidade)}">${r.severidade}</span>` +
      `<span class="origem-pill">${r.origem}</span>` +
      `<span class="report-link" data-edit="${r.id}">editar</span>` +
      `<span class="report-link" data-off="${r.id}">remover</span>`;
    const ed = row.querySelector("[data-edit]");
    if (ed) ed.addEventListener("click", () => iniciarEdicao(ed.dataset.edit));
    const off = row.querySelector("[data-off]");
    if (off) off.addEventListener("click", () => desativarRegra(tipo, off.dataset.off));
    cont.appendChild(row);
  });
  if (!ativas.length) cont.innerHTML = `<div class="empty-state"><p>Base vazia.</p></div>`;
}

function iniciarEdicao(id) {
  const r = BASE_REGRAS.find((x) => x.id === id);
  if (!r) return;
  EDITANDO_ID = id;
  $("#r-topico").value = r.topico || "";
  $("#r-texto").value = r.texto_padrao || "";
  $("#r-limites").value = (r.limites || []).join("\n");
  $("#r-flex").value = (r.flexibilidades || []).join("\n");
  $("#r-correcoes").value = (r.correcoes || []).join("\n");
  $("#r-sev").value = r.severidade || "média";
  $("#regra-form-title").textContent = "✏️ Editar regra";
  $("#btn-add-regra").textContent = "Atualizar regra";
  $("#btn-cancelar-edicao").classList.remove("hidden");
  $("#regra-msg").textContent = "";
  $("#regra-form-title").scrollIntoView({ behavior: "smooth", block: "nearest" });
}

function cancelarEdicao() {
  EDITANDO_ID = null;
  ["#r-topico", "#r-texto", "#r-limites", "#r-flex", "#r-correcoes"].forEach((s) => ($(s).value = ""));
  $("#r-sev").value = "média";
  $("#regra-form-title").textContent = "➕ Adicionar regra";
  $("#btn-add-regra").textContent = "Salvar regra";
  $("#btn-cancelar-edicao").classList.add("hidden");
  $("#regra-msg").textContent = "";
}

async function salvarRegra() {
  const tipo = $("#apr-tipo").value;
  const corpo = {
    topico: $("#r-topico").value.trim(), texto_padrao: $("#r-texto").value.trim(),
    limites: linhas($("#r-limites")), flexibilidades: linhas($("#r-flex")),
    correcoes: linhas($("#r-correcoes")), severidade: $("#r-sev").value,
  };
  const editando = !!EDITANDO_ID;
  if (editando) corpo.id = EDITANDO_ID;
  if (!corpo.topico) { $("#regra-msg").textContent = "Informe o tópico."; return; }
  try {
    await apiJSON("/tipos/" + tipo + "/conhecimento/regras", jsonBody(corpo));
    cancelarEdicao();
    $("#regra-msg").textContent = editando ? "Regra atualizada ✓" : "Regra salva ✓";
    carregarBase();
  } catch (e) { $("#regra-msg").textContent = "Erro: " + e.message; }
}
async function desativarRegra(tipo, id) {
  try { await api("/tipos/" + tipo + "/conhecimento/regras/" + id, { method: "DELETE" }); carregarBase(); }
  catch (e) { alert("Erro: " + e.message); }
}
async function definirContratoPadrao() {
  const tipo = $("#apr-tipo").value;
  const texto = $("#cp-texto").value.trim();
  if (!texto) { $("#cp-msg").textContent = "Cole o texto do contrato padrão."; return; }
  try {
    await apiJSON("/tipos/" + tipo + "/conhecimento/contrato-padrao", jsonBody({ nome_arquivo: "contrato_padrao", texto }));
    $("#cp-msg").textContent = "Contrato padrão definido ✓"; carregarBase();
  } catch (e) { $("#cp-msg").textContent = "Erro: " + e.message; }
}

// ── EVENTOS ──
document.querySelectorAll("[data-page]").forEach((el) => el.addEventListener("click", () => navegar(el.dataset.page)));

$("#uploadZone").addEventListener("click", () => $("#fileInput").click());
$("#uploadZone").addEventListener("dragover", (e) => { e.preventDefault(); $("#uploadZone").classList.add("drag-over"); });
$("#uploadZone").addEventListener("dragleave", () => $("#uploadZone").classList.remove("drag-over"));
$("#uploadZone").addEventListener("drop", (e) => { e.preventDefault(); $("#uploadZone").classList.remove("drag-over"); if (e.dataTransfer.files[0]) aplicarArquivo(e.dataTransfer.files[0]); });
$("#fileInput").addEventListener("change", (e) => { if (e.target.files[0]) aplicarArquivo(e.target.files[0]); });
$("#fileRemove").addEventListener("click", removerArquivo);
$("#analyzeBtn").addEventListener("click", analisar);
$("#btn-download").addEventListener("click", () => CURRENT_ANALYSIS && baixar(CURRENT_ANALYSIS.id));
$("#btn-nova").addEventListener("click", () => {
  removerArquivo(); hide($("#resultPanel"));
  const b = $("#analyzeBtn"); b.classList.remove("success"); b.textContent = "🔍 Analisar contrato"; b.disabled = true;
});
$("#apr-tipo").addEventListener("change", carregarBase);
$("#btn-add-regra").addEventListener("click", salvarRegra);
$("#btn-cancelar-edicao").addEventListener("click", cancelarEdicao);
$("#btn-cp").addEventListener("click", definirContratoPadrao);

// ── INÍCIO (modo dev: entra direto sem login) ──
$("#user-name").textContent = "dev local";
$("#user-role").textContent = "curador";
$("#user-avatar").textContent = "DV";
$("#cfg-email").value = "dev@local";
$("#cfg-papel").value = "curador";
carregarTipos().then(() => navegar("nova"));
