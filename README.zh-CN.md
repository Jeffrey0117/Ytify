<p align="center">
  <img src="static/logo.png" alt="Ytify Logo" width="100">
  <br>
  <b>Ytify</b>
</p>

<p align="center">
  <b>自建 YouTube 下载服务器 — 隐私、稳定、可控</b>
  <br>
  厌倦了公共下载站的广告、限速、关站？自己搭一个，永久免费用。
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License"></a>
  <a href="https://github.com/Jeffrey0117/Ytify/stargazers"><img src="https://img.shields.io/github/stars/Jeffrey0117/Ytify" alt="GitHub stars"></a>
</p>

<p align="center">
  <a href="#-30-秒快速开始">快速开始</a> ·
  <a href="https://jeffrey0117.github.io/Ytify/zh-CN.html#tampermonkey">脚本安装</a> ·
  <a href="https://jeffrey0117.github.io/Ytify/zh-CN.html">官方网站</a>
</p>

<p align="center">
  <a href="README.md">繁體中文</a> | 简体中文 | <a href="README.en.md">English</a>
</p>

## 🔍 运作原理

```
┌─────────────┐     请求下载      ┌──────────────┐     yt-dlp     ┌─────────┐
│   浏览器     │ ───────────────→ │  Ytify 服务器 │ ─────────────→ │ YouTube │
│ (你的电脑)   │ ←─────────────── │  (你的电脑)   │ ←───────────── │         │
└─────────────┘     返回文件      └──────────────┘     视频数据     └─────────┘
```

1. 你在浏览器点击下载
2. Ytify 服务器收到请求，使用 yt-dlp 从 YouTube 抓取视频
3. 视频下载到服务器后，再传回你的浏览器

---

## ✨ 为什么选 Ytify？

| 公共下载站 | Ytify |
|:---:|:---:|
| 🐌 限速、排队 | ⚡ 满速下载 |
| 🚫 随时关站 | 🏠 自己的服务器永远在 |
| 👀 下载记录被追踪 | 🔒 100% 隐私 |
| 📺 只能网页操作 | 🖱️ YouTube 页面一键下载 |
| 💸 付费解锁功能 | 🆓 完全免费开源 |

### 为什么要自建？

- **隐私**：不经过第三方服务，数据不外泄
- **稳定**：不受公共服务限制或关站影响
- **可控**：自定义画质、格式、存储位置
- **远程**：搭配 Cloudflare Tunnel 可从任何地方使用

---

## 🚀 30 秒快速开始

```bash
git clone https://github.com/Jeffrey0117/Ytify.git
cd Ytify
run.bat    # Windows 双击执行也可以
```

就这样！按 Enter 选默认选项，服务就启动了。

👉 打开 http://localhost:8765 开始下载

### 🎯 零配置安装

**全新电脑也能跑！** 不需要预先安装任何东西，run.bat 会自动：

- ✅ 检测并安装 Python、FFmpeg、Git
- ✅ **已安装但没加 PATH？自动找到并使用**
- ✅ 安装所有 Python 包
- ✅ 设置自动更新计划

> 💡 唯一前提：Windows 10 1709+ 或 Windows 11（需要 winget）

---

## 🎯 核心功能

### 🔥 并发下载
同时下载 3 个视频，不用一个一个等

### 📱 随处可用
搭配 Cloudflare Tunnel，手机、办公室都能用

### 🖱️ 一键下载
安装 Tampermonkey 脚本，在 YouTube 页面直接点击下载

### 🔄 自动更新
每 5 分钟自动同步最新版本，更新时不中断下载

### 📋 播放列表
一次下载整个播放列表，最多 50 个

### 🎵 多种格式
最佳画质 / 1080p / 720p / 480p / 仅音频 MP3

---

## 📥 两种使用方式

### 方式一：网页界面
打开 `http://localhost:8765`，粘贴网址即可下载

### 方式二：Tampermonkey 脚本 ⭐推荐
在 YouTube 视频页面直接出现下载按钮！

