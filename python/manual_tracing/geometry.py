"""User-guided medial-axis routing. Accuracy is bounded, never advertised as exact."""
from functools import lru_cache
import heapq
import math
import re
import xml.etree.ElementTree as ET

import numpy as np
from PIL import Image, ImageDraw
from scipy.spatial import cKDTree
from skimage.morphology import medial_axis
from svgpathtools import parse_path

SVG = 'http://www.w3.org/2000/svg'
INK = 'http://www.inkscape.org/namespaces/inkscape'
ET.register_namespace('', SVG)
ET.register_namespace('inkscape', INK)


def groups(source):
    root = ET.fromstring(source)
    result = []
    for group in root.iter(f'{{{SVG}}}g'):
        gid = group.get('id', '')
        outlines = [p for p in group.findall(f'{{{SVG}}}path')
                    if re.fullmatch(r'g\d+p\d+', p.get('id', ''))]
        if outlines:
            result.append((gid, group, outlines))
    if not result:
        raise ValueError('No Kano outline groups found in SVG.')
    return root, result


@lru_cache(maxsize=8)
def center_graph(source, gid):
    _, entries = groups(source)
    entry = next((e for e in entries if e[0] == gid), None)
    if entry is None:
        raise ValueError('Unknown outline group.')
    paths = [parse_path(p.get('d')) for p in entry[2]]
    boxes = [p.bbox() for p in paths]
    x0, x1 = min(b[0] for b in boxes), max(b[1] for b in boxes)
    y0, y1 = min(b[2] for b in boxes), max(b[3] for b in boxes)
    scale = 1536 / max(x1-x0, y1-y0, 1)
    origin = np.array([x0-4/scale, y0-4/scale])
    shape = (math.ceil((x1-x0)*scale)+9, math.ceil((y1-y0)*scale)+9)
    mask = np.zeros(shape[::-1], dtype=bool)
    # Preserve nonzero winding (default SVG fill rule) and counter holes.
    for element, path in zip(entry[2], paths):
        winding = np.zeros(shape[::-1], dtype=np.int16)
        parity = np.zeros_like(mask)
        for contour in path.continuous_subpaths():
            pts = []
            for seg in contour:
                count = max(2, math.ceil(seg.length()*scale/1.5))
                pts.extend((z.real, z.imag) for z in (seg.point(t) for t in np.linspace(0, 1, count)))
            pts = (np.asarray(pts)-origin)*scale
            image = Image.new('1', shape)
            ImageDraw.Draw(image).polygon([tuple(p) for p in pts], fill=1)
            part = np.asarray(image, dtype=bool)
            signed = np.sum(pts[:, 0]*np.roll(pts[:, 1], -1)-np.roll(pts[:, 0], -1)*pts[:, 1])
            winding += part.astype(np.int16)*(1 if signed >= 0 else -1)
            parity ^= part
        evenodd = element.get('fill-rule') == 'evenodd' or 'fill-rule:evenodd' in element.get('style', '').replace(' ', '')
        mask |= parity if evenodd else winding != 0
    skeleton = medial_axis(mask, rng=0)
    pixels = np.argwhere(skeleton)[:, ::-1]
    if not len(pixels):
        raise ValueError('Outline has no usable centerline.')
    lookup = {tuple(p): i for i, p in enumerate(pixels)}
    neighbors = []
    for x, y in pixels:
        neighbors.append([(lookup[(x+dx, y+dy)], math.hypot(dx, dy))
                          for dx in (-1, 0, 1) for dy in (-1, 0, 1)
                          if (dx or dy) and (x+dx, y+dy) in lookup])
    return pixels/scale+origin, neighbors, cKDTree(pixels/scale+origin), scale, mask, origin


def simplify(points, tolerance):
    """RDP with a bound on displacement from the unsimplified centerline."""
    if len(points) < 3:
        return points
    keep = {0, len(points)-1}
    pending = [(0, len(points)-1)]
    while pending:
        start, end = pending.pop()
        if end-start < 2:
            continue
        subset = points[start:end+1]
        a, b = subset[0], subset[-1]
        delta = b-a
        t = np.clip(((subset-a)@delta)/max(delta@delta, 1e-20), 0, 1)
        distances = np.linalg.norm(subset-(a+t[:, None]*delta), axis=1)
        index = int(np.argmax(distances))
        if distances[index] > tolerance:
            split = start+index
            keep.add(split)
            pending.extend(((start, split), (split, end)))
    return points[sorted(keep)]


