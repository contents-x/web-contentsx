# ContentsX HP (contentsx.jp) — Claude Code 引き継ぎ資料

## リポジトリ
- GitHub: `josawa2255/ContentsX_HP` — **PUBLIC**
- デプロイ先: GitHub Pages → contentsx.jp
- DNS: お名前.com
- Git運用・レビューとマージ許可: [github.md](github.md)（リポジトリ所有者本人の確認による例外を含む）

> ⚠️ **WPプラグイン(PHP)はこのリポジトリにありません**（2026-08-04 分離）。
> マスターは `~/Documents/contentX/web/contentsx-wp-plugin/contentsx-cms/contentsx-cms.php`
> （GitHub: **PRIVATE** `josawa2255/contentsx-wp-plugin`）。
> このリポジトリがPUBLICのため、サーバー側で動くコードは置かない方針。
> 旧 `wordpress/contentsx-cms/` は削除済み（`wordpress/SETUP.md` のみ残置）。
> **push では本番反映されない** → お名前.comで手動アップロード（BUGS #002）。

## i18n（日英切替）システム

### アーキテクチャ（2層構造）
1. **JSON辞書** `i18n/en.json`（336エントリ）: テキストノード走査で日本語→英語に自動置換
2. **data属性** `data-ja` / `data-en`: HTML要素に直接付与。JSON辞書より優先

### 主要ファイル
- `js/i18n.js` — i18nエンジン本体
- `i18n/en.json` — 翻訳辞書
- `js/nav.js` — `switchLang()` は `window.i18n.switchLang()` に委譲。未ロード時はfallbackで直接走査

### 設定値
- localStorageキー: `cx-lang`
- 言語ボタンクラス: `.header-lang-btn`
- パブリックAPI: `window.i18n`（`switchLang`, `t`, `translateAll`, `addTranslations`, `getLang`, `getDict`, `translateElement`）

### スクリプト読込順序（必須）
```html
<script src="js/i18n.js" defer></script>
<script src="js/nav.js" defer></script>
```
i18n.js → nav.js の順序が必須。トップを含む全ページで共通ヘッダーに適用済み。

### 特殊対応
- `data-ph-ja` / `data-ph-en`: input placeholder の翻訳（contact.html）
- `.nav-dropdown-arrow` span: 翻訳時にドロップダウン矢印を保持
- MutationObserver: ENモード中の動的DOM要素を自動翻訳
- `data-i18n-skip`: 翻訳対象外指定
- `data-i18n-html`: innerHTML翻訳（改行タグ含む場合）
- カスタムイベント `i18n-lang-changed` で他JSに言語変更を通知
- 二重実行回避: `if (!window.i18n) { switchLang('en'); }`

## ページ構成

| ページ | ファイル | 主要JS |
|--------|---------|--------|
| トップ | index.html | i18n.js, nav.js, wp-api.js, home-2026.js, hero-about.js, home-hero.js, home-section-labels.js, cx-dom.js, cx-manga-reader.js, cx-video-player.js, home-creative-x.js, home-topics.js, hubspot-lazy.js（共通ヘッダーを使用。Creative X はWPのビューワー動画・マンガ作品をページ内のビューワーで表示、TOPICS はWP「Contents X ＞ TOPICS」から描画。仕様は SPEC.md §3） |
| サービス一覧・事業群・個別詳細 | services/ | i18n.js, nav.js, service-media.js, sitewide-motion.js（`tools/build-services.py` で生成。仕様は SPEC.md §3。⚠️ 生成スクリプト・テンプレート・`data/services.json` を変えたら、マージ前に `python3 -m unittest discover -s tests -p test_build_services.py` を通す。Pages のデプロイも同じ検査で、落ちると本番に出ない＝BUGS #065） |
| 会社概要 | company.html | script.js, dl-modal.js, hubspot-lazy.js |
| ContentsXについて | about.html | i18n.js, nav.js, sitewide-motion.js |
| 代表メッセージ | message.html | i18n.js, nav.js（`/message`。全文、支給画像、関連導線。SPEC.md §14） |
| 役員紹介（非表示） | leadership.html | `/about#message` へ転送 |
| 関連会社（非表示） | partners.html | `/company` へ転送 |
| 私たちの思い（旧URL） | our-thoughts.html | `/about#message` へ転送 |
| 採用情報 | recruit.html | recruit.js, wp-config.js, cx-dom.js, home-topics.js, dl-modal.js, hubspot-lazy.js, sitewide-motion.js（構成と演出は SPEC.md §9） |
| お問い合わせ（法人） | contact.html | form-common.js, contact.js（旧 `?position=` は採用フォームへ転送） |
| 採用エントリー | recruit/entry.html（`/recruit/entry`） | form-common.js, recruit-entry.js（採用専用。CRM・広告CVなし。仕様は SPEC.md §9.7） |
| ニュース一覧 | news.html | wp-config.js, wp-api.js, script.js |
| ニュース詳細 | news-detail.html | wp-config.js, script.js, hubspot-lazy.js + インラインJS |

