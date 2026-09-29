/* Inicia Legal · asistente conversacional */
(function () {
  "use strict";

  var root = document.querySelector("[data-assistant]");
  if (!root) return;

  var endpoint = root.getAttribute("data-endpoint");
  var toggle = root.querySelector("[data-assistant-toggle]");
  var panel = root.querySelector("[data-assistant-panel]");
  var close = root.querySelector("[data-assistant-close]");
  var form = root.querySelector("[data-assistant-form]");
  var input = root.querySelector("[data-assistant-input]");
  var messages = root.querySelector("[data-assistant-messages]");

  function getCookie(name) {
    var match = document.cookie.match(new RegExp("(?:^|; )" + name.replace(/([.$?*|{}()[\]\\/+^])/g, "\\$1") + "=([^;]*)"));
    return match ? decodeURIComponent(match[1]) : "";
  }

  function setOpen(open) {
    panel.hidden = !open;
    toggle.setAttribute("aria-expanded", open ? "true" : "false");
    root.classList.toggle("is-open", open);
    if (open) window.setTimeout(function () { input.focus(); }, 40);
  }

  function addMessage(text, role) {
    var node = document.createElement("div");
    node.className = "assistant-message assistant-message-" + role;
    node.textContent = text;
    messages.appendChild(node);
    messages.scrollTop = messages.scrollHeight;
    return node;
  }

  function addSources(sources) {
    if (!sources || !sources.length) return;
    var wrap = document.createElement("div");
    wrap.className = "assistant-sources";
    var title = document.createElement("strong");
    title.textContent = "Fuentes sugeridas:";
    wrap.appendChild(title);
    sources.slice(0, 3).forEach(function (source) {
      if (!source.url) return;
      var link = document.createElement("a");
      link.href = source.url;
      link.textContent = source.title;
      wrap.appendChild(link);
    });
    messages.appendChild(wrap);
    messages.scrollTop = messages.scrollHeight;
  }

  function setBusy(busy) {
    root.classList.toggle("is-busy", busy);
    input.disabled = busy;
    form.querySelector("button[type=submit]").disabled = busy;
  }

  function ask(text) {
    var value = (text || input.value || "").trim();
    if (!value) return;
    addMessage(value, "user");
    input.value = "";
    setBusy(true);
    var pending = addMessage("Buscando información del sitio...", "bot");

    fetch(endpoint, {
      method: "POST",
      credentials: "same-origin",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCookie("csrftoken"),
        "X-Requested-With": "XMLHttpRequest",
      },
      body: JSON.stringify({ message: value }),
    })
      .then(function (response) {
        return response.json().then(function (data) {
          if (!response.ok || !data.ok) throw new Error(data.message || "No se pudo responder la consulta.");
          return data;
        });
      })
      .then(function (data) {
        pending.textContent = data.answer;
        addSources(data.sources);
      })
      .catch(function (err) {
        pending.textContent = err.message || "Ocurrió un error. Intente nuevamente o solicite una reunión.";
      })
      .finally(function () {
        setBusy(false);
        input.focus();
      });
  }

  toggle.addEventListener("click", function () { setOpen(panel.hidden); });
  close.addEventListener("click", function () { setOpen(false); });
  form.addEventListener("submit", function (event) {
    event.preventDefault();
    ask();
  });
  input.addEventListener("keydown", function (event) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      ask();
    }
  });
  root.querySelectorAll("[data-assistant-suggestion]").forEach(function (button) {
    button.addEventListener("click", function () {
      ask(button.getAttribute("data-assistant-suggestion"));
    });
  });
  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape" && !panel.hidden) setOpen(false);
  });
})();
