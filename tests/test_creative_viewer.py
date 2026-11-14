"""Browser checks for the Creative X work viewer (js/cx-works.js + book mode of js/cx-manga-reader.js, 2026-11).

python3 tests/test_creative_viewer.py --url http://127.0.0.1:8796 --artifacts /tmp/cx-viewer-qa [--channel chrome]
One viewer for 02 WORKS and 03 CREATIVE SOLUTION: manga as a book with BizManga biz-library's page flip,
anime / video on a phone lying on its side. WordPress answers and images are fixtures (no network); the
YouTube embed is not loaded, only the URL the player builds is checked. The page-level flows (open from each
section, focus, scroll, Esc order) are also in tests/test_creative_works.py and tests/test_creative_solution.py.
"""
import argparse
import json
import struct
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
PAGE = args.url.rstrip('/') + '/services/creative-x/'


def png(w, h, rgb):
    raw = b''.join(b'\x00' + bytes(rgb) * w for _ in range(h))
    def chunk(t, d):
        return struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    return b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(raw)) + chunk(b'IEND', b'')


UP = 'https://cms.contentsx.jp/wp-content/uploads/2026/10/'
PAGES = {i: png(70, 100, (240 - i * 12, 230, 210 + i * 4)) for i in range(1, 8)}
THUMB = png(160, 90, (60, 90, 140))
WORKS = [
    {'id': 'book', 'title_ja': '本の作品', 'view_type': 'spread', 'thumbnail': UP + 'book-thumb.png', 'gallery': [UP + f'book-{i}.png' for i in range(1, 8)]},
    {'id': 'tate', 'title_ja': '縦読みの作品', 'view_type': 'vertical_only', 'thumbnail': UP + 'tate-thumb.png', 'gallery': [UP + f'tate-{i}.png' for i in range(1, 4)]},
]
VIDEOS = {'viewer': [{'type': 'bizanime', 'title': 'Good Bye MV', 'provider': 'youtube', 'video_id': 'V9ZC16hTlZI'},
                     {'type': 'bizvideo', 'title': 'VLOG', 'provider': 'youtube', 'video_id': 'QqRlb_JGaHw'}],
          'cases': [], 'playlists': []}


def open_page(browser, width, height, reduced=False):
    ctx = browser.new_context(viewport={'width': width, 'height': height}, has_touch=width <= 768, reduced_motion='reduce' if reduced else 'no-preference')
    page = ctx.new_page()
    page.errors = []
    page.on('pageerror', lambda e: page.errors.append(str(e)))

    def route(r):
        u = r.request.url
        if '/wp-json/contentsx/v1/' in u:
            if '/wp-json/contentsx/v1/slots/' in u:
                # A WordPress without the Creative X slots (today's production): the older lists below.
                # The slots themselves are checked in tests/test_creative_slots.py.
                return r.fulfill(status=404, content_type='application/json', body='{"code":"not_found"}', headers={'Access-Control-Allow-Origin': '*'})
            return r.fulfill(status=200, content_type='application/json', body=json.dumps(VIDEOS if '/bizanime-videos' in u else WORKS))
        if u.startswith(UP):
            name = u.rsplit('/', 1)[-1]
            n = int(name.split('-')[1].split('.')[0]) if name[-5].isdigit() else 0
            return r.fulfill(status=200, content_type='image/png', body=PAGES.get(n, THUMB))
        if u.startswith(('https://i.ytimg.com/', 'https://contentsx.jp/')):
            # i.ytimg.com answers with Access-Control-Allow-Origin: * (the 3D phone draws the poster in WebGL).
            return r.fulfill(status=200, content_type='image/png', body=THUMB, headers={'Access-Control-Allow-Origin': '*'})
        if u.startswith(('http://127.0.0.1:', 'https://fonts.googleapis.com/', 'https://fonts.gstatic.com/')):
            return r.continue_()
        return r.abort()
    page.route('**/*', route)
    page.goto(PAGE, wait_until='networkidle')
    page.wait_for_timeout(600)
    return page