企業案内で非表示にした導線、復帰手順、画像素材の扱いは [CORPORATE-PAGE-VISIBILITY.md](CORPORATE-PAGE-VISIBILITY.md) を参照。**コラム（`/column`）も 2026-09-29 から共通ナビの導線だけ一時非表示**（ページ・検索掲載は公開のまま。戻し方も同ファイル）。

## bizmangaサブページ（contentsx.jp/bizmanga/）
**現在は301リダイレクトのみ**。2026-04-27にBizMangaサイトが独立ドメイン `bizmanga.contentsx.jp` へ完全移行。
旧URLのブックマーク・外部リンクを拾うため、最小限のリダイレクトHTMLだけを残してある。

- HTML 6本 + robots.txt + sitemap.xml （計8ファイル、各約1KB）
- `<meta http-equiv="refresh">` + `window.location.replace()` で即時転送
- `noindex, follow` + canonical で SEO処理済み
- robots.txt で `Disallow: /` (検索エンジンはクロール不要)
- **CSS/JS は不要** (インラインスタイルで完結)、削除済み (2026-05-12)

⛔ このフォルダを削除すると、旧URL `contentsx.jp/bizmanga/*` を踏んだ訪問者が404に飛ぶ。**削除厳禁。**

## 制作事例モーダル（旧トップの記録。2026-09-29撤去）
> ⚠️ 下の `hero-new.js`・`js/data/works-detail.js` は 2026-10-29 にファイルごと削除した（どのページからも読まれていないのに公開され、非公開にした作品のデータが残っていた。戻すなら git の履歴から。`wp-api.js` は 2026-10-13 から `/works` を取得しないので、戻すなら取得も戻す）。以下は記録。
- データ: `js/data/works-detail.js`（WORKS_DETAIL_DATA配列）／表示: `hero-new.js` の `openWorkDetail()` でモーダル表示
- 非公開にした作品は素材フォルダ（`material/manga/{id}/`）からも消す（2026-10-27〜29 に4作品を削除。ルート BUGS.md #085）。素材の画像を消す前に BizManga も含めて参照を grep する（BUGS #020）
- カルーセル: 1ページ目の縦横比で縦読み(vertical-scroll)/カルーセル切替
- タイトル+カテゴリタグ: `.work-detail-title-row` でflexbox横並び（BizMangaと同仕様）

## 採用ページ（recruit.html）
- ヒーローは白基調＋Xコラージュ、Xが書き順（＼→／）で描かれる（SPEC.md §9.0）。⚠️ 画像差し替え時は SVG の帯の座標と線の長さを測り直す
- 構成: HERO → 募集職種 → 選考 → エントリー → TOPICS（トップと共通）。日差しの演出は HERO→募集職種の切り替えだけで、他のセクションに繰り返さない（SPEC.md §9.1〜9.6）
- ⚠️ 募集職種〜エントリーの背景は `.rc-stage__bg` の1枚（sticky）を共有する。セクションごとに背景画像を足さない（SPEC.md §9.1）
- 職種カード「詳細を見る」→ カード一覧の直下にその職種の募集要項だけを開く
- ⚠️ **応募は採用専用フォーム `/recruit/entry`**（職種からは `?position=職種名`）。法人お問い合わせ `/contact` に向けない。採用フォームには CRM の貼り付けコード・Google広告のお問い合わせCV・HubSpot 追跡スクリプトを入れない。送信先は暫定で HubSpot 共通フォーム（採用専用の受付先が決まったら `js/recruit-entry.js` 先頭の1行を差し替え。SPEC.md §9.7）
- 営業・エンジニアは長期インターン。募集要項はゼロワンインターン掲載（7846／7845）と同じ内容で、掲載を変えたら募集要項と JSON-LD もそろえる（SPEC.md §9.2）
- ⚠️ 未確定: 選考セクション（PROCESS）の文言はデザイン上の仮案（掲載の選考フローは「応募→1次面接→最終面接→内定」。公開前に照合）

