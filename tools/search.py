"""Søker i Unsplash (bare gratisbilder, ikke Unsplash+) og lager kontaktark.
Inndata: requests/search-*.txt med linjer «<navn>\t<søkeord>». Utdata: _search/<navn>/sheet.jpg og meta.json."""
import glob, io, json, os, re, sys, urllib.parse, urllib.request
from PIL import Image, ImageDraw, ImageFont
UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36', 'Accept': 'text/html,*/*'}
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
            html = get('https://unsplash.com/s/photos/' + urllib.parse.quote(q.replace(' ', '-')) + '?license=free').decode('utf-8', 'replace')
        except Exception as e:
            os.makedirs('_search', exist_ok=True)
            open('_search/_log.txt', 'a').write(f'FEIL {name}: {e!r}\n')
            continue
        meta, thumbs, seen = [], [], set()
        for fig in html.split('<figure')[1:]:
            m = re.search(r'href="/photos/([^"?]+)"', fig)
            im = re.search(r'https://images\.unsplash\.com/(photo-[0-9a-f]+-[0-9a-f]+)', fig)
            if not m or not im or 'plus.unsplash.com' in fig:
                continue
            pid = m.group(1).rsplit('-', 1)[-1] if '-' in m.group(1) else m.group(1)
            slug = m.group(1)
            if slug in seen:
                continue
            seen.add(slug)
            u = re.search(r'href="/@([^"?/]+)"', fig)
            alt = re.search(r'alt="([^"]*)"', fig)
            meta.append({'i': len(meta), 'slug': slug, 'alt': alt.group(1) if alt else '', 'username': u.group(1) if u else '',
                         'page': 'https://unsplash.com/photos/' + slug, 'raw': 'https://images.unsplash.com/' + im.group(1), 'license': 'Unsplash License'})
            if len(meta) >= 24:
                break
        for r in meta:
            try:
                t = Image.open(io.BytesIO(get(r['raw'] + '?w=300&h=300&fit=crop&q=60&fm=jpg'))).convert('RGB')
            except Exception:
                t = Image.new('RGB', (300, 300), 'gray')
            thumbs.append(t.resize((300, 300)))
        if not meta:
            open('_search/_log.txt', 'a').write(f'TOMT {name}: {len(html)} tegn\n')
            continue
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
