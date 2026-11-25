const $ = (id) => document.getElementById(id);
const NS = "http://www.w3.org/2000/svg";
const storageKey = "kano-manual-tracing-v1";
let catalog = [],
  category = "Vowels",
  selected = new Set(),
  queue = [],
  position = 0;
let source = "",
  groupIds = [],
  drafts = {},
  busy = false,
  drawing = null,
  animations = [];
let previewGeneration = 0;
const current = () => catalog.find((item) => item.id === queue[position]);
const draft = () =>
  (drafts[current().file] ??= {
    strokes: [],
    reviewed: false,
    completed: false,
  });
const status = (text) => {
  $("status").textContent = text;
};
function save() {
  try {
    localStorage.setItem(storageKey, JSON.stringify(drafts));
  } catch {
    status(
      "Device storage is full. Download an editable session to keep your work."
    );
  }
}
async function api(path, body) {
  const response = await fetch(
    path,
    body
      ? {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        }
      : {}
  );
  const result = await response.json();
  if (!response.ok) throw new Error(result.error || "Request failed");
  return result;
}
async function task(fn) {
  if (busy) return;
  busy = true;
  document.body.setAttribute("aria-busy", "true");
  document.querySelectorAll("button,select,input").forEach((el) => {
    el.disabled = true;
  });
  try {
    await fn();
  } catch (error) {
    status(error.message);
  } finally {
    busy = false;
    document.body.removeAttribute("aria-busy");
    document.querySelectorAll("button,select,input").forEach((el) => {
      el.disabled = false;
    });
    if (!$("editor").hidden) updateNavigation();
  }
}
function visible() {
  const term = $("search").value.trim().toLowerCase();
  return catalog.filter(
    (item) =>
      item.category === category &&
      `${item.label} ${item.name}`.toLowerCase().includes(term)
  );
}
function renderPicker() {
  $("categories").replaceChildren(
    ...[...new Set(catalog.map((item) => item.category))].map((name) => {
      const button = document.createElement("button");
      button.textContent = name;
      button.setAttribute("aria-pressed", String(category === name));
      button.onclick = () => {
        category = name;
        renderPicker();
      };
      return button;
    })
  );
  $("characters").replaceChildren(
    ...visible().map((item) => {
      const label = document.createElement("label");
      label.className = "character";
      const input = document.createElement("input");
      input.type = "checkbox";
      input.checked = selected.has(item.id);
      input.onchange = () => {
        input.checked ? selected.add(item.id) : selected.delete(item.id);
        renderPicker();
      };
      const glyph = document.createElement("strong");
      glyph.textContent = item.label;
      const name = document.createElement("small");
      name.textContent = item.name;
      const progress = document.createElement("small");
      progress.textContent = drafts[item.file]?.completed
        ? "✓ Reviewed"
        : drafts[item.file]?.strokes.length
        ? "Draft saved"
        : "Not started";
      label.append(input, glyph, name, progress);
      return label;
    })
  );
  $("selectionCount").textContent = `${selected.size} selected`;
}
function stopPreview() {
  previewGeneration++;
  animations.forEach((animation) => animation.cancel());
  animations = [];
}
function svgElement(tag, attributes) {
  const node = document.createElementNS(NS, tag);
  Object.entries(attributes).forEach(([key, value]) =>
    node.setAttribute(key, value)
  );
  return node;
}
function makeStage(container, rawVisible) {
  const xml = new DOMParser().parseFromString(source, "image/svg+xml");
  const svg = document.importNode(xml.documentElement, true);
  svg
    .querySelectorAll("script,foreignObject,metadata")
    .forEach((node) => node.remove());
  const view = svg.getAttribute("viewBox")?.split(/[ ,]+/).map(Number) || [
    0,
    0,
    parseFloat(svg.getAttribute("width")),
    parseFloat(svg.getAttribute("height")),
  ];
  const pad = Math.max(view[2], view[3]) * 0.12;
  svg.setAttribute(
    "viewBox",
    `${view[0] - pad} ${view[1] - pad} ${view[2] + 2 * pad} ${
      view[3] + 2 * pad
    }`
  );
  svg.removeAttribute("width");
  svg.removeAttribute("height");
  svg.querySelectorAll("path").forEach((path) => {
    if (/g\d+s\d+/.test(path.id)) path.remove();
    else {
      path.removeAttribute("style");
      const active =
        container.id === "drawing" && path.parentNode.id === $("group").value;
      path.setAttribute("fill", active ? "#c5bcff" : "#b8bacb");
      path.setAttribute("opacity", active ? ".5" : ".25");
    }
  });
  const width = Math.max(view[2], view[3]) * 0.008 * +$("strokeWidth").value;
  for (const stroke of draft().strokes) {
    const group = svg.querySelector(`[id="${stroke.group}"]`);
    if (!group) continue;
    if (rawVisible)
      group.append(
        svgElement("path", {
          d: polyline(stroke.raw),
          fill: "none",
          stroke: "#ffbc77",
          "stroke-width": width * 0.7,
          opacity: ".65",
        })
      );
    const path = svgElement("path", {
      d: stroke.d,
      fill: "none",
      stroke: "#87e5c2",
      "stroke-width": width,
      "stroke-linecap": "round",
      "stroke-linejoin": "round",
      "data-trace": "true",
    });
    group.append(path);
    const start = path.getPointAtLength(0);
    group.append(
      svgElement("circle", {
        cx: start.x,
        cy: start.y,
        r: width * 1.4,
        fill: "#c5bcff",
      })
    );
  }
  container.replaceChildren(svg);
  return svg;
}
function polyline(points) {
  return "M " + points.map((p) => p.join(",")).join(" L ");
}
function renderEditor() {
  stopPreview();
  makeStage($("drawing"), $("raw").checked);
  makeStage($("preview"), false);
  $("reviewed").checked = draft().reviewed;
  $("strokes").replaceChildren(
    ...draft().strokes.map((stroke, index) => {
      const li = document.createElement("li");
      li.textContent = `${stroke.group} · Stroke ${index + 1} · ${
        stroke.points
      } points `;
      const button = document.createElement("button");
      button.textContent = "Download through this stroke";
      button.onclick = () => task(() => downloadSVG(index + 1));
      li.append(button);
      return li;
    })
  );
  const missing = groupIds.filter(
    (gid) => !draft().strokes.some((stroke) => stroke.group === gid)
  );
  $("coverage").textContent = missing.length
    ? `Untraced groups: ${missing.join(
        ", "
      )}. Downloads are partial drafts until every group is traced and reviewed.`
    : "All groups have strokes. Review full coverage: a stroke in each group does not prove the entire outline is covered.";
  const strokes = draft().strokes;
  $("metrics").textContent = strokes.length
    ? `${strokes.length} strokes · Maximum simplification tolerance ${Math.max(
        ...strokes.map((s) => s.tolerance)
      ).toFixed(4)} SVG units · Raster uncertainty up to ${Math.max(
        ...strokes.map((s) => s.rasterError)
      ).toFixed(4)} SVG units. Inspect crossings and stroke ends.`
    : "Draw your first stroke to begin.";
  const preserved = strokes.reduce(
    (count, stroke) => count + (stroke.preservedTurns || 0),
    0
  );
  if (preserved) {
    $(
      "metrics"
    ).textContent += ` ${preserved} tight turn(s) retain your manual geometry inside the outline; review their centering.`;
  }
  updateNavigation();
}
function updateNavigation() {
  $("previous").disabled = position === 0;
  $("next").disabled = position >= queue.length - 1;
  $("download").disabled = !draft().strokes.length;
  $("complete").disabled =
    !draft().reviewed ||
    groupIds.some((gid) => !draft().strokes.some((s) => s.group === gid));
  $("complete").textContent =
    position === queue.length - 1 ? "Finish selection" : "Accept & next";
}
async function openCharacter() {
  stopPreview();
  const data = await api(`/api/character?id=${current().id}`);
  source = data.svg;
  groupIds = data.groups;
  $("group").replaceChildren(...groupIds.map((gid) => new Option(gid, gid)));
  $("title").textContent = `${current().label} · ${current().name}`;
  $("position").textContent = `${position + 1} / ${queue.length}`;
  $("picker").hidden = true;
  $("editor").hidden = false;
  renderEditor();
  status(
    "Draw a stroke in the selected outline group. Original SVG files are never overwritten."
  );
}
function invalidate() {
  draft().reviewed = false;
  draft().completed = false;
  save();
  renderEditor();
}
$("drawing").addEventListener("pointerdown", (event) => {
  if (busy || drawing || event.button !== 0) return;
  const group = $("drawing").querySelector(`[id="${$("group").value}"]`);
  if (!group) return;
  const point = new DOMPoint(event.clientX, event.clientY).matrixTransform(
    group.getScreenCTM().inverse()
  );
  const svg = $("drawing").querySelector("svg");
  const width = svg.viewBox.baseVal.width * 0.006 * +$("strokeWidth").value;
  const path = svgElement("path", {
    fill: "none",
    stroke: "#ffbc77",
    "stroke-width": width,
    "stroke-linecap": "round",
    "stroke-linejoin": "round",
  });
  group.append(path);
  drawing = {
    raw: [[point.x, point.y]],
    path,
    group: $("group").value,
    pointer: event.pointerId,
  };
  $("drawing").setPointerCapture(event.pointerId);
});
$("drawing").addEventListener("pointermove", (event) => {
  if (!drawing || drawing.pointer !== event.pointerId) return;
  const matrix = drawing.path.parentNode.getScreenCTM().inverse();
  for (const sample of event.getCoalescedEvents?.() || [event]) {
    const point = new DOMPoint(sample.clientX, sample.clientY).matrixTransform(
      matrix
    );
    if (drawing.raw.length < 6000) drawing.raw.push([point.x, point.y]);
  }
  drawing.path.setAttribute("d", polyline(drawing.raw));
});
$("drawing").addEventListener("pointerup", (event) => {
  if (!drawing || drawing.pointer !== event.pointerId) return;
  const pending = drawing;
  drawing = null;
  task(async () => {
    status("Centering stroke…");
    try {
      const result = await api("/api/snap", {
        id: current().id,
        group: pending.group,
        points: pending.raw,
        accuracy: +$("accuracy").value,
      });
      draft().strokes.push({
        ...result,
        raw: pending.raw,
        group: pending.group,
      });
      invalidate();
      status("Stroke centered. Check its route and endpoints in the preview.");
    } finally {
      renderEditor();
    }
  });
});
$("drawing").addEventListener("pointercancel", () => {
  drawing = null;
  renderEditor();
  status("Drawing interrupted. Please retry this stroke.");
});
$("search").oninput = renderPicker;
$("selectAll").onclick = () => {
  visible().forEach((item) => selected.add(item.id));
  renderPicker();
};
$("deselect").onclick = () => {
  selected.clear();
  renderPicker();
};
$("start").onclick = () =>
  task(async () => {
    queue = catalog
      .filter((item) => selected.has(item.id))
      .map((item) => item.id);
    if (!queue.length) return status("Select at least one character.");
    position = 0;
    await openCharacter();
  });
