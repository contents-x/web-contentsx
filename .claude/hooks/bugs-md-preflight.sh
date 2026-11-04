#!/usr/bin/env bash
# BUGS.md Pre-flight 警告: これから「書き換える」対象が過去バグの地雷パターンに当たったら、
# 該当バグ番号を知らせる（ブロックはしない・注意喚起のみ）。元ネタは BUGS.md「着手前チェックリスト」。
#
# 2026-11-04 改訂（出しすぎの修正。改訂前は操作の約4回に1回発火し、同じ警告が1会話で平均17回出ていた）:
#   1. 同じ会話で同じ警告は1回だけ（session_id ごとに、出した番号を一時ファイルへ記録）
#   2. 読むだけの操作（grep / git log / sed -n / curl など）では判定しない
#   3. コマンド文字列全体の単語ではなく「書き換えるファイルのパス」と「書き込む中身」で判定する
#
# 正本は ContentX_HP ルートの .claude/hooks/。BizManga・ContentX の .claude/hooks/ は同じ内容の写し（3か所同時に直す）。
# 動作確認: bash .claude/hooks/tests/bugs-md-preflight.test.sh
# 逆フックから呼ばれた claude 内では発火しない（再帰ガード）。
[ -n "$CLAUDE_REVERSE_HOOK" ] && exit 0
command -v jq >/dev/null 2>&1 || exit 0

input=$(cat)
j() { printf '%s' "$input" | jq -r "$1" 2>/dev/null; }
tool=$(j '.tool_name // empty')
sid=$(j '.session_id // empty')
f=$(j '.tool_input.file_path // empty')
cmd=$(j '.tool_input.command // empty')
cwd=$(j '.cwd // empty')
body=$(j '[.tool_input.new_string, .tool_input.content] | map(select(. != null)) | join("\n")')
[ -z "$tool" ] && { [ -n "$cmd" ] && tool=Bash || tool=Edit; }

# --- 同じ会話で出した警告の記録 ---
seen=""
if [ -n "$sid" ]; then
  dir="${TMPDIR:-/tmp}/bugs-md-preflight"
  mkdir -p "$dir" 2>/dev/null && seen="$dir/$(printf '%s' "$sid" | tr -c 'A-Za-z0-9_-' '_')"
  find "$dir" -type f -mtime +3 -delete 2>/dev/null
fi
keys=""; warns=""
hit() { # $1=重複判定のキー $2=警告文
  case " $keys " in *" $1 "*) return ;; esac
  [ -n "$seen" ] && grep -qxF "$1" "$seen" 2>/dev/null && return
  keys="$keys $1"
  warns="$warns
- $2"
}

# --- 判定に使うパス（書き換える対象だけ）---
paths=""
if [ "$tool" = "Bash" ]; then
  # 書き込み・削除の動作があるコマンドだけ、コマンド中のファイル名を対象にする
  if printf '%s' "$cmd" | grep -qE '(sed|perl)[^|;&]* -[a-zA-Z]*i|\btee\b|write_text\(|\.write\(|open\([^)]*["'"'"'][wa]["'"'"']|>>? *["'"'"']?[^ |;&>]+\.(html|css|js|json|php|tpl)\b|\b(rm|mv|cp)\b|os\.remove|unlink|rmtree|git (rm|mv|restore|checkout --)'; then
    paths=$(printf '%s' "$cmd" | grep -oE '[A-Za-z0-9_./~-]+\.(html|css|js|json|php|tpl)\b' | sort -u)
  fi
else
  paths="$f"
fi

# --- パスで判定（.md などの文書は対象外）---
while IFS= read -r p; do
  [ -z "$p" ] && continue
  case "$p" in *.md|*.txt|*.jsonl) continue ;; esac
  b=$(basename "$p" | tr 'A-Z' 'a-z')
  case "$p" in
    *contentsx-cms/*|*contentsx-wp-plugin*/*) hit 002 "#002: WPプラグインは git push だけでは本番反映されない。お名前.comで手動アップロード（フォルダごと・contentsx-cms.php は最後、アップ前に php -l）" ;;
  esac
  case "$b" in
    *nav*.js|*nav*.css|*header*) hit 003 "#003/#014(B)・#062/#063(C): ヘッダー/ナビ変更はスマホでハンバーガーが押せなくなる地雷。B は .bm-nav-cta--line を除外、C の開閉処理は nav.js だけ。スマホ・タブレット・PCで実際にタップして確認" ;;
  esac
  case "$b" in
    bm-view-type*|works.js|*viewer*|biz-library*|bm-fallback-works*) hit 012 "#010/#012/#013/#069: 漫画ビューアは view_type を自前判定せず window.bmViewType.* に委譲。/library と /manga/{id} の両分岐を揃え、直リンクは WP のデータで1回だけ開く" ;;
  esac
  case "$b" in
    *i18n*|en.json) hit 005 "#005/#008/#015: i18n は読込順(i18n.js→nav.js)固定・translateAll の無条件呼び出し禁止・UIラベルに data-i18n-skip" ;;
  esac
