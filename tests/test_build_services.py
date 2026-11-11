"""Offline checks for the static service generator and sitemap preservation."""

import importlib.util
import json
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


builder = load_module("build_services", ROOT / "tools" / "build-services.py")
sitemap = load_module("generate_sitemap", ROOT / "tools" / "generate-sitemap.py")


class ServiceBuildTests(unittest.TestCase):
    def setUp(self):
        self.services = json.loads((ROOT / "data" / "services.json").read_text(encoding="utf-8"))
        self.groups = json.loads((ROOT / "data" / "service-groups.json").read_text(encoding="utf-8"))

    def test_data_and_output_are_current(self):
        builder.validate(self.services, self.groups)
        self.assertEqual(builder.build(check=True), 0)

    def test_count_is_data_driven(self):
        sales = self.groups[0]
        for count in (7, 8, 9):
            services = list(self.services)
            for number in range(7, count):
                added = dict(services[0], id=f"extra-{number}", slug=f"extra-{number}", href=f"/services/extra-{number}/")
                services.append(added)
            builder.validate(services, self.groups)
            self.assertIn('href="/services/"', builder.render_home())
            self.assertEqual(builder.render_list(services, self.groups).count('<article class="cxsd-card '), count)
            self.assertEqual(len(re.findall(r'<article class="cxsd-card [^\"]+" id=', builder.render_directory_group(sales, services, 2))), count - 3)

    def test_directory_cards_and_legacy_urls(self):
        for service in self.services:
            card = builder.render_directory_card(service, 1)
            self.assertIn(service["name"], card)
            if service["id"] in builder.COMING_SOON:
                self.assertIn("乞うご期待", card)
                self.assertNotIn('公式サイトを見る', card)
            else:
                self.assertIn(service["hoverSummary"], card)
            redirect = builder.render_redirect(service)
            self.assertIn('location.replace(', redirect)
            self.assertNotIn('cxs-detail-hero', redirect)
        directory = builder.render_list(self.services, self.groups)
        self.assertTrue(directory.lstrip().startswith('<div class="cxsd-directory">\n  <section class="cxsd-group cxsd-group--creative"'))
        self.assertLess(directory.index('id="list-group-creative"'), directory.index('id="list-group-sales"'))
        self.assertNotIn('cxsd-hero', directory)
        self.assertNotIn('cxsd-jump', directory)
        self.assertIn('<h1 id="cxsd-creative-title">Creative X</h1>', directory)
        self.assertEqual(directory.count('href="/services/creative-x/"'), 1)
        self.assertEqual(directory.count('href="/services/sales-x/"'), 1)
        self.assertNotIn('<a class="cxsd-group__image"', directory)
        self.assertIn('href="https://bizform.contentsx.jp/"', directory)
        self.assertNotIn('href="#list-group-creative"', directory)
        self.assertNotIn('href="#list-group-sales"', directory)

    def test_service_destinations_are_explicit_and_safe(self):
        expected = {
            "bizform": "https://bizform.contentsx.jp/",
            "bizaio": "/services/#bizaio",
            "bizkarte": "/services/#bizkarte",
            "bizrecruit": "https://ichioshi.contentsx.jp/service.html",
            "bizmanga": "https://bizmanga.contentsx.jp/",
            "bizanime": "https://bizmanga.contentsx.jp/bizanime",
            "bizvideo": "/services/#bizvideo",
        }
        self.assertEqual({item["id"]: builder.service_destination(item) for item in self.services}, expected)
        for service in self.services:
            card = builder.render_directory_card(service, 1)
            if service["id"] in ("bizaio", "bizkarte"):
                self.assertNotIn("<a ", card)
            elif service["id"] == "bizvideo":
                self.assertIn('href="/contact"', card)
            else:
                self.assertIn(f'href="{service["destination"]}"', card)
                self.assertNotIn(f'href="{service["href"]}"', card)
        invalid = dict(self.services[0], destination="https://example.com/escape")
        with self.assertRaises(ValueError):
            builder.validate([invalid, *self.services[1:]], self.groups)

    def test_copy_is_escaped_and_video_stays_on_page(self):
        service = dict(self.services[0], hoverSummary="安全な <文字> & 説明")
        rendered = builder.render_directory_card(service, 1)
        self.assertIn("&lt;文字&gt; &amp;", rendered)
        creative = builder.render_list(self.services, self.groups)
        self.assertIn('data-video-src="/material/service-2026/bizanime-ieye.mp4"', creative)
        self.assertIn('data-video-src="/material/service-2026/bizvideo-memory-town.mp4"', creative)
        self.assertNotIn('data-youtube-id=', creative)

    def test_group_landings_use_official_creative_destinations(self):
        sales = builder.render_group_landing("sales", self.services)
        creative = builder.render_group_landing("creative", self.services)
        # 一覧カードは共通部品 .cx-feature-card（#141）。cxg-service-card は再生中・準備中の目印として残る
        self.assertEqual(sales.count('<article class="cx-feature-card cx-feature-card--wide cx-ui-card cxg-service-card '), 4)
        self.assertIn('href="https://bizform.contentsx.jp/"', sales)
        self.assertIn('href="https://ichioshi.contentsx.jp/service.html"', sales)
        self.assertIn('乞うご期待', sales)
        self.assertIn('/services/creative-x/', sales)
        # Creative X: 03 CREATIVE SOLUTION replaced the old 03 SERVICES image cards (2026-11).
        self.assertNotIn('cx-feature-card', creative)
        self.assertNotIn('id="cxg-three"', creative)
        self.assertEqual(creative.count('id="creative-solution"'), 1)
        self.assertIn('class="cxfq-dl js-dl-trigger"', creative)   # the brochure download (dl-modal.js) stays
        # Integrated page (2026-11): HERO → WORKS (no numbers) → 01 CREATIVE SOLUTION → 02 PRODUCTION FLOW →
        # 03 FAQ / CONTACT. The old 01 ABOUT and 02 WHY CREATIVE X are gone; the kept sections keep their ids.
        for gone in ('id="cxg-about"', 'id="cxg-reasons"', 'WHY CREATIVE X', '>ABOUT<'):
            self.assertNotIn(gone, creative)
        marks = ['class="cxg-reel-hero"', 'id="works"', 'id="creative-solution"', 'id="cxg-flow"', 'id="cxg-contact"']
        at = [creative.index(m) for m in marks]
        self.assertEqual(at, sorted(at))
        self.assertIn('<span>01</span> / CREATIVE SOLUTION', creative)
        self.assertIn('<span>02</span> / PRODUCTION FLOW', creative)
        self.assertIn('<span>03</span> / FAQ', creative)
        self.assertNotIn('03 <span>CONTACT</span>', creative)
        # One stage (one background: the HERO picture) holds every section, FAQ / CONTACT included.
        stage = creative.index('data-cxg-stage')
        self.assertEqual(creative.count('data-cxg-stage'), 1)
        self.assertLess(stage, at[0])
        self.assertEqual(creative.count('data-cxg-calm'), 1)
        self.assertLess(creative.index('data-cxg-calm'), at[4])

    def test_creative_faq_contact(self):
        # 03 FAQ / CONTACT (2026-11 design): five questions with their answers in the HTML (open without JS),
        # the accordion wiring, the CONTACT panel to /contact; on the stage, last before the footer.
        creative = builder.render_group_landing("creative", self.services)
        start = creative.index('<section class="cxg-section cxfq"')
        end = creative.index('<section class="cxfq-contact"', start)   # the questions part
        section = creative[start:end]
        self.assertIn('data-cxg-still', section)
        self.assertIn('<h2 class="cxfq-title" id="cxfq-title"', section)
        questions = [re.sub(r'<wbr>', '', q) for q in re.findall(r'<span class="cxfq-q__text"[^>]*>(.*?)</span>', section)]
        self.assertEqual(questions, ['何をつくるか決まっていなくても相談できますか？', 'マンガ・アニメ・映像は1つだけでも依頼できますか？',
                                     '料金や制作期間はどれくらいですか？', '依頼前に何を準備すればよいですか？', '制作途中で内容を確認できますか？'])
        answers = [re.sub(r'<wbr>', '', a) for a in re.findall(r'<div class="cxfq-a__inner"><p[^>]*>(.*?)</p>', section)]
        self.assertEqual(len(answers), 5)
        self.assertTrue(answers[0].startswith('はい。制作する形式が決まっていなくても'))
        self.assertTrue(answers[2].startswith('制作する形式や内容、ページ数、動画の尺などによって異なります。'))
        for n in range(1, 6):
            k = f'{n:02d}'
            self.assertIn(f'id="cxfq-q{k}" aria-controls="cxfq-a{k}" aria-expanded="true" data-cx-accordion-trigger', section)
            self.assertIn(f'id="cxfq-a{k}" role="region" aria-labelledby="cxfq-q{k}" data-cx-accordion-panel', section)
        self.assertNotIn(' hidden', section)                       # answers readable without JS
        self.assertIn('<a href="/faq"', section)
        self.assertIn('<section class="cxfq-contact" aria-labelledby="cxg-contact" data-cx-page-cta>', creative)
        self.assertIn('<a class="cxg-button cxfq-cta" href="/contact">', creative)
        self.assertEqual(creative.count(' data-cx-page-cta>'), 1)        # one page CTA (the footer hides its own)
        self.assertNotIn('creative-process.jpg', creative)            # the old white CONTACT is gone
        # The stage closes after FAQ / CONTACT: nothing but the page's end follows.
        self.assertTrue(creative.rstrip().endswith('</section>\n  </div>\n</div>'), creative[-80:])
        # Accordion assets on this page only.
        self.assertIn('/js/cx-accordion.js', builder.GROUP_ASSETS['creative']['scripts'])
        self.assertIn('/css/cx-accordion.css', builder.GROUP_ASSETS['creative']['styles'])

    def test_creative_production_flow(self):
        # 02 PRODUCTION FLOW (2026-11 design): heading, four steps in order, each with its picture and the
        # customer's part; no background picture or video of its own (the stage's HERO picture shows through).
        creative = builder.render_group_landing("creative", self.services)
        start = creative.index('<section class="cxg-section cxpf"')
        section = creative[start:creative.index('</section>', start)]
        self.assertIn('data-cxg-calm', section)
        self.assertIn('id="cxg-flow"', section)
        self.assertIn('<span>ご相談から、</span><span>完成まで。</span>', section)
        self.assertIn('<span>企画・ストーリー設計から制作、納品まで。</span><span>一つひとつ確認しながら進めます。</span>', section)
        titles = re.findall(r'<h3 class="cxpf-card__title"[^>]*>([^<]+)</h3>', section)
        self.assertEqual(titles, ['ご相談・ヒアリング', '企画・ストーリー設計', '制作・確認', '納品・活用'])
        self.assertEqual(re.findall(r'cxpf-card__num" data-i18n-skip>(\d\d)<', section), ['01', '02', '03', '04'])
        self.assertEqual(section.count('cxpf-card__you-label'), 4)
        for text in ('課題や<wbr>サービスの<wbr>資料を<wbr>共有', '企画内容を<wbr>確認', '所定の<wbr>確認段階で<wbr>内容を<wbr>チェック', '営業・Web・<wbr>広告などで<wbr>活用'):
            self.assertIn(text, section)
        pictures = re.findall(r'src="(/material/service-2026/creative-flow/[\w-]+\.webp)"', section)
        self.assertEqual(len(pictures), 4)
        for src in pictures + re.findall(r'(/material/service-2026/creative-flow/[\w-]+-640\.webp) 640w', section):
            self.assertTrue((ROOT / src.lstrip('/')).is_file(), src)
        for absent in ('<video', '<iframe', 'background-image', 'style='):
            self.assertNotIn(absent, section)
        self.assertNotIn('cxg-flowglass', creative)
        self.assertNotIn('04 PRODUCTION FLOW', creative)

    def test_creative_solution_cards_name_wordpress_works_only(self):
        creative = builder.render_group_landing("creative", self.services)
        picks = json.loads((ROOT / "data" / "creative-solution.json").read_text(encoding="utf-8"))["works"]
        cards = re.findall(r'<li class="cxcs-card cxcs-card--(\w+)" id="cxcs-card-\1" data-cxcs-card data-kind="\1" data-work-id="([^"]+)"', creative)
        self.assertEqual(cards, [(w["kind"], w["id"]) for w in picks])
        self.assertEqual([kind for kind, _ in cards], ["manga", "anime", "video"])
        # Without JS / WordPress each card links to its service; no work title, picture or embed is in the HTML.
        for href in ('https://bizmanga.contentsx.jp/biz-library', 'https://bizmanga.contentsx.jp/bizanime', '/services/#bizvideo'):
            self.assertIn(f'<a class="cxcs-card__action" href="{href}" data-cxcs-action>', creative)
        self.assertEqual(creative.count('<p class="cxcs-card__title" data-cxcs-title data-i18n-skip hidden></p>'), 3)
        # The section itself (the merged page also has the HERO poster, a YouTube still, above it).
        section = creative[creative.index('id="creative-solution"'):creative.index('id="cxg-flow"')]
        for absent in ('<iframe', 'youtube', 'ytimg', 'cms.contentsx.jp', 'カミレス', 'Good Bye', 'VLOG'):
            self.assertNotIn(absent, section)
        for copy in ('企業が伝えたいこと', '活用する場面', '営業資料', 'Webサイト', 'SNS広告', '採用活動',
                     '提案・商談の理解促進に', 'サービス・事例の訴求に', '認知拡大・集客に', '会社や仕事の魅力発信に'):
            self.assertIn(copy, creative)

    def test_creative_solution_config_is_validated(self):
        good = json.loads((ROOT / "data" / "creative-solution.json").read_text(encoding="utf-8"))
        builder.validate_solution(good)
        bad_cases = [
            {"works": good["works"][:2]},                                     # a service missing
            {"works": [good["works"][1], good["works"][0], good["works"][2]]},  # wrong order
            {"works": [dict(good["works"][0], id='x" onclick="1')] + good["works"][1:]},
            {"works": good["works"][:2] + [dict(good["works"][2], id="../../etc")]},
            {"works": good["works"][:2] + [dict(good["works"][2], id=None)]},
            {"works": "nope"},
        ]
        for bad in bad_cases:
            with self.assertRaises(ValueError):
                builder.validate_solution(bad)

    def test_extra_assets_only_on_creative_page(self):
        def page(group_id):
            return builder.render_page("<p>body</p>", "t", "d", f"/services/{group_id}-x/", [], "<header></header>",
                                       "<footer></footer>", builder.GROUP_ASSETS.get(group_id))
        creative, sales = page("creative"), page("sales")
        order = ["/js/wp-config.js", "/js/cx-dom.js", "/js/cx-manga-reader.js", "/js/cx-video-player.js",
                 "/js/cx-works.js", "/js/service-creative-solution.js"]
        positions = [creative.index(f'<script src="{src}" defer></script>') for src in order]
        self.assertEqual(positions, sorted(positions))
        self.assertLess(creative.index('/js/sitewide-motion.js'), positions[0])
        for href in ("/css/home-creative-x.css", "/css/cx-works.css", "/css/service-creative-solution.css"):
            self.assertIn(f'<link rel="stylesheet" href="{href}">', creative)
            self.assertNotIn(href, sales)
        self.assertIn("media-src 'self' https://cms.contentsx.jp;", creative)
        self.assertIn("media-src 'self';", sales)
        self.assertNotIn("cx-works.js", sales)

    def test_sitemap_update_preserves_other_sections(self):
        old = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
        new = sitemap.build_sitemap([{"id": 123, "date": "2026-09-26"}])
        self.assertIn("/services/creative-x/", new)
        self.assertNotIn("/services/bizmanga/", new)
        self.assertIn("/column/manga-marketing-btob-guide", new)
        self.assertIn("/news-detail?id=123", new)
        self.assertEqual(new.split("<!-- BUILD:NEWS -->")[0], old.split("<!-- BUILD:NEWS -->")[0])


if __name__ == "__main__":
    unittest.main()
