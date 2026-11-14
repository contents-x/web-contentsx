"""Browser checks for the Creative X landing on the WordPress placement slots (2026-11).

python3 tests/test_creative_slots.py --url http://127.0.0.1:8796 --artifacts /tmp/cx-slots-qa [--channel chrome]
GET /wp-json/contentsx/v1/slots/<key> is answered from tests/fixtures/creative-x-slots.json: the real answers of
the local WordPress (plugin branch feat/creative-x-slots, docs/DESIGN-content-library.md §17), plus two
cards made the same way for the providers the real data has none of (mp4, file) and HERO MP4s. Nothing is
fetched from the network; images and videos are fixtures. Checks: WORKS order and filters (format_key),
manga spread / vertical in the book reader, every video provider in the player, the 3D phone (WordPress
pictures are never read for WebGL), CREATIVE SOLUTION picks, empty slots never filled with another work,
HERO MP4s in order (and the poster when empty), and empty / failure / 404 kept apart. Screenshots PC / phone.
"""
import argparse
import copy
import json
import shutil
import struct
import subprocess
import tempfile
import zlib
from pathlib import Path
from playwright.sync_api import sync_playwright

parser = argparse.ArgumentParser()
parser.add_argument('--url', required=True)
parser.add_argument('--artifacts', required=True)
parser.add_argument('--channel', default=None)
args = parser.parse_args()
out = Path(args.artifacts)
out.mkdir(parents=True, exist_ok=True)
BASE = args.url.rstrip('/')
PAGE = BASE + '/services/creative-x/'
ROOT = Path(__file__).resolve().parent.parent
API = 'https://cms.contentsx.jp/wp-json/contentsx/v1/'
UP = 'https://cms.contentsx.jp/wp-content/uploads/'
REAL = json.loads((ROOT / 'tests' / 'fixtures' / 'creative-x-slots.json').read_text(encoding='utf-8'))['slots']
report = []


def png(w, h, rgb):
    raw = b''.join(b'\x00' + bytes(rgb) * w for _ in range(h))
    def chunk(t, d):
        return struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    return b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(raw)) + chunk(b'IEND', b'')


def clip(seconds, color):
    ffmpeg = shutil.which('ffmpeg')
    if not ffmpeg:
        return None
    path = Path(tempfile.mkdtemp()) / 'clip.mp4'
    subprocess.run([ffmpeg, '-loglevel', 'error', '-y', '-f', 'lavfi', '-i', f'color=c={color}:size=320x180:rate=12:duration={seconds}',
                    '-c:v', 'libvpx-vp9', '-b:v', '100k', '-pix_fmt', 'yuv420p', '-an', str(path)], check=True)
    return path.read_bytes()


PAGE_IMG = png(70, 100, (238, 232, 220))
THUMB = png(160, 90, (60, 90, 140))
CLIPS = {'hero-1.mp4': clip(1, 'red'), 'hero-2.mp4': clip(1, 'blue'), 'test-mp4.mp4': clip(2, 'green'), 'test-file.mp4': clip(2, 'yellow')}
HAS_VIDEO = all(CLIPS.values())


def video_card(post_id, title, fmt, provider, src, thumb):
    return {'kind': 'video', 'id': post_id, 'title': title, 'label': 'VIDEO', 'date': '2026-11-10', 'thumb': thumb, 'url': src,
            'slug': f'test-{post_id}', 'sites': ['contentsx'], 'pickup': False, 'description': f'{title}の説明', 'achievement': '',
            'format': [fmt] if fmt else [], 'service': [], 'category': [],
            'video': {'provider': provider, 'video_id': '', 'embed': '', 'src': src, 'captions': '', 'file': src if provider == 'file' else ''},
            **({'format_key': fmt} if fmt else {})}


WORKS = copy.deepcopy(REAL['cx-creative-works']['body'])
WORKS['items'] += [video_card(9001, 'MP4のテスト動画', 'video', 'mp4', UP + '2026/11/test-mp4.mp4', UP + '2026/11/test-mp4.jpg'),
                   video_card(9002, '自社配信ファイルのテスト動画', 'anime', 'file', UP + '2026/11/test-file.mp4', UP + '2026/11/test-file.jpg')]
