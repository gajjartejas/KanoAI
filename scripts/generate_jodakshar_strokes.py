#!/usr/bin/env python3
"""Shape conjunct outlines and extract connected, hole-preserving center paths.
Existing hand-authored assets are retained. New paths are skeleton guides, not a
claim of canonical pedagogical pen order. Emits Kano's gNpN / gNsN format.
"""
import argparse
import json
import math
import sys
from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np
from scipy.ndimage import distance_transform_edt
from svgpathtools import Path as SvgPath, parse_path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'python/char_stroke_generation'))
from stroke_generator.font.shaping import shape_text_with_harfbuzz
from stroke_generator.core.bezier import resample_polyline

SCALE = 10
PAD = 4
NS = 'http://www.inkscape.org/namespaces/inkscape'

def skeletonize(mask):
    """Zhang-Suen topology-preserving thinning, vectorized over a padded mask."""
    image = np.pad(mask, 1).astype(np.uint8)
    while True:
        changed = False
        for phase in (0, 1):
            p = [image[:-2,1:-1], image[:-2,2:], image[1:-1,2:], image[2:,2:], image[2:,1:-1], image[2:,:-2], image[1:-1,:-2], image[:-2,:-2]]
            count = sum(p)
            changes = sum(((p[i] == 0) & (p[(i+1)%8] == 1)).astype(np.uint8) for i in range(8))
            if phase == 0:
                preserve = (p[0]*p[2]*p[4] == 0) & (p[2]*p[4]*p[6] == 0)
            else:
                preserve = (p[0]*p[2]*p[6] == 0) & (p[0]*p[4]*p[6] == 0)
            remove = (image[1:-1,1:-1] == 1) & (count >= 2) & (count <= 6) & (changes == 1) & preserve
            if remove.any():
                image[1:-1,1:-1][remove] = 0
                changed = True
        if not changed:
            return image[1:-1,1:-1].astype(bool)

def raster(path, width, height):
    mask = np.zeros((height, width), dtype=bool)
    for sub in path.continuous_subpaths():
        points = []
        for seg in sub:
            count = max(8, math.ceil(seg.length() * SCALE / 2))
            points.extend(((p.real + PAD) * SCALE, (p.imag + PAD) * SCALE) for p in (seg.point(t) for t in np.linspace(0, 1, count)))
        image = Image.new('1', (width, height))
        ImageDraw.Draw(image).polygon(points, fill=1)
        mask ^= np.asarray(image, dtype=bool)
    return mask

def trace_graph(mask):
    pixels = set(map(tuple, np.argwhere(skeletonize(mask))))
    graph = {}
    for y, x in pixels:
        neighbors = []
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                q = (y + dy, x + dx)
                if (dy or dx) and q in pixels:
                    if dy and dx and ((y + dy, x) in pixels or (y, x + dx) in pixels):
                        continue
                    neighbors.append(q)
        graph[(y, x)] = neighbors
    used = set()
    paths = []
    nodes = sorted(graph, key=lambda p: (len(graph[p]) == 2, p))
    for start in nodes:
        for nxt in graph[start]:
            edge = frozenset((start, nxt))
            if edge in used:
                continue
            used.add(edge)
            chain = [start, nxt]
            while len(graph[chain[-1]]) == 2:
                following = next(p for p in graph[chain[-1]] if p != chain[-2])
                edge = frozenset((chain[-1], following))
                if edge in used:
                    break
                used.add(edge)
                chain.append(following)
            paths.append(chain)
    # Remove short terminal corner spurs, while retaining independent short marks.
    distance = distance_transform_edt(mask)
    retained = []
    for chain in paths:
        length = sum(math.dist(a,b) for a,b in zip(chain,chain[1:]))
        terminal = len(graph[chain[0]]) == 1 or len(graph[chain[-1]]) == 1
        junctions = [p for p in (chain[0],chain[-1]) if len(graph[p]) >= 3]
        if terminal and junctions and length < 2.1 * max(distance[p] for p in junctions):
            continue
        retained.append(chain)
    paths = retained
    # Pair branches at junctions by tangent continuity rather than jumping gaps.
    while True:
        best = None
        for i, a in enumerate(paths):
            for j in range(i + 1, len(paths)):
                b = paths[j]
                for flip_a in (False, True):
                    aa = a[::-1] if flip_a else a
                    for flip_b in (False, True):
                        bb = b[::-1] if flip_b else b
                        if aa[-1] != bb[0]:
                            continue
                        v = np.array(aa[-1]) - np.array(aa[max(0, len(aa)-10)])
                        w = np.array(bb[min(9, len(bb)-1)]) - np.array(bb[0])
                        cosine = float(v @ w / max(1, np.linalg.norm(v) * np.linalg.norm(w)))
                        if cosine > 0.15 and (best is None or cosine > best[0]):
                            best = (cosine, i, j, aa + bb[1:])
        if best is None:
            break
        _, i, j, merged = best
        paths[i] = merged
        paths.pop(j)
    # Tiny junction artifacts have no meaningful drawable extent.
    return [p for p in paths if len(p) >= 5]

