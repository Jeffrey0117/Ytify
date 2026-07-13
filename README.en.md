<p align="center">
  <img src="static/logo.png" alt="Ytify Logo" width="100">
  <br>
  <b>Ytify</b>
</p>

<p align="center">
  <b>Self-Hosted YouTube Downloader — Private, Stable, Controllable</b>
  <br>
  Tired of ads, throttling, and shutdowns on public download sites? Host your own, free forever.
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License"></a>
  <a href="https://github.com/Jeffrey0117/Ytify/stargazers"><img src="https://img.shields.io/github/stars/Jeffrey0117/Ytify" alt="GitHub stars"></a>
</p>

<p align="center">
  <a href="#-quick-start-30-seconds">Quick Start</a> ·
  <a href="https://jeffrey0117.github.io/Ytify/en.html#tampermonkey">Script Install</a> ·
  <a href="https://jeffrey0117.github.io/Ytify/en.html">Website</a>
</p>

<p align="center">
  <a href="README.md">繁體中文</a> | <a href="README.zh-CN.md">简体中文</a> | English
</p>

## 🔍 How It Works

```
┌─────────────┐    Download Request   ┌──────────────┐     yt-dlp     ┌─────────┐
│   Browser   │ ───────────────────→  │ Ytify Server │ ─────────────→ │ YouTube │
│ (Your PC)   │ ←───────────────────  │  (Your PC)   │ ←───────────── │         │
└─────────────┘    Return File        └──────────────┘   Video Data   └─────────┘
```

1. You click download in your browser
2. Ytify server receives the request and uses yt-dlp to fetch the video from YouTube
3. Video downloads to server, then streams back to your browser

---

## ✨ Why Choose Ytify?

| Public Download Sites | Ytify |
|:---:|:---:|
| 🐌 Throttled, Queued | ⚡ Full Speed Downloads |
| 🚫 Shutdown Anytime | 🏠 Your Server, Always Available |
| 👀 Downloads Tracked | 🔒 100% Private |
| 📺 Web-Only Interface | 🖱️ One-Click Download on YouTube |
| 💸 Pay to Unlock Features | 🆓 Completely Free & Open Source |

### Why Self-Host?

- **Privacy**: No third-party services, your data stays with you
- **Stability**: Not affected by public service limits or shutdowns
- **Control**: Customize quality, format, and storage location
- **Remote Access**: Use from anywhere with Cloudflare Tunnel

---

## 🚀 Quick Start (30 Seconds)

```bash
git clone https://github.com/Jeffrey0117/Ytify.git
cd Ytify
run.bat    # On Windows, double-click works too
```

That's it! Press Enter to select defaults and the service starts.

👉 Open http://localhost:8765 to start downloading

### 🎯 Zero-Config Installation

**Works on a fresh PC!** No need to pre-install anything, run.bat automatically:

- ✅ Detects and installs Python, FFmpeg, Git
- ✅ **Installed but not in PATH? Auto-detects and uses it**
- ✅ Installs all Python packages
- ✅ Sets up auto-update schedule

> 💡 Only requirement: Windows 10 1709+ or Windows 11 (needs winget)

---

## 🎯 Core Features

### 🔥 Concurrent Downloads
Download 3 videos simultaneously, no waiting in line

### 📱 Access Anywhere
Use from phone or office with Cloudflare Tunnel

### 🖱️ One-Click Download
Install Tampermonkey script for download buttons directly on YouTube

### 🔄 Auto Updates
Syncs latest version every 5 minutes, updates don't interrupt downloads

### 📋 Playlist Support
Download entire playlists at once, up to 50 videos

### 🎵 Multiple Formats
Best Quality / 1080p / 720p / 480p / Audio Only MP3

### ✂️ Clip Sections
Download only from second X to second Y — the userscript grabs the player's current time with one click (max 30 min per clip)

---

## 📥 Two Ways to Use

### Method 1: Web Interface
Open `http://localhost:8765`, paste URL and download

### Method 2: Tampermonkey Script ⭐Recommended
Download buttons appear directly on YouTube video pages!

1. Install [Tampermonkey](https://www.tampermonkey.net/) browser extension
2. Create new script, paste contents of `scripts/ytify.user.js`
3. See download button on YouTube, click to select quality

> 📖 [Full Installation Guide](https://jeffrey0117.github.io/Ytify/en.html#tampermonkey)

---

## 🖥️ Startup Modes

| Mode | Resources | Auto Update | Best For |
|:---:|:---:|:---:|:---:|
| 🐳 Docker | 4GB+ RAM | ✅ | High-spec machines |
| 🐍 Python | Low | ❌ | Temporary use |
| 🚀 **Python + Auto Update** | Low | ✅ | **Recommended** |

> 💡 Not sure which to pick? Just press Enter for the recommended option

---

## 🌐 Remote Access (Optional)

Want to use from phone or outside network? Run the setup wizard:

```bash
setup-tunnel.bat
```

Choose your mode:

| Mode | Domain Needed | URL | Best For |
|:---:|:---:|:---:|:---:|
| ⚡ Quick Tunnel | ❌ | Changes each time | Temporary sharing |
| 🔗 Fixed URL | ✅ | Permanent | Long-term use |

<details>
<summary>Manual setup</summary>

### Quick Tunnel (No Domain)

```bash
cloudflared tunnel --url http://localhost:8765
```

### Fixed URL (Domain Required)

```bash
# First-time setup
cloudflared tunnel login
cloudflared tunnel create ytify
cloudflared tunnel route dns ytify ytify.yourdomain.com

# After that, run.bat auto-starts tunnel
```

</details>

---

## 🛠️ Web Pages

| Page | Description |
|------|------|
| `/download` | Download Interface |
| `/playlist` | Playlist Download |
| `/history` | Download History |
| `/files` | File Management |
| `/dashboard` | System Status |

---

## ❓ FAQ

<details>
<summary><b>Downloaded video has no sound?</b></summary>

Install FFmpeg:
- Windows: `winget install FFmpeg`
- Linux: `sudo apt install ffmpeg`
</details>

<details>
<summary><b>Tampermonkey script not working?</b></summary>

1. Confirm Ytify service is running
2. Click script's Info button to check connection status
3. If using remote server, modify server address in script
</details>

<details>
<summary><b>Will auto-update interrupt downloads?</b></summary>

No! Ytify has a "graceful restart" mechanism that waits for all downloads to complete before updating.
</details>

<details>
<summary><b>Which sites are supported?</b></summary>

Ytify uses yt-dlp, supporting YouTube, Bilibili, Twitter, and [1000+ sites](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md).
</details>

---

## 📊 Version History

### v10.7 (2025-01) - Latest
- ✨ Failed task "Retry" button
- ✨ Task "Close" button
- ✨ Panel "Clear" button
- 🐛 Fixed multi-task download blocking issue
- 🐛 Fixed rapid consecutive download freeze issue

### v10.6 (2025-01)
- ✨ Concurrent downloads (up to 3 simultaneous)
- ✨ Graceful restart mechanism
- ✨ Offline server address modification

<details>
<summary>Earlier versions...</summary>

### v10.5 (2025-01)
- ✨ Real-time connection status detection
- ✨ Offline-friendly prompts

### v10.0 (2024-12)
- ✨ WebSocket real-time progress
- ✨ Playlist batch download
- ✨ Proxy pool support
</details>

---

## 🤝 Contributing

Issues and PRs welcome!

---

## 📜 License

MIT - Free to use, modify, and distribute

---

<p align="center">
  <b>⭐ If you find this useful, give it a Star!</b>
</p>
