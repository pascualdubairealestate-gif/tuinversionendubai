/* ==========================================================================
   Pascual Vidal · Tu inversión en Dubái — main.js
   Patrón IIFE, sin módulos. Cada init va envuelto en safe().
   ========================================================================== */

/* -------------------------------------------------------------------------
   CONFIGURACIÓN — edita solo este bloque
   ------------------------------------------------------------------------- */
window.__PV__ = {
  // Número de WhatsApp en formato internacional, sin "+" ni espacios (ej. 971501234567)
  whatsapp: "971500000000",

  // URL del webhook / endpoint de tu CRM. Vacío = los leads se guardan solo en el navegador (pruebas).
  // Recibe un POST con JSON: { formulario, email, nombre, telefono, ..., pagina, utm_*, fecha }
  crmEndpoint: "",
  // "cors" para CRMs que aceptan JSON con CORS; "no-cors" para webhooks tipo Zapier/Make/n8n.
  crmMode: "no-cors",

  // Enlace directo al PDF de la guía (se abre tras dejar el correo). Vacío = solo mensaje de confirmación.
  guideUrl: "",
  // Segundos hasta que aparece el popup de la guía
  guideDelay: 7,

  // Canal de YouTube
  youtubeChannel: "https://www.youtube.com/",
  // IDs de tus vídeos, en el mismo orden que las tarjetas (lo que va tras "v=" en la URL)
  youtube: ["", "", ""]
};