WORK_TITLES = [c['title'] for c in WORKS['items']]
HERO_FULL = dict(REAL['cx-creative-hero']['body'], items=[video_card(9101, 'HERO 1', None, 'file', UP + '2026/11/hero-1.mp4', UP + '2026/11/hero-1.jpg'),
                                                      video_card(9102, 'HERO 2', None, 'file', UP + '2026/11/hero-2.mp4', UP + '2026/11/hero-2.jpg')])
NOT_FOUND = (404, {'code': 'not_found', 'message': 'not_found', 'data': {'status': 404}})
LEGACY_WORKS = [{'id': 'legacy-manga', 'title_ja': '移行前のマンガ', 'view_type': 'spread', 'thumbnail': UP + '2026/10/legacy-thumb.png',
                 'gallery': [UP + f'2026/10/legacy-{i}.png' for i in range(1, 5)]}]
LEGACY_VIDEOS = {'viewer': [{'type': 'bizanime', 'title': '移行前のアニメ', 'provider': 'youtube', 'video_id': 'V9ZC16hTlZI'}]}


def answers(**over):
    """Slot answers: the real ones, WORKS with the two extra providers, then any override (status, body) / 'abort'."""
    a = {k: (v['status'], v['body']) for k, v in REAL.items()}
    a['cx-creative-works'] = (200, WORKS)
    a.update({k.replace('_', '-'): v for k, v in over.items()})
    return a


def open_page(browser, width, height, slot_answers, reduced=False):
    ctx = browser.new_context(viewport={'width': width, 'height': height}, has_touch=width <= 768, reduced_motion='reduce' if reduced else 'no-preference')
    page = ctx.new_page()
    page.errors, page.warnings, page.cors = [], [], []
    page.on('pageerror', lambda e: page.errors.append(str(e)))
    page.on('console', lambda m: page.warnings.append(m.text) if m.type == 'warning' else None)

    def route(r):
        u = r.request.url
        if u.startswith(API + 'slots/'):
            key = u[len(API + 'slots/'):].split('?')[0]
            ans = slot_answers.get(key, NOT_FOUND)
            if ans == 'abort':
                return r.abort()
            return r.fulfill(status=ans[0], content_type='application/json', body=json.dumps(ans[1], ensure_ascii=False),
                             headers={'Access-Control-Allow-Origin': '*', 'Cache-Control': 'public, max-age=300'})
        if u.startswith(API):
            body = LEGACY_WORKS if '/works' in u else LEGACY_VIDEOS if '/bizanime-videos' in u else []
            return r.fulfill(status=200, content_type='application/json', body=json.dumps(body, ensure_ascii=False), headers={'Access-Control-Allow-Origin': '*'})
        if u.startswith(UP):
            name = u.rsplit('/', 1)[-1]
            if name in CLIPS:
                return r.fulfill(status=200, content_type='video/mp4', body=CLIPS[name] or b'')
            if r.request.headers.get('origin'):          # a CORS read of a WordPress picture (WebGL): must not happen
                page.cors.append(u)
            return r.fulfill(status=200, content_type='image/png', body=PAGE_IMG if '-0' in name or 'legacy-' in name or 'p0' in name else THUMB)
        if u.startswith(('https://i.ytimg.com/', 'https://contentsx.jp/')):
            return r.fulfill(status=200, content_type='image/png', body=THUMB, headers={'Access-Control-Allow-Origin': '*'})
        if u.startswith((BASE, 'https://fonts.googleapis.com/', 'https://fonts.gstatic.com/')):
            return r.continue_()
        return r.abort()                                  # YouTube / Drive embeds: their URL is what is checked
    page.route('**/*', route)
    page.goto(PAGE, wait_until='networkidle')
    page.wait_for_timeout(500)
    return page