$("selection").onclick = () => {
  if (busy) return;
  stopPreview();
  $("editor").hidden = true;
  $("picker").hidden = false;
  renderPicker();
};
$("previous").onclick = () =>
  task(async () => {
    position--;
    await openCharacter();
  });
$("next").onclick = () =>
  task(async () => {
    position++;
    await openCharacter();
  });
$("undo").onclick = $("retry").onclick = () => {
  if (busy) return;
  draft().strokes.pop();
  invalidate();
  status("Last stroke removed. Draw it again.");
};
$("clear").onclick = () => {
  if (!busy && confirm("Clear every stroke for this character?")) {
    draft().strokes = [];
    invalidate();
  }
};
$("raw").onchange = renderEditor;
$("group").onchange = renderEditor;
$("accuracy").oninput = () => {
  $("accuracyValue").value = $("accuracy").value;
};
$("refine").onclick = () =>
  task(async () => {
    status("Recalculating all strokes…");
    const updated = [];
    for (const stroke of draft().strokes) {
      const result = await api("/api/snap", {
        id: current().id,
        group: stroke.group,
        points: stroke.raw,
        accuracy: +$("accuracy").value,
      });
      updated.push({ ...stroke, ...result });
    }
    draft().strokes = updated;
    invalidate();
    status("Accuracy applied. Review the updated paths.");
  });
