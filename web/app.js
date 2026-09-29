/* =====================================================================
   Asistente ECyD — interfaz web (JavaScript sin dependencias)
   ===================================================================== */
(() => {
  "use strict";

  const $ = (s, el = document) => el.querySelector(s);
  const $$ = (s, el = document) => [...el.querySelectorAll(s)];

  // ------------------------------------------------------------ iconos (trazo 24×24)
  const P = (d) => d.map(x => x.startsWith("<") ? x : `<path d="${x}"/>`).join("");
  const ICONS = {
    home: P(["M3 10.5 12 3l9 7.5V20a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1z"]),
    chat: P(["M4 5.5A1.5 1.5 0 0 1 5.5 4h13A1.5 1.5 0 0 1 20 5.5v9a1.5 1.5 0 0 1-1.5 1.5H9l-5 4z", "M8 9h8M8 12.5h5"]),
    users: P(['<circle cx="9" cy="8" r="3.2"/>', "M3 20c0-3.3 2.7-5.6 6-5.6s6 2.3 6 5.6", '<circle cx="17" cy="9" r="2.5"/>', "M16.2 14.5c2.7.2 4.8 2.2 4.8 5"]),
    file: P(["M14 3H6.5A1.5 1.5 0 0 0 5 4.5v15A1.5 1.5 0 0 0 6.5 21h11a1.5 1.5 0 0 0 1.5-1.5V8z", "M14 3v5h5", "M8.5 13h7M8.5 16.5h5"]),
    brain: P(["M9.5 4.2A3 3 0 0 0 6 7a3 3 0 0 0-2 5.2A3 3 0 0 0 6 17a3 3 0 0 0 3.5 2.8A2.5 2.5 0 0 0 12 18V6a2.5 2.5 0 0 0-2.5-1.8z", "M14.5 4.2A3 3 0 0 1 18 7a3 3 0 0 1 2 5.2 3 3 0 0 1-2 4.8 3 3 0 0 1-3.5 2.8A2.5 2.5 0 0 1 12 18", "M8 10.5c1 0 2 .6 2 2M16 10.5c-1 0-2 .6-2 2"]),
    settings: P(['<circle cx="12" cy="12" r="3"/>', "M12 2.5v3M12 18.5v3M4.2 7l2.6 1.5M17.2 15.5l2.6 1.5M4.2 17l2.6-1.5M17.2 8.5 19.8 7", '<circle cx="12" cy="12" r="7"/>']),
    search: P(['<circle cx="11" cy="11" r="6.5"/>', "m16 16 4.5 4.5"]),
    plus: P(["M12 5v14M5 12h14"]),
    "chevron-right": P(["m9 6 6 6-6 6"]),
    "chevron-down": P(["m6 9 6 6 6-6"]),
    send: P(["M4.5 11.5 20 4l-6 16-2.8-6.2z", "M11.2 13.8 20 4"]),
    stop: P(['<rect x="7" y="7" width="10" height="10" rx="1.5"/>']),
    x: P(["M6 6l12 12M18 6 6 18"]),
    menu: P(["M4 7h16M4 12h16M4 17h16"]),
    note: P(["M5 4h14v11l-5 5H5z", "M14 20v-5h5", "M8.5 9h7M8.5 12.5h4"]),
    book: P(["M3 5.5c2.6-1 5.6-1 9 1 3.4-2 6.4-2 9-1V19c-2.6-1-5.6-1-9 1-3.4-2-6.4-2-9-1z", "M12 6.5V20"]),
    bulb: P(["M9.5 18h5M10.5 21h3", "M12 3a6 6 0 0 0-3.6 10.8c.7.5 1.1 1.3 1.1 2.2h5c0-.9.4-1.7 1.1-2.2A6 6 0 0 0 12 3z"]),
    heart: P(["M12 20s-7.5-4.5-7.5-10.2A4.2 4.2 0 0 1 12 7.2a4.2 4.2 0 0 1 7.5 2.6C19.5 15.5 12 20 12 20z"]),
    "user-pin": P(['<circle cx="12" cy="8" r="3.5"/>', "M5 20c0-3.6 3.1-6 7-6s7 2.4 7 6"]),
    calendar: P(['<rect x="4" y="5" width="16" height="15" rx="2"/>', "M4 10h16M8 3v4M16 3v4"]),
    target: P(['<circle cx="12" cy="12" r="8.5"/>', '<circle cx="12" cy="12" r="4.5"/>', '<circle cx="12" cy="12" r="1"/>']),
    clock: P(['<circle cx="12" cy="12" r="8.5"/>', "M12 7.5V12l3 2"]),
    layers: P(["m12 3 9 5-9 5-9-5z", "m3 13 9 5 9-5"]),
    flag: P(["M5 21V4", "M5 4h11.5l-2 4 2 4H5"]),
    activity: P(["M3 12h4l2.5-6 5 12 2.5-6H21"]),
    hash: P(["M9 4 7 20M17 4l-2 16M4 9h16M3.5 15h16"]),
    compass: P(['<circle cx="12" cy="12" r="8.5"/>', "m15.5 8.5-2 5-5 2 2-5z"]),
    edit: P(["M4 20h4L19 9l-4-4L4 16z", "m13.5 6.5 4 4"]),
    trash: P(["M4 7h16M9.5 7V4.5h5V7M6 7l1 13h10l1-13", "M10 11v5M14 11v5"]),
    download: P(["M12 4v11m-4-4 4 4 4-4M5 20h14"]),
    check: P(["m5 12.5 4.5 4.5L19 7"]),
    checks: P(["m2.5 12.5 4 4L15 8", "m9.5 16 1 1L21 7"]),
    sparkle: P(["M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8z"]),
    logout: P(["M15 4h3.5A1.5 1.5 0 0 1 20 5.5v13a1.5 1.5 0 0 1-1.5 1.5H15", "M10 8l-4 4 4 4M6 12h10"]),
    info: P(['<circle cx="12" cy="12" r="8.5"/>', "M12 11v5M12 8h.01"]),
  };
  function icon(name, cls = "") {
    return `<i data-icon="${name}" class="${cls}"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${ICONS[name] || ""}</svg></i>`;
  }
  function hydrateIcons(root = document) {
    $$("i[data-icon]", root).forEach(el => {
      if (!el.firstChild && ICONS[el.dataset.icon]) el.outerHTML = icon(el.dataset.icon, el.className);
    });
  }

  // ------------------------------------------------------------ constantes
  const TIPOS = {
    documento_oficial: "Documento oficial", ensayo: "Ensayo", programa_territorial: "Programa territorial",
    retiro: "Retiros", ficha: "Ficha", guia: "Guía", formulario: "Formulario", otro: "Otro",
  };
  const CAT_LABELS = {
    equipo: "Equipo", adolescente: "Adolescentes", proceso: "Procesos y decisiones",
    preferencia: "Preferencias del responsable", pendiente: "Pendientes", general: "General",
  };
  const FIELD_ICONS = {
    etapa: "layers", edades: "calendar", cantidad_chicos: "users", tema_mensual: "target",
    tema_reunion: "book", objetivo: "flag", situacion_equipo: "compass", duracion: "clock",
    tipo_encuentro: "activity", notas: "note",
  };
  const FIELD_PH = {
    etapa: "Ej.: 2da etapa", edades: "Ej.: 12 a 13 años", cantidad_chicos: "Ej.: 9", duracion: "Ej.: 1 h 30 min",
    tipo_encuentro: "Ej.: reunión semanal, salida, convivencia", tema_mensual: "Ej.: La amistad",
    tema_reunion: "Ej.: Amigos que me enriquecen", objetivo: "¿Qué querés que vivan o descubran?",
    situacion_equipo: "Clima, vínculos, participación, dificultades…", notas: "Cualquier otra cosa útil",
  };

  const state = {
    config: { team_fields: [], categorias: [] },
    teams: [], convs: [], memories: [], docs: null, health: null,
    teamId: load("teamId") || "",
    conversationId: null, conversation: null,
    controller: null, view: "inicio",
  };

  function load(k) { try { return localStorage.getItem("ecyd." + k); } catch { return null; } }
  function save(k, v) { try { v == null || v === "" ? localStorage.removeItem("ecyd." + k) : localStorage.setItem("ecyd." + k, v); } catch {} }

  // ------------------------------------------------------------ API
  async function api(path, opts = {}) {
    const res = await fetch(path, {
      headers: opts.body ? { "Content-Type": "application/json" } : {},
      credentials: "same-origin", ...opts,
      body: opts.body ? JSON.stringify(opts.body) : undefined,
    });
    if (res.status === 401) { showLogin(); throw new Error("No autorizado"); }
    if (!res.ok) {
      let msg = res.statusText;
      try { msg = (await res.json()).detail || msg; } catch {}
      throw new Error(msg);
    }
    return res.json();
  }

  // ------------------------------------------------------------ utilidades
  function esc(s) {
    return String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  }
  function toast(text, ms = 3200) {
    const t = $("#toast");
    t.textContent = text; t.classList.remove("hidden");
    clearTimeout(toast._t); toast._t = setTimeout(() => t.classList.add("hidden"), ms);
  }
  function fmtDate(iso) {
    if (!iso) return "";
    const d = new Date(iso), now = new Date();
    return d.toDateString() === now.toDateString()
      ? d.toLocaleTimeString("es-AR", { hour: "2-digit", minute: "2-digit" })
      : d.toLocaleDateString("es-AR", { day: "numeric", month: "short" });
  }
  function fmtTime(iso) {
    const d = iso ? new Date(iso) : new Date();
    return d.toLocaleTimeString("es-AR", { hour: "2-digit", minute: "2-digit" });
  }
  const etapasTxt = e => e && e.length ? "Etapa " + e.join(" y ") : "General";
  const currentTeam = () => state.teams.find(t => t.id === state.teamId) || null;
  const userName = () => (load("nombre") || "").trim();
  function initials(name) {
    const p = name.trim().split(/\s+/).filter(Boolean);
    return p.length ? (p[0][0] + (p[1]?.[0] || "")).toUpperCase() : "EC";
  }
  function debounce(fn, ms) { let t; return (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), ms); }; }

  // ------------------------------------------------------------ markdown seguro
  function inline(s) {
    s = esc(s);
    s = s.replace(/`([^`]+)`/g, "<code>$1</code>");
    s = s.replace(/\*\*F(\d{1,2})\*\*|\[F(\d{1,2})\]|\(F(\d{1,2})\)/g, (m, a, b, c) => {
      const n = a || b || c;
      return `<button type="button" class="cite" data-n="${n}" title="Ver fuente F${n}">F${n}</button>`;
    });
    s = s.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
    s = s.replace(/(^|[^*\w])\*([^*\n]+)\*(?!\w)/g, "$1<em>$2</em>");
    s = s.replace(/(^|\W)_([^_\n]+)_(?=\W|$)/g, "$1<em>$2</em>");
    return s;
  }
  function markdown(src) {
    const lines = String(src || "").replace(/\r/g, "").split("\n");
    let html = "", i = 0;
    const isSep = l => /^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$/.test(l);
    const isList = l => /^\s*([-*•]|\d+[.)])\s+/.test(l);
    while (i < lines.length) {
      const l = lines[i];
      if (!l.trim()) { i++; continue; }
      let m;
      if ((m = l.match(/^(#{1,6})\s+(.*)$/))) { const h = Math.min(4, m[1].length + 1); html += `<h${h}>${inline(m[2])}</h${h}>`; i++; continue; }
      if (/^\s*(-{3,}|\*{3,}|_{3,})\s*$/.test(l)) { html += "<hr>"; i++; continue; }
      if (/^\s*>/.test(l)) {
        const buf = [];
        while (i < lines.length && /^\s*>/.test(lines[i])) buf.push(lines[i++].replace(/^\s*>\s?/, ""));
        html += `<blockquote>${markdown(buf.join("\n"))}</blockquote>`; continue;
      }
      if (l.includes("|") && i + 1 < lines.length && isSep(lines[i + 1])) {
        const row = r => r.trim().replace(/^\||\|$/g, "").split("|").map(c => c.trim());
        let t = "<table><thead><tr>" + row(l).map(c => `<th>${inline(c)}</th>`).join("") + "</tr></thead><tbody>";
        i += 2;
        while (i < lines.length && lines[i].includes("|") && lines[i].trim()) t += "<tr>" + row(lines[i++]).map(c => `<td>${inline(c)}</td>`).join("") + "</tr>";
        html += t + "</tbody></table>"; continue;
      }
      if (isList(l)) {
        const ordered = /^\s*\d+[.)]/.test(l), items = [];
        while (i < lines.length && (isList(lines[i]) || (/^\s{2,}\S/.test(lines[i]) && items.length))) {
          const cur = lines[i++];
          if (isList(cur) && !/^\s{4,}/.test(cur)) items.push(cur.replace(/^\s*([-*•]|\d+[.)])\s+/, ""));
          else items[items.length - 1] += "\n" + cur.trim().replace(/^([-*•]|\d+[.)])\s+/, "• ");
        }
        const tag = ordered ? "ol" : "ul";
        html += `<${tag}>` + items.map(it => `<li>${inline(it).replace(/\n/g, "<br>")}</li>`).join("") + `</${tag}>`;
        continue;
      }
      const buf = [];
      while (i < lines.length && lines[i].trim() && !/^(#{1,6}\s|\s*>|\s*([-*•]|\d+[.)])\s+|\s*(-{3,}|\*{3,})\s*$)/.test(lines[i])) buf.push(lines[i++]);
      if (!buf.length) buf.push(lines[i++]);
      html += `<p>${buf.map(inline).join("<br>")}</p>`;
    }
    return html;
  }

  // ------------------------------------------------------------ acceso
  function showLogin() { $("#login").classList.remove("hidden"); $("#login-pass").focus(); }
  $("#login-form").addEventListener("submit", async e => {
    e.preventDefault();
    $("#login-error").textContent = "";
    try {
      await api("/api/login", { method: "POST", body: { password: $("#login-pass").value } });
      $("#login").classList.add("hidden"); boot();
    } catch (err) { $("#login-error").textContent = err.message; }
  });

  // ------------------------------------------------------------ tema y perfil
  function applyTheme() {
    const t = load("tema") || "auto";
    if (t === "auto") document.documentElement.removeAttribute("data-theme");
    else document.documentElement.setAttribute("data-theme", t);
  }
  function renderProfile() {
    const n = userName();
    $("#profile-name").textContent = n || "Tu nombre";
    $("#profile-role").textContent = load("rol") || "Responsable de equipo";
    $("#profile-avatar").textContent = initials(n);
    $("#greet-name").textContent = n ? `Hola, ${n.split(" ")[0]}` : "Hola";
  }
  function applyHeroPhoto(url) {
    if (!url) return;
    $("#hero").classList.add("has-photo");
    $(".hero-art").style.setProperty("--hero-photo", `url("${url}")`);
  }

  // ------------------------------------------------------------ estado del servidor
  async function pollHealth() {
    const el = $("#status"), txt = el.querySelector(".status-text");
    try {
      const h = state.health = await api("/api/health");
      el.classList.remove("ok", "err");
      if (!h.llm_configurado) { el.classList.add("err"); txt.textContent = "Falta configurar la clave de Groq"; }
      else if (h.memoria_ok === false) { el.classList.add("err"); txt.textContent = "No se pudo conectar con la memoria"; }
      else if (h.rag === "listo") {
        el.classList.add("ok");
        const mem = currentTeam()?.auto_memoria ? " · Memoria activa" : "";
        txt.textContent = `IA con ${h.llm_provider === "gemini" ? "Gemini" : "Groq"}${mem}`;
        $("#docs-note").textContent = `La IA utiliza ${h.corpus.documentos} documentos del ECyD (estatutos, estilo formativo, fichas por etapa y más) para responder a tus consultas.`;
        return;
      } else if (h.rag === "error") { el.classList.add("err"); txt.textContent = "Error al cargar los documentos"; return; }
      else txt.textContent = "Cargando documentos…";
    } catch { txt.textContent = "Sin conexión con el servidor"; }
    setTimeout(pollHealth, 3000);
  }

  // ------------------------------------------------------------ navegación
  function showView(name) {
    state.view = name;
    $$(".view").forEach(v => v.classList.toggle("hidden", v.id !== "view-" + name));
    $$(".nav-item").forEach(a => a.classList.toggle("active", a.dataset.view === name));
    closeSidebar(); closeRail();
    $("#main").scrollTop = 0;
    const renderers = { conversaciones: renderConversations, equipos: renderTeams, documentos: renderDocuments, memoria: renderMemory, configuracion: renderSettings };
    renderers[name]?.();
    if (name === "inicio") setTimeout(() => $("#input").focus(), 50);
  }
  document.addEventListener("click", e => {
    const a = e.target.closest("[data-view]");
    if (!a) return;
    e.preventDefault();
    showView(a.dataset.view);
  });

  function closeSidebar() { $("#sidebar").classList.remove("open"); syncScrim(); }
  function closeRail() { $("#rail").classList.remove("open"); syncScrim(); }
  function syncScrim() { $("#scrim").classList.toggle("show", $("#sidebar").classList.contains("open") || $("#rail").classList.contains("open")); }
  $("#open-sidebar").addEventListener("click", () => { $("#sidebar").classList.add("open"); syncScrim(); });
  $("#open-rail").addEventListener("click", () => { $("#rail").classList.add("open"); syncScrim(); });
  $("#close-rail").addEventListener("click", closeRail);
  $("#scrim").addEventListener("click", () => { closeSidebar(); closeRail(); });

  // ------------------------------------------------------------ equipos
  async function loadTeams() {
    state.teams = await api("/api/teams");
    if (state.teamId && !currentTeam()) { state.teamId = ""; save("teamId", null); }
    const sel = $("#team-select");
    sel.innerHTML = `<option value="">Sin equipo · consulta general</option>` +
      state.teams.map(t => `<option value="${esc(t.id)}">${esc(t.nombre)}</option>`).join("");
    sel.value = state.teamId;
    renderContext(); updateHeader();
    await loadMemories();
  }
  function setTeam(id) {
    state.teamId = id || ""; save("teamId", state.teamId);
    $("#team-select").value = state.teamId;
    newConversation(false);
    renderContext(); updateHeader(); loadMemories(); loadConversations(); pollHealth();
  }
  $("#team-select").addEventListener("change", e => setTeam(e.target.value));
  $("#ctx-edit").addEventListener("click", () => { showView("equipos"); if (currentTeam()) renderTeamForm(currentTeam()); else renderTeamForm(null); });

  function renderContext() {
    const t = currentTeam(), list = $("#ctx-list");
    if (!t) {
      list.innerHTML = `<p class="ctx-empty">Elegí o creá un equipo para que las respuestas tengan en cuenta su etapa, su momento y lo que ya conversaron.</p>
        <button class="btn primary small" id="ctx-create">${icon("plus")}Crear equipo</button>`;
      $("#ctx-create").addEventListener("click", () => { showView("equipos"); renderTeamForm(null); });
      return;
    }
    const fields = state.config.team_fields.filter(f => (t.perfil[f.key] || "").trim());
    list.innerHTML = fields.length ? fields.map(f => `
      <div class="ctx-item">${icon(FIELD_ICONS[f.key] || "info")}
        <div><div class="k">${esc(f.label)}</div><div class="v">${esc(t.perfil[f.key])}</div></div></div>`).join("")
      : `<p class="ctx-empty">Todavía no cargaste datos de este equipo. Tocá <strong>Editar</strong> para completar etapa, edades, tema mensual y objetivo.</p>`;
  }

  function renderTeams() {
    const v = $("#view-equipos");
    v.innerHTML = `
      <div class="page-head"><div><h1>Mis equipos</h1>
        <p>Cada equipo tiene su contexto, su memoria y sus conversaciones. El equipo activo personaliza las respuestas.</p></div>
        <span class="spacer"></span><button class="btn primary" id="team-new">${icon("plus")}Nuevo equipo</button></div>
      ${state.teams.length ? `<div class="grid-2">${state.teams.map(t => `
        <div class="team-card ${t.id === state.teamId ? "active" : ""}">
          <h3>${icon("users")}${esc(t.nombre)}${t.id === state.teamId ? ` <span class="badge red">Activo</span>` : ""}</h3>
          <div class="row-sub">${esc(t.perfil.etapa || "Etapa sin definir")}${t.perfil.edades ? " · " + esc(t.perfil.edades) : ""}${t.perfil.cantidad_chicos ? " · " + esc(t.perfil.cantidad_chicos) + " adolescentes" : ""}</div>
          ${t.perfil.tema_mensual ? `<div class="row-sub">Tema mensual: ${esc(t.perfil.tema_mensual)}</div>` : ""}
          <div class="actions">
            ${t.id === state.teamId ? "" : `<button class="btn primary small" data-use="${t.id}">Usar este equipo</button>`}
            <button class="btn small" data-edit="${t.id}">${icon("edit")}Editar</button>
          </div>
        </div>`).join("")}</div>`
      : `<div class="empty-state"><img src="/static/img/cruz-ecyd.svg" alt=""><p>Todavía no creaste ningún equipo.</p>
          <button class="btn primary" id="team-new-2">${icon("plus")}Crear mi primer equipo</button></div>`}`;
    $("#team-new")?.addEventListener("click", () => renderTeamForm(null));
    $("#team-new-2")?.addEventListener("click", () => renderTeamForm(null));
    $$("[data-use]", v).forEach(b => b.addEventListener("click", () => { setTeam(b.dataset.use); renderTeams(); toast("Equipo activo actualizado"); }));
    $$("[data-edit]", v).forEach(b => b.addEventListener("click", () => renderTeamForm(state.teams.find(t => t.id === b.dataset.edit))));
  }

  function renderTeamForm(team) {
    const v = $("#view-equipos"), p = team?.perfil || {};
    const fields = state.config.team_fields.map(f => {
      const long = ["situacion_equipo", "objetivo", "notas"].includes(f.key);
      const val = esc(p[f.key] || "");
      return `<div class="field-wrap ${long ? "wide" : ""}"><label for="f-${f.key}">${icon(FIELD_ICONS[f.key] || "info")}${esc(f.label)}</label>` +
        (long ? `<textarea class="field" id="f-${f.key}" data-k="${f.key}" placeholder="${FIELD_PH[f.key] || ""}">${val}</textarea>`
              : `<input class="field" id="f-${f.key}" data-k="${f.key}" value="${val}" placeholder="${FIELD_PH[f.key] || ""}">`) + `</div>`;
    }).join("");
    v.innerHTML = `
      <div class="page-head"><div><h1>${team ? "Editar equipo" : "Nuevo equipo"}</h1>
        <p>Completá solo lo que quieras; podés actualizarlo cuando cambie el momento del equipo. No es material del ECyD: sirve para personalizar las respuestas.</p></div></div>
      <form id="team-form" class="form-card">
        <div class="form-grid">
          <div class="field-wrap wide"><label for="f-nombre">${icon("users")}Nombre del equipo</label>
            <input class="field" id="f-nombre" required maxlength="80" value="${esc(team?.nombre || "")}" placeholder="Ej.: Equipo San Pablo"></div>
          ${fields}
          <label class="toggle wide"><input type="checkbox" id="f-auto" ${team?.auto_memoria === false ? "" : "checked"}>
            <span>Recordar automáticamente lo importante de las conversaciones<br><span class="muted" style="font-size:13px">Podés revisar, editar o borrar cada recuerdo en “Memoria”.</span></span></label>
        </div>
        <div class="actions" style="margin-top:18px">
          <button class="btn primary" type="submit">${icon("check")}${team ? "Guardar cambios" : "Crear equipo"}</button>
          <button class="btn ghost" type="button" id="team-cancel">Cancelar</button>
          ${team ? `<span style="flex:1"></span>
            <button class="btn small" type="button" id="team-export">${icon("download")}Exportar datos</button>
            <button class="btn danger small" type="button" id="team-delete">${icon("trash")}Eliminar equipo</button>` : ""}
        </div>
      </form>`;
    $("#f-nombre").focus();
    $("#team-cancel").addEventListener("click", renderTeams);
    $("#team-form").addEventListener("submit", async e => {
      e.preventDefault();
      const perfil = {};
      $$("#team-form [data-k]").forEach(el => { perfil[el.dataset.k] = el.value.trim(); });
      const body = { nombre: $("#f-nombre").value.trim(), perfil, auto_memoria: $("#f-auto").checked };
      try {
        const t = team ? await api(`/api/teams/${team.id}`, { method: "PUT", body }) : await api("/api/teams", { method: "POST", body });
        await loadTeams();
        if (!team || team.id === state.teamId) setTeam(t.id); else renderContext();
        toast(team ? "Equipo actualizado" : "Equipo creado y activado");
        renderTeams();
      } catch (err) { toast(err.message); }
    });
    if (team) {
      $("#team-export").addEventListener("click", () => { window.location = `/api/teams/${team.id}/export`; });
      $("#team-delete").addEventListener("click", async () => {
        if (!confirm(`¿Eliminar “${team.nombre}”? Se borrarán también su memoria y sus conversaciones. No se puede deshacer.`)) return;
        await api(`/api/teams/${team.id}`, { method: "DELETE" });
        if (team.id === state.teamId) setTeam("");
        await loadTeams(); renderTeams(); toast("Equipo eliminado");
      });
    }
  }

  // ------------------------------------------------------------ memoria
  async function loadMemories() {
    state.memories = state.teamId ? await api(`/api/teams/${state.teamId}/memories`).catch(() => []) : [];
    const ul = $("#mem-latest");
    const latest = [...state.memories].sort((a, b) => (b.updated_at || "").localeCompare(a.updated_at || "")).slice(0, 4);
    ul.innerHTML = latest.length ? latest.map(m => `<li>${esc(m.texto)}</li>`).join("")
      : `<li class="empty-li muted">${state.teamId ? "Todavía no hay recuerdos. Se van guardando a medida que conversás." : "Elegí un equipo para ver su memoria."}</li>`;
    if (state.view === "memoria") renderMemory();
  }

  function renderMemory(highlight = []) {
    const v = $("#view-memoria"), team = currentTeam();
    if (!team) {
      v.innerHTML = `<div class="page-head"><div><h1>Memoria</h1><p>La memoria pertenece a cada equipo.</p></div></div>
        <div class="empty-state"><img src="/static/img/cruz-ecyd.svg" alt=""><p>Elegí o creá un equipo para ver y editar lo que el asistente recuerda.</p>
        <button class="btn primary" data-view="equipos">${icon("users")}Ir a Mis equipos</button></div>`;
      return;
    }
    const groups = {};
    state.memories.forEach(m => (groups[m.categoria] ||= []).push(m));
    const cats = state.config.categorias.length ? state.config.categorias : Object.keys(CAT_LABELS);
    v.innerHTML = `
      <div class="page-head"><div><h1>Memoria · ${esc(team.nombre)}</h1>
        <p>Lo que el asistente recuerda de este equipo entre conversaciones. No es material del ECyD: sirve para contextualizar las respuestas.
        ${team.auto_memoria ? "El aprendizaje automático está <strong>activado</strong>." : "El aprendizaje automático está <strong>desactivado</strong> (se cambia al editar el equipo)."}</p></div></div>
      <form class="form-card mem-add" id="mem-add">
        <textarea class="field" id="mem-text" rows="2" placeholder="Agregar algo para recordar (ej.: “Martina se sumó al equipo en abril”)" required></textarea>
        <select id="mem-cat">${cats.map(c => `<option value="${c}">${esc(CAT_LABELS[c] || c)}</option>`).join("")}</select>
        <button class="btn primary" type="submit">${icon("plus")}Guardar</button>
      </form>
      ${cats.filter(c => groups[c]).map(c => `
        <div class="section-title">${esc(CAT_LABELS[c] || c)}</div>
        <div class="list">${groups[c].map(m => `
          <div class="row-item mem-item ${highlight.includes(m.id) ? "new" : ""}" data-id="${m.id}">
            ${icon(m.origen === "auto" ? "sparkle" : "edit")}
            <div class="row-main"><div class="mem-text">${esc(m.texto)}</div>
              <div class="row-sub">${m.origen === "auto" ? "Aprendido de una conversación" : "Agregado a mano"} · ${fmtDate(m.updated_at)}</div></div>
            <div class="row-actions">
              <button class="icon-btn mem-edit" title="Editar" aria-label="Editar">${icon("edit")}</button>
              <button class="icon-btn mem-del" title="Borrar" aria-label="Borrar">${icon("trash")}</button></div>
          </div>`).join("")}</div>`).join("") || `<div class="empty-state" style="margin-top:16px"><p>Todavía no hay recuerdos guardados.</p></div>`}
      ${state.memories.length ? `<div class="actions" style="margin-top:22px"><button class="btn danger small" id="mem-clear">${icon("trash")}Borrar toda la memoria</button></div>` : ""}`;
    $("#mem-add").addEventListener("submit", async e => {
      e.preventDefault();
      await api(`/api/teams/${team.id}/memories`, { method: "POST", body: { texto: $("#mem-text").value, categoria: $("#mem-cat").value } });
      await loadMemories(); toast("Guardado en la memoria");
    });
    $("#mem-clear")?.addEventListener("click", async () => {
      if (!confirm("¿Borrar toda la memoria de este equipo?")) return;
      await api(`/api/teams/${team.id}/memories`, { method: "DELETE" }); loadMemories();
    });
    $$(".mem-item", v).forEach(item => {
      const id = item.dataset.id;
      item.querySelector(".mem-del").addEventListener("click", async () => {
        await api(`/api/teams/${team.id}/memories/${id}`, { method: "DELETE" }); loadMemories();
      });
      item.querySelector(".mem-edit").addEventListener("click", () => {
        const box = item.querySelector(".mem-text");
        if (item.querySelector("textarea")) return;
        const ta = document.createElement("textarea");
        ta.className = "field"; ta.value = box.textContent; ta.rows = 2;
        box.replaceWith(ta); ta.focus();
        const ok = document.createElement("button");
        ok.className = "btn primary small"; ok.textContent = "Guardar"; ok.style.marginTop = "6px";
        ta.after(ok);
        ok.addEventListener("click", async () => {
          await api(`/api/teams/${team.id}/memories/${id}`, { method: "PUT", body: { texto: ta.value } });
          loadMemories();
        });
      });
    });
  }

  // ------------------------------------------------------------ conversaciones
  async function loadConversations() {
    state.convs = await api("/api/conversations").catch(() => []);
    const scoped = state.convs.filter(c => (c.team_id || "") === state.teamId).slice(0, 8);
    $("#recent").innerHTML = scoped.length ? scoped.map(c => `
      <a href="#" class="recent-item ${c.id === state.conversationId ? "active" : ""}" data-conv="${c.id}" title="${esc(c.titulo)}">${esc(c.titulo)}</a>`).join("")
      : `<div class="recent-empty">Sin conversaciones todavía.</div>`;
    $$("#recent [data-conv]").forEach(a => a.addEventListener("click", e => { e.preventDefault(); openConversation(a.dataset.conv); }));
    if (state.view === "conversaciones") renderConversations();
  }

  function renderConversations() {
    const v = $("#view-conversaciones");
    const teamName = id => state.teams.find(t => t.id === id)?.nombre || "Sin equipo";
    v.innerHTML = `
      <div class="page-head"><div><h1>Conversaciones</h1><p>Todo tu historial queda guardado. Podés retomar cualquier conversación donde la dejaste.</p></div>
        <span class="spacer"></span><button class="btn primary" id="conv-new">${icon("plus")}Nueva conversación</button></div>
      <div class="filters">
        <input class="field" type="search" id="conv-filter" placeholder="Filtrar por título…" style="max-width:320px">
        <button class="chip on" data-scope="team">${state.teamId ? "Este equipo" : "Sin equipo"}</button>
        <button class="chip" data-scope="all">Todas</button>
      </div>
      <div class="list" id="conv-list"></div>`;
    let scope = "team";
    const draw = () => {
      const q = ($("#conv-filter").value || "").toLowerCase();
      const rows = state.convs.filter(c => (scope === "all" || (c.team_id || "") === state.teamId) && (!q || c.titulo.toLowerCase().includes(q)));
      $("#conv-list").innerHTML = rows.length ? rows.map(c => `
        <div class="row-item clickable" data-open="${c.id}">
          ${icon("chat")}
          <div class="row-main"><div class="row-title">${esc(c.titulo)}</div>
            <div class="row-sub"><span>${esc(teamName(c.team_id))}</span><span>·</span><span>${c.mensajes} mensajes</span><span>·</span><span>${fmtDate(c.updated_at)}</span></div></div>
          <div class="row-actions"><button class="icon-btn" data-del="${c.id}" title="Eliminar" aria-label="Eliminar conversación">${icon("trash")}</button></div>
        </div>`).join("") : `<div class="empty-state"><p>No hay conversaciones para mostrar.</p></div>`;
      $$("[data-open]", v).forEach(r => r.addEventListener("click", () => openConversation(r.dataset.open)));
      $$("[data-del]", v).forEach(b => b.addEventListener("click", async e => {
        e.stopPropagation();
        if (!confirm("¿Eliminar esta conversación y sus notas?")) return;
        await api(`/api/conversations/${b.dataset.del}`, { method: "DELETE" });
        if (b.dataset.del === state.conversationId) newConversation(false);
        await loadConversations(); toast("Conversación eliminada");
      }));
    };
    $("#conv-new").addEventListener("click", () => { newConversation(); showView("inicio"); });
    $("#conv-filter").addEventListener("input", draw);
    $$("[data-scope]", v).forEach(ch => ch.addEventListener("click", () => {
      scope = ch.dataset.scope; $$("[data-scope]", v).forEach(x => x.classList.toggle("on", x === ch)); draw();
    }));
    draw();
  }

  async function openConversation(id) {
    if (state.controller) state.controller.abort();
    const conv = await api(`/api/conversations/${id}`);
    if ((conv.team_id || "") !== state.teamId) { state.teamId = conv.team_id || ""; save("teamId", state.teamId); $("#team-select").value = state.teamId; renderContext(); loadMemories(); }
    state.conversationId = conv.id; state.conversation = conv;
    clearThread();
    conv.messages.forEach(m => m.role === "user" ? addUser(m.content, m.created_at)
      : addAssistant({ text: m.content, sources: m.sources, weak: m.meta?.weak_evidence, time: m.created_at }));
    setChatting(true); updateHeader(); showView("inicio"); loadConversations(); scrollBottom(true);
  }

  function newConversation(focus = true) {
    if (state.controller) state.controller.abort();
    state.conversationId = null; state.conversation = null;
    clearThread(); setChatting(false); updateHeader();
    $$(".recent-item.active").forEach(a => a.classList.remove("active"));
    if (focus) { showView("inicio"); }
  }
  $("#new-chat").addEventListener("click", () => newConversation());
  $("#new-chat-2").addEventListener("click", () => newConversation());

  function setChatting(on) {
    $("#view-inicio").classList.toggle("chatting", on);
    $("#empty").classList.toggle("hidden", on);
  }
  function updateHeader() {
    $("#chat-title").textContent = state.conversation?.titulo || "Nueva conversación";
    const t = currentTeam();
    $("#chat-team").textContent = t ? `Equipo: ${t.nombre}${t.perfil?.etapa ? " · " + t.perfil.etapa : ""}` : "Consulta general, sin equipo";
  }

  // ------------------------------------------------------------ documentos
  async function renderDocuments() {
    const v = $("#view-documentos");
    v.innerHTML = `<div class="page-head"><div><h1>Documentos del ECyD</h1>
      <p>El asistente responde a partir de estos documentos y prioriza los de mayor autoridad: Estatutos, estilo formativo, material de etapas, guías y fichas.</p></div></div>
      <div class="filters" id="doc-filters"></div><div class="list" id="doc-list"><div class="thinking"><span class="spinner"></span>Cargando…</div></div>`;
    try { state.docs ||= await api("/api/documents"); } catch (err) { $("#doc-list").innerHTML = `<p class="error-text">${esc(err.message)}</p>`; return; }
    const tipos = [...new Set(state.docs.map(d => d.tipo))];
    let fTipo = "", fEtapa = "", q = "";
    $("#doc-filters").innerHTML = `<input class="field" type="search" id="doc-q" placeholder="Buscar por título o tema…" style="max-width:280px">
      <button class="chip on" data-tipo="">Todos</button>${tipos.map(t => `<button class="chip" data-tipo="${t}">${esc(TIPOS[t] || t)}</button>`).join("")}
      <span style="width:8px"></span>${[1, 2, 3, 4].map(e => `<button class="chip" data-etapa="${e}">Etapa ${e}</button>`).join("")}`;
    const draw = () => {
      const rows = state.docs.filter(d => (!fTipo || d.tipo === fTipo) && (!fEtapa || (d.etapas || []).includes(+fEtapa)) &&
        (!q || [d.titulo, (d.temas || []).join(" "), TIPOS[d.tipo]].join(" ").toLowerCase().includes(q)));
      $("#doc-list").innerHTML = `<p class="muted" style="font-size:13px;margin:0 0 4px">${rows.length} documentos</p>` + rows.map(d => `
        <div class="row-item">${icon(d.tipo === "documento_oficial" ? "book" : "file")}
          <div class="row-main"><div class="row-title">${esc(d.titulo)}</div>
            <div class="row-sub"><span class="badge ${d.autoridad?.nivel <= 2 ? "red" : ""}">${esc(TIPOS[d.tipo] || d.tipo)}</span><span>${etapasTxt(d.etapas)}</span>
              ${d.calendario?.tiempo_liturgico ? `<span>${esc(d.calendario.tiempo_liturgico.replace("_", " "))}</span>` : ""}
              ${(d.temas || []).slice(0, 3).map(t => `<span class="badge">${esc(t.replaceAll("_", " "))}</span>`).join("")}</div></div>
          <button class="btn small ghost" data-ask="${esc(d.titulo)}" title="Preguntar sobre este documento">${icon("chat")}<span class="hide-sm">Preguntar</span></button>
        </div>`).join("");
      $$("[data-ask]", v).forEach(b => b.addEventListener("click", () => {
        newConversation(); $("#input").value = `¿Qué propone el documento “${b.dataset.ask}” y cómo puedo aprovecharlo con mi equipo?`; autosize(); $("#input").focus();
      }));
    };
    $("#doc-q").addEventListener("input", e => { q = e.target.value.toLowerCase(); draw(); });
    $$("[data-tipo]", v).forEach(ch => ch.addEventListener("click", () => { fTipo = ch.dataset.tipo; $$("[data-tipo]", v).forEach(x => x.classList.toggle("on", x === ch)); draw(); }));
    $$("[data-etapa]", v).forEach(ch => ch.addEventListener("click", () => {
      fEtapa = fEtapa === ch.dataset.etapa ? "" : ch.dataset.etapa;
      $$("[data-etapa]", v).forEach(x => x.classList.toggle("on", x.dataset.etapa === fEtapa)); draw();
    }));
    draw();
  }

  // ------------------------------------------------------------ configuración
  async function renderSettings() {
    const v = $("#view-configuracion");
    const tema = load("tema") || "auto";
    const session = await fetch("/api/session", { credentials: "same-origin" }).then(r => r.json()).catch(() => ({}));
    const h = state.health || {};
    v.innerHTML = `
      <div class="page-head"><div><h1>Configuración</h1><p>Tus datos de perfil se guardan solo en este navegador.</p></div></div>
      <form class="form-card" id="profile-form">
        <div class="form-grid">
          <div class="field-wrap"><label for="p-nombre">${icon("user-pin")}Tu nombre</label><input class="field" id="p-nombre" value="${esc(userName())}" placeholder="Ej.: María López"></div>
          <div class="field-wrap"><label for="p-rol">${icon("users")}Tu rol</label><input class="field" id="p-rol" value="${esc(load("rol") || "")}" placeholder="Responsable de equipo"></div>
        </div>
        <div class="actions" style="margin-top:14px"><button class="btn primary" type="submit">${icon("check")}Guardar perfil</button></div>
      </form>
      <div class="section-title">Apariencia</div>
      <div class="form-card"><div class="seg" id="theme-seg">
        <button data-t="auto" class="${tema === "auto" ? "on" : ""}">Automático</button>
        <button data-t="light" class="${tema === "light" ? "on" : ""}">Claro</button>
        <button data-t="dark" class="${tema === "dark" ? "on" : ""}">Oscuro</button></div>
        <p class="muted" style="font-size:13px;margin:12px 0 0">Imagen de portada: guardá una foto como <code>web/img/portada.jpg</code> y aparecerá en el inicio.</p></div>
      <div class="section-title">Estado del asistente</div>
      <div class="form-card"><dl class="kv">
        <dt>Proveedor de IA</dt><dd>${esc(h.llm_provider === "gemini" ? "Gemini" : "Groq")} · ${esc(h.modelo || "")}</dd>
        <dt>Memoria</dt><dd>${h.memoria === "supabase" ? "Base de datos en la nube (Supabase)" : "Archivo local (SQLite)"}${h.memoria_ok === false ? " — sin conexión" : ""}</dd>
        <dt>Clave configurada</dt><dd>${h.llm_configurado ? "Sí (solo en el servidor)" : "No — agregá GROQ_API_KEY al archivo .env"}</dd>
        <dt>Documentos</dt><dd>${h.corpus ? `${h.corpus.documentos} documentos · ${h.corpus.chunks} fragmentos` : esc(h.rag || "—")}</dd>
        <dt>Índice</dt><dd>${h.corpus ? esc(h.corpus.chunker === "legacy_v1" ? "Heredado (conviene ejecutar scripts/build_index.py)" : "Actualizado") : "—"}</dd>
      </dl></div>
      ${session.auth_required ? `<div class="actions" style="margin-top:18px"><button class="btn" id="logout">${icon("logout")}Cerrar sesión</button></div>` : ""}`;
    $("#profile-form").addEventListener("submit", e => {
      e.preventDefault(); save("nombre", $("#p-nombre").value.trim()); save("rol", $("#p-rol").value.trim());
      renderProfile(); toast("Perfil guardado");
    });
    $$("#theme-seg button").forEach(b => b.addEventListener("click", () => {
      save("tema", b.dataset.t === "auto" ? null : b.dataset.t); applyTheme();
      $$("#theme-seg button").forEach(x => x.classList.toggle("on", x === b));
    }));
    $("#logout")?.addEventListener("click", async () => { await api("/api/logout", { method: "POST" }); location.reload(); });
  }

  // ------------------------------------------------------------ búsqueda global
  const sInput = $("#search-input"), sBox = $("#search-results");
  let sItems = [], sFocus = 0;
  const runSearch = debounce(async () => {
    const q = sInput.value.trim();
    if (!q) { sBox.classList.add("hidden"); return; }
    if (!state.docs) api("/api/documents").then(d => { state.docs = d; runSearch(); }).catch(() => {});
    const ql = q.toLowerCase();
    const convs = state.convs.filter(c => c.titulo.toLowerCase().includes(ql)).slice(0, 4);
    const mems = state.memories.filter(m => m.texto.toLowerCase().includes(ql)).slice(0, 3);
    const docs = (state.docs || []).filter(d => [d.titulo, (d.temas || []).join(" ")].join(" ").toLowerCase().includes(ql)).slice(0, 5);
    sItems = [{ kind: "ask", q }];
    let html = `<button class="sr-item" data-i="0">${icon("sparkle")}<span>Preguntar al asistente: <strong>${esc(q)}</strong></span></button>`;
    const group = (title, arr, kind, ic, label, sub) => {
      if (!arr.length) return;
      html += `<div class="sr-group">${title}</div>`;
      arr.forEach(x => { sItems.push({ kind, x }); html += `<button class="sr-item" data-i="${sItems.length - 1}">${icon(ic)}<span>${esc(label(x))}<small>${esc(sub(x))}</small></span></button>`; });
    };
    group("Conversaciones", convs, "conv", "chat", c => c.titulo, c => fmtDate(c.updated_at));
    group("Memoria del equipo", mems, "mem", "brain", m => m.texto, m => CAT_LABELS[m.categoria] || m.categoria);
    group("Documentos", docs, "doc", "file", d => d.titulo, d => `${TIPOS[d.tipo] || d.tipo} · ${etapasTxt(d.etapas)}`);
    sBox.innerHTML = html; sBox.classList.remove("hidden"); sFocus = 0; paintFocus();
    $$(".sr-item", sBox).forEach(b => b.addEventListener("mousedown", e => { e.preventDefault(); pick(+b.dataset.i); }));
  }, 120);
  function paintFocus() { $$(".sr-item", sBox).forEach((b, i) => b.classList.toggle("focus", i === sFocus)); }
  function pick(i) {
    const it = sItems[i]; if (!it) return;
    sBox.classList.add("hidden"); sInput.value = ""; sInput.blur();
    if (it.kind === "ask") { showView("inicio"); sendMessage(it.q); }
    else if (it.kind === "conv") openConversation(it.x.id);
    else if (it.kind === "mem") showView("memoria");
    else if (it.kind === "doc") { newConversation(); $("#input").value = `¿Qué propone el documento “${it.x.titulo}” y cómo puedo aprovecharlo con mi equipo?`; autosize(); }
  }
  sInput.addEventListener("input", runSearch);
  sInput.addEventListener("keydown", e => {
    if (sBox.classList.contains("hidden")) return;
    if (e.key === "ArrowDown") { sFocus = Math.min(sFocus + 1, sItems.length - 1); paintFocus(); e.preventDefault(); }
    else if (e.key === "ArrowUp") { sFocus = Math.max(sFocus - 1, 0); paintFocus(); e.preventDefault(); }
    else if (e.key === "Enter") { e.preventDefault(); pick(sFocus); }
    else if (e.key === "Escape") sBox.classList.add("hidden");
  });
  sInput.addEventListener("blur", () => setTimeout(() => sBox.classList.add("hidden"), 150));
  sInput.addEventListener("focus", () => { if (sInput.value.trim()) runSearch(); });

  // ------------------------------------------------------------ panel (notas / fuentes)
  function openPanel(title, html) {
    $("#panel-title").textContent = title; $("#panel-body").innerHTML = html;
    $("#panel").classList.add("open"); $("#panel").setAttribute("aria-hidden", "false");
  }
  function closePanel() { $("#panel").classList.remove("open"); $("#panel").setAttribute("aria-hidden", "true"); }
  $("#panel-close").addEventListener("click", closePanel);
  document.addEventListener("keydown", e => { if (e.key === "Escape") { closePanel(); closeRail(); closeSidebar(); } });

  $("#open-notes").addEventListener("click", async () => {
    if (!state.conversationId) return;
    const conv = await api(`/api/conversations/${state.conversationId}`);
    openPanel("Notas de esta conversación", `
      <p class="help">Resumen vivo que el asistente arma para no perder el hilo (qué se habló, qué se decidió, qué quedó pendiente). Es información temporal: pertenece solo a esta conversación y se borra con ella. Podés corregirlo.</p>
      <textarea class="field" id="notes-text" rows="9" placeholder="Todavía no hay notas.">${esc(conv.notas || "")}</textarea>
      <div class="actions"><button class="btn primary" id="notes-save">${icon("check")}Guardar</button><button class="btn ghost" id="notes-clear">Vaciar</button></div>`);
    const saveNotes = async val => { await api(`/api/conversations/${state.conversationId}`, { method: "PATCH", body: { notas: val } }); toast("Notas guardadas"); };
    $("#notes-save").addEventListener("click", () => saveNotes($("#notes-text").value));
    $("#notes-clear").addEventListener("click", () => { $("#notes-text").value = ""; saveNotes(""); });
  });

  function openSources(sources, focusN) {
    openPanel("Fuentes consultadas", `<p class="help">Fragmentos de los documentos del ECyD que el asistente tuvo a la vista. Las marcadas como <strong>citadas</strong> aparecen en la respuesta como [F#].</p>` +
      sources.map(s => `
        <div class="source" data-n="${s.n}">
          <div class="source-head"><span class="source-n">F${s.n}</span><span class="source-title">${esc(s.titulo)}</span>${s.citada ? `<span class="badge red">citada</span>` : ""}</div>
          <div class="source-meta"><span>${esc(TIPOS[s.tipo] || s.tipo)}</span><span>${etapasTxt(s.etapas)}</span><span>Relevancia ${Math.round((s.similitud || 0) * 100)}%</span></div>
          <div class="source-text">${esc(s.texto)}</div>
        </div>`).join(""));
    if (focusN) {
      const el = $(`#panel-body .source[data-n="${focusN}"]`);
      if (el) { setTimeout(() => el.scrollIntoView({ behavior: "smooth", block: "center" }), 230); el.classList.add("flash"); setTimeout(() => el.classList.remove("flash"), 1800); }
    }
  }

  // ------------------------------------------------------------ hilo de chat
  function clearThread() { $$("#thread > :not(#empty)").forEach(el => el.remove()); }
  function scrollBottom(force) {
    const m = $("#main");
    if (force || m.scrollHeight - m.scrollTop - m.clientHeight < 200) m.scrollTop = m.scrollHeight;
  }
  function addUser(text, time) {
    setChatting(true);
    const el = document.createElement("div");
    el.className = "msg user";
    el.innerHTML = `<div class="msg-body"><div class="bubble">${esc(text)}</div><div class="msg-time">${fmtTime(time)} ${icon("checks")}</div></div>`;
    $("#thread").appendChild(el); return el;
  }
  function addAssistant({ text = "", sources = [], weak = false, pending = false, time } = {}) {
    setChatting(true);
    const el = document.createElement("div");
    el.className = "msg assistant";
    el.innerHTML = `<img class="msg-avatar" src="/static/img/cruz-ecyd.svg" alt="">
      <div class="msg-body"><div class="bubble"><div class="weak hidden"></div><div class="md"></div><div class="extras"></div></div>
      <div class="msg-time">${time || !pending ? fmtTime(time) : ""}</div></div>`;
    $("#thread").appendChild(el);
    el._sources = sources;
    const view = {
      el,
      setText(t, streaming) { const md = el.querySelector(".md"); md.innerHTML = t ? markdown(t) : ""; md.classList.toggle("cursor", !!streaming); },
      thinking(msg) { el.querySelector(".md").innerHTML = `<div class="thinking"><span class="spinner"></span>${esc(msg)}</div>`; },
      setWeak(w) {
        const box = el.querySelector(".weak");
        box.classList.toggle("hidden", !w);
        box.textContent = "Encontré poco material del ECyD directamente relacionado con esta consulta; tomá la respuesta con más cautela.";
      },
      setSources(src) { el._sources = src || []; renderSourceBar(el); },
      setTime() { el.querySelector(".msg-time").textContent = fmtTime(); },
      error(msg) { el.querySelector(".bubble").classList.add("error"); el.querySelector(".md").textContent = "No pude generar la respuesta: " + msg; },
      memoryNote(ev) {
        const n = (ev.added?.length || 0) + (ev.updated?.length || 0);
        if (!n || !state.teamId) return;
        const ids = [...(ev.added || []), ...(ev.updated || [])].map(m => m.id);
        const div = document.createElement("div");
        div.className = "memory-note";
        div.innerHTML = `${icon("brain")}Guardé ${n === 1 ? "1 dato" : n + " datos"} en la memoria del equipo · <button class="link-btn">Revisar</button>`;
        div.querySelector("button").addEventListener("click", async () => { await loadMemories(); showView("memoria"); renderMemory(ids); });
        el.querySelector(".extras").appendChild(div);
        loadMemories();
      },
    };
    if (pending) view.thinking("Buscando en los documentos del ECyD…");
    else { view.setText(text); view.setSources(sources); view.setWeak(weak); }
    return view;
  }

  function renderSourceBar(el) {
    const extras = el.querySelector(".extras");
    extras.querySelector(".sources-bar")?.remove();
    const src = el._sources || [];
    if (!src.length) return;
    const cited = src.filter(s => s.citada);
    const show = [];
    (cited.length ? cited : src.slice(0, 2)).forEach(s => { if (!show.some(x => x.titulo === s.titulo) && show.length < 3) show.push(s); });
    const bar = document.createElement("div");
    bar.className = "sources-bar";
    bar.innerHTML = `<span class="label">${icon("file")}Fuentes:</span>` +
      show.map(s => `<button class="src-chip" data-n="${s.n}" title="${esc(s.titulo)}">${icon("file")}<span>${esc(s.titulo)}</span></button>`).join("") +
      `<button class="src-more">Ver ${src.length} fuentes${icon("chevron-right")}</button>`;
    extras.prepend(bar);
    bar.addEventListener("click", e => {
      const chip = e.target.closest(".src-chip");
      if (chip) openSources(src, chip.dataset.n);
      else if (e.target.closest(".src-more")) openSources(src);
    });
  }
  $("#thread").addEventListener("click", e => {
    const b = e.target.closest(".cite");
    if (!b) return;
    const el = b.closest(".msg");
    if (el?._sources?.length) openSources(el._sources, b.dataset.n);
  });

  // ------------------------------------------------------------ enviar
  const input = $("#input");
  function autosize() { input.style.height = "auto"; input.style.height = Math.min(input.scrollHeight, 200) + "px"; }
  input.addEventListener("input", autosize);
  input.addEventListener("keydown", e => {
    if (e.key === "Enter" && !e.shiftKey && !e.isComposing) { e.preventDefault(); $("#composer").requestSubmit(); }
  });
  $$(".quick-card").forEach(b => b.addEventListener("click", () => sendMessage(b.dataset.prompt)));
  $("#stop").addEventListener("click", () => state.controller?.abort());
  $("#composer").addEventListener("submit", e => {
    e.preventDefault();
    const text = input.value.trim();
    if (text) { input.value = ""; autosize(); sendMessage(text); }
  });
  function setBusy(b) {
    $("#send").classList.toggle("hidden", b); $("#stop").classList.toggle("hidden", !b); input.disabled = b;
  }

  async function sendMessage(text) {
    if (!text || state.controller) return;
    if (state.view !== "inicio") showView("inicio");
    addUser(text);
    const view = addAssistant({ pending: true });
    scrollBottom(true); setBusy(true);
    const controller = new AbortController();
    state.controller = controller;
    let answer = "", sources = [], raf = 0;
    const paint = () => { raf = 0; view.setText(answer, true); scrollBottom(); };
    try {
      const res = await fetch("/api/chat", {
        method: "POST", headers: { "Content-Type": "application/json" }, credentials: "same-origin",
        body: JSON.stringify({ message: text, conversation_id: state.conversationId, team_id: state.teamId || null }),
        signal: controller.signal,
      });
      if (res.status === 401) { showLogin(); throw new Error("La sesión venció"); }
      if (!res.ok) { let m = res.statusText; try { m = (await res.json()).detail; } catch {} throw new Error(m); }
      const reader = res.body.getReader(), dec = new TextDecoder();
      let buf = "";
      for (;;) {
        const { value, done } = await reader.read();
        if (done) break;
        buf += dec.decode(value, { stream: true });
        let idx;
        while ((idx = buf.indexOf("\n\n")) >= 0) {
          const raw = buf.slice(0, idx); buf = buf.slice(idx + 2);
          if (!raw.startsWith("data:")) continue;
          const ev = JSON.parse(raw.slice(5));
          if (ev.type === "meta") {
            const isNew = !state.conversationId;
            state.conversationId = ev.conversation.id; state.conversation = ev.conversation;
            sources = ev.sources; view.setWeak(ev.weak_evidence); view.thinking("Pensando la respuesta…");
            updateHeader(); if (isNew) loadConversations();
          } else if (ev.type === "delta") {
            answer += ev.text; if (!raf) raf = requestAnimationFrame(paint);
          } else if (ev.type === "done") {
            if (raf) { cancelAnimationFrame(raf); raf = 0; }
            view.setText(answer, false); view.setSources(ev.sources || sources); view.setTime(); setBusy(false);
          } else if (ev.type === "memory") {
            view.memoryNote(ev);
          } else if (ev.type === "error") {
            if (answer) { view.setText(answer + "\n\n_(La respuesta se interrumpió.)_"); view.setSources(sources); }
            else view.error(ev.message);
          }
        }
      }
    } catch (err) {
      if (err.name === "AbortError") { view.setText(answer ? answer + "\n\n_(Detenido.)_" : "_(Detenido.)_"); view.setSources(sources); }
      else view.error(err.message);
    } finally {
      state.controller = null; setBusy(false); input.focus(); scrollBottom();
    }
  }

  // ------------------------------------------------------------ inicio
  async function boot() {
    try {
      state.config = await api("/api/config");
      applyHeroPhoto(state.config.portada);
      await loadTeams(); await loadConversations();
      updateHeader(); pollHealth();
      if (!state.teams.length) toast("Tip: creá tu equipo para recibir respuestas personalizadas.", 6000);
    } catch (err) { if (err.message !== "No autorizado") toast(err.message); }
  }

  hydrateIcons(); applyTheme(); renderProfile(); showView("inicio");
  (async () => {
    try {
      const s = await (await fetch("/api/session", { credentials: "same-origin" })).json();
      if (s.auth_required && !s.authenticated) { showLogin(); return; }
    } catch {}
    boot();
  })();
})();
