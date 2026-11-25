const { svgPathProperties } = require("svg-path-properties");

/**
 * Parses an SVG `transform` attribute (`translate`, `scale`, `matrix`) into a
 * 2D affine matrix `[a, b, c, d, e, f]`.
 */
const parseTransformMatrix = (tf) => {
  if (!tf) return [1, 0, 0, 1, 0, 0];
  let m = [1, 0, 0, 1, 0, 0];
  const mul = (a, b) => [
    a[0] * b[0] + a[2] * b[1],
    a[1] * b[0] + a[3] * b[1],
    a[0] * b[2] + a[2] * b[3],
    a[1] * b[2] + a[3] * b[3],
    a[0] * b[4] + a[2] * b[5] + a[4],
    a[1] * b[4] + a[3] * b[5] + a[5],
  ];
  for (const [, fn, argsStr] of tf.matchAll(/(translate|scale|matrix)\(([^)]+)\)/g)) {
    const args = argsStr.split(/[\s,]+/).filter(Boolean).map(Number);
    if (fn === "translate") m = mul(m, [1, 0, 0, 1, args[0] || 0, args[1] || 0]);
    else if (fn === "scale") m = mul(m, [args[0] ?? 1, 0, 0, args[1] ?? args[0] ?? 1, 0, 0]);
    else if (fn === "matrix" && args.length >= 6) m = mul(m, args.slice(0, 6));
  }
  return m;
};

/**
 * Applies a 2D affine matrix `[a, b, c, d, e, f]` plus `(dx, dy)` translation.
 */
const applyAffine = (x, y, m, dx = 0, dy = 0) => ({
  x: m[0] * x + m[2] * y + m[4] + dx,
  y: m[1] * x + m[3] * y + m[5] + dy,
});

/**
 * Transforms an SVG path `d` string via an affine matrix and offset while preserving
 * cubic and quadratic Bézier curve geometry in absolute coordinates.
 */
