#!/usr/bin/env python3
"""Build a localized maps-sikhao page from the Hindi source.

Usage:  python3 tools/build.py <lang> [...]      e.g.  python3 tools/build.py hi en
Reads   tools/source-hi.html, tools/strings-hi.json, translations/<lang>.json
Writes  index.html for hi, <lang>.html for everything else.

Every build gets ?name= support: the greeting becomes
  <prefix> <name><honorific>! <suffix>   when the app appends ?name=<pro name>.
Translation JSON: { lang, voice, greeting: {prefix, suffix, honorific}, strings: [145; null = keep] }
Rule for strings: use curly apostrophes (’) only — replacements land inside single-quoted JS.
"""
import json, re, sys, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GREETING_IDX = 75  # the 'नमस्ते! मैं हूँ पारुल…' line in strings-hi.json

def build(lang: str) -> None:
    html = open(f'{ROOT}/tools/source-hi.html', encoding='utf-8').read()
    src = json.load(open(f'{ROOT}/tools/strings-hi.json', encoding='utf-8'))
    t = json.load(open(f'{ROOT}/translations/{lang}.json', encoding='utf-8'))
    strings = t['strings']
    assert len(strings) == len(src), f'{lang}: need {len(src)} entries'

    # 1) greeting -> name-aware JS expression
    g = t['greeting']
    expr = ("('%s' + (window.__PRO_NAME ? ' ' + window.__PRO_NAME + '%s' : '') + '%s')"
            % (g['prefix'], g['honorific'], g['suffix']))
    greet_lit = "'" + src[GREETING_IDX] + "'"
    assert html.count(greet_lit) == 1, 'greeting literal not found'
    html = html.replace(greet_lit, expr)
    strings = list(strings)
    strings[GREETING_IDX] = None  # handled

    # 2) translate, longest source first (avoids substring clobbering)
    pairs = sorted(((src[i], s) for i, s in enumerate(strings) if s is not None),
                   key=lambda p: -len(p[0]))
    missing = 0
    for s, out in pairs:
        if s not in html:
            print(f'  WARN not found: {s[:40]!r}'); missing += 1
        html = html.replace(s, out)

    # 3) technical swaps for non-Hindi voices
    if t['voice'] != 'hi':
        v = t['voice']
        html = html.replace('<html lang="hi">', f'<html lang="{t["lang"]}">', 1)
        html = html.replace("=== 'hi-in'", f"=== '{v}-in'")
        html = html.replace(".indexOf('hi') === 0", f".indexOf('{v}') === 0")
        html = html.replace("|| 'hi-IN'", f"|| '{v}-IN'")

    # 4) ?name= reader (sanitized), injected at body start
    m = re.search(r'<body[^>]*>', html)
    snippet = ('<script>window.__PRO_NAME=((new URLSearchParams(location.search)).get("name")||"")'
               '.slice(0,30).replace(/[^\\p{L} .-]/gu,"");</script>')
    html = html[:m.end()] + snippet + html[m.end():]

    out_name = 'index.html' if lang == 'hi' else f'{lang}.html'
    open(f'{ROOT}/{out_name}', 'w', encoding='utf-8').write(html)

    # 5) sanity: leftover Devanagari only in intentionally-kept (null) strings
    if t['voice'] != 'hi':
        tmp = html
        for i, s in enumerate(t['strings']):
            if s is None and i != GREETING_IDX:
                tmp = tmp.replace(src[i], '')
        tmp = re.sub(r"\('%s'[^)]*\)" % re.escape(g['prefix']), '', tmp)  # greeting expr
        left = re.findall(r'[ऀ-ॿ]', tmp)
        print(f'  {out_name}: leftover Devanagari outside kept strings: {len(left)}')
    print(f'built {out_name} ({lang}), warnings: {missing}')

if __name__ == '__main__':
    for lang in (sys.argv[1:] or ['hi', 'en']):
        build(lang)
