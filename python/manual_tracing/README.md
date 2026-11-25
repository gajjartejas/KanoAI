# Manual tracing studio

A local, non-destructive authoring tool for Kano SVG center strokes. Select vowels,
consonants, Barakhadi, Jodakshar or numbers from the **current Kano datasets**. Trace
characters one at a time, correct the path, preview its animation, then download.
No source assets are overwritten, and no cloud service receives drawings.

From the generator repository:

```sh
.venv/bin/python -m pip install -r python/manual_tracing/requirements.txt
.venv/bin/python python/manual_tracing/server.py
```

Open `http://127.0.0.1:8090`. The default asset source is sibling `../Kano`.
Use `--kano /path/to/Kano --port 8090` for another checkout.

## Workflow

1. Select categories/characters and start. Selection order follows Kano's datasets.
2. Select the SVG outline group, then draw one stroke per gesture in writing order.
   Each group is independently centered; lift between disconnected components.
3. Inspect the corrected green line; optionally overlay your original orange line.
   Retry/undo removes the last stroke. Clear resets the current character only.
4. Adjust **Path accuracy** and click **Apply to all strokes**. Higher values reduce
   simplification tolerance; they do not change the original glyph or stroke order.
5. Replay the animation. Review starts, ends, intersections and coverage. Kano plays
   groups in document order and strokes in their order inside each group.
6. Download at any step, or download through a particular stroke. Partial downloads
   are drafts. Mark reviewed and accept to continue. Original SVG filenames remain
   unchanged so reviewed files can replace canonical Kano assets directly.

Drafts save to this browser's local storage by asset path (shared between a vowel
and its identical Barakhadi asset). Export an editable JSON session for backup.
Changing port/browser changes local storage. Downloaded SVGs preserve original
outline geometry, dimensions, group transforms, IDs and Inkscape labels; old `gNsN`
paths are replaced by the new ordered paths. Run Kano's asset synchronization after
manually installing reviewed files. No application metadata is modified here.

## Accuracy contract

**100% geometric or pedagogical accuracy is not guaranteed.** Arbitrary hand drawn
paths do not uniquely determine the intended centerline at crossings or broad joins.
This tool uses a deterministic high-resolution Euclidean medial axis and connects
ordered waypoints from your gesture on that axis. A 1536-pixel longest group dimension
bounds raster uncertainty; the displayed value is in original SVG units. Holes use
SVG's nonzero winding rule (or explicit even-odd). Connected routing avoids jumps
across holes/disconnected ink. Ramer–Douglas–Peucker simplification uses the displayed
error tolerance; if simplification leaves the ink mask, the dense route is retained.
These are numerical bounds on the raster approximation, not proof of correspondence
to an ideal vector medial axis. Endpoint cap branches and crossings require review.

The user supplies **stroke order and direction**. Snapping is not handwriting-order
inference. Very distant gestures are rejected; ambiguous nearby branches may still
need retry. A reviewed checkbox is human sign-off, not an automated accuracy score.
The original vector outlines always remain exact.

Compact U-turns in filled joins can collapse onto a single medial-axis branch.
The studio detects those reversals at multiple scales, preserves the local manual
turn with a tapered transition back onto the centered path, and verifies every
segment stays inside the glyph mask. These regions are explicitly flagged for
centering review; they are not claimed to be medial-axis accurate. Low accuracy
settings cannot simplify away these protected turns. To update an older draft,
click **Apply to all strokes**; its saved original gestures are reused.

## Tests

```sh
.venv/bin/python -m unittest discover -s python/manual_tracing/tests -v
node --check python/manual_tracing/web/app.js
```
