import sys
import unittest
from pathlib import Path
import numpy as np
from svgpathtools import parse_path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from geometry import SVG, INK, groups, snap, export_svg, center_graph
from server import catalog, DEFAULT_KANO


def fixture(outline, extra=''):
    return f'<svg xmlns="{SVG}" xmlns:inkscape="{INK}" width="100" height="100"><g id="g0"><path id="g0p0" inkscape:label="g0p0" d="{outline}"/>{extra}</g></svg>'


class CenteringTests(unittest.TestCase):
    def test_offset_line_is_centered_and_direction_preserved(self):
        source = fixture('M0,0 H100 V20 H0 Z')
        result = snap(source, 'g0', [[12, 6], [30, 7], [50, 6], [70, 8], [88, 7]])
        path = parse_path(result['d'])
        samples = [path.point(t) for t in np.linspace(0, 1, 50)]
        self.assertLess(max(abs(p.imag-10) for p in samples), .15)
        self.assertLess(samples[0].real, samples[-1].real)
        reverse = parse_path(snap(source, 'g0', [[88, 7], [60, 8], [30, 6], [12, 6]])['d'])
        self.assertGreater(reverse.start.real, reverse.end.real)

    def test_hole_is_not_crossed(self):
        source = fixture('M0,0 H100 V100 H0 Z M20,20 V80 H80 V20 Z')
        result = snap(source, 'g0', [[10, 30], [10, 70], [25, 90], [70, 90], [90, 70], [90, 30]])
        path = parse_path(result['d'])
        for t in np.linspace(0, 1, 300):
            p = path.point(t)
            self.assertFalse(21 < p.real < 79 and 21 < p.imag < 79)

    def test_disconnected_stroke_rejected(self):
        source = fixture('M0,0 H40 V20 H0 Z M60,0 H100 V20 H60 Z')
        with self.assertRaisesRegex(ValueError, 'disconnected'):
            snap(source, 'g0', [[15, 10], [30, 10], [65, 10], [85, 10]])

    def test_invalid_and_far_input_rejected(self):
        source = fixture('M0,0 H100 V20 H0 Z')
        for points in ([[0, 0]], [[float('nan'), 0], [1, 2]], [[1000, 1000], [1100, 1000]]):
            with self.assertRaises(ValueError):
                snap(source, 'g0', points)

    def test_accuracy_slider_reduces_tolerance(self):
        source = fixture('M0,0 H100 V100 H0 Z M20,20 V80 H80 V20 Z')
        raw = [[10, 30], [10, 70], [30, 90], [70, 90], [90, 70]]
        high, low = snap(source, 'g0', raw, 100), snap(source, 'g0', raw, 0)
        self.assertLess(high['tolerance'], low['tolerance'])
        self.assertGreaterEqual(high['points'], low['points'])

    def test_export_keeps_outlines_labels_and_replaces_strokes(self):
        source = fixture('M0,0 H100 V20 H0 Z', '<path id="g0s0" d="M1,1 L2,2"/>')
        result = snap(source, 'g0', [[12, 7], [50, 8], [88, 6]])
        exported = export_svg(source, [{'group': 'g0', **result}])
        root, entries = groups(exported)
        self.assertEqual(root.get('width'), '100')
        self.assertEqual(entries[0][2][0].get('d'), 'M0,0 H100 V20 H0 Z')
        strokes = entries[0][1].findall(f'{{{SVG}}}path')[1:]
        self.assertEqual(len(strokes), 1)
        self.assertEqual(strokes[0].get(f'{{{INK}}}label'), 'g0s0')
        self.assertEqual(strokes[0].get('d'), result['d'])

    def test_filled_hairpin_keeps_two_sides_at_every_accuracy(self):
        source = fixture('M0,0 H100 V20 H0 Z')
        raw = ([[x, 7] for x in np.linspace(60, 40, 60)]
               + [[40+3*np.cos(t), 10+3*np.sin(t)]
                  for t in np.linspace(-np.pi/2, -3*np.pi/2, 60)]
               + [[x, 13] for x in np.linspace(40, 65, 70)])
        for accuracy in (0, 90, 100):
            for gesture in (raw, raw[::-1]):
                result = snap(source, 'g0', gesture, accuracy)
                path = parse_path(result['d'])
                self.assertGreater(result['preservedTurns'], 0)
                x0, x1, y0, y1 = path.bbox()
                self.assertLess(x0, 38)
                self.assertLess(y0, 8)
                self.assertGreater(y1, 12)
                # The separated arms survive export, not only an on-screen overlay.
                exported = export_svg(source, [{'group': 'g0', **result}])
                self.assertIn(result['d'], exported)

    def test_gujarati_a_reference_preserves_small_return_loop(self):
        source = (DEFAULT_KANO/'assets/svgs/barakhadi/0_aa/0_aa.svg').read_text()
        _, entries = groups(source)
        reference = next(p for p in entries[0][1].findall(f'{{{SVG}}}path') if p.get('id') == 'g0s0')
        path = parse_path(reference.get('d'))
        raw = [[z.real, z.imag] for z in (path.point(t) for t in np.linspace(0, 1, 700))]
        result = snap(source, 'g0', raw, 0)
        self.assertGreater(result['preservedTurns'], 0)
        corrected = parse_path(result['d'])
        loop = [z.imag for z in (corrected.point(t) for t in np.linspace(0, 1, 3000))
                if 4 < z.real < 7 and 28 < z.imag < 35]
        self.assertGreater(max(loop)-min(loop), 2)

    def test_catalog_all_assets_have_kano_groups(self):
        entries = catalog(DEFAULT_KANO)
        self.assertEqual({x['category'] for x in entries}, {'Vowels', 'Consonants', 'Barakhadi', 'Jodakshar', 'Numbers'})
        for item in entries:
            root, outlines = groups(item['path'].read_text())
            for gid, group, paths in outlines:
                self.assertTrue(paths, item['file'])
                for path in paths:
                    self.assertEqual(path.get(f'{{{INK}}}label'), path.get('id'), item['file'])


if __name__ == '__main__':
    unittest.main()
