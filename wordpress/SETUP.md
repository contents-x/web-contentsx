# ContentsX WordPress CMS セットアップ手順

> ## ⚠️ プラグイン本体（PHP）はこのリポジトリにありません（2026-08-04 分離）
>
> `contentsx-cms.php` のマスターソースは **別のPRIVATEリポジトリ**へ移設しました。
>
> **https://github.com/contents-x/contentsx-wp-plugin**（`contentsx-cms/contentsx-cms.php`）
>
> - **理由**: このリポジトリ（ContentsX_HP）は**PUBLIC**。サイト本体は静的HTMLなので公開して問題ないが、
>   サーバー側で実行されるコードを公開する必然性がないため
> - **ローカルの場所**: `~/Documents/contentX/web/contentsx-wp-plugin/`
> - **デプロイは従来どおり**: どちらのリポジトリでも git push では本番反映されない。
>   お名前.comのファイルマネージャーで手動アップロードが必要（BUGS #002）
>
> このファイル（WP側の初期セットアップ手順）はサイト運用にも必要なため、こちらに残しています。

## 全体構成

```
┌─────────────────────┐          ┌─────────────────────────┐
│   WordPress (裏方)   │  ──API──▶│   静的サイト (表)         │
│   bizmanga.contentsx.jp│          │   contentsx.jp        │
│   お名前.comサーバー   │          │   GitHub Pages           │
│                     │          │                         │
│  ・漫画事例の編集     │          │  ・HTML / CSS / JS       │
│  ・ニュースの投稿     │          │  ・WP APIからデータ取得    │
│  ・画像アップロード   │          │  ・HubSpotフォーム維持     │
└─────────────────────┘          └─────────────────────────┘
```

## STEP 1: お名前.comでレンタルサーバーを契約

1. お名前.com にログイン
2. 「レンタルサーバー」→「RSプラン」を契約（月額990円〜）
3. サブドメイン `bizmanga.contentsx.jp` を設定
   - サーバー管理画面 → ドメイン設定 → サブドメイン追加

## STEP 2: WordPressをインストール

1. お名前.com サーバー管理画面（コントロールパネル）にログイン
2. 「WordPress」→「簡単インストール」をクリック
3. 以下を入力:
   - インストールURL: `bizmanga.contentsx.jp`
   - サイト名: `ContentsX CMS`
   - ユーザー名: 任意（管理用）
   - パスワード: 強力なものを設定
4. 「インストール」をクリック
5. `https://bizmanga.contentsx.jp/wp-admin/` にアクセスできることを確認

## STEP 3: プラグインをインストール

1. `wordpress/contentsx-cms/` フォルダを ZIP に圧縮
   ```
   cd wordpress
   zip -r contentsx-cms.zip contentsx-cms/
   ```
2. WordPress管理画面 → プラグイン → 新規追加 → アップロード
3. `contentsx-cms.zip` をアップロードして有効化
4. 左メニューに「漫画事例」と「ニュース」が追加される

## STEP 4: SSL（HTTPS）を有効化

1. お名前.com コントロールパネル → SSL設定
2. `bizmanga.contentsx.jp` に無料SSL（Let's Encrypt）を設定
3. WordPress管理画面 → 設定 → 一般:
   - WordPress アドレス: `https://bizmanga.contentsx.jp`
   - サイトアドレス: `https://bizmanga.contentsx.jp`

## STEP 5: 初期データを投入

### ニュースタグを作成
1. ニュース → タグ → 以下を追加:
   - `お知らせ`（英語名: `News`）
   - `プレスリリース`（英語名: `Press Release`）
   - `サービス`（英語名: `Service`）

### 漫画カテゴリを作成
1. 漫画事例 → カテゴリ → 以下を追加:
   - `紹介` / `営業` / `研修` / `採用` / `集客` / `ブランド` / `IP`

### 漫画事例を登録
1. 漫画事例 → 新規追加
2. タイトル（日本語）を入力
3. 各フィールドを入力:
   - ID（フォルダ名）: `omatome-ninja` など
   - タイトル（英語）
   - ページ数 / クライアント / 制作ページ数 / 制作期間
   - 使用メディア（カンマ区切り）
   - 漫画のポイント / お客様の声
   - 表示順: 1, 2, 3... の数字
   - 新作情報に表示: する / しない
4. カテゴリを選択
5. 「公開」をクリック

### ニュースを登録
1. ニュース → 新規追加
2. タイトル（日本語）を入力
3. タイトル（英語）/ リンクURL を入力
4. タグを選択（お知らせ / プレスリリース / サービス）
5. 「公開」をクリック

## STEP 6: フロントサイトの設定を変更

### 6-1. CORS許可ドメインの設定
`contentsx-cms.php` 内の `$allowed` 配列に、本番ドメインを追加済みか確認:
```php
$allowed = [
    'https://contentsx.jp',
    'https://www.contentsx.jp',
];
```

### 6-2. フロントエンドのAPI接続をON
`js/wp-config.js` を編集:
```javascript
const WP_CONFIG = {
  apiBase: 'https://bizmanga.contentsx.jp/wp-json/contentsx/v1',
  enabled: true,
  timeout: 5000,
  cacheTTL: 5 * 60 * 1000,
};
```

