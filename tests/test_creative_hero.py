"""Browser checks for the Creative X landing HERO showreel and its hand-off to WORKS (2026-11).

python3 tests/test_creative_hero.py --url http://127.0.0.1:8792 --artifacts /tmp/cx-creative-hero-qa
Run against a loopback preview (tools/preview-extensions.py). WordPress, the poster and the videos are
replaced with fixtures, so no network is needed. The playback checks draw a 3-second test pattern with
ffmpeg (no real footage); without ffmpeg they are skipped and the run says so. --channel chrome uses the
installed Google Chrome instead of Playwright's Chromium.
"""
import argparse
import html
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
PAGE = args.url.rstrip('/') + '/services/creative-x/'
widths = [320, 375, 390, 412, 768, 1024, 1280, 1440, 1920]


def png(w, h, rgb):
    raw = b''.join(b'\x00' + bytes(rgb) * w for _ in range(h))
    def chunk(t, d):
        return struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    return b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(raw)) + chunk(b'IEND', b'')


POSTER = png(320, 180, (236, 236, 240))   # a light picture: the shade must keep the white copy readable
THUMB = png(160, 90, (60, 80, 120))


def test_pattern(ext):
    ffmpeg = shutil.which('ffmpeg')
    if not ffmpeg:
        return None
    path = Path(tempfile.mkdtemp()) / f'reel.{ext}'
    subprocess.run([ffmpeg, '-loglevel', 'error', '-y', '-f', 'lavfi', '-i', 'testsrc2=size=640x360:rate=24:duration=3',
                    '-c:v', 'libvpx-vp9', '-b:v', '300k', '-pix_fmt', 'yuv420p', '-an', str(path)], check=True)
    return path.read_bytes()


VIDEO = {'mp4': test_pattern('mp4'), 'webm': test_pattern('webm')}
HAS_VIDEO = all(VIDEO.values())
UP = 'https://cms.contentsx.jp/wp-content/uploads/2026/11/'
VIEWER = [
    {'type': 'bizvideo', 'title': 'サン', 'provider': 'youtube', 'video_id': 'DkmWuOSvCEY', 'poster': 'https://i.ytimg.com/vi/DkmWuOSvCEY/maxresdefault.jpg'},
    {'type': 'bizvideo', 'title': 'VLOG', 'provider': 'youtube', 'video_id': 'QqRlb_JGaHw'},
    {'type': 'bizvideo', 'title': '航空 採用動画', 'provider': 'youtube', 'video_id': 'A1g5Iy9_24g'},
    {'type': 'bizanime', 'title': 'Good Bye MV', 'provider': 'youtube', 'video_id': 'V9ZC16hTlZI'},
]
HERO = {'type': 'creative_hero', 'title': 'ショーリール', 'provider': 'mp4', 'video_id': '', 'src': UP + 'reel.mp4', 'poster': ''}
HERO_SP = dict(HERO, title='ショーリール SP', src=UP + 'reel-sp.mp4')


def load(page, viewer=VIEWER, fail=False, sources=None, wait=900):
    def route(r):
        u = r.request.url
        if '/wp-json/contentsx/v1/' in u:
            if '/wp-json/contentsx/v1/slots/' in u:
                # A WordPress without the Creative X slots (today's production): the older lists below.
                # The slots themselves are checked in tests/test_creative_slots.py.
                return r.fulfill(status=404, content_type='application/json', body='{"code":"not_found"}', headers={'Access-Control-Allow-Origin': '*'})
            if fail:
                return r.abort()
            body = {'main': [], 'cases': [], 'playlists': [], 'viewer': viewer} if '/bizanime-videos' in u else []
            return r.fulfill(status=200, content_type='application/json', body=json.dumps(body))
        ext = u.rsplit('.', 1)[-1]
        if ext in VIDEO and (u.startswith(UP) or '/material/' in u):
            if not VIDEO[ext] or 'broken' in u:
                return r.fulfill(status=404, body='')
            return r.fulfill(status=200, content_type=f'video/{ext}', body=VIDEO[ext])
        if u.startswith('https://i.ytimg.com/'):
            return r.fulfill(status=200, content_type='image/png', body=POSTER if 'zKvRR8xT_zY' in u else THUMB)
        if sources is not None and u.split('#')[0] == PAGE:
            res = r.fetch()
            text = res.text().replace('data-sources="[]"', 'data-sources="' + html.escape(json.dumps(sources)) + '"')
            return r.fulfill(response=res, body=text)
        if u.startswith(('http://127.0.0.1:', 'https://fonts.googleapis.com/', 'https://fonts.gstatic.com/')):
            return r.continue_()
        return r.abort()  # analytics, YouTube embeds
    page.route('**/*', route)
    page.goto(PAGE, wait_until='networkidle')
    page.wait_for_timeout(wait)