<!-- 漫画ビューアは独立BizMangaサイト (bizmanga.contentsx.jp) に移行済み。
     旧 bizmanga/js/works.js は 2026-05-12 に削除。 -->

## 共通部品（JS・CSS）
- **小さな道具は増やさず `js/cx-dom.js`（`window.cxDom`）を使う**: 要素づくり `el`、アイコンボタン、`text`、画像URLの検査 `safeImage`、タイムアウト付き取得 `getJSON`。使うファイルより前に defer で読む（SPEC.md §4）
- HubSpot 追跡コードの遅延読み込みは `js/hubspot-lazy.js` の1行で入れる（ページに埋め込まない）
- 読み込み順（`brand-system-2026.css` → `sitewide-cohesion.css`、`cx-dom.js` → 使う側）は `tests/test_asset_order.py` がデプロイ前に検査する。新しいページ・試作ページでも同じ順で書く
- コラム生成（`tools/build-c-columns.py`）は WordPress の値を信用しない: サムネイルは許可ホストの https だけ、スラッグは区切り・引用符を含まないものだけ、`<script>` 内の JSON は `<` `>` `&` を \\u 表記に（`tests/test_build_c_columns.py`）
- コラム記事の見た目は `css/column-article.css`、規約2ページは `css/legal.css`
- 使っていないCSSを消すときは [CSS-ARCHITECTURE.md](CSS-ARCHITECTURE.md)「未使用CSSの削除方法」の手順（ブラウザで変更前後のルールを照合し、全ページ撮り比べ）

## 公開範囲と監視（2026-10-14 セキュリティ強化）⭐
- ⛔ **このリポジトリは PUBLIC。顧客情報・インフラ構成・未対応の弱点リスト・認証の手順をコミットしない**（2026-10-14、`.skill` 2本と SEO 戦略の `.docx` が公開されていたのを除去。原本はローカル専用の `../docs/private-from-contentx-repo/`）。
- ⛔ **GitHub Pages の公開方式は「GitHub Actions」（`build_type: workflow`）から変えない**。「ブランチから公開（legacy）」に戻すと、従来型の公開処理がリポジトリ全体を同時に公開し、許可リストが効かなくなる（2026-10-14 に実際に競合した。監視が検知する）。
- ⚠️ **自動ビルド（GITHUB_TOKEN での push）は push トリガーのワークフロー（`static.yml` の公開と IndexNow 通知）を起動しない**（GitHub の仕様。legacy の頃は従来型の公開処理が拾っていた）。そのため `build-c-columns.yml` は、実際に main へ push したときだけ別ジョブ（`dispatch`。起動の権限 `actions: write` はこのジョブだけに付け、WordPress のデータを扱うビルドのジョブには渡さない）で `gh workflow run static.yml` を実行する。`static.yml` は公開が成功してから、前回デプロイしたコミットから今回までに変わった URL を IndexNow へ通知する（先に送るとクローラーが 404 を受け取る。旧 `indexnow.yml` はここへ統合）。workflow_dispatch は GITHUB_TOKEN からでも起動できる。**本番のファイルを書き換える自動ビルドを新しく足したら同じ `dispatch` ジョブを入れる**。漏れて本番が main より1時間以上古いままだと監視が知らせる。
- 本番に出るのは `tools/build-site-artifact.py` の**許可リスト**（HTML・CSS・JS・画像・動画・PDF・sitemap 等と、名前を指定した `robots.txt` `llms.txt` `manifest.json` `i18n/en.json` など）だけ。`*.md`・スクリプト・テスト・`data/`・`review/`・`skills/` は公開しない。**新しい種類のファイルを公開したいときは許可リストに足す**（足さないと本番で 404）。検査は `tests/test_site_artifact.py`（デプロイ前に実行。公開ページが参照するファイルの漏れも見る）。
- 改ざん・乗っ取りの監視 `.github/workflows/security-monitor.yml`（1時間ごと、`tools/security/monitor.py`）: 本番の HTML/CSS/JS がデプロイしたコミットと同一か、外部スクリプトのホスト、内部資料が見えないか、DNS、証明書、GitHub Pages の設定（独自ドメイン・HTTPS 強制・公開方式）、本番が main より1時間以上古いままか、PR を通らない main への push・強制 push、WordPress で閉じた入口（`expected.json` の `wordpress` で true にした項目だけ: ユーザー一覧API、`xmlrpc.php` が閉じている〈403/404/405/410〉、無関係なオリジン〈`null`・前方一致／後方一致の誤りを突く形を含む〉に CORS を許可していない、本番以外のオリジンに資格情報〈Cookie〉つきの CORS を出していない〈独自API と WordPress 本体の API〈代表は REST の入口 `/wp-json/`。`/wp/v2/` 以下は前段が Actions の IP を遮断する〉、GET とブラウザと同じ形のプリフライトの両方。エラー応答のヘッダーも見る。試す開発用オリジンは `cors_probe_origins`。プラグインの許可一覧とは同期しない一般的な判定〉。WordPress に接続できない・エラーを返す回は注意1件で打ち切る。サーバー（お名前.com）側の守り: 海外〈監視を動かす GitHub Actions〉から管理画面・ログイン画面に届かない〈国外アクセス制限〉、WAF が攻撃の形をした要求を止める）。判定は `tests/test_monitor.py` で検査（監視のファイルを変える PR で `security-monitor.yml` が実行する）。**異常で失敗 → GitHub からメール**。
- ⚠️ WordPress の点検項目は、プラグインの変更が**お名前.com へのアップロードで本番に反映されたのを確かめてから** `expected.json` の `wordpress` に true で足す（反映前に足すと毎時失敗する。PUBLIC リポジトリなので、未反映の項目をここに書かない）。
- 意図して変えるとき（DNS の変更・外部スクリプトの追加・WordPress の強化完了）は、`tools/security/expected.json` を同じ PR で直す。直さないと監視が毎時失敗する。