### 6-3. 動作確認
1. サイトを開いてブラウザの開発者ツール → Console を確認
2. 以下のログが出ればOK:
   ```
   [WP-API] 漫画事例: 20件 loaded
   [WP-API] 新作情報: 5件 loaded
   [WP-API] ニュース: 3件 rendered
   ```

## STEP 7: WordPress のセキュリティ設定

プラグインに以下のセキュリティ対策をすべて組み込み済みです。
追加のプラグインなしで動作します。

### プラグイン内蔵のセキュリティ（自動適用）

| 対策 | 内容 |
|---|---|
| フロント画面の無効化 | WordPressの表側にアクセスすると管理画面にリダイレクト。CMSとして裏方に徹する |
| ユーザー情報の漏洩防止 | `/wp-json/wp/v2/users` を非認証ユーザーに非公開化 |
| 標準REST APIの制限 | `contentsx/v1/*` 以外の wp/v2 エンドポイントは認証必須 |
| ユーザー列挙攻撃の防止 | `?author=1` によるユーザー名の特定をブロック |
| XML-RPC の無効化 | ブルートフォース攻撃の入口を遮断 |
| WPバージョン情報の非表示 | バージョン特定による既知の脆弱性攻撃を防止 |
| ログイン試行制限 | 同一IPから5回失敗 → 15分ロックアウト |
| APIレスポンスキャッシュ | 公開エンドポイントに5分のキャッシュヘッダー付与 |
| セキュリティヘッダー | X-Content-Type-Options / X-Frame-Options / Referrer-Policy |

### 追加で推奨する設定

1. **管理画面のアクセス制限**（推奨）
   - WP管理画面は裏方なので、一般ユーザーがアクセスする必要はない
   - お名前.com の .htaccess でIP制限を設定可能:
   ```apache
   # wp-admin と wp-login.php を特定IPのみに制限
   <Files wp-login.php>
     Order Deny,Allow
     Deny from all
     Allow from xxx.xxx.xxx.xxx  # 自分のIPアドレス
   </Files>
   ```

2. **不要な機能を無効化**
   - WordPressのフロント表示は使わないので、テーマは最小限でOK
   - コメント機能: 設定 → ディスカッション → すべてOFF
   - ピンバック・トラックバック: OFF（XML-RPCはプラグインで無効化済み）

3. **自動更新を有効化**
   - WordPress管理画面 → 更新 → 「メンテナンスリリースとセキュリティリリースのみ自動更新」を有効に
   - プラグインの自動更新も有効推奨

4. **REST APIの公開範囲**
   - CORSで許可ドメインのみ接続可能（プラグイン内蔵）
   - 公開APIは `contentsx/v1/*` のみ（読み取り専用）
   - 書き込み系API（POST/PUT/DELETE）は認証必須のまま

5. **強力なパスワード**
   - 管理者アカウントには16文字以上の複雑なパスワードを使用
   - ユーザー名を `admin` にしない

## 日常の運用フロー

### 漫画事例を追加したいとき
1. `bizmanga.contentsx.jp/wp-admin` にログイン
2. 漫画事例 → 新規追加
3. 情報を入力して「公開」
4. サイトに自動反映（数秒以内）

### ニュースを追加したいとき
1. `bizmanga.contentsx.jp/wp-admin` にログイン
2. ニュース → 新規追加
3. タイトル・タグ・リンクを入力して「公開」
4. サイトに自動反映

### 漫画の画像について
現時点では、漫画の画像ファイル（01.webp〜）は GitHub リポジトリの
`material/manga/{ID}/` フォルダに直接配置する運用です。
WordPressのメディアライブラリからの配信は将来対応可能です。

## ファイル一覧

```
wordpress/
  contentsx-cms/
    contentsx-cms.php    ← WordPressプラグイン本体
  SETUP.md               ← この手順書

js/
  wp-config.js           ← API接続設定（apiBase / enabled）
  wp-api.js              ← ニュースの取得と描画（2026-10-13 から /works・/works-new は取得しない）
  cx-dom.js              ← トップ・採用の WordPress 連携部品が共有する取得・検査の道具
```

## トラブルシューティング

**Q: WordPress API に接続できない**
→ `wp-config.js` の `apiBase` URLが正しいか確認。ブラウザで直接 `https://bizmanga.contentsx.jp/wp-json/contentsx/v1/works` を開いてJSONが返るか確認。

**Q: CORSエラーが出る**
→ `contentsx-cms.php` の `$allowed` 配列にフロントサイトのドメインが入っているか確認。

**Q: WordPress が落ちたらサイトも止まる？**
→ いいえ。ページは止まりません。WordPress から取れなかった部分は、各ページの HTML に書いてある初期表示のまま残ります（TOPICS の3枚、Creative X のサービスへのリンクなど）。ニュース一覧は読み込み表示が消えて空の一覧になります。（旧 `js/data/new-works.js` などのローカルデータは 2026-10-13 に削除）
