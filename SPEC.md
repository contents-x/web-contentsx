# ContentsX 仕様書

**ドメイン**: contentsx.jp
**リポジトリ**: [contents-x/web-contentsx](https://github.com/contents-x/web-contentsx)（2026-11 に josawa2255/ContentsX_HP から移管・改名）
**デプロイ**: GitHub Pages（CNAME: お名前.com）
**最終更新**: 2026-10-07

> このファイルは ContentsX 単体の仕様を記録します。忘れがちな特殊動作・URLパラメータ・共通コンポーネント・外部連携を一箇所に集約し、将来のメンテ時に参照します。

---

## 1. ページ構成

| ページ | ファイル | 主要JS | 説明 |
|---|---|---|---|
| トップ | `index.html` | i18n.js, wp-api.js, home-2026.js | 2026年9月版。X字の都市ビジュアル、Sales X / Creative X、支援の流れ、サービス、会社紹介、既存News（写真付きの相談CTAは2026-10-08に撤去し、共通フッター上部の小さな導線に置き換え）。CSSは `css/home-2026.css`。ヘッダーは一時撤去 |
| サービス一覧 | `services/index.html` | i18n.js, nav.js, service-media.js | Creative X / Sales Xの事業紹介とサービス一覧。動画はページ内再生 |
| Sales X / Creative X | `services/sales-x/index.html`・`services/creative-x/index.html` | i18n.js, nav.js, service-media.js | 事業群ごとの紹介ページ |
| 旧サービス詳細URL | `services/{slug}/index.html` | 転送のみ | 個別詳細は廃止。公式サイトまたは一覧の該当サービスへ転送 |
| 会社概要 | `company.html` | script.js, cta.js, dl-modal.js | |
| ContentsXについて | `about.html` | i18n.js, nav.js, sitewide-motion.js | HERO・WHY・OUR ROLE・MISSION/VISION・VALUES・MESSAGE・FUTUREを統合。前半は `css/about-2026.css` / `about-why.css` / `about-our-role.css`、後半03–06は `css/about-late-2026.css`、末尾CTAは `css/about-next-action.css`。VALUES/FUTUREは共通feature-cardを再利用。後半の人物/未来写真は生成イメージ、代表メッセージは黒宮代表の既存実写真と確定本文 |
| 代表メッセージ | `message.html` | i18n.js, nav.js, message-2026.js | `/message`。指定された新原稿を全文掲載。PCは左コピー・右ポートレート、1024px以下はMESSAGE→コピー・署名→写真→本文。本体コードで管理する静的ページ。支給PC/SPハンドオフに沿う最大1280pxの構成、本文最大720px・4章見出し、実写真、サムネイル付き関連リンク。Heroと会議写真だけ軽いフェード、本文は常時表示 |
| 役員紹介 | `leadership.html` | 転送のみ | 一時非表示。`/about#message` へ転送 |
| 主要関連会社 | `partners.html` | 転送のみ | 一時非表示。`/company` へ転送 |
| 採用情報 | `recruit.html` | recruit.js, wp-config.js, home-topics.js, dl-modal.js, sitewide-motion.js | HERO / 募集職種 / 選考 / エントリー / TOPICS（§9） |
| お問い合わせ | `contact.html` | form-common.js, contact.js | 法人向け。HubSpot Forms API + 送信ボタン演出 |
| 採用エントリー | `recruit/entry.html`（`/recruit/entry`） | form-common.js, recruit-entry.js | 採用専用フォーム（§9.7）。noindex |
| ニュース一覧 | `news.html` | wp-config.js, wp-api.js, script.js | |
| ニュース詳細 | `news-detail.html` | wp-config.js + インラインJS | |
| コラム一覧 | `column.html` | i18n.js, nav.js, column.js | Featured + カテゴリチップフィルタ + カードグリッド。`tools/build-c-columns.py` が WP API (`?site=contentx`) からカード・カテゴリ・ItemList JSON-LD・Featured を自動注入（`<!-- BUILD:COLUMN_GRID -->` マーカー間） |
| コラム個別 | `column/{slug}.html` | (静的) | `tools/build-c-columns.py` で生成。`/column/` は `column/index.html` の meta refresh で `/column` へリダイレクト |
| Chrome 拡張機能一覧 | `extensions/index.html` | i18n.js, nav.js | `/extensions/`。拡張機能ごとにカードを追加できる一覧。全ページ共通フッター（§7.5）から導線を設置 |
| TabLabo 紹介 | `extensions/tablabo/index.html` | i18n.js, nav.js | `/extensions/tablabo/`。機能・画面・料金・法人導入の案内 |
| TabLabo ポリシー・規約 | `extensions/tablabo/privacy.html`・`extensions/tablabo/terms.html` | i18n.js, nav.js | 拡張子なしURL。本文は日本語の正本を保持し、自動翻訳の対象外 |
| TabLabo AIアクセス許可 | `extensions/tablabo/oauth/consent/index.html` | 提供HTML内のJS・supabase-js | `/extensions/tablabo/oauth/consent/`。共通UIと計測タグを入れない独立画面。noindex |
| 営業管理サービス（ビズセールスナビ）紹介 | `crm/index.html` | i18n.js, nav.js | `/crm/`。Google 連携の同意画面に載せるホームページ（§1.3） |
| 営業管理サービス ポリシー・規約 | `crm/privacy.html`・`crm/terms.html` | i18n.js, nav.js | 拡張子なしURL `/crm/privacy`・`/crm/terms`。本文は日本語の正本を保持し、自動翻訳の対象外（§1.3） |

### 1.1 Chrome 拡張機能・TabLabo（Issue #69）

- デザインは `css/extensions.css` と既存の `css/style.css`・`css/sitewide-cohesion.css`。企業の濃紺・共通トークンを使用し、TabLaboの製品色は紫 `#4f46e5`。提供された実画面5枚をWebPで `material/extensions/tablabo/` に配置。画像は全体表示し、クリックで元寸法の画像を別タブに開く。UI内のデータは架空のテストデータ。
- 一覧に拡張機能を追加する際は `extensions/index.html` の `.ext-grid` 内に `.ext-card` の `article` を追加し、画像・原稿・紹介先を変更する。紹介ページも追加し、`sitemap.xml` に公開URLを登録する。OAuth許可画面はサイトマップへ載せない。
- 紹介と一覧は日英の `data-ja` / `data-en` を使用。規約・ポリシーの本文は `data-i18n-skip` で日本語を維持。共通JSは `i18n.js` → `nav.js` の順。`base href="/"` と絶対パスで深い階層のナビ・画像・CSSを解決する。
- ストアURLが未確定の間、CTAは「限定公開中・お問い合わせ」で `/contact` へ。確定後は紹介と一覧のCTAをストアへの導線へ差し替える。窓口は `help@contentsx.jp`。
- 規約・ポリシーは提供原稿の本文を保持し、草案・根拠・編集者向けの注記を公開HTMLから除く。初回公開日は2026年10月7日（日本時間）。`data-publication-date` の制定日・最終更新日4箇所に同日を設定。改定時は制定日を維持し、最終更新日だけ実際の改定日に変更する。未確定表示のまま公開しない。
- 公開は所有者の内容確認・明示的なマージ許可後に行い、公開URL5件を依頼元へ連絡する。ポリシーと規約は `/extensions/tablabo/privacy`・`/extensions/tablabo/terms`、紹介・一覧・OAuth許可画面は末尾 `/` を維持する。
- OAuth許可画面はTabLabo担当のHTMLをバイト単位で変更せず配置。ヘッダー・フッター・計測・共通CSS/JS・`base`・転送処理を追加しない。SupabaseのURLとpublishableキーはブラウザ公開を前提とする値。変更が必要な場合は担当へ依頼し、更新原稿を再配置する。
- OAuthの公開前検証は `?authorization_id=test` 付きのURLで「TabLabo にログイン」または「この接続の情報を確認できませんでした」の表示を確認する。ローカル検証では認証SDKをスタブ化し、Googleログイン・トークン発行・許可/拒否の本番書き込みを行わない。
- 再検証用スクリプト: `python3 tests/verify_extensions_layout.py --url http://127.0.0.1:8769` と `python3 tests/verify_tablabo_oauth.py --url http://127.0.0.1:8769`（Python PlaywrightとGoogle Chromeが必要）。先に `python3 tools/preview-extensions.py --port 8769` で、拡張子なしの `.html` 解決に対応したローカルサーバーを起動する。OAuth検証には提供HTMLのSHA-256一致チェックを含むため、原稿を更新した場合は担当から受け取った版との一致を確認してハッシュも更新する。PR確認用の画像は `tests/screenshots/extensions/`。

### 1.3 営業管理サービス（ビズセールスナビ）の紹介・ポリシー・規約（Issue #182）

- 当社の法人向け営業管理サービスの Google 連携（カレンダー・Gmail）の同意画面に載せる3ページ。**URL に製品名を入れない**（`/crm/`）。製品名が変わっても URL を変えない（変えると Google の同意画面の設定と審査をやり直すことになる）。
- 本文の正本はサービス側の非公開リポジトリの原稿。ここでは文面を直接直さず、原稿を直してから同じ HTML に写す。草案・編集者向けの注記は載せない。
- 型は TabLabo のポリシー（`extensions/tablabo/privacy.html`）と同じ `css/extensions.css` の `.ext-legal`。共通ヘッダー・フッターを使う。
- `services/` は `tools/build-services.py` が生成するフォルダなので、これらのページを置かない。
- 制定日・最終更新日は公開した日。文面を変えたら最終更新日を直す。

### 1.2 TabLabo規約・ポリシーの原稿更新（Issue #71）

- 2026年10月7日、TabLaboのmain（コミット `715bf521c0940b9d118acbaa6c56269139fcc2fe`）の `docs/store/terms.md`・`docs/store/privacy-policy.md` から本文を取得して更新。作業ツリーの古い原稿ではなく、依頼元が指定したmainのコミットを参照する。
- 利用規約の第7条に無料プラン・月額300円の有料プラン・1人あたり月額200円の組織プラン、支払い・解約等を反映。料金条項は11項目と第1項内の2つの箇条書きの階層を保持する。
- プライバシーポリシーにURLごとのメモ・作業の栞・候補トレイ・共有リンク・AI連携の記録・個人/組織プランの契約情報・ピン留め、端末内の起動日時とタブID、Stripeへの委託を反映。
- 同日内の差し替えのため、制定日・最終更新日は2026年10月7日を維持。草案・編集者向け注記は除外し、日本語の本文を保持。ピン留めの行は依頼に従って含める。
- 一覧・紹介・OAuth同意画面は変更しない。特定商取引法に基づく表記はStripeの準備後に依頼元から別途依頼されるため、本作業では追加しない。

### 1.1 企業案内のスマホ表示（2026-10-11・Issue #121）

- 対象: `/about`（Contents Xについて）と `/message`（代表メッセージ）。原稿・写真・共通ヘッダー/フッターは維持する。
- `/about` は1024px以下でHero・事業/理念/これから・ミッション/ビジョン・代表紹介を1列へ。本文は16〜17px/行間1.85、左右余白20px・本文領域最大720px。見出しはclampで連続調整し、理念コピーは均等な改行を補助する。署名は14pxで折り返し可能にする。
- スマホのHero/各パネルで共通 `section` の上下100px余白とPC用の最小高さを上書きし、章の始まりと写真に32px前後の余白を取る。PCの1025px以上の構図は変更しない。
- WebKitの見切れ対策: バリューのflex内見出しは `min-width:0` と `overflow-wrap:anywhere`、相談CTAのflex子は `min-width:0`・`max-width:100%` と折り返しを指定する。ページ全体の横スクロールだけでなく、`overflow:clip` の内側で文章が切れていないことも検証する。
- `/message` は既存の16〜17px・行間1.9・写真/本文の縦構成を保つ。両ページとも1024px以下で `word-break:auto-phrase` 非対応のブラウザでは日本語の本文を `word-break:normal` にし、句読点だけが行頭へ落ちる折り返しを防ぐ。代表メッセージの原稿と構図は変更しない。
- 検証: `python3 tests/test_company_mobile.py --url <loopback preview> --artifacts <output>`。Chromium/WebKit、320〜1920pxの22幅（768・800・1024pxの境界前後を含む）、日本語フォント実読込、1.4倍文字拡大、画像と本文のはみ出し/欠け/比率、タップ領域、日英往復、企業案内のタッチナビ、全文/関連リンク、通常スクロール・動き軽減・JS無効を確認する。

## 2. URL パラメータ

### 2.1 プラン事前選択（BizMangaと共通）
`?plan=light|standard|premium` — お問い合わせフォーム経由

### 2.2 採用ポジション事前選択
`?position={職種名}` — `/recruit/entry` で希望職種を自動選択（リストに無い文字は「その他・未定」＋本文の先頭に残す）。旧リンク `/contact?position=…` は `contact.html` の head で `/recruit/entry` へ転送（§9.7）
`?type=新卒|正社員（中途）|インターン` — `/recruit/entry` で応募区分を自動選択

### 2.3 UTM / トラッキング
`?utm_source=` `?utm_medium=` `?utm_campaign=` `?source=`
contact フォーム送信時にメッセージ末尾にトラッキング情報を自動付加

### 2.4 TabLabo OAuth許可画面
`/extensions/tablabo/oauth/consent/?authorization_id=...` — AIアプリから受け取った認可要求IDを保持する。Googleログインから戻る `?code=...` は提供HTMLのSupabase SDKが処理する。URLの正規化や転送でクエリを削除しない。

## 3. トップページ 2026年9月版 ⭐

- デザイン基準: `/Users/hirasawa4323/Documents/contentX/デザイン案画像/会社HP/TOP確定/分析出力 1〜14.png`。奇数=PC、偶数=SP、番号順=ページ上から下。トップも他ページと同じ共通ヘッダーを使用し、固定ヘッダーの高さ分だけヒーローを下げる。お知らせセクションのマークアップと `wp-api.js` による更新は維持。
- 構成: Hero → About（Heroからスクロール連動で接続。ABOUT・Creative X・Sales X・TOPICS・Newsは共通背景。ABOUT〜NEWS は継ぎ目なく連続） → Creative X → Sales X →（サービス一覧＝非表示中）→ TOPICS → News → フッター（写真付きの相談CTA `.cxh-contact` は Issue #94 で撤去。NEWSは最後のセクションなので下の余白を白フェードより広く取り、白になりきってから濃紺のフッターへ切り替える）。旧ロゴカルーセル・新作情報・制作事例モーダル・旧Hero OPはトップから撤去。
- 2026-10-07（Issue #83）: コンセプト（Sales X × Creative X = Contents X）・Sales X / Creative X の2枚カード・「売上が生まれるまでの流れ」を削除。ABOUT / Creative X / Sales X と内容が重なり、共通背景を白いブロックで途切れさせていたため。サービス同士のつながり（接点 → 価値 → 顧客情報）はサービス一覧ページ `/services/` で伝える。`css/home-2026.css` の `.cxh-concept` / `.cxh-pillar*` / `.cxh-mark` / `.cxh-flow*` の指定は未使用のまま残っている（戻す場合に備えて削除していない）。
- 2026-10-07（Issue #85）: サービス一覧（SERVICE、`#about`「2つの事業で、企業の成長を支えます。」）を `hidden` 属性で一時非表示（マークアップは `TEMP-HIDDEN SERVICE` コメント付きで残置）。Creative X / Sales X と内容が重なるため。後で「Contents X のまとめ」セクションとして作り直す予定。戻すときは `hidden` を外す（Sales X → SERVICE → TOPICS の `cxsb-join-*` はそのまま使える）。下層9ページの下部メニュー「サービス」は `./#about` から `/services/` に付け替えた。「制作スタジオ・IP開発（YOAKE STUDIO）」は現在トップに出ていない。
- 2026-10-07（Issue #85）: 会社紹介「Contents Xとは？ 法人の営業と売上づくりを支援する会社です。」（`#company-intro`）を削除。ABOUT の会社説明・Purpose（/about）・Company（/company）と重なるため。TOPICS → NEWS を共通背景で継ぎ目なくつなぐ。
- 白・無彩色を土台に、画像内の青とオレンジをSales X / Creative Xの識別色として使用。旧マゼンタテーマはトップとサービスページで使わない（`body[data-theme="neutral"]`）。その他のページのテーマは変更しない。
- 共通ヘッダーの「お問い合わせ」は通常時に淡いグレー地・濃紺文字、ホバーとキーボードフォーカス時に濃紺地・白文字で常に可読にする。言語切替の JP / EN ボタンは一時非表示（`css/style.css` の `.header-lang-switch`）とし、`i18n.js` / `nav.js` の言語切替ロジックと読込順は維持する。
- 共通ヘッダーの「ホーム」は単独リンクとし、ホバーやスマホメニューで「ニュース」「新作情報」の子メニューを表示しない。トップ内では `#hero` へ、その他のページでは `/` へ遷移する。「サービス」は `/services/` への親リンクとし、PCではホバー・キーボードフォーカスで Sales X / Creative X、その各項目のホバー・フォーカスで各サービスの二段メニューを表示。Sales X / Creative X 自体も紹介ページへ直接遷移できる。スマホのドロワーでは各事業のサービスリンクを常時表示する。「企業案内」の子メニューは維持する。
- 素材: `material/home-2026/{hero,sales,creative,about,contact}.jpg` と事業紹介用の `sales-safe.jpg` / `creative-safe.jpg`。ユーザー指定デザインを参照に生成した画像で、文字とロゴは画像へ焼き込まずHTMLで重ねる。事業紹介の元画像は被写体が素材の端で切れていたため、余白を設けて再生成した `*-safe.jpg` を表示に使用する。生成したオフィスはイメージ画像として扱う。
- モーション: `js/home-2026.js` と `css/home-2026.css`。ヒーロー文字の登場、スクロールでの段階的な表示、画像の左→右ワイプ（Sales X / Creative X の写真にも適用）、カード・ボタンのホバー移動。`prefers-reduced-motion: reduce` では瞬時表示。JS不在でも内容は表示する。ワイプ要素自身を幅0にクリップすると交差監視できないため、親コンテナを監視して子要素を表示する。
- サービスとその他の下層ページは `js/sitewide-motion.js` を共用する。見出し・カード群は下から24px/0.75秒で1回だけ登場し、主な写真は左から右へ1.05秒で表示する。会社概要・ニュース・コラムの初画面の見出しは0.8秒で軽く登場する。WP由来の一覧が後から表示された場合は、その時点で表示位置を判定する。`prefers-reduced-motion` とJS不在時も内容を表示する。サービス生成テンプレートにも同JSの読込を置く。
- ヒーロー右側の理念コピーは、都市画像の明暗の上でも読めるよう紺色の字に白い縁と淡い白い影を重ねる。事業紹介の中央ロゴは、青とオレンジが交差する文字なしのXマークをインラインSVGで表示する。独立したグリッド列に配置して左右の文言・CTAに重ならないようにし、SVGの viewBox に余白を取って両端を欠けずに描画する。写真は左カードを左寄せ、右カードを右寄せとして、余白付き素材の人物と作画の手を表示する。
- レスポンシブ: 768px以下でヒーローを縦構成、事業カードとサービス欄を1列にする。事業紹介は1100px以下で縦並びに切り替える。文字は `clamp()` で連続スケール。320/390/412/448/640/768/1024/1100/1101/1280/1440/1920pxの横溢れ・事業カード内の文字収まりをブラウザ確認。
- リンク: 総合ページは `/services/`。他ページの共通ナビにも独立した「サービス」を置く。ビズフォーム・ビズマンガ・ビズアニメ・ビズ採用は公開先へ直リンク。ビズビデオは一覧内の動画カード、準備中のビズAIO・ビズカルテは一覧内の該当カードへ。Sales X / Creative Xの紹介は `/services/sales-x/` と `/services/creative-x/` に向ける。
- 旧トップ用JS（`script.js`、`hero-new.js`、`hero-fx.js`、`cta.js` 等）はトップでは読み込まない。`hero-fx.js` は**どのページからも読み込まれていない**（HERO作業の完了後に削除予定。2026-10-13 時点）。`hero-new.js`・`js/data/works-detail.js` は 2026-10-29 に削除した（どのページからも読まれていないのに公開され、非公開にした作品のデータが残っていたため。必要なら git の履歴から戻す）。`wp-data-ready` は今は「ニュース描画完了」の合図で、`/works` は取得していない。トップを含む全ページで `i18n.js` → `nav.js` の読込順を維持。共通ヘッダーは1280px以下でドロワーに切り替え、文字拡大時のナビ重なりも避ける。トップは固定ヘッダーの下からヒーローを開始する。

### HERO（2026-10-10 刷新、Issue #108）

- 基準: 平澤さん支給のハンドオフ `ContentsX_TOP_HERO_Interactive_Handoff_20261010`（PC/SPの確定モック・素材・動画ID）。モック画像を貼らず、文字・ボタン・3カード・装飾をHTML/CSS/JSで組む。ヘッダーとABOUT以下は変えない。
- 構成（PC 1101px以上）: 白地＋薄い青/オレンジの幾何学背景（`material/home-2026/hero/hero-bg.webp`）。左に小見出し `BUSINESS × CREATIVE`・メインコピー「企業の価値を、売上に変える。」（明朝体、DESIGN-SYSTEM-2026.md のHERO例外）・説明「法人の営業と売上づくりを、仕組みとクリエイティブで支援します。」・ボタン「お問い合わせ」（`/contact`）「サービスを見る」（`/services/`）。右に傾いた3カード。装飾として `PEOPLE / IDEAS / SYSTEMS / GROWTH`・`CONTENTS X INC.`・`SCROLL`（読み上げ対象外）。HEROは画面の高さ−ヘッダー（最低520px）で、PC 1366×650〜1920×1080 でコピー・ボタン・3カードが1画面に収まり、カードはコピーに重ならない。
- 下段3カード（2026-10-14 平澤さん支給デザイン・Issue #154）: 暗いシネマティックな画像をカード全面に敷き、白い文字で上に小さな英字カテゴリ（`MANGA` / `ANIME` / `VIDEO`）、下にサービス名と短い説明、右下に丸い矢印（半透明の紺に細い白い輪、CSSで描画）を重ねる。読みやすさのため左と下を深い紺で暗くする。画像は `material/home-2026/creative-cards/{bizmanga,bizanime,bizvideo}.webp`（1448×1086、文字なし。ビズマンガはビズちゃん）。枠は細い半透明の白・角丸18px。3枚の高さはPCで画面の高さに合わせてそろえ、ノートPCでも1画面に収まる。選択中のカードは白い縁＋青い輪＋濃い影、矢印が白く塗られる。PCのhover/フォーカスで画像1.035倍・3px浮く・矢印が右へ（動きの軽減では止める）。カードは引き続き上のビューワーを切り替えるタブ（行き先リンク・タブ操作・WP連携は変更なし）。
- 1100px以下: コピー → ボタン → カードの箱（768px以下は縦長）。SPのカード配置はモックどおり、Creativeが右上・事業が左・仕組みが右下。
- 以前のHEROの「Sales X × Creative X」「2026.09」右下の一文「日本の中にある価値を、世の中に出し切る。」は削除。ボタン「まずは相談する」は「お問い合わせ」に変更。旧HEROの街の画像 `material/home-2026/hero.jpg` はトップでは使っていない（ファイルは残置）。
- カード2「事業を、次のステージへ。」→ `/about`、カード3「仕組みで、成果をつくる。」→ トップの `#sales-x` へなめらかにスクロール。**どちらも暫定**で、行き先は `index.html` の各 `<a>` の `href` を1か所変えるだけ。画像（`hero-card-business.webp` / `hero-card-system.webp`）は支給素材の焼き込みの角丸・白い縁を、文字にかからない範囲で切り落としたもの。画像内の文字は二重に重ねず、同じ文言を読み上げ用テキストとして持つ。右下の矢印でリンクと分かるようにする。
- カード1（Creative、2026-10-10 平澤さん指示で「動画の絵だけ」に変更・Issue #114）: カードにはYouTubeの表示（題名・アイコン・ロゴ・リンク）を一切出さず、3本の動画の絵（YouTubeのサムネイル画像）を横一列に並べる。左上には、他の2枚のカード画像の文字に合わせた見出し「クリエイティブで、ビジネスを動かす。」（明朝体、線と小さな `CREATIVE FOR BUSINESS`。SPは見出しだけ）を、白い文字で絵・動画の上に直接、左下に載せる（2026-10-11 平澤さん指示で白い板はやめた）。読みやすさのため下から薄く暗くする。動画自体の題字は上や中央に入ることが多いので、重ならないよう左下にした。開いてYouTubeを再生している間は消す（プレイヤーの上に重ねない）。並びは `index.html` の `[data-cxhv-slide]`（動画ID・題名）の順＝「どれが原宿？」`zKvRR8xT_zY` → 「High Speed Battle」`IAgFqlvSUfE` → 「ニャンポッシブル」`OYgeXiPByBg`（動画ID単位で、プレイリスト指定は使わない）。
  - ふだん: 横スクロール（スマホはスワイプ、PCはトラックパッド）で絵を切り替える。見えている絵はゆっくり少し拡大する。
  - PCの動くプレビュー（2026-10-10 平澤さん決定。bizmanga.contentsx.jp/bizanime の右側と同じ方式）: ページの読み込みが終わり、カードが見えていてHEROが場面のあいだ、見えている絵の裏でYouTubeを音なし・操作バーなし・ループで流す。再生が始まってから5秒間はYouTubeの題名などが出るので絵を上に残し、その後絵を薄くして動画を見せる。動画の部分は指し示せない・押せない（`pointer-events:none`）ので、マウスを乗せてもYouTubeの表示は戻らず、押すとカードが開く。10秒ごとに次の動画へ（マウスを乗せている間は進まない）。スマホ・タブレット・動きの軽減・タブ非表示・HEROを離れたときは絵のまま（スマホとタブレットは通信量と電池のため）。⚠️ YouTubeの規約が禁じる「公式の表示を隠す・押せなくする・上に重ねる」やり方で、YouTube側に埋め込みを止められる可能性があることを承知のうえで採用（法律ではなく利用規約の問題）。止められた場合もカードは絵のまま崩れない。
  - 絵を押すと開く: PCはカードがまっすぐになりながらHEROの右半分の中央へ動いて約1.5倍に広がり（右半分に収まらないときは縮める）、絵の外の左右に ‹ ›、右上に × を出す。タブレット・SPはカードの箱の中で横幅いっぱいに開き、‹ › × は絵の下（他の2枚は隠すが、箱の高さは保つのでページが跳ねない）。開くと操作バー付きのYouTubeプレイヤーで、プレビューの続きから音付きで再生する（ブラウザーが音付き再生を止めたときは音なしで始め、YouTubeの操作バーで音を出せる）。開いたまま横スクロール・‹ ›・←→キーで他の動画へ移ると、止まった位置の動画を再生する。×・Escで閉じると元の位置に戻り、フォーカスは絵へ戻る。他の2枚は薄く・少し小さくなり操作できない。
  - 共通: プレイヤーは常に1つ。HEROをスクロールで離れる（閉じる）・タブを隠す（一時停止）と止める。
- YouTube: 公式の IFrame Player API（`https://www.youtube.com/iframe_api`、PCは読み込み後、それ以外は開いたときに読み込む）で `youtube-nocookie.com` に埋め込む（`playsinline`・`rel=0`・`origin`・`enablejsapi`、操作バーあり）。読み込めないときは「動画を読み込めませんでした」と表示し、画面は崩れない。開いている間は、YouTube側のロゴ・題名・チャンネル名などの公式の表示とリンクが出る（開いているプレイヤーの上には何も重ねない）。ふだんのカード（PCのプレビュー含む）には出ない。`index.html` のCSPの `script-src` に `https://www.youtube.com` を追加した。
- 書体: メインコピーとCreativeカードの見出しだけ `Noto Serif JP` 500（Google Fonts の `text=` で使う文字だけ読み込む）。
- CSSは `css/home-hero.css`、JSは `js/home-hero.js`。検証は `python3 tests/test_hero.py --url <loopback preview> --artifacts <output>`（YouTube APIは記録用の代役に置換。19幅の文言・リンク・カードがHERO内・PCで1画面・コピーと重ならない・文字1.4倍、カードにYouTubeの表示が出ないこと、PCのプレビュー（音なし・操作バーなし・ループ・押せない・5秒後に絵が消える・10秒送り）、横スクロール、開いた位置（右半分の中央）と大きさ（1.5倍）・プレビューの続きから音付き再生・‹ ›と横スクロールで動画が移ること・自動送り停止・Esc・フォーカス、スクロールで閉じること、カード2/3の遷移、動きの軽減、YouTube不可、SP 375/390/430のタップ再生と「HEROの下端を見るまでフェードしない」こと、JS無効）。実際のYouTubeでの再生は手元のブラウザで確認（開く・音付き再生・横スクロールで切替・閉じる）。

### Hero直下のAboutと接続演出（Issue #59）

- `index.html` のHeroを `.cxha-transition` / `.cxha-stage` / `.cxha-hero-frame` で包む（Heroの中身は2026-10-10に刷新、上の「HERO」）。直後に `#home-about` を置く。既存のサービス用 `#about` と会社案内URL `/about` は維持する。
- ABOUTの内容・レイアウトは Issue #63 で刷新（下の「ABOUTの構成（Issue #63）」）。この節は Hero→ABOUT の接続演出の仕様。
- ユーザー提供のオフィス素材 `material/home-2026/about-office-pc.webp`（1672×941）は、#63 以降 Purpose / Company カードの画像（別crop）として使う。スマホ用の縦長版 `about-office-mobile.webp` は #63 で不要になり削除。オフィスはイメージ画像であり、実際の所在地写真として扱わない。遷移参考画像は実装素材には含めない。
- 専用の `css/hero-about.css` / `js/hero-about.js` を使用。ネイティブスクロールとstickyで、PCは画面高の1.0倍・SPは0.85倍（どちらも420〜900px）のスクロール区間に追従する。HEROが画面より高いとき（タブレット・SP）は、まずHEROを普通にスクロールさせ、HEROの下端が画面に入ってから固定と演出を始める（`--cxha-overflow`。カードを見る前に消えない）。
- 動き（2026-10-10、Issue #108でフェード接続に変更。以前の「Heroが縮んで写真に重なる」演出は、HEROが白地になり意味がなくなったため廃止）: Heroの文字が区間の4〜30%で薄くなり、3カードは4〜62%でわずかに縮み（100→88%）上へ下がりながら22〜60%で消える。HERO全体（背景を含む）は32〜64%で溶け、下からABOUTが現れる（見出し34〜60%→本文→写真46〜76%で96→100%に広がる→Purpose / Company→事業カード）。ABOUTは演出中も画面いっぱいの高さを持つので、途中で空白は出ない。PC/SPの値は `js/hero-about.js` の `PC` / `SP`。HEROが場面でなくなった（区間の20%を超えた）ことを `cxha:hero` イベントで知らせ、HEROの動画を止める。
- 描画は受動的なscroll監視とrequestAnimationFrameでまとめる。wheel/touchのキャンセルやスクロールロックを行わない。逆スクロールでも同じ量に戻り、サイズ変更・文字拡大・フォント読込・i18n切替・履歴復帰時には実寸から再計算する。非表示のAboutがHeroのCTAを遮らないよう初期はpointer-eventsを無効にする。薄くなったHeroのリンクはinertでクリック・フォーカスを抑え、完了後にaria-hiddenにする。
- `#home-about` への直接アクセスは演出完了位置へ、既存ナビの `#hero` は縮小前の先頭へ戻す。通常のアンカー操作・戻る/進むで表示状態が食い違わないようにする。
- JS無効時と `prefers-reduced-motion: reduce` ではHero→Aboutを通常フローで全表示し、sticky・縮小・フェードを使わない。設定の実行中変更にも追従する。i18n.js → nav.jsの既存読込順は維持する。

### ABOUT / SERVICE / NEWS の共通背景（Issue #61）

- 対象は `#home-about`（ABOUT）、`#about`（サービス一覧＝SERVICE）、`#news`（NEWS）の3つ。各セクションに `.cxsb-section` を付け、間のコンセプト・Sales X / Creative X・流れ・会社紹介は従来どおり白系の背景のまま残す。
- 背景はハンドオフ（ContentsX_About_Handoff）の `02_common_bg_pc` / `03_common_bg_sp`（= #59 のオフィス画像）に、ぼかし（PC 15px・SP 16px相当）と明るさ調整を焼き込んだもの。`material/home-2026/section-bg-pc.webp`（1672×941）と `section-bg-mobile.webp`（941×1672）を、768px以下または縦長画面（縦横比3:4以下）で切り替える。CSSの `filter: blur` はスクロール中の描画負荷が高いため使わない。実在のオフィス写真としては扱わない。
- 各セクション先頭の `.cxsb-backdrop` を `position:fixed` で画面全体に置き、セクション側の `clip-path:inset(0)` で切り抜く。背景は動かず、カード・見出しだけが上を流れる（`background-attachment:fixed` は iOS で効かないため使わない）。白いベールで濃紺文字の可読性を保ち、上下端は白へフェードして隣の白いセクションへつなぐ。
- 各セクション上部に大きく薄い英字 `.cxsb-label`（ABOUT / SERVICE / NEWS、`aria-hidden`・`data-i18n-skip`・`text-size-adjust:100%`）。ABOUTは #59 の巨大文字 `.cxha-wordmark` の文言を「CONTENTS X」から「ABOUT」へ変更して流用し、表示タイミングは #59 のスクロール連動のまま。
- 動き: SERVICE / NEWS の英字は左から軽くスライドしてフェード、サービス列とニュースのカードは下から＋scale .97→1 で登場、ニュースの行は0.08秒ずつ時間差。いずれも `home-2026.js` の既存 `data-cxh-reveal` を使い、新しいJSは追加しない。ニュースの行はhover可能な端末だけ右へ4px動かす。NEWSの一覧は白いカードにし、本文幅はサービスと同じ `min(100% - 80px, 1250px)`（スマホは `min(100% - 32px, 560px)`）。
- スクロールスナップ: 1025px以上かつマウス操作の端末だけ `html` に `scroll-snap-type:y proximity`。SERVICE / NEWS は先頭（固定ヘッダー64px下）、ABOUTは #59 の演出完了位置に置いた `.cxsb-about-snap` に吸着する。背の高いセクションの途中では引き戻さない。1024px以下・タッチ端末ではスナップなし。既存の `.cxh-home main [id]` の80pxずらしより後に読み込み、同じ詳細度で64pxに上書きしている。
- CSSは `css/home-sections.css`（`hero-about.css` の後に読込）。検証は `python3 tests/test_section_backdrop.py --url <loopback preview> --artifacts <output>`（16幅、背景の固定、画像切替、隣セクションへの漏れ、文字1.4倍、PCのみのスナップ、hover、動き軽減、JS無効）。

### ABOUTの構成（Issue #63）

- 基準: ハンドオフ `ContentsX_About_Handoff/00_reference_about.png`。画面を1枚画像にせず、背景・画像・文字・カードをHTML/CSSで分ける。ヘッダーは共通ヘッダーのまま。
- PC（1101px以上）: 左に見出し「コンテンツで、企業の可能性をひらく。」と本文、中央に大きなメインビジュアル `.cxha-office`（2026-10-09 から社員の集合写真 `material/home-2026/about-team-photo.webp`、2000×1500。PCは2:1の枠で後列の頭と前列の顔が入る位置〈`object-position: 50% 35%`〉、768px以下は4:3で全体を表示。旧画像 `about-main-visual.webp` は戻す場合に備えて残置）、右に Purpose 導線（「コンテンツの力で、社会にもっといい未来を。」OUR PURPOSE → `/about`）と Company 導線（「私たちについて」COMPANY → `/company`）。下段は半透明の白い帯に「価値を生み出す、2つの力。」の導入文と、Sales X（→ `/services/sales-x/`）/ Creative X（→ `/services/creative-x/`）の2カード。Contents Xカードは置かない。カードのXは Sales X が青、Creative X がオレンジ。
- Purpose / Company カードは新しい画像を増やさず、`about-office-pc.webp` を `background-size` / `background-position` で別の範囲に切り出し、Purpose は白、Company は濃紺のグラデーションを重ねる。
- 769〜1100px: 見出し・本文を上段の全幅、メインビジュアルとPurpose / Companyを2列、導入文を全幅にして事業カードを2列。
- 768px以下: ABOUT → 見出し/本文 → メインビジュアル（4:3）→ Purpose → Company → Sales X → Creative X の1カラム。導入文はスマホでは出さない。横移動や強いstickyは使わない（#59の縮小演出は中央線のまま縦方向）。
- hover（hover可能な端末のみ・0.2秒）: Purpose / Companyの画像を1.02倍、矢印を3px右へ、重ねた色をわずかに薄く。事業カードは背景を白に、影を強め、矢印を3px右へ。キーボードフォーカスは青い枠。
- 高さ（2026-10-04、平澤さんの1470×800表示で見切れ・白い帯の指摘）: スクロール演出中のABOUTは少なくとも1画面分（画面高−ヘッダー、JSが `--cxha-about-min` に設定）の高さを持ち、中身を縦中央に置く。以前はHeroの高さに合わせた舞台の下に白い帯が出ていた。PC（1101px以上）は余白・Purpose/Companyの高さ・事業カードを `svh` でも縮め、1366×650〜1920×1080でABOUT全体が1画面に収まる。
- 登場は #59 のスクロール連動の中で、見出し→メインビジュアル→導線カード→事業カードの順に軽くfade-up。`prefers-reduced-motion: reduce` とJS無効時は全表示し、hoverの変化も止める。
- CSSは `css/hero-about.css`、背景とスナップは `css/home-sections.css`（#61）。検証は `tests/test_hero_about.py`（#59の演出・Hero比較）と `tests/test_section_backdrop.py`（リンク先4件、事業カード2枚、SPの並び順、hover）。

### Creative X セクション（Issue #65、ビューワー化 Issue #97、動画の横スクロール化 Issue #102、下段カード刷新 Issue #154）

- 位置: ABOUT（`.cxha-transition`）の直後、`#creative-x`。デザインは 2026-10-04 改訂版を土台に、2026-10-08（Issue #97）で右上の PICK UP を「メインビューワー」に置き換えた。画面を1枚画像にせずHTML/CSS/JSで組む。
- 背景: ABOUTの共通背景（`.cxsb-section`）をそのまま継続。ABOUTに `.cxsb-join-next`、Creative Xに `.cxsb-join-prev` を付け、境目の白いフェードを出さず1枚の景色として続ける。上部に薄い大きな `CREATIVE X`。PCのスナップ対象。
- しくみ: 下の3カード（ビズマンガ / ビズアニメ / ビズビデオ）がタブで、上のメインビューワー1枠の中身を切り替える。初期表示はビズアニメ。HTML上のカードは各サービスへのリンク（ビズ書庫 / ビズアニメ公式 / `/services/#bizvideo`）で、JSがタブに変える。JSが動けば普通のクリックではページ移動・ポップアップはせず、Ctrl/⌘クリックは各サービスを新しいタブで開ける。切替は約200msのフェード（動き軽減時は即時）、切替時は再生中の動画を止め、マンガは1ページ目・拡大なしに戻す。タブはスペースキー・矢印キー・Home/End でも操作できる（`role="tab"` / `tabpanel` はJSが付ける）。
- PC（1101px以上）: 上段は左に「Creative X ——」・見出し「想いを、伝わるカタチに。」・説明・青いボタン「Creative X について →」（`/services/creative-x/`）、右にメインビューワー（濃紺の枠）。下段は左に「OUR WORKS ——」「作品で見る Creative X」・説明、右に3カード（画像・色付きのサービス名・一文・丸い矢印。選択中は枠線とサービス色の丸）。最下部に区切り線と「IDEAS INTO IMPACT」。ビューワーの高さはサービスを切り替えても変わらない。
- 1100px以下: 1列で「見出し・説明・ボタン → OUR WORKS → 3カード（横3列）→ ビューワー」。カードをビューワーの上に置き、ビューワーの高さが変わっても押したカードが動かないようにする。768px以下はカードを縦1列の横長（2:1）にし、592px以下はビューワーを画面の端から端まで広げる。
- ビズマンガ（`js/cx-manga-reader.js`）: ページ内で読めるマンガビューワー。BizManga の読み方の規則を写している（BizManga のJSは読み込まず、BizManga 側は変更しない）。右綴じで、PC（769px以上）は見開き [1,2],[3,4]… の若い番号が右、最終ページが奇数なら左に `/material/manga/thanks_v02.webp`。768px以下は1ページずつ。`view_type` が `vertical_only` / `vertical`、または1ページ目の縦横比が1.8超なら縦スクロール表示。1ページ目が読み込めないときは BizManga と同じく「縦読みではない」として表示を続ける。判定は BizManga の `bm-view-type.js` を読み込まずに写している（別サイトのため）ので、BizManga 側の判定を変えたら `js/cx-manga-reader.js` も合わせる。「次へ」は左・「前へ」は右、←キー＝次・→キー＝前、スワイプは左へ＝次。ページの上をクリック（スマホはタップ）すると、左半分＝次・右半分＝前（ボタンと同じ向き。2026-10-14 平澤さん指示。拡大中と縦読みでは無効）。ページ番号表示。「拡大」を押すと、ビズ書庫の読み方と同じく漫画が画面全体に広がる（ページ全体を覆う濃紺の画面。後ろのページはスクロールしない。めくり方は同じ。「閉じる」・Escで元の位置に戻る。2026-10-14 平澤さん指示で、枠の中で2倍にする以前の拡大から変更）。ページは切り取らない（`object-fit: contain`）。PCではページを枠の高さいっぱいに使い、ボタン類は左右の余白に重ねる。
- ビズアニメ / ビズビデオ（`js/cx-video-player.js`）: 共通の動画プレイヤー。各3本を横一列に並べ、横スクロール（SPは指でスワイプ、PCはトラックパッド・左右端の ‹ › ボタン・←→キー）で1本ずつ切り替える（2026-10-09 平澤さん指示で下のサムネイル列は廃止）。動画は枠の横幅いっぱいに16:9で表示し、上部の点で何本目かを示す（再生中は隠す）。最初はポスター・タイトル・説明と再生ボタンだけで、押すとその場で埋め込みを作って再生（自動再生しない）。別の動画へスクロール・別サービスを選ぶと埋め込みを外して止める。読み込み中・再生できないときは文字で知らせる。高画質サムネイル（maxresdefault）が無い動画は YouTube の灰色の代わり画像になるため、標準サイズ（hqdefault）に切り替える。
- データ（`js/home-creative-x.js`、`WP_CONFIG.apiBase` 経由）:
  - 動画: `GET /bizanime-videos` の `viewer`（WPプラグイン「ビズアニメ・ビズビデオ動画」＞「CREATIVE X ビューワー動画」。種別・タイトル・説明・URL・ポスター・表示ON/OFF・並び順）。種別ごとに再生できるものを先頭から3本。ビューワー動画が未登録の種別は、ビズアニメは `playlists` のビズアニメ分 → 既存の `cases`（単体動画）、ビズビデオは `playlists` のビズビデオ分で代用する。
  - マンガ: `GET /works?site=contentsx`（「ContentsX新作情報に表示」＝掲載可否、`cx_sort_order`＝表示順）のうち、ページ画像（`gallery`）を持つ先頭の作品。
  - 埋め込みURLはフロントで検証済みIDから組み立てる（YouTube は `youtube-nocookie.com/embed/{id}`、プレイリストは `embed/videoseries?list=`、Google ドライブは `drive.google.com/file/d/{id}/preview`、mp4 は `<video>`）。APIの `embed` は使わない。画像は `cms.contentsx.jp` / `contentsx.jp` / `i.ytimg.com` の https とサイト内パスのみ。文字は textContent で入れ、HTMLとして解釈しない。
- 大きさ: ビューワー内の高さはビューワーの横幅から決める（コンテナ単位。`--cxcx-view-h` = 横幅×9/16。上限はPCが画面の高さ−340px、タブレット・SPが画面の高さ−140px）。動画は横幅いっぱい、マンガの枠も同じ高さなので、切り替えても枠の高さは変わらない。SPのマンガは縦長（横幅×1.25、画面の高さの70%まで）。高さ860px以下のPCは上の余白とカード画像を低くする。ノートPC（1366×650〜1920×1080）ではカードまで1画面に収まり、高さ800px以上なら動画は枠の横幅いっぱい。それより低い画面では高さの上限で動画が少し小さくなる（YouTube側で左右に黒帯）。
- 状態: データ取得中は「読み込み中…」。取得に失敗したら「動画（漫画）を読み込めませんでした」、データが無ければ「準備中です」と出し、どちらも各サービスへのリンクを添える（動画とマンガは別々に判定）。JS無効・WP設定が無効のときは `index.html` の静的な表示（I eye のポスターとビズアニメへのリンク、3カードは各サービスへのリンク）が残る。
- CSSは `css/home-creative-x.css`、検証は `python3 tests/test_creative_x.py --url <loopback preview> --artifacts <output>`（WP応答と画像をフィクスチャに置換。19幅の並び・横はみ出し・文字1.4倍、タブ操作・キーボード、動画の非自動再生・停止・埋め込みURL・XSS・不正URL、マンガの見開き順・サンクスページ・キー操作・拡大・リセット・SPスワイプ・縦読み、切替でビューワーの高さが変わらない、動画の横スクロール・‹ ›・←→とスクロールで前の動画が止まること、ノートPC8サイズでカードまで1画面・高さ800px以上は動画が横幅いっぱい、スナップ、ビューワー動画未登録時、取得中・取得失敗時、動き軽減、JS無効）。
- WP側は別リポジトリ `contentsx-wp-plugin` の `contentsx-cms/bizanime-videos.php`（プレイリストは 2026-10-03 本番反映。ビューワー動画の欄・REST `viewer` は Issue #97 で追加）。

### Sales X セクション（Issue #67、画像＋ホバー型カード Issue #104）

- 位置: Creative X の直後、`#sales-x`。共通背景を継続し、Creative X に `.cxsb-join-next`、Sales X に `.cxsb-join-prev` を付けて継ぎ目を出さない。上部に薄い大きな `SALES X`。PCのスナップ対象。
- 左: 小見出し「Sales X ——」・見出し「新しい接点を、売上につなげる。」・説明（3行に区切る。768px以下は改行を外して自然に折り返す）・「Sales Xについて見る →」（`/services/sales-x/`）。
- 右: 4サービスを2列×2行（769〜1100px は説明が上・カードは2×2、768px以下は縦1列）。カードは同じ大きさ・角丸16px・同じ影で、カード全体がリンク。
- カード（2026-10-09 平澤さん指定の「B案：画像＋ホバー型」）: 上に画像（主役）、画像の下端にサービス色の線、その下にラベル（サービス色の小さな札）・サービス名・短い説明（2行。改行は外し、文節単位で折り返す）。
  - PCのホバー／キーボードのフォーカス: 画像の上に濃紺のオーバーレイを重ね、補足説明と「詳しく見る →」を出す。カードは3px浮き、画像は1.04倍、矢印は4px右。
  - ホバーできない端末（スマホ・タブレットのタッチ）と768px以下: オーバーレイは出さず、短い説明の下に「詳しく見る →」を常に出す。
- 画像（`material/home-2026/`、1672×941・16:9、平澤さん支給）: 768px以下とタブレットは16:9のまま全体を見せる。PCは画面の高さに合わせて高さを決め（`clamp(100px, 50svh − 214px, 300px)`）、16:9より横長になる分は画像ごとの `object-position` で主題を残す。

| カード | ラベル | 色（線・文字） | 遷移先 | 画像 |
|---|---|---|---|---|
| ビズフォーム | 新規開拓代行 | 青 `#1265e8` / `#0d4fb8` | https://bizform.contentsx.jp/ | `sales-x-bizform.webp`（企業調査→個別文面→送信の青い画面） |
| ビズ採用 | 採用支援 | ピンク `#ec2d87` / `#c0186b` | https://ichioshi.contentsx.jp/ | `sales-x-bizrecruit-v2.webp`（採用広報・動画・SNSのコラージュ） |
| ビズAIO | AI検索最適化 | 紫〜青のグラデーション / `#5b30d6` | `/services/#bizaio` | `sales-x-bizaio.webp`（AI検索の画面と結果） |
| ビズカルテ | 次世代AI CRM | オレンジ `#f26a1b` / `#b4470b` | `/services/#bizkarte` | `sales-x-bizkarte-v2.webp`（オレンジ系のCRMダッシュボード） |

- 文言（短い説明／補足）: ビズフォーム「企業ごとに調べて、書いて、送る。新規開拓の実務を一気通貫で代行します。」／「企業調査・個別文面の作成から、問い合わせフォーム送信・レポートまで対応。新規開拓を、もっと軽く。」、ビズ採用「SNS・コンテンツ制作・広告で、「知ってもらう → 好きになってもらう → 応募される」流れをつくります。」／「採用漫画・動画・インタビュー・広告運用を組み合わせ、会社の魅力が伝わる採用導線を設計します。」、ビズAIO「ChatGPT・Gemini・PerplexityなどのAI検索で、見つかる・選ばれる状態をつくります。」／「AI時代に最適化した情報設計・コンテンツ整備で、検索流入と商談機会の最大化を支援します。」、ビズカルテ「顧客・商談・活動をひとつに管理。AIが次に連絡すべき相手やアクションを提案します。」／「営業活動を可視化・整理し、顧客対応から成果創出までをAX化するCRMです。」。英語版は `data-en`。
- 高さ: PC（1101px以上）は1366×650〜1920×1080で4枚が1画面に収まる。
- 以前のトップ用画像 `sales-x-bizrecruit.webp` / `sales-x-bizkarte.webp` はどこからも参照されなくなったが、戻す場合に備えて残置（BizManga からの参照もなし）。暫定で使っていた `bizform-research-v2.webp` / `bizaio-search-v2.webp` はサービス一覧・Sales X紹介ページで引き続き使用。
- CSSは `css/home-sales-x.css`、検証は `python3 tests/test_sales_x.py --url <loopback preview> --artifacts <output>`（17幅の並び・横はみ出し・文字1.4倍、ラベル・画像・リンク、画像が文字より上、SPは16:9、ホバーとキーボードのフォーカスで重ねる表示、タッチ端末では「詳しく見る」を常時表示、カード全体がリンク、スナップ、動き軽減、JS無効）。共通背景のテスト `tests/test_section_backdrop.py` がノートPC6サイズで1画面に収まることを見る。

### TOPICS セクション（Issue #76）

- 目的: 正式な NEWS とは別に、動画・代表メッセージ・プレスリリース・コラム・事例などを横断して載せる「読む・選ぶ」場所。上のセクションほど演出せず、静かで見やすくする（参考: レバレジーズ「INTERVIEW by meLev」）。
- 位置: SERVICE（サービス一覧 `#about`）の直後、`#topics`。SERVICE に `.cxsb-join-next`、TOPICS に `.cxsb-join-prev` を付け、共通背景を継ぎ目なく続ける。上部に薄い大きな `TOPICS`。PCのスナップ対象。NEWS（`#news`）はこの後ろ（間に会社紹介）。
- 見出し: 「TOPICS ——」「Contents X を、もっと知る。」。PCは右上に前後の丸い矢印（1枚ずつ移動。端・全件が収まるときは押せない表示）。SP（768px以下）は矢印なしの横スワイプで、次のカードが少し見える（1枚82%）。
- カード: サムネイル（16:9）/ 種別（英大文字、MESSAGE・VIDEO・PRESS・COLUMN・CASE など自由）/ 日付 / タイトル（2行まで）/ タグ（#付き）。PCは3枚横並び、4枚目以降は横に並び矢印で送る。hover は画像1.02倍・矢印3px右・タイトルを青に。カード全体がリンクで、サイト内は同じタブ（→）、外部（YouTube・PR TIMES等）は新しいタブ（↗、読み上げに「外部サイトが開きます」）。
- データ（`js/home-topics.js`）: `GET /contentsx/v1/topics`（WPプラグイン「Contents X ＞ TOPICS」、`contentsx-cms/contentsx-topics.php`）。表示ONのみ、PICK UP を先頭に、あとは管理画面の並び順。リンクは `/` 始まりのサイト内パスか http(s)、画像は `cms.contentsx.jp` / `contentsx.jp` / `i.ytimg.com` の https かサイト内パスのみ、日付は実在する日付のみ表示。文字は textContent。
- 初期3件（`index.html` に同じ内容を JS無効・取得失敗時の表示として記載）: MESSAGE 2026-09-29「代表メッセージ｜全国で見てきたあの光景を、一社ずつ変えていきたい。」→ `/message` / VIDEO 2026-08-11 マクニカ対談（YouTube `w_O3iaQKduQ`）/ PRESS 2026-08-31 KIRINZ との共同創業（PR TIMES）。サムネイルは `material/home-2026/topics/topics-message-kuromiya.webp`（代表写真を16:9に切り出し）、YouTube の自動サムネイル、`topics-press-kirinz.webp`（リリース画像の中段のコマを切り出し）。
- 採用ページ（`/recruit`）でも同じ部品を使う（SPEC §9.6）。フォールバックの3件を変えたら recruit.html も揃える。
- TOPICSはNEWSと別のセクション。代表メッセージ本文は独立ページ `/message` へ接続（§14参照）。
- WPプラグインのアップロード前確認（2026-10-07）: TOPICSの `contentsx-topics.php` と `contentsx-cms.php` の読み込み行はプラグインのmainに取り込み済み。お名前.comへ `contentsx-cms.php` をアップロードする前に、必ずプラグイン側の最新mainを取り込み、TOPICSの読み込み行と参照先ファイルがそろっていることを確認する。古い作業ブランチのファイルで上書きしない。アップロード対象PHPは `php -l` で構文チェックする。
- 項目の追加・変更（2026-10-08 追記）: WP管理画面「Contents X ＞ TOPICS」で行う。REST の `POST /contentsx/v1/topics`（要 edit_posts）でもできるが、**一覧を丸ごと置き換える**仕様で、公開の GET は表示ONの項目しか返さない。GET の結果に足して POST すると、管理画面で表示OFFにしている項目が消えるので、表示OFFの項目が無いことを確かめてから使う。VIDEO の画像はYouTubeのURLから自動で補われるので、保存し直すときは空のまま送る。
- 反映の遅れ: `cms.contentsx.jp` の nginx が API応答を最大10分キャッシュする（`s-maxage=600`）。`Vary: Origin` のため、ブラウザからの取得（Origin付き）は curl 等とは別のキャッシュになり、curl で新しい値が見えてもトップの表示は最大10分古いまま。確認は時間を置くか、`Origin: https://contentsx.jp` を付けた取得で行う。
- CSSは `css/home-topics.css`、検証は `python3 tests/test_topics.py --url <loopback preview> --artifacts <output>`（WP応答をフィクスチャに置換。15幅、位置と背景、カードの項目、リンク、hover、矢印、不正データ、取得失敗時、ノートPCで1画面、スナップ、動き軽減、JS無効）。

### NEWS セクション（2026-10-07 ブラッシュアップ・Issue #85）

- 方針: 情報を確認する場所なので、演出は控えて読みやすさ・一覧性を優先。目指す形は「巨大な薄い NEWS ＋ 右上の一覧リンク ＋ シンプルな4件の一覧」。共通背景は TOPICS から継ぎ目なく続く（`.cxsb-join-prev`）。
- 見出し: 巨大な薄い `NEWS`（`.cxsb-label`）は残し、黒文字の「News」は表示しない（読み上げ用に `#cxnw-title`「ニュース」を視覚的に隠して残す）。「一覧を見る →」（`/news`、常に表示）は一覧の右上。
- 一覧: 最新4件（`wp-api.js` の `NEWS_HOME_LIMIT = 4`）。白い大枠は枠線・影を弱めた半透明。行は「サムネイル / カテゴリ / 日付 / タイトル / 矢印」の順で、行全体が1つのリンク（`a.cxnw-row`）。全行同じ高さ（`grid-auto-rows:1fr`、区切り線は行の内側に描く）、サムネイルは全行同じ 8:5 の枠に `contain`（WPの crop 指定がある画像は cover＋中心位置）。タイトルは濃紺・太字で最も強く、日付はやや薄く、カテゴリは小さな枠付きラベル。PC は横一列（2行まで）、1024px以下はサムネイル右に「カテゴリ・日付」→タイトル、768px以下はサムネイル88px・タイトル3行まで・行の高さ96px以上。
- 動き: 一覧全体が画面に入ったときに軽く fade-up（`data-cxh-reveal`）するだけ。hover は行の背景がごく薄く変わり、矢印が4px右、サムネイル1.02倍。行ごとの時間差アニメーションと行の横移動は廃止。
- 描画: `js/wp-api.js` の `loadNews()` が、トップ（`body` に `data-page-news` が無いとき）だけ上の行を描く。`/news` ページは従来の描画のまま。WP の `url` は http(s) か `/` 始まりだけリンクにし、それ以外は詳細ページ `/news-detail?id=` へ。`index.html` の4件は JS無効・取得失敗時の表示（2026-10-07 時点の最新4件）。
- CSS は `css/home-news.css`（旧 NEWS 指定は `home-sections.css` から削除）。検証は `python3 tests/test_news.py --url <拡張子なしURL対応のプレビュー> --artifacts <output>`（16幅、4行同じ高さ・同じサムネイル、表示順、文字の強弱、右上リンク、SPの並び、hover、不正データ、取得失敗・JS無効、/news が従来どおり）。

### 大きな半透明のセクション名を画面に固定（Issue #89 / タイミング改善 #93）

- ABOUT / CREATIVE X / SALES X / TOPICS / NEWS の大きな半透明文字を、背景の景色と同じく画面に固定する（ヘッダー下 `64px + clamp(10px,1.6vw,26px)`、480px以下は 56px 基準）。
- 仕組み（#93）: `js/home-section-labels.js` が各セクションの名前を**すべての背景（`.cxsb-backdrop`）の中に** `.cxsb-names > .cxsb-name` として描き、`html.cxsb-fixed-labels` を付けて元の `.cxsb-label` を隠す。採用ページでも共用（#135）: 共通背景の上に並ぶセクションは `data-cxsb-name="名前"` を付け、`[data-cxsb-names-host-scope]` の中の `[data-cxsb-names-host]`（採用ページの `.rc-stage__bg`）に描く。この属性が無いページ（トップ）の動きは変わらない。どの背景にも同じ名前が同じ位置に出るので、セクションの境目をまたいでも文字が切れない。
- 切り替え: 画面の**上から40%の線**を含むセクションの名前を出す（2026-10-08 平澤さん「もっと早く出したい・少し戻っても残してほしい」）。下にスクロールすると次のセクションの上端がこの線を越えた時点で切り替わり、少し上に戻っても上端がこの線より下がるまでは今の名前が残る。切り替えは0.2秒のフェード。ABOUT は Hero → ABOUT の演出（`--cxha-wordmark`）に合わせて現れる。
- JS無効時は元の `.cxsb-label` がセクションと一緒に流れる。動き軽減時はフェードなし。CSS は `css/home-sections.css`。
- 検証: `tests/test_section_backdrop.py`（PC・スマホで、各セクションの名前が1つ・スクロールしても同じ位置・上端が画面の30%まで戻っても残る・50%まで戻ると前の名前に戻る）。

### 3.0 サービスページ生成（Issue #20）

- `data/services.json`、`data/service-groups.json`、`data/design-tokens.json` を正本とし、`tools/build-services.py` が `/services/`、事業群2ページ、旧個別URLの転送ページ7件、共通デザイントークンCSS、サイトマップを生成する。トークンCSS `css/web-system-tokens.css` の色とフォントは、サイト共通の正本 `css/brand-system-2026.css` の変数の別名として出力する（例 `--cxs-ink: var(--cx-color-ink, #07143b)`。JSONの値は予備で、正本と同じ値にそろえる。2026-10-10、Issue #107）。サービスページは正本をトークンCSSより先に読み込む。`href` は旧URL、`destination` は現在の遷移先で、生成ページは後者を使う。個別詳細ページは公開しない。サイトマップには一覧と事業群2ページだけを載せる。トップは独立デザインで生成マーカーを持たないため、ビルドはトップを上書きしない。
- 一覧の最下部はページ専用CTA「LET'S TALK」（`.cxsd-contact`）1つだけ。「まずは相談する」（`/contact`）と「資料ダウンロード」（`.js-dl-trigger`、`js/dl-modal.js` の案内モーダル。記入済みならPDFを直接ダウンロード）を並べる（2026-10-10、Issue #107。以前は共通CTA `cta.js` も続けて出て2つ重なっていた）。生成ページは `cta.js` を読み込まない。
- 一覧は `tools/templates/service-list.html.tpl` と `css/service-directory-2026.css` で生成する。冒頭の重複ヒーローと事業カードを置かず、Creative X の写真・紹介から始める。Creative X → Sales Xの順に、画像左・濃紺の説明右の事業紹介、1文の概要を添えたサービスカードを置く。事業紹介の写真は装飾画像とし、各事業ページへの遷移は説明側のCTA1個に絞る。最初のCreative X見出しを一覧のH1とする。領域間の帯は見出しで、クリックできるリンクにはしない。PCのホバー/キーボードフォーカスで補足文を表示し、タッチ端末は常時見える1文を残す。公式サイトがある静止画カードは画像・見出し・CTAを同じ公開先へ向ける。動画カードのポスターはページ内再生で、ビズアニメの見出しとCTAのみ公式サイトへ進む。
- 生成するサービスページのヘッダー・フッターは `services/index.html` を正本とする。トップのヘッダー構成が変わっても、生成時はトップから抽出しない。全ページのサービス導線は実在するURLへ向ける。フッターは全ページ共通（§7.5）。
- サービスカードはPCのhover/focusで補足文を示し、スマホでは1文の概要を常時表示する。JSなしでも概要は読める。ビズAIO・ビズカルテは準備中、公開済みサービスは公式サイトへ誘導し、ビズアニメ・ビズビデオの実作品動画はユーザー操作後にページ内で再生する。
- サービス生成は `python3 tools/build-services.py --check` と `python3 -m unittest discover -s tests -p test_build_services.py` で確認する。Pagesワークフローも同じ生成処理とテストを実行する。
- Sales X・Creative Xの紹介ページは `tools/templates/service-group-*.html.tpl` と `css/service-landing-2026.css` から生成する。白・濃紺を土台に、Sales Xの青 `#005bfa` とCreative Xのオレンジ `#fa4d12` を使う。ヒーロー・相談CTAの画像は背景と境界をつなげ、スマホでは本文の下に置く。Creative Xのヒーローは `creative-hero-v2.webp`、Sales Xは `sales-hero-v2.webp`。Creative Xの「夜明けスタジオ」は表示しない。Sales Xのビズフォーム画像は実際の業務内容に沿った `bizform-research-v2.webp` を使う。
- 紹介ページのサービス一覧カード（`render_landing_card`、#141）は共通部品 `.cx-feature-card cx-feature-card--wide`（Creative X は `--creative`。Creative X 紹介ページは2026-11から下の「03 CREATIVE SOLUTION」の作品カードに置き換え、一覧カードは Sales X だけ）。画像の左上に番号と欧文ラベル（`CARD_LABELS`）、見出し・説明・タグ2つ・下のボタン（公式サイトを見る／公開予定／制作について相談）。カード全体はリンクにせず（動画の再生ボタンがあるため）、丸い矢印は置かない。`.cxg-service-card` は `js/service-media.js` の再生中クラスと準備中パネルの目印として残す（見た目の指定は無い）。スマホは縦積み。
- ビズマンガは共用WordPressの「正義の値段」表紙、ビズアニメとビズビデオは公式の実作品ポスターを使用する。後2者はポスターを押すと `js/service-media.js` がローカルのH.264/AAC MP4をページ内で音声付き再生する。YouTubeのiframe・投稿者表示・外部リンクは置かない。再生/一時停止・音量・字幕・進捗バー・拡大操作はホバー/フォーカス時に表示し、タッチ端末では常時表示する。`media-src 'self'` をサービスページのCSPに指定する。
- ビズAIO・ビズカルテは画像エリアのホバー/フォーカス時に紺・青の「乞うご期待」を表示し、詳細リンクを出さない。ビズ採用は公式サービスページのヒーロー画像を使い、`https://ichioshi.contentsx.jp/service.html` に遷移する。ビズマンガは `https://bizmanga.contentsx.jp/`、ビズアニメは `https://bizmanga.contentsx.jp/bizanime` に直リンクする。ビズビデオは一覧内で再生し、制作相談へ誘導する。両事業ページは独自の相談CTAを持つため共通CTAは重複表示しない。
- **Creative X 紹介ページの構成と共通背景（2026-11 統合、ローカル実装・未公開）**: 上から HERO（番号なし）→ WORKS（番号なし）→ 01 CREATIVE SOLUTION → 02 PRODUCTION FLOW → 03 FAQ / CONTACT → 共通フッター。旧 01 ABOUT と 02 WHY CREATIVE X は削除。旧 03 CONTACT（白地・写真）は 03 FAQ / CONTACT の CONTACT パネルに置き換え。番号を変えただけで、残したセクションの id・リンク先（`#works`・`#creative-solution`・`#cxg-flow`・`#cxg-contact`、HERO の「制作事例を見る」）は変えていない。
  - 共通背景: HERO・WORKS・01・02・03 は1つの舞台 `.cxg-stage`（`data-cxg-stage`）に入り、背景は HERO のショーリール1枚（`.cxg-reel`：ポスター＋音なしループ動画。動画の取得・再生は1回）。`js/service-creative-hero.js` が舞台に `.is-live` を付け、背景を画面に固定して舞台で切り抜く（トップの `.cxsb-backdrop` と同じ方法、iOS 可）。HERO の間はくっきり、HERO を過ぎるにつれてぼける（PC 22px・768px以下 14px、ほんの少し拡大）。ぼかしの後は**舞台の終わりまで映像を残す**（以前の「WORKS の途中で濃紺へ消す」はやめた）。色と光を残すため、ぼかしと同じ1つの filter で彩度を上げ（最大1.4倍）明るさを少し下げ（最大0.84倍。ポスターが白背景の写真で、そのままでは白文字が読めないため）、濃紺のベールは薄く（30%）、白い光沢（ガラスの反射）を少し重ねる。HERO の白文字のための影は紺ではなく中立の暗さで、コピーの周り（左下。768px以下は下側の横いっぱい）とヘッダーの下だけに置き、文字と一緒に消える。HERO の文字の影・ボタンと一時停止ボタンの半透明の地も中立の黒（共通の `.cx-image-text--light` の紺の影は HERO だけ上書き）。PRODUCTION FLOW（`data-cxg-calm`）の後ろはベールを少し足して落ち着かせる（44%）。舞台の最後（03 FAQ / CONTACT の後）はフッターの濃紺へフェードしてつなぐ。不透明な濃紺の面は重ねない。
  - 文字の読みやすさはセクションごとの局所的な面で保つ: WORKS は見出しと右の文字欄の後ろに柔らかい影（`.cxw-info::before` の放射グラデーション）と文字の影。作品ごとのぼかし背景（2枚を切り替え）は半分の強さで HERO のぼかしの上に重ね、上下端を溶かす。01 CREATIVE SOLUTION は見出しとカードの位置にだけ薄い影（`.cxcs--on-stage`）。02 PRODUCTION FLOW は暗いガラスのカード（下の「02 PRODUCTION FLOW」）。背景がすでにぼけているので `backdrop-filter` は使わない（動画の毎フレームでぼかしが重なるのを避ける）。
  - 動画: 舞台が画面外・タブ非表示・一時停止ボタン・作品ビューアを開いている間（`cxworks:viewer`）・文章の多い 03 FAQ / CONTACT（`data-cxg-still`）が画面の中央にある間は止める（静止した映像の上で読む）。動きの軽減: 動画なし・スクロール連動なし。ポスターが HERO を半分過ぎたところで1回だけ「くっきり→ぼかし」に切り替わる（文字はそのまま）。JS 無効: 背景は HERO だけで、その下は濃紺。
  - **WordPress の掲載枠（2026-11-10 接続、ローカル実装・未公開）**: HERO・WORKS・01 CREATIVE SOLUTION は WordPress「サイトの表示 ＞ ContentsX ＞ Creative X」の枠を `GET /slots/<キー>` で読む（`cxWorks.slot`、`js/cx-works.js`。WordPress 側の仕様はプラグインの `docs/DESIGN-content-library.md` §17）。キーは `cx-creative-hero`（MP4 3本まで・再生順）、`cx-creative-works`（マンガと動画、`format_key`）、`cx-creative-solution-manga` / `-anime` / `-video`（各1件まで）。
    - 応答の扱い（`cxDom.getJSONStatus` で状態を分ける）: **200・作品あり**＝WordPress の並び順のまま表示（WORKS の ALL も並べ替えない。MANGA / ANIME / VIDEO は `format_key` で絞る）。**200・`items: []`**＝WordPress で未設定。代わりの作品は入れない（WORKS は「作品は準備中です」と静的リンク、代表作品のカードは「作品は準備中です。」とサービスへのリンク、HERO はポスターのまま）。**通信エラー・時間切れ・5xx**＝空とは別に「作品を読み込めませんでした」（HERO はポスター）。**404**＝その WordPress にまだ枠が無い（プラグインの本番反映前＝2026-11-10 の本番）。コンソールに警告を出し、従来の一覧（`/works?site=contentsx`・`/bizanime-videos`、代表作品は `data/creative-solution.json` の ID）で表示する移行用の道。これも代用はしない。本番の 404 も CORS ヘッダー付きで返るので、ブラウザは 404 として読める（確認済み）。⚠️ 404 は `Cache-Control: public, max-age=300, s-maxage=600` でキャッシュされるので、プラグイン反映後も最大10分ほど古い 404 が返りうる。
    - カードの読み方: マンガは `manga.gallery`・`manga.view_type`（`spread`＝見開きの本、`vertical_only`＝縦読み）をそのままビューアへ（`/manga/{id}` は呼ばない）。動画は `video.provider`（youtube・youtube_playlist・drive・mp4。`file`＝WordPress のメディアの MP4 は `mp4` として `video.src`）を共通プレイヤー・3D スマホへ。出せないカードは除いて警告。HERO は `video.src`（`cms.contentsx.jp/wp-content/uploads/` の MP4、半角英数字のファイル名だけ）を WordPress の順に再生し、最後まで行ったら先頭へ（1本ならループ）。1本目の `thumb` をポスターにする。再生できないファイルは飛ばす。
    - 3D スマホの画面の絵（WebGL）は CORS を許すホストだけ（`i.ytimg.com`・`contentsx.jp`）。WordPress のアップロードは CORS を許していないので読まない（`crossOrigin` の読み込みも起こさない）。その作品は再生が始まるまで画面に静かな絵（暗い光と再生マーク）を出す。カード・WORKS の背景など通常の `<img>` は今までどおり WordPress の画像を使う。
    - テスト: `python3 tests/test_creative_slots.py --url <loopback preview> --artifacts <output> [--channel chrome]`。WordPress の応答は `tests/fixtures/creative-x-slots.json`（手元の WordPress〈プラグインの feat/creative-x-slots〉の実際の応答。公開データだけ）に、実データに無い mp4・file・HERO の MP4 を同じ形で足して使う（本番の成果物には入らない。`tests/` は公開しない）。ほかの Creative X のテストは枠に 404 を返し、移行用の道を確かめる。
  - 作品データ（移行用の道と、作品の形）: WORKS と 01 CREATIVE SOLUTION は同じ `cxWorks.load()`（`js/cx-works.js`）を使う。WordPress の `/works?site=contentsx` と `/bizanime-videos` の取得（各1回）と、作品の形への整え方はここだけ（WORKS 独自の整形は削除）。並び（WordPress の順・ALL の混ぜ方 `data-cxw-mix`）と絞り込みは WORKS が持つ。作品の形（`kind`・`id`・`title`・`description`・`tags`・`uses`・`visual`・`thumb`・`portrait`、マンガは `cover`・`work`、動画は `media`・`poster`・`playlist`）は `js/cx-works.js` 冒頭に書いた。掲載枠 API（未確定。推測で実装しない）が決まったら、その応答をこの形に写す関数を `cx-works.js` に足せば、両セクションとビューアは変えずに済む。
  - Three.js（作品ビューアの3Dスマホ）: **three.js r170（npm `three@0.170.0`、MIT）の `build/three.module.min.js` を無改変で `js/vendor/three/three.module.min.js` に置く**（ライセンスは同じフォルダの `LICENSE`）。npm 配布物の sha512（`FQK+LEpYc0fBD+J8g6oSEyyNzjp+Q7Ks1C568WWaoMRLW+TkNNWmenWeGgJjV105Gd+p/2ql1ZcjYvNiPZBhuQ==`）をレジストリの値と照合して取り込んだ。ファイルの SHA-256 は `08fd7545d13d2c7fb65ab691530a802dafefd638596501854f267d0fb13c39e7`。ほかの依存（アドオン・CDN）は無く、`eval` も使わないので CSP（`script-src 'self'`）を変えていない。691KB（gzip 171KB）で、ページ読み込みでは取得しない（動画を開いたとき、または「動画を見る」に指・フォーカスを置いたときに `import()`）。更新するときは同じ手順で取り込み、この節の版とハッシュを書き換え、`js/cx-phone-3d.js` の動作を確認する。
- **Creative X 紹介ページの 02 PRODUCTION FLOW（2026-11 確定デザイン、ローカル実装・未公開）**: 「02 / PRODUCTION FLOW」・見出し「ご相談から、完成まで。」（「、」の後で改行、1語は割らない）・説明「企画・ストーリー設計から制作、納品まで。一つひとつ確認しながら進めます。」・短いオレンジの線（左）と、4段の縦タイムライン（右）。生成元は `tools/templates/service-group-creative.html.tpl`、見た目は `css/service-creative-flow.css`（`GROUP_ASSETS` でこのページだけ）。見出しの id は従来の `cxg-flow`、`data-cxg-calm` も同じ。
  - 工程: 01 ご相談・ヒアリング（制作の目的、届けたい相手、伝えたい価値を整理します。／お客様：課題やサービスの資料を共有）、02 企画・ストーリー設計（伝える内容を整理し、構成・シナリオ・絵コンテなどを制作します。／お客様：企画内容を確認）、03 制作・確認（マンガの作画、アニメーション、映像制作を進めます。／お客様：所定の確認段階で内容をチェック）、04 納品・活用（完成作品を納品し、用途に応じた活用方法をご案内します。／お客様：営業・Web・広告などで活用）。文字はすべて HTML（画像に文字を入れない）。日本語は句の切れ目に `<wbr>` を入れ、このセクションだけ `word-break:keep-all`（サイト共通の `p { word-break:auto-phrase }` が「活用方法」を割ったため）。
  - カード: 番号（大）とアイコン（オレンジの線画）・縦の区切り線・工程名・説明・「お客様：」の小さなラベル（人のアイコン付き、601px以上は1行）・右側の工程画像（左へ溶けるマスク）。暗い半透明のガラス（細い明るい縁・上からの光沢・ごく弱いオレンジの光）。`backdrop-filter` は使わない。オレンジは `--cx-color-creative` と、暗いガラス上で見やすくするためにそれを白へ寄せた `color-mix`（新しい色の値は作らない）。
  - タイムライン: カードの左に縦線と円のノード。ノードは各カードの番号の高さ（PC は4枚同じ高さ、600px以下は上から34px）。線はノードごとの区間で、次のノードまで届く（カードの高さが違っても切れない）。
  - 画面幅: 1101px以上は左に見出し（縦中央。1行の「ご相談から、」は列に収まる大きさまで＝`15.6cqi` が上限、文字の大きさは 1440px で止まる）・右にタイムライン。1101〜1280px は画像を細めにして文字の場所を取る。769〜1100px と 601〜768px は見出しが上、カードは全幅（画像は右）。600px以下はカードを縦積み（番号とアイコン → 工程名 → 説明 → お客様のラベル〈ラベルと内容を2行〉→ カード下端いっぱいの画像16:9）。320px でも横にはみ出さない。
  - 工程画像: `material/service-2026/creative-flow/NN-name-{640,960}.webp`（01-hearing・02-story・03-production・04-delivery）。ビズマンガの制作フロー用イラスト `material/images/flow/`（step1_hearing・step5_name・step6_seisaku・step8_nouhin。2752×1536・最大630KB、このサイトでは未使用だった）をカード用に縮小した複製（40〜105KB）。差し替えるときは同じ名前の2ファイルを上書きする。⚠️ 元の絵はマンガ制作の場面なので、03（制作）と 04（納品）はアニメ・映像の制作や「PC・スマホでの活用」を直接は描いていない。⚠️ `material/images/flow/` は BizManga が絶対 URL で参照している可能性があるので、元ファイルは動かさない・消さない。
  - 背景: 専用の背景画像・動画は置かない。舞台の HERO の映像（ぼかし）がそのまま見える（上の「構成と共通背景」）。重いときの軽い表示は舞台の既存の仕組み（Save-Data・2G・動きの軽減ではポスターの静止画だけ）。
  - 動き: `js/sitewide-motion.js` の1回だけの登場（`.cxpf-head`・`.cxpf-timeline` を対象に追加）。見出しが下から現れ、続いてカードが STEP 01 から順に右から現れ（0.16秒ずつ）、線が次のノードへ伸び、ノードが点く。上へ戻っても消えない。動きの軽減・JS 無効では最初から全部表示。
  - 確認: `python3 -m unittest discover -s tests -p test_build_services.py`（順番・文言・画像ファイルの存在・独自背景や動画が無いこと）と `python3 tests/test_creative_flow.py --url <loopback preview> --artifacts <output> [--channel chrome]`（6幅の配置・はみ出し・12px以上・タイムラインの線とノードの位置・画像・舞台の上で透明、登場の順番、動きの軽減・JS 無効）。
- **Creative X 紹介ページの 03 FAQ / CONTACT（2026-11 確定デザイン、ローカル実装・未公開）**: PRODUCTION FLOW の直後・共通フッターの直前、舞台の最後のセクション（`#creative-faq`）。生成元は `tools/templates/service-group-creative.html.tpl`、見た目は `css/service-creative-faq.css`、開閉は `js/cx-accordion.js` ＋ `css/cx-accordion.css`（`GROUP_ASSETS` でこのページだけ）。
  - 上段 FAQ: 左に「03 / FAQ」・見出し「よくあるご質問」・説明「制作について、よくいただくご質問をまとめました。」・短いオレンジの線、右に質問5件（暗いガラスの横長の行：Q01〜Q05〈Q はオレンジ〉・縦の区切り・質問・右端の＋／−）と、その下に右寄せで「よくあるご質問をもっと見る →」（`/faq`）。1100px以下は見出し → 質問 → CONTACT の1列。⚠️ 1行の見出し「よくあるご質問」は左の列に収まる大きさまで（列をサイズコンテナにして `13.6cqi` を上限。以前は1440pxで質問の列へ20pxはみ出し、1920pxでは重なっていた）。列の間隔は 40〜88px。文字の大きさは 1440px で止まる（コンテンツの幅がそこで止まるため。1920px でも 1440px と同じ見え方）。質問は切らずに折り返す（句の切れ目に `<wbr>`、`word-break:keep-all`）。行の高さは56px以上。
  - 質問と回答（HTML に直接書く。API からは読まない。回答は依頼時の初期案）: Q01 何をつくるか決まっていなくても相談できますか？／Q02 マンガ・アニメ・映像は1つだけでも依頼できますか？／Q03 料金や制作期間はどれくらいですか？／Q04 依頼前に何を準備すればよいですか？／Q05 制作途中で内容を確認できますか？ 回答は料金・期間・修正回数を断定しない（「形式や内容によって異なる」「事前にご案内」）。`/faq`（ビズマンガ中心。8ページ税込30万円前後、3〜4週間、修正は標準5回、初回の相談・見積もり無料など）と食い違う内容は書いていない。⚠️ アニメ・映像の料金・期間・修正条件は `/faq` にも無い（未確認）。
  - 開閉（`js/cx-accordion.js`、他のページでも使える）: `data-cx-accordion`（一覧）・`data-cx-accordion-item`・`data-cx-accordion-trigger`（`<button>`、`aria-controls`・`aria-expanded`）・`data-cx-accordion-panel`（`role="region"`・`aria-labelledby`）。HTML では全部開いた状態（`aria-expanded="true"`）で、JS が閉じる（JS 無効でも全部読める）。クリック・Enter・Space で開閉、↑ ↓ Home End で質問の間を移動。複数同時に開ける（`data-cx-accordion="single"` で1つだけ）。開閉は高さの0.32秒のアニメーション（grid の行 0fr ↔ 1fr）、閉じた回答はスクリーンリーダー・Tab から外す（visibility）。動きの軽減ではアニメーションなし。
  - 下段 CONTACT: 細い区切り線の下に横長の半透明パネル（`data-cx-page-cta`：共通フッターは自分の問い合わせ欄を出さない＝重複しない、`css/site-footer.css`）。「CONTACT US」・見出し「まずは、つくりたいことをお聞かせください。」（見出しの id は従来の `cxg-contact`）・説明2行・右にオレンジのボタン「制作について相談する」（`.cxg-button` にメールのアイコンと外向きの矢印、`/contact`＝既存のフォームと計測）。ボタンの下に従来の「資料をダウンロードする」（`.js-dl-trigger`＝`js/dl-modal.js` の資料請求。確定デザインには無いが、既存の導線を消さないため小さな文字リンクで残した）。768px以下はボタンを全幅に。
  - 背景: 専用の背景は置かない（舞台の HERO の映像のぼかし。PRODUCTION FLOW と同じ落ち着いた濃さで、このセクションが画面の中央にある間は映像を止める）。パネル・行は暗いガラスで文字を読ませる。舞台の終わりはフッターの濃紺へフェード。
  - 動き: `sitewide-motion.js` の1回だけの登場（見出し・質問の一覧・CONTACT パネル）。ボタンのホバーは矢印が2px動くだけ。
  - 確認: `python3 -m unittest discover -s tests -p test_build_services.py`（質問・回答が HTML にあること、開閉の配線、JS 無効で開いていること、`/contact`・`/faq`、ページ CTA が1つ、舞台の最後）と `python3 tests/test_creative_faq.py --url <loopback preview> --artifacts <output> [--channel chrome]`（6幅の配置・質問が切れない・12px以上・押せる高さ・ボタンの幅、舞台の上で透明・フッターが直後で問い合わせ欄が出ない、マウスとキーボードの開閉・Tab 順、`/contact` へ移動、JS 無効、動きの軽減）。
- **Creative X 紹介ページの作品ビューア（2026-11、ローカル実装・未公開。WORKS と 01 CREATIVE SOLUTION で共通）**: 作品をページ内で開く画面は `js/cx-works.js` の `cxWorks.open(item, opener)` の1つだけ。WORKS（大きな絵・「マンガを読む／動画を見る」・一覧で Enter）も CREATIVE SOLUTION（代表作品カード）もこれを呼ぶ（WORKS 独自のダイアログは無い）。
  - 共通: 暗い背景（PC は後ろを軽くぼかす、768px以下は不透明）・種別（MANGA / ANIME / VIDEO）・作品名・閉じるボタン、開くときはフェード＋少し浮き上がる（0.35秒）、閉じるときは0.2秒のフェード（動画は閉じた瞬間に埋め込みごと消え、音も止まる）。読み込み中・表示できないときの文言はマンガビューア・動画プレイヤーのもの。開いている間はほかを `inert`・背面スクロール停止（`html.cxwv-lock`）。×・Esc・外側のクリックで閉じ、元のスクロール位置と開いたボタンへフォーカスを戻す（WORKS の絞り込み・選択中の作品はそのまま）。「拡大」中の Esc は先に拡大だけを閉じる。
  - **マンガ＝本型**: `js/cx-manga-reader.js` の本型モード（`opts.book`。トップの Creative X は使わないので変わらない）。ビズ書庫（`contents-x/web-bizmanga` の `biz-library.html`・`js/works.js`・`css/works.css`。このリポジトリには取り込まず、変更もしない）のページめくりを移植した: 見開きは右綴じ（右に若い番号、中央に綴じ目の影、紙の質感、ページ端の重なり）。次へは左ページが綴じ目を軸に右へめくれ、前へは右ページが左へめくれる（`goNext` / `goPrev`：表＝今のページ、裏＝めくった先のページ、0→±180°）。1ページずつの表示（768px以下）は `mobileFlipTo` と同じく左端を軸にめくる。どちらも0.5秒・`cubic-bezier(.3,0,.2,1)`、影は15〜65%で出入り、下のページは45%で差し替え（ビズ書庫と同じ値）。ページの形は1ページ目の縦横比（無ければ 0.707）。めくっている間の操作は無視（二重にめくらない）。ページ番号・‹ ›・← →・左右半分のクリック・スワイプ・「拡大」は従来どおり。縦読み作品（`view_type` が縦、または1ページ目の縦横比が1.8超）は本にせず従来の縦スクロール。動きの軽減ではめくらずに切り替える。見た目は `css/cx-manga-book.css`（ビズ書庫の値を `cxmr-` の名前で）。
  - **アニメ・ビデオ＝横向きスマホ（3D）**: `js/cx-phone-3d.js`（ES モジュール、three.js）が WebGL で横向きのスマホを描く: 本体の厚み（長辺の約5.6%）、角の丸いメタルの側面フレーム（環境光の映り込み）、黒いガラスの前面とベゼル、前面カメラと受話口、電源・音量ボタン、短辺の USB-C 端子とスピーカー穴、アンテナの帯、柔らかい影。ダイアログ全体を覆う canvas に描き、場面は CSS ピクセル単位（z=0 で1単位＝1px）なので、3D の画面はプレイヤーの箱（`.cxwv-phone__screen`）と同じ四角形・角丸で作られる。開くと、傾いて奥にあるスマホがフェードインしながら正面へ向き直る（0.9秒、イーズインアウト。画面には作品のポスター）。正面で止まったら（`.is-settled`）本物のプレイヤー（YouTube の iframe）がその上に0.24秒でフェードインし、以後は描き直さない（常時アニメーションなし。サイズ変更・スクロール時だけ1回描く）。YouTube を WebGL のテクスチャにはしない（iframe をそのまま重ねるので操作はすべて使える）。プレイヤーは押した時点で作る（再生の許可を失わないため。見えるのは正面に来てから）。閉じる・別の作品を開くと canvas・形・素材・テクスチャ・環境マップ・イベントを捨て、WebGL の文脈も解放する。動きの軽減では入場なしで正面に描く。768px以下も3D（ベゼルは細く、画面は16:9・ほぼ全幅、傾きは小さめ）。
    - CSS の代わり（従来の CSS のスマホ）: WebGL2 が無い・ソフトウェア描画になる（`failIfMajorPerformanceCaveat`）・Save-Data / 2G・CPU 2コア以下・メモリ1GB以下・モジュールが4秒以内に届かない・GPU が文脈を失ったとき。CSS のスマホは3Dの配置の基準でもある（3D のときは描画だけを消し、箱の位置はそのまま）。
    - CSS のスマホ: 枠（暗いグレーのグラデーション・角丸・細いベゼル・縁のハイライトと下側の厚み・影）、側面のカメラ、長辺のボタンは装飾で、画面の外側だけに描くので、YouTube の操作（再生・停止・音量・シーク・字幕・全画面）は隠さない。PC は画面2:1（16:9 の動画は YouTube 側で左右に細い帯、縦長の動画は切らずに帯が広がる）で、題名の下に画面の高さいっぱいまで大きく。768px以下は「スマホの中のスマホ」にしないため、枠を細いベゼルだけにして画面を16:9・ほぼ全幅に。横向きに持ったスマホ（高さ520px以下）は高さに合わせる。枠の色は端末の描写専用で、ほかの部品には使わない。
  - データ: `cxWorks.open` が読むのは上の「作品データ」の形だけ（マンガは `work` か `pages`＋`viewType`、動画は `media`・`poster`・`playlist`）。
  - 確認: `python3 tests/test_creative_viewer.py --url <loopback preview> --artifacts <output> [--channel chrome]`（PC の見開き・綴じ目・ページの形、次へ／前へのめくりの向きと表裏の絵、左右クリック、最終ページとサンクス、二重にめくらない、スマホの1ページとめくりの軸・タップ・スワイプ、縦読み、動きの軽減、横向きスマホの枠〈PC 2:1・ベゼル、スマホ 16:9 ほぼ全幅、横持ち〉でプレイヤーが画面を満たし四隅が隠れない、閉じると止まる、WORKS と CREATIVE SOLUTION が同じビューアを開く）と、`tests/test_creative_works.py`・`tests/test_creative_solution.py` のビューア部分。
- **Creative X 紹介ページの 01 CREATIVE SOLUTION（2026-11、ローカル実装・未公開）**: 旧「03 SERVICES」（サービス画像カード3枚）を置き換えた。位置は WORKS の後、02 PRODUCTION FLOW の前（2026-11 の統合で 03 → 01）。
  - 構成: 「01 / CREATIVE SOLUTION」・見出し「伝えたい価値を、最適なカタチへ。」（「最適なカタチ」はオレンジ）・説明 → 横長のパネル「企業が伝えたいこと」→ 1本の線が3方向に分かれる → ビズマンガ／ビズアニメ／ビズビデオの代表作品カード（各1作品）→ 下向きの矢印 → 「活用する場面」（営業資料・Webサイト・SNS広告・採用活動）→「1つの形式だけでも、複数の組み合わせでも制作できます。」。769px以上はカード3列、活用場面は1101px以上で4列・769〜1100pxで2×2。768px以下は縦1列で、分岐線の先に「マンガ／アニメ／映像」の小さな札を置き、その順にカードが続く（600〜768px は絵が左・文字が右）。活用場面は2×2。
  - 作品: WordPress の代表作品の枠（上の「WordPress の掲載枠」）。枠が 404 のときだけ、`data/creative-solution.json` に書いた WordPress の識別子を使う（manga＝`/works?site=contentsx` の `id`、anime・video＝`/bizanime-videos` の YouTube 動画ID かプレイリストID）。`tools/build-services.py` が検査してカードの `data-work-id` に書き、`js/service-creative-solution.js` がブラウザで WordPress から題名・表紙／サムネイル・ページ・動画を読む（HTML に作品名・画像・埋め込みを書かない）。2026-11-07 時点: マンガ `opro-kamiless`「マンガでわかるカミレス【公共・自治体編】」（8ページ・見開き）、アニメ `V9ZC16hTlZI`「Good Bye MV」（viewer）、映像 `QqRlb_JGaHw`「VLOG」（viewer）。カードの説明文はサービスの一文（静的）。WordPress に作品ごとの説明・再生時間が無いので、デザインの再生時間（2:42 など）は出さない。将来 WordPress で代表作品を指定するときは、`js/cx-works.js` の取得結果にその印を持たせ、`service-creative-solution.js` で JSON の指定より先に見る。
  - 枠が空・指定の作品が無いときは、ほかの作品で代用しない（2026-11-10 から。以前は同じ種類の先頭の作品を出していた）。取得できないときは、カードはサービスへのリンク（ビズ書庫・ビズアニメ公式・`/services/#bizvideo`）のままで「作品を読み込めませんでした。」、0件は「作品は準備中です。」。仮の作品は出さない。読み込み中は題名の場所に棒を出して高さを保つ。
  - カード: 角丸の長方形。サービス色の枠と下端の光（マンガ＝Creative X のオレンジ、アニメ＝明るい青、映像＝紫。DESIGN-SYSTEM-2026.md の例外）。絵は16:9。動画のサムネイルは切らない（maxresdefault が無ければ hqdefault）。マンガは表紙を切らずに全体を出し、余白は同じ表紙のぼかしで埋める。操作はカードに1つだけ（`<button>` の `::after` がカード全体を覆う。リンクとボタンを入れ子にしない）。ホバーで4px上がり、絵が1.035倍。キーボードは Tab → Enter / Space。
  - 閲覧（`js/cx-works.js` の `cxWorks.open`）: 上の「作品ビューア」（マンガは本型のページめくり、アニメ・ビデオは横向きスマホ型。WORKS と共通）。ページで開けるのは1つだけ（別の作品を開くと前を閉じる）。
  - 背景: 新しい画像は足さない。今は HERO の舞台 `.cxg-stage` の中にあり、セクションは透明で、上の「共通背景」のぼけた映像が見える。見出しとカードの位置にだけ薄い影を置く（`.cxcs--on-stage`）。舞台の外に置いた場合（単独）は CSS だけの暗い背景（濃紺＋淡い光）か、ページにある HERO のポスターを強くぼかして使う（`.has-hero-backdrop`、2本目の動画は読まない）。
  - 生成・読み込み: `GROUP_ASSETS` でこのページにだけ `css/home-creative-x.css`（ビューア・プレイヤーの見た目）・`css/cx-works.css`（ダイアログ）・`css/service-creative-solution.css` と、`wp-config.js` → `cx-dom.js` → `cx-manga-reader.js` → `cx-video-player.js` → `cx-works.js` → `service-creative-solution.js` を読み込む。CSP の `media-src` は `'self' https://cms.contentsx.jp`。Sales X とサービス一覧の出力は変わらない。登場演出は `sitewide-motion.js`（見出し・図・活用する場面・補足を1回だけ）。
  - 確認: `python3 -m unittest discover -s tests -p test_build_services.py`（並び順、作品IDの検査、HTML に作品名・埋め込みが無いこと、他ページに読み込みを足さないこと）と `python3 tests/test_creative_solution.py --url <loopback preview> --artifacts <output> [--channel chrome]`（8幅の並び・はみ出し・12px以上・44px、カードのどこを押しても開くこと、マンガの見開き順・ページ送り・← →・拡大と Esc の順・フォーカスとスクロールの戻り、動画の埋め込みURL・閉じると消えること・外側クリック・Enter・同時に1つ、スマホの1ページ表示・全画面ダイアログ・16:9、縦読み、指定作品が無いとき、取得失敗・片方失敗・0件・読み込み中、JS無効、動きの軽減、背景の受け渡し）。手元で実データを見るときは、WordPress が開発用に許可している `http://127.0.0.1:5500` か `http://localhost:3000` でプレビューする（ほかのポートでは CORS で取得できず「読み込めませんでした」になる）。

### 3.1 旧Hero v2（2026-09-29トップから撤去・履歴）

**2026-05-10 v2 採用、2026-09-29撤去**: 旧 hero (テキストロゴ+タグライン+カルーセル) を撤去し、左コピー+中央キャラ+右5サービスカード+下USPマーキー帯の構成に刷新していた。CSS: `css/hero-v2.css`（現在のトップでは未使用）。以下は過去の実装記録。

**2026-07-02 キャラ一体化**: 従来「背景飛沫(`hero_bg`) + 透過キャラ(`hero_chars`)」の2層構成だったが、飛沫と女性キャラ2人を1枚に焼き込んだ画像へ差し替え。専用キャラレイヤー(`.hv2-chars`)と `hero_chars.*` は廃止。女性キャラは背景イラストの一部として描画され、PC では右サービスカードが手前に重なる。PC グリッドは `minmax(620px,1fr) 280px` の2列に変更、`.hv2-bg` の opacity は 1。

**2026-07-07 イラスト改訂版へ差し替え**: 同キャラ・同構図の改訂版イラスト（元データ anime_high_quality_3840px.png 3840×2166、飛沫がより濃いバージョン）から hero_bg 6ファイルを再生成して置換。寸法・ファイル名は従来と完全同一（PC 1672×941 / SP 1375×1144、各 avif/webp/png）のため HTML/CSS 変更なし。元画像は16:9より微妙に縦長のため PC は crop 3840×2160(+0,3) で正規化してから縮小、SP はキャラ中心が右寄り約66%になるよう crop 2596×2160(+344,3) してから縮小。変換は ffmpeg(lanczos, rgb24化) + cwebp(-q82) + avifenc(-q60)。

### 3.1 PC レイアウト
| エリア | 内容 |
|---|---|
| 背景(キャラ一体) | `material/hero/hero_bg.{avif,webp,png}` (1672×941) マゼンタ飛沫+女性キャラ2人の一枚絵を全幅描画 (object-fit:cover, opacity:1) |
| 左コピー | `<h1 class="hv2-headline">` 「ストーリーで／成果を／生み出す」(成果 em 巨大化、回転+skew+SVGグランジフィルタ) + サブコピー「漫画・動画・Web・IPを横断し、企業の成長を加速する。」。**見出し・サブとも白の縁取り(8方向 text-shadow + ソフトハロー)で背景画像から可読性を確保 (2026-07-02)** |
| 右カード | `.hv2-services` の5サービス(DOM順=表示順): ビズマンガ(→ bizmanga.contentsx.jp) / スクール(→ newmanga-academy.contentsx.jp = ニューマンガアカデミーLP、2026-08-22設定) / コンテンツ採用(フル幅、→ ichioshi.contentsx.jp 2026-07-07設定、2026-07-07にスクール直後へ移動) / コンテンツセールス / IP事業。未確定の2枚(コンテンツセールス・IP事業)は `href="#"` + `data-todo` 属性。スキューシャドウ枠 |
| CTA | primary「お問い合わせ」(マゼンタ pill) + ghost「資料ダウンロード」(白枠 pill)、hover で alt テキストへスライド |
| 下帯 | `.hv2-strap` USPマーキー (業界最安値クラス／対応領域 国内外20+言語／最短2週間納品／企画から運用まで一気通貫) |

### 3.2 SP レイアウト (max-width: 768px)
| 不変条件 | 詳細 |
|---|---|
| ビジュアルゾーン(比率固定) | `.hv2-bg` を `inset: 60px 0 auto 0 / height: var(--hv2-visual-h)` に閉じ込め、キャラ一体の一枚絵 (`hero_bg_sp.{avif,webp,png}` 1375×1144) を全幅描画。**`--hv2-visual-h = calc(100vw * 1144 / 1375)`** とし box の縦横比を画像と一致させることで `object-fit:cover` でもクロップせず画像全体を表示（トリミングで縦長化するのを防止）。下端は `mask-image` + `::after` 70px 白オーバーレイでフェード |
| CTA を画像の下へ(絶対条件) | `.hv2-ctas` は `.hv2-copy`(flex縦)の**子**なので `grid-area` は効かない。`.hv2-copy { min-height: calc(var(--hv2-visual-h) + 96px) }` で画像高+余白を確保し、`.hv2-ctas { margin-top: auto }` で下端へ落とす。→ 画面幅で画像高が変わっても CTA は常に画像の直下(≒下端+16px)に並ぶ。検証: 360/390/430/768 で `ctas.top >= bg.bottom` |
| 見出し傾斜 | `transform: rotate(-6deg) skewX(-9deg)`、SP は SVG グランジフィルタを解除 (filter:none) |
| sub copy 傾斜 | 見出しと同じ `rotate(-6deg) skewX(-9deg)` で `transform-origin: left bottom` 統一 |
| client-logos 連結 | （撤去済み。ロゴ帯 `js/client-logos.js`・`js/data/client-logos.js` と style.css の指定は 2026-10-13 に削除） |

> 2026-07-02: キャラ一体化＋SP一枚絵の比率固定表示に刷新。旧「bg/chars 下端一致」ルール（`--hv2-chars-h` / `chars.top = visual_h - chars_h`）・透過キャラ `right:-100px`・固定 `margin-top:166px` は全廃止。

### 3.3 CSS変数（SP）
```css
.hv2-hero {
  /* 一枚絵をトリミングせず全幅表示するため画像比率(1375:1144)で高さを算出 */
  --hv2-visual-h: calc(100vw * 1144 / 1375);
}
```
画像は比率固定で全体表示。CTA は `.hv2-copy` の min-height + `.hv2-ctas { margin-top:auto }` で画像直下へ。`--hv2-chars-h` は廃止済み。

### 3.4 旧仕様（撤去済み・参考）
旧 hero (テキストロゴ「ContentsX_hero.webp」+ タグライン「埋もれていた物語に光を当てる」+ カルーセル + Phase 2 演出) は v2 採用で実質非表示となった。`hero-new.js` / `hero-fx.js` のトップでの読込は2026-09-29に終了。0〜3.6s イントロオーバーレイ系は 2026-05-10 撤去済み (`heroIntroOverlay` / `startIntro` / `finishIntro` 系全削除)。

## 4. 共通 JS コンポーネント

| ファイル | 役割 | 呼び出し方 |
|---|---|---|
| `js/cta.js` | 共通CTAセクション生成 | `<section id="cxCtaMount"></section>` を置く（会社概要のみ。サービス一覧は2026-10-10、採用は2026-10-12にページ専用CTAへ統合） |
| `js/nav.js` | ヘッダーナビ + ハンバーガー + 言語切替 | 全ページ（defer） |
| `js/i18n.js` | i18nエンジン | 全ページ（nav.jsより先） |
| `js/column.js` | コラム一覧の Featured 表示・カテゴリチップ生成・絞り込み | `column.html`（`#cx-column-data` JSONを読む） |
| `js/dl-modal.js` | 資料DLモーダル | contact送信済みか localStorage で判定 |
| `js/wp-api.js` | WP API クライアント（ニュースだけ） | `.news-list` を描画し、終わったら（失敗時・`WP_CONFIG.enabled=false` のときも）`wp-data-ready` を発火。`/news` の読み込み表示はこの合図で消す。2026-10-13 に旧トップ用の `/works`・`/works-new` 取得（`WORKS_DETAIL_DATA` / `NEW_WORKS_DATA`）を削除 |
| `js/cx-dom.js` | WordPress 連携部品の共通道具 `window.cxDom` | `el` / `iconButton` / `text` / `safeImage`（サイト内パスか許可ホストの https 画像だけ）/ `getJSON(path, timeout, label)` / `getJSONStatus(path, timeout, label)`（`{ status, data }`。空・404・失敗を分けたい Creative X の掲載枠用）。使う側（`cx-manga-reader.js`・`cx-video-player.js`・`home-creative-x.js`・`home-topics.js`・`cx-works.js`・`service-creative-solution.js`）より前に defer で読む（トップ・採用・Creative X 紹介）。順番は `tests/test_asset_order.py` がデプロイ前に検査し、読めなかったときは各部品が何もせず HTML のまま残る。`safeImage(url, hosts)` の hosts で許可ホストを絞れる（マンガのページ画像は WordPress と自サイトだけ） |
| `js/hubspot-lazy.js` | HubSpot 追跡コードの遅延読み込み | 初回操作か4秒後に読む。トップ・会社概要・採用・ニュース詳細。お問い合わせは従来どおり直接読み込み、採用エントリーは読み込まない |
| `js/script.js` | 下層ページの小さな動き | 会社概要・ニュース一覧・ニュース詳細。ヘッダーのスクロール時クラス、見出しのフェードイン、ページ内リンクのスムーススクロールだけ（2026-10-13 に旧トップ用の約1100行を削除） |
| `js/cx-works.js` | Creative X の作品（WordPress）の取得・整形と、作品をページ内で開く共通ビューア `window.cxWorks`（WORKS と 01 CREATIVE SOLUTION） | `slot(key)`（WordPress の掲載枠。`{ state: ok|empty|missing|error, items }`）/ `load()`（404 のときの従来の一覧。作品の形は冒頭のコメント）/ `find(data, kind, id)` / `open(item, opener)`（マンガ＝本型〈`cx-manga-reader.js` の `book`〉、アニメ・ビデオ＝横向きスマホ〈3D、使えないときは CSS〉の動画プレイヤー）/ `close()` / `isOpen()` / `warm()`（3Dスマホのモジュールを先に取得）。開閉で `document` に `cxworks:viewer`。`cx-manga-reader.js`・`cx-video-player.js` の後に読む。見た目は `css/cx-works.css` と `css/cx-manga-book.css`（§3.0「作品ビューア」） |
| `js/cx-phone-3d.js` | 作品ビューアの3Dスマホ（ES モジュール。`cx-works.js` が動画を開くときに `import()`） | `mount({ host, frame, screen, poster, reduced, onSettle, onLost })` → `{ destroy() }` か `null`（CSS のスマホを使う）。依存は `js/vendor/three/three.module.min.js`（three.js r170、MIT。§3.0「Three.js」）だけ |
| `js/wp-config.js` | WP設定 | API baseURL / cache TTL / メンテナンス表示スイッチ（§6「WordPress 一時停止スイッチ」） |

### 4.1 CTA セクション共有化 ⭐
- 6ページで CTA を重複コピペしていた問題を解消
- `<section id="cxCtaMount"></section>` + `<script src="js/cta.js">` の2行だけ書けば挿入される
- ボタンは **nav-cta (上部メニューと同じスキューフィル)** で統一
- 1箇所編集で全ページ反映

## 5. i18n 仕様

- **方式**: 2層構造（`data-ja`/`data-en` 属性 + `i18n/en.json` 辞書 336エントリ）
- **localStorageキー**: `cx-lang`
- **公開API**: `window.i18n` (switchLang/t/translateAll/addTranslations/getLang/getDict/translateElement)
- **スクリプト読込順序（必須）**:
  ```html
  <script src="js/i18n.js" defer></script>
  <script src="js/nav.js" defer></script>
  ```
- **placeholder翻訳**: `data-ph-ja` / `data-ph-en` （contact フォーム）
- **MutationObserver**: 英語モード中の動的DOMを自動翻訳
- **data-i18n-skip**: 翻訳対象外
- **data-i18n-html**: innerHTML翻訳（改行タグ含む）
- **カスタムイベント**: `i18n-lang-changed` で他JSに言語変更通知

## 6. 外部連携

| サービス | 用途 | 設定値 |
|---|---|---|
| HubSpot Forms | お問い合わせ | Portal `48367061` / Form `b6da14d0-d60d-4357-89fc-0015ed32b704`。⚠️ **部署（`busyo`）は HubSpot 側で必須**＝空だと送信が拒否される（B/C 共通フォーム）。`contact.html` の部署欄は `required`、加えて `js/contact.js` が送信時に前後の空白を除いて空なら `setCustomValidity` で止める（HTML の `required` は空白だけの入力を通すため。メッセージは日英切替に追従。2026-09-29） |
| Contents X CRM（ビズカルテ） | お問い合わせをCRMの受信箱へ連携（2026-07-29 追加・2026-09-29 **貼り付けコード方式**へ移行） | **貼り付けコード方式**: CRM の貼り付けコード `https://contentsx-crm.vercel.app/embed/inbound-v1.js` を `contact.html` の `</body>` 直前で1行読み込む（`data-source-key`＝本サイトの公開キー・`data-auto="false"`・`data-honeypot="#cxWebsite"`・`async`）。`js/contact.js` の送信処理で、HubSpot送信の直前に `copyToCrm(form)` を1回呼ぶ（中身は `BizcarteInbound.sendForm(form)`。貼り付けコードは async なので、送信時にまだ読み込めていなければ `load` を待って送る。例外は外へ出さない。読み込み失敗・API 欠落はコンソールに警告を残す。貼り付けコードは `script[data-source-key]` で探すのでファイル名に依存しない）。受信箱の種類は `form_kind: "inquiry"`（お問い合わせ）。⚠️ **採用応募は別フォーム `/recruit/entry`（§9.7）で、CRMの貼り付けコードを読み込まない＝CRMに送らない**（営業リードのみをCRMに入れる方針）。`contact.html` に来るのは法人のお問い合わせだけなので、`copyToCrm` は毎回呼ぶ（旧 `?position=` リンクは head で採用フォームへ転送）。項目は5つの入力欄の `data-crm-field`（company→`company_name`／department→`department`／fullName→`full_name`／email→`email`／message→`message`）で明示している。ハニーポット `#cxWebsite`（`data-i18n-skip`・`name="website"`＋`tabindex="-1"`）は値が入るとCRM側が黙って破棄する。送信先は `/api/inbound/s/<公開キー>`。公開キーは**秘密ではない**（ブラウザに出る前提）。CRM側は**登録済みの送信元ドメインだけ**を受け付ける＝本番ドメイン `https://contentsx.jp` 以外（localhost 等）からの送信は拒否される（HPの受付には影響なし）。連投制限は送信元ごとに10分5件。`data-auto="false"` は必須（外すと入力チェックで止まった送信まで拾う）。**トークンの管理は不要**（旧方式の `CRM_TOKEN`／CRM側 `INBOUND_SECRET` の同期ルールは廃止）。CSP は `script-src` に `https://contentsx-crm.vercel.app/embed/inbound-v1.js` を**ファイル単位で**追加（`connect-src 'self' https: wss:` は既に CRM への送信を許しているので変更なし）。SRI（`integrity`）は**付けない**（CRM 側が同じファイル名のまま互換更新するため、付けると更新のたびに読み込みが止まり CRM にだけ届かなくなる。ルート docs/operations/SECURITY.md に例外として記録）。⚠️ **CRM のドメインを変えるときは、`contact.html` の script の `src` と CSP の `script-src` の2か所を直す**。**CRM 送信は応答を待たず例外も外へ出さないため、失敗しても HubSpot 送信・完了表示・Google広告CVは従来どおり動く**。CRM側は受信箱に溜めるだけで、担当者が承認して初めて会社・担当者・活動が作られる。⚠️ 2026-09-24 の CRM の組織分離から旧経路（`/api/inbound/web` への並行 POST）は 404 になり、この間 HubSpot には届き CRM には届いていなかった（BUGS #056） |
| Google Analytics 4 | アクセス解析 | 測定ID `G-B000C4JCCX`（全HTMLの `<head>` に `gtag.js`、2026-04-16 設置） |
| Google Ads | コンバージョン計測・リマケ | コンバージョンID `AW-18108125426`（GA4タグ直下に `gtag('config', 'AW-...')` 追加、2026-05-09 設置）。**CV計測イベント2種**: ①「お問合せフォーム到達」(`9tNKCNH49agcEPKh0LpD`) = `contact.html` head で発火 / ②「送信完了サンクス」(`F13ECI3R3qgcEPKh0LpD`) = `js/contact.js` の HubSpot送信成功 `.then()` 内で発火。⚠️ 採用の応募はどちらにも数えない（`/recruit/entry` は AW の config も CV も置かず、GA4 イベント `recruit_entry_submit` だけ。旧 `/contact?position=` リンクは①の前に転送して発火させない）（2026-05-20 ラベル末尾を `…Cl…`→`…CI…` に是正、B/C共通） |
| WordPress REST API | 漫画事例 / ニュース | `https://cms.contentsx.jp/wp-json/contentsx/v1` |
| GitHub Pages | ホスティング | `contentsx.jp` (CNAME) |

### WP API エンドポイント
- `/works?site=contentsx` — 漫画事例
- `/works-new?site=contentsx` — 新作情報
- `/news?site=contentsx&per_page=50` — ニュース

### WordPress 一時停止スイッチ（メンテナンス表示・2026-10-22・Issue #173）⭐
WordPress 側の保守などで止めたいときに、**`js/wp-config.js` の `maintenance: false` を `true` にしてmainへ反映するだけ**で次が一度に起きる。戻すときは `false` に戻して反映する。
- そのページから WordPress API（`https://cms.contentsx.jp/wp-json/`）へのアクセスを一切しない（`fetch` 自体を設定ファイルで止めるので、URLを直書きしている部品も止まる）。各部品は既存の「読み込めなかったとき」の表示に落ちる（TOPICS は HTML の初期3件など）
- 画面下に中立なお知らせ「ただいま一部の表示を一時停止しています。…」を出す（`css/cx-maintenance-notice.css`。どのセクションがWPかは名指ししない。×で閉じるとそのタブでは再表示しない。スマホのドロワーより下）
- 自動ビルド（`build-c-columns`）はこの行を見て何もせず終わる（取り込み・コミットをしない）
- ⚠️ WP を使うページは必ず `wp-config.js` を **WPを読む部品より前**に読み込む（現在は index / news / news-detail / recruit / services/creative-x の5ページ。Creative X は `tools/build-services.py` の `GROUP_ASSETS` で入れる）。新しくWPを読むページ・部品を作ったら同じようにする
- ⚠️ 行の書式（`  maintenance: false,`）を変えない。ワークフローが `grep` で判定している
- ⚠️ WordPress 画像（`/wp-content/uploads/`）は止めない（静的ファイルのため）
- ⚠️ これはサイト側の表示を守るだけで、WordPress サーバー自体は守らない。サーバー側の対応は非公開の運用手順で行う

### WP 管理画面メニュー・CORS（2026-06-12 再編）
- 左メニュー階層ルール: **複数サービス共通**（漫画事例・ニュース・コラム）= 最上階層 / **サービス専用** = サービス名親メニュー配下（ビズマンガ > お客様の声・赤ペン・ネーム）。親メニューは `add_menu_page('cxcms-bizmanga')` ＋ CPT側 `show_in_menu` で実現
- CORS許可オリジン: `contentsx.jp` / `www.contentsx.jp` / `bizmanga.contentsx.jp` / `ichioshi.contentsx.jp`（イチオシ採用、2026-07-09ドメイン改名）/ `recruitx.contentsx.jp`（旧ドメイン、移行期間中残置）
- **掲載先の多サイト化（2026-06-12）**: ニュース・コラムの掲載先がチェックボックス複数選択（BizManga/ContentsX/イチオシ採用）に。保存値はCSV、旧値 `both`=B+C固定で後方互換（`cxcms_show_site_list()`）。`/columns?site=ichioshi` `/news?site=ichioshi` が利用可能。移行時にライブ全64件で新旧フィルタ結果の完全一致を検証済み
- **リクルートX→イチオシ採用 改名（2026-07-09）**: サイトキーの正式名を `recruitx`→`ichioshi` に変更。旧キーはDB保存値・APIパラメータとも `cxcms_normalize_site_key()` で読み込み時に `ichioshi` へ正規化（DB移行不要・`?site=recruitx` も引き続き動作）。新規保存は常に `ichioshi`。WP管理メニューは「イチオシ採用」（スラッグ `cxcms-ichioshi`）。CPT `rx_case`・タクソノミー `rx_case_tag`・メタキー `rx_case_*` はDB結合のため旧名維持
- 新サービスのWP取り込み手順はルートの **wp-service-onboard スキル**（`.claude/skills/wp-service-onboard/`）参照

### WP 編集可能フィールド
- `cx_title_en` / `cx_subtitle_ja` / `cx_subtitle_en`
- `cx_pages` / `cx_client` / `cx_point` / `cx_comment`
- `cx_sort_order` — 表示順（**数字が小さい＝先に表示**）
- `cx_show_hero_site` — Heroカルーセル表示先（both/bizmanga/contentsx/none）
- `cx_show_new_contentsx` — 新作情報表示フラグ
- **クイック編集対応**: 漫画事例一覧で「サブタイトル」列＋クイック編集から `cx_subtitle_ja` / `cx_subtitle_en` を直接編集可（contentsx-cms.php `quick_edit_custom_box` + `cx_qe_subtitle_*` を inline-save で保存。通常編集画面の保存とは別経路）

### 漫画PDFの一括分割（2026-08-04 新設）⭐

漫画家の納品が「複数ページを1本にまとめたPDF」のため、**管理画面から全ページを一括でWebP化してギャラリーへ入れる**機能。漫画事例の編集画面、ギャラリー欄の「PDFから一括取り込み」ボタン。

**処理の流れ**: PDFを選択 → `cxcms_pdf_info`（Imagick `pingImage` でページ数取得）→ `cxcms_pdf_split_page` を**1ページずつ**呼ぶ → 各ページをWebP化してメディア登録 → `cx_gallery` へページ順に追加。

- **1リクエスト1ページ**。タイムアウトとメモリ枯渇を避けるため一括処理はしない。進捗は「変換中… 3 / 10 ページ」と表示
- ファイル名は `{元PDF名}-p01.webp` のゼロ埋め連番。既存の「ファイル名の数字で並べ替え」ロジックにそのまま乗る
- 既存のギャラリー画像は消さず**追加**される。取り込み後に**投稿を保存するまで確定しない**
- 失敗時はそこで停止し、「何枚目で失敗したか・何枚は取り込み済みか」を表示（途中まで残る）

**設定値**（`define` で上書き可）:

| 定数 | 既定 | 根拠 |
|---|---|---|
| `CXCMS_PDF_DPI` | `150` | 元PDFの埋め込み画像が概ね100〜160ppi。150/200/300dpiを実測比較し、**150超は容量が増えるだけで画質は変わらなかった**（300dpi q92 は 6.13MB/10P、150dpi q85 は 2.02MB/10P） |
| `CXCMS_PDF_QUALITY` | `85` | q75(1.44MB)でも十分だが、差0.6MBで安全マージンを取る |
| `CXCMS_PDF_MAX_PAGES` | `200` | 暴走防止 |

**サーバー要件**: Imagick + Ghostscript。2026-08-04 に本番実測（Imagick 3.8.1 / Ghostscript 9.54.0）で**実PDFのラスタライズ動作を確認済み**。
⚠️ ただし**中身が空のダミーPDFではサムネイルが生成されなかった**（イチオシ採用側の検証）。「PDFサムネが出ない＝機能しない」と即断しないこと。実データで判定する。
⚠️ Imagick の `policy.xml` でPDFが禁止されている環境では動かない。その場合 `cxcms_pdf_info` が「サーバー側でPDF処理が許可されていない可能性」を返す。

**実装上の注意**:
- `setResolution()` は **`readImage()` より前**に呼ぶ（後だと効かない）
- 透過PDF対策に `setImageBackgroundColor('white')` + `flattenImages()`（省くと透過部分が黒くなる）
- 生成WebPは既存の `image_editor_output_format` フィルタとは**別経路**（Imagickで直接WebP出力するため）

### ニュース（cx_news）の編集可能フィールド
- `cx_news_title_en` / `cx_news_content_en` / `cx_news_url`
- `cx_news_show_site` — 表示先サイト。**2026-06-12 チェックボックス複数選択化**: 新形式はCSV（`bizmanga,contentsx,ichioshi` 等）、未チェック=`none`。旧値 `both` は「BizManga+ContentsX」の意味で固定（ichioshiには出ない）。旧キー `recruitx` は読み込み時に `ichioshi` へ正規化（2026-07-09改名）。コラム `cx_column_show_site` も同形式
**画像表示設定（top/detail 別々に保存）**
- `cx_news_image_mode_top` / `_mode_detail` — `contain`（全体表示）か `crop`（トリミング）
- `cx_news_image_crop_x_top` / `_y_top` / `_w_top` / `_h_top` — ホーム/一覧用のトリミング範囲（全て0-100%）
- `cx_news_image_crop_x_detail` / `_y_detail` / `_w_detail` / `_h_detail` — 詳細ページ用のトリミング範囲
- 旧 `cx_news_image_mode` / `_crop_*` / `_fit` / `_position` — 後方互換のため残置（top/detail未設定時のフォールバック）

**WP管理画面**: 「画像表示の調節」`<details>` 折りたたみボタンを開くと、「ホーム・一覧表示」「記事詳細ページ」の2ブロックが現れる。各ブロックに「全体表示／トリミング」のセグメントコントロール風タブ + Cropper.js (CDN 1.6.1) のクロップUI + リアルタイム表示プレビュー。1200px以上で2ブロック横並び、それ以下は縦並び（サイドバー幅対応）

**フロント描画**:
- `wp-api.js`（一覧描画）→ `image_mode_top` + `image_crop_*_top` を使用、なければ旧 `image_mode` 系にフォールバック
- `news-detail.html`（詳細）→ `image_mode_detail` + `image_crop_*_detail` を使用、なければ旧 `image_mode` 系にフォールバック
- `mode=contain` → `<img>` で width:100% height:auto（行幅は揃い、画像高さは画像比追従）
- `mode=crop` → `<div role="img">` + `aspect-ratio` + `background-image/size/position` で範囲再現

**CSS**: `.news-thumb` は `width: 200px / max-height: 280px / align-self: flex-start`（SP は 100px）

## 7. ヘッダー/ナビ仕様

### 7.1 モバイルヘッダー必須ルール ⭐再発防止
スマホでハンバーガーが押せない問題が過去に再発した履歴あり。**ヘッダー変更時は必ず以下を守る**:

1. `.hamburger` に `order: 10` + `flex-shrink: 0` + `min-width/height: 44px` + `z-index: 99999`
2. 言語ボタンは `width: 44px; height: 32px` 程度に縮小
3. `.header-right` は `gap: 8px` + `flex-wrap: nowrap` + `min-width: 0`
4. `.header-inner` の padding は 16px 以下
5. `touchend` イベントも `click` と一緒に登録（iOS Safari対策）
6. **`.header` に `isolation: isolate`** + `.header-right` に `position: relative; z-index: 10`
7. **320px (iPhone SE) まで想定**
8. メニューの開閉とリンク選択後の閉鎖は `js/nav.js` のみが担当する。`js/script.js` に同じ `#hamburger` / `#nav` のハンドラを置くと1回のタップで開閉が相殺される（会社概要・ニュース・ニュース詳細でスマホのメニューが開かなかった。2026-10-11 修正、Issue #17）。
9. `.header` に `backdrop-filter` / `transform` / `filter` があると、中の `position:fixed` のドロワーの基準がヘッダーになり、タブレット幅（769〜1280px）でメニューが88pxに押し込められる（BUGS #063）。メニュー表示中（`body.nav-locked`）はヘッダーのぼかしを外す。

### 7.2 ドロップダウン仕様
- PC: hover で展開
- モバイル: 1回目タップで展開、2回目タップで遷移
- 同時に1つだけ開く（他のドロップダウンは自動で閉じる）
- `touchend` ハンドラで iOS 対応

### 7.3 現在のメニュー構成
```
ホーム | 企業案内 ▾ (Contents Xについて / トップメッセージ / 会社概要 / 役員紹介 / 主要関連会社) | コラム | 採用情報 | お問い合わせ
```
- ⚠️ 「強み」は一時削除中（BizManga特化のため）→ 他事業展開後に全面刷新してメニュー復帰予定

### 7.5 共通フッター（2026-10-08 統一、Issue #87）
- 全ページ同じHTML・同じCSS（`.cx-footer`、`css/site-footer.css`）。各ページの `</head>` 直前で最後に読み込み、旧フッター（`.footer` / `.ax-footer` / `.cxh-footer`）のCSSとは干渉させない。旧フッターのCSSは未使用のまま残っている。
- 参考: レバレジーズ株式会社のコーポレートサイトのフッター。濃紺（`--cx-color-ink` #07143b）の面に白抜きロゴ。
- 構成: 左＝ロゴ＋小さなリンク2段（会社概要・私たちについて・ニュース・採用情報・お問い合わせ／よくあるご質問・プライバシーポリシー・利用規約・Chrome 拡張機能）、右＝Sales X・Creative X のサービス一覧2列（外部サイトへのリンクは左上に角の印＋別タブ）、下＝`© 2026 Contents X Inc.`。住所・会社名の文字表記は置かない（会社概要・構造化データに記載）。
- 768px以下は縦積み。リンクの高さは44px以上。各リンクに `data-ja` / `data-en`。
- 上部の小さなお問い合わせ導線 `.cx-footer__contact`（Issue #94）: 「まずはご相談ください／利用するサービスが決まっていなくても構いません。」＋白枠の「お問い合わせ」ボタン（`/contact`）。濃紺の面はそのまま、下に区切り線。768px以下は縦積みでボタン全幅。
- **専用CTAがあるページでは導線を出さない**: そのページのCTAセクション（またはお問い合わせフォーム）に `data-cx-page-cta` を付けると、`body:has([data-cx-page-cta])` で導線が消える。現在の付与先: 共通CTA `#cxCtaMount`（会社概要）、採用のエントリー `.rc-entry`、採用エントリーフォーム `#recruitEntryForm`、サービス一覧の `.cxsd-contact`（`service-list.html.tpl`）、FAQの `.faq-cta`、私たちについての `.ax-contact`、Sales X / Creative X の `.cxg-contact`（`service-group-*.html.tpl`）、拡張機能の `.ext-cta`、お問い合わせの `#contactForm`。下層ページに専用CTAを新設したら同じ属性を付ける。
- **変更するときは3か所を同じ内容にする**: 静的ページ全部（`<footer class="cx-footer">` を一括置換）、`tools/templates/c-column.html.tpl`（コラム記事の生成元）、`services/index.html`（`tools/build-services.py` がサービスページへ複製）。置換後に `python3 tools/build-services.py --check` で差分がないことを確認する。
- サービス名・遷移先は `data/services.json` と `js/nav.js` に合わせる（サービスを増減したらフッターも直す）。

## 7.4 コラム機能（2026-05-08 新設）
- 個別記事は WP CMS → `tools/build-c-columns.py` → `column/{slug}.html` で静的生成（既存）
- 個別記事の**検索結果・SNS 向けのタイトルと説明文**（`<title>`・`og:title`・`twitter:title`／`description`・`og:description`・`twitter:description`・JSON-LD の `description`）は、WP のコラム編集画面の「SEOタイトル」「SEO説明文」（API の `seo_title` / `seo_description`）を優先し、空なら記事タイトル・抜粋・本文の冒頭を使う。2欄とも先に1000字で切り（極端に長い値でビルドが止まらないように）、タグを外し、WP が保存時に変えた `&lt;` などを文字に戻し、空白をまとめる。SEOタイトルの末尾に編集者が書いたサイト名（「｜ContentsX」「｜ビズマンガ」「｜コラム」など）は外し、60字を超えると58字＋「…」に縮めて末尾に「｜ContentsX」を付ける（B と共有する記事でも二重にしない）。説明文は130字まで。JSON-LD の中（`headline`・`description`・`articleSection`・パンくずの `name`）は `{{…_JSON}}` の差し込みで JSON の書き方にする。差し込みは1回でまとめて置き換える（WP の値に `{{CONTENT}}` などが書かれていても展開しない）。見出し h1・JSON-LD の `headline`・パンくず・一覧カードは記事タイトルと抜粋のまま（2026-10-26 Issue #178。それまで欄は保存されるのに使われていなかった）。この2欄は管理画面でだけ入れられる（REST からは書けない）
- WP API は `?site=contentsx` フィルタで取得（`show_site` が `contentsx` または `both` の記事のみ）。⚠️ 過去に `contentx`（sなし）と誤記しC向けコラムが0件になっていた（BUGS.md #041、2026-06-12修正）
- 一覧ページ `column.html` も build-c-columns.py が自動更新（Featured 1本 + カードグリッド + カテゴリチップ + ItemList JSON-LD）
- マーカー: `<!-- BUILD:COLUMN_GRID -->` ... `<!-- /BUILD:COLUMN_GRID -->`
- `/column/` アクセス時は `column/index.html` の meta refresh で `/column` (= column.html) へ転送
- ⚠️ **2026-09-29 から導線だけ一時非表示**: 共通ナビ（`js/nav.js`）の「コラム」をコメントアウトした。一覧 `/column`・記事 `/column/{slug}`・sitemap・llms.txt・feed・WP からの自動ビルドは**そのまま公開**（URL を直接開ける・検索にも残る）。他ページからコラムへのリンクはナビの1か所だけだった。戻し方と経緯は [CORPORATE-PAGE-VISIBILITY.md](CORPORATE-PAGE-VISIBILITY.md)「コラムの導線」
- `--skip-listing` で個別ページのみ生成可能

## 8. 制作事例モーダル（2026-09-29トップから撤去）

- `openWorkDetail(workId)` で起動していた（`hero-new.js`。2026-10-29 にファイルごと削除。以下は記録）
- カルーセル: 1ページ目の縦横比で縦読み(vertical-scroll)/カルーセル切替
- **スマホ対応**: 横スワイプでページ切替（閾値40px、縦スワイプ優先）
- タイトル+カテゴリタグ: `.work-detail-title-row` で flex 横並び

## 9. 採用ページ（recruit.html）

### 9.0 ヒーロー（2026-10-11 刷新、#125）
- 構成: 白基調。左にコピー（`RECRUIT`＋「採用情報」／見出し「きっかけを、つくる側へ。」／サブ「ビジネスとクリエイティブの未来を、一緒につくっていこう。」／ボタン「募集職種を見る」→ `#positions`・「会社を知る」→ `/about`）、右にXのコラージュ画像。右下に補助コピー「コンテンツで社会に、もっといいきっかけを。」。クラスは `rc-xhero__*`（`css/recruit.css`）。
- 画像: `material/images/recruit/recruit-hero-x-collage.webp`（1672×941）。`<head>` で preload。HTML 内の SVG に3回出てくる `href` は同じファイル（1回だけ読み込まれる）。
- **Xの書き順アニメーション**: 1画目＝＼（左上→右下）→ 2画目＝／（右上→左下）。SVG の中で画像を「Xを抜いた土台」と「帯2本」に分け、帯ごとに太い線のマスクを `stroke-dashoffset` で端から端へ伸ばして“描く”。1画目 0.1s 開始・2画目 0.45s 開始、各1.0s（全体約1.45s）。描画中は帯の透明度を 0.3→1 に。補助コピーは描き終わりにフェードイン。初回表示時に1回だけ。
- 画像の読込が遅いとき: `js/recruit.js` が `.is-waiting` を付けて描画を止め、読込完了（失敗・4秒経過でも）で外して最初から描く。JS が無くても最終状態（X全体が見える）で表示される。
- `prefers-reduced-motion: reduce` では動かさず最初から全体を表示。
- **スマホ（768px以下、#152）**: 書き順アニメーションはせず、Xの画像全体を0.8秒で軽くフェードイン（下から12px）。太い線のマスクを毎コマ描き直す演出はスマホのGPUで引っかかりやすいため。画像の幅はボタンと同じ（左右の余白 `--rcx-gutter` をそろえる、最大480px）、下端はマスクで次のセクションへなじませる。PC・タブレット横は従来どおり書き順。
- ⚠️ **画像を差し替えるときは、SVG の `polygon`（帯の形・2箇所ずつ）と描画線 `path` の座標、CSS の `stroke-dasharray`（1画目 1355／2画目 1506＝線の長さ）を測り直す**。帯の形の境界が写真の端にぴったり重なると、描画前に細い線のノイズが出る（境界は写真の外側の白地に置く）。
- レイアウト: PC と横長タブレットは画像を全面に敷き（右寄せ `xMaxYMid slice`）、左に薄い白のグラデーション（`.rc-xhero__veil`）。**767px 以下と、1023px 以下の縦長画面**はコピー→ボタン→画像の縦積み（縦長で全面にするとXが大きく切れてコピーと重なるため）。
- 899px以下は §9.8 のコンパクトな縦積みを優先する。
- サブコピーと補助コピーは `<wbr>` を入れた文節の切れ目だけで改行（`word-break: keep-all`）。Android の文字拡大1.4倍・320px でも1文字だけ落ちないことを確認済み。
- 旧ヒーロー（写真＋「Careers」＋職種・会社・選考フローのボタン群、`rc-hero*` / `rc-pill`）は撤去。旧画像 `material/images/recruit/hero.webp/.avif` はどこからも参照されなくなったが残置。

### 9.1 ページ構成とモーション（2026-10-12、#127）
- 構成: HERO → 募集職種（`#positions`、募集要項はこの中で開く）→ 選考（`#flow`）→ エントリー（`#entry`）→ TOPICS（`#topics`、トップと共通）→ フッター。
- **共通背景（`.rc-stage` / `.rc-stage__bg`）**: 募集職種・募集要項・選考・エントリーは親 `.rc-stage` の中にあり、背景写真はその最初の子 `.rc-stage__bg` の1枚だけ（`recruit-positions-bg.webp`、640px以下は `-sp` を上寄せ・高さ520px）。`position: sticky; height: 100lvh; margin-bottom: -100lvh` で画面に貼り付き（⚠️ この形だと最後に親の下へ最大1画面分はみ出してフッターを覆うため、`.rc-stage` に `clip-path: inset(0)` を付けて描画を親の中に切り取っている。消さない＝BUGS #066、#156）、上を中身が流れるので、境目・繰り返し・位置のリセットが出ず、募集要項を開いてページが伸びても途切れない。白いオーバーレイ（`::after`）は旧 `.rc-op__bg` のものをそのまま使う。⚠️ セクションごとに背景画像を置かない。各セクションの `background` は透明のまま。最後は `.rc-stage::after` で淡い青（#f2f7fd）に溶かし、TOPICS の上端のグラデーション（同色）へつなぐ。旧ページの「職種カード選択で背景が切り替わる演出」「応募する／詳細を見るのボタン列」「共通CTA（`cta.js`）」は撤去。
- **スマホ（768px以下）の背景文字（#152）**: 画面上部に固定すると見出し・本文と重なって読みにくいため、固定をやめて各セクション（`data-cxsb-name` の `::before`、TOPICS は元の `.cxsb-label`）の上の余白に置く。大きさ・色はトップのスマホの TOPICS と同じ（`clamp(52px, 18vw, 130px)`、`rgba(21,88,161,.09)`）。セクションの上の余白は「欧文の大きさ×0.78＋30px」で、見出しは欧文の下から始まる（その分セクションの間が広がる）。
- **大きな背景文字（#135）**: トップと同じ見た目・仕組み（`js/home-section-labels.js` と `css/home-sections.css` の `.cxsb-name`）。募集職種＝`POSITIONS`／選考＝`PROCESS`／エントリー＝`ENTRY`（各 `section` の `data-cxsb-name`）、TOPICS は従来の `.cxsb-label`。共通背景 `.rc-stage__bg`（`data-cxsb-names-host`）の中に、画面の上から40%の線にいるセクションの名前だけを画面上部に固定で出し、切り替えは0.2秒のフェード。HERO には出さない。JS無効時は出ない（飾りのため）。
- 方針: 特徴的な演出は要所だけ（HERO の X、HERO→募集職種の日差し）。ほかは `MOTION-UI-2026.md` の「1回だけ下から24px・0.75秒」。スクロールを止める・吸着させる処理は入れない。
- 登場演出の仕組みは下層ページ共通の `js/sitewide-motion.js`（対象: `.rc-op__intro` `.rc-op-item` `.rc-sel__head` `.rc-sel__step` `.rc-entry__inner` `.cxtp-head` `.cxtp-list`）。職種カードは 0 / 0.14 / 0.28 秒、選考カードは PC で 0 / 0.12 / 0.24 / 0.36 秒の時間差（`css/recruit.css`）。選考の線とエントリーの紙飛行機の軌跡も、この登場クラス（`.cx-motion-pending` → `.cx-motion-visible`）に連動して CSS だけで1回描く（専用のJSは無い）。
- スクロール量で動くのは「日差し」だけで、監視は `js/recruit.js` の1か所（画面内のときだけ計算・passive・requestAnimationFrame）。毎フレーム書く CSS 変数は子要素のない要素に置く（`sitewide-motion.js` が style の変化を監視しているため）。
- 動きを減らす設定・JS無効: どれも最終状態で表示（日差しは完成した背景、線と軌跡は描き終えた状態、募集要項は全件表示）。読込時にすでに画面内にある要素も最初から最終状態。
- 旧カード背景画像 `material/images/recruit/{manga,production,sales}.webp/.avif` は参照されなくなったが残置（BizManga からの参照なし）。

### 9.2 募集職種（`.rc-op`）
- 見出し「OPEN POSITIONS」「その一歩が、新しい価値をつくる。」、リード「クリエイティブ、ビジネス、テクノロジー。それぞれの力で、コンテンツの未来を一緒につくりませんか。」、右上に飾りの英字（PCのみ）。
- カードは共通部品 `.cx-feature-card cx-feature-card--row-sp`（`css/feature-card.css`、#141。`--row-sp` で899px以下は横長。見た目と状態は部品側、並べ方・時間差・募集要項の開閉は `css/recruit.css` / `js/recruit.js`）。
- 職種カードは3枚（この表示名を保つ）: 01 漫画家 / 漫画制作（CREATIVE）／02 営業（SALES）／03 エンジニア（ENGINEERING）。画像は `material/images/recruit/recruit-position-{manga,sales,engineer}.webp`（800×1000、AI生成のイメージ素材なので alt は空＝装飾扱い。実在の社員・オフィスとして説明しない）。PC 3列、900〜1023pxは2列＋下段中央1枚。899px以下は1列の横長カード（左に写真・番号、右に職種名・短い説明・詳細リンク）。丸い矢印と大きな詳細ボタンの重複をなくし、3職種を比較しやすくする（#129）。
- カードの下部ボタンは「詳細を見る」（カード全体が `#detail-xxx` へのリンク）。JSがあるときは、カード一覧の直下（`.rc-req`、募集職種セクションの中）にその職種の募集要項だけを開く（漫画家 / 漫画制作は「漫画家」「マンガ製作担当」の2件を別々のパネルで、応募ボタンもそれぞれ）。別の職種を押すと同じ場所で切り替わる。同じカードをもう一度押す・「募集要項を閉じる」・スマホの要項冒頭の「職種一覧に戻る」・パネル内で Esc で閉じる（閉じるボタン／Esc では元のカードにフォーカスを戻す）。開くと詳細の先頭が固定ヘッダーに隠れる位置か画面の下60%より下にあるときだけスムーズスクロール（`scroll-margin-top: 88px`、動きを減らす設定では瞬時）。開閉は `aria-expanded` と、画面には出ない `role="status"` の文（「〇〇の募集要項を開きました／閉じました」）で伝える。カードは Enter / Space で開閉できる。`/recruit#detail-sales` などの直リンクでも開く。開いた詳細は 0.5 秒のフェードイン（下から8px）。
- 職種を選んでも背景は切り替えない（共通背景 §9.1）。日差しの光の帯（`.rc-op__light`）は高さを固定しているので、募集要項を開いてセクションが伸びても帯が伸び縮みしない（再度差し込むように見えない）。帯の下端はマスクで消して選考との境目に切れ目を出さない。
- 採用区分（新卒・正社員・インターン等）は確定したらカードの `.cx-feature-card__types` に `<span>正社員</span>` のように入れる（空なら非表示）。募集要項にも `data-hiring-types` を用意。⚠️ 確定していない条件・応募資格・報酬・雇用形態・応募先は書かない。
- **営業・エンジニアは長期インターンの募集**（2026-10-12、#127）: 募集要項は ゼロワンインターンの掲載と同じ内容（営業 https://01intern.com/job/7846.html ／エンジニア https://01intern.com/job/7845.html）。行は 業務内容／応募条件／勤務形態／勤務地／報酬／選考。カードには区分「長期インターン」を表示（`.cx-feature-card__types`）。応募ボタンは `/recruit/entry?position=職種&type=インターン`。JSON-LD は営業 `["INTERN","CONTRACTOR"]`（業務委託）・時給1,500〜1,700円、エンジニア `INTERN`（雇用契約）・時給1,300〜1,500円。⚠️ **掲載側の条件を変えたら、ここの募集要項と JSON-LD もそろえる**（電話番号は載せない）。
- **日差し（このセクションだけ）**: 背景写真 `recruit-positions-bg.webp`（スマホは `-sp`）は静止。その上の白いベール（`.rc-op__veil`）と光の帯（`.rc-op__light`、淡いブルーとオレンジのグラデーション）だけが、セクション上端が画面下端に入ってから画面の上から22%に来るまでのスクロール量（0→1、`--rcop-p`）で変化する。白が主体 → 写真が見え、光が右上から現れて左下へ72px滑りながら広がる（PCは光の届く範囲もマスクで右上→左下に広げる。スマホは不透明度と移動だけ）。光の不透明度は最大0.3（背景写真にも斜線があるため）。値の段差は `@property` の transition 0.45秒でならす。戻りスクロールは同じ式で逆に戻るだけなので点滅しない。カードの操作では再生されない。

### 9.3 募集要項（`.rc-req` / `.rc-detail`）
- id（`detail-manga` / `detail-production` / `detail-sales` / `detail-engineer`）は JSON-LD の `url` と対応しているので変えない。応募ボタン「この募集に応募する」は採用専用フォーム `/recruit/entry?position=職種名`（希望職種が選ばれた状態で開く。§9.7）。

### 9.4 選考（`.rc-sel`、PROCESS）
- 見出し: `PROCESS`／「選考について」／リード「お互いをよく知るための、シンプルで透明性の高いプロセスです。あなたの想いとこれまでの経験を、ぜひ聞かせてください。」。右に手書き風のサブコピー「一緒に、これからのコンテンツをつくろう。」（`.rc-sel__note`、Google Fonts の Zen Kurenaido を `text=` で使う文字だけ読み込み。⚠️ 文言を変えたら `<head>` のフォントURLの `text=` も変える）。
- ステップ（仮案）: 01 書類選考／02 カジュアル面談／03 面接（1〜2回）／04 内定。各カードに青い番号・青い線のアイコン（インラインSVG）・名前・説明。文字はHTMLテキスト。
- PC（900px以上）: 4枚を横一列・同じ高さ。カードの間を細い青線＋両端の小さな丸でつなぐ（`.rc-sel__step::after`）。カードが表示されたら、線が左→右へ順に1回だけ伸びる（`clip-path`）。899px以下: 縦に積み（左に番号とアイコン、右に文字）、線も縦向き。スクロールしてカードが現れるたびに、その下の線が上→下へ伸びる。
- ⚠️ **ステップの文言はデザイン上の仮案**（新卒・正社員・インターン向けを想定。旧ページの業務委託向けの「トライアル」「契約・参画」は外した）。**公開前に正式な採用フローと照合する**。募集要項の勤務形態（業務委託）や JSON-LD の雇用形態とのずれも合わせて確認する。

### 9.5 エントリー（`.rc-entry`）
- 半透明の白い横長パネル（`.rc-entry__inner`）。左に `ENTRY`／「エントリーはこちら」／「少しでも興味を持っていただけたら、まずは気軽にご応募ください。あなたからのご連絡をお待ちしています。」／ボタン「採用に応募する →」。右に青い紙飛行機と細い軌跡（インラインSVG）。軌跡はパネルの登場に合わせて1回だけ描かれ、紙飛行機は描き終わりに現れる（ループしない）。899px以下は1カラム。紙飛行機はパネル右上の88px幅の装飾とし、文章の前に専用の高さを取らない。ボタンは全幅（#129）。
- ボタンの行き先は採用専用フォーム `/recruit/entry`（§9.7）。法人お問い合わせ `/contact` には向けない。職種別の応募は募集要項の「この募集に応募する」（`?position=職種名` 付き）。ボタンの反応は共通の `.cx-ui-action`（ホバー・フォーカスで上に2px、矢印が4px右へ）。

- ページ専用CTAなので `data-cx-page-cta` を付け、フッター上の営業向け相談導線は出さない。

### 9.6 TOPICS（トップと共通）
- `index.html` の TOPICS と同じマークアップ・`css/home-topics.css`・`js/home-topics.js`・`js/wp-config.js`・`css/home-sections.css`（共通背景）。記事はトップと同じ WordPress「Contents X ＞ TOPICS」（WP側の更新が両ページに出る）。PCの横スクロールと矢印、スマホの横スワイプ、ホバー・登場演出もトップと同じ部品のまま。⚠️ JS無効・取得失敗時の3件は `index.html` と同じ内容に揃える。
- 採用ページ側の調整は `css/recruit.css` に限定する: TOPICS 上端のグラデーションを共通背景の最後と同じ淡い青（#f2f7fd）から始め、`top: -1px` で、上端が小数ピクセルのときに固定背景（`.cxsb-backdrop`）が線のように覗くのを防ぐ。トップ用のファイルは変更しない。カードに `position: relative` を指定し、画面外カード内の読み上げ用テキストがページ全体の横幅を広げる不具合を防ぐ（#129）。
- ローカル（localhost）では WordPress の CORS で記事が取れず、フォールバックの3件が出る（本番ドメインでは取得できる）。

### 9.7 採用エントリーフォーム（`/recruit/entry`、2026-10-12、#128）
- **法人のお問い合わせ（`/contact`）と採用の応募は別のフォーム**。採用ページの「採用に応募する」と募集要項の「この募集に応募する」はここへ来る。旧リンク `/contact?position=…` は `contact.html` の `<head>` で、広告計測より先に `/recruit/entry`（パラメータはそのまま）へ転送する。
- ファイル: `recruit/entry.html`・`css/recruit-entry.css`・`js/recruit-entry.js`。入力欄の見た目は共通の `css/form.css`／`.cb-submit`、送信の部品（空白だけの入力の検査・流入元の付記・HubSpot 送信・二重送信防止）は `js/form-common.js`（`window.cxForm`、お問い合わせと共用）。GitHub Pages は `/recruit` に `recruit.html`、`/recruit/entry` に `recruit/entry.html` を返す（`/column` と `column/` の並存で本番確認済み）。⚠️ このページの `href`／`src` は必ず `/` 始まり。
- 項目（新卒・正社員・インターン共通。募集状況に依存しない）: 応募区分（新卒／正社員（中途）／インターン、必須。希望職種と同じプルダウンでUIをそろえる、#131）・希望職種（漫画家／マンガ製作担当／営業／エンジニア／その他・未定、必須。⚠️ 募集職種を増減したら `recruit/entry.html` の選択肢と募集要項のリンクの `position` を揃える）・お名前（必須）・ふりがな・メール（必須）・電話・学校名・所属・卒業（予定）年月・ポートフォリオ／経歴のURL・志望動機／自己PR／ご質問（必須）・プライバシーポリシーへの同意（必須）・ハニーポット `#cxWebsite`（値があれば送らずに完了表示だけ）。ファイル添付は無し（URLで受ける）。
- **営業と混ざらないための決まり**: CRM（ビズカルテ）の貼り付けコードを読み込まない／送らない。Google広告のお問い合わせコンバージョン（到達・送信完了）を出さない。HubSpot の追跡スクリプト（フォームの自動収集）を読み込まない。計測は GA4 のイベント `recruit_entry_submit`（`hiring_type`・`position`）だけ。`noindex, follow`（フォームだけのページのため、sitemap にも載せない）。
- ⚠️ **送信先は暫定**: 採用専用の受付先がまだ無いため、今までの採用応募と同じ HubSpot の B/C 共通お問い合わせフォーム（`b6da14d0-…`）に送っている（`js/recruit-entry.js` 先頭の `RECRUIT_HUBSPOT_FORM_GUID`）。受け取った側で見分けられるよう、本文の先頭を「【採用応募】区分／職種」にして全項目を項目名つきで並べ、部署（`busyo`、フォーム側で必須）に「採用応募（区分）」、会社名（`company`）に学校名・所属（空なら「（個人）採用応募」）を入れる。**HubSpot の通知先は法人お問い合わせと同じになり、連絡先も同じポータルに作られる**。採用専用のフォーム（GUID）と通知先が決まったら、この1行を差し替え、ここと §6 を直す。
- 完了表示はページ内（「ご応募ありがとうございます。」＋採用情報へ戻る）。資料DLの案内や `cx_form_submitted` の保存はしない（法人向けの仕組みのため）。
- 入力欄は480px以下でも16px（form.css は14pxにするが、iPhone は16px未満だと入力時に画面を拡大するため）。タップ領域は応募区分・職種・送信とも48px以上。

### 9.8 スマホの情報量・読みやすさ（2026-10-12、#129）
- 対象は899px以下（スマホ〜小型タブレット）。見出しは `clamp()` の連続スケール。冒頭の上下余白を縮め、主要CTA「募集職種を見る」は全幅、「会社を知る」は44px以上のテキストリンクにする。X画像は全体を保って最大320px幅に収め、画像上の補助コピーを非表示にする。
- 職種一覧は写真付きの横長カード。固定高を使わず、英語・文字拡大に応じて伸びる。写真は独立した列、文字は `min-width:0` で縮められる。カード全体がタップ対象。
- 募集要項・職種説明・選考・エントリーの本文は16px以上。要項はラベル→本文の縦並び。本文には `text-size-adjust` による文字拡大抑制を入れない。
- 募集要項の上下に閉じる導線を用意する（上はスマホだけ）。開くと上の「職種一覧に戻る」が見える位置に移動し、閉じると選択元へスクロール・フォーカスを戻す（カードの `scroll-margin-top:88px` で固定ヘッダーに隠れない）。JS無効時は全要項が表示され、閉じるボタンはhiddenのまま。
- 選考の手書きサブコピーはスマホで非表示。4ステップの説明は維持し、間隔を20pxにする。エントリーは装飾のための専用行をなくし、CTAまでの距離を短くする。
- WebKitの短時間の履歴更新回数制限で `history.replaceState` が例外になっても、開閉とフォーカス復帰は続ける。URL更新は補助状態として扱う。
- Safari系でも選考カードの説明が枠からはみ出さないよう、`.rc-sel__text` は幅100%・`minmax(0,1fr)` を指定する。
- 募集条件・応募先・記事データは既存の内容を使う。スマホ専用の短縮文章は作らない。


## 10. お問い合わせボタン（送信ボタン）

- `cb-submit` クラス: 紙飛行機アイコンのhover拡張ボタン
- 右端の丸アイコンが **hover で横に伸びて** ボタン全体をカバー
- 共通スタイルは `style.css` に定義（全ページ利用可）

## 11. パートナー企業ロゴ

[CORPORATE-PAGE-VISIBILITY.md](CORPORATE-PAGE-VISIBILITY.md) に非表示箇所と復帰手順を記録。`partners.html` は現在転送のみで、以下は旧ページの素材に関する記録:
- 旧掲載: DM Solutions / KIRINZ
- **ASOBISYSTEMは2026-07-08にコメントアウトで非表示化**（`TEMP-HIDDEN-ASOBI-SYSTEM`マーカー、HTML内に残置。復活は該当ブロックのコメント解除のみ）
- ロゴ画像: `material/images/partners/*.webp`
- **背景透過済み**（PIL で RGB>=240を透明化）
- `max-width: 320px` でカラム幅に収める

## 12. 既知の注意点

| 事項 | 詳細 |
|---|---|
| hreflang | **2026-04-14 全ページから削除済**（JS言語切替1URL構成のため誤実装だった。sitemap.xml からも削除） |
| image alt | hero キャラ画像に alt が無い |
| image width/height | 未指定 → CLS悪化要因 |
| description | **2026-04-14 index/news/news-detail/our-thoughts/recruit の5ページを73〜90文字に拡充**（meta/og/twitter/JSON-LD の4箇所同期） |
| Organization.sameAs | **2026-04-14 `https://x.com/Bizmanga_` 追加**。他SNSは未開設 |
| Organization 詳細 | **2026-04-14 `foundingDate: 2026-03-03` / `address`（目黒区） / `subOrganization`（BizManga） / `alternateName` を追加** |
| OG画像 | 全ページ共通で `ContentsX.webp`（ロゴ）を流用中。1200×630px の専用OGP画像が未作成（TODO） |
| data-theme | 現在 `magenta-hot` がデフォルト（`var(--accent): #FF0090`）|

### 2026-04-14 SEO改善実施

- hreflangタグを全HTML・sitemap.xmlから削除（誤実装解消）
- index.html のヒーローロゴを `<h2>` → `<h1>` に変更し、sr-only h1 を削除（見出し順序の正規化）
- `<meta name="referrer" content="strict-origin-when-cross-origin">` を全ページに追加
- ルートに [llms.txt](llms.txt) を新設（AI検索エンジン向け事業概要・主要ページ一覧）
- 5ページ（index / news / news-detail / our-thoughts / recruit）の meta/og/twitter/JSON-LD description を73〜90文字に拡充
- Organization スキーマに `foundingDate` / `address` / `alternateName` / `sameAs`（X: Bizmanga_）/ `subOrganization` を追加
- **news-detail 個別記事のインデックス対応**:
  - [tools/generate-sitemap.py](tools/generate-sitemap.py) を新設（WP APIから news 一覧取得して sitemap.xml を再生成）
  - sitemap.xml を `?id=N` 形式で個別記事URLを列挙する構成に変更
  - news-detail.html に canonical / OG / twitter / description / JSON-LD `NewsArticle` の動的更新スクリプトを追加
  - `why-contentsx.html` および `css/why-contentsx.css` を削除（2026-04-19）。元々メニューから非表示・孤立ページだったため完全撤去

### sitemap再生成ルール

ニュース記事を WordPress で追加・更新したら以下を実行:

```bash
cd ContentX
python3 tools/generate-sitemap.py
git add sitemap.xml && git commit -m "chore(sitemap): news更新" && git push
```

GitHub Actions 等で月次自動化も可能（TODO）。

### 2026-04-20 SEO採点反映改善 第2弾（81→86→90+目標）

- **画像 width/height 属性を一括追加**（CLS対策）: ヘッダーロゴなど主要画像にwidth/height明示
- alt属性欠落: 0件を確認（空alt はすべて `role="presentation"` / JS動的代入 / WP本文で問題なし）

### 2026-04-20 SEO採点反映改善（監査スコア 81/100）

**[bizmanga サブディレクトリ強化]**（6ページ）
- `contentsx.jp/bizmanga/{index,works,biz-library,pricing,faq,contact}.html` に以下を一括注入:
  - `<link rel="alternate" hreflang="ja">` + `hreflang="x-default"`（メインサイトと一致）
  - `BreadcrumbList` JSON-LD（ホーム → ビズマンガ → 該当ページ）
  - index.html のみ `Organization` + `Service` + `AggregateOffer`（lowPrice 11,300 JPY）JSON-LD も追加
- 注入スクリプト: `.seo-audit/tmp-bizmanga-subdir-patch.py`（一時ツール。再実行は冪等）

**[OG画像の個別化]**
- `ContentX/material/images/og/` に `og-faq.webp` / `og-terms.webp` / `og-privacy.webp` を新規生成（1200×630 WebP、黒背景 + 赤アクセント `#E53935`）
- `faq.html` / `terms.html` / `privacy.html` の `og:image` / `twitter:image` 参照を個別画像に差替
- 生成スクリプト: `.seo-audit/tmp-og-gen.py`（Pillow + Hiragino Sans GB）

**[ニュースfallback現行化]**
- `index.html` の news-list fallback 3件を古い日付（2026.02-03月）から WP API 最新3件（2026.03.15-03.27）に置換。リンクを `news-detail?id={id}` に接続

### 2026-04-21 郵便番号統一 + GBP登録

- **郵便番号統一**: `153-0042 / 153-0063` の混在を `153-0061`（中目黒1丁目の正式番号）に統一。修正箇所: [index.html:90](index.html#L90), [company.html:100](company.html#L100), [faq.html:185,279](faq.html#L185), [bizmanga/index.html:434](bizmanga/index.html#L434), [llms.txt](llms.txt)（3箇所）
- **GBP登録**: business.google.com に登録完了（CEO決裁取得済み）。住所認証/写真/初期投稿が次の課題。確定後に Organization schema の `sameAs` に GBP プロフィールURL追加 + llms.txt の Local SEO セクションに記載予定
- **llms.txt 更新**: Last updated `2026-04-21` / Version `1.5`
- **SEO厳格採点実施**: ルート [.seo-audit/STRICT-SCORE-2026-04-21.md](../.seo-audit/STRICT-SCORE-2026-04-21.md)。コード品質ベースの旧採点(87)から、検索可視性・Authorityを15%+5%加味した厳格採点で **68/100** に下方修正。GSC実データで「contentsx」(自社名) と「ビズマンガ」(姉妹サイト名) 以外のターゲット全てが圏外と判明

### 2026-04-17 SEO監査 第2弾

- FAQ schema内のURL typo修正（`contactsx.jp` → `contentsx.jp`）
- 全7ページのpublisher JSON-LDを `@id` 参照パターンに統一（privacy/termsと同じ形式）
- Organization schema: `sameAs` からサブドメインURL除去、`postalCode: 153-0042` 追加
- news.html の WebPage JSON-LD を `<body>` → `<head>` に移動
- leadership.html の Person `worksFor` を `@id` 参照に修正
- FAQPage schema に `dateModified` 追加
- ホームページロゴ `href="#"` → `"./"` に修正
- llms.txt に英語ファクトブロック追加（Key Facts (English) セクション）
- robots.txt に Bytespider ブロック追加
- sitemap.xml lastmod 日付更新
- WP API columns エンドポイントに `modified_ymd` フィールド追加（contentsx-cms.php）

### 2026-04-14 Medium優先度対応

- 全ページに `BreadcrumbList` JSON-LD を追加
- 全ページに `twitter:site: @Bizmanga_` を追加

## 13. テーマカラー

CSS変数 `--accent` は `data-theme` で切替可能:

| テーマ | `--accent` |
|---|---|
| デフォルト | `#6fc31c` (緑) |
| magenta-hot | `#FF0090` |
| magenta-rose | `#E91E8C` |
| magenta-deep | `#C2185B` |

### 2026年9月のページ横断デザイン

- トップページとサービスページはそれぞれの担当作業ツリーで設計する。**その他のContents Xページ全体**（会社情報、採用、お問い合わせ、ニュース、コラム、FAQ、法務ページ、404）は第三の担当範囲として統一感を維持する。別セッション間の変更・色の決定は「claude連絡網」で共有する。
- 下層ページは `css/sitewide-cohesion.css` と `body.cx-sitewide` を使用。白を土台に、濃紺 `#07143b`、Sales X の青 `#005bfa`、Creative X のオレンジ `#fa4d12` を共通の視覚語彙とする。見出し、ラベル、リンク、ボタン、淡色背景、境界線の基準をこのCSSへ集約する。
- `body[data-theme="magenta-hot"]` と旧テーマ定義は互換性のため残す。下層ページでは `body.cx-sitewide` の変数が優先する。トップ・サービスのレイアウトにはこのクラスを付けない。
- コラム静的記事は生成物と `tools/templates/c-column.html.tpl` の両方へ共通CSSを読み込む。再ビルド後も外観を維持するため、テンプレートの指定を削除しない。記事の見た目は `css/column-article.css`（2026-10-13 にテンプレートの埋め込みCSSを移動）。記事ごとのサムネイルだけは `.cx-col-hero` の `style="--cx-col-thumb:url('…')"` で渡す。
- 利用規約・プライバシーポリシーの見た目は `css/legal.css`（2026-10-13 に両ページの埋め込みCSSを移動）。
- レスポンシブ検証幅は 320/390/412/448/640/768/1024/1440px。本文はユーザーの文字拡大設定を尊重する。
- 会社概要 `company.html` の会社情報は480px以下で項目名と内容を縦並びにし、長い社名・事業内容の本文幅を確保する。481px以上は2列表示とする。
- 会社概要 `company.html` 左側の紹介文（`.company-description`）は2026-09-29に営業支援の訴求へ差し替え。見出し1行（h2 `.company-description-lead`「営業の悩みを、売上につながる仕組みに。」）＋本文3段落の構成で、各段落に `data-ja`/`data-en` を付ける。旧文「埋もれていた物語に、光を当てる」「人の手7割・AI3割」は会社概要から削除（`llms.txt`・`faq.html`・`i18n/en.json` には旧文が残っている＝未変更）。meta description・og/twitter・構造化データの説明文も営業支援の訴求に合わせ、ページ内フッターの英語社名は `Contents X Inc.` にした。
- 同日、右側の会社情報（`.company-info`）を「会社名／設立／資本金（1,000万円）／役員（代表取締役 黒宮 大貴・取締役 鵜池 航太）／事業内容（4行）／所在地」に更新。複数行の項目は `data-ja`/`data-en` に `<br>` を入れ、i18n が innerHTML で差し替える。社名の表記ゆれ（コンテンツエックス等）は表から外し、構造化データの `alternateName` に残している。
- UIとモーションの共通基準は [MOTION-UI-2026.md](MOTION-UI-2026.md)。下層ページは `js/sitewide-motion.js` がセクションの1回だけの登場演出を担う。JS無し・動きの軽減設定時は常時表示する。
- フォント・文字階層・色の役割・写真上の文字は [DESIGN-SYSTEM-2026.md](DESIGN-SYSTEM-2026.md) に集約。CSSの正本は `css/brand-system-2026.css`。下層ページは `css/sitewide-cohesion.css` の直前に `<link>` で読み込み（2026-10-13 に `@import` から変更。直列の読み込み待ちをなくすため。新しいページでも2行セットで書く）、トップ/サービス担当も同じ変数を使用する。通常サイズの Creative X 文字には `#b83806` を使い、鮮やかな `#fa4d12` は大きい見出しや装飾に限定する。
- 共通の小部品は `cx-ui-surface`（淡色面と枠）、`cx-ui-pill`（丸い外形）、`cx-ui-card`（カード反応）、`cx-ui-action`（操作反応）。ページ固有クラスは配置・内容を担当する。旧生成コラムカード `cx-col-card` の動きは生成テンプレート互換のため保持する。

### About確定画像の再現（2026-10-14、Issue #165）

- デザイン正本はユーザー指定のPC/スマホ「確定画像まとめ」ZIPに収録された00〜07。旧HERO/WHY/OUR ROLE/03–06/07の実装メモを本節に統合し、旧デザインの3枚WHY・写真付きNEXT ACTIONへ戻さない。
- 並びはHERO→WHY→OUR ROLE→MISSION/VISION→VALUES→MESSAGE→FUTURE→NEXT ACTION。見本にない重複「理念」セクションを外し、既存 `#philosophy` のアンカーだけ非表示要素で保持。ヘッダー/ナビ/フッター/SEO/JS読込順/他ページは変更しない。
- **HERO**: 明朝2行・青い「輝く。」、説明と欧文補助、人物/会議/都市の斜めコラージュ。スマホはコピーの白い斜め面と写真を重ねて連続させる。本文は12px未満に縮めず、文字拡大時はコピー領域を伸ばす。会議/CREATIVE/中央英語の装飾ラベルは #167 で非表示にし、写真内は都市の締めコピーだけに整理。人物画像の拡大配置だけmax-width上限を外す。
- **WHY**: 「価値がないのではなく、出会うきっかけが足りない。」。企業価値/人の可能性の2枚の写真に白文字を重ねる。中央の「まだ、届いていない」と下段の結論。PC2列（企業写真が広い）、899px以下は縦2枚。非操作のarticleでリンクの丸矢印を付けない。文字拡大・英語で必要な分だけ写真領域が伸びる。
- **OUR ROLE**: 3枚の共通feature-cardを維持し、写真の構図/枚数/番号/本文/青いCTA/カード間の矢印を正本に合わせる。PC3列、899px以下は写真上/本文下の1列。Creative/Sales各事業ページ、IMPACTはMISSIONへ接続（架空の第3事業は作らない）。
- **MISSION/VISION**: PCは左上コピー/右上人物写真と左下都市/右下コピーが中央Xで交差する構図。MISSION/VISIONの欧文は読める淡色ラベル。1024px以下は各コピー→写真の縦構成。MISSION側は事業一覧、VISION側はVALUESへの実リンク（独立した詳細ページは存在しないため、実際の内容を示すラベルを使う）。本文や図形を完成スクリーンショットに焼き込まない。
- **VALUES/FUTURE**: 共通feature-cardを再利用。見本に近い写真/本文の比率、番号/欧文ラベル、本文の改行、下段の補助コピー・X・青い矢印へ変更。PC3列、899px以下は写真上/本文下。VALUESは非操作のarticle、FUTUREはSales/Creative/contactの実リンク。
- **MESSAGE**: 左コピー/右の代表写真。#167から全周を淡くフェードし、上下左右の四角い境界をなじませる。主見出しと既存確定本文、正式氏名・実写真、`/message` 全文リンクを維持。見本の架空代表「田中大輔」や別人の生成顔は使わない。SPはコピー→写真（PCの読み順を保持）。
- **NEXT ACTION**: 確定ZIPのPC/スマホはどちらも「挑戦する人と、挑戦する企業のそばに。」と青/オレンジの斜めパネル。以前の写真カードとは異なる。パネル全体を `/contact` / `/recruit` のリンクとし、テキストは傾けず背景だけskew。PCはコピー左/2パネル右、899px以下は縦2枚。`data-cx-page-cta` は1つ、フッター問い合わせ枠だけAbout限定で非表示。
- **字体**: HERO・NEXT ACTION主見出しとセクション下端の理念コピーは選定画像の明朝体。ほかの見出し・本文は共通Noto Sans JP。旧900ウェイトの太さを700へ合わせ、サイズ・余白は画面幅と文字量で調整。小ラベル/本文を12px未満にしない。
- **素材**: 既存の文字無し独立写真を再利用。足りないHEROの会議/OUR ROLEの漫画制作/営業モニター説明、VALUESの黒いジャケット人物、明るい都市背景は参照に合わせた生成イメージを `material/images/about-approved-2026/` に置く（1536×1024）。写真は実在社員/顧客/社屋の撮影とは表示しない。生成の入力は確定写真の構図・被写体・光、出力は写真のみ（ラベル/番号/枠/コピー無し）。写真の人物や建物の完全な画素一致は保証せず、独立素材との差をレビュー画像で明示する。生成指示と組み込み先は [素材README](material/images/about-approved-2026/README.md) に記録。
- **検証**: `tests/test_about_approved.py` が現在の統合仕様の正本。19幅（320〜1920、899/1024/1100境界前後）、日英、1.4倍文字、画像寸法/読込、写真内コピーの重なり、実リンク、focus、メニュー、JS無効/動き軽減、ヘッダー/フッターHTML維持を検証する。旧5本の構成固定テストをこの全体検証へ統合。以前の検証コードはGit履歴、以前の確認画像は既存screenshotsディレクトリで参照できる。
- 撮影は字体ロード・img.decode()・画像のスクロール表示を待って行う。PC/スマホの「見本/修正前/修正後」の比較画像と、単独セクションの画像を `tests/screenshots/about-approved/` に保存する。02〜06は専用スマホ画像が未提供のため、PC構図を読みやすい1列に変換して検証。

### Aboutのセクション末尾案内（2026-10-15、Issue #169）

- WHY / OUR ROLE / MESSAGE / FUTURE末尾の「NEXT」案内4か所は削除。同じページ内の次セクションへは通常のスクロールで進む。専用CSSとMESSAGEの空の締め枠も削除し、スマホ/中間幅で案内に割り当てていた余白を整理する。
- 事業カード・MISSION/VISION内の説明リンク・代表メッセージ全文・末尾のお問い合わせ/採用CTAは維持する。末尾CTAのセクション名「NEXT ACTION」はナビゲーションではなく見出しとして維持する。

### Aboutの構図・写真境界・スマホ調整（2026-10-14、Issue #167）

- #165の内容・実写真・8セクションの流れを維持し、全体表示で目立った構図の競合を調整。
- HEROのXは都市写真側へ縮小・低濃度化。PC見出しを抑え、本文の背後は白い斜面で確保して写真へはみ出さない。本文は16〜18px、SP本文は15〜17px。SPの人物画像を下げて頭部が白い面に隠れないようにする。都市の補助コピーは装飾としてnowrapとtext-size-adjustを限定適用し、Safariでも2行を保つ。本文/UIには適用しない。
- MISSION/VISIONは `.axl-mv-flow` の2行gridと高さ0の交点行で、人物写真の左下端・都市写真の右上端・中央Xを一致させる。本文の長さや日英・文字拡大に追従。1024px以下はコピー→写真の縦構成へ。本文17px、欧文ラベルの濃度と見出しサイズを調整。
- VALUESの番号/英語を `.axl-card-heading` の独立した白い帯へ分離。写真上の斜め帯を外し、3枚の写真先頭とカード下端を揃える。共有 `feature-card.css` は変更しない。
- MESSAGEは960×1440の既存実写真を変更せず、CSSのcropと上下左右のマスクのみ。顔全体を残しつつ頭上の余白を減らし、PC左コピー/右写真、SPコピー→写真。写真領域は比率で縮み、本文が長くても押し重ならない。
- OUR ROLE/VALUES/MESSAGE/FUTUREの都市背景・帯を低濃度化。PC見出しと本文の比率を調整し、読み進めるページとして本文を優先。
- `tests/test_about_approved.py` の19幅・日英・文字1.4倍の検証に、写真の交点/X中心、VALUESのラベル分離/写真先頭、代表の顔の投影範囲を追加。`--browser webkit` で320/390/768/1024/1440pxも確認する。目視は単体だけでなく全ページとセクション境界で行う。
- 修正前/後の画像は [比較画像の目次](tests/screenshots/about-polish/README.md)。CSSの限定変更で他ページ/共通部品を維持。

## 14. 参照ドキュメント

| ファイル | 内容 |
|---|---|
| [CLAUDE.md](CLAUDE.md) | Claude Code 引き継ぎ資料 |
| [../SPEC.md](../SPEC.md) | プロジェクト全体仕様（B/C横断） |
| [../STYLE-GUIDE.md](../STYLE-GUIDE.md) | デザインルール |
| [../COMPONENT.md](../COMPONENT.md) | 再利用UIパーツ |
| [../SEO.md](../SEO.md) | SEOメタデータ一覧 |
| [../CHECKLIST.md](../CHECKLIST.md) | 公開前チェックリスト |

## 15. よくある落とし穴（Gotchas）

1. **CTA変更忘れ** → [js/cta.js](js/cta.js) 1箇所を編集すれば共通CTAを使う全ページ（現在は会社概要のみ）に反映される（手動コピペ禁止）
2. **モバイルでハンバーガー押せない** → §7.1 のチェックリスト
3. **新作情報に漫画事例を出したい** → 旧トップの「新作情報」は撤去済み（2026-10-13 に `script.js` の描画・`wp-api.js` の `/works-new` 取得・`js/data/new-works.js` を削除）。復活させる場合は git 履歴から戻す（当時の不具合は [BUGS.md #052](../BUGS.md)）
4. **Heroカルーセルから特定漫画を外したい** → 旧HEROカルーセル（`hero-new.js`）は 2026-10-29 に削除済み。戻すときは git の履歴から戻し、`wp-api.js` の `/works` の取得（2026-10-13 に削除）も戻す
5. **i18n 切替が動かない** → `i18n.js` が `nav.js` より先にロードされているか確認
6. **テキストロゴの X だけ色を変えたい** → `.hlt-char--x` クラス
7. **ヒーロー演出のタイミング変更** → 旧ヒーローの `hero-new.js`（`startIntro()` / `startHeroAnimation()`）は 2026-10-29 に削除済み。今のヒーロー（v2）は §3 を参照
8. **タグラインの波・点滅を止めたい** → `hero-new.css` の `cxCharRipple` / `cxCharBlink` keyframes
9. **資料DL制限** → お問い合わせ送信済みか `localStorage.cx_form_submitted` で判定
10. **bizmangaサブページは別ナビ** → `ContentX/bizmanga/` 配下は `bm-nav.js` を使用（独立BizMangaサイトとは別物）

## 14. 代表メッセージ独立ページ（2026-10-07）

- 正規URL: `/message`。既存の `message.html` を再利用する。新規 `company/` ディレクトリが既存の拡張子なしURL `/company` を遮らない構成。企業案内の共通ナビ、`/about#message` 内の「代表メッセージを全文読む」、TOPICSから遷移する。旧 `/message` の転送を解除し、このページを正規URLとして再公開する。
- 原稿（Issue #80、2026-10-07更新）: 「全国で見てきたあの光景を、一社ずつ変えていきたい。」をHero見出しとし、ユーザー指定の7段落を要約・改変せず全文掲載。旧導入＋5章は新原稿へ差し替える。日英切替でも日本語の句読点・スペース・署名を保つ。本文の正本は `message.html`、一致検証用の支給原稿は `tests/test_message.py` に保持する。
- 管理方式: Contents X本体の `message.html` / `css/message-2026.css` / `js/message-2026.js` による通常の固定ページ。原稿・章構成・写真をコード側で管理し、WordPress API・WP_CONFIG・CMSの生成処理とは連携しない。TOPICSからのリンクは入口のみであり、本文取得にCMSを使わない。
- 章構成: 01「原点とこれまで」（挨拶・三重での原点・キーエンスから事業承継/製造業までの経歴）、02「全国で見てきた光景」（全国の企業に共通する伝え方の課題）、03「Contents Xをつくった理由」（新しいやり方と最初の一歩・会社の取り組み）、04「これから」（昭和と令和、地方と東京から始まる締めの段落と署名）。h2と番号を補助的に添え、本文7段落の文言と順序は変更しない。
- デザイン資料: ユーザー支給 `ContentsX_Message_Page_Handoff.zip` の `00_reference_design_pc_sp.png` と `PROMPT.md` を基準にする。参考画像そのものをページとして貼らずHTML/CSS/JSで再現。ヘッダー・フッターは既存コンポーネントを維持する。
- 写真: ZIPの `01_ceo_portrait_original.png`（934×978）と `02_team_meeting_original.png`（1398×914）をWebPに変換した `material/images/message-2026/portrait-original.webp` / `team-original.webp` を使用。元写真の人物・顔・服装・体型・背景を生成・変更せず、画像の加工はWebP圧縮のみ。実在しない会社風景・街並みを加えない。関連リンクは企業案内の実会議写真 `team-meeting-collaboration.webp`、Contents Xのロゴ、支給ポートレートを流用し、新しい景観や役員集合写真を作らない。
- デザイン: `css/message-2026.css`。白・濃紺・淡いブルーグレー、薄いXと細い罫線。全体は最大1280px、通常の長文本文は最大720px。PC Heroは左44%（MESSAGE・コピー・会社名/肩書・縦線とSCROLL）/右56%（支給ポートレート）。第1章は左端に章番号、本文の右にCSSだけの淡い面を置く（1200px以下では面を省略）。第2章は左に会議写真・右に本文の約1:1構成、続いて第3・4章を1カラムで配置する。章番号はPCの左ガター、SPでは見出し上に置く。本文は #273445、見出し #0b2145、補足は薄いグレー。PC本文17〜18px・行間1.9、SP16〜17px・行間1.9、段落間28〜32px・章間72〜96pxが基本。最終章と署名は余白を広げ、署名を本文左端に合わせる。
- SP/中間幅: 1024px以下でHeroをMESSAGE→コピー/肩書→写真→本文の縦構成へ、第2章は本文→会議写真へ。SCROLL表示は省略。768px以下の本文左右余白は24px、章番号を見出し上へ移す。タイトルはclampで連続調整し、長い文節の改行を補助する。写真の縦横比はHTML属性を元寸法に合わせ、必要な表示cropはCSSだけで行う。
- 動き: `js/message-2026.js` のIntersectionObserverでHeroコピーは14px/0.55秒のfade-up、代表写真は0.14秒遅れて8px/0.65秒、会議写真はviewportに入ったとき8px/0.8秒のfade-up。本文・章見出しはスクロール前から表示し、動かさない。一度表示した内容は再び隠さない。スクロールロック・スナップ・パララックスは追加しない。JS無効・Observer非対応/初期化失敗・印刷時も全文を表示。`prefers-reduced-motion` と実行中の設定変更に対応する。
- 関連導線: 署名の下に `RELATED CONTENTS / 関連コンテンツ` と `/about`（私たちについて）、`/company`（会社概要）、`/company#officers`（役員紹介）の3カード。既存/支給素材のサムネイル・タイトル・矢印だけにし、PC3列/SP1列、カードの高さを揃える。hover可能な端末では画像1.02倍・矢印4px/0.2秒。動き軽減時はhoverの移動も無効にする。非表示中の `/leadership` は復元しない。
- 共通ナビの企業案内に `/message` を追加する。i18n.js → nav.js → message-2026.jsの順序を維持する。
- 検証: `python3 tests/test_message.py --url http://127.0.0.1:8780`。loopback previewで原稿完全一致、320〜1920px・境界幅、1.4倍文字拡大、日英往復、タッチナビ、関連導線、画像比率、既存URL、WordPressリクエストなし、本文の常時表示/Heroと会議写真のみ表示演出、PC左右レイアウト/章番号の収まり/関連カード、JS無効/Observer非対応/動き軽減を確認する。

### 14.1 TOPICSとの接続

- TOPICS制作PR #78を土台にする。静的フォールバックカードの代表メッセージは `/message`。
- `js/home-topics.js` は WordPress の `type: MESSAGE` かつ既知の自サイトURL（`/about#message`・`/message`・`/message.html`）だけを `/message` に揃える。言語等のクエリを保持し、外部サイトや別のMESSAGEリンクは変更しない。本番WPの書換えは不要。
- `tests/test_topics.py` の旧リンクfixtureを維持して新しい行き先を検証する。静的・WP正常・取得失敗・JS無効の各経路と実クリックを確認する。
