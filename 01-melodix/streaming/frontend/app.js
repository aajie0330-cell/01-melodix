const audio = document.getElementById('audioEl');
const playBtn = document.getElementById('playBtn');
const playIcon = document.getElementById('playIcon');
const pauseIcon = document.getElementById('pauseIcon');
const progressFill = document.getElementById('progressFill');
const progressThumb = document.getElementById('progressThumb');
const currentTimeEl = document.getElementById('currentTime');
const totalTimeEl = document.getElementById('totalTime');
const playerTitle = document.getElementById('playerTitle');
const playerArtist = document.getElementById('playerArtist');
const playerThumb = document.getElementById('playerThumb');
const songListEl = document.getElementById('songList');
const emptyState = document.getElementById('emptyState');
const urlInput = document.getElementById('urlInput');
const addBtn = document.getElementById('addBtn');
const storageFill = document.getElementById('storageFill');
const storageText = document.getElementById('storageText');

let songs = [];
let currentIndex = -1;
let isPlaying = false;
let isShuffle = false;
let pollIntervals = {};

const THUMB_COLORS = [
  ['#312e81','#4f46e5'], ['#134e4a','#0f766e'],
  ['#3b0764','#7e22ce'], ['#1e3a5f','#1d4ed8'],
  ['#422006','#b45309'], ['#1a1a2e','#e94560'],
  ['#0f2027','#203a43'], ['#1a0533','#a855f7'],
];

function colorForIndex(i) {
  const [a, b] = THUMB_COLORS[i % THUMB_COLORS.length];
  return `linear-gradient(135deg,${a},${b})`;
}

function fmtTime(sec) {
  if (!sec || isNaN(sec)) return '0:00';
  const m = Math.floor(sec / 60);
  const s = Math.floor(sec % 60);
  return `${m}:${s.toString().padStart(2, '0')}`;
}

function toast(msg, type = 'info', duration = 4000) {
  const area = document.getElementById('toastArea');
  const el = document.createElement('div');
  el.className = `toast ${type}`;
  el.textContent = msg;
  area.innerHTML = '';
  area.appendChild(el);
  if (duration) setTimeout(() => { if (area.contains(el)) area.removeChild(el); }, duration);
}

function renderSongs() {
  if (songs.length === 0) {
    songListEl.innerHTML = '';
    songListEl.appendChild(emptyState);
    storageFill.style.width = '0%';
    storageText.textContent = '0 songs';
    return;
  }

  if (songListEl.contains(emptyState)) songListEl.removeChild(emptyState);

  songListEl.innerHTML = '';
  songs.forEach((song, i) => {
    const row = document.createElement('div');
    row.className = 'song-row' + (i === currentIndex ? ' playing' : '');
    row.dataset.id = song.id;
    row.dataset.index = i;

    const numCol = i === currentIndex
      ? `<div class="playing-bars"><span></span><span></span><span></span></div>`
      : `<span class="col-num">${i + 1}</span>`;

    const thumb = song.thumbnail
      ? `<img src="${song.thumbnail}" loading="lazy" onerror="this.style.display='none'" />`
      : `<div class="thumb-placeholder"><svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="#3d4657" stroke-width="1.5"><path d="M3 3h10v10H3zm5 2v4M5.5 9h5"/></svg></div>`;

    row.innerHTML = `
      <div class="col-num">${numCol}</div>
      <div class="song-info">
        <div class="song-thumb" style="background:${colorForIndex(i)}">${thumb}</div>
        <div class="song-meta">
          <div class="song-title">${escHtml(song.title)}</div>
          <div class="song-artist">${escHtml(song.artist || 'Unknown')}</div>
        </div>
      </div>
      <div class="song-duration">${fmtTime(song.duration)}</div>
      <div class="song-actions">
        <button class="icon-btn" onclick="deleteSong(event,${song.id})" title="Remove">
          <svg viewBox="0 0 12 12" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round">
            <path d="M2 3h8M5 3V2h2v1M4 3v6h4V3"/>
          </svg>
        </button>
      </div>
    `;

    row.addEventListener('click', (e) => {
      if (e.target.closest('.icon-btn')) return;
      playSong(i);
    });

    songListEl.appendChild(row);
  });

  const pct = Math.min((songs.length / 100) * 100, 100);
  storageFill.style.width = pct + '%';
  storageText.textContent = `${songs.length} song${songs.length !== 1 ? 's' : ''}`;
}

function escHtml(str) {
  return String(str).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

async function loadSongs() {
  try {
    const res = await fetch('/api/songs');
    songs = await res.json();
    renderSongs();
  } catch (e) {
    toast('Failed to load library', 'error');
  }
}

async function addSong() {
  const url = urlInput.value.trim();
  if (!url) return;
  if (!url.includes('youtube.com') && !url.includes('youtu.be')) {
    toast('Please enter a valid YouTube URL', 'error');
    return;
  }

  addBtn.disabled = true;
  toast('Downloading audio…', 'info', 0);

  try {
    const res = await fetch('/api/songs', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url }),
    });
    const data = await res.json();

    if (res.status === 409) { toast('Already in library', 'error'); addBtn.disabled = false; return; }
    if (!res.ok) { toast(data.detail || 'Error', 'error'); addBtn.disabled = false; return; }

    urlInput.value = '';
    const jobId = encodeURIComponent(url);
    pollDownload(jobId);
  } catch (e) {
    toast('Network error', 'error');
    addBtn.disabled = false;
  }
}

