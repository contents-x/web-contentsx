# github.md — ContentsX リポジトリ Git 運用ルール

> **このファイルが ContentsX の Git ルールの正本です。git 操作をするときは毎回ここを参照します。**
> 初めてこのリポジトリで作業する人は、最初に必ず一読してください。
> BizManga リポジトリにも同じ内容の `github.md` があります（差分はリポジトリ名・デプロイ先・ビルドBotだけ）。

---

## ⛔ 絶対ルール（最優先・例外なし）

チーム開発なので、次の2つは必ず守る。**`main` で直接作業しない**ための土台。

1. **会話セッションを開いたら、毎回まずブランチを切る。**
   作業を始める前に、`main` ではなく作業ブランチにいる状態を作る（§3の命名で）。
2. **1つの機能を作る・コードを編集するときは、必ずブランチを切る。**
   「ちょっとした修正」でも `main` で直接編集・コミットしない。編集に着手する前にブランチを切る。

> Claude Code で作業する場合も同じ。**セッション冒頭と、コード編集に入る前に、この2ルールに従ってブランチを切ってから作業する。**

---

## 0. 大前提 — このリポジトリは「push＝即本番公開」

- `main` ブランチは **GitHub Pages で contentsx.jp に自動デプロイ**されます（`static.yml`）。
- **`main` に入った瞬間、世界中に公開されます。** 検証していないものを `main` に入れない。
- だからこそ「直接 `main` に push しない・PRで変更内容を確認してからマージ」を徹底します（→ §4）。

---

## 1. 基本の流れ（毎回これ）

```
Issue を立てる  →  ブランチを切る  →  作業  →  push  →  PR を出す  →  内容確認・マージ許可  →  マージ  →  自動デプロイ
```

1. **Issue を立てる**（§2）— 何をやるか先に登録する
2. **`main` から新しいブランチを切る**（§3）— Issue番号を入れた名前で
3. **作業してこまめにコミット**（§6）
4. **リモートに push** して **PR を出す**（§4）
5. **変更内容を確認**する。原則として別の担当者のレビューを受ける。リポジトリ所有者が自ら確認した場合は、その明示的な確認で足りる（§4）
6. **マージ**（Squash推奨）→ 自動でデプロイ

> 小さな typo 修正でもこの流れに乗せます。「直接 main」の例外は作りません（唯一の例外はビルドBot、§4末尾）。

---

## 2. Issue — 課題ごとに1つ

**すべての作業は Issue から始めます。** 「何を・なぜ」を先に言語化することで、後から履歴を追える・二重作業を防げる・レビューしやすくなります。

- 作業を始める前に GitHub の **Issues** タブで新規Issueを作成（テンプレートあり）。
- 1 Issue = 1 つのまとまった作業。大きすぎるものは分割する。
- Issue番号（例 `#42`）を、このあとのブランチ名とPRに必ず紐づける。

**Issueを立てなくてよい例外**（それでも推奨はする）:
- 明らかに1行で終わる緊急の本番不具合（それでも後追いでIssue化する）

---

## 3. ブランチの切り方・名前の付け方

### 切り方

```bash
git checkout main
git pull origin main          # 必ず最新のmainから切る
git checkout -b feat/42-client-logos-add
```

### 命名規則

```
<type>/<Issue番号>-<短い説明（英小文字・ハイフン区切り）>
```

例:
| ブランチ名 | 意味 |
|-----------|------|
| `feat/42-client-logos-add` | スポンサーロゴ追加（新機能） |
| `fix/48-news-thumb-gray` | ニュースサムネの灰色枠修正 |
| `docs/routing-update` | ドキュメント更新（Issue無しでも可の軽微なもの） |
| `seo/50-strength-cluster` | SEO施策 |

### type の一覧

