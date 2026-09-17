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
            return '<button data-go="' + escape(page.u) + '">' +
                   (page.p ? '<span class="pp">' + escape(page.p) + " › </span>" : "") + escape(page.t) +
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
  // Three states, not two: light is the default, and a reader who chooses dark, or auto to follow the
  // system, keeps that choice on this device. The stored value is read again in the page head, before
  // anything paints, so switching pages never flashes the other theme.
  var ORDER = ["light", "dark", "auto"];
  var themeButton = document.querySelector(".theme");

  function stored() {
    try { return localStorage.getItem("wiki-theme") || "light"; } catch (e) { return "light"; }
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
  // Mermaid is several megabytes, so it is fetched only on a page that has a diagram, and only once a diagram
  // nears the screen: search, the menu and copying work at once. It draws in the page's theme -- dark when the reader
  // chose dark, or chose nothing and their system is dark -- and draws again whenever that changes. A drawn
  // diagram no longer holds the text it was written in, so each one's text is kept before the first drawing.
  var diagrams = typeof WIKI_MERMAID !== "undefined"
    ? Array.prototype.slice.call(document.querySelectorAll("pre.mermaid")) : [];
  var diagramText = diagrams.map(function (pre) { return pre.textContent; });
  // idle until a diagram nears the screen, loading while the script arrives, ready once it can draw.
  var mermaidState = "idle";
  // What watches for a diagram nearing the screen; it stops watching once Mermaid has loaded.
  var nearing = null;

  function loadMermaid() {
    if (mermaidState !== "idle") { return; }
    mermaidState = "loading";
    var script = document.createElement("script");
    script.src = WIKI_MERMAID;
    script.onload = function () {
      mermaidState = "ready";
      if (nearing) { nearing.disconnect(); }
      drawDiagrams();
    };
    // A failed fetch, such as on a dropped connection, is tried again when a diagram next nears the screen.
    script.onerror = function () { mermaidState = "idle"; script.remove(); };
    document.head.appendChild(script);
  }

  // A chart's colours are the wiki's, not Mermaid's: left to its own dark theme, a pie's first slice is very
  // nearly the page's own black and an xy chart sits in a grey panel of its own. Series colours are the
  // Okabe-Ito set, which stays apart for a reader who cannot tell red from green. Text and rules follow the
  // page's own colours, so a chart carries the theme the reader chose.
  var CHART_INK = { light: "#202122", dark: "#eaecf0" };
  var CHART_SOFT = { light: "#54595d", dark: "#a2a9b1" };
  var CHART_RULE = { light: "#a2a9b1", dark: "#54595d" };
  var CHART_PAGE = { light: "#ffffff", dark: "#101418" };
  var CHART_SHADE = { light: "#f1f3f5", dark: "#1b1e21" };
  // The darkest of the set leads on a light page and the lightest on a dark one, so no series disappears
  // into the background it is drawn on.
  var CHART_SERIES = {
    light: ["#0072b2", "#e69f00", "#009e73", "#cc79a7", "#d55e00", "#56b4e9"],
    dark: ["#56b4e9", "#e69f00", "#009e73", "#cc79a7", "#f0e442", "#0072b2"]
  };
  // A pie's slices are the only fills a label is written on top of, so they are dark enough for white text
  // in either theme rather than pale tints of the series colours.
  var CHART_SLICES = ["#0072b2", "#c1440e", "#007a5e", "#9b4b87", "#8c6d1f", "#2a6f97", "#7b5aa6", "#47632a"];
  // What a chart is drawn at before the page scales it down: the wide kinds share one width and the square
  // ones another, so a page of charts keeps one rhythm instead of each kind arriving at its own size.
  var CHART_WIDE = { width: 700, height: 400 };
  var CHART_SQUARE = 560;

  function chartColours(dark) {
    var theme = dark ? "dark" : "light";
    var ink = CHART_INK[theme], soft = CHART_SOFT[theme], rule = CHART_RULE[theme], page = CHART_PAGE[theme];
    var series = CHART_SERIES[theme];
    var colours = {
      // An xy chart with no panel of its own sits on the page, in either theme.
      xyChart: { backgroundColor: "transparent", titleColor: ink, plotColorPalette: series.join(","),
                 xAxisTitleColor: soft, xAxisLabelColor: soft, xAxisTickColor: rule, xAxisLineColor: rule,
                 yAxisTitleColor: soft, yAxisLabelColor: soft, yAxisTickColor: rule, yAxisLineColor: rule },
      // A slice carries its own percentage, so the text on it is white and the slice is dark enough to hold it.
      pieTitleTextColor: ink, pieLegendTextColor: ink, pieSectionTextColor: "#ffffff",
      pieStrokeColor: page, pieOuterStrokeColor: rule, pieOpacity: "1",
      quadrantTitleFill: ink, quadrantPointTextFill: ink, quadrantXAxisTextFill: soft,
      quadrantYAxisTextFill: soft, quadrantPointFill: series[0],
      quadrantInternalBorderStrokeFill: rule, quadrantExternalBorderStrokeFill: rule,
      radar: { axisColor: rule, graticuleColor: rule, curveOpacity: 0.4 }
    };
    CHART_SLICES.forEach(function (slice, index) { colours["pie" + (index + 1)] = slice; });
    // The quarters alternate between the page and the shade beside it, so the four are visible as four
    // without any of them claiming a meaning of its own.
    for (var quarter = 1; quarter <= 4; quarter += 1) {
      colours["quadrant" + quarter + "Fill"] = quarter % 2 ? page : CHART_SHADE[theme];
    }
    // A radar curve takes its colour from the same set the other charts use.
    series.slice(0, 3).forEach(function (colour, index) { colours["cScale" + index] = colour; });
    return colours;
  }

  function drawDiagrams() {
    if (!diagrams.length || mermaidState !== "ready") { return; }
    var chosen = root.getAttribute("data-theme");
    var dark = chosen === "dark" ||
      (!chosen && window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches);
    diagrams.forEach(function (pre, index) {
      pre.removeAttribute("data-processed");
      pre.textContent = diagramText[index];
    });
    // Numbered ids, not Mermaid's default clock: it names each drawing after the millisecond it started, so two
    // that start inside one millisecond share a name, and the second is sized against the first -- it keeps no
    // height of its own and paints over the diagram above it. Charts draw fast enough to collide every time.
    window.mermaid.initialize({ startOnLoad: false, theme: dark ? "dark" : "default", securityLevel: "strict",
                                deterministicIds: true, themeVariables: chartColours(dark),
                                xyChart: CHART_WIDE, sankey: CHART_WIDE,
                                quadrantChart: { chartWidth: CHART_SQUARE, chartHeight: CHART_SQUARE,
                                                 pointRadius: 7, pointLabelFontSize: 14 },
                                radar: { width: CHART_SQUARE, height: CHART_SQUARE } });
    // A drawing Mermaid cannot read rejects the run; the ones that did come out are still recoloured.
    window.mermaid.run({ nodes: diagrams }).catch(function () {}).then(function () { recolourFlows(dark); });
  }

  // The scheme Mermaid paints a sankey from, in its own code, where no setting reaches it. A block takes the
  // colour at its place in this list and a band is a gradient from the block it leaves to the block it
  // reaches, so swapping each of these colours for the page's own keeps every band a gradient and puts the
  // wiki's palette on the blocks and the bars between them.
  var FLOW_SCHEME = ["#4e79a7", "#f28e2c", "#e15759", "#76b7b2", "#59a14f",
                     "#edc949", "#af7aa1", "#ff9da7", "#9c755f", "#bab0ab"];

  function recolourFlows(dark) {
    var series = CHART_SERIES[dark ? "dark" : "light"];
    diagrams.forEach(function (pre) {
      var flow = pre.querySelector('svg[aria-roledescription="sankey"]');
      if (!flow) { return; }
      flow.querySelectorAll("rect").forEach(function (block) {
        var place = FLOW_SCHEME.indexOf((block.getAttribute("fill") || "").toLowerCase());
        if (place !== -1) { block.setAttribute("fill", series[place % series.length]); }
      });
      flow.querySelectorAll("stop").forEach(function (end) {
        var place = FLOW_SCHEME.indexOf((end.getAttribute("stop-color") || "").toLowerCase());
        if (place !== -1) { end.setAttribute("stop-color", series[place % series.length]); }
      });
    });
  }

  if (diagrams.length) {
    if ("IntersectionObserver" in window) {
      // 600px ahead of the screen, so a diagram is usually drawn by the time the reader reaches it.
      nearing = new IntersectionObserver(function (entries) {
        if (entries.some(function (entry) { return entry.isIntersecting; })) {
          loadMermaid();
        }
      }, { rootMargin: "600px 0px" });
      diagrams.forEach(function (pre) { nearing.observe(pre); });
    } else {
      loadMermaid();
    }
  }
  if (diagrams.length && window.matchMedia) {
    // In the automatic theme the system decides, so a system change redraws too.
    var system = window.matchMedia("(prefers-color-scheme: dark)");
    var followSystem = function () { if (!root.getAttribute("data-theme")) { drawDiagrams(); } };
    if (system.addEventListener) { system.addEventListener("change", followSystem); }
    else if (system.addListener) { system.addListener(followSystem); }
  }

  // --- the lightbox ---------------------------------------------------------------------------------
  // Pictures in a page are thumbnails, and a PDF is a link, so there has to be a way to see either whole
  // without leaving the page. One native dialog shows both. It is modal: the page behind cannot be used or
  // scrolled, Tab stays inside it, Escape, Close or a click on the backdrop closes it, and closing puts focus
  // back on the picture or link that opened it.
  //
  // Escape closes the dialog unless focus is inside a PDF's frame, where the browser's own PDF viewer takes the
  // keyboard and Escape never reaches the page. That is accepted rather than worked around: the frame stays
  // focusable, so a reader can scroll and search the PDF with the keyboard, and Close is always in view above it,
  // with Tab leading back to it.
  var dialogs = typeof HTMLDialogElement === "function" && "showModal" in HTMLDialogElement.prototype;
  var dialog = null;
  var opener = null;

  function element(tag, attributes, text) {
    var made = document.createElement(tag);
    Object.keys(attributes).forEach(function (name) { made.setAttribute(name, attributes[name]); });
    if (text) { made.textContent = text; }
    return made;
  }

  // A stop at each end of the dialog sends focus round to the control at the other end. A key listener cannot
  // do this: Tab pressed inside a PDF's frame never reaches the page, but the focus it moves lands on a stop.
  // A stop is empty and hands focus on the instant it receives it, so a screen reader has nothing to announce
  // there. It is not hidden from one either: a focusable element hidden that way is one it could land on unnamed.
  function stop(toLast) {
    var edge = element("span", { "class": "edge", tabindex: "0" });
    edge.addEventListener("focus", function () {
      var controls = dialog.querySelectorAll("a[href], button, iframe");
      controls[toLast ? controls.length - 1 : 0].focus();
    });
    return edge;
  }

  function lightbox() {
    if (dialog) { return dialog; }
    dialog = element("dialog", { "class": "lightbox" });
    document.body.appendChild(dialog);
    // The dialog covers the window, so a click that lands on the dialog itself is a click beside what it shows. It
    // closes the dialog only when the press began there too: a press on a title or a caption, dragged out to
    // select its text, ends on the dialog without being a click beside anything.
    var pressed = false;
    dialog.addEventListener("pointerdown", function (event) { pressed = event.target === dialog; });
    dialog.addEventListener("click", function (event) {
      if (pressed && event.target === dialog) { dismiss(); }
      pressed = false;
    });
    dialog.addEventListener("close", closed);
    return dialog;
  }

  // Every close path ends in the same state. The browser fires close a task after the dialog is closed, so
  // closing it and leaving the rest to that event leaves the page locked and the dialog full in between -- long
  // enough for a reader to open the next one on top of the last. Close and the backdrop therefore clean up as
  // they close, and the close event, which is all Escape leaves behind, cleans up after them: doing it twice
  // changes nothing.
  function closed() {
    root.classList.remove("lightbox-open");
    // Emptied, so a PDF still loading stops, and the next opening starts clean.
    dialog.textContent = "";
    dialog.removeAttribute("aria-label");
    var back = opener;
    opener = null;
    if (back) { back.focus(); }
  }

  function dismiss() {
    if (dialog.open) { dialog.close(); }
    closed();
  }

  function show(kind, from, parts, shut) {
    var box = lightbox();
    box.className = "lightbox " + kind;
    // Emptied before it is filled, so nothing from an earlier opening can be shown twice.
    box.textContent = "";
    box.appendChild(stop(true));
    parts.forEach(function (part) { box.appendChild(part); });
    box.appendChild(stop(false));
    shut.addEventListener("click", dismiss);
    shut.autofocus = true;
    opener = from;
    root.classList.add("lightbox-open");
    // The browser puts focus back where it was when the dialog opened, so the opener takes it first: a picture
    // takes focus from nothing, and a clicked link does not hold it in every browser.
    from.focus();
    box.showModal();
    shut.focus();
  }

  document.addEventListener("click", function (event) {
    var picture = event.target.closest("figure.fig img, .ib .pic img");
    if (!picture || !dialogs) { return; }
    var caption = picture.closest("figure");
    caption = caption ? caption.querySelector("figcaption") : null;
    if (!caption) {
      caption = picture.parentNode.querySelector(".cc");
    }
    // A picture is not focusable of its own accord, and focus has to come back to it when the dialog closes.
    if (!picture.hasAttribute("tabindex")) { picture.setAttribute("tabindex", "-1"); }
    var whole = element("img", { src: picture.getAttribute("src"), alt: picture.alt });
    var frame = element("div", { "class": "box" });
    frame.appendChild(whole);
    if (caption) { frame.appendChild(element("p", {}, caption.textContent)); }
    var shut = element("button", { "class": "shut", type: "button", "aria-label": "Close" }, "×");
    lightbox().setAttribute("aria-label", picture.alt || (caption && caption.textContent) || "Picture");
    show("picture", picture, [shut, frame], shut);
    // A picture with no size of its own, such as an SVG that gives only a viewBox, leaves the box nothing to
    // take its width from, and is drawn at nothing. It takes the thumbnail's shape instead, as large as the
    // window allows.
    var shape = picture.getBoundingClientRect();
    var fit = function () {
      if (whole.getBoundingClientRect().width || !shape.width) { return; }
      var width = Math.min(window.innerWidth * 0.96, window.innerHeight * 0.88 * shape.width / shape.height);
      frame.style.width = Math.round(width) + "px";
      whole.style.width = "100%";
    };
    if (whole.complete) { fit(); } else { whole.addEventListener("load", fit); }
  });

  // A phone or tablet opens a PDF in its own viewer instead, as does a browser that shows no PDFs itself: Safari
  // on iOS draws only the first page of a PDF in a frame, and older Chrome on Android offers to download it.
  function showsPdfs() {
    var touch = window.matchMedia && window.matchMedia("(pointer: coarse)").matches;
    return !touch && navigator.pdfViewerEnabled !== false;
  }

  document.addEventListener("click", function (event) {
    // Any other button, or a held key, keeps what the browser does with a link: a new tab, a new window, a
    // download. So does a right click, which is no click at all.
    if (event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey ||
        event.altKey) { return; }
    var link = event.target.closest("a.pdf[href]");
    if (!link || !dialogs || !showsPdfs() || link.protocol !== location.protocol || link.host !== location.host) {
      return;
    }
    event.preventDefault();
    var name = link.textContent.trim() || "PDF";
    var shut = element("button", { "class": "act", type: "button" }, "Close");
    var actions = element("div", { "class": "acts" });
    actions.appendChild(element("a", { "class": "act", href: link.href, target: "_blank", rel: "noopener" },
                                "Open in new tab"));
    actions.appendChild(element("a", { "class": "act", href: link.href, download: "" }, "Download"));
    actions.appendChild(shut);
    var bar = element("div", { "class": "bar" });
    bar.appendChild(element("h2", {}, name));
    bar.appendChild(actions);
    var sheet = element("div", { "class": "sheet" });
    sheet.appendChild(bar);
    sheet.appendChild(element("iframe", { title: name + " (PDF)", src: link.href }));
    // Named by the title's text rather than by an id, which could match a heading id the build writes.
    lightbox().setAttribute("aria-label", name);
    show("document", link, [sheet], shut);
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