def wait_until(page, js, timeout=8000):
    """Poll a JS expression with evaluate (wait_for_function's polling needs eval, which the page's CSP blocks)."""
    waited = 0
    while waited <= timeout:
        if page.evaluate(js):
            return
        page.wait_for_timeout(100)
        waited += 100
    raise AssertionError(f'timed out waiting for: {js}')


def to_works(page):
    page.evaluate("document.querySelector('#works').scrollIntoView()")
    wait_until(page, "document.querySelector('#works.cxw-ready') || document.querySelector('#works .cxw-message')", 8000)
    page.wait_for_timeout(300)


def strip_titles(page):
    return page.locator('#works .cxw-thumb__title').all_inner_texts()


def tab(page, name):
    page.locator(f'[data-cxw-filter="{name}"]').click()
    page.wait_for_timeout(450)


def open_from_works(page, title):
    i = strip_titles(page).index(title)
    page.locator('#works .cxw-thumb').nth(i).click()
    page.wait_for_timeout(350)
    page.locator('#works .cxw-open').click()
    page.wait_for_timeout(900)


def close(page):
    page.keyboard.press('Escape')
    page.wait_for_timeout(300)


with sync_playwright() as p:
    browser = p.chromium.launch(channel=args.channel) if args.channel else p.chromium.launch()

    # ---------- 1–3 WORKS: WordPress order, filters by format_key ----------
    page = open_page(browser, 1440, 900, answers())
    to_works(page)
    assert strip_titles(page) == WORK_TITLES, strip_titles(page)
    counts = {t: page.locator(f'[data-cxw-filter="{t}"] .cxw-filters__count').inner_text() for t in ('all', 'manga', 'anime', 'video')}
    for t in ('manga', 'anime', 'video'):
        tab(page, t)
        expect = [c['title'] for c in WORKS['items'] if c.get('format_key') == t]
        assert strip_titles(page) == expect, (t, strip_titles(page), expect)
        assert counts[t] == str(len(expect)), (t, counts)
    tab(page, 'all')
    assert counts['all'] == str(len(WORK_TITLES)) and not page.errors, (counts, page.errors)
    page.screenshot(path=str(out / '1440-works.png'))
    report.append('WORKS: WordPress order kept in ALL and in MANGA / ANIME / VIDEO (format_key); counts right')

    # ---------- 4 manga: spread → book, vertical_only → vertical ----------
    open_from_works(page, 'マンガでわかるカミレス【公共・自治体編】')
    assert page.locator('.cxwv[data-kind="manga"] .cxmr-stage.is-book').count() == 1 and page.locator('.cxwv .cxmr-book').count() == 1, 'spread opens as a book'
    page.screenshot(path=str(out / '1440-manga-spread.png'))
    close(page)
    open_from_works(page, '正義の値段')
    assert page.locator('.cxwv .cxmr-stage.is-vertical').count() == 1 and page.locator('.cxwv .cxmr-book, .cxwv .cxmr-pbook').count() == 0, 'vertical_only reads by scrolling'
    close(page)
    report.append('manga: spread opens as the book (page flip), vertical_only scrolls; data straight from the card (manga.gallery / view_type)')

    # ---------- 5–6 video providers in the shared player, on the 3D phone ----------
    expected = {
        'Good Bye MV': ('iframe', 'https://www.youtube-nocookie.com/embed/V9ZC16hTlZI?'),
        'バトル・アクション系アニメMV': ('iframe', 'https://www.youtube-nocookie.com/embed/videoseries?list=PLb1LJBwnSgCE'),
        '【MV】目MEめぇ～愛 I eye': ('iframe', 'https://drive.google.com/file/d/1kffZJKMAMB9rJGVKYxSgjbDs5UI99BTQ/preview'),
        'MP4のテスト動画': ('video', UP + '2026/11/test-mp4.mp4'),
        '自社配信ファイルのテスト動画': ('video', UP + '2026/11/test-file.mp4'),   # provider: file → mp4
    }
    for title, (tag, src) in expected.items():
        open_from_works(page, title)
        page.wait_for_selector('.cxwv-phone.is-settled', timeout=8000)
        node = page.locator(f'.cxwv-phone__screen {tag}')
        assert node.count() == 1 and node.get_attribute('src').startswith(src), (title, tag, node.count() and node.get_attribute('src'))
        assert page.locator('.cxwv-gl').count() == 1 and 'is-3d' in page.locator('.cxwv-phone').get_attribute('class'), title
        if tag == 'video':
            wait_until(page, "(() => { const v = document.querySelector('.cxwv-phone__screen video'); return v && v.readyState >= 2; })()", 8000)
        if title == '自社配信ファイルのテスト動画':
            page.screenshot(path=str(out / '1440-video-file-3d.png'))
        close(page)
        assert page.locator('iframe, .cxwv video').count() == 0 and page.locator('.cxwv-gl').count() == 0, title
    assert not page.cors, ('WordPress pictures must never be read for WebGL (no CORS there)', page.cors)
    assert not page.errors, page.errors
    page.context.close()
    report.append('video: youtube / playlist / Drive in the iframe, mp4 and file (as mp4) in <video>; all on the 3D phone; closed = gone; no CORS read of WordPress pictures')

    # ---------- 7 CREATIVE SOLUTION: the chosen works ----------
    page = open_page(browser, 1440, 900, answers())
    page.evaluate("document.querySelector('#creative-solution').scrollIntoView()")
    wait_until(page, "document.querySelector('#creative-solution.is-ready')", 8000)
    titles = page.locator('[data-cxcs-title]').all_inner_texts()
    assert titles == ['マンガでわかるカミレス【公共・自治体編】', 'Good Bye MV', 'VLOG'], titles
    page.locator('#cxcs-card-anime .cxcs-card__action').click()
    page.wait_for_selector('.cxwv[data-kind="anime"] .cxwv-phone__screen iframe', timeout=8000)
    close(page)
    page.screenshot(path=str(out / '1440-solution.png'))
    page.context.close()
    report.append('CREATIVE SOLUTION: the three works chosen in WordPress; they open in the shared viewer')

    # ---------- 8 + 10 empty is never filled; empty / failure / time-out apart ----------
    page = open_page(browser, 1280, 800, answers(**{'cx_creative_solution_manga': (200, dict(REAL['cx-creative-solution-manga']['body'], items=[])),
                                                   'cx_creative_solution_anime': (500, {'code': 'internal'}), 'cx_creative_solution_video': 'abort'}))
    page.evaluate("document.querySelector('#creative-solution').scrollIntoView()")
    wait_until(page, "document.querySelector('#creative-solution.is-ready')", 12000)
    st = page.evaluate("""() => ['manga', 'anime', 'video'].map(k => { const c = document.querySelector('#cxcs-card-' + k), s = c.querySelector('[data-cxcs-status]');
      return { status: s && !s.hidden ? s.textContent.trim() : '', picture: !!c.querySelector('.cxcs-card__picture'), title: !c.querySelector('[data-cxcs-title]').hidden,
               link: (c.querySelector('a.cxcs-card__action') || {}).getAttribute ? c.querySelector('a.cxcs-card__action').getAttribute('href') : null }; })""")
    assert st[0] == {'status': '作品は準備中です。', 'picture': False, 'title': False, 'link': 'https://bizmanga.contentsx.jp/biz-library'}, st[0]   # WORKS has manga, yet none is put here
    assert st[1]['status'] == '作品を読み込めませんでした。' and not st[1]['picture'], st[1]
    assert st[2]['status'] == '作品を読み込めませんでした。' and not st[2]['picture'], st[2]
    page.screenshot(path=str(out / '1280-solution-empty-and-failed.png'))
    page.context.close()
    for name, ans, message in (('empty', (200, dict(WORKS, items=[])), '作品は準備中です'), ('failed', (503, {}), '作品を読み込めませんでした'), ('offline', 'abort', '作品を読み込めませんでした')):
        page = open_page(browser, 1280, 800, answers(cx_creative_works=ans))
        to_works(page)
        assert message in page.locator('#works .cxw-message').inner_text() and page.locator('[data-cxw-fallback] a').count() == 3, name
        assert page.locator('[data-cxw-filters]').is_hidden(), name
        page.context.close()
    report.append('empty slots stay empty (no stand-in work); empty, 5xx and network failure show different, honest states')

    # ---------- 10 404 = a WordPress without the slots yet (today's production): the older lists ----------
    page = open_page(browser, 1280, 800, {})
    to_works(page)
    assert strip_titles(page) == ['移行前のマンガ', '移行前のアニメ'], strip_titles(page)
    assert any('not released there yet' in w for w in page.warnings), page.warnings[:5]
    page.evaluate("document.querySelector('#creative-solution').scrollIntoView()")
    wait_until(page, "document.querySelector('#creative-solution.is-ready')", 8000)
    assert page.locator('#cxcs-card-manga .cxcs-card__picture').count() == 0      # the named work is not in the older lists: no stand-in
    assert not page.errors, page.errors
    page.context.close()
    report.append('404 (slots not on that WordPress yet): older lists with a console warning; still no stand-in work')

    # ---------- 9 HERO: empty → the poster; MP4s → played in order, thumb as poster ----------
    page = open_page(browser, 1280, 800, answers())
    hero = page.evaluate("(() => { const v = document.querySelector('.cxg-reel video'); return { src: v.getAttribute('src') || '', poster: document.querySelector('.cxg-reel__poster').getAttribute('src'), toggle: !document.querySelector('[data-cxg-reel-toggle]').hidden }; })()")
    assert hero == {'src': '', 'poster': 'https://i.ytimg.com/vi/zKvRR8xT_zY/maxres1.jpg', 'toggle': False}, hero
    page.screenshot(path=str(out / '1280-hero-empty.png'))
    page.context.close()
    if HAS_VIDEO:
        page = open_page(browser, 1280, 800, answers(cx_creative_hero=(200, HERO_FULL)))
        wait_until(page, "(() => { const v = document.querySelector('.cxg-reel video'); return v && /hero-1\\.mp4$/.test(v.currentSrc) && !v.paused; })()", 8000)
        assert page.evaluate("document.querySelector('.cxg-reel__poster').getAttribute('src')") == UP + '2026/11/hero-1.jpg'
        assert page.evaluate("document.querySelector('.cxg-reel video').loop") is False
        wait_until(page, "/hero-2\\.mp4$/.test(document.querySelector('.cxg-reel video').currentSrc)", 8000)
        wait_until(page, "/hero-1\\.mp4$/.test(document.querySelector('.cxg-reel video').currentSrc)", 8000)   # round again
        assert not page.errors, page.errors
        page.context.close()
        report.append('HERO: empty slot → the poster, no video, no other work; MP4s play in WordPress order and round again, first thumb as poster')
    else:
        report.append('HERO: empty slot → the poster (ffmpeg missing: MP4 order not checked)')

    # ---------- 11 PC / phone with the slot data ----------
    for width, height in ((1440, 900), (390, 844), (320, 640)):
        page = open_page(browser, width, height, answers())
        to_works(page)
        assert page.evaluate('document.documentElement.scrollWidth - innerWidth') <= 0, width
        page.screenshot(path=str(out / f'{width}-works-slots.png'))
        page.evaluate("document.querySelector('#creative-solution').scrollIntoView()")
        page.wait_for_timeout(900)
        page.screenshot(path=str(out / f'{width}-solution-slots.png'))
        if width == 390:
            open_from_works(page, 'Good Bye MV')
            page.wait_for_selector('.cxwv-phone.is-settled', timeout=8000)
            page.screenshot(path=str(out / '390-video.png'))
            close(page)
        assert not page.errors, (width, page.errors)
        page.context.close()
    report.append('PC and phones (1440 / 390 / 320): no horizontal scroll with the slot data')
    browser.close()

(out / 'report.txt').write_text('\n'.join(report) + '\n', encoding='utf-8')
print('creative slots: ok')
for line in report:
    print(' -', line)
