"""Build only the checked-in synthetic documentation examples, without live data."""
from pathlib import Path
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / 'skills/privacy-first-database-documentation-builder'
API = ROOT / 'skills/api-documentation-builder'
DB_OUT = DB / 'examples/synthetic-demo/output'
API_OUT = API / 'examples/synthetic-demo/output'
API_DOCS = ('api-catalog', 'api-data-dictionary', 'api-reference',
            'api-consumer-guide', 'api-governance', 'ai-agent-integration-guide')


def run(script, *args):
    env = {**os.environ, 'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONUTF8': '1'}
    subprocess.run([sys.executable, str(script), *(str(a) for a in args)],
                   check=True, env=env)


def render_api_pdf(md, out):
    from markdown_it import MarkdownIt
    from weasyprint import HTML, CSS
    from html import escape
    text = md.read_text(encoding='utf-8')
    title = text.splitlines()[0].removeprefix('# ')
    orientation = 'landscape' if md.stem in ('api-catalog', 'api-data-dictionary') else 'portrait'
    parser = MarkdownIt('commonmark', {'html': False, 'linkify': False}).enable('table')
    parser.disable(['image', 'autolink', 'link'])
    content = parser.render(text)
    def deny(url, *args, **kwargs):
        raise RuntimeError('resource-fetch-denied')
    style = '''@page {size:A4 ORIENTATION; margin:15mm 16mm 18mm;
      @bottom-left {content:"SYNTHETIC CONTRACT | NO LIVE CALLS"; color:#52657a; font-size:8pt;}
      @bottom-right {content:counter(page) " / " counter(pages); color:#52657a; font-size:8pt;}}
      body{font-family:"Noto Sans Thai",sans-serif;color:#182c40;font-size:11pt;line-height:1.48}
      h1{font-size:21pt;line-height:1.2;color:#20466d;border-bottom:2pt solid #4a80be;padding-bottom:8pt;margin:0 0 10pt}
      h2{font-size:15pt;color:#20466d;margin:16pt 0 6pt;break-after:avoid}h3{font-size:12pt;color:#28618c;break-after:avoid}
      p{margin:6pt 0 9pt}li{margin-bottom:3pt}table{width:100%;border-collapse:collapse;font-size:10pt;table-layout:fixed;margin:8pt 0 14pt}
      th,td{padding:6pt 7pt;border-bottom:.6pt solid #d9e3eb;overflow-wrap:anywhere;vertical-align:middle}
      th{background:#e9f0f8;color:#20466d;text-align:left}tr{break-inside:avoid}thead{display:table-header-group}
      tbody tr:nth-child(even){background:#f6f8fb}pre{background:#eef3f8;padding:10pt;border-left:3pt solid #4a80be;white-space:pre-wrap;overflow-wrap:anywhere;break-inside:avoid}
      code{font-family:monospace;font-size:9.5pt;overflow-wrap:anywhere}'''.replace('ORIENTATION', orientation)
    HTML(string='<!doctype html><html lang="th"><head><meta charset="utf-8"><title>'+escape(title)+'</title></head><body>'+content+'</body></html>',
         url_fetcher=deny).write_pdf(str(out), stylesheets=[CSS(string=style, url_fetcher=deny)])


def validate_api_examples(directory):
    import yaml
    from jsonschema import Draft202012Validator
    contract = yaml.safe_load((directory / 'openapi.yaml').read_text(encoding='utf-8'))
    if contract['servers'] != [{'url': 'https://api.example.invalid'}]:
        raise ValueError('Expected a synthetic reserved-domain server')
    if json.loads((directory / 'tools.json').read_text(encoding='utf-8'))['tools'] != []:
        raise ValueError('Synthetic example must not authorize any agent tools')
    for name in ('api-reference', 'api-consumer-guide'):
        doc = (directory / (name + '.md')).read_text(encoding='utf-8')
        examples = [json.loads(x) for x in re.findall(r'```json\s*(.*?)\s*```', doc, re.S)]
        if len(examples) != 2:
            raise ValueError('Expected two synthetic response examples')
        for example, path in zip(examples, ('/demo/departments', '/demo/departments/{code}')):
            schema = contract['paths'][path]['get']['responses']['200']['content']['application/json']['schema']
            Draft202012Validator({'components': contract['components'], **schema}).validate(example)
    print('PASS: synthetic API response examples and empty agent manifest')


def main():
    with tempfile.TemporaryDirectory(prefix='documentation-demo-') as work:
        temp = Path(work)
        db_render = temp / 'database'
        run(DB / 'scripts/build_dictionary.py', DB / 'assets/metadata-template.json',
            '--mode', 'full', '--pdf', '--out', db_render)
        # Check that the committed non-PDF database outputs are the actual generator output.
        for p in sorted(db_render.iterdir()):
            if p.suffix != '.pdf' and (DB_OUT / p.name).read_text(encoding='utf-8') != p.read_text(encoding='utf-8'):
                raise ValueError('Checked-in database example drift: ' + p.name)
        api_render = temp / 'api'
        api_render.mkdir()
        for p in API_OUT.iterdir():
            if p.is_file() and p.suffix != '.pdf':
                shutil.copy2(p, api_render / p.name)
        run(API / 'scripts/validate_openapi.py', api_render / 'openapi.yaml')
        validate_api_examples(api_render)
        for name in API_DOCS:
            render_api_pdf(api_render / (name + '.md'), api_render / (name + '.pdf'))
        run(API / 'scripts/release_check.py', api_render)
        # Publish only after validation and lint of both candidate sets succeed.
        for src, dest in ((db_render, DB_OUT), (api_render, API_OUT)):
            for p in sorted(src.glob('*.pdf')):
                shutil.copy2(p, dest / p.name)
            print(f'Built {len(list(src.glob("*.pdf")))} synthetic PDFs: {dest.relative_to(ROOT)}')


if __name__ == '__main__':
    main()
