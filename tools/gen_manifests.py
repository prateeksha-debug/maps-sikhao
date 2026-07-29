#!/usr/bin/env python3
"""Build per-language recording manifests (line_id, text) for the ElevenLabs step.

Maps the original script tsv (L-ids -> Hindi line) through tools/strings-hi.json
indices into each translations/<lang>.json, writing tools/manifest-<lang>.csv.
The greeting line uses the plain (no-name) form: greeting.prefix + greeting.suffix.
"""
import csv, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TSV = f'{ROOT}/tools/script-hi.tsv'
GREETING_IDX = 75
LANGS = ['hi', 'en', 'ta', 'kn', 'te']

src = json.load(open(f'{ROOT}/tools/strings-hi.json', encoding='utf-8'))
idx_of = {s: i for i, s in enumerate(src)}
# tsv wording drifted slightly from the page for these ids -> map manually
MANUAL_IDX = {'L12': 37}

rows = list(csv.DictReader(open(TSV, encoding='utf-8'), delimiter='\t'))
print(f'script lines: {len(rows)}')

for lang in LANGS:
    t = json.load(open(f'{ROOT}/translations/{lang}.json', encoding='utf-8'))
    strings, greeting = t['strings'], t['greeting']
    out, unmatched = [], []
    for r in rows:
        lid, hindi = r['id'], r['text'].strip()
        if lang == 'hi':
            out.append((lid, hindi)); continue
        i = idx_of.get(hindi, MANUAL_IDX.get(lid))
        if i is None:
            unmatched.append(lid); out.append((lid, f'UNMATCHED: {hindi}')); continue
        if i == GREETING_IDX:
            out.append((lid, greeting['prefix'] + greeting['suffix']))
        elif strings[i] is not None:
            out.append((lid, strings[i]))
        else:
            out.append((lid, hindi))  # intentionally-kept line
    path = f'{ROOT}/tools/manifest-{lang}.csv'
    with open(path, 'w', encoding='utf-8', newline='') as f:
        w = csv.writer(f)
        w.writerow(['line_id', 'text'])
        w.writerows(out)
    print(f'{lang}: {len(out)} lines -> {path}' + (f'  UNMATCHED: {unmatched}' if unmatched else ''))
