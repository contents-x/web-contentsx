"""Browser checks for the Creative X section (Issue #65, viewer since Issue #97). Run against a loopback preview.

python3 tests/test_creative_x.py --url http://127.0.0.1:8765 --artifacts /tmp/cx-creative-qa
WordPress responses and images are replaced with the fixtures below, so the test needs no network access.
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
args = parser.parse_args()
out = Path(args.artifacts)
out.mkdir(parents=True, exist_ok=True)
widths = [320, 375, 390, 412, 448, 480, 481, 592, 593, 640, 767, 768, 769, 1024, 1100, 1101, 1280, 1440, 1920]


def png(w, h, rgb=(200, 210, 230)):
    """A plain PNG of the given size (stands in for manga pages and posters)."""
    raw = b''.join(b'\x00' + bytes(rgb) * w for _ in range(h))
    def chunk(t, d):
        return struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    return b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(raw)) + chunk(b'IEND', b'')


PAGE = png(70, 100)       # portrait manga page
TALL = png(60, 200)       # vertical-scroll page (ratio > 1.8)
POSTER = png(160, 90, (60, 80, 120))
GREY = png(120, 90, (200, 200, 200))  # what YouTube returns when maxresdefault does not exist

UP = 'https://cms.contentsx.jp/wp-content/uploads/2026/06/'
VIEWER = [
    {'type': 'bizanime', 'title': '<img src=x onerror="window.__xss=1">アニメ1', 'description': '説明1',
     'provider': 'youtube', 'video_id': 'V9ZC16hTlZI', 'poster': 'javascript:alert(1)',
     'embed': 'https://attacker.example.com/embed'},  # must be ignored: the client rebuilds embeds
    {'type': 'bizvideo', 'title': 'ビデオ1', 'description': '', 'provider': 'youtube', 'video_id': 'DkmWuOSvCEY',
     'poster': 'https://i.ytimg.com/vi/DkmWuOSvCEY/maxresdefault.jpg'},
    {'type': 'bizanime', 'title': 'broken id', 'provider': 'youtube', 'video_id': 'bad"id'},
    {'type': 'bizanime', 'title': 'アニメ2', 'description': '', 'provider': 'youtube', 'video_id': '7m2ORgR-PDg',
     'poster': 'https://evil.example.com/x.jpg'},
    {'type': 'bizanime', 'title': 'アニメ3', 'description': '', 'provider': 'drive', 'video_id': '1kffZJKMAMB9rJGVKYxSgjbDs5UI99BTQ',
     'poster': UP + 'drive-poster.png'},
    {'type': 'bizanime', 'title': 'アニメ4（4本目は出さない）', 'provider': 'youtube', 'video_id': 'CduBxsawUkQ'},
    {'type': 'bizvideo', 'title': 'ビデオ2', 'description': '', 'provider': 'youtube', 'video_id': 'QqRlb_JGaHw'},
    {'type': 'bizvideo', 'title': 'ビデオ3', 'description': '', 'provider': 'youtube', 'video_id': 'A1g5Iy9_24g'},
]
PLAYLISTS = [
    {'title': 'IPキャラクター・オリジナル開発', 'type': 'bizanime', 'playlist_id': 'PLbAH9KNME5V0'},
    {'title': 'VLOG・旅行・ライフスタイルCM', 'type': 'bizvideo', 'playlist_id': 'PLD2nZrEveSfI'},
    {'title': 'シネマティック・ストーリーMV', 'type': 'bizvideo', 'playlist_id': 'PLTGR0hc6ZaWs'},
]
CASES = [{'title': 'I eye', 'provider': 'youtube', 'video_id': 'CduBxsawUkQ',
          'poster': 'https://i.ytimg.com/vi/CduBxsawUkQ/maxresdefault.jpg'}]
VIDEOS = {'main': [], 'cases': CASES, 'playlists': PLAYLISTS, 'viewer': VIEWER}
MANGA = {'id': 'gaudia', 'title_ja': 'ガウディア１話', 'view_type': 'spread',
         'gallery': [UP + '1.png', UP + '2.png', 'https://evil.example.com/p.png', UP + '3.png', UP + '4.png', UP + '5.png']}
WORKS = [{'id': 'nogallery', 'title_ja': 'ページなし', 'gallery': []}, MANGA]
VERTICAL = [{'id': 'tate', 'title_ja': '縦読み', 'view_type': 'vertical_only', 'gallery': [UP + 'tall1.png', UP + 'tall2.png', UP + 'tall3.png']}]


HELD = []  # API requests left unanswered by load(hang=True)


def load(page, videos=VIDEOS, works=WORKS, fail=False, hang=False):
    def route(r):
        u = r.request.url
        if '/wp-json/contentsx/v1/' in u:
            if fail:
                return r.abort()
            if hang:
                return HELD.append(r)  # no answer yet: the loading state stays
            if videos is None and '/bizanime-videos' in u:
                return r.abort()  # only the video API fails
            body = videos if '/bizanime-videos' in u else works if '/works' in u else []
            return r.fulfill(status=200, content_type='application/json', body=json.dumps(body))
        if u.startswith(UP):
            if 'missing' in u:
                return r.fulfill(status=404, body='')
            return r.fulfill(status=200, content_type='image/png', body=TALL if 'tall' in u else POSTER if 'poster' in u else PAGE)
        if u.startswith('https://i.ytimg.com/'):
            return r.fulfill(status=200, content_type='image/png', body=GREY if 'maxresdefault' in u else POSTER)
        if u.startswith(('http://127.0.0.1:', 'https://fonts.googleapis.com/', 'https://fonts.gstatic.com/')):
            return r.continue_()
        return r.abort()  # includes the YouTube/Drive embeds: the test only checks their URLs
    page.route('**/*', route)
    page.goto(args.url, wait_until='domcontentloaded' if hang else 'networkidle')
    page.wait_for_timeout(800)


def to_section(page, wait=1500):
    y = page.evaluate("document.querySelector('#creative-x').getBoundingClientRect().top + scrollY - 64")
    page.evaluate('(y)=>window.scrollTo({top:y,behavior:"instant"})', y)
    page.wait_for_timeout(wait)


def rect(page, selector):
    return page.locator(selector).first.evaluate('e=>e.getBoundingClientRect().toJSON()')


CUR = '.cxvp-stage[aria-hidden="false"]'  # the video in view


def titles_of(page):
    return page.locator('.cxvp-stage .cxvp-title').all_inner_texts()


def scroll_track(page, index):
    """Swipe / trackpad: scroll the video row sideways to the given video."""
    page.locator('.cxvp-track').evaluate('(t, i)=>t.scrollTo({left:i*t.clientWidth,behavior:"instant"})', index)
    page.wait_for_timeout(250)


def switch(page, service):
    page.locator(f'[data-cxcx-service="{service}"]').click()
    page.wait_for_timeout(450)


report = []
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    for width in widths:
        page = browser.new_page(viewport={'width': width, 'height': 900 if width > 768 else 844}, device_scale_factor=1)
        errors = []
        page.on('pageerror', lambda e: errors.append(str(e)))
        load(page)
        assert page.locator('#creative-x').evaluate("e=>e.classList.contains('cxcx-ready')")
        assert page.evaluate('document.body.scrollWidth <= innerWidth'), f'Horizontal overflow at {width}px'
        # Shared backdrop continues from ABOUT without a white seam.
        assert page.locator('#creative-x > .cxsb-backdrop').evaluate('e=>getComputedStyle(e).position') == 'fixed'
        assert page.locator('#creative-x').evaluate("e=>getComputedStyle(e,'::before').display") == 'none'
        assert page.locator('#home-about').evaluate("e=>getComputedStyle(e,'::after').display") == 'none'
        to_section(page)
        assert page.locator('#creative-x > .cxsb-label').inner_text().strip() == 'CREATIVE X'
        # Three cards are the tabs; BizAnime is selected first.
        cards = page.locator('.cxcx-card-name').all_inner_texts()
        assert cards == ['ビズマンガ', 'ビズアニメ', 'ビズビデオ'], cards
        assert page.locator('[role="tab"][aria-selected="true"]').get_attribute('data-cxcx-service') == 'bizanime'
        assert page.locator('#cxcx-panel').get_attribute('data-service') == 'bizanime'
        assert page.locator('.cxvp-stage').count() == 3 and page.locator('.cxvp-thumb').count() == 0
        r = page.locator('.cxcx-card').evaluate_all('(n)=>n.map(e=>e.getBoundingClientRect().toJSON())')
        if width > 768:
            assert abs(r[0]['top'] - r[2]['top']) < 1 and r[1]['left'] > r[0]['right'], 'cards in one row'
        else:
            # SP (Issue #154): one column of wide (2:1) cards.
            assert all(r[i + 1]['top'] >= r[i]['bottom'] - 1 for i in range(2)), 'SP cards stack'
            assert all(abs(c['width'] / c['height'] - 2) < .05 for c in r), r
        assert min(c['height'] for c in r) >= 44, 'cards are tappable'
        # Card design (Issue #154): full picture, white category/name/line, arrow clear of the text.
        assert page.locator('.cxcx-card-label').all_inner_texts() == ['MANGA', 'ANIME', 'VIDEO']
        assert [x.split('/')[-1] for x in page.locator('.cxcx-card img').evaluate_all('(n)=>n.map(i=>i.getAttribute("src"))')] == ['bizmanga.webp', 'bizanime.webp', 'bizvideo.webp']
        for i in range(3):
            card = page.locator('.cxcx-card').nth(i)
            cb, mb = card.bounding_box(), card.locator('.cxcx-card-media').bounding_box()
            assert abs(mb['width'] - cb['width']) < 3 and abs(mb['height'] - cb['height']) < 3, 'picture fills the card'
            assert card.locator('.cxcx-card-name').evaluate('e=>getComputedStyle(e).color') == 'rgb(255, 255, 255)'
            assert card.locator('.cxcx-card-desc').is_visible()
            body, go = card.locator('.cxcx-card-body').bounding_box(), card.locator('.cxcx-card-go').bounding_box()
            assert body['x'] + body['width'] <= go['x'] + 1 or body['y'] + body['height'] <= go['y'] + 1, 'arrow clear of text'
        viewer = rect(page, '.cxcx-viewer')
        if width > 1100:
            # Copy on the left of the viewer; OUR WORKS on the left of the cards; cards below the viewer.
            assert rect(page, '.cxcx-copy')['right'] <= viewer['left']
            assert rect(page, '.cxcx-works-intro')['right'] <= r[0]['left']
            assert r[0]['top'] >= viewer['bottom']
        else:
            # One column: copy → OUR WORKS → cards → viewer, so the tapped card never moves.
            order = ['.cxcx-copy', '.cxcx-works-intro', '.cxcx-cards', '.cxcx-viewer']
            tops = [rect(page, s)['top'] for s in order]
            assert tops == sorted(tops), f'order at {width}px: {tops}'
        if width <= 592:
            assert abs(viewer['left']) < 1 and abs(viewer['right'] - width) < 1, f'SP viewer edge to edge at {width}px'
        # The video uses the whole frame width at 16:9.
        stage = rect(page, '.cxvp-stage')
        assert abs(stage['width'] / stage['height'] - 16 / 9) < 0.02, stage
        assert abs(stage['width'] - rect(page, '#cxcx-panel')['width']) < 1, stage
        # Manga: spread on wide frames, one page at a time on narrow ones (BizManga rule: PC >= 769).
        switch(page, 'manga')
        page.wait_for_selector('.cxmr.is-ready')
        assert page.locator('.cxmr-stage').evaluate("e=>e.classList.contains('is-spread')") == (width >= 769)
        assert page.locator('.cxmr-count').inner_text() == ('1-2 / 5' if width >= 769 else '1 / 5')
        page_box = rect(page, '.cxmr-page')
        stage_box = rect(page, '.cxmr-stage')
        assert page_box['height'] <= stage_box['height'] + 1 and page_box['width'] <= stage_box['width'] + 1, 'page not cropped'
        assert page.evaluate('document.body.scrollWidth <= innerWidth'), f'Overflow with manga at {width}px'
        # Body/UI text expansion (Android scaling); the CREATIVE X label is ornamental and fixed.
        page.locator('#creative-x h2,#creative-x h3,#creative-x p:not(.cxcx-tagline),#creative-x strong,#creative-x .cxcx-card-desc,#creative-x .cxcx-button,#creative-x .cxmr-count').evaluate_all(
            '(nodes)=>nodes.forEach(e=>e.style.fontSize=(parseFloat(getComputedStyle(e).fontSize)*1.4)+"px")')
        page.wait_for_timeout(150)
        assert page.evaluate('document.body.scrollWidth <= innerWidth'), f'Overflow with 1.4x text at {width}px'
        if width in [390, 1440]:
            page.screenshot(path=str(out / f'{width}-creative-x-manga.png'))
        assert not errors, errors
        report.append({'width': width, 'cards': cards, 'text_1_4x': 'pass'})
        page.close()

    # Video carousel: no autoplay, embed rebuilt from the ID on play, previous video stops when it
    # leaves the view; videos change by scrolling sideways (no thumbnail strip).
    page = browser.new_page(viewport={'width': 1440, 'height': 900})
    load(page)
    to_section(page)
    assert page.evaluate('window.__xss') is None
    assert page.locator('#creative-x img[src*="evil"], #creative-x img[src^="javascript"]').count() == 0
    assert page.locator('.cxvp-thumb, .cxvp-strip').count() == 0
    titles = titles_of(page)
    assert titles == ['<img src=x onerror="window.__xss=1">アニメ1', 'アニメ2', 'アニメ3'], titles  # bad ID dropped, max 3
    assert page.locator('.cxvp-desc').first.inner_text() == '説明1'
    track, stage = rect(page, '.cxvp-track'), rect(page, '.cxvp-stage')
    assert abs(stage['width'] - track['width']) < 1, 'each video uses the whole frame width'
    assert abs(stage['width'] - rect(page, '#cxcx-panel')['width']) < 1
    assert page.locator(CUR).count() == 1 and page.locator(CUR).get_attribute('aria-label').startswith('1 / 3')
    assert page.locator(CUR + ' .cxvp-poster').get_attribute('src') == 'https://i.ytimg.com/vi/V9ZC16hTlZI/hqdefault.jpg'
    assert page.locator('.cxvp-stage iframe').count() == 0, 'no autoplay on load'
    assert page.locator('.cxvp-dot.is-active').count() == 1 and page.locator('.cxvp-arrow-prev').is_disabled()
    page.locator(CUR + ' .cxvp-play').click()
    assert page.locator('.cxvp-stage iframe').get_attribute('src') == 'https://www.youtube-nocookie.com/embed/V9ZC16hTlZI?autoplay=1&rel=0&playsinline=1'
    assert page.locator('.cxvp-stage iframe').get_attribute('title') == titles[0]
    # Scrolling sideways to another video stops the one that was playing.
    scroll_track(page, 2)
    assert page.locator('.cxvp-stage iframe').count() == 0, 'previous video stops'
    assert page.locator(CUR).get_attribute('aria-label').startswith('3 / 3')
    assert page.locator('.cxvp-dot').nth(2).evaluate("e=>e.classList.contains('is-active')")
    assert page.locator('.cxvp-arrow-next').is_disabled() and not page.locator('.cxvp-arrow-prev').is_disabled()
    assert page.locator(CUR + ' .cxvp-poster').get_attribute('src') == UP + 'drive-poster.png'
    page.locator(CUR + ' .cxvp-play').click()
    assert page.locator('.cxvp-stage iframe').get_attribute('src') == 'https://drive.google.com/file/d/1kffZJKMAMB9rJGVKYxSgjbDs5UI99BTQ/preview'
    assert page.locator('.cxvp-dots').is_hidden(), 'dots step aside while a video plays'
    # ‹ › buttons and ← → keys also move one video at a time.
    page.locator('.cxvp-arrow-prev').click()
    page.wait_for_timeout(700)
    assert page.locator(CUR).get_attribute('aria-label').startswith('2 / 3')
    assert page.locator('.cxvp-stage iframe').count() == 0
    assert abs(page.locator('.cxvp-track').evaluate('t=>t.scrollLeft/t.clientWidth') - 1) < 0.02
    page.locator('.cxvp-arrow-next').focus()
    page.keyboard.press('ArrowLeft')
    page.wait_for_timeout(700)
    assert page.locator(CUR).get_attribute('aria-label').startswith('1 / 3')
    # Switching service while playing removes the embed and fades the panel (200ms).
    page.locator(CUR + ' .cxvp-play').click()
    assert page.locator('.cxvp-stage iframe').count() == 1
    h_anime = rect(page, '.cxcx-viewer')['height']
    page.locator('[data-cxcx-service="bizvideo"]').click()
    assert page.locator('#cxcx-panel').evaluate("e=>e.classList.contains('is-fading')")
    assert page.locator('#creative-x iframe').count() == 0
    page.wait_for_timeout(450)
    assert not page.locator('#cxcx-panel').evaluate("e=>e.classList.contains('is-fading')")
    assert page.locator('#cxcx-panel').get_attribute('aria-labelledby') == 'cxcx-tab-bizvideo'
    assert titles_of(page) == ['ビデオ1', 'ビデオ2', 'ビデオ3']
    page.wait_for_timeout(300)
    assert page.locator(CUR + ' .cxvp-poster').get_attribute('src') == 'https://i.ytimg.com/vi/DkmWuOSvCEY/hqdefault.jpg', 'grey maxres placeholder replaced'
    h_video = rect(page, '.cxcx-viewer')['height']
    page.locator(CUR + ' .cxvp-play').click()
    assert page.locator('.cxvp-stage iframe').get_attribute('src').startswith('https://www.youtube-nocookie.com/embed/DkmWuOSvCEY?')
    # Tabs: arrow keys and Home/End move the selection and focus.
    page.locator('[data-cxcx-service="bizvideo"]').focus()
    page.keyboard.press('ArrowRight')  # wraps to BizManga
    page.wait_for_timeout(450)
    assert page.locator('[data-cxcx-service="manga"]').evaluate('e=>e===document.activeElement && e.getAttribute("aria-selected")==="true" && e.tabIndex===0')
    assert page.locator('#creative-x iframe').count() == 0
    page.keyboard.press('End')
    page.wait_for_timeout(450)
    assert page.locator('[data-cxcx-service="bizvideo"]').get_attribute('aria-selected') == 'true'
    page.keyboard.press('Home')
    page.wait_for_timeout(450)

    # Manga reader (PC): right-bound spreads, lower page on the right, odd last page + thanks page.
    page.wait_for_selector('.cxmr.is-ready')
    h_manga = rect(page, '.cxcx-viewer')['height']
    assert abs(h_anime - h_video) < 2 and abs(h_anime - h_manga) < 2, ('panel height jumps', h_anime, h_video, h_manga)
    srcs = page.locator('.cxmr-page').evaluate_all('(n)=>n.map(e=>e.getAttribute("src"))')
    assert srcs == [UP + '2.png', UP + '1.png'], srcs
    assert page.locator('.cxmr-prev').is_disabled() and not page.locator('.cxmr-next').is_disabled()
    next_box, prev_box = rect(page, '.cxmr-next'), rect(page, '.cxmr-prev')
    assert next_box['left'] < prev_box['left'], 'next sits on the left (right-bound book)'
    page.locator('.cxmr-next').click()
    assert page.locator('.cxmr-count').inner_text() == '3-4 / 5'
    page.locator('.cxmr-stage').focus()
    page.keyboard.press('ArrowLeft')  # ← = next
    assert page.locator('.cxmr-count').inner_text() == '5 / 5'
    srcs = page.locator('.cxmr-page').evaluate_all('(n)=>n.map(e=>e.getAttribute("src"))')
    assert srcs == ['/material/manga/thanks_v02.webp', UP + '5.png'], srcs
    assert page.locator('.cxmr-next').is_disabled()
    page.keyboard.press('ArrowRight')  # → = previous
    assert page.locator('.cxmr-count').inner_text() == '3-4 / 5'
    # Click on the pages: left half = next, right half = previous (same as ‹ ›).
    st = page.locator('.cxmr-stage').bounding_box()
    page.mouse.click(st['x'] + st['width'] * .25, st['y'] + st['height'] / 2)
    page.wait_for_timeout(150)
    assert page.locator('.cxmr-count').inner_text() == '5 / 5'
    page.mouse.click(st['x'] + st['width'] * .75, st['y'] + st['height'] / 2)
    page.wait_for_timeout(150)
    assert page.locator('.cxmr-count').inner_text() == '3-4 / 5'
    # 「拡大」: the reader covers the whole screen (like biz-library); the button stays visible.
    small = rect(page, '.cxmr-stage')
    y_before = page.evaluate('scrollY')
    page.locator('.cxmr-zoom').click()
    page.wait_for_timeout(200)
    assert page.locator('.cxmr-zoom').get_attribute('aria-pressed') == 'true'
    full = rect(page, '.cxmr')
    assert full['left'] == 0 and full['top'] == 0 and full['width'] == 1440 and full['height'] == 900, full
    big = rect(page, '.cxmr-stage')
    assert big['height'] > small['height'] * 1.3, (small, big)
    assert page.locator('.cxmr').evaluate("e=>e.parentElement===document.body && e.getAttribute('role')==='dialog'")
    assert page.evaluate("getComputedStyle(document.documentElement).overflow") == 'hidden'
    zb = rect(page, '.cxmr-zoom')
    assert page.evaluate('([x,y])=>!!document.elementFromPoint(x,y).closest(".cxmr-zoom")', [zb['left'] + zb['width'] / 2, zb['top'] + zb['height'] / 2]), 'close button visible on top'
    assert page.locator('.cxmr-zoom').evaluate('e=>getComputedStyle(e).backgroundColor') != 'rgb(255, 255, 255)'
    assert page.locator('.cxmr-count').inner_text() == '3-4 / 5'
    st = page.locator('.cxmr-stage').bounding_box()
    page.mouse.click(st['x'] + st['width'] * .25, st['y'] + st['height'] / 2)
    page.wait_for_timeout(150)
    assert page.locator('.cxmr-count').inner_text() == '5 / 5', 'pages still turn while enlarged'
    page.keyboard.press('Escape')
    page.wait_for_timeout(200)
    assert page.locator('.cxmr-zoom').get_attribute('aria-pressed') == 'false'
    assert page.locator('.cxcx-panel .cxmr').count() == 1 and page.locator('.cxmr-placeholder').count() == 0, 'back in its place'
    assert page.evaluate("getComputedStyle(document.documentElement).overflow") != 'hidden'
    assert abs(page.evaluate('scrollY') - y_before) < 2
    assert page.evaluate("document.activeElement.classList.contains('cxmr-zoom')")
    # Leaving and coming back resets the reader.
    switch(page, 'bizanime')
    switch(page, 'manga')
    page.wait_for_selector('.cxmr.is-ready')
    assert page.locator('.cxmr-count').inner_text() == '1-2 / 5'
    assert page.locator('.cxmr-zoom').get_attribute('aria-pressed') == 'false'
    assert page.locator('body > .cxmr').count() == 0 and page.evaluate("getComputedStyle(document.documentElement).overflow") != 'hidden'
    # The cards are links in the HTML; with JS a plain click switches the viewer instead of leaving the page.
    assert page.locator('.cxcx-card').first.evaluate('e=>e.tagName') == 'A'
    assert page.url.rstrip('/') == args.url.rstrip('/')
    page.locator('[data-cxcx-service="bizvideo"]').focus()
    page.keyboard.press(' ')
    page.wait_for_timeout(450)
    assert page.locator('[data-cxcx-service="bizvideo"]').get_attribute('aria-selected') == 'true'
    assert page.url.rstrip('/') == args.url.rstrip('/')
    page.close()

    # Manga reader (SP): one page, swipe left = next, right = previous.
    page = browser.new_page(viewport={'width': 390, 'height': 844}, has_touch=True)
    load(page)
    to_section(page)
    switch(page, 'manga')
    page.wait_for_selector('.cxmr.is-ready')
    stage = page.locator('.cxmr-stage')
    def swipe(dx):
        stage.dispatch_event('pointerdown', {'pointerType': 'touch', 'clientX': 200, 'clientY': 300, 'isPrimary': True})
        stage.dispatch_event('pointerup', {'pointerType': 'touch', 'clientX': 200 + dx, 'clientY': 305, 'isPrimary': True})
    swipe(-120)
    assert page.locator('.cxmr-count').inner_text() == '2 / 5'
    swipe(-120)
    swipe(90)
    assert page.locator('.cxmr-count').inner_text() == '2 / 5'
    swipe(-20)  # too short: ignored
    assert page.locator('.cxmr-count').inner_text() == '2 / 5'
    assert all(rect(page, s)['height'] >= 44 for s in ['.cxmr-next', '.cxmr-prev', '.cxmr-zoom'])
    page.screenshot(path=str(out / '390-creative-x-manga-page2.png'))
    page.close()

    # Vertical-scroll works keep BizManga's rule (view_type vertical_only / tall first page).
    page = browser.new_page(viewport={'width': 1440, 'height': 900})
    load(page, works=VERTICAL)
    to_section(page)
    switch(page, 'manga')
    page.wait_for_selector('.cxmr.is-ready')
    assert page.locator('.cxmr-stage').evaluate("e=>e.classList.contains('is-vertical')")
    assert page.locator('.cxmr-page').count() == 3 and page.locator('.cxmr-next').is_hidden()
    page.close()
    page = browser.new_page(viewport={'width': 1440, 'height': 900})
    load(page, works=[{**VERTICAL[0], 'view_type': ''}])
    to_section(page)
    switch(page, 'manga')
    page.wait_for_selector('.cxmr.is-ready')
    assert page.locator('.cxmr-stage').evaluate("e=>e.classList.contains('is-vertical')")
    page.close()

    # PC hover: image ≤1.035×, card lifts ≤4px, arrow moves right; selected card ring; reduced motion stops it.
    page = browser.new_page(viewport={'width': 1440, 'height': 900})
    load(page)
    to_section(page)
    card = page.locator('.cxcx-card--video')
    card.hover()
    page.wait_for_timeout(700)
    assert card.locator('img').evaluate('e=>getComputedStyle(e).transform') == 'matrix(1.035, 0, 0, 1.035, 0, 0)'
    lift = card.evaluate('e=>parseFloat(getComputedStyle(e).translate.split(" ")[1]||0)')
    assert -4 <= lift < 0, lift
    assert card.locator('.cxcx-card-go').evaluate('e=>new DOMMatrix(getComputedStyle(e).transform).m41') > 0
    sel = page.locator('.cxcx-card[aria-selected="true"]')
    assert sel.evaluate('e=>getComputedStyle(e).backgroundColor') != 'rgb(255, 255, 255)', 'selected card stays dark'
    page.close()
    page = browser.new_page(viewport={'width': 1440, 'height': 900}, reduced_motion='reduce')
    load(page)
    to_section(page, 300)
    page.locator('.cxcx-card--video').hover()
    page.wait_for_timeout(400)
    assert page.locator('.cxcx-card--video').evaluate('e=>getComputedStyle(e).translate') == 'none'
    page.close()

    # Laptops: the whole section (viewer and cards) stays inside one screen below the fixed header;
    # from 800px tall the video uses the whole frame width.
    for w, h in [(1470, 800), (1280, 800), (1440, 900), (1448, 1086), (1920, 1080), (1280, 720), (1536, 730), (1366, 650)]:
        page = browser.new_page(viewport={'width': w, 'height': h})
        load(page)
        to_section(page)  # measure after the entrance animation (cards start 30px lower)
        box = page.evaluate("(()=>{const s=document.querySelector('#creative-x').getBoundingClientRect().top;const b=x=>Math.max(...[...document.querySelectorAll(x)].map(e=>e.getBoundingClientRect().bottom))-s;return {viewer:b('.cxcx-viewer'),cards:b('.cxcx-card')}})()")
        assert box['viewer'] <= h - 64 and box['cards'] <= h - 64, (w, h, box)
        if h >= 800:
            stage = rect(page, '.cxvp-stage')
            assert abs(stage['width'] / stage['height'] - 16 / 9) < 0.02, (w, h, stage)
        page.close()

    # PC snap includes Creative X.
    page = browser.new_page(viewport={'width': 1440, 'height': 900})
    load(page)
    target = page.evaluate("document.querySelector('#creative-x').getBoundingClientRect().top + scrollY - 64")
    page.evaluate('(y)=>window.scrollTo({top:y,behavior:"instant"})', target - 120)
    page.wait_for_timeout(1500)
    assert abs(page.evaluate('scrollY') - target) <= 2, (page.evaluate('scrollY'), target)
    page.close()

    # Before viewer videos are registered: BizAnime uses existing cases, BizVideo the BizVideo playlists.
    page = browser.new_page(viewport={'width': 1440, 'height': 900})
    load(page, videos={'main': [], 'cases': CASES, 'playlists': PLAYLISTS})
    to_section(page)
    # BizAnime: its playlists first, then the existing single videos.
    assert titles_of(page) == ['IPキャラクター・オリジナル開発', 'I eye']
    switch(page, 'bizvideo')
    assert titles_of(page) == ['VLOG・旅行・ライフスタイルCM', 'シネマティック・ストーリーMV']
    page.locator(CUR + ' .cxvp-play').click()
    assert page.locator('.cxvp-stage iframe').get_attribute('src') == 'https://www.youtube-nocookie.com/embed/videoseries?list=PLD2nZrEveSfI&autoplay=1&rel=0&playsinline=1'
    page.close()

    # Loading and API failure states.
    page = browser.new_page(viewport={'width': 390, 'height': 844})
    load(page, hang=True)
    to_section(page, 300)
    assert page.locator('#cxcx-panel .cxcx-message').inner_text() == '読み込み中…'
    for r in HELD:
        r.abort()
    page.wait_for_timeout(300)
    page.close()
    page = browser.new_page(viewport={'width': 390, 'height': 844})
    errors = []
    page.on('pageerror', lambda e: errors.append(str(e)))
    load(page, fail=True)
    to_section(page)
    assert '動画を読み込めませんでした' in page.locator('.cxcx-message').inner_text()
    assert page.locator('.cxcx-message a').get_attribute('href') == 'https://bizmanga.contentsx.jp/bizanime'
    switch(page, 'manga')
    assert page.locator('.cxcx-message a').get_attribute('href') == 'https://bizmanga.contentsx.jp/biz-library'
    assert page.evaluate('document.body.scrollWidth <= innerWidth') and not errors, errors
    page.close()

    # Only the video API fails: the viewer says so (not "準備中") and links to the service; manga still reads.
    page = browser.new_page(viewport={'width': 1440, 'height': 900})
    load(page, videos=None)
    to_section(page)
    assert '動画を読み込めませんでした' in page.locator('.cxcx-message').inner_text()
    switch(page, 'manga')
    page.wait_for_selector('.cxmr.is-ready')
    page.close()

    # A broken first page does not stop the reader (same as bm-view-type.js: treated as not vertical).
    page = browser.new_page(viewport={'width': 1440, 'height': 900})
    load(page, works=[{**MANGA, 'gallery': [UP + 'missing.png'] + MANGA['gallery'][1:]}])
    to_section(page)
    switch(page, 'manga')
    page.wait_for_selector('.cxmr.is-ready')
    assert page.locator('.cxmr-count').inner_text() == '1-2 / 5'
    page.close()

    # Reduced motion: switch without fading; content visible.
    page = browser.new_page(viewport={'width': 1440, 'height': 900}, reduced_motion='reduce')
    load(page)
    to_section(page, 300)
    for selector in ['.cxcx-copy', '.cxcx-viewer', '.cxcx-works-intro', '.cxcx-card']:
        assert set(page.locator(f'#creative-x {selector}').evaluate_all('(n)=>n.map(e=>getComputedStyle(e).opacity)')) == {'1'}
    page.locator('[data-cxcx-service="bizvideo"]').click()
    assert not page.locator('#cxcx-panel').evaluate("e=>e.classList.contains('is-fading')")
    assert page.locator('#cxcx-panel').get_attribute('data-service') == 'bizvideo'
    page.close()

    # JS off: the panel keeps its link to the BizAnime works.
    page = browser.new_page(viewport={'width': 390, 'height': 844}, java_script_enabled=False)
    load(page)
    assert page.locator('.cxcx-fallback').is_visible()
    assert page.locator('.cxcx-fallback').get_attribute('href') == 'https://bizmanga.contentsx.jp/bizanime'
    hrefs = page.locator('.cxcx-card').evaluate_all('(n)=>n.map(a=>a.getAttribute("href"))')
    assert hrefs == ['https://bizmanga.contentsx.jp/biz-library', 'https://bizmanga.contentsx.jp/bizanime', '/services/#bizvideo'], hrefs
    assert page.locator('.cxcx-card[role="tab"]').count() == 0
    assert page.evaluate('document.body.scrollWidth <= innerWidth')
    page.close()
    browser.close()
(out / 'results.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
print(f'PASS: {len(widths)} widths, tabs, video carousel, manga reader (PC/SP/vertical), safety, fit, snap, fallbacks, reduced-motion and JS-off.')
