/* CRM · Tu inversión en Dubái — panel (vanilla JS, sin dependencias) */
(function () {
  "use strict";

  var API = "api.php?action=";
  var TZ = (Intl.DateTimeFormat().resolvedOptions().timeZone) || "UTC";
  var S = {
    leads: [], stages: {}, csrf: "", notify: "", ics: "",
    page: "inicio", q: "", origen: "", etapa: "", hoy: false, vista: savedView(), plegadas: savedFolds(),
    open: null, dirty: false,
    cal: {}, calErr: "", month: null, day: null,
    tpls: null, docs: null, mail: { to: "", tpl: "", asunto: "", cuerpo: "", boletin: false }
  };
  var PAGES = { inicio: "Inicio", contactos: "Contactos", ventas: "Ventas", correo: "Correo", calendario: "Calendario", documentos: "Documentos" };
  var STAGE_HINT = {
    lead: "Acaba de llegar",
    qualified: "Presupuesto y plazo claros",
    opportunity: "Proyecto concreto / reserva",
    customer: "Ha comprado",
    nurturing: "Aún no: seguir en contacto"
  };
  var ORIGENES = ["Web · Guía", "Web · Boletín", "Web · Consultoría", "Web · Dossier", "Instagram", "WhatsApp", "YouTube", "Referido", "Evento", "Llamada", "Manual", "Otro"];
  var PRESUPUESTOS = ["Menos de 250.000 €", "250.000 – 500.000 €", "500.000 – 1.000.000 €", "Más de 1.000.000 €"];
  var OBJETIVOS = ["Rentabilidad por alquiler", "Revalorización / reventa", "Golden Visa / residencia", "Segunda vivienda", "Crear empresa en Dubái"];
  var DOC_EXT = "pdf,doc,docx,xls,xlsx,ppt,pptx,jpg,jpeg,png,webp,heic,txt,csv,zip,mp4,mov";

  /* ---------- Utilidades ---------- */
  var $ = function (s, c) { return (c || document).querySelector(s); };
  var $$ = function (s, c) { return Array.prototype.slice.call((c || document).querySelectorAll(s)); };
  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }
  function pad(n) { return (n < 10 ? "0" : "") + n; }
  function ymd(d) { return d.getFullYear() + "-" + pad(d.getMonth() + 1) + "-" + pad(d.getDate()); }
  function today() { return ymd(new Date()); }
  function addDays(d, n) { var x = new Date(d); x.setDate(x.getDate() + n); return x; }
  function parseDay(s) { return new Date(s + "T12:00:00"); }
  function fmtDate(iso, withTime) {
    if (!iso) return "";
    var d = new Date(iso.length === 10 ? iso + "T12:00:00" : iso);
    if (isNaN(d)) return iso;
    var o = { day: "numeric", month: "short" };
    if (d.getFullYear() !== new Date().getFullYear()) o.year = "numeric";
    if (withTime) { o.hour = "2-digit"; o.minute = "2-digit"; }
    return d.toLocaleDateString("es-ES", o);
  }
  function fmtTime(iso) { return new Date(iso).toLocaleTimeString("es-ES", { hour: "2-digit", minute: "2-digit" }); }
  function dayLabel(s) {
    var t = today();
    if (s === t) return "Hoy";
    if (s === ymd(addDays(new Date(), 1))) return "Mañana";
    var txt = parseDay(s).toLocaleDateString("es-ES", { weekday: "long", day: "numeric", month: "long" });
    return txt.charAt(0).toUpperCase() + txt.slice(1);
  }
  function num(v) { var n = parseFloat(String(v || "").replace(/[^\d,.-]/g, "").replace(/\./g, "").replace(",", ".")); return isNaN(n) ? 0 : n; }
  function money(n) { return n ? n.toLocaleString("es-ES", { maximumFractionDigits: 0 }) + " €" : "—"; }
  function size(b) { return b > 1048576 ? (b / 1048576).toFixed(1).replace(".", ",") + " MB" : Math.max(1, Math.round(b / 1024)) + " KB"; }
  function initials(l) {
    var s = (l.nombre || l.email || "?").trim().split(/\s+/);
    return ((s[0] || "")[0] + ((s[1] || "")[0] || "")).toUpperCase();
  }
  function waLink(tel) {
    var d = String(tel || "").replace(/\D/g, "");
    if (d.indexOf("00") === 0) d = d.slice(2);
    if (d.length === 9 && /^[67]/.test(d)) d = "34" + d; // móvil español sin prefijo
    return d.length >= 8 ? "https://wa.me/" + d : "";
  }
  function overdue(l) { return !!l.seguimiento && l.seguimiento <= today() && l.etapa !== "customer"; }
  function leadById(id) { return S.leads.filter(function (x) { return x.id === id; })[0]; }
  function leadName(id) { var l = leadById(id); return l ? (l.nombre || l.email || "Sin nombre") : ""; }
  function eventDay(e) { return e.todoElDia ? e.inicio : ymd(new Date(e.inicio)); }
  function gcalLink(title, day, details) {
    var d = (day || today()).replace(/-/g, "");
    var next = ymd(addDays(parseDay(day || today()), 1)).replace(/-/g, "");
    return "https://calendar.google.com/calendar/render?action=TEMPLATE&text=" + encodeURIComponent(title || "") +
      "&dates=" + d + "/" + next + (details ? "&details=" + encodeURIComponent(details) : "");
  }
  var ICON = {
    cal: '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 10h18M8 3v4M16 3v4"/></svg>',
    user: '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><circle cx="12" cy="8" r="4"/><path d="M4 21c1-4 4-6 8-6s7 2 8 6"/></svg>',
    file: '<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5"/></svg>'
  };

  function toast(t, bad) {
    var el = $("#toast");
    el.textContent = t;
    el.className = "toast is-on" + (bad ? " bad" : "");
    clearTimeout(toast.t);
    toast.t = setTimeout(function () { el.className = "toast"; }, 2800);
  }

  function api(action, data, isForm) {
    var opts = { credentials: "same-origin" };
    if (data !== undefined) {
      opts.method = "POST";
      opts.headers = { "X-CSRF": S.csrf };
      if (isForm) opts.body = data;
      else { opts.headers["Content-Type"] = "application/json"; opts.body = JSON.stringify(data); }
    }
    return fetch(API + action, opts).then(function (r) {
      if (r.status === 401) { location.reload(); throw new Error("auth"); }
      return r.json().catch(function () { return { error: "Respuesta no válida del servidor" }; }).then(function (j) {
        if (!r.ok) throw new Error(j.error || "Error");
        return j;
      });
    });
  }

  function load(silent) {
    return api("state").then(function (j) {
      var before = S.leads.length;
      S.leads = j.leads || [];
      S.stages = j.stages;
      S.csrf = j.csrf;
      S.notify = j.notify || "";
      S.ics = j.ics || "";
      if (silent && S.leads.length > before) toast("Nuevo contacto recibido desde la web");
      if (S.ready && (!silent || ["inicio", "contactos", "ventas"].indexOf(S.page) > -1)) render();
    }).catch(function (e) { if (e.message !== "auth") toast("No se pudo cargar el CRM", true); });
  }

  // Eventos de Google Calendar por rango, con caché en memoria (el servidor cachea 5 min).
  function loadCal(from, to, force) {
    var key = from + "_" + to;
    if (S.cal[key] && !force) return Promise.resolve(S.cal[key]);
    return api("calendar&from=" + from + "&to=" + to + "&tz=" + encodeURIComponent(TZ)).then(function (j) {
      S.calErr = j.error || "";
      S.cal[key] = { eventos: j.eventos || [], conectado: !!j.conectado };
      return S.cal[key];
    }).catch(function (e) { S.calErr = e.message; return { eventos: [], conectado: !!S.ics }; });
  }

  /* ---------- Navegación ---------- */
  function go(page) {
    if (!PAGES[page]) page = "inicio";
    S.page = page;
    $("#page-title").textContent = PAGES[page];
    document.title = PAGES[page] + " · CRM";
    $$(".nav-link[data-nav]").forEach(function (a) { a.classList.toggle("is-on", a.getAttribute("data-nav") === page); });
    render();
    $(".content").scrollTop = 0;
    window.scrollTo(0, 0);
  }

  function render() {
    var fn = { inicio: renderHome, contactos: renderContacts, ventas: renderSales, correo: renderMail, calendario: renderCalendar, documentos: renderDocs }[S.page];
    $("#main").className = "page page-" + S.page;
    fn();
  }

  /* ---------- Inicio ---------- */
  function greeting() {
    var h = new Date().getHours();
    return h < 13 ? "Buenos días" : h < 20 ? "Buenas tardes" : "Buenas noches";
  }

  function statsHtml() {
    var L = S.leads, week = Date.now() - 7 * 864e5;
    var nuevos = L.filter(function (l) { return new Date(l.creado).getTime() > week; }).length;
    var clientes = L.filter(function (l) { return l.etapa === "customer"; }).length;
    var abierto = L.filter(function (l) { return l.etapa === "qualified" || l.etapa === "opportunity"; })
      .reduce(function (s, l) { return s + num(l.valor); }, 0);
    var conv = L.length ? Math.round(clientes / L.length * 100) : 0;
    return '<section class="stats">' + [
      ["Contactos", L.length, ""],
      ["Nuevos esta semana", nuevos, ""],
      ["En negociación", money(abierto), "Qualified + Opportunity"],
      ["Clientes", clientes, conv + "% de conversión"]
    ].map(function (s) {
      return '<div class="stat"><span>' + s[0] + "</span><b>" + esc(s[1]) + "</b>" + (s[2] ? "<small>" + esc(s[2]) + "</small>" : "") + "</div>";
    }).join("") + "</section>";
  }

  function renderHome() {
    var t = new Date();
    var from = ymd(t), to = ymd(addDays(t, 7));
    var due = S.leads.filter(overdue).sort(function (a, b) { return a.seguimiento.localeCompare(b.seguimiento); });
    var recent = S.leads.slice().sort(function (a, b) { return (b.creado || "").localeCompare(a.creado || ""); }).slice(0, 6);
    var counts = Object.keys(S.stages).map(function (k) { return [k, S.leads.filter(function (l) { return l.etapa === k; }).length]; });
    var max = Math.max.apply(null, counts.map(function (c) { return c[1]; }).concat([1]));
    var dateTxt = t.toLocaleDateString("es-ES", { weekday: "long", day: "numeric", month: "long" });

    $("#main").innerHTML =
      '<div class="hello"><h2>' + greeting() + ", Pascual</h2><p>" + esc(dateTxt.charAt(0).toUpperCase() + dateTxt.slice(1)) + "</p></div>" +
      '<div class="home-grid">' +
      '<section class="panel tasks"><header class="panel-h"><h3>Tareas pendientes</h3>' +
      '<a class="btn ghost sm" href="' + gcalLink("", today()) + '" target="_blank" rel="noopener">+ Tarea en Google Calendar</a></header>' +
      '<div id="home-tasks"><p class="muted">Cargando tu Google Calendar…</p></div>' +
      (due.length ? '<h4 class="sub">Seguimientos de contactos</h4><ul class="task-list">' + due.map(function (l) {
        return '<li class="task crm' + (l.seguimiento < from ? " late" : "") + '" data-id="' + esc(l.id) + '" tabindex="0"><span class="t-when">' +
          (l.seguimiento < from ? "Atrasado · " + fmtDate(l.seguimiento) : "Hoy") + '</span><span class="t-what">' + ICON.user + " " +
          esc(l.nombre || l.email) + (l.proxima_accion ? " — " + esc(l.proxima_accion) : "") + "</span></li>";
      }).join("") + "</ul>" : "") +
      "</section>" +
      '<div class="home-side">' + statsHtml() +
      '<section class="panel"><header class="panel-h"><h3>Pipeline</h3><a href="#ventas" class="link">Ver ventas →</a></header><div class="bars">' +
      counts.map(function (c) {
        return '<a href="#ventas" class="bar-row"><span>' + esc(S.stages[c[0]]) + '</span><span class="bar"><i class="s-' + c[0] + '" style="width:' + (c[1] / max * 100) + '%"></i></span><b>' + c[1] + "</b></a>";
      }).join("") + "</div></section>" +
      '<section class="panel"><header class="panel-h"><h3>Últimos contactos</h3><a href="#contactos" class="link">Ver todos →</a></header>' +
      (recent.length ? '<ul class="mini-list">' + recent.map(function (l) {
        return '<li data-id="' + esc(l.id) + '" tabindex="0"><span class="avatar">' + esc(initials(l)) + '</span><span class="who"><b>' + esc(l.nombre || "Sin nombre") +
          (l.nuevo ? ' <span class="pill new">Nuevo</span>' : "") + "</b><small>" + esc(l.origen || "") + " · " + fmtDate(l.creado) + '</small></span><span class="stage s-' + esc(l.etapa) + '">' + esc(S.stages[l.etapa] || "") + "</span></li>";
      }).join("") + "</ul>" : '<p class="muted">Aún no hay contactos. Los formularios de la web aparecerán aquí solos.</p>') +
      "</section></div></div>";

    if (!S.ics) {
      $("#home-tasks").innerHTML = '<div class="connect"><p><b>Conecta tu Google Calendar</b> para ver aquí las tareas y citas que te programes.</p><button class="btn primary sm" data-act="settings">Conectar</button></div>';
      return;
    }
    loadCal(from, to).then(function (c) {
      var box = $("#home-tasks");
      if (!box) return;
      if (S.calErr) { box.innerHTML = '<p class="err">' + esc(S.calErr) + "</p>"; return; }
      var list = c.eventos.filter(function (e) { return e.todoElDia ? e.fin >= from : eventDay(e) >= from; });
      if (!list.length) { box.innerHTML = '<p class="muted">Nada programado para los próximos 7 días.</p>'; return; }
      var groups = {};
      list.forEach(function (e) { var d = e.todoElDia && e.inicio < from ? from : eventDay(e); (groups[d] = groups[d] || []).push(e); });
      box.innerHTML = Object.keys(groups).sort().map(function (d) {
        return '<h4 class="sub">' + esc(dayLabel(d)) + '</h4><ul class="task-list">' + groups[d].map(eventLi).join("") + "</ul>";
      }).join("");
    });
  }

  function eventLi(e) {
    var past = !e.todoElDia && new Date(e.fin).getTime() < Date.now();
    return '<li class="task' + (past ? " done" : "") + '"><span class="t-when">' + (e.todoElDia ? "Todo el día" : fmtTime(e.inicio) + "–" + fmtTime(e.fin)) +
      '</span><span class="t-what">' + esc(e.titulo) + (e.lugar ? '<small>' + esc(e.lugar) + "</small>" : "") + "</span></li>";
  }

  /* ---------- Contactos ---------- */
  function filtered() {
    var q = S.q.toLowerCase().trim();
    return S.leads.filter(function (l) {
      if (S.origen && l.origen !== S.origen) return false;
      if (S.etapa && l.etapa !== S.etapa) return false;
      if (S.hoy && !overdue(l)) return false;
      if (!q) return true;
      return [l.nombre, l.email, l.telefono, l.proyecto, l.etiquetas, l.pais, l.origen].join(" ").toLowerCase().indexOf(q) > -1;
    }).sort(function (a, b) { return (b.actualizado || "").localeCompare(a.actualizado || ""); });
  }

  function toolbar(withStage) {
    var have = {};
    S.leads.forEach(function (l) { if (l.origen) have[l.origen] = 1; });
    return '<nav class="toolbar"><input class="search" id="q" type="search" placeholder="Buscar nombre, email, teléfono, proyecto…" value="' + esc(S.q) + '" />' +
      '<select id="f-origen" aria-label="Origen"><option value="">Todos los orígenes</option>' + Object.keys(have).sort().map(function (o) {
        return "<option" + (o === S.origen ? " selected" : "") + ">" + esc(o) + "</option>";
      }).join("") + "</select>" +
      (withStage ? '<select id="f-etapa" aria-label="Etapa"><option value="">Todas las etapas</option>' + Object.keys(S.stages).map(function (k) {
        return '<option value="' + k + '"' + (k === S.etapa ? " selected" : "") + ">" + esc(S.stages[k]) + "</option>";
      }).join("") + "</select>" : "") +
      '<label class="chk"><input type="checkbox" id="f-hoy"' + (S.hoy ? " checked" : "") + " /> Seguimientos pendientes</label></nav>";
  }

  function savedFolds() {
    try { return JSON.parse(localStorage.getItem("crm-plegadas") || "{}") || {}; } catch (e) { return {}; }
  }
  function savedView() {
    try { return localStorage.getItem("crm-vista") === "columnas" ? "columnas" : "lista"; } catch (e) { return "lista"; }
  }
  function viewToggle() {
    return '<div class="view-toggle" role="group" aria-label="Forma de ver">' + [["lista", "Lista"], ["columnas", "Columnas"]].map(function (v) {
      return '<button type="button" data-act="vista" data-v="' + v[0] + '" aria-pressed="' + (S.vista === v[0]) + '">' + v[1] + "</button>";
    }).join("") + "</div>";
  }

  function renderContacts() {
    var cols = S.vista === "columnas";
    if (cols) S.etapa = "";
    $("#main").innerHTML = viewToggle() + toolbar(!cols) + '<div id="results"></div>';
    refreshResults();
  }

  function contactsTable(list) {
    if (!list.length) return '<p class="empty big">' + (S.leads.length ? "No hay contactos con estos filtros." : "Aún no hay contactos. Añade el primero con «+ Nuevo contacto».") + "</p>";
    return '<div class="table-wrap"><table class="contacts"><thead><tr><th>Nombre</th><th>Etapa</th><th>Origen</th><th>Teléfono</th><th>Proyecto</th><th>Seguimiento</th><th>Alta</th></tr></thead><tbody>' +
      list.map(function (l) {
        return '<tr data-id="' + esc(l.id) + '" tabindex="0"><td class="c-name"><span class="avatar">' + esc(initials(l)) + "</span><span><b>" + esc(l.nombre || "Sin nombre") + (l.nuevo ? ' <span class="pill new">Nuevo</span>' : "") + "</b><small>" + esc(l.email) + "</small></span></td>" +
          '<td><span class="stage s-' + esc(l.etapa) + '">' + esc(S.stages[l.etapa] || l.etapa) + '</span></td><td data-l="Origen">' + esc(l.origen) + '</td><td data-l="Teléfono">' + esc(l.telefono) + '</td><td data-l="Proyecto">' + esc(l.proyecto) + "</td>" +
          '<td data-l="Seguimiento" class="' + (overdue(l) ? "late" : "") + '">' + fmtDate(l.seguimiento) + '</td><td data-l="Alta">' + fmtDate(l.creado) + "</td></tr>";
      }).join("") + "</tbody></table></div>";
  }

  /* ---------- Ventas (pipeline) ---------- */
  function card(l) {
    var tags = [];
    if (l.nuevo) tags.push('<span class="pill new">Nuevo</span>');
    if (l.origen) tags.push('<span class="pill">' + esc(l.origen) + "</span>");
    var meta = [];
    if (l.proyecto) meta.push(esc(l.proyecto));
    if (l.presupuesto) meta.push(esc(l.presupuesto));
    var foot = "";
    if (l.seguimiento) foot = '<span class="due' + (overdue(l) ? " late" : "") + '">' + ICON.cal + " " + fmtDate(l.seguimiento) + (l.proxima_accion ? " · " + esc(l.proxima_accion) : "") + "</span>";
    else if (l.proxima_accion) foot = '<span class="due">' + esc(l.proxima_accion) + "</span>";
    return '<article class="card" draggable="true" data-id="' + esc(l.id) + '" tabindex="0">' +
      '<div class="card-top"><span class="avatar">' + esc(initials(l)) + '</span><div class="who"><b>' + esc(l.nombre || "Sin nombre") + "</b><small>" + esc(l.email || l.telefono || "") + "</small></div></div>" +
      (num(l.valor) ? '<span class="val">' + money(num(l.valor)) + "</span>" : "") +
      (meta.length ? '<p class="meta">' + meta.join(" · ") + "</p>" : "") +
      '<div class="tags">' + tags.join("") + "</div>" + foot + "</article>";
  }

  function renderSales() {
    $("#main").innerHTML = statsHtml() + toolbar(false) + '<div id="results"></div>';
    renderBoard();
  }

  function renderBoard() {
    var list = filtered(), keys = Object.keys(S.stages);
    var tpl = function (w) { return keys.map(function (k) { return S.plegadas[k] ? "52px" : w; }).join(" "); };
    $("#results").innerHTML = '<div class="board" style="--cols:' + tpl("minmax(180px, 1fr)") + ";--cols-m:" + tpl("84%") + '">' + keys.map(function (k) {
      var items = list.filter(function (l) { return l.etapa === k; });
      var sum = items.reduce(function (s, l) { return s + num(l.valor); }, 0);
      var fold = '<button type="button" class="fold" data-act="fold" data-stage="' + k + '" aria-expanded="' + !S.plegadas[k] + '" aria-label="' + (S.plegadas[k] ? "Desplegar " : "Ocultar ") + esc(S.stages[k]) + '">' +
        '<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m15 6-6 6 6 6"/></svg></button>';
      if (S.plegadas[k]) return '<section class="col folded" data-stage="' + k + '">' + fold + '<span class="count">' + items.length + '</span><h2><i class="dot s-' + k + '"></i>' + esc(S.stages[k]) + "</h2></section>";
      return '<section class="col" data-stage="' + k + '"><header><div><h2>' + fold + '<i class="dot s-' + k + '"></i>' + esc(S.stages[k]) + "</h2><small>" + STAGE_HINT[k] + "</small></div>" +
        '<span class="count">' + items.length + "</span></header>" + (sum ? '<p class="sum">' + money(sum) + "</p>" : "") +
        '<div class="cards">' + (items.map(card).join("") || '<p class="empty">Arrastra aquí</p>') + "</div></section>";
    }).join("") + "</div>";
  }

  function refreshResults() {
    if (S.page === "contactos" && S.vista !== "columnas") $("#results").innerHTML = contactsTable(filtered());
    else if (S.page === "contactos") renderBoard();
    else if (S.page === "ventas") renderBoard();
  }

  /* ---------- Correo ---------- */
  function fillVars(txt, l) {
    l = l || {};
    var first = (l.nombre || "").split(/\s+/)[0];
    return String(txt || "").replace(/\{nombre\}/g, first || "").replace(/\{proyecto\}/g, l.proyecto || "el proyecto").replace(/\{nombre_completo\}/g, l.nombre || "");
  }
  function mailTarget() {
    var v = S.mail.to.trim().toLowerCase();
    var m = v.match(/<([^>]+)>/);
    var email = (m ? m[1] : v).trim();
    return { email: email, lead: S.leads.filter(function (l) { return l.email && l.email === email; })[0] };
  }

  function renderMail() {
    if (!S.tpls) {
      $("#main").innerHTML = '<p class="muted">Cargando plantillas…</p>';
      api("templates").then(function (j) { S.tpls = j.plantillas; if (S.page === "correo") renderMail(); }).catch(function (e) { toast(e.message, true); });
      return;
    }
    var subs = S.leads.filter(function (l) { return l.boletin && l.email; });
    $("#main").innerHTML =
      '<div class="mail-grid">' +
      '<section class="panel"><header class="panel-h"><h3>Plantillas</h3><button class="btn ghost sm" data-act="tpl-new">+ Nueva</button></header><ul class="tpl-list">' +
      S.tpls.map(function (t) {
        return '<li><button class="tpl' + (S.mail.tpl === t.id ? " is-on" : "") + '" data-tpl="' + esc(t.id) + '"><b>' + esc(t.nombre) + "</b><small>" + esc(t.asunto) + "</small></button>" +
          '<button class="btn icon sm" data-act="tpl-edit" data-id="' + esc(t.id) + '" aria-label="Editar plantilla">✎</button></li>';
      }).join("") + '</ul><p class="muted small">Usa <code>{nombre}</code> y <code>{proyecto}</code>: se rellenan con los datos del contacto.</p></section>' +
      '<section class="panel compose"><header class="panel-h"><h3>Redactar</h3></header>' +
      '<form id="mail-form" autocomplete="off">' +
      '<label class="f"><span>Para</span><input id="m-to" list="dl-contacts" placeholder="Escribe un nombre o email" value="' + esc(S.mail.to) + '"' + (S.mail.boletin ? " disabled" : "") + " /></label>" +
      '<datalist id="dl-contacts">' + S.leads.filter(function (l) { return l.email; }).map(function (l) { return "<option value=\"" + esc((l.nombre ? l.nombre + " " : "") + "<" + l.email + ">") + "\"></option>"; }).join("") + "</datalist>" +
      '<label class="chk"><input type="checkbox" id="m-bol"' + (S.mail.boletin ? " checked" : "") + " /> Enviar a todos los suscritos al boletín (" + subs.length + ") en copia oculta</label>" +
      '<label class="f"><span>Asunto</span><input id="m-asunto" value="' + esc(S.mail.asunto) + '" /></label>' +
      '<label class="f"><span>Mensaje</span><textarea id="m-cuerpo" rows="12">' + esc(S.mail.cuerpo) + "</textarea></label>" +
      '<div class="d-actions"><button class="btn primary" type="button" data-act="mail-gmail">Abrir en Gmail</button><button class="btn ghost" type="button" data-act="mail-app">Abrir en mi app de correo</button><button class="btn ghost" type="button" data-act="mail-copy">Copiar texto</button></div>' +
      '<p class="muted small">El correo se envía desde tu Gmail. Si el destinatario es un contacto, queda anotado en su historial.</p>' +
      "</form></section></div>";
  }

  function composeUrl(kind) {
    var tg = mailTarget();
    var subj = fillVars(S.mail.asunto, tg.lead), body = fillVars(S.mail.cuerpo, tg.lead);
    var bcc = S.mail.boletin ? S.leads.filter(function (l) { return l.boletin && l.email; }).map(function (l) { return l.email; }).join(",") : "";
    if (S.mail.boletin) { subj = fillVars(S.mail.asunto, {}); body = fillVars(S.mail.cuerpo, {}).replace(/^Hola ,/m, "Hola,"); }
    if (kind === "gmail") {
      return "https://mail.google.com/mail/?view=cm&fs=1" + (S.mail.boletin ? "&bcc=" + encodeURIComponent(bcc) : "&to=" + encodeURIComponent(tg.email)) +
        "&su=" + encodeURIComponent(subj) + "&body=" + encodeURIComponent(body);
    }
    if (kind === "app") return "mailto:" + (S.mail.boletin ? "?bcc=" + encodeURIComponent(bcc) + "&" : encodeURIComponent(tg.email) + "?") + "subject=" + encodeURIComponent(subj) + "&body=" + encodeURIComponent(body);
    return subj + "\n\n" + body;
  }

  function logMail() {
    var tg = mailTarget();
    if (S.mail.boletin || !tg.lead) return;
    saveLead(tg.lead.id, { nota: "✉ Email enviado: " + fillVars(S.mail.asunto, tg.lead) }, true).catch(function () {});
  }

  function openTemplate(id) {
    var t = id ? S.tpls.filter(function (x) { return x.id === id; })[0] : { id: "", nombre: "", asunto: "", cuerpo: "" };
    S.open = "__tpl";
    S.dirty = false;
    $(".drawer-panel").innerHTML = '<form id="tpl-form"><header class="d-head"><h2 id="d-title">' + (t.id ? "Editar plantilla" : "Nueva plantilla") + '</h2><button type="button" class="btn icon" data-close aria-label="Cerrar">✕</button></header>' +
      '<input type="hidden" name="id" value="' + esc(t.id) + '" />' +
      '<label class="f"><span>Nombre de la plantilla</span><input name="nombre" required value="' + esc(t.nombre) + '" /></label>' +
      '<label class="f"><span>Asunto</span><input name="asunto" value="' + esc(t.asunto) + '" /></label>' +
      '<label class="f"><span>Mensaje</span><textarea name="cuerpo" rows="14">' + esc(t.cuerpo) + "</textarea></label>" +
      '<div class="d-actions"><button class="btn primary" type="submit">Guardar</button>' + (t.id ? '<button class="btn danger" type="button" data-act="tpl-del">Eliminar</button>' : "") + "</div></form>";
    showDrawer();
  }

  /* ---------- Calendario ---------- */
  function renderCalendar() {
    var m = S.month || new Date(new Date().getFullYear(), new Date().getMonth(), 1);
    S.month = m;
    var first = new Date(m.getFullYear(), m.getMonth(), 1);
    var start = addDays(first, -((first.getDay() + 6) % 7));
    var days = [];
    for (var i = 0; i < 42; i++) days.push(addDays(start, i));
    if (ymd(days[35]).slice(0, 7) !== ymd(first).slice(0, 7)) days = days.slice(0, 35);
    var from = ymd(days[0]), to = ymd(days[days.length - 1]);
    var sel = S.day || today();
    var title = first.toLocaleDateString("es-ES", { month: "long", year: "numeric" });

    $("#main").innerHTML =
      '<div class="cal-head"><div class="cal-nav"><button class="btn icon" data-act="cal-prev" aria-label="Mes anterior">‹</button><h2>' + esc(title.charAt(0).toUpperCase() + title.slice(1)) +
      '</h2><button class="btn icon" data-act="cal-next" aria-label="Mes siguiente">›</button><button class="btn ghost sm" data-act="cal-today">Hoy</button></div>' +
      '<div class="cal-tools"><span class="legend"><i class="lg-g"></i>Google Calendar <i class="lg-c"></i>Seguimientos</span>' +
      '<a class="btn primary sm" href="' + gcalLink("", sel) + '" target="_blank" rel="noopener">+ Evento en Google Calendar</a></div></div>' +
      (!S.ics ? '<div class="connect"><p><b>Conecta tu Google Calendar</b> para ver aquí tus citas y tareas.</p><button class="btn primary sm" data-act="settings">Conectar</button></div>' : "") +
      '<div class="cal-wrap"><div class="cal" role="grid">' +
      ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"].map(function (d) { return '<div class="cal-dow">' + d + "</div>"; }).join("") +
      days.map(function (d) {
        var k = ymd(d);
        return '<button class="cal-day' + (k.slice(0, 7) !== ymd(first).slice(0, 7) ? " out" : "") + (k === today() ? " today" : "") + (k === sel ? " sel" : "") +
          '" data-day="' + k + '"><span class="n">' + d.getDate() + '</span><span class="ev-list" data-evs="' + k + '"></span></button>';
      }).join("") + '</div><section class="panel agenda" id="agenda"></section></div>';

    var follow = {};
    S.leads.forEach(function (l) { if (l.seguimiento && l.etapa !== "customer") (follow[l.seguimiento] = follow[l.seguimiento] || []).push(l); });
    var paint = function (evs) {
      var by = {};
      evs.forEach(function (e) {
        var d0 = eventDay(e), d1 = e.todoElDia ? e.fin : d0;
        for (var d = parseDay(d0), n = 0; ymd(d) <= d1 && n < 40; d = addDays(d, 1), n++) (by[ymd(d)] = by[ymd(d)] || []).push(e);
      });
      $$("[data-evs]").forEach(function (box) {
        var k = box.getAttribute("data-evs");
        var items = (by[k] || []).map(function (e) { return '<i class="ev g">' + (e.todoElDia ? "" : fmtTime(e.inicio) + " ") + esc(e.titulo) + "</i>"; })
          .concat((follow[k] || []).map(function (l) { return '<i class="ev c">' + esc(l.nombre || l.email) + "</i>"; }));
        box.innerHTML = items.slice(0, 3).join("") + (items.length > 3 ? '<i class="ev more">+' + (items.length - 3) + "</i>" : "");
      });
      renderAgenda(sel, by[sel] || [], follow[sel] || []);
    };
    paint([]);
    if (S.ics) loadCal(from, to).then(function (c) { if (S.page === "calendario" && S.month === m) { paint(c.eventos); if (S.calErr) toast(S.calErr, true); } });
  }

  function renderAgenda(day, evs, follow) {
    var box = $("#agenda");
    if (!box) return;
    box.innerHTML = '<header class="panel-h"><h3>' + esc(dayLabel(day)) + '</h3><a class="btn ghost sm" href="' + gcalLink("", day) + '" target="_blank" rel="noopener">+ Añadir</a></header>' +
      (evs.length || follow.length ? '<ul class="task-list">' + evs.map(eventLi).join("") + follow.map(function (l) {
        return '<li class="task crm" data-id="' + esc(l.id) + '" tabindex="0"><span class="t-when">Seguimiento</span><span class="t-what">' + ICON.user + " " + esc(l.nombre || l.email) + (l.proxima_accion ? " — " + esc(l.proxima_accion) : "") + "</span></li>";
      }).join("") + "</ul>" : '<p class="muted">Nada programado este día.</p>');
  }

  /* ---------- Documentos ---------- */
  function loadDocs() {
    return api("docs").then(function (j) { S.docs = j.docs || []; return S.docs; });
  }

  function leadOptions(selected) {
    return '<option value="">Sin contacto</option>' + S.leads.slice().sort(function (a, b) { return (a.nombre || a.email).localeCompare(b.nombre || b.email); }).map(function (l) {
      return '<option value="' + esc(l.id) + '"' + (l.id === selected ? " selected" : "") + ">" + esc(l.nombre || l.email) + "</option>";
    }).join("");
  }

  function docRow(d, compact) {
    var url = API + "doc&id=" + encodeURIComponent(d.id);
    return '<li class="doc" data-doc="' + esc(d.id) + '"><span class="doc-ic ext-' + esc(d.ext) + '">' + esc(d.ext.toUpperCase()) + '</span><span class="doc-main"><a href="' + url + '" target="_blank" rel="noopener"><b>' + esc(d.nombre) + "</b></a><small>" + size(d.tamano) + " · " + fmtDate(d.creado) +
      (compact ? "" : (d.lead && leadName(d.lead) ? " · " + esc(leadName(d.lead)) : "")) + "</small></span>" +
      (compact ? "" : '<select class="doc-lead" aria-label="Contacto vinculado">' + leadOptions(d.lead) + "</select>") +
      '<a class="btn icon sm" href="' + url + '&dl=1" aria-label="Descargar">↓</a><button class="btn icon sm" data-act="doc-del" aria-label="Eliminar">✕</button></li>';
  }

  function renderDocs() {
    if (!S.docs) {
      $("#main").innerHTML = '<p class="muted">Cargando documentos…</p>';
      loadDocs().then(function () { if (S.page === "documentos") renderDocs(); }).catch(function (e) { toast(e.message, true); });
      return;
    }
    var q = S.q.toLowerCase();
    var list = S.docs.filter(function (d) { return !q || (d.nombre + " " + leadName(d.lead)).toLowerCase().indexOf(q) > -1; })
      .sort(function (a, b) { return b.creado.localeCompare(a.creado); });
    $("#main").innerHTML =
      '<label class="drop" id="dropzone"><input type="file" id="doc-file" multiple accept="' + DOC_EXT.split(",").map(function (e) { return "." + e; }).join(",") + '" hidden />' +
      ICON.file + "<b>Arrastra archivos aquí o pulsa para subir</b><small>Contratos, dossiers, pasaportes, planos… PDF, Word, Excel, imágenes · máx. 25 MB</small></label>" +
      '<nav class="toolbar"><input class="search" id="q-docs" type="search" placeholder="Buscar documento o contacto…" value="' + esc(S.q) + '" /></nav>' +
      (list.length ? '<ul class="doc-list">' + list.map(function (d) { return docRow(d); }).join("") + "</ul>" : '<p class="empty big">' + (S.docs.length ? "Ningún documento coincide." : "Todavía no has subido documentos.") + "</p>");
  }

  function uploadFiles(files, leadId) {
    var arr = Array.prototype.slice.call(files || []);
    if (!arr.length) return Promise.resolve();
    toast("Subiendo " + arr.length + (arr.length > 1 ? " archivos…" : " archivo…"));
    return arr.reduce(function (p, f) {
      return p.then(function () {
        var fd = new FormData();
        fd.append("file", f);
        fd.append("lead", leadId || "");
        return api("upload", fd, true).then(function (j) { (S.docs = S.docs || []).push(j.doc); })
          .catch(function (e) { toast(f.name + ": " + e.message, true); });
      });
    }, S.docs ? Promise.resolve() : loadDocs()).then(function () {
      toast("Subido");
      if (S.page === "documentos") renderDocs();
      if (S.open && S.open.charAt(0) !== "_") renderLeadDocs(S.open);
    });
  }

  /* ---------- Ficha de contacto ---------- */
  function field(name, label, val, type, list) {
    return '<label class="f"><span>' + label + '</span><input name="' + name + '" type="' + (type || "text") + '" value="' + esc(val) + '"' + (list ? ' list="dl-' + name + '"' : "") + " /></label>";
  }
  function select(name, label, val, arr) {
    var opts = val && arr.indexOf(val) < 0 ? [val].concat(arr) : arr;
    return '<label class="f"><span>' + label + '</span><select name="' + name + '">' + opts.map(function (o) {
      return "<option" + (o === val ? " selected" : "") + ">" + esc(o) + "</option>";
    }).join("") + "</select></label>";
  }
  function datalist(name, arr) {
    return '<datalist id="dl-' + name + '">' + arr.map(function (o) { return "<option>" + esc(o) + "</option>"; }).join("") + "</datalist>";
  }

  function openLead(id) {
    var l = id ? leadById(id) : null;
    if (id && !l) return;
    l = l || { id: "", etapa: "lead", actividad: [], origen: "Manual" };
    S.open = l.id || "__new";
    S.dirty = false;
    var wa = waLink(l.telefono);
    var quick = [
      wa ? '<a class="btn wa sm" href="' + wa + '" target="_blank" rel="noopener">WhatsApp</a>' : "",
      l.telefono ? '<a class="btn ghost sm" href="tel:' + esc(l.telefono.replace(/[^\d+]/g, "")) + '">Llamar</a>' : "",
      l.email ? '<button type="button" class="btn ghost sm" data-act="lead-mail">Email</button>' : "",
      l.id ? '<a class="btn ghost sm" href="' + gcalLink((l.proxima_accion || "Seguimiento") + " · " + (l.nombre || l.email), l.seguimiento || today(), [l.telefono, l.email, l.proyecto].filter(Boolean).join(" · ")) + '" target="_blank" rel="noopener">' + ICON.cal + " Agendar</a>" : ""
    ].join("");
    var stages = Object.keys(S.stages).map(function (k) {
      return '<button type="button" class="seg s-' + k + (k === l.etapa ? " is-on" : "") + '" data-stage="' + k + '">' + esc(S.stages[k]) + "</button>";
    }).join("");
    var acts = (l.actividad || []).slice().reverse().map(function (a) {
      return '<li class="a-' + esc(a.tipo) + '"><time>' + fmtDate(a.fecha, true) + "</time><p>" + esc(a.texto).replace(/\n/g, "<br>") + "</p></li>";
    }).join("");
    var utm = l.utm && Object.keys(l.utm).length ? '<p class="muted small">Campaña: ' + esc(Object.keys(l.utm).map(function (k) { return k.replace("utm_", "") + "=" + l.utm[k]; }).join(" · ")) + "</p>" : "";

    $(".drawer-panel").innerHTML =
      '<form id="lead-form" autocomplete="off">' +
      '<header class="d-head"><div><h2 id="d-title">' + esc(l.nombre || (l.id ? "Sin nombre" : "Nuevo contacto")) + "</h2>" +
      (l.id ? '<p class="muted small">' + esc(l.origen || "") + " · alta " + fmtDate(l.creado) + "</p>" : "") + "</div>" +
      '<button type="button" class="btn icon" data-close aria-label="Cerrar">✕</button></header>' +
      (quick ? '<div class="quick">' + quick + "</div>" : "") +
      '<div class="segs" role="group" aria-label="Etapa">' + stages + "</div>" +
      '<input type="hidden" name="etapa" value="' + esc(l.etapa) + '" />' +
      '<div class="grid">' +
      field("nombre", "Nombre", l.nombre) + field("email", "Email", l.email, "email") +
      field("telefono", "Teléfono / WhatsApp", l.telefono, "tel") + field("pais", "País", l.pais) +
      select("origen", "Origen", l.origen || "Manual", ORIGENES) + field("presupuesto", "Presupuesto", l.presupuesto, "text", true) +
      field("objetivo", "Objetivo", l.objetivo, "text", true) + field("proyecto", "Proyecto de interés", l.proyecto) +
      field("valor", "Valor operación (€)", l.valor, "text") + field("etiquetas", "Etiquetas", l.etiquetas) +
      field("proxima_accion", "Próxima acción", l.proxima_accion) + field("seguimiento", "Fecha de seguimiento", l.seguimiento, "date") +
      "</div>" +
      '<label class="chk"><input type="checkbox" name="boletin"' + (l.boletin ? " checked" : "") + " /> Suscrito al boletín semanal</label>" +
      '<label class="f full"><span>Añadir nota</span><textarea name="nota" rows="3" placeholder="Llamada, lo que te ha contado, siguiente paso…"></textarea></label>' +
      '<div class="d-actions"><button class="btn primary" type="submit">' + (l.id ? "Guardar" : "Crear contacto") + "</button>" +
      (l.id ? '<button class="btn danger" type="button" data-act="delete">Eliminar</button>' : "") + "</div>" +
      (l.id ? '<div class="lead-docs"><header class="panel-h"><h3>Documentos</h3><label class="btn ghost sm">+ Subir<input type="file" id="lead-file" multiple hidden /></label></header><ul class="doc-list" id="lead-doc-list"><li class="muted small">Cargando…</li></ul></div>' : "") +
      (acts ? '<h3>Actividad</h3><ol class="timeline">' + acts + "</ol>" : "") + utm +
      datalist("presupuesto", PRESUPUESTOS) + datalist("objetivo", OBJETIVOS) +
      "</form>";
    showDrawer();
    if (!l.id) setTimeout(function () { $("#lead-form [name=nombre]").focus(); }, 60);
    else renderLeadDocs(l.id);
    if (l.nuevo) api("seen", { id: l.id }).then(function () { delete l.nuevo; render(); }).catch(function () {});
  }

  function renderLeadDocs(id) {
    (S.docs ? Promise.resolve(S.docs) : loadDocs()).then(function (docs) {
      var box = $("#lead-doc-list");
      if (!box || S.open !== id) return;
      var mine = docs.filter(function (d) { return d.lead === id; });
      box.innerHTML = mine.length ? mine.map(function (d) { return docRow(d, true); }).join("") : '<li class="muted small">Sin documentos. Sube aquí contratos, pasaporte, reserva…</li>';
    }).catch(function () {});
  }

  function showDrawer() {
    var d = $("#drawer");
    d.hidden = false;
    requestAnimationFrame(function () { d.classList.add("is-on"); });
    document.body.classList.add("lock");
  }
  function closeDrawer(force) {
    if (S.dirty && !force && !confirm("Tienes cambios sin guardar. ¿Cerrar igualmente?")) return;
    var d = $("#drawer");
    d.classList.remove("is-on");
    document.body.classList.remove("lock");
    S.open = null; S.dirty = false;
    setTimeout(function () { if (!d.classList.contains("is-on")) d.hidden = true; }, 250);
  }

  function saveLead(id, patch, quiet) {
    return api("save", { id: id || "", patch: patch }).then(function (j) {
      var i = S.leads.findIndex(function (x) { return x.id === j.lead.id; });
      if (i > -1) S.leads[i] = j.lead; else S.leads.push(j.lead);
      if (!quiet || ["inicio", "contactos", "ventas", "calendario"].indexOf(S.page) > -1) render();
      return j.lead;
    });
  }

  function submitLead(form) {
    var patch = {};
    $$("input[name], select[name], textarea[name]", form).forEach(function (f) {
      patch[f.name] = f.type === "checkbox" ? f.checked : f.value.trim();
    });
    if (!patch.nombre && !patch.email && !patch.telefono) { toast("Pon al menos nombre, email o teléfono", true); return; }
    var btn = $("button[type=submit]", form);
    btn.disabled = true;
    saveLead(S.open && S.open.charAt(0) !== "_" ? S.open : "", patch).then(function (lead) {
      S.dirty = false;
      toast("Guardado");
      openLead(lead.id);
    }).catch(function (e) { toast(e.message, true); btn.disabled = false; });
  }

  /* ---------- Ajustes ---------- */
  function openSettings() {
    S.open = "__settings";
    S.dirty = false;
    $(".drawer-panel").innerHTML =
      '<header class="d-head"><h2 id="d-title">Ajustes</h2><button type="button" class="btn icon" data-close aria-label="Cerrar">✕</button></header>' +
      '<form class="box set-form"><h3>Google Calendar</h3><p class="muted small">En Google Calendar (ordenador): ⚙ Configuración → elige tu calendario → <b>Integrar el calendario</b> → copia la <b>Dirección secreta en formato iCal</b> y pégala aquí. Es privada: no la compartas.</p>' +
      '<label class="f"><span>Dirección secreta iCal</span><input name="ics" type="url" value="' + esc(S.ics) + '" placeholder="https://calendar.google.com/calendar/ical/…/private-…/basic.ics" /></label>' +
      '<button class="btn primary" type="submit">Conectar calendario</button></form>' +
      '<form class="box set-form"><h3>Avisos por email</h3><p class="muted small">Recibe un email cada vez que entre un contacto desde la web.</p>' +
      '<label class="f"><span>Email para avisos</span><input name="notify" type="email" value="' + esc(S.notify) + '" placeholder="tu@email.com" /></label>' +
      '<button class="btn primary" type="submit">Guardar aviso</button></form>' +
      '<div class="box"><h3>Exportar</h3><p class="muted small">CSV para Excel o para importar en Mailchimp/Brevo. Haz una copia de seguridad de vez en cuando.</p>' +
      '<div class="quick"><a class="btn ghost sm" href="' + API + 'export">Contactos (CSV)</a><a class="btn ghost sm" href="' + API + 'export&solo=boletin">Suscritos al boletín (CSV)</a><a class="btn ghost sm" href="' + API + 'export&fmt=json">Copia de seguridad (JSON)</a></div></div>' +
      '<form class="box set-form"><h3>Cambiar contraseña</h3>' +
      '<label class="f"><span>Contraseña actual</span><input name="actual" type="password" autocomplete="current-password" required /></label>' +
      '<label class="f"><span>Nueva contraseña (mín. 10)</span><input name="nueva" type="password" minlength="10" autocomplete="new-password" required /></label>' +
      '<button class="btn primary" type="submit">Cambiar contraseña</button></form>' +
      '<form method="post" class="box"><input type="hidden" name="form" value="logout" /><button class="btn ghost" type="submit">Cerrar sesión</button></form>';
    showDrawer();
  }

  function submitSettings(form) {
    var data = {};
    $$("input[name]", form).forEach(function (f) { data[f.name] = f.value.trim(); });
    api("settings", data).then(function (j) {
      if (j.csrf) S.csrf = j.csrf;
      if ("notify" in data) S.notify = data.notify;
      if ("ics" in data) { S.ics = data.ics; S.cal = {}; S.calErr = ""; render(); }
      toast("ics" in data ? (data.ics ? "Calendario conectado" : "Calendario desconectado") : "Guardado");
      if (data.nueva) form.reset();
      S.dirty = false;
    }).catch(function (e) { toast(e.message, true); });
  }

  /* ---------- Eventos ---------- */
  window.addEventListener("hashchange", function () { go(location.hash.slice(1)); });

  document.addEventListener("click", function (e) {
    var t = e.target;
    if (t.closest("[data-close]")) { closeDrawer(); return; }
    var act = t.closest("[data-act]");
    if (act) {
      var a = act.getAttribute("data-act");
      if (a === "new") openLead(null);
      if (a === "fold") {
        var st = act.getAttribute("data-stage");
        if (S.plegadas[st]) delete S.plegadas[st]; else S.plegadas[st] = 1;
        try { localStorage.setItem("crm-plegadas", JSON.stringify(S.plegadas)); } catch (err) {}
        renderBoard();
      }
      if (a === "vista") {
        S.vista = act.getAttribute("data-v");
        try { localStorage.setItem("crm-vista", S.vista); } catch (err) {}
        renderContacts();
      }
      if (a === "settings") openSettings();
      if (a === "delete" && S.open && confirm("¿Eliminar este contacto y todo su historial? No se puede deshacer.")) {
        var id = S.open;
        api("delete", { id: id }).then(function () {
          S.leads = S.leads.filter(function (l) { return l.id !== id; });
          closeDrawer(true); render(); toast("Eliminado");
        }).catch(function (err) { toast(err.message, true); });
      }
      if (a === "lead-mail") {
        var l = leadById(S.open);
        S.mail.to = (l.nombre ? l.nombre + " " : "") + "<" + l.email + ">";
        S.mail.boletin = false;
        closeDrawer(true);
        location.hash = "correo";
        if (S.page === "correo") renderMail();
      }
      if (a === "mail-gmail" || a === "mail-app" || a === "mail-copy") {
        if (!S.mail.boletin && !mailTarget().email) { toast("Indica a quién va el correo", true); return; }
        if (a === "mail-copy") {
          navigator.clipboard.writeText(composeUrl("text")).then(function () { toast("Texto copiado"); }, function () { toast("No se pudo copiar", true); });
          return;
        }
        if (a === "mail-gmail") window.open(composeUrl("gmail"), "_blank", "noopener");
        else location.href = composeUrl("app");
        logMail();
      }
      if (a === "tpl-new") openTemplate(null);
      if (a === "tpl-edit") openTemplate(act.getAttribute("data-id"));
      if (a === "tpl-del" && confirm("¿Eliminar esta plantilla?")) {
        api("tpl_save", { id: $("#tpl-form [name=id]").value, borrar: true }).then(function (j) { S.tpls = j.plantillas; closeDrawer(true); renderMail(); toast("Plantilla eliminada"); })
          .catch(function (err) { toast(err.message, true); });
      }
      if (a === "cal-prev" || a === "cal-next") { S.month = new Date(S.month.getFullYear(), S.month.getMonth() + (a === "cal-next" ? 1 : -1), 1); renderCalendar(); }
      if (a === "cal-today") { S.month = null; S.day = today(); renderCalendar(); }
      if (a === "doc-del") {
        var li = act.closest("[data-doc]");
        if (confirm("¿Eliminar este documento? No se puede deshacer.")) {
          api("doc_update", { id: li.getAttribute("data-doc"), borrar: true }).then(function (j) {
            S.docs = j.docs; toast("Documento eliminado");
            if (S.page === "documentos") renderDocs();
            if (S.open && S.open.charAt(0) !== "_") renderLeadDocs(S.open);
          }).catch(function (err) { toast(err.message, true); });
        }
      }
      return;
    }
    var tpl = t.closest("[data-tpl]");
    if (tpl) {
      var tp = S.tpls.filter(function (x) { return x.id === tpl.getAttribute("data-tpl"); })[0];
      S.mail.tpl = tp.id; S.mail.asunto = tp.asunto; S.mail.cuerpo = tp.cuerpo;
      renderMail();
      return;
    }
    var seg = t.closest(".seg");
    if (seg) {
      $$(".seg").forEach(function (b) { b.classList.toggle("is-on", b === seg); });
      $("#lead-form [name=etapa]").value = seg.getAttribute("data-stage");
      S.dirty = true;
      return;
    }
    var day = t.closest("[data-day]");
    if (day) {
      S.day = day.getAttribute("data-day");
      if (S.day.slice(0, 7) !== ymd(S.month).slice(0, 7)) S.month = new Date(parseDay(S.day).getFullYear(), parseDay(S.day).getMonth(), 1);
      renderCalendar();
      return;
    }
    var row = t.closest(".card, tr[data-id], li[data-id]");
    if (row && !t.closest("a")) openLead(row.getAttribute("data-id"));
  });

  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && S.open !== null) closeDrawer();
    if (e.key === "Enter" && e.target.matches && e.target.matches(".card, tr[data-id], li[data-id]")) openLead(e.target.getAttribute("data-id"));
  });

  document.addEventListener("submit", function (e) {
    var f = e.target;
    if (f.id === "lead-form") { e.preventDefault(); submitLead(f); }
    if (f.classList.contains("set-form")) { e.preventDefault(); submitSettings(f); }
    if (f.id === "tpl-form") {
      e.preventDefault();
      var data = {};
      $$("[name]", f).forEach(function (x) { data[x.name] = x.value; });
      api("tpl_save", data).then(function (j) { S.tpls = j.plantillas; S.dirty = false; closeDrawer(true); renderMail(); toast("Plantilla guardada"); })
        .catch(function (err) { toast(err.message, true); });
    }
  });

  document.addEventListener("input", function (e) {
    var t = e.target;
    if (t.closest(".drawer") && t.type !== "file") S.dirty = true;
    if (t.id === "q" || t.id === "q-docs") {
      S.q = t.value;
      if (t.id === "q") refreshResults();
      else { var pos = t.selectionStart; renderDocs(); var n = $("#q-docs"); n.focus(); try { n.setSelectionRange(pos, pos); } catch (err) {} }
    }
    if (t.id === "m-to") S.mail.to = t.value;
    if (t.id === "m-asunto") S.mail.asunto = t.value;
    if (t.id === "m-cuerpo") S.mail.cuerpo = t.value;
  });

  document.addEventListener("change", function (e) {
    var t = e.target;
    if (t.id === "f-origen") { S.origen = t.value; refreshResults(); }
    if (t.id === "f-etapa") { S.etapa = t.value; refreshResults(); }
    if (t.id === "f-hoy") { S.hoy = t.checked; refreshResults(); }
    if (t.id === "m-bol") { S.mail.boletin = t.checked; renderMail(); }
    if (t.id === "doc-file") uploadFiles(t.files, "");
    if (t.id === "lead-file") uploadFiles(t.files, S.open);
    if (t.classList.contains("doc-lead")) {
      var id = t.closest("[data-doc]").getAttribute("data-doc");
      api("doc_update", { id: id, lead: t.value }).then(function (j) { S.docs = j.docs; toast("Documento vinculado"); renderDocs(); })
        .catch(function (err) { toast(err.message, true); });
    }
  });

  // Arrastrar: tarjetas entre etapas (Ventas) y archivos a Documentos.
  var dragId = null;
  document.addEventListener("dragstart", function (e) {
    var c = e.target.closest && e.target.closest(".card");
    if (!c) return;
    dragId = c.getAttribute("data-id");
    c.classList.add("dragging");
    e.dataTransfer.effectAllowed = "move";
    try { e.dataTransfer.setData("text/plain", dragId); } catch (err) {}
  });
  document.addEventListener("dragend", function () {
    dragId = null;
    $$(".dragging, .drop").forEach(function (el) { el.classList.remove("dragging", "drop"); });
  });
  document.addEventListener("dragover", function (e) {
    var zone = e.target.closest && e.target.closest("#dropzone");
    if (zone && !dragId) { e.preventDefault(); zone.classList.add("drop"); return; }
    var col = dragId && e.target.closest && e.target.closest(".col");
    if (!col) return;
    e.preventDefault();
    $$(".col.drop").forEach(function (c) { if (c !== col) c.classList.remove("drop"); });
    col.classList.add("drop");
  });
  document.addEventListener("dragleave", function (e) {
    var zone = e.target.closest && e.target.closest("#dropzone");
    if (zone && !zone.contains(e.relatedTarget)) zone.classList.remove("drop");
  });
  document.addEventListener("drop", function (e) {
    var zone = e.target.closest && e.target.closest("#dropzone");
    if (zone && !dragId) { e.preventDefault(); zone.classList.remove("drop"); uploadFiles(e.dataTransfer.files, ""); return; }
    var col = dragId && e.target.closest && e.target.closest(".col");
    if (!col) return;
    e.preventDefault();
    var stage = col.getAttribute("data-stage");
    var l = leadById(dragId);
    if (!l || l.etapa === stage) return;
    var prev = l.etapa;
    l.etapa = stage;
    renderBoard();
    saveLead(l.id, { etapa: stage }, true).then(function () { toast("Movido a " + S.stages[stage]); })
      .catch(function (err) { l.etapa = prev; renderBoard(); toast(err.message, true); });
  });

  load().then(function () { S.ready = true; go(location.hash.slice(1) || "inicio"); });
  // Cada minuto mira si han entrado contactos nuevos (no molesta si tienes una ficha abierta).
  setInterval(function () { if (!document.hidden && S.open === null) load(true); }, 60000);
})();