const transformSvgPathD = (dStr, m = [1, 0, 0, 1, 0, 0], dx = 0, dy = 0) => {
  const tokens = dStr.match(/[a-zA-Z]|[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?/g) || [];
  let i = 0;
  let cmd = "";
  let cx = 0;
  let cy = 0;
  let sx = 0;
  let sy = 0;
  let lastCpx = 0;
  let lastCpy = 0;
  let lastCmd = "";
  const out = [];

  const fmt = (n) => Number(n.toFixed(4));
  const tp = (x, y) => {
    const p = applyAffine(x, y, m, dx, dy);
    return `${fmt(p.x)},${fmt(p.y)}`;
  };
  const num = () => parseFloat(tokens[i++]);
  const isNum = () => i < tokens.length && !/^[a-zA-Z]$/.test(tokens[i]);

  while (i < tokens.length) {
    if (/^[a-zA-Z]$/.test(tokens[i])) {
      cmd = tokens[i++];
      if (cmd === "Z" || cmd === "z") {
        out.push("Z");
        cx = sx;
        cy = sy;
        lastCmd = cmd;
        continue;
      }
    } else if (cmd === "M") {
      cmd = "L";
    } else if (cmd === "m") {
      cmd = "l";
    }

    switch (cmd) {
      case "M":
      case "L": {
        cx = num();
        cy = num();
        if (cmd === "M") {
          sx = cx;
          sy = cy;
        }
        out.push(`${cmd} ${tp(cx, cy)}`);
        break;
      }
      case "m":
      case "l": {
        cx += num();
        cy += num();
        if (cmd === "m") {
          sx = cx;
          sy = cy;
        }
        out.push(`${cmd === "m" ? "M" : "L"} ${tp(cx, cy)}`);
        break;
      }
      case "H":
        cx = num();
        out.push(`L ${tp(cx, cy)}`);
        break;
      case "h":
        cx += num();
        out.push(`L ${tp(cx, cy)}`);
        break;
      case "V":
        cy = num();
        out.push(`L ${tp(cx, cy)}`);
        break;
      case "v":
        cy += num();
        out.push(`L ${tp(cx, cy)}`);
        break;
      case "C": {
        const x1 = num();
        const y1 = num();
        const x2 = num();
        const y2 = num();
        cx = num();
        cy = num();
        lastCpx = x2;
        lastCpy = y2;
        out.push(`C ${tp(x1, y1)} ${tp(x2, y2)} ${tp(cx, cy)}`);
        break;
      }
      case "c": {
        const x1 = cx + num();
        const y1 = cy + num();
        const x2 = cx + num();
        const y2 = cy + num();
        cx += num();
        cy += num();
        lastCpx = x2;
        lastCpy = y2;
        out.push(`C ${tp(x1, y1)} ${tp(x2, y2)} ${tp(cx, cy)}`);
        break;
      }
      case "S":
      case "s": {
        const rel = cmd === "s";
        const x1 = /[CcSs]/.test(lastCmd) ? 2 * cx - lastCpx : cx;
        const y1 = /[CcSs]/.test(lastCmd) ? 2 * cy - lastCpy : cy;
        const x2 = (rel ? cx : 0) + num();
        const y2 = (rel ? cy : 0) + num();
        cx = (rel ? cx : 0) + num();
        cy = (rel ? cy : 0) + num();
        lastCpx = x2;
        lastCpy = y2;
        out.push(`C ${tp(x1, y1)} ${tp(x2, y2)} ${tp(cx, cy)}`);
        break;
      }
      case "Q":
      case "q": {
        const rel = cmd === "q";
        const x1 = (rel ? cx : 0) + num();
        const y1 = (rel ? cy : 0) + num();
        cx = (rel ? cx : 0) + num();
        cy = (rel ? cy : 0) + num();
        lastCpx = x1;
        lastCpy = y1;
        out.push(`Q ${tp(x1, y1)} ${tp(cx, cy)}`);
        break;
      }
      case "T":
      case "t": {
        const rel = cmd === "t";
        const x1 = /[QqTt]/.test(lastCmd) ? 2 * cx - lastCpx : cx;
        const y1 = /[QqTt]/.test(lastCmd) ? 2 * cy - lastCpy : cy;
        cx = (rel ? cx : 0) + num();
        cy = (rel ? cy : 0) + num();
        lastCpx = x1;
        lastCpy = y1;
        out.push(`Q ${tp(x1, y1)} ${tp(cx, cy)}`);
        break;
      }
      default:
        i++;
        break;
    }
    lastCmd = cmd;
    if (isNum() && (cmd === "M" || cmd === "m")) {
      cmd = cmd === "M" ? "L" : "l";
    }
  }
  return out.join(" ");
};

/**
 * Samples contiguous contours of an SVG path (handling relative `m` jumps cleanly)
 * for even-odd point-in-polygon containment checks.
 */
const flattenSvgPathPolys = (d, mat = [1, 0, 0, 1, 0, 0], step = 1.5) => {
  const props = new svgPathProperties(d);
  const parts = props.getParts();
  const polys = [];
  let curPoly = [];
  let lastEnd = null;
  for (const part of parts) {
    if (!lastEnd || Math.hypot(part.start.x - lastEnd.x, part.start.y - lastEnd.y) > 0.5) {
      if (curPoly.length >= 3) polys.push(curPoly);
      curPoly = [];
      const tp = applyAffine(part.start.x, part.start.y, mat);
      curPoly.push([tp.x, tp.y]);
    }
    const n = Math.max(2, Math.ceil(part.length / step));
    for (let i = 1; i <= n; i++) {
      const pt = part.getPointAtLength((part.length * i) / n);
      const tp = applyAffine(pt.x, pt.y, mat);
      curPoly.push([tp.x, tp.y]);
    }
    lastEnd = part.end;
  }
  if (curPoly.length >= 3) polys.push(curPoly);
  return polys;
};

/**
 * Even-odd ray-casting check against a list of flattened contours (hole-aware).
 */
const isPointInPolys = (x, y, polys) => {
  let inside = false;
  for (const poly of polys) {
    for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) {
      const xi = poly[i][0];
      const yi = poly[i][1];
      const xj = poly[j][0];
      const yj = poly[j][1];
      if ((yi > y) !== (yj > y) && x < ((xj - xi) * (y - yi)) / (yj - yi + 1e-12) + xi) {
        inside = !inside;
      }
    }
  }
  return inside;
};

/**
 * Returns the fraction `[0..1]` of sampled points along `strokeD` (after affine
 * transform and translation) that lie inside the target polygon contours.
 */
const strokeContainmentRatio = (strokeD, mat, dx, dy, polys, samples = 30) => {
  const props = new svgPathProperties(strokeD);
  const len = props.getTotalLength();
  if (len <= 0) return 0;
  let inside = 0;
  for (let i = 0; i <= samples; i++) {
    const pt = props.getPointAtLength((len * i) / samples);
    const tp = applyAffine(pt.x, pt.y, mat, dx, dy);
    if (isPointInPolys(tp.x, tp.y, polys)) inside++;
  }
  return inside / (samples + 1);
};

module.exports = {
  parseTransformMatrix,
  applyAffine,
  transformSvgPathD,
  flattenSvgPathPolys,
  isPointInPolys,
  strokeContainmentRatio,
};
