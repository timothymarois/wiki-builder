// What the wiki does in the browser: find a page, choose a theme, open the navigation on a narrow
// screen, and copy a page's source. Everything else is rendered when the site is built.
(function () {
  "use strict";
  var root = document.documentElement;

  // --- search -------------------------------------------------------------------------------------
  // The index is a constant inlined into every page rather than a file the page fetches, so a page keeps
  // working however it is opened. Its shape is {u: url, t: title, s: subtitle}.
  var box = document.getElementById("q");
  var results = document.getElementById("res");

  function escape(text) {
    return String(text).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }

  if (box && results && typeof WIKI_INDEX !== "undefined") {
    box.addEventListener("input", function () {
      var needle = box.value.trim().toLowerCase();
      if (!needle) { results.hidden = true; return; }
      var hits = WIKI_INDEX.filter(function (page) {
        return page.t.toLowerCase().indexOf(needle) !== -1;
      }).slice(0, 8);
      results.innerHTML = hits.length
        ? hits.map(function (page) {
            return '<button data-go="' + escape(page.u) + '">' + escape(page.t) +
                   "<em>" + escape(page.s) + "</em></button>";
          }).join("")
        : '<button disabled style="color:var(--faint);cursor:default">No page matches</button>';
      results.hidden = false;
    });

    results.addEventListener("click", function (event) {
      var button = event.target.closest("button[data-go]");
      if (button) { location.href = button.dataset.go; }
    });

    document.addEventListener("click", function (event) {
      if (!event.target.closest(".sbox")) { results.hidden = true; }
    });
  }

  // --- theme --------------------------------------------------------------------------------------
  // Three states, not two: following the system is the default, and a reader who has chosen light or
  // dark keeps that choice on this device. The stored value is read again in the page head, before
  // anything paints, so switching pages never flashes the other theme.
  var ORDER = ["auto", "light", "dark"];
  var themeButton = document.querySelector(".theme");

  function stored() {
    try { return localStorage.getItem("wiki-theme") || "auto"; } catch (e) { return "auto"; }
  }

  function showTheme(mode) {
    if (mode === "auto") { root.removeAttribute("data-theme"); }
    else { root.setAttribute("data-theme", mode); }
    if (themeButton) {
      themeButton.textContent = mode.charAt(0).toUpperCase() + mode.slice(1);
      themeButton.setAttribute("aria-label", "Theme: " + mode + ". Click to change.");
    }
  }

  if (themeButton) {
    showTheme(stored());
    themeButton.addEventListener("click", function () {
      var next = ORDER[(ORDER.indexOf(stored()) + 1) % ORDER.length];
      try { localStorage.setItem("wiki-theme", next); } catch (e) { /* a private window; this page still switches */ }
      showTheme(next);
      drawDiagrams();
    });
  }

  // --- the navigation on a narrow screen -----------------------------------------------------------
  var navToggle = document.querySelector(".navtoggle");
  var rail = document.querySelector(".rail");
  if (navToggle && rail) {
    navToggle.addEventListener("click", function () {
      var open = rail.classList.toggle("open");
      navToggle.setAttribute("aria-expanded", open ? "true" : "false");
    });
  }

  // --- the current page in a long page list -----------------------------------------------------------
  // The list scrolls on its own, so a page far down it would open with its own link out of sight. Only
  // the list moves: the article stays where the reader put it.
  var nav = document.getElementById("nav");
  var current = nav && nav.querySelector("a.on");
  if (current && nav.scrollHeight > nav.clientHeight) {
    var top = current.getBoundingClientRect().top - nav.getBoundingClientRect().top;
    if (top < 0 || top > nav.clientHeight - current.offsetHeight) {
      nav.scrollTop += top - nav.clientHeight / 3;
    }
  }

  // --- diagrams ------------------------------------------------------------------------------------------
  // Mermaid is loaded only on a page that has a diagram. It draws in the page's theme -- dark when the reader
  // chose dark, or chose nothing and their system is dark -- and draws again whenever that changes. A drawn
  // diagram no longer holds the text it was written in, so each one's text is kept before the first drawing.
  var diagrams = window.mermaid ? Array.prototype.slice.call(document.querySelectorAll("pre.mermaid")) : [];
  var diagramText = diagrams.map(function (pre) { return pre.textContent; });

  function drawDiagrams() {
    if (!diagrams.length) { return; }
    var chosen = root.getAttribute("data-theme");
    var dark = chosen === "dark" ||
      (!chosen && window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches);
    diagrams.forEach(function (pre, index) {
      pre.removeAttribute("data-processed");
      pre.textContent = diagramText[index];
    });
    window.mermaid.initialize({ startOnLoad: false, theme: dark ? "dark" : "default", securityLevel: "strict" });
    window.mermaid.run({ nodes: diagrams });
  }

  drawDiagrams();
  if (diagrams.length && window.matchMedia) {
    // In the automatic theme the system decides, so a system change redraws too.
    var system = window.matchMedia("(prefers-color-scheme: dark)");
    var followSystem = function () { if (!root.getAttribute("data-theme")) { drawDiagrams(); } };
    if (system.addEventListener) { system.addEventListener("change", followSystem); }
    else if (system.addListener) { system.addListener(followSystem); }
  }

  // --- the lightbox ---------------------------------------------------------------------------------
  // Pictures in a page are thumbnails, so there has to be a way to see one whole. Click anywhere, or
  // press Escape, to close it again.
  var open = null;

  function shut() {
    if (open) { open.remove(); open = null; }
  }

  document.addEventListener("click", function (event) {
    if (open) { shut(); return; }
    var picture = event.target.closest("figure.fig img, .ib .pic img");
    if (!picture) { return; }
    var caption = picture.closest("figure");
    caption = caption ? caption.querySelector("figcaption") : null;
    if (!caption) {
      caption = picture.parentNode.querySelector(".cc");
    }
    open = document.createElement("div");
    open.className = "lightbox";
    open.setAttribute("role", "dialog");
    open.setAttribute("aria-label", picture.alt || "Picture");
    open.innerHTML = '<button class="shut" type="button" aria-label="Close">&times;</button>' +
      '<div class="box"><img src="' + escape(picture.getAttribute("src")) + '" alt="' + escape(picture.alt) + '">' +
      (caption ? "<p>" + escape(caption.textContent) + "</p>" : "") + "</div>";
    document.body.appendChild(open);
    open.querySelector(".shut").focus();
  });

  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape") { shut(); }
  });

  // --- copying a page's source ---------------------------------------------------------------------
  // The block holds nothing but the file, so its own text is what gets copied.
  document.addEventListener("click", function (event) {
    var button = event.target.closest(".copy");
    if (!button) { return; }
    var block = button.parentNode.querySelector("pre");
    if (!block) { return; }
    var said = function (word) {
      button.textContent = word;
      setTimeout(function () { button.textContent = "Copy"; }, 1500);
    };
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(block.textContent).then(function () { said("Copied"); },
                                                            function () { said("Press ⌘C"); });
      return;
    }
    // Older or non-secure contexts have no clipboard API; select the text so one keystroke finishes it.
    var range = document.createRange();
    range.selectNodeContents(block);
    var selection = window.getSelection();
    selection.removeAllRanges();
    selection.addRange(range);
    said("Press ⌘C");
  });
})();