def open_work(page, kind, wid):
    page.evaluate("([k, i]) => window.cxWorks.load().then(d => window.cxWorks.open(window.cxWorks.find(d, k, i)))", [kind, wid])
    page.wait_for_timeout(900)


def leaf_srcs(page):
    return page.evaluate("""() => { const r = document.querySelector('.cxwv .cxmr-leaf--right img'), l = document.querySelector('.cxwv .cxmr-leaf--left img');
      return [r && r.src.split('/').pop(), l && l.src.split('/').pop()]; }""")


report = []
with sync_playwright() as p:
    browser = p.chromium.launch(channel=args.channel) if args.channel else p.chromium.launch()

    # ---------- PC: the book, right-bound, both turn directions ----------
    page = open_page(browser, 1440, 900)
    open_work(page, 'manga', 'book')
    assert page.locator('.cxwv').get_attribute('data-kind') == 'manga' and page.locator('.cxwv-phone').count() == 0, 'no phone frame on manga'
    assert page.locator('.cxwv .cxmr-stage').evaluate("e => e.classList.contains('is-book') && e.classList.contains('is-spread')")
    assert leaf_srcs(page) == ['book-1.png', 'book-2.png']
    box = page.evaluate("""() => { const r = s => document.querySelector(s).getBoundingClientRect().toJSON();
      return { book: r('.cxwv .cxmr-book'), right: r('.cxwv .cxmr-leaf--right'), left: r('.cxwv .cxmr-leaf--left'), spine: r('.cxwv .cxmr-spine') }; }""")
    assert box['right']['left'] >= box['left']['right'] - 1, box                      # page 1 on the right
    assert abs((box['spine']['left'] + box['spine']['width'] / 2) - (box['book']['left'] + box['book']['width'] / 2)) < 2, box
    assert abs(box['right']['width'] / box['right']['height'] - 0.7) < 0.02, box     # page shape from page 1 (70×100)
    assert box['book']['height'] > 600, box
    # Next: the LEFT page turns on the spine (hinge = its right edge) over to the right.
    page.locator('.cxwv .cxmr-next').click()
    page.wait_for_timeout(240)
    mid = page.evaluate("""() => { const f = document.querySelector('.cxwv .cxmr-flip'); const m = new DOMMatrix(getComputedStyle(f).transform);
      return { cls: f.className, origin: getComputedStyle(f).transformOrigin, width: f.offsetWidth, front: f.querySelector('.cxmr-flip__front img').src.split('/').pop(),
               back: f.querySelector('.cxmr-flip__back img').src.split('/').pop(), angle: Math.round(Math.atan2(-m.m13, m.m11) * 180 / Math.PI) }; }""")
    assert 'is-active' in mid['cls'] and 'is-left' in mid['cls'] and mid['origin'].startswith(f"{mid['width']}px"), mid
    assert mid['front'] == 'book-2.png' and mid['back'] == 'book-3.png', mid          # BizManga goNext: current left → next right
    assert 30 < abs(mid['angle']) < 180, mid
    page.screenshot(path=str(out / '1440-book-turning.png'))
    page.wait_for_timeout(450)
    assert leaf_srcs(page) == ['book-3.png', 'book-4.png'] and page.locator('.cxwv .cxmr-count').inner_text() == '3-4 / 7'
    assert page.locator('.cxwv .cxmr-flip.is-active').count() == 0
    # Previous: the RIGHT page turns over to the left.
    page.locator('.cxwv .cxmr-prev').click()
    page.wait_for_timeout(240)
    mid = page.evaluate("""() => { const f = document.querySelector('.cxwv .cxmr-flip'); return { cls: f.className, origin: getComputedStyle(f).transformOrigin,
      front: f.querySelector('.cxmr-flip__front img').src.split('/').pop(), back: f.querySelector('.cxmr-flip__back img').src.split('/').pop() }; }""")
    assert 'is-right' in mid['cls'] and mid['origin'].startswith('0px') and mid['front'] == 'book-3.png' and mid['back'] == 'book-2.png', mid
    page.wait_for_timeout(450)
    assert leaf_srcs(page) == ['book-1.png', 'book-2.png']
    # Click halves turn too (left = next); an odd last page faces the thanks page.
    page.locator('.cxwv .cxmr-stage').click(position={'x': 200, 'y': 300})
    page.wait_for_timeout(700)
    for _ in range(2):
        page.keyboard.press('ArrowLeft')
        page.wait_for_timeout(700)
    assert page.locator('.cxwv .cxmr-count').inner_text() == '7 / 7' and leaf_srcs(page) == ['book-7.png', 'thanks_v02.webp']
    assert page.locator('.cxwv .cxmr-next').is_disabled()
    page.screenshot(path=str(out / '1440-book-last.png'))
    # A turn in progress ignores more clicks (no double turn).
    page.keyboard.press('ArrowRight'); page.keyboard.press('ArrowRight')
    page.wait_for_timeout(700)
    assert page.locator('.cxwv .cxmr-count').inner_text() == '5-6 / 7'
    assert not page.errors, page.errors
    page.context.close()
    report.append('PC book: right-bound spread, spine, next/previous turn direction and faces, click halves, thanks page, no double turn')

    # ---------- phone: one page, BizManga mobileFlipTo ----------
    page = open_page(browser, 390, 844)
    open_work(page, 'manga', 'book')
    page.wait_for_timeout(400)
    assert page.locator('.cxwv .cxmr-stage').evaluate("e => e.classList.contains('is-book') && e.classList.contains('is-single')")
    pg = page.locator('.cxwv .cxmr-pbook__page').bounding_box()
    assert pg['width'] >= 340 and abs(pg['width'] / pg['height'] - 0.7) < 0.02, pg     # as large as the stage
    page.locator('.cxwv .cxmr-next').tap()
    page.wait_for_timeout(240)
    mid = page.evaluate("""() => { const f = document.querySelector('.cxwv .cxmr-pflip'); return { active: f.classList.contains('is-active'), origin: getComputedStyle(f).transformOrigin,
      front: f.querySelector('.cxmr-pflip__front img').src.split('/').pop(), back: f.querySelector('.cxmr-pflip__back img').src.split('/').pop(),
      under: document.querySelector('.cxwv .cxmr-pbook__page').src.split('/').pop() }; }""")
    assert mid['active'] and mid['origin'].startswith('0px') and mid == {**mid, 'front': 'book-1.png', 'back': 'book-2.png', 'under': 'book-2.png'}, mid
    page.screenshot(path=str(out / '390-page-turning.png'))
    page.wait_for_timeout(450)
    assert page.locator('.cxwv .cxmr-count').inner_text() == '2 / 7'
    # Swipe right = previous.
    st = page.locator('.cxwv .cxmr-stage').bounding_box()
    page.evaluate("""([x, y]) => { const s = document.querySelector('.cxwv .cxmr-stage');
      s.dispatchEvent(new PointerEvent('pointerdown', { clientX: x, clientY: y, pointerType: 'touch', bubbles: true }));
      s.dispatchEvent(new PointerEvent('pointerup', { clientX: x + 120, clientY: y, pointerType: 'touch', bubbles: true })); }""", [st['x'] + 80, st['y'] + 200])
    page.wait_for_timeout(700)
    assert page.locator('.cxwv .cxmr-count').inner_text() == '1 / 7'
    page.context.close()
    report.append('phone book: one page as large as the stage, left-edge turn (mobileFlipTo faces), tap and swipe')

    # ---------- vertical works keep their scroll ----------
    page = open_page(browser, 1280, 800)
    open_work(page, 'manga', 'tate')
    assert page.locator('.cxwv .cxmr-stage.is-vertical').count() == 1 and page.locator('.cxwv .cxmr-book, .cxwv .cxmr-pbook').count() == 0
    assert page.locator('.cxwv .cxmr-stage .cxmr-page').count() == 3
    page.context.close()
    report.append('vertical work: scroll reading, no book')

    # ---------- reduced motion: pages change without the turn ----------
    page = open_page(browser, 1280, 800, reduced=True)
    open_work(page, 'manga', 'book')
    page.locator('.cxwv .cxmr-next').click()
    page.wait_for_timeout(60)
    assert page.locator('.cxwv .cxmr-count').inner_text() == '3-4 / 7' and page.locator('.cxwv .cxmr-flip.is-active').count() == 0
    assert page.locator('.cxwv-panel').evaluate('e => getComputedStyle(e).transitionDuration') == '0s'
    page.context.close()
    report.append('reduced motion: instant page change, no rise-in')

    # ---------- video on a phone lying on its side ----------
    for width, height, ratio in ((1440, 900, 2), (1280, 720, 2), (390, 844, 16 / 9), (844, 390, 2)):
        page = open_page(browser, width, height)
        open_work(page, 'video', 'QqRlb_JGaHw')
        page.wait_for_timeout(400)
        assert page.locator('.cxwv').get_attribute('data-kind') == 'video' and page.locator('.cxwv .cxmr').count() == 0, 'no book on video'
        geo = page.evaluate("""() => { const r = s => document.querySelector(s).getBoundingClientRect().toJSON();
          const f = document.querySelector('.cxwv-phone__screen iframe').getBoundingClientRect();
          const hits = [[.5, .5], [.04, .96], [.96, .96], [.96, .04]].map(([x, y]) => (document.elementFromPoint(f.left + f.width * x, f.top + f.height * y) || {}).tagName);
          return { phone: r('.cxwv-phone'), frame: r('.cxwv-phone__frame'), screen: r('.cxwv-phone__screen'), iframe: f.toJSON(), hits, head: r('.cxwv-head') }; }""")
        assert geo['iframe'] == geo['screen'], (width, geo)                               # the player fills the screen
        assert set(geo['hits']) == {'IFRAME'}, (width, geo['hits'])                       # nothing over the player's corners
        assert abs(geo['screen']['width'] / geo['screen']['height'] - ratio) < 0.02, (width, geo['screen'])
        assert geo['frame']['left'] >= 0 and geo['frame']['right'] <= width and geo['frame']['bottom'] <= height + 1, (width, geo['frame'])
        assert geo['head']['bottom'] <= geo['phone']['top'] + 1, (width, geo)             # title above the phone
        if width <= 768:
            assert geo['screen']['width'] >= width - 50, (width, geo['screen'])           # no phone inside the phone
        else:
            assert geo['frame']['width'] - geo['screen']['width'] >= 14, (width, geo)     # a real bezel on PC
        assert page.locator('.cxwv iframe').get_attribute('src').startswith('https://www.youtube-nocookie.com/embed/QqRlb_JGaHw?autoplay=1')
        page.wait_for_selector('.cxwv-phone.is-settled', timeout=6000)
        page.wait_for_timeout(400)
        page.screenshot(path=str(out / f'{width}x{height}-phone.png'))
        page.keyboard.press('Escape')
        assert page.locator('iframe').count() == 0, 'closing stops the video at once'
        page.context.close()
    report.append('video: phone frame on PC (2:1 screen, bezel), 16:9 edge to edge on phones, landscape phones by height; player fills the screen, corners uncovered, stops on close')

    # ---------- the 3D phone (js/cx-phone-3d.js, three.js r170) ----------
    STATE = """() => { const d = document.querySelector('.cxwv'), c = document.querySelector('.cxwv-gl');
      const s = document.querySelector('.cxwv-phone__screen'), f = document.querySelector('.cxwv-phone__frame');
      const r = c && c.getBoundingClientRect();
      return { canvases: document.querySelectorAll('canvas').length, inDialog: !!c && c.parentNode === d, w: r && r.width, h: r && r.height,
        pe: c && getComputedStyle(c).pointerEvents, screen: s && getComputedStyle(s).opacity, frame: f && getComputedStyle(f).boxShadow,
        phone: (document.querySelector('.cxwv-phone') || {}).className, rect: s && s.getBoundingClientRect().toJSON() }; }"""
    for width, height in ((1440, 900), (1280, 720), (390, 844)):
        page = open_page(browser, width, height)
        page.evaluate("() => { window.__cxv = []; document.addEventListener('cxworks:viewer', e => window.__cxv.push(e.detail.open)); }")
        page.evaluate("() => window.cxWorks.load().then(d => window.cxWorks.open(window.cxWorks.find(d, 'anime', 'V9ZC16hTlZI')))")
        page.wait_for_selector('.cxwv-phone.is-3d.is-settled', timeout=6000)
        # The 3D screen must be the player's box to the pixel. With the player hidden, the canvas shows the
        # 3D screen (dark glass, a little lighter) inside the bezel (black glass): the edge between them must
        # fall on the player's edges, on all four sides.
        page.wait_for_timeout(700)
        page.evaluate("() => { document.querySelector('.cxwv-phone__screen').style.visibility = 'hidden'; }")
        st = page.evaluate(STATE)
        shot = out / f'{width}x{height}-3d-screen.png'
        page.screenshot(path=str(shot))
        px = page.evaluate("""async (src) => { const img = new Image(); img.src = src; await img.decode();
          const c = document.createElement('canvas'); c.width = img.width; c.height = img.height; const x = c.getContext('2d'); x.drawImage(img, 0, 0);
          const s = document.querySelector('.cxwv-phone__screen').getBoundingClientRect(); const k = img.width / innerWidth;
          const at = (X, Y) => { const d = x.getImageData(Math.round(X * k), Math.round(Y * k), 1, 1).data; return d[0] + d[1] + d[2]; };
          const cx = s.left + s.width / 2, cy = s.top + s.height / 2;
          return { top: [at(cx, s.top + 3), at(cx, s.top - 3)], bottom: [at(cx, s.bottom - 3), at(cx, s.bottom + 3)],
                   left: [at(s.left + 3, cy), at(s.left - 3, cy)], right: [at(s.right - 3, cy), at(s.right + 3, cy)] }; }""",
          'data:image/png;base64,' + __import__('base64').b64encode(shot.read_bytes()).decode())
        # PC only: on phones the bezel is 7px and the metal edge starts 3–4px from the screen, too close for
        # a colour check (there the screen box itself is checked below, and the phone is built from it).
        if width > 768:
            for side, (inside, outside) in px.items():
                assert inside - outside >= 15 and outside < 90, (width, side, px)
        page.evaluate("() => { document.querySelector('.cxwv-phone__screen').style.visibility = ''; }")
        assert st['canvases'] == 1 and st['inDialog'] and abs(st['w'] - width) < 2 and abs(st['h'] - height) < 2, (width, st)
        assert st['pe'] == 'none' and st['frame'] == 'none', (width, st)   # the CSS phone's drawing gives way
        assert page.evaluate("getComputedStyle(document.querySelector('.cxwv-phone__screen')).opacity") == '1'
        # Nothing over the player's corners (the canvas is behind the panel and lets clicks through).
        hits = page.evaluate("""() => { const f = document.querySelector('.cxwv-phone__screen iframe').getBoundingClientRect();
          return [[.5, .5], [.03, .97], [.97, .97], [.97, .03], [.03, .03]].map(([x, y]) => document.elementFromPoint(f.left + f.width * x, f.top + f.height * y).tagName); }""")
        assert set(hits) == {'IFRAME'}, (width, hits)
        page.screenshot(path=str(out / f'{width}x{height}-3d-settled.png'))
        if width > 768:
            page.mouse.click(4, height - 4)                                # outside: closes through the canvas
        else:
            page.locator('.cxwv-close').click()                            # phones: full-screen dialog, no outside
        page.wait_for_timeout(300)
        after = page.evaluate(STATE)
        assert after['canvases'] == 0 and page.locator('iframe').count() == 0, (width, after)
        assert page.evaluate('window.__cxv') == [True, False], page.evaluate('window.__cxv')
        # Open and close again: one canvas while open, none after (WebGL released each time).
        for _ in range(3):
            page.evaluate("() => window.cxWorks.load().then(d => window.cxWorks.open(window.cxWorks.find(d, 'video', 'QqRlb_JGaHw')))")
            page.wait_for_selector('.cxwv-phone.is-settled', timeout=6000)
            assert page.evaluate("document.querySelectorAll('canvas').length") == 1
            page.keyboard.press('Escape')
            page.wait_for_timeout(250)
            assert page.evaluate("document.querySelectorAll('canvas').length") == 0
        assert not page.errors, page.errors
        page.context.close()
    report.append('3D phone: WebGL canvas over the dialog, entrance then still; the 3D screen is the player\'s box to the pixel; player on top with all corners free; outside click closes; canvas and context released on every close; cxworks:viewer open/close')

    # Fallbacks: the module cannot be fetched, or there is no WebGL2 → the CSS phone, same player.
    for case in ('blocked', 'no-webgl'):
        page = open_page(browser, 1280, 800)
        asked = []
        page.on('request', lambda r: asked.append(r.url) if 'cx-phone-3d' in r.url else None)
        if case == 'blocked':
            page.route('**/js/cx-phone-3d.js', lambda r: r.abort())
        else:
            page.evaluate('() => { delete window.WebGL2RenderingContext; }')
        open_work(page, 'video', 'QqRlb_JGaHw')
        page.wait_for_timeout(500)
        st = page.evaluate(STATE)
        assert st['canvases'] == 0 and 'is-3d' not in st['phone'] and st['screen'] == '1' and st['frame'] != 'none', (case, st)
        assert page.locator('.cxwv-phone__screen iframe').count() == 1, case
        assert (case == 'blocked') == bool(asked), (case, asked)
        page.screenshot(path=str(out / f'1280x800-phone-fallback-{case}.png'))
        page.keyboard.press('Escape')
        page.context.close()
    report.append('3D phone fallback: module blocked / no WebGL2 → CSS phone with the same player (no module request without WebGL2)')

    # Reduced motion: no entrance, the phone is straight on at once.
    page = open_page(browser, 1280, 800, reduced=True)
    page.evaluate("() => window.cxWorks.load().then(d => window.cxWorks.open(window.cxWorks.find(d, 'video', 'QqRlb_JGaHw')))")
    page.wait_for_selector('.cxwv-phone.is-3d.is-settled', timeout=6000)
    st = page.evaluate("() => ({ op: document.querySelector('.cxwv-gl').style.opacity, screen: getComputedStyle(document.querySelector('.cxwv-phone__screen')).opacity })")
    assert st == {'op': '1', 'screen': '1'}, st
    page.context.close()
    report.append('3D phone, reduced motion: straight on at once, player shown without a fade')

    # ---------- one viewer for both sections ----------
    page = open_page(browser, 1280, 800)
    page.locator('#works .cxw-open').click()
    page.wait_for_timeout(700)
    from_works = page.evaluate("[document.querySelectorAll('.cxwv').length, document.querySelector('.cxwv').dataset.kind]")
    page.keyboard.press('Escape'); page.wait_for_timeout(300)
    page.locator('#cxcs-card-anime .cxcs-card__action').click()
    page.wait_for_timeout(700)
    from_solution = page.evaluate("[document.querySelectorAll('.cxwv').length, document.querySelector('.cxwv').dataset.kind, !!document.querySelector('.cxwv-phone iframe')]")
    assert from_works == [1, 'manga'] and from_solution == [1, 'anime', True], (from_works, from_solution)
    assert page.locator('.cxw-modal').count() == 0, 'WORKS has no dialog of its own'
    assert not page.errors, page.errors
    page.context.close()
    report.append('WORKS and CREATIVE SOLUTION open the same single viewer')
    browser.close()

(out / 'report.txt').write_text('\n'.join(report) + '\n', encoding='utf-8')
print('creative viewer: ok')
for line in report:
    print(' -', line)
