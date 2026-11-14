"""Browser checks for Creative X landing「03 FAQ / CONTACT」(2026-11) and js/cx-accordion.js.

python3 tests/test_creative_faq.py --url http://127.0.0.1:8796 --artifacts /tmp/cx-faq-qa [--channel chrome]
Layout at six widths (FAQ heading left / questions right on PC, one column below, CONTACT after), questions never
cut, readable sizes, touch targets, no horizontal scroll; the section on the HERO stage with no background of
its own and the footer right after it (its own contact block hidden); the accordion by mouse and keyboard
(aria-expanded, closed answers out of reach), the CTA to /contact, JS off (all answers shown) and reduced motion.
WordPress is answered empty (the section does not use it).
"""
import argparse
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
QUESTIONS = ['何をつくるか決まっていなくても相談できますか？', 'マンガ・アニメ・映像は1つだけでも依頼できますか？',
             '料金や制作期間はどれくらいですか？', '依頼前に何を準備すればよいですか？', '制作途中で内容を確認できますか？']
report = []


def open_page(browser, width, height, reduced=False, js=True):
    ctx = browser.new_context(viewport={'width': width, 'height': height}, has_touch=width <= 768,
                              reduced_motion='reduce' if reduced else 'no-preference', java_script_enabled=js)
    page = ctx.new_page()
    page.errors = []
    page.on('pageerror', lambda e: page.errors.append(str(e)))

    def route(r):
        u = r.request.url
        if '/wp-json/contentsx/v1/' in u:
            return r.fulfill(status=200, content_type='application/json', body='[]' if '/works' in u else '{}')
        if u.startswith((BASE, 'https://fonts.googleapis.com/', 'https://fonts.gstatic.com/', 'https://i.ytimg.com/')):
            return r.continue_()
        return r.abort()
    page.route('**/*', route)
    page.goto(PAGE, wait_until='networkidle')
    page.wait_for_timeout(300)
    return page


def scroll_to(page, selector, step=0.7):
    """Scroll down as a visitor would, so the one-time reveals run."""
    top = page.evaluate(f"document.querySelector('{selector}').getBoundingClientRect().top + scrollY")
    y, h = 0, page.viewport_size['height']
    while y < top - 40:
        y = min(top - 40, y + h * step)
        page.evaluate(f'window.scrollTo(0, {y})')
        page.wait_for_timeout(70)
    page.wait_for_timeout(1000)


STATE = """() => [...document.querySelectorAll('.cxfq-item')].map(it => { const b = it.querySelector('.cxfq-q__button'), p = it.querySelector('.cxfq-a'), t = p.firstElementChild;
  return { exp: b.getAttribute('aria-expanded'), open: it.classList.contains('is-open'), h: Math.round(p.getBoundingClientRect().height), vis: getComputedStyle(t).visibility }; })"""