| type | 用途 |
|------|------|
| `feat` | 新機能・新セクション・新ページ |
| `fix` | バグ修正 |
| `style` | 見た目・CSSのみ（挙動を変えない） |
| `refactor` | 挙動を変えないコード整理 |
| `docs` | ドキュメント（SPEC.md / CLAUDE.md / *.md） |
| `seo` | SEO施策（メタ・スキーマ・LP・sitemap等） |
| `chore` | ビルド・設定・依存・雑務 |

### ブランチは短命に

- **数日で終わるサイズに保つ。** 長生きするブランチは `main` と乖離して事故のもと。
- マージが済んだブランチは削除する（PR画面の "Delete branch" ボタン）。

---

## 4. Pull Request（PR）

### ルール

- **`main` への直接 push は禁止。必ず PR 経由。**（運用ルール。GitHub側の設定状況は§5）
- PR は原則として**別の担当者1人のレビュー**を受ける。ただし、**リポジトリ所有者が変更内容を自ら確認し、当該PRのマージを明示的に許可した場合は、別の担当者によるレビュー承認を必須としない**。所有者の確認とマージ許可は、対象PRが分かる形で会話またはPRに記録する。
- 所有者以外の依頼者による確認だけで上記の例外を適用しない。
- PR本文はテンプレートに沿って埋める（変更概要 / 対応Issue / チェックリスト）。
- **`Closes #42`** を PR 本文に書くと、マージ時にそのIssueが自動でクローズされます。

### マージ方式

- **Squash and merge を推奨**（1PR＝1コミットにまとまり、`main` の履歴がきれいになる）。
- マージ後はブランチを削除。

### マージの実行者（2026-07-19 運用変更）⭐

- **マージ操作は Claude Code が実行する**（人間がGitHub画面でマージボタンを押す運用から変更）。
- ただし **AIエージェントは必ず事前に依頼者（またはリポジトリ所有者）から対象PRの明示的なマージ許可を得てから実行する。許可なしのマージは絶対禁止**。別担当者のレビュー承認とマージ許可は別物（承認が付いていても、マージ実行前にあらためて許可を取る）。所有者が自ら内容を確認した場合は、§4の例外を適用できる。
- マージ後は Claude がブランチ削除・Issue自動クローズの確認・本番反映（GitHub Pagesデプロイ）の確認まで行う。
- このルールは招待メンバーを含む**全チーム共通**（ContentsX_HP / bizmanga 両リポジトリ同一運用）。人間による手動マージも従来通り可能だが、基本フローはClaude実行に統一する。

### ⚠️ ビルドBotだけは直接pushする（正常）

このリポジトリでは、以下の **GitHub Actions が自動で `main` に commit/push** します。これは仕様であり、止めてはいけません。

| ワークフロー | 何をするか |
|------------|-----------|
| `build-c-columns.yml` | WPのコラムから静的ページを生成 |
| `static.yml` | GitHub Pages へのデプロイと、成功後の IndexNow へのURL通知（人の push・手動実行で起動。ボットの push では起動しないので、`build-c-columns.yml` が push の後に手動起動する） |

→ ブランチ保護を設定する際は、これらの Bot（`github-actions[bot]`）を**例外として許可**します（§5参照）。人間だけがPR必須になるよう設定します。

---

## 5. ブランチ保護の設定（管理者＝リポジトリ所有者が実施）

> 2026-09-29 時点で、GitHub API 上の `main` には削除禁止・強制更新禁止の ruleset が適用されています。PR必須・レビュー承認必須の保護は設定されていません。PR経由の運用は現在この文書で定めています。以下は今後PR必須の保護を追加する場合の確認事項です。

**Settings → Branches → Add branch ruleset**（または旧UI: Branch protection rules）で `main` に対して:

1. ☑ **Require a pull request before merging**
   - **Require approvals を必須にしない**。所有者本人の確認で進める§4の運用と、GitHubの「別アカウントからの承認1件」強制は両立しないため。別担当者レビューはPR運用で管理する。
