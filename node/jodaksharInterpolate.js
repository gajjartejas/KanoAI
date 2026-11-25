const fs = require("fs");
const path = require("path");
const {
  parseTransformMatrix,
  transformSvgPathD,
  flattenSvgPathPolys,
  strokeContainmentRatio,
} = require("./svgGeometry");

const INSIDE_THRESHOLD = 0.75;
const IDENTITY_MATRIX = [1, 0, 0, 1, 0, 0];

/**
 * Parses an Inkscape `interpolate-svg` file into normalized groups containing
 * affine transforms, outline `gNp0` paths, stroke `gNsN` paths, and bounding boxes.
 */
const parseInterpolateSvgGroups = (svgFile) => {
  const xml = fs.readFileSync(svgFile, "utf8");
  const wM = xml.match(/\bwidth="([\d.]+)"/);
  const hM = xml.match(/\bheight="([\d.]+)"/);
  const groups = [];

  for (const [, gAttrs, inner] of xml.matchAll(/<g\b([^>]*)>([\s\S]*?)<\/g>/g)) {
    const tfM = gAttrs.match(/transform="([^"]+)"/);
    const mat = parseTransformMatrix(tfM ? tfM[1] : "");
    let outline = null;
    const strokes = [];

    for (const [, pAttrs] of inner.matchAll(/<path\b([^>]*)\/?>/g)) {
      const idM = pAttrs.match(/id="([^"]+)"/) || pAttrs.match(/inkscape:label="([^"]+)"/);
      const dM = pAttrs.match(/\bd="([^"]+)"/);
      if (!idM || !dM) continue;
      if (/^g\d+p\d+$/.test(idM[1])) outline = dM[1];
      else if (/^g\d+s\d+$/.test(idM[1])) strokes.push({ id: idM[1], d: dM[1] });
    }

    let x1 = Infinity;
    let y1 = Infinity;
    let x2 = -Infinity;
    let y2 = -Infinity;
    if (outline) {
      for (const poly of flattenSvgPathPolys(outline, mat, 3)) {
        for (const [px, py] of poly) {
          x1 = Math.min(x1, px);
          x2 = Math.max(x2, px);
          y1 = Math.min(y1, py);
          y2 = Math.max(y2, py);
        }
      }
    }
    groups.push({ mat, outline, strokes, bb: { x1, y1, x2, y2 } });
  }

  return {
    refW: wM ? parseFloat(wM[1]) : 0,
    refH: hM ? parseFloat(hM[1]) : 0,
    groups,
  };
};

/**
 * Builds a Gujarati character -> `interpolate-svg/svgs/barakhadi` file lookup map,
 * keeping the first match per glyph so primary base characters win over duplicates.
 */
const buildCharToInterpolateMap = (rootDir, barakhdi) => {
  const interpRoot = path.join(rootDir, "interpolate-svg/svgs/barakhadi");
  const map = {};
  if (!fs.existsSync(interpRoot)) return map;

  const entries = fs.readdirSync(interpRoot);
  for (const group of barakhdi) {
    const dirName = entries.find((d) => d.startsWith(`${group.id}_`));
    if (!dirName) continue;
    const dir = path.join(interpRoot, dirName);
    const files = fs.readdirSync(dir);
    for (const ch of group.chars) {
      const f = files.find((x) => new RegExp(`^${ch.id}_`).test(x));
      if (f && !map[ch.gu]) {
        map[ch.gu] = path.join(dir, f);
      }
    }
  }
  return map;
};

const flattenComponents = (components, charToInterp) => {
  const result = [];
  for (const c of components || []) {
    const stripped = c.replace(/\u0ACD$/, "");
    if (charToInterp[stripped]) result.push(stripped);
    else for (const sub of c.split(/\u0ACD/).filter(Boolean)) result.push(sub);
  }
  return result;
};