with sync_playwright() as p:
    browser = p.chromium.launch(channel=args.channel) if args.channel else p.chromium.launch()

    # ---------- layout at six widths ----------
    for width, height in ((1920, 1080), (1440, 900), (1280, 800), (768, 1024), (390, 844), (375, 812), (320, 640)):
        page = open_page(browser, width, height)
        scroll_to(page, '.cxfq')
        g = page.evaluate("""() => { const r = s => document.querySelector(s).getBoundingClientRect().toJSON(), s = document.querySelector('.cxfq');
          const qs = [...s.querySelectorAll('.cxfq-q__text')];
          return { over: document.documentElement.scrollWidth - innerWidth, head: r('.cxfq-head'), list: r('.cxfq-list'), contact: r('.cxfq-contact'),
            questions: qs.map(q => q.textContent.trim()), cut: qs.filter(q => q.scrollWidth > q.clientWidth + 1 || q.scrollHeight > q.clientHeight + 1).length,
            buttons: [...s.querySelectorAll('.cxfq-q__button')].map(b => Math.round(b.getBoundingClientRect().height)),
            titleText: (() => { const g = document.createRange(); g.selectNodeContents(document.querySelector('.cxfq-title')); return g.getBoundingClientRect().toJSON(); })(),
            cta: r('.cxfq-cta'), ctaHref: s.querySelector('.cxfq-cta').getAttribute('href'),
            small: [...s.querySelectorAll('.cxfq-index, .cxfq-lead, .cxfq-q__text, .cxfq-q__num, .cxfq-a__inner p, .cxfq-more a, .cxfq-contact__label, .cxfq-contact__text, .cxfq-cta, .cxfq-dl')].map(e => parseFloat(getComputedStyle(e).fontSize)).filter(v => v < 12),
            bg: getComputedStyle(s).backgroundImage + '|' + getComputedStyle(s).backgroundColor, onStage: !!s.closest('.cxg-stage'), media: s.querySelectorAll('video, iframe, img').length,
            reel: getComputedStyle(document.querySelector('.cxg-reel')).position + '|' + getComputedStyle(document.querySelector('.cxg-reel')).visibility,
            footerContact: (document.querySelector('.cx-footer__contact') ? getComputedStyle(document.querySelector('.cx-footer__contact')).display : 'none'),
            gap: Math.round(document.querySelector('.cx-footer').getBoundingClientRect().top - document.querySelector('.cxg-stage').getBoundingClientRect().bottom) }; }""")
        assert g['over'] <= 0, (width, 'horizontal overflow', g['over'])
        assert g['questions'] == QUESTIONS and g['cut'] == 0, (width, g['questions'], g['cut'])
        assert all(h >= 56 for h in g['buttons']), (width, 'question rows too short to tap', g['buttons'])
        assert not g['small'], (width, 'text under 12px', g['small'])
        assert g['ctaHref'] == '/contact' and g['cta']['height'] >= 48, (width, g['cta'])
        if width > 1100:
            assert g['head']['right'] < g['list']['left'] and g['contact']['top'] > max(g['head']['bottom'], g['list']['bottom']), (width, g)
            assert g['cta']['left'] > g['contact']['left'] + g['contact']['width'] / 2, (width, 'CTA on the right of the panel')
            # The one-line title stays in its column, clear of the questions (it once ran into them).
            assert g['titleText']['right'] <= g['head']['right'] + 1 and g['list']['left'] - g['titleText']['right'] >= 48, (width, g['titleText'], g['head'], g['list'])
        else:
            assert g['head']['bottom'] <= g['list']['top'] and g['list']['bottom'] < g['contact']['top'], (width, g)
        if width <= 768:
            assert g['cta']['width'] >= g['contact']['width'] - 60, (width, 'CTA across the panel on phones', g['cta'], g['contact'])
        assert g['bg'] == 'none|rgba(0, 0, 0, 0)' and g['onStage'] and g['media'] == 0, (width, g['bg'])
        assert g['reel'] == 'fixed|visible', (width, g['reel'])
        assert g['footerContact'] == 'none' and abs(g['gap']) <= 1, (width, 'footer follows without its own contact block', g)
        page.screenshot(path=str(out / f'{width}-faq.png'))
        page.locator('#cxfq-q01').click()
        page.wait_for_timeout(450)
        page.screenshot(path=str(out / f'{width}-faq-open.png'))
        page.evaluate("document.querySelector('.cxfq-contact').scrollIntoView({ block: 'center' })")
        page.wait_for_timeout(1100)
        page.screenshot(path=str(out / f'{width}-contact.png'))
        assert not page.errors, (width, page.errors)
        page.context.close()
        report.append(f'{width}px: layout, questions whole, sizes, CTA, transparent on the stage, footer right after it ok')

    # ---------- accordion: mouse ----------
    page = open_page(browser, 1280, 800)
    scroll_to(page, '.cxfq')
    st = page.evaluate(STATE)
    assert all(s['exp'] == 'false' and not s['open'] and s['h'] <= 1 and s['vis'] == 'hidden' for s in st), st      # closed, out of reach
    page.locator('#cxfq-q03').click()
    page.wait_for_timeout(450)
    st = page.evaluate(STATE)
    assert st[2]['exp'] == 'true' and st[2]['open'] and st[2]['h'] > 40 and st[2]['vis'] == 'visible', st[2]
    assert page.locator('#cxfq-a03').inner_text().startswith('制作する形式や内容、ページ数、動画の尺などによって異なります。')
    assert page.evaluate("getComputedStyle(document.querySelector('#cxfq-q03 .cxfq-q__icon'), '::after').transform") != page.evaluate("getComputedStyle(document.querySelector('#cxfq-q01 .cxfq-q__icon'), '::after').transform")   # − vs +
    page.locator('#cxfq-q05').click()
    page.wait_for_timeout(450)
    assert [s['exp'] for s in page.evaluate(STATE)] == ['false', 'false', 'true', 'false', 'true']   # several may be open
    page.locator('#cxfq-q03').click()
    page.wait_for_timeout(450)
    st = page.evaluate(STATE)
    assert st[2]['exp'] == 'false' and st[2]['h'] <= 1 and st[2]['vis'] == 'hidden', st[2]
    report.append('accordion (mouse): closed at first, opens / closes on click, +/− icon, several may stay open')

    # ---------- accordion: keyboard ----------
    page.locator('#cxfq-q01').focus()
    page.keyboard.press('Enter'); page.wait_for_timeout(400)
    assert page.evaluate(STATE)[0]['exp'] == 'true'
    page.keyboard.press('Space'); page.wait_for_timeout(400)
    assert page.evaluate(STATE)[0]['exp'] == 'false'
    page.keyboard.press('ArrowDown')
    assert page.evaluate('document.activeElement.id') == 'cxfq-q02'
    page.keyboard.press('End')
    assert page.evaluate('document.activeElement.id') == 'cxfq-q05'
    page.keyboard.press('ArrowDown')
    assert page.evaluate('document.activeElement.id') == 'cxfq-q01'
    page.keyboard.press('Home')
    assert page.evaluate('document.activeElement.id') == 'cxfq-q01'
    # Tab goes from question to question (closed answers hold nothing focusable), then to the /faq link.
    page.keyboard.press('Tab')
    assert page.evaluate('document.activeElement.id') == 'cxfq-q02'
    page.locator('#cxfq-q05').focus()
    page.keyboard.press('Tab')
    assert page.evaluate("document.activeElement.getAttribute('href')") == '/faq'
    # The CTA goes to the existing contact page.
    page.locator('.cxfq-cta').click()
    page.wait_for_load_state('domcontentloaded')
    assert page.evaluate('location.pathname').rstrip('/') in ('/contact', '/contact.html'), page.url
    assert page.locator('form').count() >= 1, 'the existing contact form'
    assert not page.errors, page.errors
    page.context.close()
    report.append('accordion (keyboard): Enter / Space toggle, ↑ ↓ Home End move, Tab order; CTA → /contact (the existing form)')

    # ---------- JS off: every answer readable; reduced motion: no transition ----------
    page = open_page(browser, 390, 844, js=False)
    page.locator('.cxfq').scroll_into_view_if_needed()
    assert page.locator('.cxfq-a').count() == 5
    for i in range(1, 6):
        box = page.locator(f'#cxfq-a0{i}').bounding_box()
        assert box and box['height'] > 40, (i, box)
        assert page.locator(f'#cxfq-q0{i}').get_attribute('aria-expanded') == 'true'
    page.screenshot(path=str(out / '390-faq-nojs.png'))
    page.context.close()
    page = open_page(browser, 1280, 800, reduced=True)
    assert page.evaluate("getComputedStyle(document.querySelector('.cxfq-a')).transitionDuration") == '0s'
    assert page.evaluate("document.querySelectorAll('.cxfq .cx-motion-pending').length") == 0
    page.locator('#cxfq-q02').click()
    assert page.evaluate("Math.round(document.querySelector('#cxfq-a02').getBoundingClientRect().height)") > 40   # at once
    page.context.close()
    report.append('JS off: all five answers shown; reduced motion: no reveal, answers open at once')
    browser.close()

(out / 'report.txt').write_text('\n'.join(report) + '\n', encoding='utf-8')
print('creative faq: ok')
for line in report:
    print(' -', line)
