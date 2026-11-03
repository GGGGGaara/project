"""Download public author copies for private literature inspection, not redistribution."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.request import Request, urlopen
import json
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'tmp' / 'sources'
OUT.mkdir(parents=True, exist_ok=True)
SOURCES = {
    'itsc2020_proactive': 'https://www-sop.inria.fr/members/Philippe.Martinet/publis/2020/ITSC20maria.pdf',
    'icsr2015_waiting': 'https://www.tu-ilmenau.de/fileadmin/Bereiche/IA/neurob/Publikationen/conferences_int/2015/Trinh-ICSR-2015.pdf',
    'gross2017_hospital': 'https://www.tu-ilmenau.de/fileadmin/Bereiche/IA/neurob/Publikationen/journals/Gross-AR-2017.pdf',
}

def inspect(item):
    key, url = item
    path = OUT / (key + '.pdf')
    try:
        if not path.exists():
            request = Request(url, headers={'User-Agent': 'Mozilla/5.0 (research reading)'})
            with urlopen(request, timeout=30) as response:
                data = response.read()
            if not data.startswith(b'%PDF'):
                raise ValueError('Response is not a PDF')
            path.write_bytes(data)
        reader = PdfReader(path)
        pages = [page.extract_text() or '' for page in reader.pages]
        (OUT / (key + '.txt')).write_text('\n\n'.join(f'=== PAGE {i+1} ===\n{text}' for i, text in enumerate(pages)), encoding='utf-8')
        return {'id': key, 'url': url, 'pages': len(pages), 'bytes': path.stat().st_size, 'status': 'readable'}
    except Exception as exc:
        return {'id': key, 'url': url, 'status': 'failed', 'error': str(exc)}

if __name__ == '__main__':
    with ThreadPoolExecutor(max_workers=3) as pool:
        result = list(pool.map(inspect, SOURCES.items()))
    (OUT / 'manifest.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=2))