const buildCandidates = ({
  ci,
  compCount,
  rg,
  ref,
  baseDy,
  minX,
  minY,
  width,
  shapedGlyphs,
  normGlyphPolys,
  allPolys,
  consonantGlyphIndices,
  vowelGlyphIndices,
  exactGlyphSplit,
  isRephPattern,
}) => {
  if (rg.bb.y1 > 50 && vowelGlyphIndices.length > 0) {
    return vowelGlyphIndices.map((gi) => ({
      dx: shapedGlyphs[gi].bb.x1 - minX - rg.bb.x1,
      dy: shapedGlyphs[gi].bb.y1 - minY - rg.bb.y1,
      polys: normGlyphPolys[gi],
    }));
  }
  if (exactGlyphSplit || isRephPattern) {
    const gi = consonantGlyphIndices[isRephPattern ? ci - 1 : ci];
    return [
      {
        dx: shapedGlyphs[gi].bb.x1 - minX - rg.bb.x1,
        dy: baseDy - rg.bb.y1,
        polys: normGlyphPolys[gi],
      },
    ];
  }
  // Fused single-glyph ligatures: align first component left, last component right
  if (ci === 0) return [{ dx: -rg.bb.x1, dy: baseDy - rg.bb.y1, polys: allPolys }];
  if (ci === compCount - 1) {
    return [{ dx: width - ref.refW - rg.bb.x1, dy: baseDy - rg.bb.y1, polys: allPolys }];
  }
  return [{ dx: (width - ref.refW) / 2 - rg.bb.x1, dy: baseDy - rg.bb.y1, polys: allPolys }];
};

/**
 * Generates `resources/jodakshar/svgs-interpolate/` SVGs by pairing shaped Jodakshar
 * outlines (`g0p0`) with matching `gNsN` interpolated strokes copied from
 * `interpolate-svg/svgs/barakhadi/`. Unmatched or clipped stems are skipped.
 */
