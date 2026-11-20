/* ============================================================
   WordPress API 設定
   ============================================================
   ■ 使い方
   WP_API_BASE を WordPress のインストール先に変更してください。
   例: https://cms.contentsx.jp/wp-json/contentsx/v1

   ■ フォールバック
   WordPress に接続できない場合は、各ページの HTML に書いてある初期表示のまま残します
   （TOPICS の3枚、ニュースの読み込み表示など）。
   ============================================================ */

const WP_CONFIG = {
  /* WordPress REST API のベースURL（末尾スラッシュなし） */
  apiBase: 'https://cms.contentsx.jp/wp-json/contentsx/v1',

  /* true にすると WordPress API から取得、false なら取得しない */
  enabled: true,

  /* API タイムアウト（ミリ秒） */
  timeout: 3000,

  /* キャッシュ有効期間（ミリ秒）— ブラウザメモリ内 */
  cacheTTL: 5 * 60 * 1000,   // 5分

  /* Creative X 紹介ページの WordPress 移行スイッチ（SPEC.md §3.0「WordPress への移行」、js/cx-works.js）
     true（移行中）: WORKS と CREATIVE SOLUTION の代表作品は、新しい掲載枠（/slots/cx-creative-*）に
       何件登録されていても読まず、これまでの一覧（71作品・data/creative-solution.json の代表3作品）を出す。
       HERO だけは今までどおり枠を読み、MP4 が登録されていれば流す（空ならこれまでの表示）。
     false（切り替え後）: WORKS と代表作品も枠の作品と並び順を出す（空の枠は「作品は準備中です」）。
     WordPress で登録と並び順を確かめてから false にする。問題があれば true に戻す（切り戻し）。 */
  creativeXLegacyFallback: true,

  /* メンテナンス表示スイッチ（手順: SPEC.md「WordPress 一時停止スイッチ」）
     true にすると WordPress API へのアクセスをすべて止め、画面下に中立なお知らせを出す。
     自動ビルド（コラム）もこの行を見て止まる。行の書式を変えないこと。 */
  maintenance: false,
};

/* メンテナンス中: WordPress API 宛ての fetch をここで一括して失敗させる。
   WP の URL を直書きしている部品もあるため、呼び出し側ではなく fetch 自体で止める。
   失敗扱いになるので、各部品は既存の「読み込めなかったとき」の表示に落ちる。 */
(function () {
  if (!WP_CONFIG.maintenance || typeof window.fetch !== 'function') return;

  const WP_API_PREFIX = 'https://cms.contentsx.jp/wp-json/';
  const originalFetch = window.fetch;
  WP_CONFIG.enabled = false;

  window.fetch = function (input) {
    const url = typeof input === 'string' ? input : (input && input.url) || String(input);
    if (url.indexOf(WP_API_PREFIX) === 0) {
      return Promise.reject(new TypeError('maintenance'));
    }
    return originalFetch.apply(this, arguments);
  };

  if (window.top !== window.self) return;

  const DISMISS_KEY = 'cxMaintenanceNoticeClosed';
  try { if (sessionStorage.getItem(DISMISS_KEY)) return; } catch (e) {}

  function showNotice() {
    if (document.getElementById('cxMaintenanceNotice')) return;

    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = '/css/cx-maintenance-notice.css';
    document.head.appendChild(link);

    const bar = document.createElement('div');
    bar.id = 'cxMaintenanceNotice';
    bar.className = 'cx-maintenance-notice';
    bar.setAttribute('role', 'status');

    const text = document.createElement('p');
    text.className = 'cx-maintenance-notice__text';
    text.textContent = 'ただいま一部の表示を一時停止しています。しばらくしてから再度ご覧ください。';

    const close = document.createElement('button');
    close.type = 'button';
    close.className = 'cx-maintenance-notice__close';
    close.setAttribute('aria-label', 'お知らせを閉じる');
    close.textContent = '×';
    close.addEventListener('click', function () {
      bar.remove();
      try { sessionStorage.setItem(DISMISS_KEY, '1'); } catch (e) {}
    });

    bar.appendChild(text);
    bar.appendChild(close);
    document.body.appendChild(bar);
  }

  if (document.body) showNotice();
  else document.addEventListener('DOMContentLoaded', showNotice);
})();