def scroll(page, y):
    page.evaluate('(y)=>window.scrollTo({top:y,behavior:"instant"})', y)
    page.wait_for_timeout(160)


def state(page):
    return page.evaluate("""() => {
      const reel = document.querySelector('.cxg-reel'), frame = reel.querySelector('.cxg-reel__frame');
      const copy = document.querySelector('.cxg-reel-hero__copy'), video = reel.querySelector('video');
      return { live: document.querySelector('.cxg-stage').classList.contains('is-live'), position: getComputedStyle(reel).position,
        fade: +getComputedStyle(reel).opacity, visible: getComputedStyle(reel).visibility === 'visible',
        blur: getComputedStyle(frame).filter, veil: +getComputedStyle(reel.querySelector('.cxg-reel__veil')).opacity,
        copy: +getComputedStyle(copy).opacity, src: video.currentSrc || video.getAttribute('src') || '', paused: video.paused,
        playing: reel.classList.contains('is-playing'), toggle: !document.querySelector('[data-cxg-reel-toggle]').hidden,
        hero: document.querySelector('.cxg-reel-hero').getBoundingClientRect().toJSON(), works: document.querySelector('#works').getBoundingClientRect().toJSON() };
    }""")


def blur_px(value):
    return 0.0 if value == 'none' else float(value.split('(')[1].split('px')[0])


