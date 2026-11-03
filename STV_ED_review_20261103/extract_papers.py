from pathlib import Path
import json
from pypdf import PdfReader

root = Path(__file__).resolve().parent / 'tmp' / 'papers'
manifest = []
for path in sorted(root.glob('*.pdf')):
    reader = PdfReader(path)
    pages = [p.extract_text(extraction_mode='layout') for p in reader.pages]
    (root / (path.stem + '.txt')).write_text('\n\n'.join(f'[PDF PAGE {i}]\n{text}' for i, text in enumerate(pages, 1)), encoding='utf-8')
    (root / (path.stem + '_pages.json')).write_text(json.dumps(pages, ensure_ascii=False), encoding='utf-8')
    manifest.append({'name': path.stem, 'pages': len(pages), 'characters': sum(map(len, pages))})
print(json.dumps(manifest, indent=2))
