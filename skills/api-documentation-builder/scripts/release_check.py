#!/usr/bin/env python3
"""Supplementary lint for already reviewed, generated release artifacts ONLY."""
import argparse
import re
import shutil
import subprocess
from pathlib import Path

RULES = {
    'private-key': r'-----BEGIN (?:[A-Z0-9 ]+ )?PRIVATE KEY-----',
    'jwt-like': r'\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b',
    'known-token-pattern': r'\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9_-]{20,}|AKIA[A-Z0-9]{16}|xox[baprs]-[A-Za-z0-9-]{12,})\b',
    'url-credentials': r'(?i)\b[a-z][a-z0-9+.-]*://[^\s/@:]+:[^\s/@]+@',
    'possible-thai-national-id': r'(?<!\d)(?:\d[ -]?){12}\d(?!\d)',
    'possible-thai-phone': r'(?<!\d)(?:\+66[ -]?|0)[689][ -]?\d{1}[ -]?\d{3}[ -]?\d{4}(?!\d)',
    'email-address': r'(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b',
    'private-ip': r'(?<![\d.])(?:10\.(?:\d{1,3}\.){2}\d{1,3}|192\.168\.\d{1,3}\.\d{1,3}|172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3})(?![\d.])',
    'credential-literal': r'(?im)\b(?:password|passwd|client_secret|api_key|access_token|refresh_token)\s*["\']?\s*[:=]\s*["\'](?!YOUR_|DEMO_|REDACTED|PLACEHOLDER|<|\$\{)[^"\'\r\n]{4,}["\']',
    'bearer-literal': r'(?i)\bBearer\s+(?!YOUR_ACCESS_TOKEN\b|DEMO_TOKEN\b|REDACTED\b)[A-Za-z0-9._~-]{12,}\b',
}
# No matching values, filenames or subprocess diagnostics are printed.
ALLOWED = {'.md', '.txt', '.json', '.yaml', '.yml', '.pdf', '.mmd', '.mermaid'}

def scan(s):
    for rule, pattern in RULES.items():
        for m in re.finditer(pattern, s):
            yield rule, s.count('\n', 0, m.start()) + 1

def run_pdf(p):
    for cmd in ('pdftotext', 'pdfinfo', 'pdfdetach'):
        if not shutil.which(cmd):
            raise RuntimeError('pdf-tool-unavailable')
    def run(args):
        r = subprocess.run(args, capture_output=True, timeout=45, check=False)
        if r.returncode:
            raise RuntimeError('pdf-inspection-failed')
        return r.stdout.decode('utf-8', errors='replace')
    text = run(['pdftotext', '-layout', str(p), '-'])
    info = run(['pdfinfo', str(p)])
    embeds = run(['pdfdetach', '-list', str(p)])
    if not re.search(r'(?m)^0 embedded files', embeds):
        raise RuntimeError('pdf-embedded-files-or-unknown')
    if not text.strip():
        raise RuntimeError('pdf-no-extractable-text')
    return text + '\n' + info

def main():
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument('release_dir', type=Path)
    d = a.parse_args().release_dir
    if not d.is_dir() or d.is_symlink():
        print('FAIL: expected a generated release directory'); return 1
    files = sorted(d.rglob('*'))
    issues = 0; n = 0
    for p in files:
        if p.is_symlink():
            issues += 1; print('BLOCK: symlink'); continue
        if not p.is_file(): continue
        n += 1
        if p.suffix.lower() not in ALLOWED:
            issues += 1; print(f'BLOCK file {n}: unsupported release artifact'); continue
        if p.stat().st_size > 50 * 1024 * 1024:
            issues += 1; print(f'BLOCK file {n}: exceeds lint size limit; split output'); continue
        try:
            s = run_pdf(p) if p.suffix.lower() == '.pdf' else p.read_text(encoding='utf-8')
            for rule, line in scan(str(p.relative_to(d)) + '\n' + s):
                issues += 1; print(f'BLOCK file {n}, line {line}: {rule}')
        except (RuntimeError, OSError, UnicodeError, subprocess.SubprocessError):
            issues += 1; print(f'BLOCK file {n}: unreadable or PDF inspection unavailable')
    if not n: issues += 1; print('BLOCK: empty release')
    print(f'{"FAIL" if issues else "PASS"}: {n} files; {issues} lint findings. Manual privacy and consistency review remains mandatory.')
    return int(bool(issues))
if __name__ == '__main__': raise SystemExit(main())
