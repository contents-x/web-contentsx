/* Play the approved works directly in this page, with no third-party player UI.
   Since 2026-11-07 a poster with data-wp-slot reads the video chosen in WordPress
   (「サイトの表示 → ContentsX → サービスページ → ビズアニメ欄／ビズビデオ欄の動画」 GET /slots/<key>):
   WordPress only returns videos that have their own MP4 file and a picture. The file must be on
   cms.contentsx.jp (the pages' CSP allows media from there). Its captions are not used: WordPress does not
   send CORS headers for uploads, so a <track> from there would not load (checked 2026-11-07); without a
   track the CC button is left out. When the slot is empty, cannot be read or WordPress is off, the video
   written in the HTML stays. */
const LOCAL_VIDEO = /^\/material\/service-2026\/[\w-]+\.mp4$/;
const LOCAL_CAPTIONS = /^\/material\/service-2026\/[\w-]+\.ja\.vtt$/;
const WP_UPLOAD = /^https:\/\/cms\.contentsx\.jp\/wp-content\/uploads\/[\w\/.%-]+$/;
const SLOT_TIMEOUT = 5000;

function wpFile(url, ext) {
  return WP_UPLOAD.test(url || '') && new RegExp(`\\.${ext}$`, 'i').test(url) && !url.includes('..');
}

function applySlot(poster, card) {
  const video = card && card.video;
  if (!video || !wpFile(video.src, 'mp4')) return;
  const thumb = String(card.thumb || '');
  if (!/^https:\/\/cms\.contentsx\.jp\/|^https:\/\/i\.ytimg\.com\//.test(thumb)) return;
  poster.dataset.videoSrc = video.src;
  delete poster.dataset.captionSrc;
  const img = poster.querySelector('img');
  if (img) img.src = thumb;
  const title = String(card.title || '').trim();
  if (title) poster.setAttribute('aria-label', `${poster.dataset.wpLabel || '制作事例'}「${title}」を音声付きで再生`);
}

function loadSlots() {
  if (typeof WP_CONFIG === 'undefined' || WP_CONFIG.enabled === false || !WP_CONFIG.apiBase || !window.fetch) return;
  const posters = Array.from(document.querySelectorAll('.cxg-video-play[data-wp-slot]'));
  const keys = [...new Set(posters.map((p) => p.dataset.wpSlot).filter((k) => /^[a-z0-9-]+$/.test(k)))];
  keys.forEach((key) => {
    const ctrl = 'AbortController' in window ? new AbortController() : null;
    const timer = setTimeout(() => { if (ctrl) ctrl.abort(); }, SLOT_TIMEOUT);
    fetch(`${WP_CONFIG.apiBase}/slots/${key}`, ctrl ? { signal: ctrl.signal } : {})
      .then((r) => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json(); })
      .then((d) => {
        const card = d && Array.isArray(d.items) ? d.items[0] : null;
        // A poster that is already playing has been replaced by the player; only the waiting ones change.
        posters.filter((p) => p.dataset.wpSlot === key && p.isConnected).forEach((p) => applySlot(p, card));
      })
      .catch((e) => console.warn(`[service-media] /slots/${key} failed:`, e.message))
      .finally(() => clearTimeout(timer));
  });
}
function mediaButton(action, label, symbol) {
  const button = document.createElement('button');
  button.type = 'button';
  button.className = 'cxg-video-controls__button';
  button.dataset.action = action;
  button.setAttribute('aria-label', label);
  button.textContent = symbol;
  return button;
}

