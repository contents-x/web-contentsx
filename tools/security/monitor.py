#!/usr/bin/env python3
"""contentsx.jp の改ざん・乗っ取りの兆候を点検する（2026-10-14、.github/workflows/security-monitor.yml から1時間ごと）。

異常があれば終了コード1 → GitHub がワークフローの失敗をメールで知らせる。
標準ライブラリだけで動く。基準値は tools/security/expected.json。

点検すること:
  1. 本番の HTML / CSS / JS / XML / TXT が、最後に成功したデプロイのコミットと1バイト違わず同じか（改ざん）
  2. 本番の HTML が読み込む外部スクリプト・iframe のホストが許可リストの中か（不正なスクリプトの差し込み）
  3. 内部資料が本番から取得できないか（公開範囲の後退）
  4. DNS（NS / A / CNAME / MX / CAA）が基準値と同じか（ドメイン・DNSの乗っ取り）
  5. TLS 証明書の残り日数
  6. GitHub Pages の独自ドメイン・HTTPS 強制・公開方式、本番が main より古いまま止まっていないか、
     main への PR を通らない push・強制 push（リポジトリの乗っ取り）
     push した人は GitHub の操作記録（activity API）の actor で見る（コミットの作者名は偽装できるため）
  7. WordPress で閉じた入口が開いていないか（expected.json で true にした項目だけ。WP 側の後退）:
     ユーザー一覧API、xmlrpc.php（本文が XML-RPC の応答なら開いている）、許可してはいけないオリジン
     （null・前方/後方一致の誤り・http の本番ホスト・偽サブドメイン）への CORS、開発用オリジンへの資格情報つき CORS。
     独自API と WordPress 本体の API、GET とプリフライトを試す。API ごとに本番オリジン（対照）に許可が返るかを
     確かめ、返らない API（WAF の遮断ページ等）と取れなかった組は「確認できない」の注意にする。
     海外（監視を動かす GitHub Actions）から管理画面・ログイン画面に届かないこと（サーバーの国外アクセス制限）と、
     サーバーの WAF が攻撃の形をした要求を止めていること

Usage:
  python3 tools/security/monitor.py --site-dir _site            # 点検（異常で exit 1）
  python3 tools/security/monitor.py --site-dir _site --report   # 記録だけ（常に exit 0。基準値づくり用）
"""
import argparse
import functools
import json
from concurrent.futures import ThreadPoolExecutor
import os
import re
import socket
import ssl
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import quote, urlsplit

ROOT = Path(__file__).resolve().parents[2]
EXPECTED = json.loads((ROOT / "tools" / "security" / "expected.json").read_text(encoding="utf-8"))
UA = "ContentsX-SecurityMonitor/1.0 (+https://github.com/contents-x/web-contentsx)"
TEXT_EXT = {".html", ".css", ".js", ".xml", ".txt", ".json"}
DNS_QUERIES = [
    ("contentsx.jp", "NS"), ("contentsx.jp", "A"), ("contentsx.jp", "AAAA"), ("contentsx.jp", "MX"),
    ("contentsx.jp", "CAA"), ("www.contentsx.jp", "CNAME"), ("bizmanga.contentsx.jp", "CNAME"),
    ("cms.contentsx.jp", "A"), ("cms.contentsx.jp", "CNAME"),
]

problems, warnings, notes = [], [], []
# 本番の取得は毎回別の URL にして CDN（最大10分のキャッシュ）を通り越す。GitHub Pages はクエリを無視して同じファイルを返す
BUST = f"cxmon={int(time.time())}"


def live(site, rel):
    return http(f"{site}/{quote(rel)}?{BUST}")


def merge_headers(msg):
    """応答ヘッダーを名前を小文字にした辞書にする。同じ名前（大文字小文字違いも同じ扱い）が複数あれば
    ", " でつなぐ（dict(msg) だと最初の1つしか残らない）"""
    out = {}
    for k, v in (msg.items() if msg else []):
        k = k.lower()
        out[k] = f"{out[k]}, {v}" if k in out else v
    return out