done <<EOF
$paths
EOF

# --- 書き込む中身で判定（Edit / Write。サイトのコードだけ）---
if [ "$tool" != "Bash" ] && [ -n "$body" ]; then
  case "$f" in
    *.html|*.js|*.css|*.tpl|*.php|*.py)
      case "$body" in *bm-nav-cta*|*hamburger*) hit 003 "#003/#014(B)・#062/#063(C): ヘッダー/ナビ変更はスマホでハンバーガーが押せなくなる地雷。B は .bm-nav-cta--line を除外、C の開閉処理は nav.js だけ。スマホ・タブレット・PCで実際にタップして確認" ;; esac
      case "$body" in *translateAll*) hit 005 "#005/#008/#015: i18n は読込順(i18n.js→nav.js)固定・translateAll の無条件呼び出し禁止・UIラベルに data-i18n-skip" ;; esac
      case "$f" in
        *.html|*.js|*.tpl|*.py)
          # href/src の値が相対パス（/・http・#・mailto: 等で始まらない）なら警告。テンプレの差し込み（${ {{）は除く
          if printf '%s' "$body" | grep -oE '(href|src)="[^"]*"' | sed -E 's/^(href|src)="//; s/"$//' \
             | grep -vE '^$|^/|^https?:|^#|^(mailto|tel|data|javascript|about|blob):|^\$|^\{|^\+|^'"'" | grep -q .; then
            hit 006 "#006: href/src は必ず絶対パス(/始まり)。相対パスはサブディレクトリで404"
          fi ;;
      esac ;;
    *) : ;;
  esac
fi

# --- コマンドで判定（Bash）---
if [ "$tool" = "Bash" ]; then
  # #020: material/ の削除・移動（削除の命令と material/ が同じ1つのコマンド内にあるときだけ）
  if printf '%s' "$cmd" | grep -qE '(^|[;&|(]|then|do) *(git +)?(rm|mv) [^;&|]*material/|(os\.remove|os\.unlink|unlink|rmtree|shutil\.move)\([^)]*material/'; then
    hit 020 "#020: ContentX/material の画像は BizManga が絶対URLで参照している。削除・移動の前に両サイトを同時に grep"
  fi
  # #016: sed / perl でファイルを直接書き換え、CSP や URL を置き換える（同じ1つのコマンド内）
  if printf '%s' "$cmd" | grep -qiE '(sed|perl)( +-[a-z]+)* +-[a-z]*i[a-z]*( [^;&]*)?(content-security-policy|csp|https?:)'; then
    hit 016 "#016: CSPメタの一括書換で sed の全体置換は禁止。同じURL文字列がインラインJSにも出るため壊す。アドレス指定するか Edit で行ごと差し替え"
  fi
  # #002: WPプラグインのリポジトリで push しても本番には出ない
  if printf '%s' "$cmd" | grep -qE 'git( -C [^ ]+)? push' && printf '%s %s' "$cwd" "$cmd" | grep -q 'contentsx-wp-plugin'; then
    hit 002 "#002: WPプラグインは git push だけでは本番反映されない。お名前.comで手動アップロード（フォルダごと・contentsx-cms.php は最後、アップ前に php -l）"
  fi
fi

[ -z "$warns" ] && exit 0
[ -n "$seen" ] && printf '%s\n' $keys >> "$seen" 2>/dev/null

jq -n --arg w "$warns" '{
  systemMessage: ("[BUGS.md Pre-flight] 過去バグの地雷パターンに一致（この会話では各1回だけ表示）:\($w)\n詳細は BUGS.md の索引から該当番号を開く。"),
  hookSpecificOutput: { hookEventName: "PreToolUse", additionalContext: ("この操作は過去バグの再発リスクあり（詳細は BUGS.md の索引から該当番号を開く）:\($w)") }
}'
exit 0