function pollDownload(jobId) {
  const interval = setInterval(async () => {
    try {
      const res = await fetch(`/api/songs/status/${jobId}`);
      const data = await res.json();

      if (data.status === 'done') {
        clearInterval(interval);
        toast(`Added: ${data.title}`, 'success');
        addBtn.disabled = false;
        loadSongs();
      } else if (data.status === 'error') {
        clearInterval(interval);
        toast(data.message || 'Download failed', 'error');
        addBtn.disabled = false;
      }
    } catch (e) {
      clearInterval(interval);
      addBtn.disabled = false;
    }
  }, 1500);
  pollIntervals[jobId] = interval;
}

async function deleteSong(e, id) {
  e.stopPropagation();
  const idx = songs.findIndex(s => s.id === id);
  if (idx === currentIndex && isPlaying) {
    audio.pause();
    isPlaying = false;
    updatePlayBtn();
  }
  try {
    await fetch(`/api/songs/${id}`, { method: 'DELETE' });
    await loadSongs();
    toast('Removed from library', 'info');
  } catch (e) {
    toast('Delete failed', 'error');
  }
}

function playSong(index) {
  if (index < 0 || index >= songs.length) return;
  currentIndex = index;
  const song = songs[index];

  audio.src = `/api/stream/${song.id}`;
  audio.load();
  audio.play().catch(() => {});
  isPlaying = true;
  updatePlayBtn();
  updatePlayerMeta(song, index);
  renderSongs();
}

function updatePlayerMeta(song, colorIdx) {
  playerTitle.textContent = song.title;
  playerArtist.textContent = song.artist || 'Unknown';

  playerThumb.innerHTML = song.thumbnail
    ? `<img src="${song.thumbnail}" style="width:100%;height:100%;object-fit:cover" />`
    : `<div style="width:100%;height:100%;background:${colorForIndex(colorIdx)}"></div>`;

  document.title = `${song.title} — melodix`;
  if ('mediaSession' in navigator) {
    navigator.mediaSession.metadata = new MediaMetadata({
      title: song.title,
      artist: song.artist || 'Unknown',
      artwork: song.thumbnail ? [{ src: song.thumbnail }] : [],
    });
  }
}

function togglePlay() {
  if (currentIndex < 0 && songs.length > 0) { playSong(0); return; }
  if (audio.paused) {
    audio.play().catch(() => {});
    isPlaying = true;
  } else {
    audio.pause();
    isPlaying = false;
  }
  updatePlayBtn();
}

function updatePlayBtn() {
  playIcon.style.display = isPlaying ? 'none' : 'block';
  pauseIcon.style.display = isPlaying ? 'block' : 'none';
}

function playNext() {
  if (songs.length === 0) return;
  let next;
  if (isShuffle) {
    next = Math.floor(Math.random() * songs.length);
  } else {
    next = (currentIndex + 1) % songs.length;
  }
  playSong(next);
}

function playPrev() {
  if (songs.length === 0) return;
  if (audio.currentTime > 3) { audio.currentTime = 0; return; }
  const prev = (currentIndex - 1 + songs.length) % songs.length;
  playSong(prev);
}

function toggleShuffle() {
  isShuffle = !isShuffle;
  document.getElementById('shuffleBtn').classList.toggle('active', isShuffle);
}

function seekTo(e) {
  const bar = document.getElementById('progressBar');
  const rect = bar.getBoundingClientRect();
  const pct = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
  if (audio.duration) audio.currentTime = pct * audio.duration;
}

function setVolume(val) {
  audio.volume = val / 100;
}

audio.addEventListener('timeupdate', () => {
  if (!audio.duration) return;
  const pct = (audio.currentTime / audio.duration) * 100;
  progressFill.style.width = pct + '%';
  progressThumb.style.left = pct + '%';
  currentTimeEl.textContent = fmtTime(audio.currentTime);
});

audio.addEventListener('loadedmetadata', () => {
  totalTimeEl.textContent = fmtTime(audio.duration);
});

audio.addEventListener('ended', () => {
  isPlaying = false;
  updatePlayBtn();
  playNext();
});

audio.addEventListener('play', () => { isPlaying = true; updatePlayBtn(); });
audio.addEventListener('pause', () => { isPlaying = false; updatePlayBtn(); });

if ('mediaSession' in navigator) {
  navigator.mediaSession.setActionHandler('play', () => { audio.play(); });
  navigator.mediaSession.setActionHandler('pause', () => { audio.pause(); });
  navigator.mediaSession.setActionHandler('nexttrack', playNext);
  navigator.mediaSession.setActionHandler('previoustrack', playPrev);
}

urlInput.addEventListener('keydown', (e) => { if (e.key === 'Enter') addSong(); });

audio.volume = 0.8;
loadSongs();