def generate(item, font, destination):
    glyphs = shape_text_with_harfbuzz(str(font), item['cluster'])
    combined = SvgPath(*[seg for g in glyphs for seg in g.local_path.translated(complex(g.global_pos_x, g.global_pos_y))])
    left, right, top, bottom = combined.bbox()
    outline = combined.translated(complex(-left, -top))
    w, h = right-left, bottom-top
    mask = raster(outline, math.ceil((w+2*PAD)*SCALE)+1, math.ceil((h+2*PAD)*SCALE)+1)
    chains = trace_graph(mask)
    paths = []
    for chain in chains:
        points = np.array([(x/SCALE, y/SCALE) for y,x in chain])
        if tuple(points[-1][::-1]) < tuple(points[0][::-1]):
            points = points[::-1]
        # Fine linear sampling stays on the medial ridge; cubic smoothing can overshoot holes.
        points = resample_polyline(points, max(3, math.ceil(len(chain)/3)))
        paths.append(points)
    paths.sort(key=lambda points: (round(points[:,0].mean()/12), points[0,1]))
    root = ET.Element('svg', {'xmlns':'http://www.w3.org/2000/svg', 'xmlns:inkscape':NS, 'id':'svg4', 'width':f'{w+2*PAD:.4f}', 'height':f'{h+2*PAD:.4f}', 'viewBox':f'0 0 {w+2*PAD:.4f} {h+2*PAD:.4f}'})
    group = ET.SubElement(root,'g',{'id':'g0','inkscape:label':'g0'})
    ET.SubElement(group,'path',{'id':'g0p0','inkscape:label':'g0p0','d':outline.translated(complex(PAD,PAD)).d()})
    total = 0
    inside = []
    for i,points in enumerate(paths):
        d = 'M '+' L '.join(f'{x:.3f},{y:.3f}' for x,y in points)
        total += parse_path(d).length()
        for x,y in points:
            inside.append(bool(mask[min(mask.shape[0]-1,round(y*SCALE)),min(mask.shape[1]-1,round(x*SCALE))]))
        ET.SubElement(group,'path',{'id':f'g0s{i}','inkscape:label':f'g0s{i}','d':d,'style':'fill:none;stroke:#000000;stroke-width:1;stroke-linecap:round;stroke-linejoin:round'})
    if not paths or np.mean(inside) < 0.99:
        raise ValueError(f"Invalid guides for {item['cluster']}")
    ET.indent(root)
    ET.ElementTree(root).write(destination,encoding='utf-8',xml_declaration=True)
    return {'strokes':len(paths),'insideRatio':round(float(np.mean(inside)),5),'totalLength':round(total,3)}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--app', type=Path, required=True)
    parser.add_argument('--missing-only', action='store_true', help='Only generate missing SVGs')
    args = parser.parse_args()
    app = args.app.resolve()
    source = app / 'app/assets/lang/sections/jodakshar.json'
    data = json.loads(source.read_text())
    output = app / 'assets/svgs/jodakshar'
    output.mkdir(parents=True, exist_ok=True)
    validation_path = output / 'validation.json'
    existing_reports = {}
    if validation_path.exists():
        try:
            for r in json.loads(validation_path.read_text()):
                existing_reports[r['id']] = r
        except Exception:
            pass
    report = []
    for item in data['items']:
        if item['id'] in (6, 7):
            report.append({'id': item['id'], 'cluster': item['cluster'], 'source': 'existing-manual'})
            continue
        relative = f"svgs/jodakshar/{item['id']}_{item['romanization']}.svg"
        dest = app / 'assets' / relative
        if args.missing_only and dest.exists() and item.get('total_length'):
            rep = existing_reports.get(item['id'], {
                'id': item['id'],
                'cluster': item['cluster'],
                'source': 'shaped-medial-skeleton',
                'strokes': item.get('groups', 1),
                'totalLength': item['total_length'],
            })
            report.append(rep)
            continue
        result = generate(item, app / 'assets/fonts/NotoSansGujarati-Regular.ttf', dest)
        item.update(svg=relative, total_length=result['totalLength'], groups=1)
        rep = {'id': item['id'], 'cluster': item['cluster'], 'source': 'shaped-medial-skeleton', **result}
        report.append(rep)
        existing_reports[item['id']] = rep
    source.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    validation_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(f'Processed {len(report)} Jodakshar SVGs (validation updated).')
if __name__=='__main__':
    main()