def http(url, method="GET", data=None, headers=None, timeout=20):
    h = {"User-Agent": UA, "Cache-Control": "no-cache"}
    h.update(headers or {})
    req = urllib.request.Request(url, data=data, method=method, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read(), merge_headers(r.headers)
    except urllib.error.HTTPError as e:
        return e.code, e.read() if e.fp else b"", merge_headers(e.headers)
    except Exception as e:  # noqa: BLE001 — 通信の失敗も記録して続ける
        return 0, str(e).encode(), {}


def github(path):
    token = os.environ.get("GITHUB_TOKEN")
    repo = os.environ.get("GITHUB_REPOSITORY")
    if not token or not repo:
        return None, None
    status, body, _ = http(f"https://api.github.com/repos/{repo}{path}",
                           headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"})
    try:
        return status, json.loads(body or b"null")
    except ValueError:
        return status, None


# ---------- 1〜3. 本番の内容 ----------
class TagHosts(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hosts = set()

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "iframe"):
            src = dict(attrs).get("src") or ""
            u = urlsplit(src if not src.startswith("//") else "https:" + src)
            if u.netloc:
                self.hosts.add(u.netloc.lower())


def check_content(site_dir):
    site = EXPECTED["site"]
    def served(p):
        parts = p.relative_to(site_dir).parts
        return not any(x.startswith(".") for x in parts) and parts[0] != "tools"
    files = sorted(p for p in Path(site_dir).rglob("*") if p.is_file() and p.suffix.lower() in TEXT_EXT and served(p))
    if not files:
        problems.append(f"点検対象のファイルが見つからない: {site_dir}")
        return
    mismatched = []
    for p in files:
        rel = p.relative_to(site_dir).as_posix()
        status, body, _ = live(site, rel)
        if status != 200 or body != p.read_bytes():
            mismatched.append(rel)
        if rel.endswith(".html") and status == 200:
            parser = TagHosts()
            parser.feed(body.decode("utf-8", "replace"))
            unknown = sorted(parser.hosts - set(EXPECTED["script_hosts"]) - {"contentsx.jp", "www.contentsx.jp"})
            if unknown:
                problems.append(f"許可していない外部スクリプト/iframe: {rel} → {', '.join(unknown)}")
    still = mismatched
    # デプロイの切り替わり中・配信の反映待ちかもしれないので、間を空けて2回まで取り直す（合計約7分）
    for wait in (120, 300):
        if not still:
            break
        time.sleep(wait)
        retry = []
        for rel in still:
            status, body, _ = http(f"{site}/{quote(rel)}?cxmon={int(time.time())}")
            if status != 200 or body != (Path(site_dir) / rel).read_bytes():
                retry.append(rel)
        still = retry
    if still:
        problems.append(f"本番の内容がデプロイしたコミットと違う（改ざんの可能性）: {len(still)}件 — " + ", ".join(still[:15]))
    notes.append(f"本番の内容: {len(files)}ファイルを照合")


def check_hidden():
    site = EXPECTED["site"]
    leaked = []
    for rel in EXPECTED["must_be_hidden"]:
        status, _, _ = live(site, rel)
        if status == 200:
            leaked.append(rel)
    if leaked:
        problems.append("内部資料が本番から取得できる: " + ", ".join(leaked))


# ---------- 4. DNS ----------
def dig(name, rtype):
    try:
        res = subprocess.run(["dig", "+short", "+time=5", "+tries=2", name, rtype, "@1.1.1.1"],
                             capture_output=True, text=True, timeout=30)
    except Exception as e:  # noqa: BLE001
        return None, str(e)
    out = res.stdout
    # 問い合わせ自体の失敗（タイムアウト・SERVFAIL）は「空の答え」ではない。乗っ取りと誤判定しないよう別扱いにする
    if res.returncode != 0 or any(line.startswith(";;") for line in out.splitlines()):
        return None, (out.strip() or res.stderr.strip() or f"dig exit {res.returncode}")[:120]
    vals = sorted({line.strip().rstrip(".").lower() for line in out.splitlines() if line.strip() and not line.startswith(";")})
    # A / AAAA の問い合わせでは途中の CNAME も返るので、アドレスだけ残す
    if rtype == "A":
        vals = [v for v in vals if re.fullmatch(r"\d+\.\d+\.\d+\.\d+", v)]
    elif rtype == "AAAA":
        vals = [v for v in vals if ":" in v]
    return vals, None


def check_dns(report):
    expected = EXPECTED.get("dns", {})
    current = {}
    for name, rtype in DNS_QUERIES:
        vals, err = dig(name, rtype)
        key = f"{name} {rtype}"
        if vals is None:
            warnings.append(f"DNS を引けない: {key} ({err})")
            continue
        current[key] = vals
        if key not in expected:
            warnings.append(f"DNS の基準値が未登録: {key} = {vals}")
        elif sorted(expected[key]) != vals:
            problems.append(f"DNS が基準値と違う（乗っ取り・誤設定の可能性）: {key} 基準={expected[key]} 現在={vals}")
    if report:
        notes.append("現在の DNS（expected.json の dns に貼る値）:\n```json\n" + json.dumps(current, ensure_ascii=False, indent=2) + "\n```")


# ---------- 5. TLS ----------
def check_tls():
    ctx = ssl.create_default_context()
    for host in EXPECTED["tls_hosts"]:
        try:
            with socket.create_connection((host, 443), timeout=15) as sock, ctx.wrap_socket(sock, server_hostname=host) as s:
                not_after = s.getpeercert()["notAfter"]
            days = (datetime.strptime(not_after, "%b %d %H:%M:%S %Y %Z").replace(tzinfo=timezone.utc)
                    - datetime.now(timezone.utc)).days
            if days < 14:
                problems.append(f"TLS 証明書の残りが {days} 日: {host}")
            elif days < 30:
                warnings.append(f"TLS 証明書の残りが {days} 日: {host}")
        except Exception as e:  # noqa: BLE001
            problems.append(f"HTTPS で接続できない・証明書が不正: {host} ({e})")


# ---------- 6. GitHub ----------
def check_github():
    exp = EXPECTED["github"]
    status, pages = github("/pages")
    if status is None:
        warnings.append("GITHUB_TOKEN が無いので GitHub の点検を省略")
        return
    if status == 200 and isinstance(pages, dict):
        if (pages.get("cname") or "") != exp["pages_cname"]:
            problems.append(f"GitHub Pages の独自ドメインが変わった: {pages.get('cname')}")
        if exp["pages_https_enforced"] and not pages.get("https_enforced"):
            problems.append("GitHub Pages の HTTPS 強制が外れている")
        # legacy（ブランチから公開）に戻るとリポジトリ全体が公開され、許可リストが効かなくなる（CLAUDE.md「公開範囲と監視」）
        if exp.get("pages_build_type") and pages.get("build_type") != exp["pages_build_type"]:
            problems.append(f"GitHub Pages の公開方式が変わった: {pages.get('build_type')}（GitHub Actions 以外だと内部資料まで公開される）")
    else:
        warnings.append(f"GitHub Pages の設定を読めない (HTTP {status})")
    # main への操作の記録（直近1日）。actor は実際に操作した認証済みアカウントで、コミットの作者名と違い偽装できない
    status, acts = main_activity()
    if acts is None:
        problems.append(f"main への操作の記録を読めない（PR を通らない push を確認できない）: HTTP {status}")
        return
    for a in acts:
        kind = a.get("activity_type")
        actor = (a.get("actor") or {}).get("login") or "?"
        sha = (a.get("after") or "")[:7]
        if kind in ("force_push", "branch_deletion"):
            problems.append(f"main に {kind} があった: {actor} {a.get('timestamp')} {sha}")
        elif kind == "push" and actor not in exp["direct_push_allowed"]:
            problems.append(f"PR を通らずに main へ push された: {actor} {a.get('timestamp')} {sha}")


ACTIVITY_PAGE = 100


@functools.cache
def main_activity():
    """main への操作の記録（直近1日・新しい順）を (HTTP status, list or None) で返す。
    失敗も含めて1回の実行で1度だけ取り、check_github と check_stale_deploy が共有する"""
    status, acts = github(f"/activity?ref=refs/heads/main&time_period=day&per_page={ACTIVITY_PAGE}")
    if status != 200 or not isinstance(acts, list):
        return status, None
    return status, [a for a in acts if isinstance(a, dict)]


def parse_utc(value):
    """GitHub の時刻（ISO 8601）を UTC の日時にする。時差の無い表記は UTC とみなす。読めなければ None"""
    try:
        t = datetime.fromisoformat(str(value or "").replace("Z", "+00:00"))
    except ValueError:
        return None
    return t if t.tzinfo else t.replace(tzinfo=timezone.utc)


def check_stale_deploy():
    """本番が main より古いまま放置されていないか（デプロイが止まっている・自動ビルドの反映漏れ）。
    起点は「本番に出ていない main への操作のうち最も古いもの」の時刻。GitHub が記録した操作の時刻を使う
    （コミットの日時は書き換えられる。最新の操作を起点にすると、push が続く限り遅れに気づけない）"""
    live_sha = os.environ.get("LIVE_SHA")
    if not live_sha:
        warnings.append("本番のコミット（LIVE_SHA）が分からないので、本番の更新停止の点検を省略")
        return
    status, acts = main_activity()
    if acts is None:
        warnings.append(f"main への操作の記録を読めないので、本番の更新停止の点検を省略 (HTTP {status})")
        return
    if not acts:
        # 直近1日に main への操作が無い。main の先頭と本番が違えば、1日以上止まっている
        status, head = github("/commits/main")
        head_sha = head.get("sha") if status == 200 and isinstance(head, dict) else None
        if head_sha is None:
            warnings.append(f"直近1日の操作記録が無く、main の先頭も読めないので、本番の更新停止の点検を省略 (HTTP {status})")
        elif head_sha != live_sha:
            problems.append(f"本番が main より古いまま、少なくとも1日（直近1日に main への操作なし）: 本番 {live_sha[:7]} / main {head_sha[:7]}")
        return
    # 新しい順に見て、本番のコミットに届くまでの操作が「本番に出ていない操作」
    pending = []
    for a in acts:
        if (a.get("after") or "") == live_sha:
            break
        pending.append(a)
    if not pending:
        return
    oldest = pending[-1]
    if len(pending) == len(acts) and len(acts) >= ACTIVITY_PAGE:
        warnings.append(f"main への操作が直近1日で {len(acts)} 件以上あり、本番のコミットを記録の中で見つけられない（本番の更新停止の点検を省略）")
        return
    if len(pending) == len(acts) and (oldest.get("before") or "") != live_sha:
        # 本番のコミットが直近1日の記録に無く、最初の未反映の操作も記録より前 → 1日以上遅れている
        problems.append(f"本番が main より古いまま、少なくとも1日（本番のコミットが直近1日の操作記録に無い）: "
                        f"本番 {live_sha[:7]} / main {(acts[0].get('after') or '?')[:7]}")
        return
    started = parse_utc(oldest.get("timestamp"))
    if started is None:
        warnings.append(f"main への操作の時刻を読めない: {oldest.get('timestamp')!r}")
        return
    age_h = (datetime.now(timezone.utc) - started).total_seconds() / 3600
    if age_h >= 1:
        problems.append(f"本番が main より古いまま {age_h:.1f} 時間（デプロイが止まっている可能性）: "
                        f"本番 {live_sha[:7]} / main {(acts[0].get('after') or '?')[:7]}・未反映の操作 {len(pending)} 件")


# ---------- 7. WordPress ----------
# 許可してはいけないオリジン。null（sandbox の iframe・file://）、許可判定の前方一致・後方一致の誤り、
# スキームを見ない誤り（http の本番ホスト）、サブドメインを広く許す誤りを突く形も試す
UNRELATED_ORIGINS = ["https://cxmon-probe.invalid", "null",
                     "https://contentsx.jp.cxmon-probe.invalid", "https://cxmon-probecontentsx.jp",
                     "http://contentsx.jp", "https://cxmon-probe.contentsx.jp"]
# 許可されているはずの本番オリジン（対照）。これに許可が返らない応答は WordPress のものではない（WAF の遮断ページ等）
CONTROL_ORIGIN = "https://contentsx.jp"
# 独自の API と WordPress 本体の API（Cookie 認証で管理者として操作されうる。CORS の付け方は本体の API 全体で同じ）の
# 両方を試す。本体の代表は REST の入口 /wp-json/（前段が GitHub Actions の IP からの /wp/v2/ への要求を遮断し、
# users・types 等は確かめられないため。CORS は REST の応答全体に同じ処理で付く）
CORS_PATHS = ["/wp-json/contentsx/v1/topics", "/wp-json/"]
XMLRPC_CLOSED = (403, 404, 405, 410)


def header_values(h, name):
    return [v.strip().lower() for v in h.get(name, "").split(",") if v.strip()]


def cors_grants(h, origin):
    vals = header_values(h, "access-control-allow-origin")
    return origin.lower() in vals or "*" in vals


def cors_with_credentials(h, origin):
    # ブラウザは「*」と資格情報つきの組み合わせを拒否するので、オリジンが完全に一致するときだけ数える
    return origin.lower() in header_values(h, "access-control-allow-origin") \
        and "true" in header_values(h, "access-control-allow-credentials")


def fetch_cors(api, path, origin, preflight):
    """(status, ヘッダー〈名前は http() が小文字にそろえる〉)。オリジンごとに URL を変え、WP の前段のキャッシュ
    （最大10分。Vary: Origin を見ない場合もある）を共有させない。プリフライトは本物のブラウザが Cookie つきの
    POST の前に送る形"""
    url = f"{api}{path}?{BUST}&o={quote(origin, safe='')}"
    if preflight:
        headers = {"Origin": origin, "Access-Control-Request-Method": "POST",
                   "Access-Control-Request-Headers": "content-type,x-wp-nonce"}
        status, _, h = http(url, method="OPTIONS", headers=headers, timeout=15)
    else:
        status, _, h = http(url, headers={"Origin": origin}, timeout=15)
    return status, h


def is_production_origin(origin):
    host = urlsplit(origin).hostname or ""
    return origin.startswith("https://") and (host == "contentsx.jp" or host.endswith(".contentsx.jp"))


def check_wordpress():
    wp = EXPECTED["wordpress"]
    api = wp["api"]
    # 1つの入口の失敗で他の点検を省かない（それぞれ注意にとどめて続ける）
    if wp.get("users_endpoint_closed"):
        # パス（/wp-json/wp/v2/...）は前段が GitHub Actions の IP からの要求を遮断するので、同じ API をクエリで指定する。
        # 遮断ページの 403 を「閉じている」と取り違えないよう、WordPress 自身の拒否（JSON の code）を確かめる
        status, body, _ = http(f"{api}/?rest_route=/wp/v2/users&{BUST}")
        if status == 200 and body.strip().startswith(b"["):
            problems.append("WordPress のユーザー一覧APIが開いている（管理者名が取得できる）")
        elif not (status in (401, 403) and body.lstrip().startswith(b"{") and b'"code"' in body):
            warnings.append(f"WordPress のユーザー一覧APIが閉じているか確認できない (HTTP {status})")
    if wp.get("xmlrpc_closed"):
        status, body, _ = http(f"{api}/xmlrpc.php", method="POST",
                               data=b"<?xml version='1.0'?><methodCall><methodName>system.listMethods</methodName></methodCall>",
                               headers={"Content-Type": "text/xml"})
        # urllib は POST への 301/302/303 を GET で追うので、状態コードではなく本文で「開いている」を判定する
        if status == 200 and b"<methodResponse" in body:
            problems.append("WordPress の xmlrpc.php が開いている（XML-RPC の応答が返る）")
        elif status not in XMLRPC_CLOSED and not (status == 200 and b"<methodResponse" not in body):
            warnings.append(f"WordPress の xmlrpc.php を確認できない (HTTP {status})")
    if wp.get("overseas_dashboard_blocked"):
        # 監視は GitHub Actions（海外の IP）から動く。サーバーの「国外アクセス制限（ダッシュボード）」で
        # 管理画面・ログイン画面に届かないこと（urllib はリダイレクトを追うので、届けば最後は 200 になる）
        for path in ("/wp-login.php", "/wp-admin/"):
            status, _, _ = http(f"{api}{path}?{BUST}")
            if status == 200:
                problems.append(f"海外から WordPress の管理画面・ログイン画面に届く（国外アクセス制限が外れている）: {path}")
            elif status != 403:
                warnings.append(f"海外からの {path} を確認できない (HTTP {status})")
    if wp.get("waf_blocks_attacks"):
        # サーバーの WAF が、攻撃の形をした要求を止めているか。同じ URL の普通の要求（対照）は通ることも確かめる
        base = f"{api}/wp-json/contentsx/v1/topics?{BUST}"
        normal, _, _ = http(base)
        attack, _, _ = http(base + "&q=" + quote("<script>alert(1)</script>", safe=""))
        if normal != 200:
            warnings.append(f"WAF を確認できない（普通の要求が HTTP {normal}）")
        elif attack == 200:
            problems.append("WordPress の WAF が攻撃の形をした要求を止めていない（WAF が外れている可能性）")
        elif attack != 403:
            warnings.append(f"WAF の応答が想定外 (HTTP {attack})")
    if not (wp.get("cors_unknown_origin_blocked") or wp.get("cors_credentials_production_only")):
        return
    probe = []
    for origin in wp.get("cors_probe_origins", []):   # 一般的な開発用ポート（プラグインの許可一覧とは同期しない）
        if is_production_origin(origin):
            warnings.append(f"cors_probe_origins に本番のオリジンが入っているので除外: {origin}")
        else:
            probe.append(origin)
    # プリフライトはプラグインが REST 全体で同じ経路で返すので独自APIで試す（共用サーバーへの要求数を抑える）
    combos = [(path, False) for path in CORS_PATHS] + [(CORS_PATHS[0], True)]
    jobs = [(path, CONTROL_ORIGIN, pre) for path, pre in combos]
    jobs += [(path, o, pre) for o in UNRELATED_ORIGINS + probe for path, pre in combos]
    with ThreadPoolExecutor(max_workers=3) as pool:
        results = dict(zip(jobs, pool.map(lambda j: fetch_cors(api, *j), jobs)))
    def label(path, pre):
        return f"{path}・{'プリフライト' if pre else 'GET'}"
    # 対照（API・GET/プリフライトごと）: 本番オリジンに許可が返らない組は、届いているのが WordPress の応答ではない
    # （WAF の遮断ページ・前段が OPTIONS を一律に拒否する等）ので、その組は判定しない
    checked = []
    for path, pre in combos:
        st, h = results[(path, CONTROL_ORIGIN, pre)]
        if cors_grants(h, CONTROL_ORIGIN):
            checked.append((path, pre))
        else:
            warnings.append(f"本番オリジンにも CORS の許可が返らないので、{label(path, pre)} の CORS を確認できない (HTTP {st})")

    def usable(st, h):
        # 接続できない、または CORS ヘッダーが無く WordPress が返す状態（200/204/401/403/404）でもない応答
        # （429・5xx の遮断ページ等）は、許可していない証拠にならない
        return st != 0 and (st in (200, 204, 401, 403, 404) or "access-control-allow-origin" in h)
    unverified = [k for k in jobs if k[1] != CONTROL_ORIGIN and (k[0], k[2]) in checked and not usable(*results[k])]
    if unverified:
        codes = sorted({results[k][0] for k in unverified})
        warnings.append(f"WordPress の CORS の点検で {len(unverified)} 件を確認できなかった（HTTP {codes}。取れた結果だけで判定）")

    def got(origin):
        """この origin について、確かめられた組の使える結果 [(path, preflight, ヘッダー)]"""
        return [(path, pre, results[(path, origin, pre)][1]) for path, pre in combos
                if (path, pre) in checked and usable(*results[(path, origin, pre)])]
    # 応答の状態（401・404 など）に関係なくヘッダーを見る。エラー応答でも CORS の許可があればブラウザは読ませる
    if wp.get("cors_unknown_origin_blocked"):
        for origin in UNRELATED_ORIGINS:
            hits = [label(path, pre) for path, pre, h in got(origin) if cors_grants(h, origin)]
            if hits:
                problems.append(f"WordPress の CORS が許可してはいけないオリジン {origin} を許可している: {', '.join(hits)}")
    if wp.get("cors_credentials_production_only"):
        # 資格情報（Cookie）つきの CORS は本番ドメインだけ。開発用オリジンに出すと、手元などで開いた
        # 任意のページからログイン中の管理者として API を呼べてしまう（許可してはいけないオリジンは上で報告済み）
        for origin in probe:
            hits = [label(path, pre) for path, pre, h in got(origin) if cors_with_credentials(h, origin)]
            if hits:
                problems.append(f"WordPress の CORS が {origin} に資格情報つきの呼び出しを許可している: {', '.join(hits)}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--site-dir", default=str(ROOT / "_site"))
    ap.add_argument("--report", action="store_true", help="記録だけ。異常があっても exit 0")
    args = ap.parse_args()
    for fn in (lambda: check_content(args.site_dir), check_hidden, lambda: check_dns(args.report),
               check_tls, check_github, check_stale_deploy, check_wordpress):
        try:
            fn()
        except Exception as e:  # noqa: BLE001 — 1つの点検の失敗で他を止めない。失敗自体は異常扱い
            problems.append(f"点検そのものが失敗: {getattr(fn, '__name__', fn)}: {e}")
    lines = ["## セキュリティ点検 " + datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")]
    lines += ["### ❌ 異常"] + [f"- {p}" for p in problems] if problems else ["### ✅ 異常なし"]
    if warnings:
        lines += ["### ⚠️ 注意（未対応の既知事項・基準値の未登録など）"] + [f"- {w}" for w in warnings]
    lines += ["### 記録"] + [f"- {n}" for n in notes]
    out = "\n".join(lines)
    print(out)
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as f:
            f.write(out + "\n")
    return 1 if problems and not args.report else 0


if __name__ == "__main__":
    sys.exit(main())