function startServiceVideo(poster) {
  const src = poster.dataset.videoSrc;
  const captionsSrc = poster.dataset.captionSrc;
  if (!LOCAL_VIDEO.test(src || '') && !wpFile(src, 'mp4')) return;

  const shell = document.createElement('div');
  shell.className = 'cxg-video-shell';
  shell.dataset.playing = 'true';
  const video = document.createElement('video');
  video.className = 'cxg-video-player';
  video.src = src;
  video.preload = 'metadata';
  video.playsInline = true;
  video.poster = poster.querySelector('img')?.src || '';
  video.setAttribute('aria-label', poster.getAttribute('aria-label') || '制作事例の動画');
  const hasCaptions = LOCAL_CAPTIONS.test(captionsSrc || '');
  if (hasCaptions) {
    const track = document.createElement('track');
    track.kind = 'captions';
    track.label = '日本語（自動生成）';
    track.srclang = 'ja';
    track.src = captionsSrc;
    video.append(track);
  }

  const surface = mediaButton('surface', '動画を一時停止', '');
  surface.className = 'cxg-video-surface';
  const controls = document.createElement('div');
  controls.className = 'cxg-video-controls';
  const play = mediaButton('play', '動画を一時停止', 'Ⅱ');
  const volume = mediaButton('volume', '音声をミュート', '◖))');
  const captions = mediaButton('captions', '自動字幕を表示', 'CC');
  captions.setAttribute('aria-pressed', 'false');
  const progress = document.createElement('input');
  progress.className = 'cxg-video-controls__progress';
  progress.type = 'range';
  progress.min = '0';
  progress.max = '100';
  progress.value = '0';
  progress.setAttribute('aria-label', '動画の再生位置');
  const fullscreen = mediaButton('fullscreen', '動画を拡大', '⛶');
  controls.append(play, volume);
  if (hasCaptions) controls.append(captions);
  controls.append(progress, fullscreen);
  shell.append(video, surface, controls);
  poster.replaceWith(shell);
  shell.closest('.cxg-service-card')?.classList.add('cxg-service-card--playing');
  shell.closest('.cxsd-card')?.classList.add('cxsd-card--playing');

  function syncPlayState() {
    const playing = !video.paused && !video.ended;
    shell.dataset.playing = String(playing);
    play.textContent = playing ? 'Ⅱ' : '▶';
    play.setAttribute('aria-label', playing ? '動画を一時停止' : '動画を再生');
    surface.setAttribute('aria-label', playing ? '動画を一時停止' : '動画を再生');
  }

  function togglePlay() {
    if (video.paused || video.ended) video.play().catch(() => { shell.dataset.playing = 'false'; });
    else video.pause();
  }

  play.addEventListener('click', togglePlay);
  surface.addEventListener('click', togglePlay);
  video.addEventListener('play', syncPlayState);
  video.addEventListener('pause', syncPlayState);
  video.addEventListener('ended', syncPlayState);
  video.addEventListener('timeupdate', () => {
    if (!Number.isFinite(video.duration) || !video.duration || document.activeElement === progress) return;
    progress.value = String(Math.round(video.currentTime / video.duration * 100));
    progress.style.setProperty('--cxg-progress', `${progress.value}%`);
  });
  progress.addEventListener('input', () => {
    if (Number.isFinite(video.duration) && video.duration) {
      video.currentTime = video.duration * Number(progress.value) / 100;
      progress.style.setProperty('--cxg-progress', `${progress.value}%`);
    }
  });
  volume.addEventListener('click', () => {
    video.muted = !video.muted;
    volume.textContent = video.muted ? '◖×' : '◖))';
    volume.setAttribute('aria-label', video.muted ? '音声をオンにする' : '音声をミュート');
  });
  captions.addEventListener('click', () => {
    const track = video.textTracks[0];
    if (!track) return;
    const enabled = track.mode !== 'showing';
    track.mode = enabled ? 'showing' : 'disabled';
    captions.setAttribute('aria-pressed', String(enabled));
    captions.setAttribute('aria-label', enabled ? '自動字幕を非表示' : '自動字幕を表示');
  });
  fullscreen.addEventListener('click', () => {
    if (document.fullscreenElement === shell) document.exitFullscreen();
    else if (shell.requestFullscreen) shell.requestFullscreen();
    else if (video.webkitEnterFullscreen) video.webkitEnterFullscreen();
  });

  video.play().catch(() => {
    shell.dataset.playing = 'false';
    syncPlayState();
  });
}

loadSlots();

document.addEventListener('click', (event) => {
  const poster = event.target.closest('.cxg-video-play');
  if (poster) startServiceVideo(poster);
});
