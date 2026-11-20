"""Browser checks for the Creative X landing on the WordPress placement slots (2026-11).

python3 tests/test_creative_slots.py --url http://127.0.0.1:8796 --artifacts /tmp/cx-slots-qa [--channel chrome]
GET /wp-json/contentsx/v1/slots/<key> is answered from tests/fixtures/creative-x-slots.json: the real answers of
the local WordPress (plugin branch feat/creative-x-slots, docs/DESIGN-content-library.md §17), plus two
cards made the same way for the providers the real data has none of (mp4, file) and HERO MP4s. Nothing is
fetched from the network; images and videos are fixtures (the test MP4s are drawn by ffmpeg in a temp folder,
never written into the site). Checks: WORKS order and filters (format_key), manga spread / vertical in the
book reader, every video provider in the player, the 3D phone (WordPress pictures are never read for WebGL),
CREATIVE SOLUTION picks, HERO MP4s in order (and the poster when there are none), empty / failure / 404 kept
apart, and the move to WordPress (js/wp-config.js creativeXLegacyFallback): with the switch on, WORKS and
the picks keep the older lists (71 works, the three named picks) and do not even ask their slots, however
many works WordPress holds; switched off they show WordPress's works and order (empty as empty), and
switched on again they are back on the older lists. The HERO reads its slot either way. HERO: a slow WordPress answer still
starts the video, one that never comes leaves the poster, and a refused autoplay keeps the poster.
Screenshots PC / phone.
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
CLIPS = {'hero-1.mp4': clip(1, 'red'), 'hero-2.mp4': clip(1, 'blue'), 'hero-3.mp4': clip(1, 'white'),
         'test-mp4.mp4': clip(2, 'green'), 'test-file.mp4': clip(2, 'yellow')}
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
HERO_FULL = dict(REAL['cx-creative-hero']['body'], items=[video_card(9100 + n, f'HERO {n}', None, 'file', UP + f'2026/11/hero-{n}.mp4', UP + f'2026/11/hero-{n}.jpg')
                                                           for n in (1, 2, 3)])
NOT_FOUND = (404, {'code': 'not_found', 'message': 'not_found', 'data': {'status': 404}})
# The older lists as production has them today (2026-11-20: 71 works on the page): /works?site=contentsx (manga)
# and /bizanime-videos (anime and video), with the three works data/creative-solution.json names. The other
# IDs are made up for the test and never leave tests/.
PICKS = {'manga': ('opro-kamiless', 'マンガでわかるカミレス【公共・自治体編】'), 'anime': ('V9ZC16hTlZI', 'Good Bye MV'), 'video': ('QqRlb_JGaHw', 'VLOG')}


def legacy_manga(i, wid, title):
    return {'id': wid, 'title_ja': title, 'view_type': 'spread', 'thumbnail': UP + f'2026/10/legacy-thumb-{i}.png',
            'gallery': [UP + f'2026/10/legacy-{i}-{p}.png' for p in range(1, 5)]}


def legacy_video(kind, vid, title):
    return {'type': 'bizanime' if kind == 'anime' else 'bizvideo', 'title': title, 'provider': 'youtube', 'video_id': vid}


LEGACY_WORKS = [legacy_manga(0, *PICKS['manga'])] + [legacy_manga(i, f'legacy-manga-{i}', f'移行前のマンガ{i}') for i in range(1, 40)]
LEGACY_VIDEOS = {'viewer': [legacy_video('anime', *PICKS['anime'])] + [legacy_video('anime', f'testAnime{i:02d}', f'移行前のアニメ{i}') for i in range(1, 21)]
                 + [legacy_video('video', *PICKS['video'])] + [legacy_video('video', f'testVideo{i:02d}', f'移行前の映像{i}') for i in range(1, 10)]}
LEGACY_COUNTS = {'all': '71', 'manga': '40', 'anime': '21', 'video': '10'}
EMPTY = {k: (200, dict(v['body'], items=[])) for k, v in REAL.items() if v['status'] == 200}   # the plugin released, nothing set yet


def answers(**over):
    """Slot answers: the real ones, WORKS with the two extra providers, then any override (status, body) / 'abort'."""
    a = {k: (v['status'], v['body']) for k, v in REAL.items()}
    a['cx-creative-works'] = (200, WORKS)
    a.update({k.replace('_', '-'): v for k, v in over.items()})
    return a


def open_page(browser, width, height, slot_answers, reduced=False, migration=True, legacy=None, hold=(), init=None):
    """migration: js/wp-config.js creativeXLegacyFallback (true as published). hold: slot keys whose answer waits
    until the test sends it (page.held); the page is then opened without waiting for the network to go quiet."""
    ctx = browser.new_context(viewport={'width': width, 'height': height}, has_touch=width <= 768, reduced_motion='reduce' if reduced else 'no-preference')
    page = ctx.new_page()
    page.errors, page.warnings, page.cors, page.held, page.older, page.slots = [], [], [], {}, [], []
    page.on('pageerror', lambda e: page.errors.append(str(e)))
    page.on('console', lambda m: page.warnings.append(m.text) if m.type == 'warning' else None)
    if init:
        page.add_init_script(init)
    legacy_works, legacy_videos = legacy if isinstance(legacy, tuple) else (LEGACY_WORKS, LEGACY_VIDEOS)   # legacy='abort': older lists down

    def route(r):
        u = r.request.url
        if u.startswith(API + 'slots/'):
            key = u[len(API + 'slots/'):].split('?')[0]
            page.slots.append(key)
            if key in hold:
                page.held[key] = r
                return None
            ans = slot_answers.get(key, NOT_FOUND)
            if ans == 'abort':
                return r.abort()
            return r.fulfill(status=ans[0], content_type='application/json', body=json.dumps(ans[1], ensure_ascii=False),
                             headers={'Access-Control-Allow-Origin': '*', 'Cache-Control': 'public, max-age=300'})
        if u.startswith(API):
            page.older.append(u[len(API):])
            if legacy == 'abort':
                return r.abort()
            body = legacy_works if '/works' in u else legacy_videos if '/bizanime-videos' in u else []
            return r.fulfill(status=200, content_type='application/json', body=json.dumps(body, ensure_ascii=False), headers={'Access-Control-Allow-Origin': '*'})
        if u.startswith(BASE) and u.split('?')[0].endswith('/js/wp-config.js') and not migration:
            res = r.fetch()
            return r.fulfill(response=res, body=res.text().replace('creativeXLegacyFallback: true,', 'creativeXLegacyFallback: false,'))
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
    page.goto(PAGE, wait_until='load' if hold else 'networkidle')
    page.wait_for_timeout(500)
    assert page.evaluate('WP_CONFIG.creativeXLegacyFallback') is migration, 'the move switch is not what the test asked for'
    return page


def send(page, key, ans):
    """Answer a held slot request now."""
    page.held.pop(key).fulfill(status=ans[0], content_type='application/json', body=json.dumps(ans[1], ensure_ascii=False),
                               headers={'Access-Control-Allow-Origin': '*'})


def hero_state(page):
    return page.evaluate("""() => { const v = document.querySelector('.cxg-reel video'), r = document.querySelector('.cxg-reel');
      return { src: v.currentSrc || v.getAttribute('src') || '', paused: v.paused, playing: r.classList.contains('is-playing'),
               toggle: !document.querySelector('[data-cxg-reel-toggle]').hidden, poster: document.querySelector('.cxg-reel__poster').getAttribute('src'),
               posterShown: getComputedStyle(document.querySelector('.cxg-reel__poster')).visibility === 'visible' }; }""")


def solution_state(page):
    page.evaluate("document.querySelector('#creative-solution').scrollIntoView()")
    wait_until(page, "document.querySelector('#creative-solution.is-ready')", 12000)
    return page.evaluate("""() => ['manga', 'anime', 'video'].map(k => { const c = document.querySelector('#cxcs-card-' + k), s = c.querySelector('[data-cxcs-status]'), t = c.querySelector('[data-cxcs-title]');
      return { title: t.hidden ? '' : t.textContent, status: s && !s.hidden ? s.textContent.trim() : '', picture: !!c.querySelector('.cxcs-card__picture') }; })""")


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

    # ---------- 1–7 after the switch (creativeXLegacyFallback: false): the slots' works ----------
    # ---------- 1–3 WORKS: WordPress order, filters by format_key ----------
    page = open_page(browser, 1440, 900, answers(), migration=False)
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
    report.append('switched (off): WORKS keeps WordPress order in ALL and in MANGA / ANIME / VIDEO (format_key); counts right')

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
    page = open_page(browser, 1440, 900, answers(), migration=False)
    page.evaluate("document.querySelector('#creative-solution').scrollIntoView()")
    wait_until(page, "document.querySelector('#creative-solution.is-ready')", 8000)
    titles = page.locator('[data-cxcs-title]').all_inner_texts()
    assert titles == ['マンガでわかるカミレス【公共・自治体編】', 'Good Bye MV', 'VLOG'], titles
    page.locator('#cxcs-card-anime .cxcs-card__action').click()
    page.wait_for_selector('.cxwv[data-kind="anime"] .cxwv-phone__screen iframe', timeout=8000)
    close(page)
    page.screenshot(path=str(out / '1440-solution.png'))
    page.context.close()
    report.append('switched (off): CREATIVE SOLUTION shows the three works chosen in WordPress; they open in the shared viewer')

    # ---------- 8 failure is not empty: 5xx and network errors keep their own state (after the switch) ----------
    for name, ans in (('failed', (503, {})), ('offline', 'abort')):
        page = open_page(browser, 1280, 800, answers(cx_creative_works=ans, cx_creative_solution_manga=ans, cx_creative_solution_anime=ans,
                                                     cx_creative_solution_video=ans, cx_creative_hero=ans), migration=False)
        to_works(page)
        assert '作品を読み込めませんでした' in page.locator('#works .cxw-message').inner_text() and page.locator('[data-cxw-fallback] a').count() == 3, name
        assert page.locator('[data-cxw-filters]').is_hidden() and page.locator('#works .cxw-thumb').count() == 0 and not page.older, (name, page.older)   # not the older lists
        st = solution_state(page)
        assert all(s == {'title': '', 'status': '作品を読み込めませんでした。', 'picture': False} for s in st), (name, st)
        h = hero_state(page)
        assert not h['src'] and not h['playing'] and not h['toggle'] and h['posterShown'], (name, h)
        assert not page.errors, (name, page.errors)
        if name == 'offline':
            page.screenshot(path=str(out / '1280-offline.png'))
        page.context.close()
    report.append('4 通信エラー after the switch (slots 5xx / network): WORKS and the picks say 「読み込めませんでした」, HERO keeps the poster; never the older lists, never empty-looking')
    # During the move the older lists are what WORKS reads: when they fail, the same honest state.
    page = open_page(browser, 1280, 800, answers(), legacy='abort')
    to_works(page)
    assert '作品を読み込めませんでした' in page.locator('#works .cxw-message').inner_text() and page.locator('#works .cxw-thumb').count() == 0
    st = solution_state(page)
    assert all(s == {'title': '', 'status': '作品を読み込めませんでした。', 'picture': False} for s in st), st
    assert set(page.slots) == {'cx-creative-hero'} and hero_state(page)['posterShown'] and not page.errors, (page.slots, page.errors)
    page.context.close()
    report.append('4 通信エラー during the move (older lists down): the same 「読み込めませんでした」; the WORKS / pick slots are still not asked')

    # ---------- 9 404 = a WordPress without the slots yet (production on 2026-11-20): the older lists ----------
    def older_lists_kept(page, label, switch_on=True):
        to_works(page)
        titles = strip_titles(page)
        counts = {t: page.locator(f'[data-cxw-filter="{t}"] .cxw-filters__count').inner_text() for t in ('all', 'manga', 'anime', 'video')}
        assert len(titles) == 71 and counts == LEGACY_COUNTS, (label, len(titles), counts)
        assert titles[:3] == [PICKS['manga'][1], PICKS['anime'][1], PICKS['video'][1]], (label, titles[:3])   # ALL mixes manga / anime / video
        assert not set(titles) & (set(WORK_TITLES) - {t for _, t in PICKS.values()}), label                 # nothing from the slot fixture
        st = solution_state(page)
        assert [s['title'] for s in st] == [PICKS[k][1] for k in ('manga', 'anime', 'video')] and all(s['picture'] and not s['status'] for s in st), (label, st)
        h = hero_state(page)
        assert not h['src'] and not h['playing'] and h['poster'] == 'https://i.ytimg.com/vi/zKvRR8xT_zY/maxres1.jpg', (label, h)
        if switch_on:                                                              # WORKS and the picks never ask their slots
            assert set(page.slots) == {'cx-creative-hero'}, (label, page.slots)
        assert not page.errors, (label, page.errors)

    page = open_page(browser, 1280, 800, {})
    older_lists_kept(page, '404')
    assert any('not released there yet' in w for w in page.warnings), page.warnings[:5]
    page.context.close()
    report.append('1 404 (slots not on that WordPress yet = production today): WORKS 71 works from the older lists, the three named picks, HERO poster; console warning')

    # ---------- 10 the plugin released, nothing set yet: 200 + items: [] everywhere, switch on ----------
    page = open_page(browser, 1280, 800, EMPTY)
    older_lists_kept(page, 'empty + switch on')
    assert any('creativeXLegacyFallback is on' in w for w in page.warnings), page.warnings[:8]
    page.screenshot(path=str(out / '1280-empty-switch-on-solution.png'))
    to_works(page)
    page.screenshot(path=str(out / '1280-empty-switch-on-works.png'))
    page.context.close()
    report.append('2 200 + items: [] with the switch on (= right after the plugin upload): the same 71 works and three picks stay; HERO poster; console note')

    # ---------- 11 works registered in WordPress (some of them) — on: unchanged; off: WordPress; on again: back ----------
    other_anime = next(c for c in WORKS['items'] if c['title'] == 'バトル・アクション系アニメMV')   # not the named anime pick
    REGISTERED = answers(cx_creative_solution_anime=(200, dict(REAL['cx-creative-solution-anime']['body'], items=[other_anime])),
                         **({'cx_creative_hero': (200, HERO_FULL)} if HAS_VIDEO else {}))
    for step, migration in (('switch on, 8 works registered', True), ('switched off', False), ('switched back on', True)):
        page = open_page(browser, 1280, 800, REGISTERED, migration=migration)
        to_works(page)
        titles = strip_titles(page)
        picks = [s['title'] for s in solution_state(page)]
        if migration:
            assert len(titles) == 71 and not set(titles) & (set(WORK_TITLES) - {t for _, t in PICKS.values()}), (step, len(titles))
            assert picks == [PICKS[k][1] for k in ('manga', 'anime', 'video')], (step, picks)
            assert set(page.slots) == {'cx-creative-hero'}, (step, page.slots)          # WORKS / pick slots not even asked
        else:
            assert titles == WORK_TITLES, (step, titles)                                # WordPress's works and order only
            assert picks == [PICKS['manga'][1], other_anime['title'], PICKS['video'][1]], (step, picks)
            assert {'cx-creative-works', 'cx-creative-solution-anime'} <= set(page.slots), (step, page.slots)
        if HAS_VIDEO:                                                                   # the HERO reads its slot either way
            page.evaluate('window.scrollTo({ top: 0, behavior: "instant" })')
            wait_until(page, "/hero-[123]\\.mp4$/.test(document.querySelector('.cxg-reel video').currentSrc)", 8000)
        assert not page.errors, (step, page.errors)
        to_works(page)
        page.screenshot(path=str(out / f"1280-registered-{step.replace(' ', '-').replace(',', '')}.png"))
        page.context.close()
    report.append('3 200 with works: switch on → still the 71 older works and the named picks (WORKS / pick slots not asked), HERO plays its slot; '
                  'switched off → WordPress works and order only, picks from their slots; switched back on → the 71 again (切り戻し)')

    # ---------- 12 a named pick missing from the older lists: no stand-in, even during the move ----------
    page = open_page(browser, 1280, 800, EMPTY, legacy=([w for w in LEGACY_WORKS if w['id'] != PICKS['manga'][0]], LEGACY_VIDEOS))
    st = solution_state(page)
    assert st[0] == {'title': '', 'status': '作品は準備中です。', 'picture': False}, st[0]
    assert [s['title'] for s in st[1:]] == [PICKS['anime'][1], PICKS['video'][1]], st
    assert any('is not in WordPress; the card shows no work' in w for w in page.warnings), page.warnings[:8]
    page.context.close()
    report.append('pick missing from the older lists (switch on): that card says 「準備中」, no other work is chosen')

    # ---------- 13 switch off (the move finished): empty is shown as empty ----------
    page = open_page(browser, 1280, 800, EMPTY, migration=False)
    to_works(page)
    assert '作品は準備中です' in page.locator('#works .cxw-message').inner_text() and page.locator('[data-cxw-fallback] a').count() == 3
    assert page.locator('[data-cxw-filters]').is_hidden() and page.locator('#works .cxw-thumb').count() == 0
    st = solution_state(page)
    assert all(s == {'title': '', 'status': '作品は準備中です。', 'picture': False} for s in st), st
    link = page.locator('#cxcs-card-manga a.cxcs-card__action').get_attribute('href')
    assert link == 'https://bizmanga.contentsx.jp/biz-library', link             # the card keeps its link to the service
    h = hero_state(page)
    assert not h['src'] and not h['playing'] and h['posterShown'], h
    assert not page.older and not any('creativeXLegacyFallback' in w for w in page.warnings), (page.older, page.warnings[:8])
    assert not page.errors, page.errors
    page.screenshot(path=str(out / '1280-empty-switch-off.png'))
    page.context.close()
    page = open_page(browser, 1280, 800, answers(cx_creative_solution_manga=EMPTY['cx-creative-solution-manga'], cx_creative_solution_anime=(500, {'code': 'internal'}),
                                                 cx_creative_solution_video='abort'), migration=False)
    st = solution_state(page)
    assert [s['status'] for s in st] == ['作品は準備中です。', '作品を読み込めませんでした。', '作品を読み込めませんでした。'] and not any(s['picture'] for s in st), st
    page.screenshot(path=str(out / '1280-solution-empty-and-failed.png'))
    page.context.close()
    report.append('8 switch off: empty WORKS / picks say 「作品は準備中です」 (no older lists, no stand-in), HERO poster; empty and failure still differ')
    page = open_page(browser, 1280, 800, {}, migration=False)
    older_lists_kept(page, '404 + switch off', switch_on=False)
    page.context.close()
    report.append('switched off before the plugin is up (404): still the 71 older works and the picks — the order of the two steps cannot empty the page')

    # ---------- 14 HERO: none → the poster; three MP4s → in order and round again; slow and silent WordPress ----------
    for label, ans, migration in (('empty, switch on', EMPTY['cx-creative-hero'], True), ('empty, switch off', EMPTY['cx-creative-hero'], False),
                                  ('only a YouTube card', (200, dict(HERO_FULL, items=[next(c for c in WORKS['items'] if c['title'] == 'Good Bye MV')])), True)):
        page = open_page(browser, 1280, 800, answers(cx_creative_hero=ans), migration=migration)
        page.wait_for_timeout(600)
        h = hero_state(page)
        assert h == {'src': '', 'paused': True, 'playing': False, 'toggle': False, 'poster': 'https://i.ytimg.com/vi/zKvRR8xT_zY/maxres1.jpg', 'posterShown': True}, (label, h)
        assert not page.errors, (label, page.errors)
        if label == 'empty, switch on':
            page.screenshot(path=str(out / '1280-hero-empty.png'))
        page.context.close()
    report.append('6 HERO with no video (empty with the switch on or off, or only a non-MP4 card): the poster, no other work played')
    if HAS_VIDEO:
        for width, height in ((1280, 800), (390, 844)):
            page = open_page(browser, width, height, answers(cx_creative_hero=(200, HERO_FULL)))
            wait_until(page, "(() => { const v = document.querySelector('.cxg-reel video'); return v && /hero-1\\.mp4$/.test(v.currentSrc) && !v.paused; })()", 8000)
            assert page.evaluate("document.querySelector('.cxg-reel__poster').getAttribute('src')") == UP + '2026/11/hero-1.jpg'
            assert page.evaluate("(() => { const v = document.querySelector('.cxg-reel video'); return !v.loop && v.muted && v.playsInline; })()")
            seen = ['hero-1.mp4']
            for name in ('hero-2.mp4', 'hero-3.mp4', 'hero-1.mp4'):                # 1 → 2 → 3 → round again
                wait_until(page, f"/{name.replace('.', '[.]')}$/.test(document.querySelector('.cxg-reel video').currentSrc)", 8000)
                seen.append(name)
            wait_until(page, "document.querySelector('.cxg-reel').classList.contains('is-playing')", 4000)
            assert page.evaluate('document.documentElement.scrollWidth - innerWidth') <= 0, width
            assert not page.errors, (width, page.errors)
            page.screenshot(path=str(out / f'{width}-hero-three.png'))
            page.context.close()
        report.append('7 HERO with three MP4s (1280 / 390): 1 → 2 → 3 → 1 in WordPress order, muted + inline, first thumb as the poster, no overflow')

        # WordPress answers after 4 s (the old 2.5 s limit dropped such an answer): the video still starts.
        page = open_page(browser, 1280, 800, answers(), hold=('cx-creative-hero',))
        page.wait_for_timeout(4000)
        h = hero_state(page)
        assert 'cx-creative-hero' in page.held and not h['src'] and h['posterShown'], h        # the poster while waiting
        send(page, 'cx-creative-hero', (200, HERO_FULL))
        wait_until(page, "(() => { const v = document.querySelector('.cxg-reel video'); return /hero-1\\.mp4$/.test(v.currentSrc) && !v.paused && document.querySelector('.cxg-reel').classList.contains('is-playing'); })()", 6000)
        to_works(page)
        assert len(strip_titles(page)) == 71 and not page.errors, page.errors          # WORKS on the older lists meanwhile
        page.context.close()
        report.append('5 slow WordPress (HERO slot answered after 4 s): the poster first, then the video starts and fades in')

        # WordPress never answers: the request gives up (8 s) and the HERO stops waiting (10 s); the poster stays.
        page = open_page(browser, 1280, 800, answers(), hold=('cx-creative-hero',))
        page.wait_for_timeout(10800)
        h = hero_state(page)
        assert not h['src'] and not h['playing'] and h['posterShown'], h
        try:
            send(page, 'cx-creative-hero', (200, HERO_FULL))                       # too late: ignored
        except Exception:
            pass                                                                    # the page already gave the request up
        page.wait_for_timeout(1200)
        assert not hero_state(page)['src'] and not page.errors, (hero_state(page), page.errors)
        page.context.close()
        report.append('5 WordPress silent: the poster stays; an answer after the limit is ignored (no late surprise)')

        # Autoplay refused (as on an iPhone in Low Power Mode): the poster stays and play() is not retried.
        refuse = ("window.__plays = 0; HTMLMediaElement.prototype.play = function () { window.__plays++; "
                  "return Promise.reject(new DOMException('refused', 'NotAllowedError')); };")
        page = open_page(browser, 390, 844, answers(cx_creative_hero=(200, HERO_FULL)), init=refuse)
        page.wait_for_timeout(800)
        for y in (200, 0, 300, 0):
            page.evaluate('(y) => window.scrollTo({ top: y, behavior: "instant" })', y)
            page.wait_for_timeout(150)
        h = hero_state(page)
        assert not h['src'] and not h['playing'] and not h['toggle'] and h['posterShown'], h
        assert page.evaluate('window.__plays') == 1, page.evaluate('window.__plays')
        assert any('does not allow the background video' in w for w in page.warnings) and not page.errors, (page.warnings[:6], page.errors)
        page.screenshot(path=str(out / '390-hero-autoplay-refused.png'))
        page.context.close()
        report.append('autoplay refused (iPhone Low Power Mode, simulated): the poster stays, play() tried once, no pause button')
    else:
        report.append('HERO: ffmpeg missing — the MP4 order, slow-answer and refused-autoplay checks were not run')

    # ---------- 15 PC / phone, during the move (71 older works) and after the switch (slot data) ----------
    for (width, height), migration in [(size, m) for size in ((1440, 900), (390, 844), (320, 640)) for m in (True, False)]:
        name = 'move' if migration else 'slots'
        page = open_page(browser, width, height, answers(), migration=migration)
        to_works(page)
        assert len(strip_titles(page)) == (71 if migration else len(WORK_TITLES)), (width, name)
        assert page.evaluate('document.documentElement.scrollWidth - innerWidth') <= 0, (width, name)
        page.screenshot(path=str(out / f'{width}-works-{name}.png'))
        page.evaluate("document.querySelector('#creative-solution').scrollIntoView()")
        page.wait_for_timeout(900)
        page.screenshot(path=str(out / f'{width}-solution-{name}.png'))
        if width == 390:
            open_from_works(page, 'Good Bye MV')
            page.wait_for_selector('.cxwv-phone.is-settled', timeout=8000)
            page.screenshot(path=str(out / f'390-video-{name}.png'))
            close(page)
        assert not page.errors, (width, name, page.errors)
        page.context.close()
    report.append('PC and phones (1440 / 390 / 320), during the move and after the switch: no horizontal scroll; the viewer opens')
    browser.close()

(out / 'report.txt').write_text('\n'.join(report) + '\n', encoding='utf-8')
print('creative slots: ok')
for line in report:
    print(' -', line)
