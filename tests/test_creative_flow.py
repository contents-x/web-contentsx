"""Browser checks for Creative X landing「02 PRODUCTION FLOW」(2026-11). Run against a loopback preview.

python3 tests/test_creative_flow.py --url http://127.0.0.1:8796 --artifacts /tmp/cx-flow-qa [--channel chrome]
Layout at six widths (heading left / timeline right on PC, one column below), the four steps in order, the
rail (nodes level with each card, segments joining them), readable sizes, no horizontal scroll; the section
sits on the HERO stage with no background of its own; the one-time entrance (sitewide-motion.js) in order;
reduced motion and JS off show everything at once. WordPress is answered empty (the section does not use it).
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
PAGE = args.url.rstrip('/') + '/services/creative-x/'
TITLES = ['ご相談・ヒアリング', '企画・ストーリー設計', '制作・確認', '納品・活用']
YOU = ['課題やサービスの資料を共有', '企画内容を確認', '所定の確認段階で内容をチェック', '営業・Web・広告などで活用']
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
        if u.startswith(('http://127.0.0.1:', 'http://localhost:', 'https://fonts.googleapis.com/', 'https://fonts.gstatic.com/', 'https://i.ytimg.com/')):
            return r.continue_()
        return r.abort()
    page.route('**/*', route)
    page.goto(PAGE, wait_until='networkidle')
    page.wait_for_timeout(400)
    return page


def scroll_to_flow(page, step=0.6):
    """Scroll down as a visitor would, so the one-time entrance runs."""
    top = page.evaluate("document.querySelector('.cxpf').getBoundingClientRect().top + scrollY")
    y, h = 0, page.viewport_size['height']
    while y < top - 40:
        y = min(top - 40, y + h * step)
        page.evaluate(f'window.scrollTo(0, {y})')
        page.wait_for_timeout(80)


GEO = """() => {
  const r = e => e.getBoundingClientRect().toJSON(), q = s => document.querySelector(s);
  const steps = [...document.querySelectorAll('.cxpf-step')];
  const pseudo = (e, which) => { const cs = getComputedStyle(e, which), b = e.getBoundingClientRect();
    return { x: b.left + parseFloat(cs.left) + parseFloat(cs.width) / 2, top: b.top + parseFloat(cs.top) + (which === '::before' ? parseFloat(cs.marginTop) + parseFloat(cs.height) / 2 : 0),
             h: parseFloat(cs.height), content: cs.content }; };
  const s = q('.cxpf');
  return {
    over: document.documentElement.scrollWidth - innerWidth,
    head: r(q('.cxpf-head')), timeline: r(q('.cxpf-timeline')),
    titleText: (() => { const g = document.createRange(); g.selectNodeContents(q('.cxpf-title')); return g.getBoundingClientRect().toJSON(); })(),
    cards: steps.map(st => r(st.querySelector('.cxpf-card'))),
    titles: steps.map(st => st.querySelector('.cxpf-card__title').textContent.trim()),
    nums: steps.map(st => st.querySelector('.cxpf-card__num').textContent.trim()),
    you: steps.map(st => st.querySelector('.cxpf-card__you-label + span').textContent.trim()),
    youLines: steps.map(st => Math.round(st.querySelector('.cxpf-card__you').getBoundingClientRect().height)),
    nodes: steps.map(st => pseudo(st, '::before')), segs: steps.slice(0, -1).map(st => pseudo(st, '::after')),
    lastSeg: getComputedStyle(steps[3], '::after').content,
    imgs: steps.map(st => { const i = st.querySelector('.cxpf-card__img'), c = st.querySelector('.cxpf-card').getBoundingClientRect(), b = i.getBoundingClientRect();
      return { ok: i.complete && i.naturalWidth > 0, inside: b.left >= c.left - 1 && b.right <= c.right + 1 && b.top >= c.top - 1 && b.bottom <= c.bottom + 1 }; }),
    small: [...s.querySelectorAll('.cxpf-index, .cxpf-lead, .cxpf-card__desc, .cxpf-card__you, .cxpf-card__title')].map(e => parseFloat(getComputedStyle(e).fontSize)).filter(v => v < 12),
    bg: getComputedStyle(s).backgroundImage + '|' + getComputedStyle(s).backgroundColor,
    onStage: !!s.closest('.cxg-stage'), video: s.querySelectorAll('video, iframe').length,
    titleLines: Math.round(q('.cxpf-title').getBoundingClientRect().height / parseFloat(getComputedStyle(q('.cxpf-title')).lineHeight)),
    reel: (() => { const reel = q('.cxg-reel'); return { pos: getComputedStyle(reel).position, vis: getComputedStyle(reel).visibility, blur: getComputedStyle(reel.querySelector('.cxg-reel__frame')).filter }; })()
  };
}"""

with sync_playwright() as p:
    browser = p.chromium.launch(channel=args.channel) if args.channel else p.chromium.launch()

    # ---------- layout at six widths ----------
    for width, height in ((1920, 1080), (1440, 900), (1280, 800), (768, 1024), (390, 844), (375, 812), (320, 640)):
        page = open_page(browser, width, height)
        scroll_to_flow(page)
        page.wait_for_timeout(1400)                       # entrance done
        # Pictures load lazily: pass the last card once, as a visitor reading on would.
        page.evaluate("document.querySelector('.cxpf-step:last-child').scrollIntoView({ block: 'end' })")
        for _ in range(40):
            if page.evaluate("[...document.querySelectorAll('.cxpf-card__img')].every(i => i.complete && i.naturalWidth > 0)"):
                break
            page.wait_for_timeout(100)
        scroll_to_flow(page)
        page.wait_for_timeout(200)
        g = page.evaluate(GEO)
        assert g['over'] <= 0, (width, 'horizontal overflow', g['over'])
        assert g['titles'] == TITLES and g['nums'] == ['01', '02', '03', '04'] and g['you'] == YOU, (width, g['titles'], g['you'])
        assert g['titleLines'] == 2 or width in (768,), (width, 'title lines', g['titleLines'])   # 「ご相談から、」「完成まで。」
        assert not g['small'], (width, 'text under 12px', g['small'])
        assert all(i['ok'] and i['inside'] for i in g['imgs']), (width, g['imgs'])
        cards = g['cards']
        assert all(cards[i]['bottom'] <= cards[i + 1]['top'] for i in range(3)), (width, 'cards overlap')
        if width > 1100:   # heading left, vertically centred on the timeline
            assert g['head']['right'] < g['timeline']['left'], (width, g['head'], g['timeline'])
            mid = lambda b: (b['top'] + b['bottom']) / 2
            assert abs(mid(g['head']) - mid(g['timeline'])) < 60, (width, 'heading not centred')
            assert len({round(c['height']) for c in cards}) == 1, (width, 'cards differ in height')
            # The one-line 「ご相談から、」 stays in its column, clear of the timeline's rail.
            assert g['titleText']['right'] <= g['head']['right'] + 1 and min(n['x'] for n in g['nodes']) - g['titleText']['right'] >= 48, (width, g['titleText'], g['head'])
        else:              # heading above the cards
            assert g['head']['bottom'] < g['timeline']['top'], (width, g['head'], g['timeline'])
        if width > 600:    # the customer's part stays on one line
            assert len(set(g['youLines'])) == 1, (width, g['youLines'])
        # Rail: every node on one vertical line left of the cards, level inside its card; each segment
        # starts at its node and ends at the next one.
        xs = [n['x'] for n in g['nodes']]
        assert max(xs) - min(xs) < 1 and max(xs) < cards[0]['left'], (width, xs)
        for i, n in enumerate(g['nodes']):
            assert cards[i]['top'] + 10 < n['top'] < cards[i]['bottom'] - 10, (width, i, n, cards[i])
        for i, sgm in enumerate(g['segs']):
            assert abs(sgm['x'] - xs[0]) < 1.5 and abs(sgm['top'] - g['nodes'][i]['top']) < 1.5, (width, i, sgm)
            assert abs(sgm['top'] + sgm['h'] - g['nodes'][i + 1]['top']) < 2, (width, i, 'segment does not reach the next node')
        assert g['lastSeg'] == 'none', (width, 'no segment after STEP 04')
        # Background: none of its own; the stage's blurred HERO picture behind it.
        assert g['bg'] == 'none|rgba(0, 0, 0, 0)' and g['onStage'] and g['video'] == 0, (width, g['bg'])
        assert g['reel']['pos'] == 'fixed' and g['reel']['vis'] == 'visible' and 'blur' in g['reel']['blur'], (width, g['reel'])
        page.screenshot(path=str(out / f'{width}-flow.png'))
        assert not page.errors, (width, page.errors)
        page.context.close()
        report.append(f'{width}px: layout, order, rail, sizes, pictures, transparent on the stage ok')

    # ---------- the one-time entrance ----------
    page = open_page(browser, 1440, 900)
    before = page.evaluate("[document.querySelector('.cxpf-head').className, document.querySelector('.cxpf-timeline').className, getComputedStyle(document.querySelector('.cxpf-card')).opacity]")
    assert 'cx-motion-pending' in before[1] and 'cx-motion-visible' not in before[1] and before[2] == '0', before
    unlit = page.evaluate("getComputedStyle(document.querySelector('.cxpf-step'), '::before').backgroundColor")
    scroll_to_flow(page)
    page.wait_for_timeout(120)
    early = page.evaluate("[...document.querySelectorAll('.cxpf-card')].map(c => +getComputedStyle(c).opacity)")
    assert early[0] >= early[3], ('STEP 01 comes first', early)
    page.wait_for_timeout(1400)
    after = page.evaluate("""() => ({ cards: [...document.querySelectorAll('.cxpf-card')].map(c => getComputedStyle(c).opacity),
      nodes: [...document.querySelectorAll('.cxpf-step')].map(s => getComputedStyle(s, '::before').backgroundColor),
      segs: [...document.querySelectorAll('.cxpf-step')].slice(0, 3).map(s => getComputedStyle(s, '::after').transform),
      head: getComputedStyle(document.querySelector('.cxpf-head')).opacity })""")
    assert after['cards'] == ['1'] * 4 and after['head'] == '1', after
    assert all(n == 'rgb(255, 255, 255)' for n in after['nodes']) and unlit != 'rgb(255, 255, 255)', (unlit, after['nodes'])
    assert all(t in ('none', 'matrix(1, 0, 0, 1, 0, 0)') for t in after['segs']), after['segs']
    # Scrolling back up leaves everything shown (once only).
    page.evaluate('window.scrollTo(0, 0)'); page.wait_for_timeout(300)
    assert page.evaluate("getComputedStyle(document.querySelector('.cxpf-card')).opacity") == '1'
    page.context.close()
    report.append('entrance: heading, then cards from STEP 01 down, segments grow, nodes light; once only')

    # ---------- reduced motion, JS off ----------
    for name, kw in (('reduced', {'reduced': True}), ('nojs', {'js': False})):
        page = open_page(browser, 1280, 800, **kw)
        st = page.evaluate("""() => ({ pending: document.querySelectorAll('.cxpf .cx-motion-pending').length,
          cards: [...document.querySelectorAll('.cxpf-card')].map(c => getComputedStyle(c).opacity),
          nodes: [...document.querySelectorAll('.cxpf-step')].map(s => getComputedStyle(s, '::before').backgroundColor) })""") if kw.get('js', True) else None
        if st:
            assert st['pending'] == 0 and st['cards'] == ['1'] * 4 and all(n == 'rgb(255, 255, 255)' for n in st['nodes']), (name, st)
        else:
            assert page.locator('.cxpf-card').count() == 4 and page.locator('.cxpf-card').first.is_visible()
        page.evaluate("document.querySelector('.cxpf').scrollIntoView()") if kw.get('js', True) else page.locator('.cxpf').scroll_into_view_if_needed()
        page.wait_for_timeout(200)
        page.screenshot(path=str(out / f'1280-flow-{name}.png'))
        page.context.close()
    report.append('reduced motion and JS off: everything shown at once')
    browser.close()

(out / 'report.txt').write_text('\n'.join(report) + '\n', encoding='utf-8')
print('creative flow: ok')
for line in report:
    print(' -', line)