## 外部サービス
- HubSpot: Portal 48367061, Form b6da14d0-d60d-4357-89fc-0015ed32b704
- WordPress API: `https://cms.contentsx.jp/wp-json/contentsx/v1`（wp-config.js）
- DNS/ドメイン: お名前.com

## CSS設計
- メインサイト: `css/style.css`（共通）+ ページ別CSS。トップは `css/home-2026.css`（HEROは `home-hero.css`、Hero→Aboutは `hero-about.css`、ABOUT / SERVICE / NEWS の共通背景とスナップは `home-sections.css`、Creative X は `home-creative-x.css`、Sales X は `home-sales-x.css`、TOPICS は `home-topics.css`、NEWS は `home-news.css`（行の描画は `wp-api.js` のトップ用分岐）。仕様は SPEC.md §3）、他ページは `recruit.css` 等を使用。
- **CSS構成・共通化の計画と、共通CSSを変えたときの全ページ撮り比べ（`tests/sitewide_check.py`）は [CSS-ARCHITECTURE.md](CSS-ARCHITECTURE.md)**。共通CSS・トークン・共通部品を触るPRは必ず撮り比べる。
- フッターは全ページ共通の `.cx-footer`（`css/site-footer.css`）。変更時は静的ページ・コラム記事テンプレ・`services/index.html` の3か所を揃える（SPEC.md §7.5）。
- トップ・サービス以外の下層ページは `css/brand-system-2026.css` → `css/sitewide-cohesion.css` の順に `<link>`（2026-10-13 から `@import` ではなく2行セット）し、`body.cx-sitewide` を追加して共通の色、文字、余白、CTAを揃える（仕様は [SPEC.md §13](SPEC.md)）。コラム記事は `tools/templates/c-column.html.tpl` にも読み込みを置く。並列のトップ・サービス担当との色の調整は「claude連絡網」で共有する。
- トップ・サービス・下層ページ共通のモーションとUIの判断基準は [MOTION-UI-2026.md](MOTION-UI-2026.md)。サービスと下層ページの登場・画像ワイプ演出は `js/sitewide-motion.js`。動きの軽減設定とJS無効時の表示を必ず確認する。
- トップ・サービス・下層ページのフォント、色、文字階層、画像上の文字は [DESIGN-SYSTEM-2026.md](DESIGN-SYSTEM-2026.md) が正本。再利用する変数・画像文字クラスは `css/brand-system-2026.css`。担当ごとに色・フォントの値を新設しない。

## 未完了タスク
- トップページとSales X / Creative X紹介ページに続き、会社案内・採用・ニュース・コラム等の**その他すべてのページ**を同じデザイン体系に揃える。3体目のAIエージェントが担当予定（2026-09-29 平澤依頼）。色・余白・タイポグラフィー・共通ヘッダーを `data/design-tokens.json` とトップ/サービスの実装に照らして統一し、ページ固有機能と既存の外部連携は保つ。並列作業中は別worktreeを使い、トップ・サービス担当とは連絡網でリンク先と共通UIを調整する。
