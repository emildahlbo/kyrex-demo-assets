"""Søker i Unsplash (bare gratisbilder, ikke Unsplash+) og lager kontaktark.
Inndata: requests/search-*.txt med linjer «<navn>\t<søkeord>». Utdata: _search/<navn>/sheet.jpg og meta.json."""
import glob, io, json, os, sys, urllib.parse, urllib.request
from PIL import Image, ImageDraw, ImageFont
UA = {'User-Agent': 'Mozilla/5.0 kyrex-demo-assets', 'Accept': 'application/json'}
def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read()
font = ImageFont.load_default(size=22)
for f in sorted(glob.glob('requests/search-*.txt')):
    for line in open(f, encoding='utf-8'):
        if not line.strip() or line.startswith('#'):
            continue
        name, q = line.rstrip('\n').split('\t')[:2]
        out = f'_search/{name}'
        if os.path.exists(f'{out}/meta.json'):
            continue
        os.makedirs(out, exist_ok=True)
        try:
            d = json.loads(get('https://unsplash.com/napi/search/photos?' + urllib.parse.urlencode({'query': q, 'per_page': 30, 'plus': 'none'})))
        except Exception as e:
            print('FEIL', name, e); continue
        res = [r for r in d.get('results', []) if not r.get('premium') and not r.get('plus')][:24]
        meta, thumbs = [], []
        for i, r in enumerate(res):
            meta.append({'i': i, 'id': r['id'], 'alt': r.get('alt_description'), 'w': r['width'], 'h': r['height'],
                         'user': r['user']['name'], 'username': r['user']['username'], 'page': r['links']['html'],
                         'raw': r['urls']['raw'].split('?')[0], 'license': 'Unsplash License'})
            try:
                im = Image.open(io.BytesIO(get(r['urls']['raw'].split('?')[0] + '?w=300&h=300&fit=crop&q=60&fm=jpg'))).convert('RGB')
            except Exception:
                im = Image.new('RGB', (300, 300), 'gray')
            thumbs.append(im.resize((300, 300)))
        cols = 6
        rows = max(1, (len(thumbs) + cols - 1) // cols)
        sheet = Image.new('RGB', (cols * 300, rows * 300), 'white')
        dr = ImageDraw.Draw(sheet)
        for i, t in enumerate(thumbs):
            x, y = (i % cols) * 300, (i // cols) * 300
            sheet.paste(t, (x, y))
            dr.rectangle([x, y, x + 40, y + 30], fill='black')
            dr.text((x + 6, y + 3), str(i), fill='white', font=font)
        sheet.save(f'{out}/sheet.jpg', quality=70)
        json.dump(meta, open(f'{out}/meta.json', 'w'), ensure_ascii=False, indent=1)
        print('ok', name, len(meta))
