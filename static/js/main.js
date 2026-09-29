/* Inicia Legal · comportamiento del sitio */
(function () {
  "use strict";

  // Navbar sombreada al hacer scroll + botón volver arriba
  var nav = document.querySelector(".navbar-il");
  var toTop = document.querySelector(".back-to-top");
  function onScroll() {
    var y = window.scrollY || document.documentElement.scrollTop;
    if (nav) nav.classList.toggle("scrolled", y > 30);
    if (toTop) toTop.classList.toggle("show", y > 500);
  }
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();
  if (toTop) {
    toTop.addEventListener("click", function () {
      window.scrollTo({ top: 0, behavior: "smooth" });
    });
  }

  // Animaciones de aparición (solo si hay JS y IntersectionObserver)
  var reveals = document.querySelectorAll(".reveal");
  if ("IntersectionObserver" in window && reveals.length) {
    document.documentElement.classList.add("js");
    var io = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (e) {
          if (e.isIntersecting) {
            e.target.classList.add("visible");
            io.unobserve(e.target);
          }
        });
      },
      { threshold: 0.12 }
    );
    reveals.forEach(function (el) { io.observe(el); });
  } else {
    reveals.forEach(function (el) { el.classList.add("visible"); });
  }

  // Cerrar menú móvil al hacer clic en un enlace
  var collapse = document.getElementById("mainNav");
  if (collapse && window.bootstrap) {
    collapse.querySelectorAll(".nav-link:not(.dropdown-toggle), .dropdown-item").forEach(function (link) {
      link.addEventListener("click", function () {
        var inst = bootstrap.Collapse.getInstance(collapse);
        if (inst && collapse.classList.contains("show")) inst.hide();
      });
    });
  }

  // Auto-cerrar alertas flash
  document.querySelectorAll(".flash-wrap .alert").forEach(function (el) {
    setTimeout(function () {
      if (window.bootstrap) bootstrap.Alert.getOrCreateInstance(el).close();
    }, 6000);
  });

  // Newsletter por AJAX
  document.querySelectorAll("form[data-newsletter]").forEach(function (form) {
    form.addEventListener("submit", function (ev) {
      ev.preventDefault();
      var btn = form.querySelector("button[type=submit]");
      var feedback = form.querySelector("[data-feedback]");
      var fd = new FormData(form);
      if (btn) btn.disabled = true;
      fetch(form.action, {
        method: "POST",
        body: fd,
        headers: { "X-Requested-With": "XMLHttpRequest" },
        credentials: "same-origin",
      })
        .then(function (r) { return r.json(); })
        .then(function (data) {
          if (feedback) {
            feedback.textContent = data.message;
            feedback.className = "small mt-2 " + (data.ok ? "text-success" : "text-warning");
          }
          if (data.ok) form.reset();
        })
        .catch(function () {
          if (feedback) { feedback.textContent = "Ocurrió un error, inténtalo nuevamente."; feedback.className = "small mt-2 text-warning"; }
        })
        .finally(function () { if (btn) btn.disabled = false; });
    });
  });

  // Responder comentario: rellena parent y hace scroll al formulario
  document.querySelectorAll("[data-reply]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var form = document.getElementById("commentForm");
      if (!form) return;
      form.querySelector("input[name=parent]").value = btn.getAttribute("data-reply");
      var note = form.querySelector("[data-reply-note]");
      if (note) {
        note.classList.remove("d-none");
        note.querySelector("span").textContent = btn.getAttribute("data-reply-name");
      }
      form.scrollIntoView({ behavior: "smooth", block: "center" });
      form.querySelector("textarea").focus();
    });
  });
  var cancelReply = document.querySelector("[data-cancel-reply]");
  if (cancelReply) {
    cancelReply.addEventListener("click", function () {
      var form = document.getElementById("commentForm");
      form.querySelector("input[name=parent]").value = "";
      form.querySelector("[data-reply-note]").classList.add("d-none");
    });
  }

  // Cifras destacadas: conteo animado al entrar en pantalla
  var statValues = document.querySelectorAll(".stat-item .value[data-count]");
  function runCount(el) {
    var raw = el.getAttribute("data-count");
    var m = raw.match(/(\d+(?:[.,]\d+)?)/);
    if (!m) return;
    var target = parseFloat(m[1].replace(",", "."));
    var prefix = raw.slice(0, m.index);
    var suffix = raw.slice(m.index + m[1].length);
    var decimals = (m[1].split(/[.,]/)[1] || "").length;
    var t0 = null;
    var duration = 1400;
    function step(ts) {
      if (t0 === null) t0 = ts;
      var p = Math.min((ts - t0) / duration, 1);
      var eased = 1 - Math.pow(1 - p, 3); // ease-out cúbico
      var current = target * eased;
      el.textContent = prefix + (decimals ? current.toFixed(decimals) : Math.round(current)) + suffix;
      if (p < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
  }
  if (statValues.length) {
    if ("IntersectionObserver" in window && !window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      var so = new IntersectionObserver(function (entries) {
        entries.forEach(function (e) {
          if (e.isIntersecting) {
            e.target.classList.add("in-view");
            runCount(e.target.querySelector(".value"));
            so.unobserve(e.target);
          }
        });
      }, { threshold: 0.5 });
      statValues.forEach(function (v) { so.observe(v.closest(".stat-item")); });
    } else {
      statValues.forEach(function (v) { v.closest(".stat-item").classList.add("in-view"); });
    }
  }

  // Acordeón de imágenes (áreas): se expande al pasar el cursor; en táctil, el primer toque expande y el segundo navega
  document.querySelectorAll("[data-area-accordion]").forEach(function (acc) {
    var items = Array.prototype.slice.call(acc.querySelectorAll(".area-acc-item"));
    function activate(el) {
      items.forEach(function (i) { i.classList.toggle("is-active", i === el); });
    }
    items.forEach(function (el) {
      el.addEventListener("pointerenter", function (e) {
        if (e.pointerType === "mouse") activate(el);
      });
      el.addEventListener("focus", function () { activate(el); });
      el.addEventListener("click", function (e) {
        var coarse = window.matchMedia("(hover: none)").matches;
        if (coarse && !el.classList.contains("is-active")) {
          e.preventDefault();
          activate(el);
        }
      });
    });
  });

  // Carrusel del hero: principal, banners y plan
  var hero = document.querySelector("[data-hero-slider]");
  if (hero) {
    var heroSlides = Array.prototype.slice.call(hero.querySelectorAll(".hero-slide"));
    var heroDots = Array.prototype.slice.call(hero.querySelectorAll("[data-hero-dot]"));
    var heroIndex = 0;
    var heroTimer = null;
    function showHero(next) {
      if (!heroSlides.length || next === heroIndex) return;
      var current = heroSlides[heroIndex];
      current.classList.remove("is-active");
      current.classList.add("is-leaving");
      current.setAttribute("aria-hidden", "true");
      if (heroDots[heroIndex]) { heroDots[heroIndex].classList.remove("is-active"); heroDots[heroIndex].removeAttribute("aria-selected"); }
      heroIndex = (next + heroSlides.length) % heroSlides.length;
      var incoming = heroSlides[heroIndex];
      incoming.classList.add("is-active");
      incoming.setAttribute("aria-hidden", "false");
      if (heroDots[heroIndex]) { heroDots[heroIndex].classList.add("is-active"); heroDots[heroIndex].setAttribute("aria-selected", "true"); }
      window.setTimeout(function () { current.classList.remove("is-leaving"); }, 700);
    }
    function startHero() {
      stopHero();
      if (heroSlides.length < 2 || window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
      heroTimer = window.setInterval(function () { showHero(heroIndex + 1); }, 6000);
    }
    function stopHero() { if (heroTimer) { window.clearInterval(heroTimer); heroTimer = null; } }
    heroDots.forEach(function (dot, n) {
      dot.addEventListener("click", function () { showHero(n); startHero(); });
    });
    hero.addEventListener("mouseenter", stopHero);
    hero.addEventListener("mouseleave", startHero);
    hero.addEventListener("focusin", stopHero);
    hero.addEventListener("focusout", function (e) { if (!hero.contains(e.relatedTarget)) startHero(); });
    startHero();
  }

  // Planes del inicio: una tarjeta a la vez, con flechas y deslizamiento
  document.querySelectorAll("[data-plan-switch]").forEach(function (root) {
    var track = root.querySelector(".plan-switch-track");
    var slides = Array.prototype.slice.call(root.querySelectorAll(".plan-switch-slide"));
    var dots = Array.prototype.slice.call(root.querySelectorAll("[data-plan-dot]"));
    var index = 0;
    var startX = 0;
    var dragging = false;
    var desktop = window.matchMedia("(min-width: 992px)");
    if (slides.length < 2) return;
    function show(next) {
      if (desktop.matches) return;
      index = (next + slides.length) % slides.length;
      track.style.transform = "translateX(" + (-index * 100) + "%)";
      slides.forEach(function (slide, n) {
        slide.setAttribute("aria-hidden", n === index ? "false" : "true");
      });
      dots.forEach(function (dot, n) {
        dot.classList.toggle("is-active", n === index);
        if (n === index) dot.setAttribute("aria-selected", "true");
        else dot.removeAttribute("aria-selected");
      });
    }
    var prev = root.querySelector("[data-plan-prev]");
    var next = root.querySelector("[data-plan-next]");
    if (prev) prev.addEventListener("click", function () { show(index - 1); });
    if (next) next.addEventListener("click", function () { show(index + 1); });
    dots.forEach(function (dot, n) {
      dot.addEventListener("click", function () { show(n); });
    });
    root.addEventListener("pointerdown", function (e) {
      if (e.target.closest("a, button")) return;
      dragging = true;
      startX = e.clientX;
    });
    root.addEventListener("pointerup", function (e) {
      if (!dragging) return;
      dragging = false;
      var delta = e.clientX - startX;
      if (delta > 40) show(index - 1);
      else if (delta < -40) show(index + 1);
    });
    root.addEventListener("pointercancel", function () { dragging = false; });
    function layout() {
      if (!desktop.matches) return;
      track.style.transform = "";
      slides.forEach(function (slide) { slide.removeAttribute("aria-hidden"); });
    }
    if (desktop.addEventListener) desktop.addEventListener("change", function () { layout(); if (!desktop.matches) show(index); });
    layout();
  });

  // Consentimiento de cookies (Ley N.° 21.719): nada de analítica hasta que el usuario acepte
  var CONSENT_KEY = "il_consent_v1";
  var CONSENT_DAYS = 180;
  var cfg = window.IL || {};

  function consentFromCookie() {
    var match = document.cookie.match(new RegExp("(?:^|; )" + CONSENT_KEY + "=([^;]*)"));
    if (!match) return null;
    var flags = decodeURIComponent(match[1]);
    return { necessary: true, analytics: flags.indexOf("a") !== -1, marketing: flags.indexOf("m") !== -1, ts: Date.now() };
  }
  function readConsent() {
    try {
      var raw = localStorage.getItem(CONSENT_KEY);
      if (raw) {
        var data = JSON.parse(raw);
        if (data && data.ts && Date.now() - data.ts <= CONSENT_DAYS * 864e5) return data;
      }
    } catch (e) {}
    return consentFromCookie();
  }
  function writeConsent(data) {
    data.ts = Date.now();
    try { localStorage.setItem(CONSENT_KEY, JSON.stringify(data)); } catch (e) {}
    document.cookie = CONSENT_KEY + "=" + (data.analytics ? "a" : "") + (data.marketing ? "m" : "") + "n; Max-Age=" + CONSENT_DAYS * 86400 + "; Path=/; SameSite=Lax" + (location.protocol === "https:" ? "; Secure" : "");
  }
  var gaLoaded = false;
  function loadAnalytics() {
    if (gaLoaded || !cfg.gaId) return;
    gaLoaded = true;
    window.dataLayer = window.dataLayer || [];
    window.gtag = window.gtag || function () { dataLayer.push(arguments); };
    gtag("consent", "default", { ad_storage: "denied", ad_user_data: "denied", ad_personalization: "denied", analytics_storage: "granted" });
    gtag("js", new Date());
    gtag("config", cfg.gaId, { anonymize_ip: true });
    var s = document.createElement("script");
    s.async = true;
    s.src = "https://www.googletagmanager.com/gtag/js?id=" + encodeURIComponent(cfg.gaId);
    document.head.appendChild(s);
  }
  function applyConsent(data) {
    if (data && data.analytics) loadAnalytics();
    document.dispatchEvent(new CustomEvent("il:consent", { detail: data }));
  }

  var consentBox = document.getElementById("cookieConsent");
  if (consentBox) {
    var views = consentBox.querySelectorAll("[data-cookie-view]");
    var switches = consentBox.querySelectorAll("[data-cookie-cat]");
    function showView(name) {
      views.forEach(function (v) { v.hidden = v.getAttribute("data-cookie-view") !== name; });
    }
    function openConsent(view) {
      var current = readConsent() || {};
      switches.forEach(function (sw) { sw.checked = !!current[sw.getAttribute("data-cookie-cat")]; });
      showView(view || "main");
      consentBox.hidden = false;
      document.body.classList.add("cookie-open");
      var first = consentBox.querySelector("[data-cookie-view]:not([hidden]) .btn");
      if (first) first.focus({ preventScroll: true });
    }
    function closeConsent() {
      consentBox.hidden = true;
      document.body.classList.remove("cookie-open");
    }
    function decide(analytics, marketing) {
      var data = { necessary: true, analytics: !!analytics, marketing: !!marketing };
      writeConsent(data);
      applyConsent(data);
      closeConsent();
    }
    consentBox.querySelectorAll("[data-cookie-accept-all]").forEach(function (b) { b.addEventListener("click", function () { decide(true, true); }); });
    consentBox.querySelectorAll("[data-cookie-deny]").forEach(function (b) { b.addEventListener("click", function () { decide(false, false); }); });
    consentBox.querySelectorAll("[data-cookie-save]").forEach(function (b) {
      b.addEventListener("click", function () {
        var picked = {};
        switches.forEach(function (sw) { picked[sw.getAttribute("data-cookie-cat")] = sw.checked; });
        decide(picked.analytics, picked.marketing);
      });
    });
    consentBox.querySelectorAll("[data-cookie-prefs]").forEach(function (b) { b.addEventListener("click", function () { showView("prefs"); }); });
    consentBox.querySelectorAll("[data-cookie-back]").forEach(function (b) { b.addEventListener("click", function () { showView("main"); }); });
    // Cerrar sin elegir guarda «solo necesarias» una vez, para no repetir el aviso en cada página.
    // Si ya había una decisión, cerrar no la pisa. «Configurar cookies» del pie sigue pudiendo reabrirla.
    function dismissConsent() {
      if (readConsent()) closeConsent();
      else decide(false, false);
    }
    consentBox.querySelectorAll("[data-cookie-close]").forEach(function (b) { b.addEventListener("click", dismissConsent); });
    document.addEventListener("keydown", function (e) { if (e.key === "Escape" && !consentBox.hidden) dismissConsent(); });
    document.querySelectorAll("[data-cookie-open]").forEach(function (a) {
      a.addEventListener("click", function (e) { e.preventDefault(); openConsent("prefs"); });
    });

    var stored = readConsent();
    if (stored) applyConsent(stored);
    else setTimeout(function () { openConsent("main"); }, 900);
  } else if (!cfg.consentRequired) {
    // Aviso desactivado desde el administrador: se carga analítica directamente
    loadAnalytics();
  }

  // Compartir con Web Share API si está disponible
  var shareBtn = document.querySelector("[data-share]");
  if (shareBtn && navigator.share) {
    shareBtn.classList.remove("d-none");
    shareBtn.addEventListener("click", function () {
      navigator.share({ title: document.title, url: window.location.href }).catch(function () {});
    });
  }
})();