with sync_playwright() as p:
    browser = p.chromium.launch(channel=args.channel) if args.channel else p.chromium.launch()

    # ---------- layout and scroll at every width (poster only, as published today) ----------
    for width in widths:
        height = 900 if width > 768 else 844
        page = browser.new_page(viewport={'width': width, 'height': height}, device_scale_factor=1)
        errors = []
        page.on('pageerror', lambda e: errors.append(str(e)))
        load(page)
        s = state(page)
        assert s['live'] and s['position'] == 'fixed', (width, s)
        assert abs(s['hero']['height'] - max(height, 560)) <= 1, (width, s['hero'])
        assert s['blur'] == 'none' and s['fade'] == 1 and s['copy'] == 1 and not s['src'] and not s['toggle'], (width, s)
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), f'horizontal overflow at {width}px'
        box = page.evaluate("""() => {
          const r = s => document.querySelector(s).getBoundingClientRect();
          return { header: r('.header').bottom, crumbs: r('.cxg-reel-hero .cxs-breadcrumbs').top, copyTop: r('.cxg-reel-hero__copy').top,
                   copyBottom: r('.cxg-reel-hero__copy').bottom, tools: r('.cxg-reel-hero__tools').toJSON(),
                   buttons: [...document.querySelectorAll('.cxg-reel-hero__button')].map(b => ({...b.getBoundingClientRect().toJSON(), clip: b.scrollWidth > b.clientWidth})),
                   chunks: [...document.querySelectorAll('.cxg-reel-hero__title > span')].map(c => c.getClientRects().length),
                   lead: getComputedStyle(document.querySelector('.cxg-reel-hero__lead')).fontSize };
        }""")
        assert box['crumbs'] >= box['header'] - 1, (width, box)                     # breadcrumbs below the fixed header
        assert box['copyTop'] > box['crumbs'] and box['copyBottom'] <= height, (width, box)
        assert all(b['height'] >= 44 and b['left'] >= 0 and b['right'] <= width and not b['clip'] for b in box['buttons']), (width, box['buttons'])
        assert box['chunks'] == [1, 1, 1], (width, box['chunks'])                    # 価値を、｜伝わる｜カタチにする。 never split
        texts = page.locator('.cxg-reel-hero__copy').inner_text()
        for text in ('Creative X', '価値を、伝わるカタチにする。', 'マンガ・アニメ・映像で、企業の魅力を届ける。', '制作事例を見る', 'お問い合わせ'):
            assert text in texts.replace('\n', ''), (width, text)
        if width > 768:  # the tools column must not sit on the copy
            assert box['tools']['left'] > max(b['right'] for b in box['buttons']), (width, box)
        page.screenshot(path=str(out / f'{width}-hero.png'))
        H = s['hero']['height']
        scroll(page, int(H * 0.15))
        mid = state(page)
        assert 0 < mid['copy'] < 1 and blur_px(mid['blur']) > 0, (width, mid)
        scroll(page, int(H))
        start = state(page)                                                          # WORKS at the top of the screen
        assert abs(start['works']['top']) <= 1 and start['copy'] == 0, (width, start)
        # A clear glass, not a navy fill: blurred, a light veil, the copy's shade gone.
        assert blur_px(start['blur']) >= 12 and 0.25 <= start['veil'] <= 0.35 and start['visible'] and start['fade'] == 1, (width, start)
        assert 'saturate' in start['blur'] and page.evaluate("+getComputedStyle(document.querySelector('.cxg-reel__shade')).opacity") == 0, (width, start)
        # WORKS sits in front of the picture.
        hit = page.evaluate("()=>{const r=document.querySelector('#works .cxw-head').getBoundingClientRect();const e=document.elementFromPoint(r.left+10,Math.max(r.top+10,80));return !!e.closest('#works')}")
        assert hit, width
        page.screenshot(path=str(out / f'{width}-works.png'))
        # The picture stays behind 01 CREATIVE SOLUTION, 02 PRODUCTION FLOW and 03 FAQ (a little calmer there).
        flow_top = page.evaluate("document.querySelector('[data-cxg-calm]').getBoundingClientRect().top + scrollY")
        scroll(page, int(flow_top - height * 0.1))
        calm = state(page)
        assert calm['visible'] and calm['fade'] == 1 and blur_px(calm['blur']) >= 12 and calm['veil'] > 0.4, (width, calm)
        page.screenshot(path=str(out / f'{width}-flow.png'))
        # 03 FAQ / CONTACT is the last section on the stage; the footer follows the stage directly.
        edges = page.evaluate("[document.querySelector('.cxg-stage').contains(document.querySelector('.cxfq')), Math.round(document.querySelector('.cxg-stage').getBoundingClientRect().bottom - document.querySelector('.cx-footer').getBoundingClientRect().top)]")
        assert edges[0] and abs(edges[1]) <= 1, (width, edges)
        scroll(page, 0)
        back = state(page)
        assert back['blur'] == 'none' and back['copy'] == 1 and back['fade'] == 1 and back['visible'], (width, back)
        # WORKS = the gallery (WordPress data); its own checks are tests/test_creative_works.py.
        assert page.locator('#works').evaluate("e=>e.classList.contains('cxw-ready')"), width
        assert page.locator('#works .cxw-thumb__title').all_inner_texts()[:3] == ['Good Bye MV', 'サン', 'VLOG']
        assert page.locator('.cxg-stage video').count() == 1 and page.locator('#works video').count() == 0
        # The rest of the page is unchanged.
        # (integrated page: 01 CREATIVE SOLUTION and 02 PRODUCTION FLOW on the stage)
        assert page.locator('[data-cxcs-card]').count() == 3 and page.locator('#cxg-flow').count() == 1
        assert not errors, (width, errors)
        page.close()

    # ---------- the CTA goes to WORKS on this page (<base href="/"> must not send it home) ----------
    page = browser.new_page(viewport={'width': 1280, 'height': 800})
    load(page)
    page.locator('.cxg-reel-hero__button--primary').click()
    page.wait_for_timeout(1400)
    assert page.evaluate('location.pathname') == '/services/creative-x/' and abs(state(page)['works']['top']) <= 2
    # A keyboard focus inside the faded copy shows it again.
    scroll(page, 400)
    assert state(page)['copy'] == 0
    page.locator('.cxg-reel-hero__button--primary').focus()
    assert page.evaluate("+getComputedStyle(document.querySelector('.cxg-reel-hero__copy')).opacity") == 1
    page.close()

    # ---------- video from WordPress (type creative_hero), pause/play, off-screen pause ----------
    if HAS_VIDEO:
        for width, expected in ((1280, UP + 'reel.mp4'), (390, UP + 'reel-sp.mp4')):
            page = browser.new_page(viewport={'width': width, 'height': 800 if width > 768 else 844})
            load(page, viewer=VIEWER + [HERO, HERO_SP], wait=1500)
            s = state(page)
            assert s['src'] == expected and s['playing'] and not s['paused'] and s['toggle'], (width, s)
            assert page.evaluate("(()=>{const v=document.querySelector('.cxg-reel video');return v.muted&&v.loop&&v.playsInline})()")
            page.locator('[data-cxg-reel-toggle]').click()
            page.wait_for_timeout(150)
            assert state(page)['paused'] and page.locator('[data-cxg-reel-toggle]').get_attribute('aria-label') == '背景の動画を再生'
            page.locator('[data-cxg-reel-toggle]').click()
            page.wait_for_timeout(300)
            assert not state(page)['paused']
            H = s['hero']['height']
            # Behind the text-heavy FAQ ([data-cxg-still]) the picture is held still; back in WORKS it plays again.
            faq_mid = page.evaluate("(() => { const r = document.querySelector('[data-cxg-still]').getBoundingClientRect(); return r.top + scrollY + r.height / 2 - innerHeight / 2; })()")
            scroll(page, int(faq_mid))
            page.wait_for_timeout(250)
            assert state(page)['paused'], 'held still behind FAQ'
            scroll(page, int(s['hero']['height']))
            page.wait_for_timeout(400)
            assert not state(page)['paused'], 'plays again in WORKS'
            # The stage now ends just above a short footer, so the page alone cannot scroll it off the screen:
            # a spacer after the footer lets the test reach that state.
            page.evaluate("(() => { const d = document.createElement('div'); d.id = 'cxg-test-spacer'; d.style.height = '200vh'; document.body.append(d); })()")
            past = page.evaluate("document.querySelector('.cxg-stage').getBoundingClientRect().bottom + scrollY")
            scroll(page, int(past + 10))                                             # stage off screen → paused
            page.wait_for_timeout(200)
            assert state(page)['paused']
            scroll(page, 0)
            page.wait_for_timeout(400)
            assert not state(page)['paused']
            # The work viewer covers the page: the background video waits (cxworks:viewer from js/cx-works.js).
            page.evaluate("document.dispatchEvent(new CustomEvent('cxworks:viewer', { detail: { open: true } }))")
            page.wait_for_timeout(150)
            assert state(page)['paused']
            page.evaluate("document.dispatchEvent(new CustomEvent('cxworks:viewer', { detail: { open: false } }))")
            page.wait_for_timeout(400)
            assert not state(page)['paused']
            page.screenshot(path=str(out / f'{width}-hero-video.png'))
            page.close()

        # Static sources (data/service-groups.json → data-sources) when WordPress has none; WebM first.
        page = browser.new_page(viewport={'width': 1280, 'height': 800})
        load(page, sources=[{'src': '/material/service-2026/test-reel.webm', 'type': 'video/webm'}], wait=1500)
        s = state(page)
        assert s['src'].endswith('/material/service-2026/test-reel.webm') and s['playing'], s
        page.close()

        # A broken file leaves the poster, without the pause button.
        page = browser.new_page(viewport={'width': 1280, 'height': 800})
        load(page, viewer=VIEWER + [dict(HERO, src=UP + 'broken.mp4')], wait=1500)
        s = state(page)
        assert not s['playing'] and not s['toggle'] and page.locator('.cxg-reel__poster').is_visible(), s
        page.close()
    else:
        print('ffmpeg not found: playback checks skipped')

    # Untrusted WordPress rows are ignored (other hosts, other types, plain http).
    page = browser.new_page(viewport={'width': 1280, 'height': 800})
    load(page, viewer=VIEWER + [dict(HERO, src='https://evil.example.com/reel.mp4'), dict(HERO, type='bizvideo'),
                                dict(HERO, src='http://cms.contentsx.jp/wp-content/uploads/reel.mp4')])
    assert not state(page)['src']
    page.close()

    # WordPress down: poster and scroll effect stay; WORKS says so.
    page = browser.new_page(viewport={'width': 1280, 'height': 800})
    load(page, fail=True)
    assert state(page)['live'] and '作品を読み込めませんでした' in page.locator('#works .cxw-message').inner_text()
    page.close()

    # Save-Data: scroll effect on the poster, no video.
    if HAS_VIDEO:
        page = browser.new_page(viewport={'width': 1280, 'height': 800})
        page.add_init_script("Object.defineProperty(navigator,'connection',{value:{saveData:true,effectiveType:'4g'}})")
        load(page, viewer=VIEWER + [HERO], wait=1500)
        s = state(page)
        assert s['live'] and not s['src'], s
        page.close()

    # Reduced motion: no video, no scroll-linked change; the poster switches once (sharp → blurred) and the
    # sections below still sit on it.
    for width in (390, 1280):
        page = browser.new_page(viewport={'width': width, 'height': 844 if width < 769 else 800}, reduced_motion='reduce')
        load(page, viewer=VIEWER + [HERO])
        s = state(page)
        assert s['live'] and s['position'] == 'fixed' and not s['src'] and s['blur'] == 'none', s
        scroll(page, int(s['hero']['height'] * 0.3))
        r = state(page)
        assert r['copy'] == 1 and r['blur'] == 'none', r
        scroll(page, int(s['hero']['height'] * 0.6))
        r = state(page)
        assert r['copy'] == 1 and blur_px(r['blur']) >= 12 and r['visible'], r
        assert page.locator('.cxg-reel__frame').evaluate('e=>getComputedStyle(e).transitionDuration') == '0s'
        page.screenshot(path=str(out / f'{width}-reduced.png'), full_page=False)
        page.close()

    # JS off: the HERO, the poster and the WORKS links are all there.
    ctx = browser.new_context(viewport={'width': 390, 'height': 844}, java_script_enabled=False)
    page = ctx.new_page()
    page.route('**/*', lambda r: r.fulfill(status=200, content_type='image/png', body=POSTER) if r.request.url.startswith('https://i.ytimg.com/')
               else r.continue_() if r.request.url.startswith('http://127.0.0.1:') else r.abort())
    page.goto(PAGE, wait_until='load')
    assert page.locator('h1').inner_text().replace('\n', '') == 'Creative X価値を、伝わるカタチにする。'
    assert page.locator('.cxg-reel__poster').evaluate('e=>e.complete && e.naturalWidth > 0')
    assert page.locator('.cxg-stage').evaluate("e=>!e.classList.contains('is-live')")
    assert page.locator('#works [data-cxw-fallback]').is_visible() and page.locator('#works [data-cxw-fallback] a').count() == 3
    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
    page.screenshot(path=str(out / '390-nojs.png'))
    ctx.close()
    browser.close()

print('creative hero: ok' + ('' if HAS_VIDEO else ' (playback skipped)'))
