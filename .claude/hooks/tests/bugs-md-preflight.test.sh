#!/usr/bin/env bash
# bugs-md-preflight.sh の動作確認。一時フォルダだけを使う（本物の記録には触れない）。
# 実行: bash .claude/hooks/tests/bugs-md-preflight.test.sh
set -u
HOOK="$(cd "$(dirname "$0")/.." && pwd)/bugs-md-preflight.sh"
export TMPDIR; TMPDIR=$(mktemp -d)
trap 'rm -rf "$TMPDIR"' EXIT
pass=0; fail=0

# run <説明> <期待: 番号 or none> <JSON>
run() {
  local out got
  out=$(printf '%s' "$3" | bash "$HOOK")
  if [ -z "$out" ]; then got=none; else got=$(printf '%s' "$out" | jq -r '.hookSpecificOutput.additionalContext' | grep -oE '^- #[0-9]+' | head -1 | tr -d '#- '); fi
  if [ "$got" = "$2" ]; then pass=$((pass+1)); else fail=$((fail+1)); echo "NG: $1（期待 ${2} / 実際 ${got}）"; fi
}
bash_() { jq -n --arg c "$1" --arg s "${2:-s1}" --arg w "${3:-/x}" '{tool_name:"Bash",session_id:$s,cwd:$w,tool_input:{command:$c}}'; }
edit_() { jq -n --arg f "$1" --arg b "${2:-x}" --arg s "${3:-s1}" '{tool_name:"Edit",session_id:$s,tool_input:{file_path:$f,new_string:$b}}'; }

# 読むだけの操作では出ない
run "grep で header を検索"        none "$(bash_ 'grep -rn header index.html js/bm-nav.js')"
run "git log で nav.js"            none "$(bash_ 'git log --oneline -- js/nav.js')"
run "sed -n で読む"                none "$(bash_ 'sed -n 1,40p css/header.css')"
run "curl で WP API を読む"        none "$(bash_ 'curl -s https://cms.contentsx.jp/wp-json/contentsx/v1/works | jq .')"
run "ls material/"                 none "$(bash_ 'ls ContentX/material/images/')"
run "python で読むだけ"            none "$(bash_ "python3 - <<'EOF'
print(open('header.html').read())
EOF")"
# 文書・道具の編集では出ない
run "md の編集"                    none "$(edit_ /r/docs/header-nav-notes.md 'hamburger translateAll')"
run "シェルの中身に hamburger"     none "$(edit_ /r/.claude/hooks/x.sh 'hamburger translateAll')"

# 書き換える操作では出る
run "bm-nav.js の編集"             003  "$(edit_ /r/BizManga/js/bm-nav.js 'x' a1)"
run "同じ会話で2回目は出ない"      none "$(edit_ /r/BizManga/js/bm-nav.js 'x' a1)"
run "別の会話なら出る"             003  "$(edit_ /r/BizManga/js/bm-nav.js 'x' a2)"
run "中身に hamburger"             003  "$(edit_ /r/BizManga/index.html '<button class="bm-hamburger">' b1)"
run "ビューアの編集"               010 "$(edit_ /r/BizManga/js/bm-view-type.js 'x' b2)"
run "i18n.js の編集"               005  "$(edit_ /r/ContentX/js/i18n.js 'x' b3)"
run "中身に translateAll"          005  "$(edit_ /r/ContentX/js/home.js 'window.i18n.translateAll()' b4)"
run "WPプラグインの PHP"           002  "$(edit_ /p/contentsx-wp-plugin/contentsx-cms/core/api.php 'x' b5)"
run "プラグインの README は出ない" none "$(edit_ /p/contentsx-wp-plugin/README.md 'x' b6)"
run "相対パスの href"              006  "$(edit_ /r/BizManga/index.html '<a href="about.html">' b7)"
run "絶対パスの href は出ない"     none "$(edit_ /r/BizManga/index.html '<a href="/about">x</a><img src="https://a/b.png"><a href="#top">' b8)"
run "テンプレの差し込みは出ない"   none "$(edit_ /r/BizManga/js/a.js 'const t = `<a href="${url}">`' b9)"
run "material の削除"              020  "$(bash_ 'git rm ContentX/material/images/a.webp' c1)"
run "sed -i で URL 置換"           016  "$(bash_ "sed -i '' 's|https://a.example|https://b.example|' index.html" c2)"
run "python で i18n.js を書く"     005  "$(bash_ "python3 - <<'EOF'
p='js/i18n.js'; s=open(p).read(); open(p,'w').write(s)
EOF" c3)"
run "プラグインで git push"        002  "$(bash_ 'git push -u origin fix/x' c4 /Users/u/contentsx-wp-plugin)"
run "読むだけの rm を含む文"       none "$(bash_ 'echo "git rm で material/ を消すと危ない" | wc -l' c6)"
run "sed -n の後の grep -i は出ない" none "$(bash_ 'sed -n 1,5p index.html | grep -i https' c7)"
run "B で git push は出ない"       none "$(bash_ 'git push -u origin fix/x' c5 /Users/u/BizManga)"

echo "bugs-md-preflight: PASS $pass / FAIL $fail"
[ "$fail" -eq 0 ]