const generateJodaksharInterpolateSvg = async ({
  rootDir,
  resourcesDir,
  jodakshar,
  barakhdi,
  shaper,
  fontSize,
}) => {
  const dir = path.join(resourcesDir, "jodakshar/svgs-interpolate");
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
  const charToInterp = buildCharToInterpolateMap(rootDir, barakhdi);

  for (const item of jodakshar) {
    const cluster = item.cluster || item.gu;
    const fileName = `${item.id}_${(item.romanization || item.en || "")
      .replace(/[\s\/]+/g, "_")
      .toLowerCase()}.svg`;
    const outPath = path.join(dir, fileName);

    if (charToInterp[cluster]) {
      fs.copyFileSync(charToInterp[cluster], outPath);
      continue;
    }

    const shaped = await shaper.shapeTextGlyphs(cluster, fontSize);
    const rawBB = shaped.combinedPath.getBoundingBox();
    const minX = rawBB.x1;
    const minY = rawBB.y1;
    const width = Number((rawBB.x2 - minX).toFixed(4));
    const height = Number((rawBB.y2 - minY).toFixed(4));

    const normOutlineD = transformSvgPathD(
      shaped.combinedPath.toPathData(),
      IDENTITY_MATRIX,
      -minX,
      -minY
    );
    const normGlyphPolys = shaped.glyphs.map((g) =>
      flattenSvgPathPolys(transformSvgPathD(g.path.toPathData(), IDENTITY_MATRIX, -minX, -minY))
    );
    const allPolys = normGlyphPolys.flat();

    const comps = flattenComponents(item.components, charToInterp);
    const consonantGlyphIndices = [];
    const vowelGlyphIndices = [];
    let hasReph = false;

    shaped.glyphs.forEach((g, idx) => {
      if (g.name === "rephgujr") hasReph = true;
      else if (g.name.includes("vowel")) vowelGlyphIndices.push(idx);
      else consonantGlyphIndices.push(idx);
    });

    const isRephPattern =
      hasReph && comps[0] === "ર" && consonantGlyphIndices.length === comps.length - 1;
    const exactGlyphSplit = consonantGlyphIndices.length === comps.length;

    const matchedStrokes = [];
    const usedSlots = new Set();

    for (let ci = 0; ci < comps.length; ci++) {
      if (isRephPattern && ci === 0) continue;
      const cc = comps[ci];
      const refFile = charToInterp[cc];
      if (!refFile) continue;

      const ref = parseInterpolateSvgGroups(refFile);
      const compFontY1 = shaped.font
        .charToGlyph(cc[0])
        .getPath(0, shaped.ascender, shaped.fontSize)
        .getBoundingBox().y1;
      const baseDy = compFontY1 - minY;

      for (const rg of ref.groups) {
        const candidates = buildCandidates({
          ci,
          compCount: comps.length,
          rg,
          ref,
          baseDy,
          minX,
          minY,
          width,
          shapedGlyphs: shaped.glyphs,
          normGlyphPolys,
          allPolys,
          consonantGlyphIndices,
          vowelGlyphIndices,
          exactGlyphSplit,
          isRephPattern,
        });

        let best = null;
        for (const cand of candidates) {
          const slotKey = `${cc}:${Math.round(cand.dx / 5)},${Math.round(cand.dy / 5)}`;
          if (usedSlots.has(slotKey)) continue;

          const ratios = rg.strokes.map((s) =>
            strokeContainmentRatio(s.d, rg.mat, cand.dx, cand.dy, cand.polys)
          );
          const passing = ratios.filter((r) => r >= INSIDE_THRESHOLD).length;
          const sumRatio = ratios.reduce((a, b) => a + b, 0);
          if (
            !best ||
            passing > best.passing ||
            (passing === best.passing && sumRatio > best.sumRatio)
          ) {
            best = { ...cand, ratios, passing, sumRatio, slotKey };
          }
        }

        if (!best || best.passing === 0) continue;
        usedSlots.add(best.slotKey);

        rg.strokes.forEach((s, si) => {
          if (best.ratios[si] >= INSIDE_THRESHOLD) {
            matchedStrokes.push(transformSvgPathD(s.d, rg.mat, best.dx, best.dy));
          }
        });
      }
    }

    const strokeTags = matchedStrokes
      .map(
        (d, idx) =>
          `    <path id="g0s${idx}" inkscape:label="g0s${idx}" d="${d}" style="fill:none;stroke:#000000;stroke-width:1px;stroke-linecap:butt;stroke-linejoin:miter;stroke-opacity:1" />`
      )
      .join("\n");

    const svgOut = [
      `<?xml version="1.0" encoding="UTF-8" standalone="no"?>`,
      `<svg xmlns="http://www.w3.org/2000/svg" xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape" id="svg4" version="1.1" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}">`,
      `  <g id="g0" inkscape:label="g0">`,
      `    <path id="g0p0" inkscape:label="g0p0" d="${normOutlineD}" />`,
      strokeTags,
      `  </g>`,
      `</svg>`,
      "",
    ]
      .filter(Boolean)
      .join("\n");

    fs.writeFileSync(outPath, svgOut);
  }
};

/**
 * Mirrors Jodakshar stroke SVGs from Kano React Native app into `interpolate-svg/svgs/jodakshar`.
 */
const syncJodaksharFromKano = (rootDir, kanoJodaksharSvgsDir) => {
  if (!fs.existsSync(kanoJodaksharSvgsDir)) return;
  const interpolateDir = path.join(rootDir, "interpolate-svg/svgs/jodakshar");
  if (!fs.existsSync(interpolateDir)) {
    fs.mkdirSync(interpolateDir, { recursive: true });
  }
  for (const file of fs.readdirSync(kanoJodaksharSvgsDir)) {
    if (file.endsWith(".svg") || file.endsWith(".json")) {
      fs.copyFileSync(path.join(kanoJodaksharSvgsDir, file), path.join(interpolateDir, file));
    }
  }
};

module.exports = {
  parseInterpolateSvgGroups,
  buildCharToInterpolateMap,
  generateJodaksharInterpolateSvg,
  syncJodaksharFromKano,
};