$("reviewed").onchange = () => {
  draft().reviewed = $("reviewed").checked;
  save();
  updateNavigation();
};
$("stop").onclick = () => {
  stopPreview();
  makeStage($("preview"), false);
};
$("strokeWidth").oninput = () => {
  $("strokeWidthValue").value = `${$("strokeWidth").value}×`;
  if (!drawing) renderEditor();
};
$("speed").oninput = () => {
  const speed = +$("speed").value;
  $("speedValue").value = `${speed}×`;
  animations.forEach((animation) => animation.updatePlaybackRate(speed));
};
$("replay").onclick = async () => {
  stopPreview();
  makeStage($("preview"), false);
  const generation = previewGeneration;
  const paths = [...$("preview").querySelectorAll("[data-trace]")];
  // DOM order matches Kano: group order, then stroke order within each group.
  for (const path of paths) {
    const length = path.getTotalLength();
    path.style.strokeDasharray = length;
    path.style.strokeDashoffset = length;
  }
  for (const path of paths) {
    if (generation !== previewGeneration) return;
    const length = path.getTotalLength();
    const animation = path.animate(
      [{ strokeDashoffset: length }, { strokeDashoffset: 0 }],
      { duration: 1100, fill: "forwards", easing: "linear" }
    );
    animation.updatePlaybackRate(+$("speed").value);
    animations.push(animation);
    try {
      await animation.finished;
    } catch {
      return;
    }
  }
};
function download(content, name, type) {
  const url = URL.createObjectURL(new Blob([content], { type }));
  const link = document.createElement("a");
  link.href = url;
  link.download = name;
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
async function downloadSVG(count = draft().strokes.length) {
  const result = await api("/api/export", {
    id: current().id,
    strokes: draft().strokes.slice(0, count),
  });
  download(result.svg, current().file.split("/").pop(), "image/svg+xml");
  status(
    "SVG downloaded with original outlines and Kano stroke labels. Only replace your app asset after reviewing it."
  );
}
$("download").onclick = () => task(() => downloadSVG());
$("complete").onclick = () =>
  task(async () => {
    draft().completed = true;
    save();
    if (position < queue.length - 1) {
      position++;
      await openCharacter();
    } else {
      $("editor").hidden = true;
      $("picker").hidden = false;
      renderPicker();
      status(
        "Selection reviewed. Use each character’s Download SVG button to export its file."
      );
    }
  });
$("backup").onclick = () =>
  download(
    JSON.stringify({ version: 1, drafts }, null, 2),
    "kano-tracing-session.json",
    "application/json"
  );
function validDrafts(value) {
  if (!value || typeof value !== "object" || Array.isArray(value))
    throw new Error("Invalid session.");
  const result = {};
  for (const [file, entry] of Object.entries(value)) {
    if (!catalog.some((item) => item.file === file)) continue;
    if (!Array.isArray(entry.strokes) || entry.strokes.length > 200)
      throw new Error("Invalid stroke list.");
    for (const stroke of entry.strokes) {
      if (
        !/^g\d+$/.test(stroke.group) ||
        typeof stroke.d !== "string" ||
        stroke.d.length > 500000 ||
        !Array.isArray(stroke.raw) ||
        stroke.raw.length > 6000 ||
        !stroke.raw.every(
          (p) => Array.isArray(p) && p.length === 2 && p.every(Number.isFinite)
        ) ||
        !["points", "tolerance", "rasterError"].every((k) =>
          Number.isFinite(stroke[k])
        )
      )
        throw new Error("Invalid saved stroke.");
    }
    result[file] = {
      ...entry,
      reviewed: Boolean(entry.reviewed),
      completed: Boolean(entry.completed),
    };
  }
  return result;
}
$("restore").onchange = () =>
  task(async () => {
    const file = $("restore").files[0];
    if (!file) return;
    if (file.size > 20_000_000) throw new Error("Session is too large.");
    const data = JSON.parse(await file.text());
    if (data.version !== 1) throw new Error("Unsupported session version.");
    const restored = validDrafts(data.drafts);
    if (!confirm("Replace matching local drafts with this session?")) return;
    drafts = { ...drafts, ...restored };
    save();
    renderEditor();
    status("Session restored.");
  });
try {
  catalog = await api("/api/catalog");
  try {
    drafts = validDrafts(JSON.parse(localStorage.getItem(storageKey) || "{}"));
  } catch {
    status(
      "Saved draft could not be loaded. Restore an exported session or start fresh."
    );
  }
  renderPicker();
} catch (error) {
  status(`Cannot load characters: ${error.message}`);
}
