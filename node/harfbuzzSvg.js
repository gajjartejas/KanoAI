const fs = require("fs");
const opentype = require("opentype.js");

/**
 * Creates a HarfBuzz + OpenType shaper bound to a font file for GSUB/GPOS Indic shaping.
 */
const createHarfBuzzShaper = (fontFilePath, textToSVGFont) => {
  let hbContextPromise = null;

  const getHarfBuzzFont = () => {
    if (!hbContextPromise) {
      hbContextPromise = import("harfbuzzjs").then((hb) => {
        const fontData = fs.readFileSync(fontFilePath);
        const blob = new hb.Blob(fontData);
        const face = new hb.Face(blob);
        const hbFont = new hb.Font(face);
        return { hb, blob, face, hbFont };
      });
    }
    return hbContextPromise;
  };

  /**
   * Shapes an Indic/Gujarati text string via HarfBuzz and returns glyph outlines
   * and cumulative vector path from `opentype.js` at `fontSize`.
   */
  const shapeTextGlyphs = async (text, fontSize = 100, startX = 0, baselineY = null) => {
    const { hb, hbFont } = await getHarfBuzzFont();
    const fontScale = (1 / textToSVGFont.unitsPerEm) * fontSize;
    const ascender = textToSVGFont.ascender * fontScale;
    const yStart = baselineY === null ? ascender : baselineY;

    const buf = new hb.Buffer();
    buf.addText(text);
    buf.guessSegmentProperties();
    hb.shape(hbFont, buf);

    const infos = buf.getGlyphInfos();
    const positions = buf.getGlyphPositions();
    const totalAdvance = positions.reduce((sum, p) => sum + (p.xAdvance || 0), 0);

    const glyphs = [];
    const combinedPath = new opentype.Path();
    let xCursor = startX;
    let yCursor = yStart;

    for (let i = 0; i < infos.length; i++) {
      const glyph = textToSVGFont.glyphs.get(infos[i].codepoint);
      const pos = positions[i];
      const gx = xCursor + (pos.xOffset || 0) * fontScale;
      const gy = yCursor - (pos.yOffset || 0) * fontScale;
      const gPath = glyph.getPath(gx, gy, fontSize);
      combinedPath.extend(gPath);
      glyphs.push({
        name: glyph.name,
        path: gPath,
        bb: gPath.getBoundingBox(),
      });
      xCursor += (pos.xAdvance || 0) * fontScale;
      yCursor -= (pos.yAdvance || 0) * fontScale;
    }

    return {
      glyphs,
      combinedPath,
      font: textToSVGFont,
      fontSize,
      fontScale,
      ascender,
      height: (textToSVGFont.ascender - textToSVGFont.descender) * fontScale,
      advanceWidth: totalAdvance * fontScale,
    };
  };

  /**
   * Renders an Indic/Gujarati string as a shaped `<svg>` element matching `text-to-svg`
   * anchor and metric conventions while shaping conjuncts properly.
   */
  const getShapedSVG = async (text, svgOptions = {}) => {
    const fontSize = svgOptions.fontSize || 72;
    const fontScale = (1 / textToSVGFont.unitsPerEm) * fontSize;
    const ascender = textToSVGFont.ascender * fontScale;
    const height = (textToSVGFont.ascender - textToSVGFont.descender) * fontScale;

    const anchor = svgOptions.anchor || "";
    const preShape = await shapeTextGlyphs(text, fontSize, 0, ascender);
    let width = preShape.advanceWidth;

    let x = svgOptions.x || 0;
    if (/center/i.test(anchor)) x -= width / 2;
    else if (/right/i.test(anchor)) x -= width;

    let y = svgOptions.y || 0;
    if (/top/i.test(anchor)) y -= 0;
    else if (/middle/i.test(anchor)) y -= height / 2;
    else if (/bottom/i.test(anchor)) y -= height;
    else y -= ascender;

    const placed =
      x === 0 && y === 0 ? preShape : await shapeTextGlyphs(text, fontSize, x, y + ascender);
    const bbox = placed.combinedPath.getBoundingBox();
    if (Number.isFinite(bbox.x2) && bbox.x2 > width) {
      width = Number(bbox.x2.toFixed(2));
    }

    const attrString = Object.keys(svgOptions.attributes || {})
      .map((key) => `${key}="${svgOptions.attributes[key]}"`)
      .join(" ");
    const d = placed.combinedPath.toPathData();
    const pathTag = attrString ? `<path ${attrString} d="${d}"/>` : `<path d="${d}"/>`;

    return `<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="${width}" height="${height}">${pathTag}</svg>`;
  };

  return { shapeTextGlyphs, getShapedSVG };
};

module.exports = { createHarfBuzzShaper };