1. 安装 [Tampermonkey](https://www.tampermonkey.net/) 浏览器扩展
2. 新建脚本，粘贴 `scripts/ytify.user.js` 内容
3. 在 YouTube 看到下载按钮，点击选择画质

> 📖 [完整安装教程](https://jeffrey0117.github.io/Ytify/zh-CN.html#tampermonkey)

---

## 🖥️ 启动模式

| 模式 | 资源需求 | 自动更新 | 适合 |
|:---:|:---:|:---:|:---:|
| 🐳 Docker | 4GB+ RAM | ✅ | 高配电脑 |
| 🐍 Python | 低 | ❌ | 临时使用 |
| 🚀 **Python + 自动更新** | 低 | ✅ | **推荐** |

> 💡 不知道选哪个？直接按 Enter，默认就是最推荐的选项

---

## 🌐 远程访问（可选）

想从手机或外网使用？有两种方式：

### 方式一：快速隧道（无需域名）⚡

最简单的方式，适合临时使用或没有域名的人：

```bash
# 1. 安装 cloudflared
winget install Cloudflare.cloudflared

# 2. 启动快速隧道（每次网址不同）
cloudflared tunnel --url http://localhost:8765
```

会自动产生类似 `https://xxx-yyy-zzz.trycloudflare.com` 的临时网址。

> ⚠️ 每次执行网址都会变，适合临时分享使用

### 方式二：固定网址（需要域名）🔗

适合长期使用，网址永久固定：

**前置需求：**
- Cloudflare 账号（免费）
- 已加入 Cloudflare 的域名

**首次设置（只需一次）：**

```bash
# 1. 安装 cloudflared
winget install Cloudflare.cloudflared

# 2. 登录 Cloudflare（会打开浏览器）
cloudflared tunnel login

# 3. 创建名为 ytify 的 tunnel
cloudflared tunnel create ytify

# 4. 设置 DNS（改成你要的网址）
cloudflared tunnel route dns ytify ytify.你的域名.com
```

**日常使用：**

设置完成后，执行 `run.bat` 会自动启动 tunnel。

> 💡 Tunnel 名称固定为 `ytify`，脚本会自动使用这个名称

---

## 🛠️ 网页功能

| 页面 | 说明 |
|------|------|
| `/download` | 下载界面 |
| `/playlist` | 播放列表下载 |
| `/history` | 下载历史 |
| `/files` | 文件管理 |
| `/dashboard` | 系统状态 |

---

## ❓ 常见问题

<details>
<summary><b>下载的视频没有声音？</b></summary>

安装 FFmpeg：
- Windows: `winget install FFmpeg`
- Linux: `sudo apt install ffmpeg`
</details>

<details>
<summary><b>Tampermonkey 脚本没反应？</b></summary>

1. 确认 Ytify 服务已启动
2. 点击脚本的 Info 按钮检查连接状态
3. 如果是远程服务器，修改脚本中的服务器地址
</details>

<details>
<summary><b>自动更新会中断下载吗？</b></summary>

不会！Ytify 有「优雅重启」机制，会等所有下载任务完成后才更新重启。
</details>

<details>
<summary><b>支持哪些网站？</b></summary>

Ytify 使用 yt-dlp，支持 YouTube、Bilibili、Twitter 等 [1000+ 网站](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md)。
</details>

---

## 📊 版本历史

### v10.7 (2025-01) - 最新
- ✨ 失败任务「重试」按钮
- ✨ 任务「关闭」按钮
- ✨ 面板「清除」按钮
- 🐛 修复多任务下载阻塞问题
- 🐛 修复快速连续下载卡住问题

### v10.6 (2025-01)
- ✨ 并发下载（最多 3 个同时）
- ✨ 优雅重启机制
- ✨ 离线时可修改服务器位置

<details>
<summary>更早版本...</summary>

### v10.5 (2025-01)
- ✨ 连接状态即时检测
- ✨ 离线友好提示

### v10.0 (2024-12)
- ✨ WebSocket 即时进度
- ✨ 播放列表批量下载
- ✨ 代理池支持
</details>

---

## 🤝 贡献

欢迎 Issue 和 PR！

---

## 📜 License

MIT - 自由使用、修改、分发

---

<p align="center">
  <b>⭐ 如果觉得好用，给个 Star 支持一下！</b>
</p>
