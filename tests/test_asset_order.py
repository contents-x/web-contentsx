"""共通CSS・共通JSの読み込み順の検査（2026-10-13 #147）。デプロイ前にも実行する（.github/workflows/static.yml）。
- sitewide-cohesion.css を読むページは、その前に brand-system-2026.css を読む（@import をやめたため）
- cxDom を使うJSを読むページは、その前に js/cx-dom.js を読む
python3 -m unittest discover -s tests -p test_asset_order.py"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP = ('_archive/', 'review/', 'tests/', 'skills/', 'node_modules/')
CX_DOM_USERS = ('cx-manga-reader.js', 'cx-video-player.js', 'home-creative-x.js', 'home-topics.js',
                'cx-works.js', 'service-creative-solution.js')


def pages():
    for p in list(ROOT.rglob('*.html')) + list((ROOT / 'tools' / 'templates').glob('*.tpl')):
        rel = p.relative_to(ROOT).as_posix()
        if not rel.startswith(SKIP):
            yield rel, p.read_text(encoding='utf-8', errors='ignore')


def first(text, pattern):
    m = re.search(pattern, text)
    return m.start() if m else None


class AssetOrder(unittest.TestCase):
    def test_brand_system_before_sitewide_cohesion(self):
        bad = []
        for rel, text in pages():
            cohesion = first(text, r'href="/?css/sitewide-cohesion\.css"')
            if cohesion is None:
                continue
            brand = first(text, r'href="/?css/brand-system-2026\.css"')
            if brand is None or brand > cohesion:
                bad.append(rel)
        self.assertEqual(bad, [], 'brand-system-2026.css を sitewide-cohesion.css より前に <link> してください')

    def test_cx_dom_before_users(self):
        bad = []
        for rel, text in pages():
            users = [first(text, r'src="/?js/' + re.escape(u) + '"') for u in CX_DOM_USERS]
            users = [u for u in users if u is not None]
            if not users:
                continue
            dom = first(text, r'src="/?js/cx-dom\.js"')
            if dom is None or dom > min(users):
                bad.append(rel)
        self.assertEqual(bad, [], 'js/cx-dom.js を使う側のJSより前に読み込んでください')


if __name__ == '__main__':
    unittest.main()
