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
    community: P(['<circle cx="12" cy="7" r="2.6"/>', '<circle cx="5.5" cy="10" r="2.1"/>', '<circle cx="18.5" cy="10" r="2.1"/>',
      "M7.5 20c0-2.8 2-4.8 4.5-4.8s4.5 2 4.5 4.8", "M2 19c0-2.2 1.5-3.8 3.5-3.8 1 0 1.8.3 2.5.9", "M22 19c0-2.2-1.5-3.8-3.5-3.8-1 0-1.8.3-2.5.9"]),
    copy: P(['<rect x="8" y="8" width="12" height="12" rx="2"/>', "M16 8V5.5A1.5 1.5 0 0 0 14.5 4h-9A1.5 1.5 0 0 0 4 5.5v9A1.5 1.5 0 0 0 5.5 16H8"]),
    share: P(['<circle cx="18" cy="5" r="2.5"/>', '<circle cx="6" cy="12" r="2.5"/>', '<circle cx="18" cy="19" r="2.5"/>', "m8.2 10.8 7.6-4.4M8.2 13.2l7.6 4.4"]),
    refresh: P(["M20 11a8 8 0 1 0-2.3 5.7", "M20 5v6h-6"]),
    pdf: P(["M14 3H6.5A1.5 1.5 0 0 0 5 4.5v15A1.5 1.5 0 0 0 6.5 21h11a1.5 1.5 0 0 0 1.5-1.5V8z", "M14 3v5h5", "M12 11v6m-3-3 3 3 3-3"]),
    "chevron-left": P(["m15 6-6 6 6 6"]),
    "chat-bubbles": P(["M4 5.5A1.5 1.5 0 0 1 5.5 4h9A1.5 1.5 0 0 1 16 5.5v6a1.5 1.5 0 0 1-1.5 1.5H9l-3.5 3V13H5.5A1.5 1.5 0 0 1 4 11.5z", "M16 8h2.5A1.5 1.5 0 0 1 20 9.5v6a1.5 1.5 0 0 1-1.5 1.5H18v3l-3.5-3H11a1.5 1.5 0 0 1-1.5-1.5V15"]),
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
    tipo_encuentro: "activity", notas: "note", composicion: "users",
  };
  const FIELD_PH = {
    etapa: "Etapa", edades: "Ej.: 12 a 13 años", cantidad_chicos: "Ej.: 9", duracion: "Ej.: 1 h 30 min",
    tipo_encuentro: "Ej.: reunión semanal, salida, convivencia", tema_mensual: "Ej.: La amistad",
    tema_reunion: "Ej.: Amigos que me enriquecen", objetivo: "¿Qué querés que vivan o descubran?",
    situacion_equipo: "Clima, vínculos, participación, dificultades…", notas: "Cualquier otra cosa útil",
  };

  const ETAPAS = [
    { n: 1, nombre: "Primera etapa", edades: "11-12 años" }, { n: 2, nombre: "Segunda etapa", edades: "12-13 años" },
    { n: 3, nombre: "Tercera etapa", edades: "13-14 años" }, { n: 4, nombre: "Cuarta etapa", edades: "15-16 años" },
  ];
  const COMPOSICIONES = [["mixto", "Mixto"], ["solo chicas", "Solo chicas"], ["solo chicos", "Solo chicos"]];
  const ESTADOS = { borrador: "Borrador", planificado: "Planificado", realizado: "Realizado" };
  const CATEGORIA_DOC = { programa: "Programa", ficha: "Ficha", documento: "Documento", recurso: "Recurso" };

  const state = {
    config: { team_fields: [], categorias: [] },
    user: null, programas: null, encuentros: [], month: null,
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
  const userName = () => (state.user?.nombre || "").trim();
  const parseEtapa = v => { const m = String(v || "").match(/[1-4]/); return m ? +m[0] : null; };
  const teamEtapa = t => parseEtapa(t?.perfil?.etapa);
  const etapaInfo = n => (state.programas?.etapas?.[n]) || ETAPAS.find(e => e.n === n) || null;
  const docEtapas = d => [...new Set([...(d.etapas || []), ...(d.duplicados || []).flatMap(x => x.etapas || [])])].sort();
  function fmtDay(s) {
    if (!s) return "Sin fecha";
    const d = new Date(String(s).slice(0, 10) + "T12:00:00");
    return isNaN(d) ? s : d.toLocaleDateString("es-AR", { weekday: "short", day: "numeric", month: "short", year: "numeric" });
  }
  const todayISO = () => { const d = new Date(); d.setMinutes(d.getMinutes() - d.getTimezoneOffset()); return d.toISOString().slice(0, 10); };
  const cap = s => s ? s[0].toUpperCase() + s.slice(1) : "";

  // lee una respuesta en streaming (SSE) y llama a onEvent por cada evento
  async function readSSE(res, onEvent) {
    const reader = res.body.getReader(), dec = new TextDecoder();
    let buf = "";
    for (;;) {
      const { value, done } = await reader.read();
      if (done) break;
      buf += dec.decode(value, { stream: true });
      let idx;
      while ((idx = buf.indexOf("\n\n")) >= 0) {
        const raw = buf.slice(0, idx); buf = buf.slice(idx + 2);
        if (raw.startsWith("data:")) onEvent(JSON.parse(raw.slice(5)));
      }
    }
  }
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

  // ------------------------------------------------------------ acceso (cuentas individuales)
  let authInfo = {};
  // invitación por enlace: https://…/?comunidad=ABCD-2345
  const normCodigo = c => { const x = String(c || "").toUpperCase().replace(/[^A-Z0-9]/g, ""); return x.length === 8 ? `${x.slice(0, 4)}-${x.slice(4)}` : ""; };
  let invite = "";
  try {
    const qp = new URLSearchParams(location.search);
    invite = normCodigo(qp.get("comunidad")) || sessionStorage.getItem("ecyd.invite") || "";
    if (qp.has("comunidad")) { history.replaceState(null, "", location.pathname); }
    if (invite) sessionStorage.setItem("ecyd.invite", invite);
  } catch {}
  const clearInvite = () => { invite = ""; try { sessionStorage.removeItem("ecyd.invite"); } catch {} };

  async function procesarInvitacion(yaUnida) {
    if (yaUnida) { clearInvite(); com.id = yaUnida.id; save("comunidadId", yaUnida.id); toast(`Te sumaste a ${yaUnida.nombre}. La coordinación te va a asignar tu equipo.`, 7000); showView("comunidad"); return; }
    if (!invite) return;
    try {
      const c = await api("/api/comunidades/unirse", { method: "POST", body: { codigo: invite } });
      com.id = c.id; save("comunidadId", c.id);
      toast(`Te sumaste a ${c.nombre}.`, 6000); showView("comunidad");
    } catch (err) { toast("No se pudo usar la invitación: " + err.message, 8000); }
    clearInvite();
  }
  function setAuthTab(tab) {
    $$("[data-auth]").forEach(b => b.classList.toggle("on", b.dataset.auth === tab));
    $("#login-form").classList.toggle("hidden", tab !== "login");
    $("#register-form").classList.toggle("hidden", tab !== "register");
    $("#login-error").textContent = "";
    setTimeout(() => (tab === "login" ? $("#login-email") : $("#reg-nombre")).focus(), 30);
  }
  function showLogin() {
    if (!$("#login").classList.contains("hidden")) return;
    $("#login").classList.remove("hidden");
    fetch("/api/session", { credentials: "same-origin" }).then(r => r.json()).then(s => {
      authInfo = s;
      $("#first-user-note").classList.toggle("hidden", !s.first_user);
      const inv = $("#invite-note");
      inv.classList.toggle("hidden", !invite);
      if (invite) { inv.innerHTML = `Te invitaron a una comunidad del asistente (código <strong>${esc(invite)}</strong>). Creá tu cuenta, o ingresá si ya tenés una, y te sumamos automáticamente.`; $("#reg-codigo").value = invite; }
      $("#reg-codigo").classList.toggle("hidden", !s.registration_requires_code);
      $("#reg-code-help").classList.toggle("hidden", !s.registration_requires_code);
      $("#reg-codigo").required = !!s.registration_requires_code;
      setAuthTab(s.first_user || invite ? "register" : "login");
    }).catch(() => setAuthTab("login"));
  }
  $$("[data-auth]").forEach(b => b.addEventListener("click", () => setAuthTab(b.dataset.auth)));
  async function authPost(path, body) {
    const res = await fetch(path, { method: "POST", credentials: "same-origin", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.detail || res.statusText);
    return data;
  }
  async function signedIn(user, unida) {
    if (load("uid") !== user.id) { save("teamId", null); state.teamId = ""; }
    save("uid", user.id);
    state.user = user;
    $("#login").classList.add("hidden");
    $("#login-pass").value = ""; $("#reg-pass").value = ""; $("#reg-codigo").value = "";
    renderProfile(); await boot();
    await procesarInvitacion(unida);
  }
  $("#login-form").addEventListener("submit", async e => {
    e.preventDefault();
    $("#login-error").textContent = "";
    try {
      const r = await authPost("/api/login", { email: $("#login-email").value.trim(), password: $("#login-pass").value });
      signedIn(r.user);
    } catch (err) { $("#login-error").textContent = err.message; }
  });
  $("#register-form").addEventListener("submit", async e => {
    e.preventDefault();
    $("#login-error").textContent = "";
    try {
      const r = await authPost("/api/register", {
        nombre: $("#reg-nombre").value.trim(), email: $("#reg-email").value.trim(), password: $("#reg-pass").value,
        rol: $("#reg-rol").value.trim(), codigo: $("#reg-codigo").value.trim(), comunidad: invite,
      });
      signedIn(r.user, r.comunidad);
      const n = r.datos_asignados || {};
      if (n.equipos || n.conversaciones) toast(`Bienvenido/a. Quedaron en tu cuenta ${n.equipos || 0} equipo(s) y ${n.conversaciones || 0} conversación(es) que ya existían.`, 7000);
      else if (!r.comunidad) toast("Cuenta creada. Empezá creando tu equipo o sumate a tu comunidad.", 5000);
    } catch (err) { $("#login-error").textContent = err.message; }
  });
  async function logout() {
    await fetch("/api/logout", { method: "POST", credentials: "same-origin" }).catch(() => {});
    save("teamId", null); location.reload();
  }

  // ------------------------------------------------------------ tema y perfil
  function applyTheme() {
    const t = load("tema") || "auto";
    if (t === "auto") document.documentElement.removeAttribute("data-theme");
    else document.documentElement.setAttribute("data-theme", t);
  }
  function renderProfile() {
    const n = userName();
    $("#profile-name").textContent = n || "Tu nombre";
    $("#profile-role").textContent = state.user?.rol || "Responsable de equipo";
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
    if (name !== "chat") stopChatPoll();
    state.view = name;
    $$(".view").forEach(v => v.classList.toggle("hidden", v.id !== "view-" + name));
    $$(".nav-item").forEach(a => a.classList.toggle("active", a.dataset.view === name));
    closeSidebar(); closeRail();
    $("#main").scrollTop = 0;
    const renderers = { chat: renderChat, comunidad: renderComunidad, preparar: renderPreparar, encuentros: renderEncuentros, conversaciones: renderConversations, equipos: renderTeams, documentos: renderDocuments, memoria: renderMemory, configuracion: renderSettings };
    renderers[name]?.();
    if (name === "inicio") setTimeout(() => $("#input").focus(), 50);
  }
  document.addEventListener("click", e => {
    const a = e.target.closest("[data-view]");
    if (!a) return;
    e.preventDefault();
    if (a.dataset.view === "encuentros") encOpen = null;
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
    renderContext(); updateHeader(); loadMonth();
    await loadMemories();
  }
  function setTeam(id) {
    state.teamId = id || ""; save("teamId", state.teamId);
    if (state.teamId && prep.teamId !== state.teamId) { prep.teamId = state.teamId; prep.selected = []; prep.temaManual = false; }
    $("#team-select").value = state.teamId;
    newConversation(false);
    renderContext(); updateHeader(); loadMemories(); loadConversations(); loadMonth(); pollHealth();
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
    const comLine = t.comunidad ? `<div class="ctx-item">${icon("community")}<div><div class="k">Comunidad</div><div class="v">${esc(t.comunidad.nombre)}${t.responsables?.length ? " · " + t.responsables.map(r => esc(r.nombre.split(" ")[0])).join(", ") : ""}</div></div></div>` : "";
    list.innerHTML = comLine + (fields.length ? fields.map(f => `
      <div class="ctx-item">${icon(FIELD_ICONS[f.key] || "info")}
        <div><div class="k">${esc(f.label)}</div><div class="v">${esc(t.perfil[f.key])}</div></div></div>`).join("")
      : `<p class="ctx-empty">Todavía no cargaste datos de este equipo. Tocá <strong>Editar</strong> para completar etapa, edades, tema mensual y objetivo.</p>`);
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
          <div class="row-sub">${esc(t.perfil.etapa || "Etapa sin definir")}${t.perfil.edades ? " · " + esc(t.perfil.edades) : ""}${t.perfil.cantidad_chicos ? " · " + esc(t.perfil.cantidad_chicos) + " adolescentes" : ""}${t.perfil.composicion ? " · " + esc(cap(t.perfil.composicion)) : ""}</div>
          ${t.perfil.tema_mensual ? `<div class="row-sub">Tema mensual: ${esc(t.perfil.tema_mensual)}</div>` : ""}
          ${t.comunidad ? `<div class="row-sub">${icon("community", "ri")}${esc(t.comunidad.nombre)}${t.responsables?.length > 1 ? ` · con ${t.responsables.filter(r => r.user_id !== state.user?.id).map(r => esc(r.nombre.split(" ")[0])).join(", ")}` : ""}</div>`
            : (com.list.length ? `<div class="row-sub"><button class="link-btn" data-mover="${t.id}">${icon("community", "ri")}Llevar a una comunidad</button></div>` : "")}
          <div class="actions">
            ${t.id === state.teamId ? "" : `<button class="btn primary small" data-use="${t.id}">Usar este equipo</button>`}
            <button class="btn small" data-edit="${t.id}">${icon("edit")}Editar</button>
            <button class="btn small ghost" data-prep="${t.id}">${icon("sparkle")}Preparar encuentro</button>
          </div>
        </div>`).join("")}</div>`
      : `<div class="empty-state"><img src="/static/img/cruz-ecyd.svg" alt=""><p>Todavía no creaste ningún equipo.</p>
          <button class="btn primary" id="team-new-2">${icon("plus")}Crear mi primer equipo</button></div>`}`;
    $("#team-new")?.addEventListener("click", () => renderTeamForm(null));
    $("#team-new-2")?.addEventListener("click", () => renderTeamForm(null));
    $$("[data-use]", v).forEach(b => b.addEventListener("click", () => { setTeam(b.dataset.use); renderTeams(); toast("Equipo activo actualizado"); }));
    $$("[data-edit]", v).forEach(b => b.addEventListener("click", () => renderTeamForm(state.teams.find(t => t.id === b.dataset.edit))));
    $$("[data-prep]", v).forEach(b => b.addEventListener("click", () => { if (b.dataset.prep !== state.teamId) setTeam(b.dataset.prep); showView("preparar"); }));
    $$("[data-mover]", v).forEach(b => b.addEventListener("click", () => {
      const t = state.teams.find(x => x.id === b.dataset.mover);
      openPanel("Llevar a una comunidad", `<p class="help">“${esc(t.nombre)}” pasa a ser un equipo de la comunidad. Vos seguís como responsable, con su memoria y sus encuentros. La coordinación va a ver su planificación (no la memoria) y puede sumar co-responsables.</p>
        <select class="field" id="mv-com">${com.list.map(c => `<option value="${esc(c.id)}">${esc(c.nombre)}</option>`).join("")}</select>
        <div class="actions"><button class="btn primary" id="mv-ok">${icon("check")}Llevar a la comunidad</button></div>`);
      $("#mv-ok").addEventListener("click", async () => {
        try { await api(`/api/teams/${t.id}/comunidad`, { method: "POST", body: { community_id: $("#mv-com").value } }); closePanel(); await loadTeams(); renderTeams(); toast("Equipo sumado a la comunidad"); }
        catch (err) { toast(err.message); }
      });
    }));
  }

  function renderTeamForm(team) {
    const v = $("#view-equipos"), p = team?.perfil || {};
    const fields = state.config.team_fields.map(f => {
      const long = ["situacion_equipo", "objetivo", "notas"].includes(f.key);
      const val = esc(p[f.key] || "");
      const lbl = `<label for="f-${f.key}">${icon(FIELD_ICONS[f.key] || "info")}${esc(f.label)}</label>`;
      if (f.key === "etapa") {
        const cur = parseEtapa(p.etapa);
        return `<div class="field-wrap">${lbl}<select class="field" id="f-etapa" data-k="etapa">
          <option value="">Elegí la etapa…</option>${ETAPAS.map(e => `<option value="Etapa ${e.n}" ${cur === e.n ? "selected" : ""}>Etapa ${e.n} · ${e.nombre} (${e.edades})</option>`).join("")}</select></div>`;
      }
      if (f.key === "composicion") {
        const cur = (p.composicion || "").toLowerCase();
        return `<div class="field-wrap">${lbl}<select class="field" id="f-composicion" data-k="composicion">
          <option value="">Sin indicar</option>${COMPOSICIONES.map(([v, l]) => `<option value="${v}" ${cur === v ? "selected" : ""}>${l}</option>`).join("")}</select></div>`;
      }
      return `<div class="field-wrap ${long ? "wide" : ""}">${lbl}` +
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
    $("#f-etapa")?.addEventListener("change", e => {
      const info = ETAPAS.find(x => x.n === parseEtapa(e.target.value)), ed = $("#f-edades");
      if (info && ed && !ed.value.trim()) ed.value = info.edades;
    });
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

  // ------------------------------------------------------------ documentos (por etapa)
  let docTab = null;
  async function ensureDocs() { state.docs ||= await api("/api/documents"); return state.docs; }
  async function ensureProgramas() { state.programas ||= await api("/api/programas"); return state.programas; }

  function docRow(d, extra = "") {
    const et = docEtapas(d);
    return `<div class="row-item clickable doc-row" data-doc="${esc(d.id)}">${icon(d.categoria === "ficha" ? "note" : d.categoria === "documento" ? "book" : "file")}
      <div class="row-main"><div class="row-title">${esc(d.titulo)}</div>
        <div class="row-sub"><span class="badge ${d.categoria === "ficha" || d.autoridad?.nivel <= 2 ? "red" : ""}">${esc(CATEGORIA_DOC[d.categoria] || TIPOS[d.tipo] || d.tipo)}</span><span>${etapasTxt(et)}</span>${extra}
          ${(d.temas || []).slice(0, 3).map(t => `<span class="badge">${esc(t.replaceAll("_", " "))}</span>`).join("")}</div></div>
      ${icon("chevron-right", "chev")}</div>`;
  }
  function bindDocRows(root) { $$("[data-doc]", root).forEach(r => r.addEventListener("click", e => { e.preventDefault(); openDoc(r.dataset.doc); })); }

  async function renderDocuments() {
    const v = $("#view-documentos");
    docTab ||= String(teamEtapa(currentTeam()) || 1);
    v.innerHTML = `<div class="page-head"><div><h1>Documentos del ECyD</h1>
      <p>Organizados por etapa: el programa, las fichas de cada mes, los documentos y los recursos. El asistente busca primero en la etapa de tu grupo.</p></div></div>
      <div class="filters">
        <div class="seg tabs" id="doc-tabs">${[1, 2, 3, 4].map(n => `<button data-tab="${n}">Etapa ${n}</button>`).join("")}<button data-tab="general">Generales</button></div>
        <input class="field" type="search" id="doc-q" placeholder="Buscar ficha o documento…" style="max-width:280px;margin-left:auto">
      </div>
      <div id="doc-body"><div class="thinking"><span class="spinner"></span>Cargando…</div></div>`;
    try { await Promise.all([ensureDocs(), ensureProgramas()]); }
    catch (err) { $("#doc-body").innerHTML = `<p class="error-text">${esc(err.message)}</p>`; return; }
    const paintTabs = () => $$("#doc-tabs button").forEach(b => b.classList.toggle("on", b.dataset.tab === docTab));
    $$("#doc-tabs button").forEach(b => b.addEventListener("click", () => { docTab = b.dataset.tab; $("#doc-q").value = ""; paintTabs(); draw(); }));
    $("#doc-q").addEventListener("input", debounce(draw, 120));
    paintTabs(); draw();

    async function draw() {
      const body = $("#doc-body"), q = $("#doc-q").value.trim().toLowerCase();
      if (q) {
        const rows = state.docs.filter(d => [d.titulo, (d.temas || []).join(" "), d.categoria, d.carpeta].join(" ").toLowerCase().includes(q));
        body.innerHTML = `<p class="muted small-note">${rows.length} resultados en todas las etapas</p><div class="list">${rows.map(d => docRow(d)).join("")}</div>`;
        bindDocRows(body); return;
      }
      if (docTab === "general") {
        const gen = state.docs.filter(d => !docEtapas(d).length);
        body.innerHTML = ["documento", "ficha", "recurso", "programa"].map(c => {
          const rows = gen.filter(d => d.categoria === c);
          return rows.length ? `<div class="section-title">${esc(CATEGORIA_DOC[c])}s generales · ${rows.length}</div><div class="list">${rows.map(d => docRow(d)).join("")}</div>` : "";
        }).join("") || `<div class="empty-state"><p>No hay documentos generales.</p></div>`;
        bindDocRows(body); return;
      }
      const n = +docTab, info = state.programas.etapas?.[docTab];
      const deEtapa = state.docs.filter(d => docEtapas(d).includes(n));
      const actual = await api(`/api/programa?etapa=${n}`).catch(() => null);
      const actuales = new Set((actual?.periodos || []).map(p => p.periodo));
      const enCal = new Set();
      let html = "";
      if (info) {
        const r = info.resumen || {};
        html += `<div class="form-card prog-card">
          <div class="prog-head"><div><div class="prog-kicker">Programa de la etapa</div><h2>${esc(info.nombre)} <span class="muted">· ${esc(info.edades)}</span></h2></div>
            <button class="btn primary small" data-view="preparar">${icon("sparkle")}Preparar encuentro</button></div>
          <div class="prog-grid">
            <div><div class="k">Alianza</div><p>${esc(r.alianza || "—")}</p></div>
            <div><div class="k">Amor</div><p>${esc(r.amor || "—")}</p></div>
            <div><div class="k">Virtud</div><p>${esc(r.virtud || "—")}</p></div>
            <div><div class="k">Símbolo</div><p>${esc(r.simbolo || "—")}</p></div>
          </div>
          ${info.temas_centrales ? `<details class="prog-more"><summary>Temas centrales y necesidades de la etapa</summary><p>${esc(info.temas_centrales)}</p>
            ${(info.necesidades || []).length ? `<ul class="dot-list">${info.necesidades.map(x => `<li>${esc(x)}</li>`).join("")}</ul>` : ""}</details>` : ""}
          <p class="src-note">${icon("book")}Fuente: ${esc(state.programas.fuente?.titulo || "Formando apóstoles en el ECyD")}. ${esc(state.programas.nota_calendario || "")}</p>
        </div>`;
        html += `<div class="section-title">Fichas por mes</div><div class="cal">` + (info.calendario || []).map(p => {
          p.fichas.forEach(f => enCal.add(f.doc_id));
          const now = actuales.has(p.periodo);
          return `<div class="cal-row ${now ? "now" : ""}"><div class="cal-month">${esc(cap((state.programas.periodos.find(x => x.periodo === p.periodo) || {}).label || p.periodo))}${now ? `<span class="badge red">Ahora</span>` : ""}</div>
            <div class="cal-fichas">${p.fichas.map(f => `<button class="ficha-chip" data-doc="${esc(f.doc_id)}">${icon("note")}${esc(f.titulo)}</button>`).join("")}</div></div>`;
        }).join("") + `</div>`;
        const lit = info.tiempos_liturgicos || [];
        if (lit.length) html += `<div class="section-title">Tiempos litúrgicos</div><div class="cal">${lit.map(t => `<div class="cal-row"><div class="cal-month">${esc(cap(t.tiempo_liturgico.replaceAll("_", " ")))}</div>
          <div class="cal-fichas">${t.fichas.map(f => { enCal.add(f.doc_id); return `<button class="ficha-chip" data-doc="${esc(f.doc_id)}">${icon("note")}${esc(f.titulo)}</button>`; }).join("")}</div></div>`).join("")}</div>`;
      }
      const otras = deEtapa.filter(d => d.categoria === "ficha" && !enCal.has(d.id));
      if (otras.length) html += `<div class="section-title">Otras fichas de la etapa · ${otras.length}</div><div class="list">${otras.map(d => docRow(d)).join("")}</div>`;
      for (const c of ["documento", "recurso"]) {
        const rows = deEtapa.filter(d => d.categoria === c || (c === "documento" && d.categoria === "programa"));
        if (rows.length) html += `<div class="section-title">${c === "documento" ? "Documentos" : "Recursos adicionales"} · ${rows.length}</div><div class="list">${rows.map(d => docRow(d)).join("")}</div>`;
      }
      body.innerHTML = html || `<div class="empty-state"><p>No hay material cargado para esta etapa.</p></div>`;
      hydrateIcons(body); bindDocRows(body);
    }
  }

  async function openDoc(id) {
    openPanel("Documento", `<div class="thinking"><span class="spinner"></span>Cargando…</div>`);
    try {
      const d = await api(`/api/documents/${encodeURIComponent(id)}`);
      const et = docEtapas(d), grupo = teamEtapa(currentTeam());
      const avanzada = grupo && et.length && Math.min(...et) > grupo;
      $("#panel-title").textContent = CATEGORIA_DOC[d.categoria] || "Documento";
      $("#panel-body").innerHTML = `
        <h2 class="doc-title">${esc(d.titulo)}</h2>
        <div class="source-meta"><span>${esc(TIPOS[d.tipo] || d.tipo)}</span><span>${etapasTxt(et)}</span>${d.carpeta ? `<span>${esc(d.carpeta)}</span>` : ""}</div>
        ${avanzada ? `<div class="weak">Este material es de una etapa más avanzada que la de tu grupo (${esc(currentTeam().perfil.etapa)}). Usalo solo si tenés un motivo claro.</div>` : ""}
        <div class="actions">
          ${d.categoria === "ficha" ? `<button class="btn primary small" id="doc-prep">${icon("sparkle")}Preparar encuentro con esta ficha</button>` : ""}
          <button class="btn small" id="doc-ask">${icon("chat")}Preguntar</button></div>
        <div class="doc-text">${esc(d.texto || "Sin texto disponible.").split(/\n{2,}/).map(p => `<p>${p.replace(/-\n(?=\p{Ll})/gu, "").replace(/\n/g, " ")}</p>`).join("")}</div>`;
      $("#doc-prep")?.addEventListener("click", () => { closePanel(); prep.preselect = d.id; showView("preparar"); });
      $("#doc-ask").addEventListener("click", () => {
        closePanel(); newConversation(); $("#input").value = `¿Qué propone el documento “${d.titulo}” y cómo puedo aprovecharlo con mi equipo?`; autosize(); $("#input").focus();
      });
    } catch (err) { $("#panel-body").innerHTML = `<p class="error-text">${esc(err.message)}</p>`; }
  }

  // ------------------------------------------------------------ configuración
  async function renderSettings() {
    const v = $("#view-configuracion");
    const tema = load("tema") || "auto";
    const h = state.health || {}, u = state.user || {};
    v.innerHTML = `
      <div class="page-head"><div><h1>Configuración</h1><p>Tu cuenta es personal: tus equipos, encuentros y conversaciones solo los ves vos.</p></div></div>
      <form class="form-card" id="profile-form">
        <div class="form-grid">
          <div class="field-wrap"><label for="p-nombre">${icon("user-pin")}Tu nombre</label><input class="field" id="p-nombre" value="${esc(u.nombre || "")}" required maxlength="120"></div>
          <div class="field-wrap"><label for="p-rol">${icon("users")}Tu rol</label><input class="field" id="p-rol" value="${esc(u.rol || "")}" placeholder="Responsable de equipo" maxlength="120"></div>
          <div class="field-wrap wide"><label>${icon("info")}Email</label><input class="field" value="${esc(u.email || "")}" disabled></div>
        </div>
        <div class="actions" style="margin-top:14px"><button class="btn primary" type="submit">${icon("check")}Guardar perfil</button></div>
      </form>
      <div class="section-title">Contraseña</div>
      <form class="form-card" id="pass-form">
        <div class="form-grid">
          <div class="field-wrap"><label for="pw-actual">Contraseña actual</label><input class="field" type="password" id="pw-actual" autocomplete="current-password" required></div>
          <div class="field-wrap"><label for="pw-nueva">Contraseña nueva</label><input class="field" type="password" id="pw-nueva" autocomplete="new-password" minlength="8" required></div>
        </div>
        <div class="actions" style="margin-top:14px"><button class="btn" type="submit">${icon("check")}Cambiar contraseña</button></div>
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
      </dl></div>
      <div class="actions" style="margin-top:18px"><button class="btn" id="logout">${icon("logout")}Cerrar sesión</button></div>`;
    $("#profile-form").addEventListener("submit", async e => {
      e.preventDefault();
      try {
        state.user = await api("/api/me", { method: "PUT", body: { nombre: $("#p-nombre").value.trim(), rol: $("#p-rol").value.trim() } });
        renderProfile(); toast("Perfil guardado");
      } catch (err) { toast(err.message); }
    });
    $("#pass-form").addEventListener("submit", async e => {
      e.preventDefault();
      try {
        await api("/api/me/password", { method: "POST", body: { actual: $("#pw-actual").value, nueva: $("#pw-nueva").value } });
        e.target.reset(); toast("Contraseña actualizada");
      } catch (err) { toast(err.message); }
    });
    $$("#theme-seg button").forEach(b => b.addEventListener("click", () => {
      save("tema", b.dataset.t === "auto" ? null : b.dataset.t); applyTheme();
      $$("#theme-seg button").forEach(x => x.classList.toggle("on", x === b));
    }));
    $("#logout").addEventListener("click", logout);
  }

  // ------------------------------------------------------------ "Para este mes" (columna derecha)
  async function loadMonth() {
    const body = $("#month-body"), t = currentTeam();
    state.month = null;
    if (!t) { body.innerHTML = `<p class="ctx-empty">Elegí un equipo para ver qué propone el programa de su etapa en este momento del año.</p>`; return; }
    if (!teamEtapa(t)) {
      body.innerHTML = `<p class="ctx-empty">Indicá la <strong>etapa</strong> del equipo para ver las fichas que propone el programa.</p>`;
      return;
    }
    try {
      const s = state.month = await api(`/api/programa?team_id=${encodeURIComponent(t.id)}`);
      if (!s.disponible) { body.innerHTML = `<p class="ctx-empty">No hay programa cargado para esta etapa.</p>`; return; }
      const per = s.periodos.map(p => p.label).join(" y ");
      body.innerHTML = `
        <div class="month-meta">${esc(cap(s.mes))} · ${esc(s.nombre)}</div>
        <p class="card-note">${s.receso ? `Receso de verano: el programa retoma en marzo con estas fichas.` : `Según el programa de esta etapa, para ${esc(per)}:`}</p>
        <ul class="month-list">${s.fichas.slice(0, 5).map(f => `<li><button class="link-li" data-prep-ficha="${esc(f.doc_id)}">${icon("note")}${esc(f.titulo)}</button></li>`).join("") || `<li class="muted">Sin fichas asignadas a este período.</li>`}</ul>
        ${s.liturgico ? `<div class="month-lit">${icon("sparkle")}<span>${esc(s.liturgico.nombre)} ${s.liturgico.en_curso ? "(en curso)" : "(se acerca)"}${s.liturgico.fichas?.length ? `: ${s.liturgico.fichas.map(f => `<button class="link-btn" data-prep-ficha="${esc(f.doc_id)}">${esc(f.titulo)}</button>`).join(", ")}` : ""}</span></div>` : ""}`;
      $$("[data-prep-ficha]", body).forEach(b => b.addEventListener("click", () => { prep.preselect = b.dataset.prepFicha; showView("preparar"); }));
    } catch { body.innerHTML = `<p class="ctx-empty">No se pudo cargar el programa.</p>`; }
  }

  // ------------------------------------------------------------ encuentros (datos)
  async function loadEncuentros() {
    state.encuentros = await api("/api/encuentros").catch(() => []);
    return state.encuentros;
  }
  const encDeEquipo = id => state.encuentros.filter(e => e.team_id === id);
  function encMeta(e) {
    return [e.team_nombre || state.teams.find(t => t.id === e.team_id)?.nombre, e.etapa ? `Etapa ${e.etapa}` : "", fmtDay(e.fecha),
      e.cantidad ? `${e.cantidad} chicos` : "", e.composicion ? cap(e.composicion) : "", e.duracion].filter(Boolean);
  }

  // ------------------------------------------------------------ preparar encuentro
  const prep = { teamId: "", prog: null, selected: [], fichaInfo: {}, temaManual: false, preselect: null, controller: null };

  async function renderPreparar() {
    const v = $("#view-preparar");
    if (prep.controller) return; // generando: no redibujar
    if (!state.teams.length) {
      v.innerHTML = `<div class="page-head"><div><h1>Preparar encuentro</h1></div></div>
        <div class="empty-state"><img src="/static/img/cruz-ecyd.svg" alt=""><p>Para preparar un encuentro primero creá tu equipo e indicá su etapa.</p>
        <button class="btn primary" id="prep-team">${icon("plus")}Crear mi equipo</button></div>`;
      $("#prep-team").addEventListener("click", () => { showView("equipos"); renderTeamForm(null); });
      return;
    }
    if (!prep.teamId || !state.teams.some(t => t.id === prep.teamId)) prep.teamId = state.teamId || state.teams[0].id;
    if (prep.done) { prep.selected = []; prep.temaManual = false; prep.done = false; }
    if (prep.preselect && !prep.selected.includes(prep.preselect)) { prep.selected = [prep.preselect]; prep.temaManual = false; }
    const t = state.teams.find(x => x.id === prep.teamId), p = t.perfil || {}, etapa = teamEtapa(t);
    v.innerHTML = `
      <div class="page-head"><div><h1>Preparar encuentro</h1>
        <p>Elegí el grupo, mirá qué propone el programa de su etapa para este momento del año y generá una propuesta basada en las fichas. Después la adaptás y la guardás.</p></div></div>

      <div class="step-card">
        <div class="step-head"><span class="step-n">1</span><h3>Grupo</h3></div>
        <div class="step-row">
          <select id="prep-team-sel" class="field">${state.teams.map(x => `<option value="${esc(x.id)}" ${x.id === t.id ? "selected" : ""}>${esc(x.nombre)}</option>`).join("")}</select>
          <button class="btn small ghost" id="prep-edit-team">${icon("edit")}Editar datos</button>
        </div>
        <div class="pill-row">
          <span class="pill ${etapa ? "on" : "warn"}">${icon("layers")}${etapa ? `Etapa ${etapa}` : "Etapa sin definir"}</span>
          ${p.edades ? `<span class="pill">${icon("calendar")}${esc(p.edades)}</span>` : ""}
          ${p.cantidad_chicos ? `<span class="pill">${icon("users")}${esc(p.cantidad_chicos)} chicos</span>` : ""}
          ${p.composicion ? `<span class="pill">${icon("users")}${esc(cap(p.composicion))}</span>` : ""}
        </div>
        ${etapa ? "" : `<div class="weak">Sin la etapa no puedo ubicar el encuentro en el programa. <button class="link-btn" id="prep-set-etapa">Indicar etapa</button></div>`}
        <div id="prep-hist"></div>
      </div>

      <div class="step-card">
        <div class="step-head"><span class="step-n">2</span><h3>Tema y fichas</h3></div>
        <div id="prep-prog"><div class="thinking"><span class="spinner"></span>Buscando el programa de la etapa…</div></div>
        <div class="field-wrap" style="margin-top:14px"><label for="prep-tema">${icon("target")}Tema del encuentro</label>
          <input class="field" id="prep-tema" maxlength="300" placeholder="Elegí una ficha arriba o escribí otro tema"></div>
        <div class="field-wrap ficha-search"><label for="prep-buscar">${icon("search")}Buscar otra ficha</label>
          <input class="field" id="prep-buscar" type="search" placeholder="Ej.: amistad, oración, servicio…" autocomplete="off">
          <div id="prep-buscar-res" class="search-results hidden"></div></div>
        <div id="prep-sel" class="sel-list"></div>
      </div>

      <div class="step-card">
        <div class="step-head"><span class="step-n">3</span><h3>Datos del encuentro</h3><span class="muted small-note">Opcional: si no los cambiás, uso los del grupo.</span></div>
        <div class="form-grid">
          <div class="field-wrap"><label for="prep-fecha">${icon("calendar")}Fecha</label><input class="field" type="date" id="prep-fecha" value="${todayISO()}"></div>
          <div class="field-wrap"><label for="prep-duracion">${icon("clock")}Duración</label><input class="field" id="prep-duracion" value="${esc(p.duracion || "")}" placeholder="Ej.: 1 h 30 min"></div>
          <div class="field-wrap"><label for="prep-cantidad">${icon("users")}Cantidad de chicos</label><input class="field" type="number" min="1" max="200" id="prep-cantidad" value="${esc(parseInt(p.cantidad_chicos) || "")}"></div>
          <div class="field-wrap"><label for="prep-comp">${icon("users")}Composición</label><select class="field" id="prep-comp">
            <option value="">Sin indicar</option>${COMPOSICIONES.map(([val, l]) => `<option value="${val}" ${(p.composicion || "").toLowerCase() === val ? "selected" : ""}>${l}</option>`).join("")}</select></div>
          <div class="field-wrap wide"><label for="prep-notas">${icon("note")}¿Algo a tener en cuenta?</label>
            <textarea class="field" id="prep-notas" rows="2" maxlength="2000" placeholder="Ej.: es al aire libre, vienen dos chicos nuevos, quiero cerrar con un momento de oración…"></textarea></div>
        </div>
      </div>

      <div class="prep-go">
        <button class="btn primary big" id="prep-generar">${icon("sparkle")}Generar propuesta</button>
        <span class="muted small-note">La propuesta se basa en el programa y las fichas de la etapa, y queda guardada como borrador en “Mis encuentros”.</span>
      </div>
      <div id="prep-out"></div>`;

    $("#prep-team-sel").addEventListener("change", e => { prep.teamId = e.target.value; prep.selected = []; prep.preselect = null; prep.temaManual = false; if (e.target.value !== state.teamId) setTeam(e.target.value); renderPreparar(); });
    const editTeam = () => { showView("equipos"); renderTeamForm(t); };
    $("#prep-edit-team").addEventListener("click", editTeam);
    $("#prep-set-etapa")?.addEventListener("click", editTeam);
    $("#prep-tema").addEventListener("input", () => { prep.temaManual = !!$("#prep-tema").value.trim(); });
    $("#prep-generar").addEventListener("click", generarEncuentro);
    setupFichaSearch(etapa);
    renderHistorial(t);

    // programa de la etapa en este momento del año
    const box = $("#prep-prog");
    if (!etapa) { box.innerHTML = `<p class="muted">Cuando indiques la etapa vas a ver acá las fichas que propone el programa para este mes. Mientras tanto, podés escribir el tema.</p>`; syncSelected(); return; }
    try {
      const s = prep.prog = await api(`/api/programa?team_id=${encodeURIComponent(t.id)}`);
      if (!s.disponible) { box.innerHTML = `<p class="muted">No hay programa cargado para esta etapa.</p>`; syncSelected(); return; }
      const r = s.resumen || {};
      const fichaBtn = (f, periodo) => { prep.fichaInfo[f.doc_id] = { ...f, periodo, etapas: [etapa] };
        return `<button class="ficha-card" data-pick="${esc(f.doc_id)}"><span class="ficha-check">${icon("check")}</span><span class="ficha-txt"><strong>${esc(f.titulo)}</strong>
          <small>${(f.temas || []).slice(0, 3).map(x => x.replaceAll("_", " ")).join(" · ") || "Ficha de la etapa"}</small></span>
          <span class="icon-btn ficha-ver" data-ver="${esc(f.doc_id)}" title="Leer la ficha">${icon("book")}</span></button>`; };
      box.innerHTML = `
        <div class="prog-banner">${icon("compass")}<div><strong>Según el programa de la ${esc(s.nombre.toLowerCase())}</strong> (${esc(s.edades)}) — ${esc(cap(s.mes))}${s.receso ? " · receso: el programa retoma en marzo" : ""}
          <div class="muted small-note">${esc(r.amor || "")} ${esc(r.virtud || "")}</div></div></div>
        <div class="sub-label">Fichas para ${esc(s.periodos.map(x => x.label).join(" y "))}</div>
        <div class="ficha-grid">${s.fichas.map(f => fichaBtn(f, f.periodo)).join("") || `<p class="muted">El programa no asigna fichas a este período.</p>`}</div>
        ${s.liturgico?.fichas?.length ? `<div class="sub-label">${esc(s.liturgico.nombre)} ${s.liturgico.en_curso ? "· en curso" : "· se acerca"}</div>
          <div class="ficha-grid">${s.liturgico.fichas.map(f => fichaBtn(f, s.liturgico.clave)).join("")}</div>` : ""}
        ${s.proximo ? `<details class="prog-more"><summary>Próximo período: ${esc(s.proximo.label)}</summary>
          <div class="ficha-grid">${s.proximo.fichas.map(f => fichaBtn(f, s.proximo.periodo)).join("")}</div></details>` : ""}
        <p class="muted small-note">El programa es una guía: podés seguirlo o elegir otro tema. Vos decidís.</p>`;
      $$("[data-pick]", box).forEach(b => b.addEventListener("click", e => {
        if (e.target.closest("[data-ver]")) { e.stopPropagation(); openDoc(e.target.closest("[data-ver]").dataset.ver); return; }
        toggleFicha(b.dataset.pick);
      }));
      hydrateIcons(box);
    } catch (err) { box.innerHTML = `<p class="error-text">${esc(err.message)}</p>`; }
    syncSelected();
  }

  function toggleFicha(id, info) {
    if (info) prep.fichaInfo[id] = info;
    const i = prep.selected.indexOf(id);
    if (i >= 0) prep.selected.splice(i, 1);
    else { if (prep.selected.length >= 3) { toast("Podés elegir hasta 3 fichas."); return; } prep.selected.push(id); }
    syncSelected();
  }

  function fichaData(id) {
    if (prep.fichaInfo[id]) return prep.fichaInfo[id];
    const d = (state.docs || []).find(x => x.id === id);
    return d ? { doc_id: d.id, titulo: d.titulo, etapas: docEtapas(d) } : { doc_id: id, titulo: "Ficha" };
  }

  function syncSelected() {
    const box = $("#prep-sel"); if (!box) return;
    $$("[data-pick]").forEach(b => b.classList.toggle("on", prep.selected.includes(b.dataset.pick)));
    const etapa = teamEtapa(state.teams.find(t => t.id === prep.teamId));
    box.innerHTML = prep.selected.map(id => {
      const f = fichaData(id), et = f.etapas || [];
      const adv = etapa && et.length && Math.min(...et) > etapa;
      const otra = etapa && et.length && !et.includes(etapa);
      return `<div class="sel-item ${adv ? "warn" : ""}">${icon("note")}<span><strong>${esc(f.titulo)}</strong>
        ${adv ? `<small>Es de una etapa más avanzada (${etapasTxt(et)}). Usala solo si tenés un motivo claro.</small>` : otra ? `<small>Material de ${etapasTxt(et)}: se adapta a tu grupo.</small>` : ""}</span>
        <button class="icon-btn" data-unpick="${esc(id)}" aria-label="Quitar">${icon("x")}</button></div>`;
    }).join("");
    $$("[data-unpick]", box).forEach(b => b.addEventListener("click", () => toggleFicha(b.dataset.unpick)));
    const tema = $("#prep-tema");
    if (tema && !prep.temaManual) tema.value = prep.selected.length ? fichaData(prep.selected[0]).titulo : "";
    prep.preselect = null;
  }

  function setupFichaSearch(etapa) {
    const inp = $("#prep-buscar"), res = $("#prep-buscar-res");
    const run = debounce(async () => {
      const q = inp.value.trim().toLowerCase();
      if (!q) { res.classList.add("hidden"); return; }
      try { await ensureDocs(); } catch { res.innerHTML = `<div class="sr-empty">Los documentos todavía se están cargando…</div>`; res.classList.remove("hidden"); return; }
      const score = d => { const et = docEtapas(d); return et.includes(etapa) ? 0 : !et.length ? 1 : Math.min(...et) < etapa ? 2 : 3; };
      const rows = state.docs.filter(d => ["ficha", "recurso"].includes(d.categoria) &&
        [d.titulo, (d.temas || []).join(" ")].join(" ").toLowerCase().includes(q)).sort((a, b) => score(a) - score(b)).slice(0, 8);
      res.innerHTML = rows.length ? rows.map(d => { const et = docEtapas(d); const adv = etapa && et.length && Math.min(...et) > etapa;
        return `<button class="sr-item" data-add="${esc(d.id)}">${icon("note")}<span>${esc(d.titulo)}<small>${etapasTxt(et)}${et.includes(etapa) ? " · tu etapa" : adv ? " · más avanzada" : ""}</small></span></button>`; }).join("")
        : `<div class="sr-empty">No encontré fichas con “${esc(inp.value)}”.</div>`;
      res.classList.remove("hidden");
      $$("[data-add]", res).forEach(b => b.addEventListener("mousedown", e => {
        e.preventDefault(); const d = state.docs.find(x => x.id === b.dataset.add);
        if (!prep.selected.includes(d.id)) toggleFicha(d.id, { doc_id: d.id, titulo: d.titulo, etapas: docEtapas(d) });
        inp.value = ""; res.classList.add("hidden");
      }));
    }, 150);
    inp.addEventListener("input", run);
    inp.addEventListener("blur", () => setTimeout(() => res.classList.add("hidden"), 150));
  }

  async function renderHistorial(t) {
    const box = $("#prep-hist"); if (!box) return;
    await loadEncuentros();
    const prev = encDeEquipo(t.id).slice(0, 4);
    box.innerHTML = prev.length ? `<div class="sub-label">Lo que ya trabajó este grupo</div><div class="hist">${prev.map(e => `
      <button class="hist-item" data-enc="${esc(e.id)}"><span class="hist-date">${esc(fmtDay(e.fecha))}</span><span class="hist-t">${esc(e.titulo || e.tema || "Encuentro")}</span>
      <span class="badge ${e.estado === "realizado" ? "red" : ""}">${esc(ESTADOS[e.estado] || e.estado)}</span></button>`).join("")}</div>`
      : `<p class="muted small-note" style="margin-top:12px">Este grupo todavía no tiene encuentros guardados.</p>`;
    $$("[data-enc]", box).forEach(b => b.addEventListener("click", () => openEncuentro(b.dataset.enc)));
  }

  async function generarEncuentro() {
    if (prep.controller) return;
    const tema = $("#prep-tema").value.trim();
    if (!tema && !prep.selected.length) { toast("Elegí una ficha del programa o escribí un tema."); $("#prep-tema").focus(); return; }
    const delPrograma = prep.selected.find(id => prep.prog?.fichas?.some(f => f.doc_id === id) || prep.prog?.liturgico?.fichas?.some(f => f.doc_id === id) || prep.prog?.proximo?.fichas?.some(f => f.doc_id === id));
    const body = {
      team_id: prep.teamId, tema, fichas: prep.selected, origen_tema: delPrograma ? "programa" : "otro",
      periodo: delPrograma ? (fichaData(delPrograma).periodo || "") : "",
      fecha: $("#prep-fecha").value || null, cantidad: parseInt($("#prep-cantidad").value) || null,
      composicion: $("#prep-comp").value, duracion: $("#prep-duracion").value.trim(), notas: $("#prep-notas").value.trim(),
      edades: state.teams.find(t => t.id === prep.teamId)?.perfil?.edades || "",
    };
    await streamEncuentro(body, $("#prep-out"));
  }

  // genera (o regenera) una propuesta y la muestra en `out`
  async function streamEncuentro(body, out, onSaved) {
    out.innerHTML = `<div class="form-card enc-out"><div class="weak hidden"></div><div class="md"><div class="thinking"><span class="spinner"></span>Buscando en el programa y las fichas de la etapa…</div></div><div class="extras"></div></div>`;
    const card = $(".enc-out", out), md = $(".md", card);
    out.scrollIntoView({ behavior: "smooth", block: "start" });
    const btn = $("#prep-generar"); if (btn) { btn.disabled = true; btn.innerHTML = `<span class="spinner"></span>Generando…`; }
    const controller = prep.controller = new AbortController();
    let text = "", raf = 0, saved = null;
    const paint = () => { raf = 0; md.innerHTML = markdown(text); md.classList.add("cursor"); };
    try {
      const res = await fetch("/api/encuentros/generar", { method: "POST", credentials: "same-origin", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body), signal: controller.signal });
      if (res.status === 401) { showLogin(); throw new Error("La sesión venció"); }
      if (!res.ok) { let m = res.statusText; try { m = (await res.json()).detail; } catch {} throw new Error(m); }
      await readSSE(res, ev => {
        if (ev.type === "meta") {
          card._sources = ev.sources || [];
          const w = $(".weak", card);
          const avisos = [ev.aviso, ev.weak_evidence ? "Encontré poco material del ECyD directamente relacionado; revisá la propuesta con más cuidado." : ""].filter(Boolean);
          if (avisos.length) { w.innerHTML = avisos.map(esc).join("<br>"); w.classList.remove("hidden"); }
          md.innerHTML = `<div class="thinking"><span class="spinner"></span>Armando la propuesta…</div>`;
        } else if (ev.type === "delta") { text += ev.text; if (!raf) raf = requestAnimationFrame(paint); }
        else if (ev.type === "done") { saved = ev.encuentro; saved._sources = ev.sources; }
        else if (ev.type === "error") throw new Error(ev.message);
      });
    } catch (err) {
      if (raf) cancelAnimationFrame(raf);
      md.classList.remove("cursor");
      if (err.name === "AbortError") md.innerHTML = markdown(text + "\n\n_(Detenido.)_");
      else { card.classList.add("error-card"); md.innerHTML = (text ? markdown(text) : "") + `<p class="error-text">No pude generar la propuesta: ${esc(err.message)}</p>`; }
    } finally {
      prep.controller = null;
      if (btn) { btn.disabled = false; btn.innerHTML = `${icon("sparkle")}Generar otra propuesta`; }
    }
    if (raf) cancelAnimationFrame(raf);
    if (saved) {
      prep.done = true;
      await loadEncuentros();
      if (onSaved) onSaved(saved);
      else { renderEncuentroEditor(out, saved, { sources: saved._sources }); toast("Propuesta guardada como borrador en “Mis encuentros”"); }
      renderHistorial(state.teams.find(t => t.id === saved.team_id) || { id: saved.team_id });
    }
  }

  // ------------------------------------------------------------ ajustes con la IA
  const AJUSTES_RAPIDOS = ["Más corto", "Más dinámico, con juegos", "Más tiempo de oración", "Para hacer al aire libre",
    "Más simple de preparar", "Más profundo para conversar", "Menos materiales"];

  function setupAjuste(box, q, enc) {
    const instr = q("instr"), btn = q("ajustar");
    const grow = () => { instr.style.height = "auto"; instr.style.height = Math.min(instr.scrollHeight, 160) + "px"; };
    instr.addEventListener("input", grow);
    instr.addEventListener("keydown", e => { if (e.key === "Enter" && !e.shiftKey && !e.isComposing) { e.preventDefault(); run(); } });
    $$("[data-quick]", box).forEach(c => c.addEventListener("click", () => {
      const t = c.dataset.quick;
      instr.value = instr.value.trim() ? `${instr.value.trim().replace(/[.;,]$/, "")}; ${t.toLowerCase()}` : t;
      grow(); instr.focus();
    }));
    btn.addEventListener("click", () => box._ajusteCtl ? box._ajusteCtl.abort() : run());
    paintHist();

    function paintHist() {
      const aj = (enc.meta?.ajustes || []).slice(-5).reverse();
      q("hist").innerHTML = (aj.length ? `<div class="sub-label">Cambios pedidos</div>` + aj.map(a => `
        <div class="aj-item">${icon("edit")}<div><div>${esc(a.instruccion)}</div>${a.cambios ? `<div class="aj-cambios">${markdown(a.cambios)}</div>` : ""}</div></div>`).join("") : "")
        + (enc.meta?.version_anterior ? `<button type="button" class="link-btn aj-undo" data-e="undo">↺ Volver a la versión anterior</button>` : "");
      q("undo")?.addEventListener("click", undo);
    }

    function showText(text) {
      q("text").value = text;
      $$(".enc-tabs [data-mode]", box).forEach(x => x.classList.toggle("on", x.dataset.mode === "ver"));
      const md = $(".enc-md", box); md.classList.remove("hidden"); q("text").classList.add("hidden");
      md.innerHTML = markdown(text);
    }
    function applySaved(saved, sources) {
      Object.assign(enc, saved);
      showText(enc.propuesta || "");
      if (saved.titulo) q("titulo").value = saved.titulo;
      box._sources = sources || enc.meta?.sources || []; renderSourceBar(box);
      paintHist(); loadEncuentros();
    }

    async function undo() {
      const prev = enc.meta?.version_anterior; if (prev == null) return;
      const actual = q("text").value;
      const m = prev.match(/^#\s+(.+)$/m);
      try {
        const saved = await api(`/api/encuentros/${enc.id}`, { method: "PUT", body: {
          propuesta: prev, ...(m ? { titulo: m[1].trim().slice(0, 140) } : {}), meta: { ...(enc.meta || {}), version_anterior: actual } } });
        applySaved(saved); toast("Volviste a la versión anterior");
      } catch (err) { toast(err.message); }
    }

    async function run() {
      const pedido = instr.value.trim();
      if (pedido.length < 2) { toast("Escribí qué querés cambiar."); instr.focus(); return; }
      const actual = q("text").value, md = $(".enc-md", box);
      showText(actual);
      md.classList.add("regenerating");
      const status = document.createElement("div");
      status.className = "thinking aj-status"; status.innerHTML = `<span class="spinner"></span>Aplicando: “${esc(pedido)}”…`;
      q("ajuste").prepend(status);
      const ctl = box._ajusteCtl = new AbortController();
      btn.innerHTML = icon("stop"); btn.title = "Detener"; instr.disabled = true; box.classList.add("busy");
      let text = "", raf = 0, saved = null, sources = null, first = true;
      const paint = () => { raf = 0; if (first) { md.classList.remove("regenerating"); first = false; } md.innerHTML = markdown(text); md.classList.add("cursor"); };
      try {
        const res = await fetch(`/api/encuentros/${enc.id}/ajustar`, { method: "POST", credentials: "same-origin",
          headers: { "Content-Type": "application/json" }, body: JSON.stringify({ instruccion: pedido, propuesta: actual }), signal: ctl.signal });
        if (res.status === 401) { showLogin(); throw new Error("La sesión venció"); }
        if (!res.ok) { let m = res.statusText; try { m = (await res.json()).detail; } catch {} throw new Error(m); }
        await readSSE(res, ev => {
          if (ev.type === "delta") { text += ev.text; if (!raf) raf = requestAnimationFrame(paint); }
          else if (ev.type === "done") { saved = ev.encuentro; sources = ev.sources; }
          else if (ev.type === "error") throw new Error(ev.message);
        });
      } catch (err) {
        if (err.name !== "AbortError") toast("No se pudo aplicar el cambio: " + err.message, 6000);
        else toast("Cambio cancelado: se mantiene la versión anterior");
      } finally {
        if (raf) cancelAnimationFrame(raf);
        box._ajusteCtl = null; status.remove();
        md.classList.remove("cursor", "regenerating");
        btn.innerHTML = icon("send"); btn.title = "Aplicar cambios"; instr.disabled = false; box.classList.remove("busy");
      }
      if (saved) { instr.value = ""; grow(); applySaved(saved, sources); toast("Propuesta actualizada"); md.scrollIntoView({ behavior: "smooth", block: "start" }); }
      else showText(actual);
    }
  }

  // ------------------------------------------------------------ PDF
  async function descargarPDF(enc, propuesta, titulo) {
    toast("Preparando el PDF…", 8000);
    try {
      const res = await fetch(`/api/encuentros/${enc.id}/pdf`, { method: "POST", credentials: "same-origin",
        headers: { "Content-Type": "application/json" }, body: JSON.stringify({ propuesta, titulo: (titulo || "").trim() || null }) });
      if (res.status === 401) { showLogin(); throw new Error("La sesión venció"); }
      if (!res.ok) { let m = res.statusText; try { m = (await res.json()).detail; } catch {} throw new Error(m); }
      const blob = await res.blob();
      const name = (res.headers.get("Content-Disposition") || "").match(/filename="([^"]+)"/)?.[1] || "encuentro.pdf";
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url; a.download = name; document.body.appendChild(a); a.click(); a.remove();
      setTimeout(() => URL.revokeObjectURL(url), 30000);
      toast("PDF descargado");
    } catch (err) { toast("No se pudo crear el PDF: " + err.message, 6000); }
  }

  // ------------------------------------------------------------ feedback después del encuentro
  const PUNTOS = [[1, "Muy difícil"], [2, "Flojo"], [3, "Bien"], [4, "Muy bien"], [5, "Excelente"]];
  const FB_PREG = [
    ["funciono", "¿Qué funcionó bien?", "Ej.: el juego del inicio los enganchó, participaron todos en el diálogo…"],
    ["cambiaria", "¿Qué cambiarías o no funcionó?", "Ej.: la lectura fue larga, faltó tiempo para el cierre…"],
    ["oracion", "¿Cómo respondieron al momento de oración o reflexión?", "Ej.: estuvieron atentos, les costó el silencio…"],
    ["pendiente", "¿Quedó algo pendiente para el próximo encuentro?", "Ej.: retomar la pregunta sobre la amistad, hablar con un chico…"],
  ];
  const puntosTxt = n => (PUNTOS.find(p => p[0] === n) || [])[1] || "";

  function paintFeedback(el, enc, ro, open) {
    if (!el) return;
    const fb = enc.feedback;
    if (!fb) {
      el.innerHTML = enc.estado === "realizado" && !ro ? `<div class="fb-missing">${icon("info")}<span><strong>Falta el feedback de este encuentro.</strong>
        <small>Un minuto: la IA lo usa para preparar el próximo.</small></span><button class="btn small primary" data-fb-open>¿Cómo salió?</button></div>` : "";
    } else {
      el.innerHTML = `<div class="fb-card">
        <div class="fb-head"><h3>${icon("check")}Cómo salió</h3>${ro ? "" : `<button class="link-btn" data-fb-open>Editar</button>`}</div>
        <div class="fb-stats">${fb.puntuacion ? `<span class="fb-score s${fb.puntuacion}">${fb.puntuacion}/5 · ${esc(puntosTxt(fb.puntuacion))}</span>` : ""}
          ${fb.asistentes != null ? `<span class="pill">${icon("users")}Vinieron ${fb.asistentes}</span>` : ""}</div>
        ${FB_PREG.filter(([k]) => fb[k]).map(([k, label]) => `<div class="fb-item"><div class="k">${esc(label)}</div><div class="v">${esc(fb[k])}</div></div>`).join("")}
        ${ro ? `<p class="muted small-note">Las respuestas escritas las ven solo los responsables del equipo.</p>` : ""}
      </div>`;
    }
    hydrateIcons(el);
    el.querySelector("[data-fb-open]")?.addEventListener("click", open);
  }

  function feedbackForm(enc, onSaved, onCancel) {
    const fb = enc.feedback || {};
    let punt = fb.puntuacion || null, guardado = false;
    openPanel("¿Cómo salió el encuentro?", `
      <form id="fb-form" class="stack">
        <p class="help">${esc(enc.titulo || "Encuentro")}${enc.fecha ? " · " + esc(fmtDay(enc.fecha)) : ""}</p>
        <div class="field-wrap"><label>En general, ¿cómo salió?</label>
          <div class="fb-rate">${PUNTOS.map(([n, l]) => `<button type="button" data-p="${n}" class="${punt === n ? "on" : ""}"><strong>${n}</strong><small>${l}</small></button>`).join("")}</div></div>
        <div class="field-wrap"><label for="fb-asis">¿Cuántos chicos vinieron?</label>
          <input class="field" type="number" min="0" max="500" id="fb-asis" value="${esc(fb.asistentes ?? "")}" placeholder="${esc(enc.cantidad || "")}"></div>
        ${FB_PREG.map(([k, label, ph]) => `<div class="field-wrap"><label for="fb-${k}">${esc(label)}</label>
          <textarea class="field" id="fb-${k}" rows="2" maxlength="1500" placeholder="${esc(ph)}">${esc(fb[k] || "")}</textarea></div>`).join("")}
        <p class="help">${icon("info", "ri")}Lo ven solo los responsables del equipo; la coordinación ve la puntuación y cuántos vinieron. La IA lo tiene en cuenta para el próximo encuentro de este grupo.</p>
        <div class="actions"><button class="btn primary" type="submit">${icon("check")}Guardar</button>
          ${enc.feedback ? "" : `<button class="btn ghost" type="button" id="fb-later">Más tarde</button>`}</div>
      </form>`);
    hydrateIcons($("#panel-body"));
    $$(".fb-rate button").forEach(b => b.addEventListener("click", () => {
      punt = +b.dataset.p; $$(".fb-rate button").forEach(x => x.classList.toggle("on", x === b));
    }));
    const put = async body => {
      try { const upd = await api(`/api/encuentros/${enc.id}`, { method: "PUT", body }); guardado = true; closePanel(); onSaved(upd); return upd; }
      catch (err) { toast(err.message); }
    };
    $("#fb-form").addEventListener("submit", async e => {
      e.preventDefault();
      const feedback = { puntuacion: punt, asistentes: $("#fb-asis").value === "" ? null : +$("#fb-asis").value };
      FB_PREG.forEach(([k]) => { feedback[k] = $(`#fb-${k}`).value.trim(); });
      if (await put({ estado: "realizado", feedback })) toast("¡Gracias! Feedback guardado");
    });
    $("#fb-later")?.addEventListener("click", async () => {
      if (await put({ estado: "realizado" })) toast("Quedó como realizado. Podés completar el feedback cuando quieras.");
    });
    // si cierra el panel sin elegir, el estado vuelve a como estaba
    const closeBtn = $("#panel-close");
    const onClose = () => { closeBtn.removeEventListener("click", onClose); if (!guardado && onCancel) onCancel(); };
    closeBtn.addEventListener("click", onClose);
  }

  // ------------------------------------------------------------ editor de un encuentro
  function renderEncuentroEditor(container, enc, opts = {}) {
    const sources = opts.sources || enc.meta?.sources || [];
    const fichas = enc.fichas || [];
    const ro = !!enc.solo_lectura;
    const backTxt = opts.back === "comunidad" ? "← Volver a la comunidad" : "← Volver a Mis encuentros";
    container.innerHTML = `
      <div class="form-card enc-editor ${ro ? "read-only" : ""}">
        ${opts.back ? `<button class="link-btn back" data-e="back">${backTxt}</button>` : ""}
        ${ro ? `<div class="ro-note">${icon("info")}Lo ves en modo lectura como coordinación de la comunidad. Solo los responsables del equipo pueden editarlo.</div>` : ""}
        <div class="enc-top">
          ${ro ? `<h2 class="enc-title-ro">${esc(enc.titulo || "Encuentro")}</h2><span class="badge ${enc.estado === "realizado" ? "red" : ""}">${esc(ESTADOS[enc.estado] || "")}</span>`
            : `<input class="field enc-title" data-e="titulo" value="${esc(enc.titulo || "")}" maxlength="140" aria-label="Título">
          <select class="field enc-estado" data-e="estado">${Object.entries(ESTADOS).map(([k, l]) => `<option value="${k}" ${enc.estado === k ? "selected" : ""}>${l}</option>`).join("")}</select>`}
        </div>
        <div class="row-sub enc-meta">${encMeta(enc).map(x => `<span>${esc(x)}</span>`).join("<span>·</span>")}</div>
        <div class="pill-row">
          ${enc.tema ? `<span class="pill on">${icon("target")}${esc(enc.tema)}</span>` : ""}
          ${enc.origen_tema === "programa" ? `<span class="pill">${icon("compass")}Sugerido por el programa</span>` : `<span class="pill">${icon("edit")}Tema elegido por el responsable</span>`}
          ${fichas.map(f => `<button class="pill clickable" data-doc="${esc(f.doc_id)}">${icon("note")}${esc(f.titulo)}</button>`).join("")}
        </div>
        ${enc.meta?.aviso ? `<div class="weak">${esc(enc.meta.aviso)}</div>` : ""}
        <div class="enc-tabs">${ro ? "" : `<div class="seg"><button class="on" data-mode="ver">Ver</button><button data-mode="editar">${icon("edit")}Editar</button></div>`}
          <span class="muted small-note">Es una propuesta: adaptala a tu grupo antes de usarla.</span>
          <span style="flex:1"></span><button class="btn small" data-e="pdf">${icon("pdf")}Descargar PDF</button></div>
        <div class="md enc-md">${markdown(enc.propuesta || "_Todavía no hay propuesta._")}</div>
        <textarea class="field enc-text hidden" data-e="text" rows="22">${esc(enc.propuesta || "")}</textarea>
        <div class="extras"></div>
        <div class="fb-block" data-e="fb"></div>
        ${ro ? `<div class="actions" style="margin-top:16px"><button class="btn small" data-e="copy">${icon("copy")}Copiar texto</button></div></div>` : `
        <div class="ajuste" data-e="ajuste">
          <div class="ajuste-head">${icon("sparkle")}<div><strong>Pedile cambios a la IA</strong>
            <small>Aclarale lo que necesites y reescribe la propuesta. Siempre podés volver a la versión anterior.</small></div></div>
          <div class="ajuste-chips">${AJUSTES_RAPIDOS.map(t => `<button type="button" class="chip" data-quick="${esc(t)}">${esc(t)}</button>`).join("")}</div>
          <div class="ajuste-box">
            <textarea data-e="instr" rows="1" maxlength="2000" placeholder="Ej.: son 45 minutos y vienen 3 chicos nuevos…"></textarea>
            <button type="button" class="send-btn" data-e="ajustar" aria-label="Aplicar cambios" title="Aplicar cambios">${icon("send")}</button>
          </div>
          <div class="ajuste-hist" data-e="hist"></div>
        </div>
        <div class="form-grid" style="margin-top:16px">
          <div class="field-wrap"><label >${icon("calendar")}Fecha</label><input class="field" type="date" data-e="fecha" value="${esc((enc.fecha || "").slice(0, 10))}"></div>
          <div class="field-wrap"><label >${icon("users")}Cantidad de chicos</label><input class="field" type="number" min="1" data-e="cant" value="${esc(enc.cantidad || "")}"></div>
          <div class="field-wrap wide"><label >${icon("note")}Observaciones</label>
            <textarea class="field" data-e="obs" rows="3" placeholder="¿Cómo salió? Qué funcionó, qué cambiarías, qué quedó pendiente…">${esc(enc.observaciones || "")}</textarea></div>
        </div>
        <div class="actions" style="margin-top:16px">
          <button class="btn primary" data-e="save">${icon("check")}Guardar</button>
          <button class="btn small" data-e="copy">${icon("note")}Copiar texto</button>
          <button class="btn small" data-e="dup">${icon("plus")}Duplicar</button>
          <span style="flex:1"></span>
          <button class="btn danger small" data-e="del">${icon("trash")}Eliminar</button>
        </div>
      </div>`}`;
    const box = $(".enc-editor", container);
    const q = k => box.querySelector(`[data-e="${k}"]`);
    box._sources = sources;
    renderSourceBar(box);
    hydrateIcons(box);
    if (!ro) setupAjuste(box, q, enc);
    const paintFb = () => paintFeedback(q("fb"), enc, ro, () => feedbackForm(enc, upd => {
      Object.assign(enc, upd); if (q("estado")) q("estado").value = enc.estado; paintFb(); loadEncuentros();
    }));
    paintFb();
    q("estado")?.addEventListener("change", e => {
      if (e.target.value === "realizado" && !enc.feedback) feedbackForm(enc, upd => {
        Object.assign(enc, upd); paintFb(); loadEncuentros();
      }, () => { e.target.value = enc.estado; });
    });
    $$("[data-doc]", box).forEach(b => b.addEventListener("click", () => openDoc(b.dataset.doc)));
    q("back")?.addEventListener("click", () => {
      encOpen = null;
      if (opts.back === "comunidad") showView("comunidad"); else renderEncuentros();
    });
    q("pdf")?.addEventListener("click", () => descargarPDF(enc, ro ? enc.propuesta : q("text")?.value ?? enc.propuesta, ro ? enc.titulo : q("titulo")?.value));
    $$(".enc-tabs [data-mode]", box).forEach(b => b.addEventListener("click", () => {
      const edit = b.dataset.mode === "editar";
      $$(".enc-tabs [data-mode]", box).forEach(x => x.classList.toggle("on", x === b));
      if (!edit) $(".enc-md", box).innerHTML = markdown(q("text").value);
      $(".enc-md", box).classList.toggle("hidden", edit); q("text").classList.toggle("hidden", !edit);
      if (edit) q("text").focus();
    }));
    q("save")?.addEventListener("click", async () => {
      try {
        const upd = await api(`/api/encuentros/${enc.id}`, { method: "PUT", body: {
          titulo: q("titulo").value.trim() || enc.titulo, estado: q("estado").value, fecha: q("fecha").value || null,
          cantidad: parseInt(q("cant").value) || null, propuesta: q("text").value, observaciones: q("obs").value } });
        Object.assign(enc, upd); await loadEncuentros(); toast("Encuentro guardado");
      } catch (err) { toast(err.message); }
    });
    q("copy")?.addEventListener("click", async () => {
      try { await navigator.clipboard.writeText(q("text").value); toast("Texto copiado"); } catch { toast("No se pudo copiar"); }
    });
    q("dup")?.addEventListener("click", async () => {
      const keys = ["team_id", "etapa", "tema", "origen_tema", "periodo", "fichas", "cantidad", "composicion", "edades", "duracion"];
      const body = Object.fromEntries(keys.filter(k => enc[k] != null && enc[k] !== "").map(k => [k, enc[k]]));
      Object.assign(body, { titulo: (enc.titulo || "Encuentro") + " (copia)", propuesta: q("text").value, estado: "borrador" });
      try { const c = await api("/api/encuentros", { method: "POST", body }); await loadEncuentros(); toast("Copia creada"); openEncuentro(c.id); }
      catch (err) { toast(err.message); }
    });
    q("del")?.addEventListener("click", async () => {
      if (!confirm(`¿Eliminar “${enc.titulo || "este encuentro"}”? No se puede deshacer.`)) return;
      await api(`/api/encuentros/${enc.id}`, { method: "DELETE" });
      await loadEncuentros(); toast("Encuentro eliminado");
      encOpen = null; showView("encuentros");
    });
  }

  // ------------------------------------------------------------ mis encuentros
  let encOpen = null;
  const encFilter = { team: "", etapa: "", estado: "", q: "" };
  let encFrom = "encuentros";
  async function openEncuentro(id, from = "encuentros") { encOpen = id; encFrom = from; showView("encuentros"); }

  async function renderEncuentros() {
    const v = $("#view-encuentros");
    if (encOpen) {
      v.innerHTML = `<div class="thinking"><span class="spinner"></span>Cargando…</div>`;
      try { const e = await api(`/api/encuentros/${encOpen}`); renderEncuentroEditor(v, e, { back: encFrom }); }
      catch (err) { encOpen = null; v.innerHTML = `<p class="error-text">${esc(err.message)}</p>`; }
      return;
    }
    v.innerHTML = `
      <div class="page-head"><div><h1>Mis encuentros</h1><p>Todo lo que preparaste, por grupo. Sirve para no repetir temas y para ver cómo fue avanzando cada equipo.</p></div>
        <span class="spacer"></span><button class="btn primary" data-view="preparar">${icon("sparkle")}Preparar encuentro</button></div>
      <div class="filters">
        <select class="field" id="ef-team" style="max-width:220px"><option value="">Todos los grupos</option>${state.teams.map(t => `<option value="${esc(t.id)}">${esc(t.nombre)}</option>`).join("")}</select>
        <span class="chip-group">${[1, 2, 3, 4].map(n => `<button class="chip" data-ef-etapa="${n}">Etapa ${n}</button>`).join("")}</span>
        <span class="chip-group">${Object.entries(ESTADOS).map(([k, l]) => `<button class="chip" data-ef-estado="${k}">${l}</button>`).join("")}<button class="chip" data-ef-estado="sinfb">Falta feedback</button></span>
        <input class="field" type="search" id="ef-q" placeholder="Buscar por título o tema…" style="max-width:240px">
      </div>
      <div class="list" id="enc-list"><div class="thinking"><span class="spinner"></span>Cargando…</div></div>`;
    hydrateIcons(v);
    $("#ef-team").value = encFilter.team; $("#ef-q").value = encFilter.q;
    const paint = () => {
      $$("[data-ef-etapa]", v).forEach(b => b.classList.toggle("on", b.dataset.efEtapa === encFilter.etapa));
      $$("[data-ef-estado]", v).forEach(b => b.classList.toggle("on", b.dataset.efEstado === encFilter.estado));
      const q = encFilter.q.toLowerCase();
      const rows = state.encuentros.filter(e => (!encFilter.team || e.team_id === encFilter.team) && (!encFilter.etapa || String(e.etapa) === encFilter.etapa)
        && (!encFilter.estado || (encFilter.estado === "sinfb" ? e.estado === "realizado" && !e.feedback : e.estado === encFilter.estado)) && (!q || [e.titulo, e.tema, ...(e.fichas || []).map(f => f.titulo)].join(" ").toLowerCase().includes(q)));
      $("#enc-list").innerHTML = rows.length ? rows.map(e => `
        <div class="row-item clickable" data-open-enc="${esc(e.id)}">
          <div class="enc-date"><span>${e.fecha ? new Date(e.fecha.slice(0, 10) + "T12:00").getDate() : "—"}</span><small>${e.fecha ? new Date(e.fecha.slice(0, 10) + "T12:00").toLocaleDateString("es-AR", { month: "short" }) : ""}</small></div>
          <div class="row-main"><div class="row-title">${esc(e.titulo || e.tema || "Encuentro")}</div>
            <div class="row-sub">${encMeta(e).filter((x, i) => i !== 2).map(x => `<span>${esc(x)}</span>`).join("<span>·</span>")}
              ${(e.fichas || []).slice(0, 2).map(f => `<span class="badge">${esc(f.titulo)}</span>`).join("")}</div></div>
          ${e.estado === "realizado" && !e.feedback ? `<span class="badge warn">Falta feedback</span>` : e.feedback?.puntuacion ? `<span class="badge">${e.feedback.puntuacion}/5</span>` : ""}
          <span class="badge ${e.estado === "realizado" ? "red" : ""}">${esc(ESTADOS[e.estado] || e.estado)}</span>
        </div>`).join("")
        : `<div class="empty-state"><img src="/static/img/cruz-ecyd.svg" alt=""><p>${state.encuentros.length ? "No hay encuentros con esos filtros." : "Todavía no preparaste ningún encuentro."}</p>
           <button class="btn primary" data-view="preparar">${icon("sparkle")}Preparar el primero</button></div>`;
      $$("[data-open-enc]", v).forEach(r => r.addEventListener("click", () => openEncuentro(r.dataset.openEnc)));
    };
    $("#ef-team").addEventListener("change", e => { encFilter.team = e.target.value; paint(); });
    $("#ef-q").addEventListener("input", e => { encFilter.q = e.target.value; paint(); });
    $$("[data-ef-etapa]", v).forEach(b => b.addEventListener("click", () => { encFilter.etapa = encFilter.etapa === b.dataset.efEtapa ? "" : b.dataset.efEtapa; paint(); }));
    $$("[data-ef-estado]", v).forEach(b => b.addEventListener("click", () => { encFilter.estado = encFilter.estado === b.dataset.efEstado ? "" : b.dataset.efEstado; paint(); }));
    await loadEncuentros(); paint();
  }

  // ------------------------------------------------------------ comunidades
  const com = { list: [], id: load("comunidadId") || "", data: null, mes: null };
  const ROL_TXT = { coordinador: "Coordinación", responsable: "Responsable" };
  const MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"];
  const mesActual = () => todayISO().slice(0, 7);
  const mesTxt = m => { const [y, mm] = m.split("-").map(Number); return `${cap(MESES[mm - 1])} ${y}`; };
  const mesMover = (m, d) => { let [y, mm] = m.split("-").map(Number); mm += d; if (mm < 1) { mm = 12; y--; } if (mm > 12) { mm = 1; y++; } return `${y}-${String(mm).padStart(2, "0")}`; };

  async function loadComunidades() {
    com.list = await api("/api/comunidades").catch(() => []);
    if (!com.list.some(c => c.id === com.id)) { com.id = com.list[0]?.id || ""; save("comunidadId", com.id); }
    return com.list;
  }

  async function renderComunidad() {
    const v = $("#view-comunidad");
    v.innerHTML = `<div class="thinking"><span class="spinner"></span>Cargando…</div>`;
    await loadComunidades();
    if (!com.list.length) return renderSinComunidad(v);
    com.mes ||= mesActual();
    try { com.data = await api(`/api/comunidades/${com.id}?mes=${com.mes}`); }
    catch (err) { v.innerHTML = `<p class="error-text">${esc(err.message)}</p>`; return; }
    const d = com.data, coord = d.rol === "coordinador", r = d.resumen;
    const porEtapa = [1, 2, 3, 4, null].map(n => ({ n, equipos: d.equipos.filter(e => (e.etapa || null) === n) })).filter(g => g.n || g.equipos.length);
    v.innerHTML = `
      <div class="page-head com-head"><div>
        ${com.list.length > 1 ? `<select class="field com-switch" id="com-switch">${com.list.map(c => `<option value="${esc(c.id)}" ${c.id === d.id ? "selected" : ""}>${esc(c.nombre)}</option>`).join("")}</select>` : ""}
        <h1>${esc(d.nombre)}</h1>
        <p>${d.lugar ? esc(d.lugar) + " · " : ""}<span class="badge red">${ROL_TXT[d.rol]}</span> · ${r.miembros} ${r.miembros === 1 ? "miembro" : "miembros"} · ${r.equipos} ${r.equipos === 1 ? "equipo" : "equipos"}</p></div>
        <span class="spacer"></span>
        <button class="btn primary" id="com-new-team">${icon("plus")}Nuevo equipo</button>
      </div>

      ${coord ? `<div class="invite-card">
        <div class="invite-txt">${icon("share")}<div><strong>Invitá a los responsables</strong>
          <small>Mandales el enlace: se crean la cuenta y quedan adentro. También pueden poner el código al registrarse o en <em>Comunidad → Unirme</em>.</small></div></div>
        <div class="invite-code"><code id="com-code">${esc(d.codigo)}</code>
          <button class="btn small" id="com-copy" title="Copiar el enlace de invitación">${icon("copy")}Copiar enlace</button>
          <a class="btn small" id="com-wa" target="_blank" rel="noopener" href="https://wa.me/?text=${encodeURIComponent(`Sumate a ${d.nombre} en el Asistente ECyD. Entrá a este enlace, creá tu cuenta y quedás adentro: ${location.origin}/?comunidad=${d.codigo}`)}">${icon("share")}WhatsApp</a>
          <button class="icon-btn" id="com-regen" title="Generar un código nuevo (el anterior deja de funcionar)">${icon("refresh")}</button></div>
      </div>` : ""}

      <div class="month-bar">
        <button class="icon-btn" id="mes-prev" aria-label="Mes anterior">${icon("chevron-left")}</button>
        <strong>${mesTxt(d.mes)}</strong>
        <button class="icon-btn" id="mes-next" aria-label="Mes siguiente">${icon("chevron-right")}</button>
        ${d.mes !== mesActual() ? `<button class="link-btn" id="mes-hoy">Volver a este mes</button>` : ""}
      </div>
      <div class="stats">
        <div class="stat"><span>${r.con_plan}/${r.equipos}</span><small>equipos con encuentro este mes</small></div>
        <div class="stat"><span>${r.encuentros_mes}</span><small>encuentros preparados</small></div>
        <div class="stat"><span>${r.realizados_mes}</span><small>ya realizados${r.promedio ? ` · cómo salieron: ${r.promedio}/5` : ""}${r.falta_feedback ? ` · ${r.falta_feedback} sin feedback` : ""}</small></div>
        <div class="stat ${r.sin_responsable ? "warn" : ""}"><span>${r.sin_responsable}</span><small>equipos sin responsable</small></div>
      </div>

      ${d.equipos.length ? porEtapa.map(g => `
        <div class="etapa-block">
          <div class="etapa-title"><span class="etapa-n">${g.n || "?"}</span><h2>${g.n ? `Etapa ${g.n}` : "Sin etapa"}</h2>
            <span class="muted small-note">${g.n ? esc((ETAPAS.find(e => e.n === g.n) || {}).edades || "") : ""}</span></div>
          ${g.equipos.length ? `<div class="com-grid">${g.equipos.map(e => teamCardCom(e, coord)).join("")}</div>`
            : `<p class="muted small-note etapa-empty">Todavía no hay equipos de esta etapa.</p>`}
        </div>`).join("")
      : `<div class="empty-state"><img src="/static/img/cruz-ecyd.svg" alt=""><p>La comunidad todavía no tiene equipos.${coord ? " Creá los equipos de cada etapa y asigná sus responsables." : ""}</p></div>`}

      <div class="section-title">Miembros</div>
      <div class="list">${d.miembros.map(m => `
        <div class="row-item member-row">
          <span class="avatar sm">${esc(initials(m.nombre || "?"))}</span>
          <div class="row-main"><div class="row-title">${esc(m.nombre)}${m.user_id === state.user?.id ? ` <span class="muted">(vos)</span>` : ""}</div>
            <div class="row-sub"><span>${ROL_TXT[m.rol]}</span>${m.email ? `<span>·</span><span>${esc(m.email)}</span>` : ""}
              <span>·</span><span>${d.equipos.filter(e => e.responsables.some(x => x.user_id === m.user_id)).map(e => esc(e.nombre)).join(", ") || "sin equipo asignado"}</span></div></div>
          ${coord && m.user_id !== state.user?.id ? `<div class="row-actions">
            <button class="btn small ghost" data-rol="${esc(m.user_id)}" data-to="${m.rol === "coordinador" ? "responsable" : "coordinador"}">${m.rol === "coordinador" ? "Quitar coordinación" : "Hacer coordinador"}</button>
            <button class="icon-btn" data-quitar="${esc(m.user_id)}" title="Quitar de la comunidad" aria-label="Quitar">${icon("trash")}</button></div>` : ""}
        </div>`).join("")}</div>

      <div class="actions com-foot">
        <button class="btn small" id="com-otra">${icon("plus")}Crear o unirme a otra comunidad</button>
        ${coord ? `<button class="btn small" id="com-edit">${icon("edit")}Editar comunidad</button>` : ""}
        <span style="flex:1"></span>
        <button class="btn small ghost" id="com-salir">${icon("logout")}Salir de la comunidad</button>
        ${coord ? `<button class="btn danger small" id="com-del">${icon("trash")}Eliminar comunidad</button>` : ""}
      </div>`;
    hydrateIcons(v);
    bindComunidad(v, d, coord);
  }

  function teamCardCom(e, coord) {
    const soy = e.acceso === "responsable";
    return `<div class="com-team ${e.encuentros_mes.length ? "" : "pending"}">
      <div class="com-team-head"><h3>${esc(e.nombre)}</h3>
        ${coord ? `<button class="icon-btn" data-edit-team="${esc(e.id)}" title="Editar equipo" aria-label="Editar equipo">${icon("edit")}</button>` : ""}</div>
      <div class="row-sub">${[e.edades, e.cantidad ? `${esc(e.cantidad)} chicos` : ""].filter(Boolean).map(esc).join(" · ") || "&nbsp;"}</div>
      <div class="resp-row">${e.responsables.length ? e.responsables.map(r => `<span class="resp-chip" title="${esc(r.nombre)}"><span class="avatar xs">${esc(initials(r.nombre))}</span>${esc(r.nombre.split(" ")[0])}</span>`).join("")
        : `<span class="pill warn">${icon("info")}Sin responsable</span>`}</div>
      <div class="com-encs">${e.encuentros_mes.length ? e.encuentros_mes.map(x => `
        <button class="com-enc" data-enc="${esc(x.id)}"><span>${esc(fmtDay(x.fecha))}</span><strong>${esc(x.titulo || x.tema || "Encuentro")}</strong>
          <span class="badge ${x.falta_feedback ? "warn" : x.estado === "realizado" ? "red" : ""}">${x.puntuacion ? `${x.puntuacion}/5` : x.falta_feedback ? "Falta feedback" : esc(ESTADOS[x.estado] || x.estado)}</span></button>`).join("")
        : `<div class="com-empty">${icon("calendar")}<span>Sin encuentro este mes${e.programa_mes.length ? `<small>El programa sugiere: ${e.programa_mes.slice(0, 2).map(esc).join(" · ")}</small>` : ""}</span></div>`}</div>
      <div class="com-team-foot"><span class="muted small-note">${e.ultimo ? `Último: ${esc(fmtDay(e.ultimo))}` : "Sin encuentros todavía"}</span>
        ${soy ? `<button class="btn small primary" data-prep-team="${esc(e.id)}">${icon("sparkle")}Preparar</button>` : ""}</div>
    </div>`;
  }

  function bindComunidad(v, d, coord) {
    $("#com-switch")?.addEventListener("change", e => { com.id = e.target.value; save("comunidadId", com.id); com.mes = null; renderComunidad(); });
    $("#mes-prev").addEventListener("click", () => { com.mes = mesMover(d.mes, -1); renderComunidad(); });
    $("#mes-next").addEventListener("click", () => { com.mes = mesMover(d.mes, 1); renderComunidad(); });
    $("#mes-hoy")?.addEventListener("click", () => { com.mes = mesActual(); renderComunidad(); });
    $("#com-new-team").addEventListener("click", () => teamFormCom(d, null));
    $$("[data-edit-team]", v).forEach(b => b.addEventListener("click", () => teamFormCom(d, d.equipos.find(e => e.id === b.dataset.editTeam))));
    $$("[data-enc]", v).forEach(b => b.addEventListener("click", () => openEncuentro(b.dataset.enc, "comunidad")));
    $$("[data-prep-team]", v).forEach(b => b.addEventListener("click", async () => {
      await loadTeams(); setTeam(b.dataset.prepTeam); prep.teamId = b.dataset.prepTeam; showView("preparar");
    }));
    $("#com-copy")?.addEventListener("click", async () => {
      const link = `${location.origin}/?comunidad=${d.codigo}`;
      try { await navigator.clipboard.writeText(link); toast("Enlace de invitación copiado"); } catch { toast(link, 9000); }
    });
    $("#com-regen")?.addEventListener("click", async () => {
      if (!confirm("¿Generar un código nuevo? El código actual deja de funcionar (quienes ya entraron siguen en la comunidad).")) return;
      await api(`/api/comunidades/${d.id}/codigo`, { method: "POST" }); renderComunidad(); toast("Código nuevo generado");
    });
    $$("[data-rol]", v).forEach(b => b.addEventListener("click", async () => {
      try { await api(`/api/comunidades/${d.id}/miembros/${b.dataset.rol}`, { method: "PUT", body: { rol: b.dataset.to } }); renderComunidad(); }
      catch (err) { toast(err.message); }
    }));
    $$("[data-quitar]", v).forEach(b => b.addEventListener("click", async () => {
      const m = d.miembros.find(x => x.user_id === b.dataset.quitar);
      if (!confirm(`¿Quitar a ${m?.nombre || "esta persona"} de la comunidad? También deja de ser responsable de sus equipos.`)) return;
      try { await api(`/api/comunidades/${d.id}/miembros/${b.dataset.quitar}`, { method: "DELETE" }); renderComunidad(); toast("Miembro quitado"); }
      catch (err) { toast(err.message); }
    }));
    $("#com-otra").addEventListener("click", () => openPanel("Otra comunidad", comunidadForms(true)) || bindComunidadForms($("#panel-body")));
    $("#com-edit")?.addEventListener("click", () => {
      openPanel("Editar comunidad", `<form id="com-edit-form" class="stack">
        <div class="field-wrap"><label>Nombre</label><input class="field" id="ce-nombre" value="${esc(d.nombre)}" required minlength="2" maxlength="100"></div>
        <div class="field-wrap"><label>Lugar</label><input class="field" id="ce-lugar" value="${esc(d.lugar || "")}" maxlength="120"></div>
        <div class="actions"><button class="btn primary" type="submit">${icon("check")}Guardar</button></div></form>`);
      $("#com-edit-form").addEventListener("submit", async e => {
        e.preventDefault();
        try { await api(`/api/comunidades/${d.id}`, { method: "PUT", body: { nombre: $("#ce-nombre").value.trim(), lugar: $("#ce-lugar").value.trim() } }); closePanel(); renderComunidad(); }
        catch (err) { toast(err.message); }
      });
    });
    $("#com-salir").addEventListener("click", async () => {
      if (!confirm(`¿Salir de ${d.nombre}? Dejás de ver la comunidad y sus equipos.`)) return;
      try { await api(`/api/comunidades/${d.id}/miembros/${state.user.id}`, { method: "DELETE" }); com.id = ""; await loadTeams(); renderComunidad(); toast("Saliste de la comunidad"); }
      catch (err) { toast(err.message); }
    });
    $("#com-del")?.addEventListener("click", async () => {
      if (!confirm(`¿Eliminar ${d.nombre}? Los equipos NO se borran: quedan como equipos de sus responsables.`)) return;
      await api(`/api/comunidades/${d.id}`, { method: "DELETE" }); com.id = ""; await loadTeams(); renderComunidad(); toast("Comunidad eliminada");
    });
  }

  function teamFormCom(d, team) {
    const coord = d.rol === "coordinador";
    const sel = new Set((team?.responsables || []).map(r => r.user_id));
    openPanel(team ? "Editar equipo" : "Nuevo equipo de la comunidad", `
      <form id="tc-form" class="stack">
        <div class="field-wrap"><label for="tc-nombre">Nombre del equipo</label>
          <input class="field" id="tc-nombre" required maxlength="80" value="${esc(team?.nombre || "")}" placeholder="Ej.: Etapa 2 · chicas"></div>
        <div class="field-wrap"><label for="tc-etapa">Etapa</label><select class="field" id="tc-etapa">
          <option value="">Elegí la etapa…</option>${ETAPAS.map(e => `<option value="${e.n}" ${team?.etapa === e.n ? "selected" : ""}>Etapa ${e.n} · ${e.nombre} (${e.edades})</option>`).join("")}</select></div>
        ${coord ? `<div class="field-wrap"><label>Responsables</label>
          <p class="help">Pueden ser varios. Ellos usan el equipo (memoria, encuentros, chat). La coordinación ve la planificación, no la memoria.</p>
          <div class="check-list">${d.miembros.map(m => `<label class="check-item"><input type="checkbox" value="${esc(m.user_id)}" ${sel.has(m.user_id) ? "checked" : ""}>
            <span class="avatar xs">${esc(initials(m.nombre))}</span><span>${esc(m.nombre)}${m.user_id === state.user?.id ? " (vos)" : ""}</span></label>`).join("")}</div></div>`
          : `<p class="help">Vas a quedar como responsable de este equipo. La coordinación puede sumar a otros responsables.</p>`}
        <div class="actions"><button class="btn primary" type="submit">${icon("check")}${team ? "Guardar" : "Crear equipo"}</button>
          ${team ? `<span style="flex:1"></span><button class="btn danger small" type="button" id="tc-del">${icon("trash")}Eliminar equipo</button>` : ""}</div>
      </form>`);
    $("#tc-nombre").focus();
    $("#tc-form").addEventListener("submit", async e => {
      e.preventDefault();
      const etapa = parseInt($("#tc-etapa").value) || null;
      const responsables = coord ? $$("#tc-form .check-item input:checked").map(x => x.value) : undefined;
      try {
        if (team) await api(`/api/comunidades/${d.id}/equipos/${team.id}`, { method: "PUT", body: { nombre: $("#tc-nombre").value.trim(), etapa, responsables } });
        else await api(`/api/comunidades/${d.id}/equipos`, { method: "POST", body: { nombre: $("#tc-nombre").value.trim(), etapa, responsables: responsables || [] } });
        closePanel(); await loadTeams(); renderComunidad(); toast(team ? "Equipo actualizado" : "Equipo creado");
      } catch (err) { toast(err.message); }
    });
    $("#tc-del")?.addEventListener("click", async () => {
      if (!confirm(`¿Eliminar “${team.nombre}”? Se borran también su memoria y sus conversaciones. No se puede deshacer.`)) return;
      try { await api(`/api/teams/${team.id}`, { method: "DELETE" }); closePanel(); await loadTeams(); renderComunidad(); toast("Equipo eliminado"); }
      catch (err) { toast(err.message); }
    });
  }

  function comunidadForms(compact) {
    return `<div class="${compact ? "stack" : "grid-2 com-start"}">
      <form class="form-card" id="cf-crear">
        <h3>${icon("community")}Crear una comunidad</h3>
        <p class="help">Para coordinadores: armás los equipos de cada etapa e invitás a los responsables con un código.</p>
        <input class="field" id="cf-nombre" required minlength="2" maxlength="100" placeholder="Ej.: ECyD Mano Amiga">
        <input class="field" id="cf-lugar" maxlength="120" placeholder="Colegio, parroquia o ciudad (opcional)">
        <button class="btn primary" type="submit">${icon("plus")}Crear comunidad</button>
      </form>
      <form class="form-card" id="cf-unirse">
        <h3>${icon("share")}Unirme con un código</h3>
        <p class="help">Si tu coordinador ya creó la comunidad, pedile el código de invitación.</p>
        <input class="field code-input" id="cf-codigo" required maxlength="12" placeholder="ABCD-2345" autocomplete="off" autocapitalize="characters">
        <button class="btn primary" type="submit">${icon("check")}Unirme</button>
      </form></div>`;
  }
  function bindComunidadForms(root) {
    hydrateIcons(root);
    $("#cf-crear", root).addEventListener("submit", async e => {
      e.preventDefault();
      try {
        const c = await api("/api/comunidades", { method: "POST", body: { nombre: $("#cf-nombre", root).value.trim(), lugar: $("#cf-lugar", root).value.trim() } });
        com.id = c.id; save("comunidadId", c.id); closePanel(); showView("comunidad"); toast("Comunidad creada. Ahora creá los equipos e invitá a los responsables.", 6000);
      } catch (err) { toast(err.message); }
    });
    $("#cf-unirse", root).addEventListener("submit", async e => {
      e.preventDefault();
      try {
        const c = await api("/api/comunidades/unirse", { method: "POST", body: { codigo: $("#cf-codigo", root).value.trim() } });
        com.id = c.id; save("comunidadId", c.id); closePanel(); showView("comunidad"); toast(`Te sumaste a ${c.nombre}. La coordinación te va a asignar tu equipo.`, 6000);
      } catch (err) { toast(err.message); }
    });
  }
  function renderSinComunidad(v) {
    v.innerHTML = `<div class="page-head"><div><h1>Comunidad</h1>
      <p>Una comunidad (por ejemplo, <em>ECyD Mano Amiga</em>) reúne los equipos de todas las etapas y a sus responsables. La coordinación ve cómo va la planificación de cada equipo; la memoria de cada equipo queda solo para sus responsables.</p></div></div>
      ${comunidadForms(false)}`;
    bindComunidadForms(v);
  }

  // ------------------------------------------------------------ chat entre responsables
  const chat = { canales: [], actual: null, mensajes: [], poll: null, unreadPoll: null, sending: false };
  const canalPath = c => `/api/chats/${c.tipo}/${encodeURIComponent(c.id)}/mensajes`;
  const visible = () => document.visibilityState === "visible";
  const esMovil = () => window.matchMedia("(max-width: 880px)").matches;

  function fmtHora(iso) { const d = new Date(iso); return isNaN(d) ? "" : d.toLocaleTimeString("es-AR", { hour: "2-digit", minute: "2-digit" }); }
  function fmtDiaChat(iso) {
    const d = new Date(iso), hoy = new Date(), ayer = new Date(Date.now() - 864e5);
    if (d.toDateString() === hoy.toDateString()) return "Hoy";
    if (d.toDateString() === ayer.toDateString()) return "Ayer";
    return d.toLocaleDateString("es-AR", { weekday: "long", day: "numeric", month: "long" });
  }
  function fmtCuando(iso) {
    if (!iso) return "";
    const d = new Date(iso);
    return d.toDateString() === new Date().toDateString() ? fmtHora(iso) : d.toLocaleDateString("es-AR", { day: "numeric", month: "short" });
  }

  async function loadUnread() {
    try {
      const r = await api("/api/chats");
      chat.canales = r.canales;
      const b = $("#chat-badge");
      b.textContent = r.no_leidos > 99 ? "99+" : r.no_leidos;
      b.classList.toggle("hidden", !r.no_leidos);
      $("#open-sidebar").classList.toggle("has-dot", !!r.no_leidos);
      if (state.view === "chat") paintCanales();
      return r;
    } catch { return null; }
  }
  function startUnreadPoll() {
    clearInterval(chat.unreadPoll);
    chat.unreadPoll = setInterval(() => { if (visible() && state.user) loadUnread(); }, 30000);
  }
  function stopChatPoll() { clearInterval(chat.poll); chat.poll = null; }

  async function renderChat() {
    const v = $("#view-chat");
    v.innerHTML = `<div class="chat-layout ${chat.actual ? "has-open" : ""}">
      <aside class="chat-list"><div class="chat-list-head"><h1>Chat</h1><p>Con los responsables de tu comunidad y de tu equipo.</p></div>
        <div id="chat-canales"><div class="thinking"><span class="spinner"></span>Cargando…</div></div></aside>
      <section class="chat-conv" id="chat-conv"></section></div>`;
    await loadUnread();
    paintCanales();
    if (chat.actual && chat.canales.some(c => c.canal === chat.actual.canal)) openCanal(chat.actual.canal);
    else if (!esMovil() && chat.canales.length) openCanal(chat.canales[0].canal);
    else paintConvVacia();
  }

  function paintCanales() {
    const box = $("#chat-canales"); if (!box) return;
    if (!chat.canales.length) {
      box.innerHTML = `<div class="chat-empty">${icon("community")}<p>Todavía no tenés chats. Se crean solos cuando te sumás a una comunidad o compartís un equipo con otros responsables.</p>
        <button class="btn primary small" data-view="comunidad">${icon("community")}Ir a Comunidad</button></div>`;
      hydrateIcons(box); return;
    }
    const grupo = (titulo, arr) => arr.length ? `<div class="side-label">${titulo}</div>` + arr.map(c => `
      <button class="canal-item ${chat.actual?.canal === c.canal ? "active" : ""}" data-canal="${esc(c.canal)}">
        <span class="canal-ico ${c.tipo}">${icon(c.tipo === "comunidad" ? "community" : "users")}</span>
        <span class="canal-txt"><span class="canal-top"><strong>${esc(c.nombre)}</strong><small>${esc(fmtCuando(c.ultimo?.created_at))}</small></span>
          <span class="canal-prev">${c.ultimo ? `${c.ultimo.mio ? "Vos" : esc((c.ultimo.nombre || "").split(" ")[0])}: ${esc(c.ultimo.texto.slice(0, 70))}` : `<em>${esc(c.subtitulo)}</em>`}</span></span>
        ${c.no_leidos ? `<span class="nav-badge">${c.no_leidos}</span>` : ""}
      </button>`).join("") : "";
    box.innerHTML = grupo("Comunidades", chat.canales.filter(c => c.tipo === "comunidad")) + grupo("Equipos", chat.canales.filter(c => c.tipo === "equipo"));
    $$("[data-canal]", box).forEach(b => b.addEventListener("click", () => openCanal(b.dataset.canal)));
  }

  function paintConvVacia() {
    const conv = $("#chat-conv"); if (!conv) return;
    conv.innerHTML = chat.canales.length ? `<div class="chat-empty">${icon("chat")}<p>Elegí un chat para empezar.</p></div>` : "";
    hydrateIcons(conv);
  }

  async function openCanal(canalId) {
    const c = chat.canales.find(x => x.canal === canalId); if (!c) return;
    stopChatPoll();
    chat.actual = c; chat.mensajes = [];
    $(".chat-layout")?.classList.add("has-open");
    paintCanales();
    const conv = $("#chat-conv");
    conv.innerHTML = `
      <header class="conv-head">
        <button class="icon-btn conv-back" id="conv-back" aria-label="Volver a los chats">${icon("chevron-left")}</button>
        <span class="canal-ico ${c.tipo}">${icon(c.tipo === "comunidad" ? "community" : "users")}</span>
        <div class="conv-title"><strong>${esc(c.nombre)}</strong><small>${c.tipo === "comunidad" ? "Todos los miembros de la comunidad" : esc((c.responsables || []).join(", ") || c.subtitulo)}</small></div>
      </header>
      ${c.tipo === "comunidad" ? `<div class="conv-note">${icon("info")}Este canal lo ven todos los miembros de la comunidad. No compartas datos personales de los chicos acá.</div>`
        : `<div class="conv-note">${icon("info")}Solo lo ven los responsables de este equipo.</div>`}
      <div class="conv-msgs" id="conv-msgs"><div class="thinking"><span class="spinner"></span>Cargando…</div></div>
      <form class="conv-compose" id="conv-compose">
        <textarea id="conv-input" rows="1" maxlength="2000" placeholder="Escribí un mensaje…" aria-label="Mensaje"></textarea>
        <button class="send-btn" type="submit" aria-label="Enviar">${icon("send")}</button>
      </form>`;
    hydrateIcons(conv);
    $("#conv-back").addEventListener("click", () => {
      stopChatPoll(); chat.actual = null; $(".chat-layout")?.classList.remove("has-open"); paintCanales(); paintConvVacia(); loadUnread();
    });
    const inp = $("#conv-input");
    const grow = () => { inp.style.height = "auto"; inp.style.height = Math.min(inp.scrollHeight, 140) + "px"; };
    inp.addEventListener("input", grow);
    inp.addEventListener("keydown", e => { if (e.key === "Enter" && !e.shiftKey && !e.isComposing && !esMovil()) { e.preventDefault(); $("#conv-compose").requestSubmit(); } });
    $("#conv-compose").addEventListener("submit", async e => {
      e.preventDefault();
      const texto = inp.value.trim();
      if (!texto || chat.sending) return;
      chat.sending = true;
      try {
        const m = await api(canalPath(c), { method: "POST", body: { texto } });
        inp.value = ""; grow(); addMensajes([m], true);
      } catch (err) { toast(err.message); }
      finally { chat.sending = false; inp.focus(); }
    });
    try {
      const r = await api(canalPath(c));
      if (chat.actual?.canal !== canalId) return;
      chat.mensajes = r.mensajes; c.rol = r.rol;
      paintMensajes(true, r.mensajes.length >= 60);
      c.no_leidos = 0; paintCanales(); loadUnread();
    } catch (err) { $("#conv-msgs").innerHTML = `<p class="error-text">${esc(err.message)}</p>`; return; }
    if (!esMovil()) inp.focus();
    chat.poll = setInterval(pollMensajes, 4000);
  }

  async function pollMensajes() {
    const c = chat.actual;
    if (!c || !visible() || state.view !== "chat") return;
    const last = chat.mensajes[chat.mensajes.length - 1];
    try {
      const r = await api(canalPath(c) + (last ? `?after=${encodeURIComponent(last.created_at)}` : ""));
      if (chat.actual?.canal === c.canal && r.mensajes.length) addMensajes(r.mensajes, false);
    } catch { /* se reintenta en el próximo ciclo */ }
  }

  function addMensajes(nuevos, forceScroll) {
    const ids = new Set(chat.mensajes.map(m => m.id));
    const add = nuevos.filter(m => !ids.has(m.id));
    if (!add.length) return;
    chat.mensajes.push(...add);
    chat.mensajes.sort((a, b) => new Date(a.created_at) - new Date(b.created_at));
    const box = $("#conv-msgs");
    const cerca = box && box.scrollHeight - box.scrollTop - box.clientHeight < 120;
    paintMensajes(forceScroll || cerca);
  }

  function paintMensajes(scroll, hayMas) {
    const box = $("#conv-msgs"); if (!box) return;
    const prevTop = box.scrollTop;
    if (hayMas !== undefined) box.dataset.mas = hayMas ? "1" : "";
    if (!chat.mensajes.length) {
      box.innerHTML = `<div class="chat-empty small">${icon("chat")}<p>Todavía no hay mensajes. ¡Escribí el primero!</p></div>`;
      hydrateIcons(box); return;
    }
    let html = box.dataset.mas ? `<button class="link-btn conv-more" id="conv-more">Ver mensajes anteriores</button>` : "";
    let dia = "", prev = null;
    for (const m of chat.mensajes) {
      const d = fmtDiaChat(m.created_at);
      if (d !== dia) { html += `<div class="conv-day"><span>${esc(d)}</span></div>`; dia = d; prev = null; }
      const seguido = prev && prev.user_id === m.user_id && (new Date(m.created_at) - new Date(prev.created_at)) < 5 * 60e3;
      html += `<div class="cmsg ${m.mio ? "mine" : ""} ${seguido ? "cont" : ""}" data-id="${esc(m.id)}">
        ${m.mio || seguido ? "" : `<span class="avatar xs">${esc(initials(m.nombre || "?"))}</span>`}
        <div class="cbubble">${m.mio || seguido ? "" : `<div class="cname">${esc(m.nombre || "Alguien")}</div>`}
          <div class="ctext">${esc(m.texto).replace(/\n/g, "<br>")}</div>
          <div class="ctime">${fmtHora(m.created_at)}${m.mio || chat.actual?.rol === "coordinador" ? `<button class="cdel" data-del-msg="${esc(m.id)}" title="Borrar mensaje" aria-label="Borrar mensaje">${icon("trash")}</button>` : ""}</div></div>
      </div>`;
      prev = m;
    }
    box.innerHTML = html;
    hydrateIcons(box);
    box.scrollTop = scroll ? box.scrollHeight : prevTop;
    $("#conv-more")?.addEventListener("click", cargarAnteriores);
    $$("[data-del-msg]", box).forEach(b => b.addEventListener("click", async () => {
      if (!confirm("¿Borrar este mensaje para todos?")) return;
      try { await api(`/api/chats/mensajes/${b.dataset.delMsg}`, { method: "DELETE" }); chat.mensajes = chat.mensajes.filter(m => m.id !== b.dataset.delMsg); paintMensajes(false); }
      catch (err) { toast(err.message); }
    }));
  }

  async function cargarAnteriores() {
    const c = chat.actual, first = chat.mensajes[0]; if (!c || !first) return;
    const box = $("#conv-msgs"), prevH = box.scrollHeight;
    try {
      const r = await api(canalPath(c) + `?before=${encodeURIComponent(first.created_at)}&leer=false`);
      chat.mensajes = [...r.mensajes.filter(m => !chat.mensajes.some(x => x.id === m.id)), ...chat.mensajes];
      paintMensajes(false, r.mensajes.length >= 60);
      box.scrollTop = box.scrollHeight - prevH;
    } catch (err) { toast(err.message); }
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
    const encs = state.encuentros.filter(e => [e.titulo, e.tema].join(" ").toLowerCase().includes(ql)).slice(0, 3);
    sItems = [{ kind: "ask", q }];
    let html = `<button class="sr-item" data-i="0">${icon("sparkle")}<span>Preguntar al asistente: <strong>${esc(q)}</strong></span></button>`;
    const group = (title, arr, kind, ic, label, sub) => {
      if (!arr.length) return;
      html += `<div class="sr-group">${title}</div>`;
      arr.forEach(x => { sItems.push({ kind, x }); html += `<button class="sr-item" data-i="${sItems.length - 1}">${icon(ic)}<span>${esc(label(x))}<small>${esc(sub(x))}</small></span></button>`; });
    };
    group("Mis encuentros", encs, "enc", "calendar", e => e.titulo || e.tema || "Encuentro", e => `${e.team_nombre || ""} · ${fmtDay(e.fecha)}`);
    group("Conversaciones", convs, "conv", "chat", c => c.titulo, c => fmtDate(c.updated_at));
    group("Memoria del equipo", mems, "mem", "brain", m => m.texto, m => CAT_LABELS[m.categoria] || m.categoria);
    group("Documentos y fichas", docs, "doc", "file", d => d.titulo, d => `${CATEGORIA_DOC[d.categoria] || TIPOS[d.tipo] || d.tipo} · ${etapasTxt(docEtapas(d))}`);
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
    else if (it.kind === "doc") openDoc(it.x.id);
    else if (it.kind === "enc") openEncuentro(it.x.id);
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
  document.addEventListener("click", e => {
    const b = e.target.closest(".cite");
    if (!b) return;
    const el = b.closest(".msg, .enc-editor, .enc-out");
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
      await readSSE(res, ev => {
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
      });
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
      ensureProgramas().catch(() => {});
      await loadTeams(); await loadConversations(); loadEncuentros(); loadComunidades();
      loadUnread(); startUnreadPoll();
      updateHeader(); pollHealth();
      if (state.view !== "inicio") showView(state.view);
      if (!state.teams.length) toast("Tip: creá tu equipo e indicá su etapa para preparar encuentros según el programa.", 6000);
    } catch (err) { if (err.message !== "No autorizado") toast(err.message); }
  }

  // placeholder corto en pantallas chicas
  const mq = window.matchMedia("(max-width: 600px)");
  const setPh = () => { sInput.placeholder = mq.matches ? "Buscar o preguntar…" : "Buscar en documentos, conversaciones o preguntar algo…"; };
  setPh(); mq.addEventListener?.("change", setPh);

  hydrateIcons(); applyTheme(); showView("inicio");
  (async () => {
    try {
      const s = await (await fetch("/api/session", { credentials: "same-origin" })).json();
      if (!s.authenticated) { showLogin(); return; }
      if (load("uid") !== s.user.id) { save("teamId", null); state.teamId = ""; }
      save("uid", s.user.id);
      state.user = s.user;
    } catch { showLogin(); return; }
    renderProfile(); await boot();
    await procesarInvitacion();
  })();
})();