def turn_samples(points, extent, tree):
    """Protect compact reversals whose two sides collapse to one medial branch.

    A filled stroke join does not encode the two sides of a handwriting turn.
    Keep that local manual geometry rather than pretending its skeleton is unique.
    """
    lengths = np.r_[0, np.cumsum(np.linalg.norm(np.diff(points, axis=0), axis=1))]
    unique = np.r_[True, np.diff(lengths) > 1e-10]
    lengths, points = lengths[unique], points[unique]
    if lengths[-1] <= 1e-8:
        raise ValueError('Stroke is too short. Draw along the outline.')
    count = min(6000, max(2, math.ceil(lengths[-1]/(extent/600))+1))
    positions = np.linspace(0, lengths[-1], count)
    dense = np.column_stack([np.interp(positions, lengths, points[:, axis]) for axis in (0, 1)])
    step = lengths[-1]/(count-1)
    _, indices = tree.query(dense)
    snapped = tree.data[indices]
    weights = np.zeros(count)
    for fraction in (.018, .035, .06):
        radius = max(2, round(extent*fraction/step))
        for i in range(radius, count-radius):
            incoming = dense[i]-dense[i-radius]
            outgoing = dense[i+radius]-dense[i]
            norm = np.linalg.norm(incoming)*np.linalg.norm(outgoing)
            # A sharp reversal, with distinct manual sides mapped onto the same branch.
            if norm < 1e-12 or incoming@outgoing/norm > -.15:
                continue
            separation = np.linalg.norm(dense[i-radius]-dense[i+radius])
            collapsed = np.linalg.norm(snapped[i-radius]-snapped[i+radius])
            if separation < extent*.003 or collapsed > separation*.65:
                continue
            for j in range(max(0, i-2*radius), min(count, i+2*radius+1)):
                weight = min(1, max(0, 2-abs(j-i)/radius))
                weights[j] = max(weights[j], weight)
    protected = weights > 0
    runs = int(np.sum(protected & ~np.r_[False, protected[:-1]]))
    return dense, indices, weights, runs


def snap(source, gid, raw, accuracy=90):
    points = np.asarray(raw, dtype=float)
    if points.ndim != 2 or points.shape[1] != 2 or not 2 <= len(points) <= 6000 or not np.isfinite(points).all():
        raise ValueError('Draw a stroke with 2–6000 finite points.')
    nodes, edges, tree, scale, mask, origin = center_graph(source, gid)
    extent = max(np.ptp(nodes, axis=0))
    distances, indices = tree.query(points)
    if np.max(distances) > extent*.12:
        raise ValueError('Stroke is too far from this group. Select the correct group or retry closer to the outline.')
    points, indices, weights, preserved_turns = turn_samples(points, extent, tree)
    local = nodes[indices]*(1-weights[:, None])+points*weights[:, None]
    route = [local[0]]
    for i in range(1, len(points)):
        if weights[i] > 0 or weights[i-1] > 0:
            route.append(local[i])
            continue
        start, target = int(indices[i-1]), int(indices[i])
        if start == target:
            continue
        queue, costs, previous = [(0, start)], {start: 0}, {}
        while queue:
            cost, node = heapq.heappop(queue)
            if cost != costs[node]:
                continue
            if node == target:
                break
            for nxt, distance in edges[node]:
                candidate = cost+distance
                if candidate < costs.get(nxt, float('inf')):
                    costs[nxt], previous[nxt] = candidate, node
                    heapq.heappush(queue, (candidate, nxt))
        if target not in costs:
            raise ValueError('Stroke crosses disconnected outlines. Lift and draw each disconnected part separately.')
        chain = [target]
        while chain[-1] != start:
            chain.append(previous[chain[-1]])
        route.extend(nodes[index] for index in reversed(chain[:-1]))
    if len(route) < 3:
        raise ValueError('Stroke is too short. Draw along the outline.')
    centered = np.asarray(route)
    def inside(polyline):
        for a, b in zip(polyline, polyline[1:]):
            samples = np.linspace(a, b, max(2, math.ceil(np.linalg.norm(b-a)*scale*2)))
            pixel = np.rint((samples-origin)*scale).astype(int)
            if ((pixel < 0).any() or (pixel[:, 0] >= mask.shape[1]).any()
                    or (pixel[:, 1] >= mask.shape[0]).any()
                    or not mask[pixel[:, 1], pixel[:, 0]].all()):
                return False
        return True
    if not inside(centered):
        raise ValueError('The preserved turn leaves the outline. Retry this turn inside the highlighted glyph.')
    tolerance = extent*(.00015+.0025*(1-float(np.clip(accuracy, 0, 100))/100))
    optimized = simplify(centered, tolerance)
    # Keep optimization from flattening a protected turn, even at low accuracy.
    if preserved_turns:
        optimized = simplify(centered, min(tolerance, extent*.00015))
    if not inside(optimized):
        optimized = centered
    d = 'M '+' L '.join(f'{x:.5f},{y:.5f}' for x, y in optimized)
    return {'d': d, 'preservedTurns': preserved_turns, 'points': len(optimized), 'tolerance': round(tolerance, 5),
            'rasterError': round(math.sqrt(2)/scale, 5),
            'maxCorrection': round(float(np.max(distances)), 3)}


def export_svg(source, strokes):
    root, entries = groups(source)
    known = {e[0] for e in entries}
    if not strokes or any(s.get('group') not in known for s in strokes):
        raise ValueError('Draw at least one stroke in a valid group.')
    for gid, group, _ in entries:
        for child in list(group):
            if re.fullmatch(r'g\d+s\d+', child.get('id', '')):
                group.remove(child)
        for index, stroke in enumerate(s for s in strokes if s['group'] == gid):
            d = stroke['d']
            path = parse_path(d)
            if not path or not math.isfinite(path.length()):
                raise ValueError('Invalid stroke path.')
            label = f'{gid}s{index}'
            ET.SubElement(group, f'{{{SVG}}}path', {'id': label, f'{{{INK}}}label': label,
                          'd': d, 'fill': 'none', 'stroke': '#000000', 'stroke-width': '1',
                          'stroke-linecap': 'round', 'stroke-linejoin': 'round'})
    return ET.tostring(root, encoding='unicode')
