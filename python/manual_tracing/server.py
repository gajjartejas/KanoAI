#!/usr/bin/env python3
"""Local-only manual SVG tracing studio; original assets are read-only."""
import argparse
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs

from geometry import groups, snap, export_svg

WEB = Path(__file__).parent / 'web'
DEFAULT_KANO = Path(__file__).resolve().parents[3] / 'Kano'


def catalog(kano):
    lang = kano / 'app/assets/lang'
    specs = [('Vowels', 'vowels/vowels.json'), ('Consonants', 'consonants/consonants.json'),
             ('Barakhadi', 'barakhadi/barakhadi.json'), ('Jodakshar', 'sections/jodakshar.json'),
             ('Numbers', 'numerals/numerals.json')]
    items = []
    for category, filename in specs:
        data = json.loads((lang/filename).read_text())
        rows = data.get('items', []) if isinstance(data, dict) else data
        for row in rows:
            for char in row.get('chars', [row]):
                relative = char.get('svg')
                if not relative:
                    continue
                path = (kano/'assets'/relative).resolve()
                if not path.is_relative_to((kano/'assets').resolve()) or not path.is_file():
                    raise ValueError(f'Missing asset: {relative}')
                items.append({'id': str(len(items)), 'category': category,
                              'label': char.get('gu', char.get('cluster', '')),
                              'name': char.get('en', char.get('romanization', '')),
                              'file': relative, 'path': path})
    return items


def serve(kano, port):
    items = catalog(kano)
    by_id = {item['id']: item for item in items}

    class Handler(BaseHTTPRequestHandler):
        def send(self, data, mime='application/json', status=200):
            body = data if isinstance(data, bytes) else (json.dumps(data).encode() if mime == 'application/json' else data.encode())
            self.send_response(status)
            self.send_header('Content-Type', mime+'; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            url = urlparse(self.path)
            try:
                if url.path == '/api/catalog':
                    self.send([{k: v for k, v in item.items() if k != 'path'} for item in items])
                elif url.path == '/api/character':
                    item = by_id[parse_qs(url.query)['id'][0]]
                    source = item['path'].read_text()
                    _, entries = groups(source)
                    self.send({'svg': source, 'groups': [g[0] for g in entries]})
                elif url.path in ('/', '/index.html', '/app.js', '/style.css'):
                    filename = 'index.html' if url.path == '/' else url.path[1:]
                    mime = {'html': 'text/html', 'js': 'text/javascript', 'css': 'text/css'}[filename.split('.')[-1]]
                    self.send((WEB/filename).read_bytes(), mime)
                else:
                    self.send({'error': 'Not found'}, status=404)
            except (ValueError, KeyError, OSError) as error:
                self.send({'error': str(error)}, status=400)

        def do_POST(self):
            # Reject cross-origin browser requests; bind only to loopback.
            origin = self.headers.get('Origin')
            if origin and origin != f'http://{self.headers.get("Host")}':
                self.send({'error': 'Cross-origin request rejected'}, status=403)
                return
            try:
                length = int(self.headers.get('Content-Length', '0'))
                if not 0 < length <= 2_000_000:
                    raise ValueError('Request exceeds limit.')
                data = json.loads(self.rfile.read(length))
                source = by_id[data['id']]['path'].read_text()
                if self.path == '/api/snap':
                    self.send(snap(source, data['group'], data['points'], data.get('accuracy', 90)))
                elif self.path == '/api/export':
                    self.send({'svg': export_svg(source, data['strokes'])})
                else:
                    self.send({'error': 'Not found'}, status=404)
            except (ValueError, KeyError, TypeError, IndexError) as error:
                self.send({'error': str(error)}, status=400)

    print(f'Manual tracing studio: http://127.0.0.1:{port} ({len(items)} entries)', flush=True)
    HTTPServer(('127.0.0.1', port), Handler).serve_forever()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--kano', type=Path, default=DEFAULT_KANO)
    parser.add_argument('--port', type=int, default=8090)
    args = parser.parse_args()
    serve(args.kano.resolve(), args.port)
