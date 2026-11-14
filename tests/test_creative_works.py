"""Browser checks for the Creative X landing WORKS gallery (2026-11).

python3 tests/test_creative_works.py --url http://127.0.0.1:5500 --artifacts /tmp/cx-creative-works-qa
Run against a loopback preview (tools/preview-extensions.py). WordPress answers and images are replaced
with the fixtures below, so no network is needed. --channel chrome uses the installed Google Chrome.
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
widths = [320, 375, 390, 768, 1280, 1440]


def png(w, h, rgb):
    raw = b''.join(b'\x00' + bytes(rgb) * w for _ in range(h))
    def chunk(t, d):
        return struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    return b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(raw)) + chunk(b'IEND', b'')


PAGE_IMG = png(70, 100, (230, 220, 200))
THUMB = png(160, 90, (60, 90, 140))
UP = 'https://cms.contentsx.jp/wp-content/uploads/2026/10/'


def manga(i, **kw):
    w = {'id': f'm{i}', 'title_ja': f'マンガ{i}', 'subtitle_ja': 'サービス紹介マンガ', 'categories': ['商品紹介', '営業'],
         'view_type': 'spread', 'thumbnail': UP + f'm{i}-thumb.png', 'gallery': [UP + f'm{i}-{p}.png' for p in range(1, 6)],
         'point': '導入前の悩みから導入後の変化までを描いた構成です。' * (6 if i == 1 else 1), 'media': ['採用サイト', 'SNS'] if i == 1 else [],
         'spec': {'pages': '5P'}, 'client': '実在しない会社'}
    w.update(kw)
    return w


WORKS = [manga(1), manga(2, title_ja='<img src=x onerror="window.__xss=1">マンガ2'), manga(3, gallery=[]),
         manga(4, gallery=['https://evil.example.com/p.png']), manga(5, view_type='vertical_only')]
VIDEOS = {
    'main': [{'title': 'I eye', 'provider': 'youtube', 'video_id': 'CduBxsawUkQ'}],
    'viewer': [
        {'type': 'bizanime', 'title': 'Good Bye MV', 'provider': 'youtube', 'video_id': 'V9ZC16hTlZI'},
        {'type': 'bizanime', 'title': '【MV】目MEめぇ～愛 I eye', 'provider': 'drive', 'video_id': '1kffZJKMAMB9rJGVKYxSgjbDs5UI99BTQ', 'poster': 'https://contentsx.jp/material/service-2026/bizanime-ieye.jpg'},
        {'type': 'bizvideo', 'title': 'サン', 'provider': 'youtube', 'video_id': 'DkmWuOSvCEY'},
        {'type': 'bizvideo', 'title': 'VLOG', 'provider': 'youtube', 'video_id': 'QqRlb_JGaHw'},
        {'type': 'bizvideo', 'title': 'broken', 'provider': 'youtube', 'video_id': 'bad"id'},
    ],
    'cases': [
        {'title': '仙人VS魔物', 'provider': 'youtube', 'video_id': 'tJxBUZfWqTs', 'category': 'OTHER'},
        {'title': '【MV】目MEめぇ～愛 I eye', 'provider': 'youtube', 'video_id': 'CduBxsawUkQ', 'category': 'MUSIC_VIDEO'},
        {'title': 'Drive case', 'provider': 'drive', 'video_id': '1kffZJKMAMB9rJGVKYxSgjbDs5UI99BTQ'},
    ],
    'playlists': [
        {'title': 'IPキャラクター・オリジナル開発', 'type': 'bizanime', 'playlist_id': 'PLbAH9KNME5V0', 'poster': 'https://i.ytimg.com/vi/9FikBXFaH8E/hqdefault.jpg'},
        {'title': 'VLOG・旅行・ライフスタイルCM', 'type': 'bizvideo', 'playlist_id': 'PLD2nZrEveSfI', 'poster': 'https://i.ytimg.com/vi/uBhpYFilpf4/hqdefault.jpg'},
        {'title': 'bad list', 'type': 'bizvideo', 'playlist_id': 'x'},
    ],
}
MANGA_TITLES = ['マンガ1', '<img src=x onerror="window.__xss=1">マンガ2', 'マンガ5']
ANIME_TITLES = ['Good Bye MV', '【MV】目MEめぇ～愛 I eye', '仙人VS魔物', 'IPキャラクター・オリジナル開発']
VIDEO_TITLES = ['サン', 'VLOG', 'VLOG・旅行・ライフスタイルCM']


def load(page, works=WORKS, videos=VIDEOS, fail=(), html=None, wait=900):
    def route(r):
        u = r.request.url
        if '/wp-json/contentsx/v1/' in u:
            if '/wp-json/contentsx/v1/slots/' in u:
                # A WordPress without the Creative X slots (today's production): the older lists below.
                # The slots themselves are checked in tests/test_creative_slots.py.
                return r.fulfill(status=404, content_type='application/json', body='{"code":"not_found"}', headers={'Access-Control-Allow-Origin': '*'})
            kind = 'videos' if '/bizanime-videos' in u else 'works'
            if kind in fail:
                return r.abort()
            return r.fulfill(status=200, content_type='application/json', body=json.dumps(videos if kind == 'videos' else works))
        if u.startswith(UP):
            return r.fulfill(status=200, content_type='image/png', body=THUMB if 'thumb' in u else PAGE_IMG)
        if u.startswith(('https://i.ytimg.com/', 'https://contentsx.jp/material/')):
            return r.fulfill(status=200, content_type='image/png', body=THUMB)
        if html and u.split('#')[0] == PAGE:
            res = r.fetch()
            return r.fulfill(response=res, body=html(res.text()))
        if u.startswith(('http://127.0.0.1:', 'http://localhost:', 'https://fonts.googleapis.com/', 'https://fonts.gstatic.com/')):
            return r.continue_()
        return r.abort()  # analytics and the YouTube / Drive embeds (only their URLs are checked)
    page.route('**/*', route)
    page.goto(PAGE + '#works', wait_until='networkidle')
    page.wait_for_timeout(wait)


def titles(page):
    return page.locator('.cxw-thumb .cxw-thumb__title').all_inner_texts()


def current(page):
    return page.evaluate("""() => ({ title: document.querySelector('.cxw-info__title').textContent,
      kind: document.querySelector('.cxw-feature').dataset.kind, selected: [...document.querySelectorAll('.cxw-thumb')].findIndex(t => t.getAttribute('aria-selected') === 'true'),
      focused: document.activeElement.getAttribute('data-index'), backdrop: (document.querySelector('.cxw-backdrop__img.is-active') || {}).src || '',
      visual: document.querySelector('.cxw-visual__img').src, open: document.querySelector('.cxw-open').textContent })""")


def tab(page, name):
    page.locator(f'#cxw-tab-{name}').click()
    page.wait_for_timeout(450)


with sync_playwright() as p:
    browser = p.chromium.launch(channel=args.channel) if args.channel else p.chromium.launch()
    for width in widths:
        height = 900 if width > 768 else 844
        page = browser.new_page(viewport={'width': width, 'height': height}, device_scale_factor=1, has_touch=width <= 768)
        errors = []
        page.on('pageerror', lambda e: errors.append(str(e)))
        load(page)
        assert page.locator('#works').evaluate("e=>e.classList.contains('cxw-ready')"), width
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), f'horizontal overflow at {width}px'
        assert page.locator('[data-cxw-filters]').is_visible() and page.locator('[data-cxw-fallback]').count() == 0
        assert page.locator('[data-cxw-filter]').all_inner_texts() == ['ALL10', 'MANGA3', 'ANIME4', 'VIDEO3'] or \
            [t.replace('\n', '') for t in page.locator('[data-cxw-filter]').all_inner_texts()] == ['ALL10', 'MANGA3', 'ANIME4', 'VIDEO3']
        # ALL: one of each kind in turn, each kind in WordPress order.
        assert titles(page) == [MANGA_TITLES[0], ANIME_TITLES[0], VIDEO_TITLES[0], MANGA_TITLES[1], ANIME_TITLES[1], VIDEO_TITLES[1],
                                MANGA_TITLES[2], ANIME_TITLES[2], VIDEO_TITLES[2], ANIME_TITLES[3]], titles(page)
        assert page.evaluate('window.__xss') is None
        c = current(page)
        assert c['title'] == 'マンガ1' and c['kind'] == 'manga' and c['selected'] == 0 and c['open'].startswith('マンガを読む'), c
        assert c['visual'].endswith('m1-1.png') and c['backdrop'].endswith('m1-thumb.png'), c
        # Text sizes, tap targets, heading levels.
        small = page.evaluate("""() => [...document.querySelectorAll('#works *')].filter(e => e.offsetParent && [...e.childNodes].some(n => n.nodeType === 3 && n.textContent.trim()))
          .map(e => [e.className, parseFloat(getComputedStyle(e).fontSize)]).filter(x => x[1] < 12)""")
        assert not small, (width, small)
        if width <= 768:
            taps = page.evaluate("""() => [...document.querySelectorAll('#works button, #works a, #works [role=option]')].filter(e => e.offsetParent)
              .map(e => [e.className || e.textContent, Math.round(e.getBoundingClientRect().height)]).filter(x => x[1] < 44)""")
            assert not taps, (width, taps)
        assert page.locator('#works h2').count() == 1 and page.locator('#works h3').count() == 1
        # The strip runs past the right edge so a further work peeks in.
        peek = page.evaluate("""() => { const t = document.querySelector('.cxw-strip__track'); const r = t.getBoundingClientRect();
          return [...t.children].some(o => { const b = o.getBoundingClientRect(); return b.left < innerWidth && b.right > innerWidth - 4; }) || t.scrollWidth <= t.clientWidth; }""")
        assert peek, width
        # No player before the visitor asks for one.
        assert page.locator('iframe').count() == 0
        page.screenshot(path=str(out / f'{width}-works.png'))

        # Filters select their first work; ANIME prefers the YouTube copy of a title also on Drive.
        tab(page, 'manga')
        assert titles(page) == MANGA_TITLES and current(page)['title'] == 'マンガ1'
        tab(page, 'anime')
        assert titles(page) == ANIME_TITLES and current(page)['kind'] == 'anime'
        page.locator('.cxw-thumb').nth(1).click()
        page.wait_for_timeout(450)
        c = current(page)
        assert c['visual'] == 'https://i.ytimg.com/vi/CduBxsawUkQ/maxresdefault.jpg' and c['selected'] == 1, c
        assert page.locator('.cxw-tags').inner_text().strip() == 'ミュージックビデオ'
        tab(page, 'video')
        assert titles(page) == VIDEO_TITLES and current(page)['title'] == 'サン'
        page.locator('.cxw-thumb').nth(2).click()
        page.wait_for_timeout(450)
        assert current(page)['open'].startswith('プレイリストを見る')
        assert page.locator('#cxw-tab-video').get_attribute('aria-selected') == 'true'
        assert not errors, (width, errors)
        page.close()

    # ---------- keyboard, arrows, drag (PC) ----------
    page = browser.new_page(viewport={'width': 1280, 'height': 800})
    load(page)
    page.locator('.cxw-thumb[aria-selected="true"]').focus()
    page.keyboard.press('ArrowRight')
    page.wait_for_timeout(300)
    c = current(page)
    assert c['selected'] == 1 and c['focused'] == '1' and c['kind'] == 'anime', c
    page.keyboard.press('End')
    page.wait_for_timeout(300)
    assert current(page)['selected'] == 9
    page.keyboard.press('Home')
    page.wait_for_timeout(300)
    assert current(page)['selected'] == 0
    page.locator('#cxw-tab-all').focus()
    page.keyboard.press('ArrowRight')
    page.wait_for_timeout(450)
    assert page.locator('#cxw-tab-manga').get_attribute('aria-selected') == 'true' and page.evaluate('document.activeElement.id') == 'cxw-tab-manga'
    tab(page, 'all')
    track = page.locator('.cxw-strip__track')
    assert page.locator('.cxw-strip__arrow').first.is_disabled()
    page.locator('.cxw-strip__arrow').last.click()
    page.wait_for_timeout(700)
    moved = track.evaluate('t=>t.scrollLeft')
    assert moved > 0 and not page.locator('.cxw-strip__arrow').first.is_disabled(), moved
    track.evaluate('t=>t.scrollLeft=0')
    box = track.bounding_box()
    page.mouse.move(box['x'] + box['width'] * 0.6, box['y'] + 60)
    page.mouse.down()
    page.mouse.move(box['x'] + box['width'] * 0.6 - 260, box['y'] + 60, steps=8)
    page.mouse.up()
    page.wait_for_timeout(300)
    assert track.evaluate('t=>t.scrollLeft') > 150 and current(page)['selected'] == 0, 'a drag scrolls and does not select'
    # Vertical wheel scrolls the page, not the strip.
    y = page.evaluate('scrollY')
    page.mouse.wheel(0, 300)
    page.wait_for_timeout(500)
    assert page.evaluate('scrollY') > y

    # ---------- the page's one work viewer (js/cx-works.js): video on a phone lying on its side ----------
    scroll_y = page.evaluate("document.querySelector('#works').getBoundingClientRect().top + scrollY")
    page.evaluate('(y)=>window.scrollTo({top:y,behavior:"instant"})', scroll_y)
    tab(page, 'video')
    page.locator('.cxw-thumb').nth(1).click()
    page.wait_for_timeout(450)
    page.locator('.cxw-open').click()
    page.wait_for_timeout(500)
    assert page.locator('.cxwv').is_visible() and page.locator('.cxwv').get_attribute('data-kind') == 'video'
    assert page.locator('.cxwv-phone__screen iframe').get_attribute('src') == 'https://www.youtube-nocookie.com/embed/QqRlb_JGaHw?autoplay=1&rel=0&playsinline=1'
    assert page.evaluate("document.documentElement.classList.contains('cxwv-lock') && document.querySelector('header').inert && document.querySelector('main').inert")
    assert page.evaluate("document.activeElement.classList.contains('cxwv-close')")
    assert page.locator('#cxwv-title').inner_text() == 'VLOG'
    # The frame is drawn around the screen; the player fills the screen and nothing covers it.
    geo = page.evaluate("""() => { const r = s => document.querySelector(s).getBoundingClientRect().toJSON();
      const f = document.querySelector('.cxwv-phone__screen iframe').getBoundingClientRect(); const c = document.elementFromPoint(f.left + f.width / 2, f.bottom - 8);
      return { screen: r('.cxwv-phone__screen'), frame: r('.cxwv-phone__frame'), iframe: f.toJSON(), top: c && c.tagName }; }""")
    assert geo['iframe'] == geo['screen'] and geo['top'] == 'IFRAME', geo
    assert geo['frame']['width'] > geo['screen']['width'] and abs(geo['screen']['width'] / geo['screen']['height'] - 2) < 0.02, geo
    page.screenshot(path=str(out / '1280-video-open.png'))
    page.keyboard.press('Escape')
    page.wait_for_timeout(300)
    assert page.locator('.cxwv').is_hidden() and page.locator('iframe').count() == 0, 'closing removes the embed'
    assert page.evaluate("document.activeElement.classList.contains('cxw-open') && !document.querySelector('main').inert && !document.documentElement.classList.contains('cxwv-lock')")
    # The gallery is as it was: VIDEO tab, second work.
    assert page.locator('#cxw-tab-video').get_attribute('aria-selected') == 'true' and current(page)['selected'] == 1
    # A click outside the phone closes it too; the playlist opens as videoseries.
    page.locator('.cxw-thumb').nth(2).click()
    page.wait_for_timeout(450)
    page.locator('.cxw-open').click()
    page.wait_for_timeout(400)
    assert 'videoseries?list=PLD2nZrEveSfI' in page.locator('.cxwv iframe').get_attribute('src')
    page.mouse.click(8, 400)
    page.wait_for_timeout(300)
    assert page.locator('.cxwv').is_hidden() and page.locator('iframe').count() == 0

    # ---------- manga as a book (BizManga's page flip), 拡大, Esc order ----------
    tab(page, 'manga')
    page.locator('.cxw-thumb').first.focus()
    page.keyboard.press('Enter')
    page.wait_for_timeout(900)
    assert page.locator('.cxwv .cxmr-stage').evaluate("e=>e.classList.contains('is-spread') && e.classList.contains('is-book')")
    assert page.locator('.cxwv .cxmr-count').inner_text() == '1-2 / 5'
    page.keyboard.press('ArrowLeft')                                         # ← = next (right-bound)
    page.wait_for_timeout(230)
    turning = page.locator('.cxwv .cxmr-flip').evaluate('e=>[e.classList.contains("is-active"), e.classList.contains("is-left"), getComputedStyle(e).transformOrigin]')
    assert turning[0] and turning[1] and turning[2].startswith(str(int(page.locator('.cxwv .cxmr-flip').evaluate('e=>e.offsetWidth')))), turning   # the left page turns on the spine
    page.wait_for_timeout(450)
    assert page.locator('.cxwv .cxmr-count').inner_text() == '3-4 / 5'
    page.screenshot(path=str(out / '1280-manga-open.png'))
    page.locator('.cxmr-zoom').click()
    page.wait_for_timeout(300)
    assert page.locator('.cxmr.is-full').count() == 1 and page.locator('.cxmr.is-full').is_visible()
    page.keyboard.press('Escape')                                            # closes 拡大 only
    page.wait_for_timeout(300)
    assert page.locator('.cxmr.is-full').count() == 0 and page.locator('.cxwv').is_visible()
    page.keyboard.press('Escape')
    page.wait_for_timeout(300)
    assert page.locator('.cxwv').is_hidden() and page.locator('.cxmr').count() == 0
    assert page.evaluate("document.activeElement.getAttribute('role')") == 'option'
    assert page.locator('#cxw-tab-manga').get_attribute('aria-selected') == 'true'
    page.close()

    # Phones: the viewer fills the screen; the book shows one page; video gets a thin bezel only.
    page = browser.new_page(viewport={'width': 390, 'height': 844}, has_touch=True)
    load(page)
    page.locator('.cxw-open').click()
    page.wait_for_timeout(900)
    panel = page.locator('.cxwv-panel').bounding_box()
    assert panel['width'] == 390 and page.locator('.cxwv .cxmr-stage').evaluate("e=>e.classList.contains('is-single') && e.classList.contains('is-book')")
    page.screenshot(path=str(out / '390-manga-open.png'))
    page.keyboard.press('Escape')
    page.wait_for_timeout(300)
    tab(page, 'video')
    page.locator('.cxw-open').click()
    page.wait_for_timeout(500)
    screen = page.locator('.cxwv-phone__screen').bounding_box()
    assert screen['width'] >= 340 and abs(screen['width'] / screen['height'] - 16 / 9) < 0.02, screen
    page.screenshot(path=str(out / '390-video-open.png'))
    page.close()

    # ---------- on the HERO stage: the shared blur shows through, the selected work tints it ----------
    page = browser.new_page(viewport={'width': 1280, 'height': 800})
    load(page)
    assert page.locator('.cxg-stage #works').count() == 1
    page.wait_for_function("document.querySelector('#works .cxw-backdrop__img.is-active')")
    page.wait_for_timeout(800)
    st = page.locator('#works').evaluate("""e => { const b = e.querySelector('.cxw-backdrop'), cs = getComputedStyle(b);
      return { bg: getComputedStyle(e).backgroundColor, op: cs.opacity, mask: cs.maskImage || cs.webkitMaskImage || '',
               img: getComputedStyle(e.querySelector('.cxw-backdrop__img.is-active')).opacity, handoff: e.style.getPropertyValue('--cxw-handoff') }; }""")
    assert st['bg'] == 'rgba(0, 0, 0, 0)' and st['op'] == '1' and 'linear-gradient' in st['mask'] and st['handoff'] == '', st
    assert abs(float(st['img']) - 0.55) < 0.02, st   # half strength over the HERO blur
    page.close()

    # ---------- WordPress failures ----------
    page = browser.new_page(viewport={'width': 1280, 'height': 800})
    load(page, fail=('works', 'videos'))
    assert page.locator('[data-cxw-fallback] a').count() == 3 and page.locator('[data-cxw-filters]').is_hidden()
    assert '作品を読み込めませんでした' in page.locator('.cxw-message').inner_text()
    page.close()
    page = browser.new_page(viewport={'width': 1280, 'height': 800})
    load(page, fail=('videos',))
    assert titles(page) == MANGA_TITLES and page.locator('#cxw-tab-anime').is_hidden() and page.locator('#cxw-tab-video').is_hidden()
    assert '動画を読み込めませんでした' in page.locator('.cxw-message').inner_text()
    page.close()
    page = browser.new_page(viewport={'width': 1280, 'height': 800})
    load(page, works=[], videos={'viewer': [], 'cases': [], 'playlists': []})
    assert '準備中' in page.locator('.cxw-message').inner_text() and page.locator('[data-cxw-fallback] a').count() == 3
    page.close()

    # ---------- reduced motion: no fades, everything still works ----------
    page = browser.new_page(viewport={'width': 390, 'height': 844}, reduced_motion='reduce')
    load(page)
    assert page.locator('.cxw-feature > .cxw-visual').evaluate('e=>getComputedStyle(e).transitionDuration') == '0s'
    tab(page, 'anime')
    assert current(page)['title'] == 'Good Bye MV'
    page.close()

    # ---------- JS off: the section text and the three service links ----------
    ctx = browser.new_context(viewport={'width': 390, 'height': 844}, java_script_enabled=False)
    page = ctx.new_page()
    page.goto(PAGE + '#works', wait_until='load')
    assert page.locator('#works h2').inner_text().replace('\n', ' ').strip() == '作品で見る Creative X'
    hrefs = page.locator('[data-cxw-fallback] a').evaluate_all('(a)=>a.map(x=>x.getAttribute("href"))')
    assert hrefs == ['https://bizmanga.contentsx.jp/biz-library', 'https://bizmanga.contentsx.jp/bizanime', '/services/#bizvideo'], hrefs
    assert page.locator('[data-cxw-filters]').is_hidden() and page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    page.screenshot(path=str(out / '390-nojs.png'))
    ctx.close()
    browser.close()

print('creative works: ok')
