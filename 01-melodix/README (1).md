# 01-melodix

Your music. Your server. No subscriptions.

Paste a YouTube link → audio extracted → stream from your server → listen on any device, screen off, no ads.

---

## Stack

- **Backend** — FastAPI + yt-dlp + SQLite
- **Frontend** — Vanilla HTML/CSS/JS (dark tech UI)
- **Audio** — HTTP range streaming, MediaSession API (lock screen controls)
- **PWA** — installable on mobile, works offline for cached tracks

---

## Quick start

```bash
git clone <your-repo>
cd 01-melodix
chmod +x run.sh
./run.sh
```

Then open **http://localhost:8000** in your browser (or your server's IP on mobile).

---

## Project structure

```
01-melodix/
├── app/
│   ├── main.py            # FastAPI app, routes registration
│   ├── downloader.py      # yt-dlp audio extraction
│   ├── models/
│   │   └── database.py    # SQLite init + connection
│   └── routes/
│       ├── songs.py       # GET/POST/DELETE /api/songs
│       └── stream.py      # GET /api/stream/:id  (range streaming)
├── frontend/
│   ├── templates/
│   │   └── index.html     # Main SPA
│   └── static/
│       ├── css/style.css  # Dark tech UI
│       ├── js/app.js      # Player logic, API calls
│       └── manifest.json  # PWA manifest
├── music/                 # mp3 files stored here (gitignored)
├── melodix.db             # SQLite database (gitignored)
├── requirements.txt
└── run.sh
```

---

## API reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/songs` | List all songs |
| POST | `/api/songs` | Add song `{ "url": "https://youtube.com/..." }` |
| GET | `/api/songs/status/{job_id}` | Poll download progress |
| DELETE | `/api/songs/{id}` | Remove song + file |
| GET | `/api/stream/{id}` | Stream audio (supports HTTP range) |

---

## Mobile setup

1. Open `http://<your-server-ip>:8000` in Safari/Chrome
2. "Add to Home Screen" → installs as PWA
3. Play music → lock screen controls work via MediaSession API
4. Screen off = music keeps playing ✓

---

## Deployment (later)

- VPS: Hetzner CX22 (~€4/month)
- Reverse proxy: Nginx
- Process manager: systemd or PM2
- SSL: Cloudflare or Let's Encrypt

---

## Roadmap

- [ ] Playlist management
- [ ] Search / filter
- [ ] Equalizer
- [ ] Bulk import
- [ ] Mobile swipe gestures
