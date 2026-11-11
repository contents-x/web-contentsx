"""Browser checks for Creative X landing「01 CREATIVE SOLUTION」(2026-11). Run against a loopback preview.

python3 tools/preview-extensions.py --port 8797 &
python3 tests/test_creative_solution.py --url http://127.0.0.1:8797 --artifacts /tmp/cx-solution-qa [--channel chrome]
WordPress responses and images are replaced with the fixtures below, so the test needs no network access
(the YouTube embed is not loaded; the test checks the URL the player builds).
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
parser.add_argument('--channel', default=None, help='e.g. chrome to use the installed Chrome')
args = parser.parse_args()
out = Path(args.artifacts)
out.mkdir(parents=True, exist_ok=True)
PAGE_URL = args.url.rstrip('/') + '/services/creative-x/'
WIDTHS = [1440, 1280, 1024, 768, 640, 390, 375, 320]


def png(w, h, rgb=(200, 210, 230)):
    raw = b''.join(b'\x00' + bytes(rgb) * w for _ in range(h))
    def chunk(t, d):
        return struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    return b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(raw)) + chunk(b'IEND', b'')


PAGE = png(70, 99)                    # portrait manga page (A-size)
TALL = png(60, 200)                   # vertical-scroll page
THUMB = png(160, 90, (60, 80, 120))
GREY = png(120, 90, (200, 200, 200))  # YouTube's answer when maxresdefault does not exist
UP = 'https://cms.contentsx.jp/wp-content/uploads/2026/10/'

KAMI = {'id': 'opro-kamiless', 'title_ja': 'マンガでわかるカミレス【公共・自治体編】', 'view_type': 'spread',
        'thumbnail': UP + 'k-thumb.png', 'gallery': [UP + f'k-{i}.png' for i in range(1, 9)]}
OTHER = {'id': 'other-work', 'title_ja': '<img src=x onerror="window.__xss=1">別の漫画', 'view_type': 'spread',
         'gallery': [UP + 'o-1.png', UP + 'o-2.png', UP + 'o-3.png']}
TATE = {'id': 'tate', 'title_ja': '縦読み', 'view_type': 'vertical_only', 'gallery': [UP + 'tall-1.png', UP + 'tall-2.png']}
WORKS = [{'id': 'nogallery', 'title_ja': 'ページなし', 'gallery': []}, OTHER, KAMI]
VIDEOS = {
    'main': [],
    'viewer': [
        {'type': 'bizanime', 'title': '炎と紫電の空中戦', 'provider': 'youtube', 'video_id': '7m2ORgR-PDg'},
        {'type': 'bizanime', 'title': 'Good Bye MV', 'description': '', 'provider': 'youtube', 'video_id': 'V9ZC16hTlZI',
         'poster': 'https://i.ytimg.com/vi/V9ZC16hTlZI/maxresdefault.jpg', 'embed': 'https://attacker.example.com/embed'},
        {'type': 'bizvideo', 'title': 'サン', 'provider': 'youtube', 'video_id': 'DkmWuOSvCEY'},
        {'type': 'bizvideo', 'title': 'VLOG', 'description': '', 'provider': 'youtube', 'video_id': 'QqRlb_JGaHw'},
        {'type': 'bizvideo', 'title': 'broken', 'provider': 'youtube', 'video_id': 'bad"id'},
    ],
    'cases': [], 'playlists': [],
}


def route_for(videos=VIDEOS, works=WORKS, fail=False, videos_fail=False, hang=None):
    def route(r):
        u = r.request.url
        if '/wp-json/contentsx/v1/' in u:
            if '/wp-json/contentsx/v1/slots/' in u:
                # A WordPress without the Creative X slots (today's production): the older lists below.
                # The slots themselves are checked in tests/test_creative_slots.py.
                return r.fulfill(status=404, content_type='application/json', body='{"code":"not_found"}', headers={'Access-Control-Allow-Origin': '*'})
            if hang is not None:
                return hang.append(r)
            if fail or (videos_fail and '/bizanime-videos' in u):
                return r.abort()
            body = videos if '/bizanime-videos' in u else works if '/works' in u else []
            return r.fulfill(status=200, content_type='application/json', body=json.dumps(body))
        if u.startswith(UP):
            return r.fulfill(status=200, content_type='image/png', body=TALL if 'tall' in u else PAGE)
        if u.startswith('https://i.ytimg.com/'):
            return r.fulfill(status=200, content_type='image/png', body=GREY if 'maxresdefault' in u else THUMB)
        if u.startswith(('http://127.0.0.1:', 'http://localhost:', 'https://fonts.googleapis.com/', 'https://fonts.gstatic.com/')):
            return r.continue_()
        return r.abort()   # analytics, YouTube / Drive embeds
    return route


def open_page(browser, width, height=None, js=True, reduced=False, init=None, **route):
    ctx = browser.new_context(viewport={'width': width, 'height': height or (900 if width > 768 else 844)},
                              java_script_enabled=js, reduced_motion='reduce' if reduced else 'no-preference',
                              has_touch=width <= 768)
    page = ctx.new_page()
    page.errors = []
    page.warnings = []
    page.on('pageerror', lambda e: page.errors.append(str(e)))
    page.on('console', lambda m: page.warnings.append(m.text) if m.type == 'warning' else None)
    if init:
        page.add_init_script(init)
    page.route('**/*', route_for(**route))
    page.goto(PAGE_URL, wait_until='load')
    if js and 'hang' not in route:
        page.wait_for_function("document.querySelector('[data-cxcs]').classList.contains('is-ready')", timeout=10000)
    page.wait_for_timeout(300)
    return page


def to_section(page):
    page.evaluate("window.scrollTo({top: document.querySelector('#creative-solution').offsetTop, behavior: 'instant'})")
    page.wait_for_timeout(500)


def reveal(page):
    """Scroll through the section so every one-time reveal (sitewide-motion.js) has run."""
    top, h = page.evaluate("[document.querySelector('#creative-solution').offsetTop, document.querySelector('#creative-solution').offsetHeight]")
    for y in range(int(top), int(top + h), 300):
        page.evaluate('(y) => window.scrollTo({top: y, behavior: "instant"})', y)
        page.wait_for_timeout(60)
    page.wait_for_timeout(900)


def shoot(page, name):
    """Section screenshot without the fixed header on top of it."""
    page.add_style_tag(content='header{visibility:hidden!important}')
    page.locator('#creative-solution').screenshot(path=str(out / name))


def rect(page, sel):
    return page.locator(sel).first.evaluate('e => e.getBoundingClientRect().toJSON()')


def press_on(page, sel, touch=False):
    """Click / tap the middle of an element the way a visitor does. Inside a card the button's ::after
    covers everything, so the button is what receives it (Playwright's own click() refuses that)."""
    page.locator(sel).first.scroll_into_view_if_needed()
    r = rect(page, sel)
    x, y = r['left'] + r['width'] / 2, r['top'] + r['height'] / 2
    if touch:
        page.touchscreen.tap(x, y)
    else:
        page.mouse.click(x, y)


report = []


def done(message):
    report.append(message)
    print(message, flush=True)


with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, channel=args.channel) if args.channel else p.chromium.launch(headless=True)

    # ---------- layout at each width ----------
    for width in WIDTHS:
        page = open_page(browser, width)
        to_section(page)
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), f'horizontal overflow at {width}px'
        assert page.locator('#creative-solution .cxcs-index').inner_text().replace(' ', '') == '01/CREATIVESOLUTION'
        assert page.locator('#cxcs-title').inner_text().replace('\n', '') == '伝えたい価値を、最適なカタチへ。'
        names = page.locator('.cxcs-card__name').all_inner_texts()
        assert names == ['ビズマンガ', 'ビズアニメ', 'ビズビデオ'], names
        titles = page.locator('[data-cxcs-title]').all_inner_texts()
        assert titles == ['マンガでわかるカミレス【公共・自治体編】', 'Good Bye MV', 'VLOG'], titles
        assert page.locator('.cxcs-card button.cxcs-card__action').count() == 3
        assert page.locator('.cxcs-card a.cxcs-card__action').count() == 0
        assert page.locator('#creative-solution iframe, .cxwv iframe').count() == 0, 'no embed before a click'
        labels = page.locator('.cxcs-card__action > span').all_inner_texts()
        assert labels == ['マンガを読む', '動画を見る', '動画を見る'], labels
        # Pictures: manga cover whole (contain), video thumbnails 16:9 (maxres → hq fallback).
        assert page.locator('.cxcs-card--manga .cxcs-card__cover').evaluate('e => getComputedStyle(e).objectFit') == 'contain'
        for kind in ('anime', 'video'):
            box = rect(page, f'.cxcs-card--{kind} .cxcs-card__media')
            assert abs(box['width'] / box['height'] - 16 / 9) < 0.02, (width, kind, box)
        page.wait_for_function("[...document.querySelectorAll('.cxcs-card__thumb')].every(i => /hqdefault/.test(i.src))")
        cards = [rect(page, f'#cxcs-card-{k}') for k in ('manga', 'anime', 'video')]
        if width >= 769:
            assert len({round(c['top']) for c in cards}) == 1, f'three in a row at {width}px'
            assert cards[0]['right'] <= cards[1]['left'] and cards[1]['right'] <= cards[2]['left']
            assert page.locator('.cxcs-branch__map').evaluate('e => getComputedStyle(e).display') == 'none'
        else:
            assert cards[0]['bottom'] <= cards[1]['top'] and cards[1]['bottom'] <= cards[2]['top'], f'stacked at {width}px'
            assert page.locator('.cxcs-branch__map li').all_inner_texts() == ['マンガ', 'アニメ', '映像']
            assert cards[0]['width'] >= width - 48, f'cards nearly full width at {width}px'
            cols = page.locator('.cxcs-uses__list').evaluate("e => getComputedStyle(e).gridTemplateColumns.split(' ').length")
            assert cols == 2, f'uses 2×2 at {width}px'
        if width >= 1101:
            assert page.locator('.cxcs-uses__list').evaluate("e => getComputedStyle(e).gridTemplateColumns.split(' ').length") == 4
        # Nothing in the section leaves the screen; no text under 12px; buttons at least 44px tall.
        off = page.evaluate("""() => [...document.querySelectorAll('#creative-solution .cxcs-inner *')]
          .filter(e => { const r = e.getBoundingClientRect(); return r.width && (r.left < -0.5 || r.right > innerWidth + 0.5); }).length""")
        assert off == 0, f'{off} elements off screen at {width}px'
        small = page.evaluate("""() => [...document.querySelectorAll('#creative-solution *')].filter(e =>
          [...e.childNodes].some(n => n.nodeType === 3 && n.textContent.trim()) && e.getClientRects().length &&
          parseFloat(getComputedStyle(e).fontSize) < 12).map(e => e.textContent.trim())""")
        assert not small, (width, small)
        # Rendered buttons only (a card's static link is swapped for its button when WordPress answers).
        heights = page.locator('.cxcs-card__action').evaluate_all('a => a.filter(e => e.getClientRects().length).map(e => e.getBoundingClientRect().height)')
        assert heights and all(h >= 43.5 for h in heights), (width, heights)
        # Text inside each card stays inside it.
        spill = page.evaluate("""() => [...document.querySelectorAll('.cxcs-card')].flatMap(c => { const b = c.getBoundingClientRect();
          return [...c.querySelectorAll('.cxcs-card__body *, .cxcs-card__head *')].filter(e => { const r = e.getBoundingClientRect();
          return r.width && (r.right > b.right + .5 || r.left < b.left - .5 || r.bottom > b.bottom + .5); }).map(e => e.className); })""")
        assert not spill, (width, spill)
        reveal(page)
        hidden = page.evaluate("""() => ['.cxcs-head', '.cxcs-flow', '.cxcs-uses', '.cxcs-note']
          .filter(s => getComputedStyle(document.querySelector(s)).opacity !== '1')""")
        assert not hidden, f'not shown after scrolling at {width}px: {hidden}'
        shoot(page, f'solution-{width}.png')
        assert not page.errors, page.errors
        done(f'{width}px layout ok')
        page.context.close()

    # ---------- manga: PC spread, page turns, 拡大, Esc order, focus and scroll restored ----------
    page = open_page(browser, 1440)
    to_section(page)
    page.evaluate('window.scrollBy(0, 120)')
    y0 = page.evaluate('scrollY')
    press_on(page, '#cxcs-card-manga .cxcs-card__media')               # anywhere on the card opens it
    page.wait_for_selector('.cxwv.is-open')
    assert page.locator('.cxwv').get_attribute('role') == 'dialog' and page.locator('.cxwv').get_attribute('aria-modal') == 'true'
    assert page.locator('#cxwv-title').inner_text() == 'マンガでわかるカミレス【公共・自治体編】'
    assert page.evaluate("document.documentElement.classList.contains('cxwv-lock')")
    assert page.evaluate("document.querySelector('header').inert && document.querySelector('main').inert")
    page.wait_for_selector('.cxwv .cxmr.is-ready')
    # An open book (BizManga's page flip): right-bound, page 1 on the right.
    book = page.evaluate("""() => { const r = document.querySelector('.cxwv .cxmr-leaf--right'), l = document.querySelector('.cxwv .cxmr-leaf--left');
      return { right: r.querySelector('img').src.split('/').pop(), left: l.querySelector('img').src.split('/').pop(),
               rightIsRight: r.getBoundingClientRect().left > l.getBoundingClientRect().left }; }""")
    assert book == {'right': 'k-1.png', 'left': 'k-2.png', 'rightIsRight': True}, book
    assert page.locator('.cxwv .cxmr-count').inner_text() == '1-2 / 8'
    turn = 650                                                          # BizManga FLIP_DURATION 500ms + settle
    page.locator('.cxwv .cxmr-next').click()
    page.wait_for_timeout(turn)
    assert page.locator('.cxwv .cxmr-count').inner_text() == '3-4 / 8'
    page.keyboard.press('ArrowLeft')                                    # ← = next
    page.wait_for_timeout(turn)
    assert page.locator('.cxwv .cxmr-count').inner_text() == '5-6 / 8'
    page.keyboard.press('ArrowRight')
    page.wait_for_timeout(turn)
    assert page.locator('.cxwv .cxmr-count').inner_text() == '3-4 / 8'
    page.locator('.cxwv .cxmr-zoom').click()
    assert page.locator('.cxmr.is-full').count() == 1
    stage_h = rect(page, '.cxmr.is-full .cxmr-stage')['height']
    assert stage_h > 700, stage_h
    page.keyboard.press('Escape')                                       # closes 拡大 first
    assert page.locator('.cxmr.is-full').count() == 0 and page.locator('.cxwv.is-open').count() == 1
    page.keyboard.press('Escape')
    page.wait_for_timeout(260)                                          # the 0.2s fade-out
    assert page.locator('.cxwv').is_hidden()
    assert not page.evaluate("document.documentElement.classList.contains('cxwv-lock')")
    assert not page.evaluate("document.querySelector('main').inert")
    assert page.evaluate("document.activeElement.closest('#cxcs-card-manga') !== null"), 'focus back on the card'
    assert abs(page.evaluate('scrollY') - y0) <= 1, 'scroll position restored'
    done('manga: spread, page turns, 拡大, Esc order, focus/scroll restored ok')

    # ---------- video: built on click, plays at once, stops on close, one dialog at a time ----------
    press_on(page, '#cxcs-card-anime .cxcs-card__title')
    page.wait_for_selector('.cxwv iframe')
    src = page.locator('.cxwv iframe').get_attribute('src')
    assert src.startswith('https://www.youtube-nocookie.com/embed/V9ZC16hTlZI?autoplay=1'), src
    assert 'mute' not in src and 'attacker' not in src
    assert 'fullscreen' in page.locator('.cxwv iframe').get_attribute('allow')
    assert page.locator('.cxwv iframe').evaluate('e => e.allowFullscreen')
    assert page.evaluate("document.activeElement.classList.contains('cxwv-close')")
    # Opening another work replaces the first: still one dialog and one embed.
    page.evaluate("""() => window.cxWorks.load().then(d => window.cxWorks.open(window.cxWorks.find(d, 'video', 'QqRlb_JGaHw')))""")
    page.wait_for_timeout(200)
    assert page.locator('.cxwv').count() == 1 and page.locator('iframe').count() == 1
    assert 'QqRlb_JGaHw' in page.locator('.cxwv iframe').get_attribute('src')
    page.locator('.cxwv').click(position={'x': 5, 'y': 5})              # outside the panel
    assert page.locator('iframe').count() == 0, 'closing removes the embed at once'
    page.wait_for_timeout(260)
    assert page.locator('.cxwv').is_hidden()
    page.locator('#cxcs-card-video .cxcs-card__action').focus()
    page.keyboard.press('Enter')
    page.wait_for_selector('.cxwv iframe')
    page.locator('.cxwv-close').click()
    assert page.locator('iframe').count() == 0
    assert page.evaluate("document.activeElement.closest('#cxcs-card-video') !== null")
    assert not page.evaluate('window.__xss'), 'WordPress text is never parsed as HTML'
    reveal(page)
    shoot(page, 'solution-after-close.png')
    assert not page.errors, page.errors
    page.context.close()
    done('video: embed on click, autoplay with sound, fullscreen allowed, close/outside/Esc stop it, single dialog ok')

    # ---------- phone: one page at a time, swipe, full-screen dialog ----------
    page = open_page(browser, 390)
    to_section(page)
    press_on(page, '#cxcs-card-manga .cxcs-card__action', touch=True)
    page.wait_for_selector('.cxwv .cxmr.is-ready')
    assert page.locator('.cxwv .cxmr-stage .cxmr-page').count() == 1
    assert page.locator('.cxwv .cxmr-count').inner_text() == '1 / 8'
    page.wait_for_timeout(400)                                          # the 0.35s rise-in
    panel = rect(page, '.cxwv-panel')
    assert panel['width'] == 390 and panel['height'] >= 840, panel
    page_box = rect(page, '.cxwv .cxmr-page')
    assert page_box['width'] >= 300, page_box
    assert rect(page, '.cxwv .cxmr-bar')['bottom'] <= 844
    page.locator('.cxwv .cxmr-next').tap()
    page.wait_for_timeout(650)
    assert page.locator('.cxwv .cxmr-count').inner_text() == '2 / 8'
    page.screenshot(path=str(out / 'solution-390-manga.png'))
    page.locator('.cxwv-close').tap()
    press_on(page, '#cxcs-card-video .cxcs-card__media', touch=True)
    page.wait_for_selector('.cxwv iframe')
    # On a phone the phone frame thins to a bezel: the video keeps 16:9 and nearly the whole width.
    frame = rect(page, '.cxwv .cxvp-stage')
    screen = rect(page, '.cxwv-phone__screen')
    assert abs(frame['width'] / frame['height'] - 16 / 9) < 0.02 and frame['width'] >= 340, frame
    assert frame == screen, (frame, screen)
    page.screenshot(path=str(out / 'solution-390-video.png'))
    page.keyboard.press('Escape')
    assert page.locator('iframe').count() == 0
    page.context.close()
    done('phone: single page, page turn, full-screen dialog, 16:9 video ok')

    # ---------- the named work is missing: no stand-in work (2026-11 slots spec) ----------
    page = open_page(browser, 1280, works=[TATE])
    assert any('opro-kamiless' in w for w in page.warnings), ('missing pick is reported', page.warnings)
    assert page.locator('#cxcs-card-manga .cxcs-card__picture').count() == 0 and page.locator('#cxcs-card-manga [data-cxcs-title]').is_hidden()
    assert page.locator('#cxcs-card-manga [data-cxcs-status]').inner_text() == '作品は準備中です。'
    assert page.locator('#cxcs-card-manga a.cxcs-card__action').get_attribute('href') == 'https://bizmanga.contentsx.jp/biz-library'
    page.context.close()
    # ---------- vertical manga ----------
    page = open_page(browser, 1280, works=[dict(TATE, id='opro-kamiless')])
    page.locator('#cxcs-card-manga .cxcs-card__action').click()
    page.wait_for_selector('.cxwv .cxmr-stage.is-vertical')
    assert page.locator('.cxwv .cxmr-book, .cxwv .cxmr-pbook').count() == 0, 'vertical works keep their scroll, no book'
    assert page.locator('#cxcs-card-manga [data-cxcs-title]').inner_text() == '縦読み'
    page.context.close()
    done('missing pick: no stand-in work; vertical reading ok')

    # ---------- WordPress fails / partly fails / loading ----------
    page = open_page(browser, 1280, fail=True)
    assert page.locator('.cxcs-card a.cxcs-card__action').count() == 3, 'service links stay'
    assert page.locator('.cxcs-card button').count() == 0
    assert page.locator('[data-cxcs-status]').all_inner_texts() == ['作品を読み込めませんでした。'] * 3
    assert page.locator('[data-cxcs-title]:visible').count() == 0, 'no placeholder works'
    hrefs = page.locator('.cxcs-card a.cxcs-card__action').evaluate_all('a => a.map(e => e.getAttribute("href"))')
    assert hrefs == ['https://bizmanga.contentsx.jp/biz-library', 'https://bizmanga.contentsx.jp/bizanime', '/services/#bizvideo'], hrefs
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    reveal(page)
    shoot(page, 'solution-wp-failed.png')
    page.context.close()
    page = open_page(browser, 1280, videos_fail=True)
    assert page.locator('#cxcs-card-manga button.cxcs-card__action').count() == 1
    assert page.locator('#cxcs-card-anime a.cxcs-card__action').count() == 1
    assert page.locator('#cxcs-card-video [data-cxcs-status]').inner_text() == '作品を読み込めませんでした。'
    page.context.close()
    page = open_page(browser, 1280, videos={'viewer': [], 'cases': [], 'playlists': []})
    assert page.locator('#cxcs-card-anime [data-cxcs-status]').inner_text() == '作品は準備中です。'
    page.context.close()
    held = []
    page = open_page(browser, 1280, hang=held)
    assert page.locator('[data-cxcs]').get_attribute('aria-busy') == 'true'
    assert page.locator('.cxcs-card__fallback').first.evaluate('e => getComputedStyle(e).opacity') == '0'
    for r in held:                               # answer the held requests, or closing the page can wait forever
        r.abort()
    page.context.close()
    done('WordPress failure, partial failure, empty data and loading state ok')

    # ---------- JS off, reduced motion ----------
    page = open_page(browser, 390, js=False)
    assert page.locator('.cxcs-card a.cxcs-card__action').count() == 3
    assert page.locator('.cxcs-card__fallback').first.evaluate('e => getComputedStyle(e).opacity') != '0'
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    # add_style_tag never finishes with JavaScript off, so this shot keeps the header.
    page.locator('#creative-solution').screenshot(path=str(out / 'solution-nojs-390.png'))
    page.context.close()
    page = open_page(browser, 1440, reduced=True)
    to_section(page)
    assert page.locator('.cxcs-card').first.evaluate('e => getComputedStyle(e).transitionDuration') == '0s'
    assert page.locator('.cxcs-head').evaluate('e => getComputedStyle(e).opacity') == '1'
    page.context.close()
    done('JS off and reduced motion ok')

    # ---------- backdrop: on the HERO stage (the page as built), and alone (moved out of the stage) ----------
    page = open_page(browser, 1440)
    assert page.locator('.cxg-stage #creative-solution').count() == 1
    assert page.locator('#creative-solution').evaluate("e => e.classList.contains('cxcs--on-stage') && !e.classList.contains('has-hero-backdrop') && getComputedStyle(e).backgroundColor === 'rgba(0, 0, 0, 0)'")
    # No second video: nothing in this section, and only the HERO's own one on the page.
    assert page.locator('#creative-solution video').count() == 0 and page.locator('video').count() <= 1, 'no second video'
    page.context.close()
    alone = """document.addEventListener('readystatechange', () => { if (document.readyState !== 'interactive') return;
      const s = document.querySelector('#creative-solution'), st = document.querySelector('.cxg-stage'); if (s && st) st.after(s); });"""
    page = open_page(browser, 1440, init=alone)
    for _ in range(40):
        if page.evaluate("document.querySelector('#creative-solution').classList.contains('has-hero-backdrop')"):
            break
        page.wait_for_timeout(100)
    assert page.evaluate("(() => { const e = document.querySelector('#creative-solution'); return !e.closest('.cxg-stage') && e.classList.contains('has-hero-backdrop') && !e.classList.contains('cxcs--on-stage'); })()")
    assert page.locator('.cxcs-backdrop__img').get_attribute('src') == page.locator('.cxg-reel__poster').get_attribute('src')
    assert page.locator('#creative-solution video').count() == 0
    page.context.close()
    done('backdrop: transparent on the HERO stage; alone, the HERO poster reused (no second video) ok')

    browser.close()

(out / 'report.txt').write_text('\n'.join(report) + '\n', encoding='utf-8')
print('OK')
