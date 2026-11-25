const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const { svgPathProperties } = require("svg-path-properties");

const { parseTransformMatrix, transformSvgPathD } = require("./svgGeometry");
const { generateResources } = require("./index");

const ROOT_DIR = path.resolve(__dirname, "..");
const JODAKSHAR_JSON = path.join(ROOT_DIR, "resources/jodakshar/jodakshar.json");
const SVGS_DIR = path.join(ROOT_DIR, "resources/jodakshar/svgs");
const SVGS_INTERP_DIR = path.join(ROOT_DIR, "resources/jodakshar/svgs-interpolate");

test("transformSvgPathD preserves relative segments and affine transforms", () => {
  const mat = parseTransformMatrix("translate(5,-5)");
  const out = transformSvgPathD("m 10,20 c 1,2 3,4 5,6 z", mat, 2, 3);
  assert.equal(out, "M 17,18 C 18,20 20,22 22,24 Z");
});

test("generateResources produces all 62 shaped Jodakshar SVGs and interpolate SVGs", async () => {
  await generateResources();

  const items = JSON.parse(fs.readFileSync(JODAKSHAR_JSON, "utf8")).items;
  assert.equal(items.length, 62);
  assert.equal(fs.existsSync(path.join(ROOT_DIR, "resources/jodakshar/kano_svgs")), false);

  for (const item of items) {
    const fileName = `${item.id}_${item.romanization.toLowerCase()}.svg`;

    const rawSvg = fs.readFileSync(path.join(SVGS_DIR, fileName), "utf8");
    assert.match(rawSvg, /^<svg\b[^>]*><path d="M[^"]+"\/><\/svg>$/);

    const interpSvg = fs.readFileSync(path.join(SVGS_INTERP_DIR, fileName), "utf8");
    assert.match(interpSvg, /<svg\b[^>]*id="svg4"/);
    assert.match(interpSvg, /<g\b[^>]*id="g0"/);
    assert.match(interpSvg, /inkscape:label="g0p0"/);

    for (const [, attrs] of interpSvg.matchAll(/<path\b([^>]+)\/?>/g)) {
      const label = attrs.match(/\binkscape:label="([^"]+)"/);
      const d = attrs.match(/\bd="([^"]+)"/);
      assert.ok(label && d, `${fileName} path missing inkscape:label or d`);
      assert.ok(Number.isFinite(new svgPathProperties(d[1]).getTotalLength()));
    }
  }
});