(function () {
  "use strict";
  var CFG = window.__PV__;
  var doc = document.documentElement;
  doc.classList.remove("no-js");

  function safe(fn, name) {
    try { fn(); } catch (e) { if (window.console) console.warn("[init " + name + "]", e); }
  }
  function $(s, r) { return (r || document).querySelector(s); }
  function $$(s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); }
  function track(event, data) {
    window.dataLayer = window.dataLayer || [];
    var o = { event: event };
    for (var k in data) o[k] = data[k];
    window.dataLayer.push(o);
  }
  var canHover = window.matchMedia("(hover: hover) and (pointer: fine)").matches;

  /* ---------- Toast ---------- */
  var toastTimer;
  function toast(msg) {
    var t = $("[data-toast]");
    if (!t) return;
    t.textContent = msg;
    t.classList.add("is-on");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { t.classList.remove("is-on"); }, 3200);
  }

  /* ---------- Splash ---------- */
  function initSplash() {
    var s = $("[data-splash]");
    if (!s) return;
    var hide = function () { s.classList.add("is-out"); };
    if (document.readyState === "complete") setTimeout(hide, 500);
    else window.addEventListener("load", function () { setTimeout(hide, 300); });
    setTimeout(hide, 2500);
  }

  /* ---------- Navegación ---------- */
  function initNav() {
    var nav = $("[data-nav]"), burger = $("[data-burger]"), wa = $(".wa-float");
    var onScroll = function () {
      var y = window.scrollY;
      nav.classList.toggle("is-scrolled", y > 40);
      if (wa && y > 300) wa.classList.add("is-visible");
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();
    setTimeout(function () { if (wa) wa.classList.add("is-visible"); }, 3000);

    burger.addEventListener("click", function () {
      var open = nav.classList.toggle("is-open");
      burger.setAttribute("aria-expanded", open ? "true" : "false");
      document.body.style.overflow = open ? "hidden" : "";
    });
    $$("[data-menu] a").forEach(function (a) {
      a.addEventListener("click", function () {
        nav.classList.remove("is-open");
        burger.setAttribute("aria-expanded", "false");
        document.body.style.overflow = "";
      });
    });
  }

  /* ---------- WhatsApp ---------- */
  function initWhatsApp() {
    $$("[data-wa]").forEach(function (a) {
      var msg = a.getAttribute("data-wa-msg") || "Hola Pascual";
      a.href = "https://wa.me/" + CFG.whatsapp + "?text=" + encodeURIComponent(msg);
      a.addEventListener("click", function () { track("whatsapp_click", { ubicacion: a.className }); });
    });
    $$("[data-youtube-channel]").forEach(function (a) { a.href = CFG.youtubeChannel; });
  }

  /* ---------- Reveal on scroll (umbral bajo + red de seguridad) ---------- */
  function initReveal() {
    var els = $$(".reveal");
    // Escalonado suave dentro de cada grupo
    $$(".services-grid, .videos-grid, .hero-copy, .problem").forEach(function (g) {
      $$(".reveal", g).forEach(function (el, i) { el.style.setProperty("--d", (i * 0.08) + "s"); });
    });
    if (!("IntersectionObserver" in window)) {
      els.forEach(function (el) { el.classList.add("is-visible"); });
      return;
    }
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) { e.target.classList.add("is-visible"); io.unobserve(e.target); }
      });
    }, { threshold: 0.01, rootMargin: "0px 0px -4% 0px" });
    els.forEach(function (el) { io.observe(el); });
    setTimeout(function () {
      $$(".reveal:not(.is-visible)").forEach(function (el) {
        if (el.getBoundingClientRect().top < window.innerHeight) el.classList.add("is-visible");
      });
    }, 6000);
  }

  /* ---------- Contadores ---------- */
  function initCount() {
    var els = $$("[data-count]");
    if (!els.length || !("IntersectionObserver" in window)) return;
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (!e.isIntersecting) return;
        io.unobserve(e.target);
        var el = e.target, to = parseFloat(el.getAttribute("data-count")), suf = el.getAttribute("data-suffix") || "", pre = el.getAttribute("data-prefix") || "";
        if (!to) return;
        var t0 = performance.now(), dur = 1400;
        (function tick(now) {
          var p = Math.min(1, (now - t0) / dur), v = Math.round(to * (1 - Math.pow(1 - p, 3)));
          el.textContent = pre + v + suf;
          if (p < 1) requestAnimationFrame(tick);
        })(t0);
      });
    }, { threshold: 0.01 });
    els.forEach(function (el) { io.observe(el); });
  }

  /* ---------- Hero: luz que sigue al ratón + parallax de la foto ---------- */
  function initHero() {
    var hero = $("[data-hero]");
    if (!hero) return;
    if (canHover) {
      var raf = 0, mx = 70, my = 40;
      hero.addEventListener("mousemove", function (e) {
        var r = hero.getBoundingClientRect();
        mx = ((e.clientX - r.left) / r.width) * 100;
        my = ((e.clientY - r.top) / r.height) * 100;
        if (!raf) raf = requestAnimationFrame(function () {
          hero.style.setProperty("--mx", mx + "%");
          hero.style.setProperty("--my", my + "%");
          raf = 0;
        });
      });
    }
    var par = $$("[data-parallax]");
    var ticking = false;
    var update = function () {
      par.forEach(function (el) {
        var r = el.getBoundingClientRect();
        if (r.bottom < 0 || r.top > window.innerHeight) return;
        var k = parseFloat(el.getAttribute("data-parallax")) || 0.05;
        var img = el.querySelector("img");
        if (img) img.style.setProperty("--py", (-(r.top) * k).toFixed(1) + "px");
      });
      ticking = false;
    };
    window.addEventListener("scroll", function () {
      if (!ticking) { ticking = true; requestAnimationFrame(update); }
    }, { passive: true });
  }

  /* ---------- Botones magnéticos (sutil) ---------- */
  function initMagnetic() {
    if (!canHover) return;
    $$("[data-magnetic]").forEach(function (b) {
      b.addEventListener("mousemove", function (e) {
        var r = b.getBoundingClientRect();
        var x = (e.clientX - r.left - r.width / 2) * 0.18, y = (e.clientY - r.top - r.height / 2) * 0.25;
        b.style.transform = "translate(" + x + "px," + y + "px)";
      });
      b.addEventListener("mouseout", function (e) {
        if (!b.contains(e.relatedTarget)) b.style.transform = "";
      });
    });
  }

  /* ---------- Tilt 3D ligero ---------- */
  function initTilt() {
    if (!canHover) return;
    $$("[data-tilt]").forEach(function (c) {
      if (c.dataset.tiltBound) return;
      c.dataset.tiltBound = "1";
      c.addEventListener("mousemove", function (e) {
        var r = c.getBoundingClientRect();
        var px = (e.clientX - r.left) / r.width - 0.5, py = (e.clientY - r.top) / r.height - 0.5;
        c.style.transform = "perspective(900px) rotateX(" + (-py * 5) + "deg) rotateY(" + (px * 6) + "deg) translateY(-4px)";
      });
      c.addEventListener("mouseout", function (e) {
        if (!c.contains(e.relatedTarget)) c.style.transform = "";
      });
    });
  }

  /* ---------- Slider de proyectos ---------- */
  function initSlider() {
    var root = $("[data-slider]"), trackEl = $("[data-slider-track]");
    if (!root || !trackEl) return;
    var cards = $$(".project", trackEl);
    var n = cards.length;
    var cur = $("[data-slider-current]"), tot = $("[data-slider-total]"), bar = $("[data-slider-bar]");
    var prev = $("[data-slider-prev]"), next = $("[data-slider-next]");
    if (tot) tot.textContent = String(n).padStart(2, "0");
    if (bar) bar.style.width = (100 / n) + "%";

    // Espaciador final para que la última tarjeta también pueda alinearse al inicio
    var spacer = document.createElement("div");
    spacer.setAttribute("aria-hidden", "true");
    spacer.style.flex = "0 0 1px";
    trackEl.appendChild(spacer);
    function padStart() { return parseFloat(getComputedStyle(trackEl).paddingLeft) || 0; }
    function sizeSpacer() {
      var w = trackEl.clientWidth - cards[0].offsetWidth - padStart() * 2;
      spacer.style.flexBasis = Math.max(1, w) + "px";
    }

    var active = -1;
    function setActive(i) {
      if (i === active) return;
      active = i;
      cards.forEach(function (c, k) { c.classList.toggle("is-active", k === i); });
      if (cur) cur.textContent = String(i + 1).padStart(2, "0");
      if (bar) bar.style.width = ((i + 1) / n * 100) + "%";
      if (prev) prev.disabled = i === 0;
      if (next) next.disabled = i === n - 1;
    }
    function update() {
      var tr = trackEl.getBoundingClientRect();
      var anchor = tr.left + padStart();
      var best = 0, bestD = Infinity;
      cards.forEach(function (c, k) {
        var r = c.getBoundingClientRect();
        var d = r.left - anchor;
        if (Math.abs(d) < bestD) { bestD = Math.abs(d); best = k; }
        // Parallax interno de la imagen
        var img = c.querySelector(".project-media img");
        if (img) img.style.setProperty("--px", Math.max(-60, Math.min(60, -d * 0.08)).toFixed(1) + "px");
      });
      setActive(best);
    }
    var ticking = false;
    trackEl.addEventListener("scroll", function () {
      if (!ticking) { ticking = true; requestAnimationFrame(function () { update(); ticking = false; }); }
    }, { passive: true });

    function goTo(i) {
      i = Math.max(0, Math.min(n - 1, i));
      trackEl.scrollTo({ left: cards[i].offsetLeft - padStart(), behavior: "smooth" });
    }
    if (prev) prev.addEventListener("click", function () { goTo(active - 1); });
    if (next) next.addEventListener("click", function () { goTo(active + 1); });
    cards.forEach(function (c, k) {
      c.addEventListener("click", function (e) {
        if (k !== active && !e.target.closest("button")) goTo(k);
      });
    });
    trackEl.setAttribute("tabindex", "0");
    trackEl.addEventListener("keydown", function (e) {
      if (e.key === "ArrowRight") { e.preventDefault(); goTo(active + 1); }
      if (e.key === "ArrowLeft") { e.preventDefault(); goTo(active - 1); }
    });

    // Arrastrar con el ratón (en táctil, el desplazamiento es nativo)
    var down = false, startX = 0, startL = 0, moved = 0, startActive = 0;
    trackEl.addEventListener("pointerdown", function (e) {
      if (e.pointerType !== "mouse" || e.button !== 0) return;
      down = true; moved = 0; startX = e.clientX; startL = trackEl.scrollLeft; startActive = active;
    });
    window.addEventListener("pointermove", function (e) {
      if (!down) return;
      var dx = e.clientX - startX;
      moved = Math.max(moved, Math.abs(dx));
      if (moved > 5) trackEl.classList.add("is-dragging");
      trackEl.scrollLeft = startL - dx;
    });
    window.addEventListener("pointerup", function (e) {
      if (!down) return;
      down = false;
      if (!trackEl.classList.contains("is-dragging")) return;
      var dx = e.clientX - startX;
      trackEl.classList.remove("is-dragging");
      // Snap con inercia: si el gesto es claro, avanza una tarjeta
      var target = active;
      if (Math.abs(dx) > 60 && active === startActive) target = active + (dx < 0 ? 1 : -1);
      goTo(target);
    });
    trackEl.addEventListener("click", function (e) {
      if (moved > 5) { e.preventDefault(); e.stopPropagation(); moved = 0; }
    }, true);

    sizeSpacer();
    window.addEventListener("resize", function () { sizeSpacer(); update(); });
    update();
  }

  /* ---------- Reseñas: duplicar para bucle infinito ---------- */
  function initReviews() {
    var t = $("[data-reviews] .reviews-track");
    if (!t || t.dataset.cloned) return;
    t.dataset.cloned = "1";
    $$(".review", t).forEach(function (r) {
      var c = r.cloneNode(true);
      c.setAttribute("aria-hidden", "true");
      t.appendChild(c);
    });
  }

  /* ---------- Modales ---------- */
  var lastFocus = null;
  function openModal(name) {
    var m = $('[data-modal="' + name + '"]');
    if (!m) return;
    $$(".modal").forEach(function (x) { if (x !== m) x.hidden = true; });
    lastFocus = document.activeElement;
    m.hidden = false;
    document.body.style.overflow = "hidden";
    var f = m.querySelector("input:not([type=hidden]), button");
    if (f && name !== "video") setTimeout(function () { f.focus({ preventScroll: true }); }, 250);
    track("modal_open", { modal: name });
  }
  function closeModal(m) {
    m.hidden = true;
    document.body.style.overflow = "";
    if (m.dataset.modal === "video") { var s = $("[data-video-slot]"); if (s) s.innerHTML = ""; }
    if (m.dataset.modal === "guide") { try { sessionStorage.setItem("pv_guide_seen", "1"); } catch (e) {} }
    if (lastFocus && lastFocus.focus) lastFocus.focus({ preventScroll: true });
  }
  function initModals() {
    $$(".modal").forEach(function (m) {
      $$("[data-close]", m).forEach(function (b) { b.addEventListener("click", function () { closeModal(m); }); });
    });
    document.addEventListener("keydown", function (e) {
      if (e.key !== "Escape") return;
      $$(".modal").forEach(function (m) { if (!m.hidden) closeModal(m); });
    });
    $$("[data-open-guide]").forEach(function (b) { b.addEventListener("click", function () { openModal("guide"); }); });
    $$("[data-open-lead]").forEach(function (b) {
      b.addEventListener("click", function () {
        var p = b.getAttribute("data-open-lead");
        var m = $('[data-modal="lead"]');
        $("[data-lead-project]", m).textContent = p;
        $('input[name="proyecto"]', m).value = p;
        openModal("lead");
      });
    });
  }

  /* ---------- Popup de la guía a los 7 segundos ---------- */
  function initGuidePopup() {
    var seen = false;
    try { seen = sessionStorage.getItem("pv_guide_seen") || localStorage.getItem("pv_guide_done"); } catch (e) {}
    if (seen) return;
    setTimeout(function () {
      var anyOpen = $$(".modal").some(function (m) { return !m.hidden; });
      if (anyOpen) return;
      openModal("guide");
      try { sessionStorage.setItem("pv_guide_seen", "1"); } catch (e) {}
    }, (CFG.guideDelay || 7) * 1000);
  }

  /* ---------- Vídeos de YouTube (carga ligera) ---------- */
  function initVideos() {
    $$("[data-yt]").forEach(function (v, i) {
      var id = v.getAttribute("data-yt") || CFG.youtube[i] || "";
      v.setAttribute("data-yt", id);
      if (id) {
        var img = v.querySelector(".video-thumb img");
        if (img) {
          var hq = "https://i.ytimg.com/vi/" + id + "/hqdefault.jpg";
          var test = new Image();
          test.onload = function () { if (test.naturalWidth > 120) img.src = hq; };
          test.src = hq;
        }
      }
      v.addEventListener("click", function () {
        var vid = v.getAttribute("data-yt");
        track("video_click", { video: vid || "sin_id", posicion: i + 1 });
        if (!vid) {
          if (CFG.youtubeChannel && CFG.youtubeChannel !== "https://www.youtube.com/") window.open(CFG.youtubeChannel, "_blank", "noopener");
          else toast("Vídeo disponible muy pronto en el canal.");
          return;
        }
        var slot = $("[data-video-slot]");
        slot.innerHTML = '<iframe src="https://www.youtube-nocookie.com/embed/' + encodeURIComponent(vid) +
          '?autoplay=1&rel=0&modestbranding=1" title="Vídeo de Pascual Vidal" allow="autoplay; encrypted-media; picture-in-picture" allowfullscreen></iframe>';
        openModal("video");
      });
    });
  }

  /* ---------- Formularios → CRM ---------- */
  function getUTM() {
    var out = {};
    try {
      var stored = JSON.parse(sessionStorage.getItem("pv_utm") || "{}");
      var q = new URLSearchParams(location.search);
      ["utm_source", "utm_medium", "utm_campaign", "utm_content", "utm_term", "gclid", "fbclid"].forEach(function (k) {
        if (q.get(k)) stored[k] = q.get(k);
      });
      sessionStorage.setItem("pv_utm", JSON.stringify(stored));
      out = stored;
    } catch (e) {}
    return out;
  }
  function sendLead(payload) {
    try {
      var q = JSON.parse(localStorage.getItem("pv_leads") || "[]");
      q.push(payload);
      localStorage.setItem("pv_leads", JSON.stringify(q.slice(-30)));
    } catch (e) {}
    track("lead_submit", { formulario: payload.formulario });
    if (!CFG.crmEndpoint) return Promise.resolve();
    var opts = { method: "POST", body: JSON.stringify(payload), mode: CFG.crmMode || "cors" };
    opts.headers = { "Content-Type": CFG.crmMode === "no-cors" ? "text/plain;charset=UTF-8" : "application/json" };
    return fetch(CFG.crmEndpoint, opts);
  }
  var EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;
  function initForms() {
    var utm = getUTM();
    $$("[data-lead-form]").forEach(function (form) {
      if (form.dataset.bound) return;
      form.dataset.bound = "1";
      form.addEventListener("submit", function (e) {
        e.preventDefault();
        var msg = form.querySelector(".form-msg");
        var ok = true;
        $$("input, select, textarea", form).forEach(function (f) {
          var bad = false;
          if (f.required) {
            if (f.type === "checkbox") bad = !f.checked;
            else bad = !f.value.trim();
          }
          if (!bad && f.type === "email" && f.value) bad = !EMAIL_RE.test(f.value.trim());
          if (!bad && f.type === "tel" && f.value) bad = f.value.replace(/\D/g, "").length < 7;
          var target = f.type === "checkbox" ? f.closest(".consent") : f;
          if (target) target.classList.toggle("is-invalid", bad);
          if (bad) ok = false;
        });
        if (!ok) {
          if (msg) { msg.className = "form-msg err"; msg.textContent = "Revisa los campos marcados."; }
          return;
        }
        var type = form.getAttribute("data-lead-form");
        var payload = { formulario: type, pagina: location.href, fecha: new Date().toISOString() };
        $$("input, select, textarea", form).forEach(function (f) {
          if (!f.name) return;
          payload[f.name] = f.type === "checkbox" ? f.checked : f.value.trim();
        });
        for (var k in utm) payload[k] = utm[k];

        var btn = form.querySelector("button[type=submit]");
        var label = btn ? btn.innerHTML : "";
        if (btn) { btn.disabled = true; btn.textContent = "Enviando…"; }

        var done = function () {
          if (btn) { btn.disabled = false; btn.innerHTML = label; }
          var texts = {
            guia: "¡Hecho! Revisa tu correo: la guía va de camino.",
            newsletter: "¡Bienvenido! Recibirás el primer boletín el lunes.",
            consultoria: "Gracias. Te escribo en menos de 24 h para agendar la llamada.",
            dossier: "Perfecto. Te envío el dossier por email y WhatsApp."
          };
          if (msg) { msg.className = "form-msg ok"; msg.textContent = texts[type] || "¡Enviado!"; }
          form.reset();
          if (type === "guia") {
            try { localStorage.setItem("pv_guide_done", "1"); } catch (err) {}
            if (CFG.guideUrl) window.open(CFG.guideUrl, "_blank", "noopener");
            setTimeout(function () { var m = form.closest(".modal"); if (m && !m.hidden) closeModal(m); toast(texts.guia); }, 1800);
          }
          if (type === "dossier") {
            setTimeout(function () { var m = form.closest(".modal"); if (m && !m.hidden) closeModal(m); toast(texts.dossier); }, 1800);
          }
        };
        var fail = function () {
          if (btn) { btn.disabled = false; btn.innerHTML = label; }
          if (msg) { msg.className = "form-msg err"; msg.textContent = "No se pudo enviar. Escríbeme por WhatsApp, por favor."; }
        };
        sendLead(payload).then(done, fail);
      });
      $$("input, select, textarea", form).forEach(function (f) {
        f.addEventListener("input", function () {
          var target = f.type === "checkbox" ? f.closest(".consent") : f;
          if (target) target.classList.remove("is-invalid");
        });
      });
    });
  }

  function initYear() {
    $$("[data-year]").forEach(function (y) { y.textContent = new Date().getFullYear(); });
  }

  function boot() {
    safe(initSplash, "splash");
    safe(initNav, "nav");
    safe(initWhatsApp, "whatsapp");
    safe(initReveal, "reveal");
    safe(initCount, "count");
    safe(initHero, "hero");
    safe(initMagnetic, "magnetic");
    safe(initTilt, "tilt");
    safe(initSlider, "slider");
    safe(initReviews, "reviews");
    safe(initModals, "modals");
    safe(initVideos, "videos");
    safe(initForms, "forms");
    safe(initGuidePopup, "guide");
    safe(initYear, "year");
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();
})();