2. ☑ **Require status checks to pass**（任意。ビルド系チェックがあれば）
3. ☐ **Do NOT** enable "Include administrators" を強制しすぎない
   — ただし所有者も基本はPRに従う運用にする
4. **ビルドBotの例外**:
   - Ruleset の **Bypass list** に `Repository admin` と、Actions が使う `github-actions[bot]` 相当を追加する
   - 旧UIの場合: `github-actions[bot]` は `GITHUB_TOKEN` で push するため、"Allow specified actors to bypass required pull requests" に追加、もしくは各ビルドワークフローの push 先を保護対象から外れるよう運用で担保する
   - **設定後、必ず `build-c-columns` を手動実行（workflow_dispatch）してBotのpushが通ることを確認する**（コラムに変更があれば、そのまま本番へのデプロイと IndexNow の通知まで走る）

> 設定でBotのpushがブロックされると、コラムの静的ページ更新が止まります。設定変更の翌日は反映を必ず確認してください。

---

## 6. コミットのルール

### メッセージ形式

```
<type>: <日本語で何をしたか（現在形・簡潔に）>

（必要なら本文で「なぜ」を説明）

Closes #42
```

例:
```
fix: ニュースサムネの灰色枠を解消

.news-thumb の #f5f5f5 明示指定が原因。cover+白背景に修正。

Closes #48
```

- `type` はブランチのtypeと揃える（`feat` / `fix` / `docs` …）。
- 1コミット＝1つの意味のまとまり。「あれもこれも」を1コミットに詰めない。
- **こまめにコミットする**（作業の区切りごと）。

### Claude Code で作業する場合

Claude がコミットする際は、末尾に共同作成者行を付けます（プロジェクト規約）:
```
Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
```

---

## 7. 仕様書の同時更新（このプロジェクト必須ルール）⭐

機能追加・動作変更・URLパラメータ追加・共通コンポーネント変更などを行ったら、**同じPR内で対象の仕様書も更新する**こと。「後でまとめて」は禁止。

- どのmdを更新するかは [../docs/MD-UPDATE-ROUTING.md](../docs/MD-UPDATE-ROUTING.md) を参照。
- ContentsX の変更 → [SPEC.md](SPEC.md) または [CLAUDE.md](CLAUDE.md)。
- バグ修正・再発防止 → ルートの [BUGS.md](../BUGS.md) の索引に1行、本文はルートの `docs/bugs/` の分野別ファイルに追記（手順は BUGS.md 末尾）。

PRテンプレートのチェックリストにこの項目が入っています。

---

## 8. やってはいけないこと（禁止事項）

- ❌ **`main` への直接 push / force push**（Botを除く）
- ❌ 検証していない変更を `main` にマージ（＝即本番公開される）
- ❌ `ContentX/bizmanga/*.html`（8ファイル）の削除 — 旧URL救済の301リダイレクト、削除厳禁
- ❌ ビルドBotの Actions を止める・保護でブロックする
- ❌ 他人のブランチに勝手に force push する
- ❌ 仕様書更新をサボる（§7）

---

## 9. 困ったときのクイックリファレンス

```bash
# 最新のmainから作業ブランチを切る
git checkout main && git pull origin main
git checkout -b fix/48-news-thumb-gray

# 作業 → コミット
git add -A
git commit -m "fix: ..."

# push（初回は -u で上流を設定）
git push -u origin fix/48-news-thumb-gray
# → 表示されるURLからPRを作成

# mainが進んだので取り込みたい（コンフリクト前に）
git checkout main && git pull
git checkout fix/48-news-thumb-gray
git merge main            # またはお好みで rebase

# マージ済みブランチの掃除
git checkout main && git pull
git branch -d fix/48-news-thumb-gray
```

---

**関連ドキュメント**: [CLAUDE.md](CLAUDE.md)（開発仕様） / [SPEC.md](SPEC.md)（機能仕様） / [../docs/OPERATIONS.md](../docs/OPERATIONS.md)（運用全体像）
