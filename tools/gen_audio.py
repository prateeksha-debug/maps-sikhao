#!/usr/bin/env python3
"""Generate per-language Parul audio from the manifests via ElevenLabs.

Usage:  ELEVENLABS_API_KEY=... python3 tools/gen_audio.py <lang> [...]
Writes  audio/<lang>/<line_id>.mp3

Voice spec = the production Parul persona from voice-gateway-service
(personas/constants.ts): one multilingual voice across Indian languages,
model per language, fixed voice settings.
"""
import csv, json, os, sys, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API_KEY = os.environ.get('ELEVENLABS_API_KEY')

VOICE_ID = 'Wh1QG8ICTAxQWHIbW3SS'          # PersonaName.PARUL, all Indian languages
VOICE_SETTINGS = {'stability': 0.7, 'similarity_boost': 1, 'style': 0.38,
                  'use_speaker_boost': True, 'speed': 1.1}
MODEL_BY_LANG = {'en': 'eleven_turbo_v2_5', 'hi': 'eleven_turbo_v2_5',
                 'ta': 'eleven_turbo_v2_5', 'te': 'eleven_v3', 'kn': 'eleven_v3'}

def gen(lang: str) -> None:
    model = MODEL_BY_LANG[lang]
    outdir = f'{ROOT}/audio/{lang}'
    os.makedirs(outdir, exist_ok=True)
    rows = list(csv.DictReader(open(f'{ROOT}/tools/manifest-{lang}.csv', encoding='utf-8')))
    for r in rows:
        lid, text = r['line_id'], r['text']
        path = f'{outdir}/{lid}.mp3'
        if os.path.exists(path):
            continue
        req = urllib.request.Request(
            f'https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}?output_format=mp3_44100_128',
            data=json.dumps({'text': text, 'model_id': model,
                             'voice_settings': VOICE_SETTINGS}).encode(),
            headers={'xi-api-key': API_KEY, 'Content-Type': 'application/json'})
        with urllib.request.urlopen(req) as resp, open(path, 'wb') as f:
            f.write(resp.read())
        print(f'{lang}/{lid}.mp3 ok')
    print(f'{lang}: done ({len(rows)} lines)')

if __name__ == '__main__':
    if not API_KEY:
        sys.exit('set ELEVENLABS_API_KEY first')
    for lang in (sys.argv[1:] or ['hi', 'en', 'ta', 'kn', 'te']):
        gen(lang)
