// ==UserScript==
// @name         ytify Downloader
// @namespace    http://tampermonkey.net/
// @license MIT
// @version      10.8.0
// @description  搭配 ytify 自架伺服器，在 YouTube 頁面一鍵下載影片
// @author       Jeffrey
// @match        https://www.youtube.com/*
// @match        https://youtube.com/*
// @grant        GM_xmlhttpRequest
// @grant        GM_addStyle
// @connect      localhost
// @connect      127.0.0.1
// @connect      *.trycloudflare.com
// @connect      *
// @run-at       document-idle
// @homepageURL  https://jeffrey0117.github.io/Ytify/
// @supportURL   https://github.com/Jeffrey0117/Ytify/issues
// ==/UserScript==

/**
 * ytify Downloader v10.8.0
 * - 新增：✂️ 剪片段——只下載影片的某一段（起訖可一鍵抓播放器當前時間）
 *
 * v10.7.3:
 * - 改進：下載完成後任務自動從面板消失（1.5 秒後）
 * - 移除：完成任務不再顯示多餘按鈕，下載已自動觸發
 *
 * v10.7.2:
 * - 修復：多任務下載不再阻塞（移除 /api/info 預先請求）
 * - 修復：快速連續下載時任務卡住的問題
 *
 * v10.7.1:
 * - 修復：失敗任務不自動消失，等待用戶手動關閉或重試
 *
 * v10.7:
 * - 新增：失敗任務「重試」按鈕
 * - 新增：任務「關閉」按鈕
 *
 * 官方網站: https://jeffrey0117.github.io/Ytify/
 * GitHub:  https://github.com/Jeffrey0117/Ytify
 */

(function() {
    'use strict';

    // ╔════════════════════════════════════════════════════════════╗
    // ║                    🔧 使用者設定區                          ║
    // ║          修改下方網址為你的 ytify 服務位置                   ║
    // ╚════════════════════════════════════════════════════════════╝

    const YTIFY_API_URL_DEFAULT = 'http://localhost:8765';
    const YTIFY_API_URL = localStorage.getItem('ytify_api_url') || YTIFY_API_URL_DEFAULT;

    // 範例：
    // const YTIFY_API_URL = 'http://localhost:8765';           // 本地
    // const YTIFY_API_URL = 'https://ytify.你的域名.com';       // 自訂域名
    // const YTIFY_API_URL = 'https://xxx.trycloudflare.com';   // 臨時 tunnel

    // ═══════════════════════════════════════════════════════════════

    const CONFIG = {
        YTIFY_API: YTIFY_API_URL,
        POLL_INTERVAL: 1500,
        POLL_TIMEOUT: 600000,
    };

    const YTIFY_FORMATS = [
        { format: 'best', label: '最佳畫質', audioOnly: false },
        { format: '1080p', label: '1080p', audioOnly: false },
        { format: '720p', label: '720p', audioOnly: false },
        { format: '480p', label: '480p', audioOnly: false },
        { format: 'best', label: '僅音訊', audioOnly: true },
    ];

    GM_addStyle(`
        .ytdl-btn {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 8px 16px;
            margin-left: 8px;
            background: #065fd4;
            color: white;
            border: none;
            border-radius: 18px;
            font-size: 14px;
            font-weight: 500;
            cursor: pointer;
        }
        .ytdl-btn:hover { background: #0056b8; }
        .ytdl-btn svg { width: 18px; height: 18px; }
        .ytdl-btn .badge {
            background: #f44336;
            color: white;
            font-size: 11px;
            padding: 1px 6px;
            border-radius: 10px;
            margin-left: 4px;
        }
        .ytdl-menu {
            position: absolute;
            top: 100%;
            left: 0;
            margin-top: 8px;
            background: #212121;
            border-radius: 10px;
            padding: 6px 0;
            min-width: 160px;
            box-shadow: 0 4px 32px rgba(0,0,0,0.4);
            z-index: 9999;
            display: none;
        }
        .ytdl-menu.show { display: block; }
        .ytdl-menu-header {
            padding: 6px 12px 4px;
            color: #888;
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 4px;
        }
        .ytdl-menu-header svg { width: 12px; height: 12px; flex-shrink: 0; }
        .ytdl-menu-item {
            padding: 7px 12px;
            color: white;
            cursor: pointer;
            font-size: 13px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .ytdl-menu-item:hover { background: #3a3a3a; }
        .ytdl-menu-item.disabled { color: #666; cursor: not-allowed; }
        .ytdl-menu-item.disabled:hover { background: transparent; }
        .ytdl-menu-item svg { width: 14px; height: 14px; opacity: 0.7; }
        .ytdl-wrapper { position: relative; display: inline-block; }
        .ytdl-ytify-status {
            display: inline-flex;
            align-items: center;
            gap: 4px;
            font-size: 10px;
            padding: 2px 6px;
            border-radius: 4px;
            margin-left: auto;
        }
        .ytdl-ytify-status.online { background: #4caf50; color: #fff; font-weight: 500; }
        .ytdl-ytify-status.offline { background: #f44336; color: #fff; font-weight: 500; }

        /* ===== 下載面板 ===== */
        .ytdl-panel {
            position: fixed;
            bottom: 24px;
            right: 24px;
            width: 360px;
            background: #1a1a1a;
            border-radius: 12px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.6);
            z-index: 999999;
            font-family: 'Roboto', Arial, sans-serif;
            overflow: hidden;
            transform: translateY(calc(100% + 30px));
            transition: transform 0.3s ease;
        }
        .ytdl-panel.show { transform: translateY(0); }
        .ytdl-panel.minimized .ytdl-panel-body { display: none; }
        .ytdl-panel-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 12px 16px;
            background: #282828;
            cursor: pointer;
            user-select: none;
        }
        .ytdl-panel-header:hover { background: #333; }
        .ytdl-panel-title {
            display: flex;
            align-items: center;
            gap: 8px;
            color: white;
            font-weight: 500;
            font-size: 14px;
        }
        .ytdl-panel-title svg { width: 18px; height: 18px; }
        .ytdl-panel-badge {
            background: #065fd4;
            color: white;
            font-size: 11px;
            padding: 2px 8px;
            border-radius: 10px;
        }
        .ytdl-panel-actions {
            display: flex;
            gap: 8px;
        }
        .ytdl-panel-btn {
            background: transparent;
            border: none;
            color: #888;
            cursor: pointer;
            padding: 4px;
            border-radius: 4px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .ytdl-panel-btn:hover { background: #444; color: white; }
        .ytdl-panel-btn svg { width: 16px; height: 16px; }
        .ytdl-panel-body {
            max-height: 300px;
            overflow-y: auto;
        }
        .ytdl-panel-empty {
            padding: 24px;
            text-align: center;
            color: #666;
            font-size: 13px;
        }

        /* 任務項目 */
        .ytdl-task {
            padding: 12px 16px;
            border-bottom: 1px solid #333;
        }
        .ytdl-task:last-child { border-bottom: none; }
        .ytdl-task-header {
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            margin-bottom: 8px;
        }
        .ytdl-task-title {
            color: white;
            font-size: 13px;
            font-weight: 500;
            max-width: 260px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        .ytdl-task-status {
            font-size: 11px;
            padding: 2px 6px;
            border-radius: 4px;
            flex-shrink: 0;
        }
        .ytdl-task-status.downloading { background: #065fd4; color: white; }
        .ytdl-task-status.queued { background: #666; color: white; }
        .ytdl-task-status.merging { background: #9c27b0; color: white; }
        .ytdl-task-status.processing { background: #ff9800; color: white; }
        .ytdl-task-status.completed { background: #4caf50; color: white; }
        .ytdl-task-status.failed { background: #f44336; color: white; }
        .ytdl-task-info {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 6px;
        }
        .ytdl-task-sub {
            color: #888;
            font-size: 12px;
        }
        .ytdl-task-progress {
            color: #3ea6ff;
            font-size: 12px;
            font-weight: 500;
        }
        .ytdl-task-bar {
            height: 3px;
            background: #444;
            border-radius: 2px;
            overflow: hidden;
        }
        .ytdl-task-bar-fill {
            height: 100%;
            background: #3ea6ff;
            transition: width 0.3s ease;
        }
        .ytdl-task-bar-fill.anim {
            animation: ytdl-pulse 1.5s ease-in-out infinite;
            width: 30% !important;
        }
        .ytdl-task-bar-fill.done { background: #4caf50; }
        .ytdl-task-bar-fill.fail { background: #f44336; }

        /* 任務操作按鈕 */
        .ytdl-task-actions {
            display: flex;
            gap: 8px;
            margin-top: 8px;
        }
        .ytdl-task-action-btn {
            flex: 1;
            padding: 6px 12px;
            border: none;
            border-radius: 4px;
            font-size: 12px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 4px;
            transition: background 0.2s;
        }
        .ytdl-task-action-btn.retry {
            background: #ff9800;
            color: white;
        }
        .ytdl-task-action-btn.retry:hover { background: #f57c00; }
        .ytdl-task-action-btn.download {
            background: #4caf50;
            color: white;
        }
        .ytdl-task-action-btn.download:hover { background: #388e3c; }
        .ytdl-task-action-btn.dismiss {
            background: #333;
            color: #aaa;
        }
        .ytdl-task-action-btn.dismiss:hover { background: #444; color: white; }

        /* 完成訊息 */
        .ytdl-task-message {
            font-size: 11px;
            color: #4caf50;
            margin-top: 4px;
        }
        .ytdl-task-message.error {
            color: #f44336;
        }

        @keyframes ytdl-pulse {
            0%, 100% { margin-left: 0; }
            50% { margin-left: 70%; }
        }

        .ytdl-panel-body::-webkit-scrollbar { width: 6px; }
        .ytdl-panel-body::-webkit-scrollbar-track { background: #1a1a1a; }
        .ytdl-panel-body::-webkit-scrollbar-thumb { background: #444; border-radius: 3px; }

        /* ===== Info 按鈕與 Popup ===== */
        .ytdl-info-btn {
            display: inline-flex;
            align-items: center;
            margin-left: 10px;
            background: transparent;
            color: #ff4444;
            border: none;
            font-size: 12px;
            cursor: pointer;
            transition: color 0.2s ease;
            vertical-align: middle;
            padding: 0;
        }
        .ytdl-info-btn:hover {
            color: #ff8888;
        }
        .ytdl-info-overlay {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.5);
            z-index: 99998;
            display: none;
        }
        .ytdl-info-overlay.show { display: block; }
        .ytdl-info-popup {
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: #212121;
            border-radius: 12px;
            padding: 20px;
            min-width: 300px;
            max-width: 380px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.6);
            z-index: 99999;
            display: none;
            color: #ffffff;
            font-family: 'Roboto', Arial, sans-serif;
        }
        .ytdl-info-popup.show { display: block; }
        .ytdl-info-popup-title {
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 12px;
            color: #ffffff;
        }
        .ytdl-info-popup-divider {
            height: 1px;
            background: #3a3a3a;
            margin: 12px 0;
        }
        .ytdl-info-popup-link {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 10px 12px;
            margin: 4px -12px;
            color: #ffffff;
            text-decoration: none;
            border-radius: 8px;
            transition: background 0.2s ease;
            cursor: pointer;
        }
        .ytdl-info-popup-link:hover {
            background: #383838;
        }
        .ytdl-info-popup-link-icon {
            font-size: 16px;
            width: 24px;
            text-align: center;
        }
        .ytdl-info-popup-link-text {
            font-size: 14px;
        }
        .ytdl-info-popup-server {
            padding: 10px 12px;
            margin: 4px -12px;
            background: #2a2a2a;
            border-radius: 8px;
        }
        .ytdl-info-popup-server-label {
            font-size: 12px;
            color: #aaaaaa;
            margin-bottom: 4px;
        }
        .ytdl-info-popup-server-value {
            font-size: 14px;
            color: #ffffff;
            word-break: break-all;
        }
        .ytdl-info-popup-hint {
            font-size: 11px;
            color: #aaaaaa;
            margin-top: 8px;
            text-align: center;
        }
        .ytdl-info-popup-server-row {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 8px;
        }
        .ytdl-info-popup-server-value {
            flex: 1;
        }
        .ytdl-info-popup-edit-btn {
            background: #3a3a3a;
            border: none;
            color: #aaa;
            font-size: 11px;
            padding: 4px 8px;
            border-radius: 4px;
            cursor: pointer;
            white-space: nowrap;
        }
        .ytdl-info-popup-edit-btn:hover {
            background: #4a4a4a;
            color: #fff;
        }

        /* ===== 離線按鈕樣式 ===== */
        .ytdl-btn.offline {
            background: #ff9800;
            cursor: pointer;
        }
        .ytdl-btn.offline:hover { background: #e68900; }

        /* ===== 離線 Popup ===== */
        .ytdl-offline-popup {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.7);
            z-index: 9999999;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .ytdl-offline-popup-content {
            background: #212121;
            border-radius: 12px;
            padding: 24px;
            max-width: 420px;
            width: 90%;
            box-shadow: 0 8px 32px rgba(0,0,0,0.6);
            font-family: 'Roboto', Arial, sans-serif;
        }
        .ytdl-offline-popup-header {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 16px;
            color: #ff9800;
            font-size: 18px;
            font-weight: 600;
        }
        .ytdl-offline-popup-url {
            background: #333;
            padding: 8px 12px;
            border-radius: 6px;
            font-family: monospace;
            font-size: 12px;
            color: #3ea6ff;
            margin-bottom: 16px;
            word-break: break-all;
        }
        .ytdl-offline-popup-url-label {
            color: #888;
            font-size: 12px;
            margin-bottom: 4px;
        }
        .ytdl-offline-popup-reasons {
            margin-bottom: 20px;
        }
        .ytdl-offline-popup-reasons-title {
            color: #ccc;
            font-size: 13px;
            margin-bottom: 8px;
        }
        .ytdl-offline-popup-reasons ul {
            margin: 0;
            padding-left: 20px;
            color: #aaa;
            font-size: 13px;
            line-height: 1.8;
        }
        .ytdl-offline-popup-reasons li {
            margin-bottom: 4px;
        }
        .ytdl-offline-popup-reasons code {
            background: #333;
            padding: 2px 6px;
            border-radius: 4px;
            font-family: monospace;
            color: #3ea6ff;
        }
        .ytdl-offline-popup-actions {
            display: flex;
            gap: 12px;
            justify-content: flex-end;
            flex-wrap: wrap;
        }
        .ytdl-offline-popup-btn {
            padding: 10px 18px;
            border-radius: 20px;
            border: none;
            font-size: 13px;
            font-weight: 500;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 6px;
            color: white;
        }
        .ytdl-offline-popup-btn.primary {
            background: #065fd4;
        }
        .ytdl-offline-popup-btn.primary:hover { background: #0056b8; }
        .ytdl-offline-popup-btn.secondary {
            background: #3a3a3a;
        }
        .ytdl-offline-popup-btn.secondary:hover { background: #4a4a4a; }
        .ytdl-offline-popup-btn.reconnecting {
            opacity: 0.7;
            cursor: wait;
        }
        .ytdl-offline-popup-input {
            width: 100%;
            padding: 10px 12px;
            background: #333;
            border: 1px solid #555;
            border-radius: 6px;
            font-family: monospace;
            font-size: 13px;
            color: #3ea6ff;
            margin-bottom: 16px;
            box-sizing: border-box;
        }
        .ytdl-offline-popup-input:focus {
            outline: none;
            border-color: #3ea6ff;
        }
        .ytdl-offline-popup-saved {
            color: #4caf50;
            font-size: 12px;
            margin-left: 8px;
            opacity: 0;
            transition: opacity 0.3s ease;
        }
        .ytdl-offline-popup-saved.show {
            opacity: 1;
        }
        .ytdl-clip-row {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 12px;
        }
        .ytdl-clip-row label {
            width: 40px;
            font-size: 13px;
            color: #aaa;
            flex-shrink: 0;
        }
        .ytdl-clip-row .ytdl-offline-popup-input {
            margin-bottom: 0;
            flex: 1;
        }
        .ytdl-clip-now-btn {
            padding: 8px 12px;
            border-radius: 6px;
            border: 1px solid #555;
            background: #333;
            color: #3ea6ff;
            font-size: 12px;
            cursor: pointer;
            white-space: nowrap;
            flex-shrink: 0;
        }
        .ytdl-clip-now-btn:hover { background: #3a3a3a; }
        .ytdl-clip-select {
            width: 100%;
            padding: 10px 12px;
            background: #333;
            border: 1px solid #555;
            border-radius: 6px;
            font-size: 13px;
            color: white;
            margin-bottom: 16px;
            box-sizing: border-box;
        }
        .ytdl-clip-error {
            color: #f28b82;
            font-size: 12px;
            margin-bottom: 12px;
            min-height: 14px;
        }
    `);

    // ===== 狀態管理 =====
    let videoId = null;
    let container = null;
    let panel = null;
    let infoPopup = null;
    let infoOverlay = null;
    let offlinePopup = null;
    let clipPopup = null;
    let ytifyOnline = false;
    const tasks = new Map();

    const getVideoId = () => new URLSearchParams(location.search).get('v');

    // ===== 剪片段時間工具 =====
    // 秒 → "1:23" / "1:02:03"
    const secToClock = (sec) => {
        const s = Math.floor(sec);
        const h = Math.floor(s / 3600);
        const m = Math.floor((s % 3600) / 60);
        const ss = String(s % 60).padStart(2, '0');
        return h > 0 ? `${h}:${String(m).padStart(2, '0')}:${ss}` : `${m}:${ss}`;
    };
    // "83" / "1:23" / "1:02:03" → 秒；無效回傳 NaN
    const parseClipTime = (str) => {
        const t = (str || '').trim();
        if (!t) return NaN;
        if (!/^[\d:.]+$/.test(t)) return NaN;
        const parts = t.split(':');
        if (parts.length > 3 || parts.some(p => p === '')) return NaN;
        return parts.reduce((acc, p) => acc * 60 + parseFloat(p), 0);
    };
    const getTitle = () => {
        const el = document.querySelector('h1 yt-formatted-string');
        return (el?.textContent?.trim() || 'video').replace(/[<>:"/\\|?*]/g, '');
    };

    // ===== SVG 建立（避免 innerHTML）=====
    function createSvg(pathD) {
        const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        svg.setAttribute('viewBox', '0 0 24 24');
        svg.setAttribute('fill', 'currentColor');
        const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        path.setAttribute('d', pathD);
        svg.appendChild(path);
        return svg;
    }

    const SVG_PATHS = {
        download: 'M12 16l-5-5h3V4h4v7h3l-5 5zm-7 2h14v2H5v-2z',
        local: 'M20 18c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2H4c-1.1 0-2 .9-2 2v10c0 1.1.9 2 2 2H0v2h24v-2h-4zM4 6h16v10H4V6z',
        video: 'M18 4l2 4h-3l-2-4h-2l2 4h-3l-2-4H8l2 4H7L5 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V4h-4z',
        audio: 'M12 3v10.55c-.59-.34-1.27-.55-2-.55-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4V7h4V3h-6z',
        minimize: 'M19 13H5v-2h14v2z',
        close: 'M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z',
    };

    // ===== API 請求 =====
    function ytifyRequest(method, path, data = null, timeout = 30000) {
        return new Promise((resolve, reject) => {
            GM_xmlhttpRequest({
                method,
                url: CONFIG.YTIFY_API + path,
                headers: { 'Content-Type': 'application/json' },
                data: data ? JSON.stringify(data) : null,
                timeout,
                onload: (res) => {
                    try {
                        const result = JSON.parse(res.responseText);
                        if (res.status >= 400) {
                            reject(new Error(result.detail || result.error || '請求失敗'));
                        } else {
                            resolve(result);
                        }
                    } catch {
                        res.status === 200 ? resolve({ status: 'ok' }) : reject(new Error('解析失敗'));
                    }
                },
                onerror: () => reject(new Error('無法連接 ytify 服務')),
                ontimeout: () => reject(new Error('請求超時')),
            });
        });
    }

    async function checkYtifyStatus() {
        try {
            await ytifyRequest('GET', '/health');
            ytifyOnline = true;
        } catch {
            ytifyOnline = false;
        }
        updateMenuStatus();
    }

    function updateMenuStatus() {
        const indicator = document.querySelector('.ytdl-ytify-indicator');
        if (indicator) {
            indicator.className = 'ytdl-ytify-status ytdl-ytify-indicator ' + (ytifyOnline ? 'online' : 'offline');
            indicator.textContent = ytifyOnline ? '已連線' : '離線';
        }
        document.querySelectorAll('.ytdl-menu-item[data-ytify]').forEach(item => {
            item.classList.toggle('disabled', !ytifyOnline);
        });

        // Update button state
        const btn = document.querySelector('.ytdl-btn');
        if (btn) {
            btn.classList.toggle('offline', !ytifyOnline);
        }
    }

    // ===== 下載面板 =====
    function getPanel() {
        if (!panel) {
            panel = document.createElement('div');
            panel.className = 'ytdl-panel';

            // Header
            const header = document.createElement('div');
            header.className = 'ytdl-panel-header';

            const title = document.createElement('div');
            title.className = 'ytdl-panel-title';
            title.appendChild(createSvg(SVG_PATHS.download));
            const titleText = document.createElement('span');
            titleText.textContent = '下載任務';
            title.appendChild(titleText);
            const badge = document.createElement('span');
            badge.className = 'ytdl-panel-badge';
            badge.textContent = '0';
            title.appendChild(badge);

            const actions = document.createElement('div');
            actions.className = 'ytdl-panel-actions';

            const clearAllBtn = document.createElement('button');
            clearAllBtn.className = 'ytdl-panel-btn ytdl-panel-clear';
            clearAllBtn.title = '清除全部';
            clearAllBtn.textContent = '清除';
            clearAllBtn.onclick = () => {
                tasks.clear();
                updatePanel();
                updateButtonBadge(0);
            };

            const minimizeBtn = document.createElement('button');
            minimizeBtn.className = 'ytdl-panel-btn ytdl-panel-minimize';
            minimizeBtn.title = '最小化';
            minimizeBtn.appendChild(createSvg(SVG_PATHS.minimize));

            const closeBtn = document.createElement('button');
            closeBtn.className = 'ytdl-panel-btn ytdl-panel-close';
            closeBtn.title = '關閉';
            closeBtn.appendChild(createSvg(SVG_PATHS.close));

            actions.append(clearAllBtn, minimizeBtn, closeBtn);
            header.append(title, actions);

            // Body
            const body = document.createElement('div');
            body.className = 'ytdl-panel-body';
            const empty = document.createElement('div');
            empty.className = 'ytdl-panel-empty';
            empty.textContent = '沒有進行中的下載';
            body.appendChild(empty);

            panel.append(header, body);

            // Events
            header.onclick = () => panel.classList.toggle('minimized');
            minimizeBtn.onclick = (e) => {
                e.stopPropagation();
                panel.classList.add('minimized');
            };
            closeBtn.onclick = (e) => {
                e.stopPropagation();
                panel.classList.remove('show');
            };

            document.body.appendChild(panel);
        }
        return panel;
    }

    function showPanel() {
        const p = getPanel();
        p.classList.add('show');
        p.classList.remove('minimized');
    }

    function updatePanel() {
        const p = getPanel();
        const body = p.querySelector('.ytdl-panel-body');
        const badge = p.querySelector('.ytdl-panel-badge');
        const activeCount = [...tasks.values()].filter(t => !['completed', 'failed'].includes(t.status)).length;

        badge.textContent = activeCount;
        updateButtonBadge(activeCount);

        // 清空 body
        while (body.firstChild) {
            body.removeChild(body.firstChild);
        }

        if (tasks.size === 0) {
            const empty = document.createElement('div');
            empty.className = 'ytdl-panel-empty';
            empty.textContent = '沒有進行中的下載';
            body.appendChild(empty);
            return;
        }

        tasks.forEach((task, taskId) => {
            const el = document.createElement('div');
            el.className = 'ytdl-task';
            el.dataset.taskId = taskId;

            const statusClass = task.status || 'queued';
            const statusText = {
                queued: '排隊中',
                downloading: '下載中',
                merging: '合併中',
                processing: '處理中',
                completed: '完成',
                failed: '失敗',
                retrying: '重試中'
            }[statusClass] || statusClass;

            const progress = task.progress || 0;
            const isLoading = ['queued', 'merging', 'processing', 'retrying'].includes(task.status);
            const isDone = task.status === 'completed';
            const isFail = task.status === 'failed';

            // Task header
            const taskHeader = document.createElement('div');
            taskHeader.className = 'ytdl-task-header';

            const taskTitle = document.createElement('div');
            taskTitle.className = 'ytdl-task-title';
            taskTitle.title = task.title || '';
            taskTitle.textContent = task.title || '載入中...';

            const taskStatus = document.createElement('div');
            taskStatus.className = 'ytdl-task-status ' + statusClass;
            taskStatus.textContent = statusText;

            taskHeader.append(taskTitle, taskStatus);

            // Task info
            const taskInfo = document.createElement('div');
            taskInfo.className = 'ytdl-task-info';

            const taskSub = document.createElement('div');
            taskSub.className = 'ytdl-task-sub';
            taskSub.textContent = (task.format || '') + ' ' + (task.speed || '');

            const taskProgress = document.createElement('div');
            taskProgress.className = 'ytdl-task-progress';
            taskProgress.textContent = isDone ? '100%' : isFail ? '' : Math.round(progress) + '%';

            taskInfo.append(taskSub, taskProgress);

            // Task bar
            const taskBar = document.createElement('div');
            taskBar.className = 'ytdl-task-bar';

            const taskBarFill = document.createElement('div');
            taskBarFill.className = 'ytdl-task-bar-fill';
            if (isLoading) taskBarFill.classList.add('anim');
            if (isDone) taskBarFill.classList.add('done');
            if (isFail) taskBarFill.classList.add('fail');
            taskBarFill.style.width = (isDone ? 100 : isFail ? 100 : progress) + '%';

            taskBar.appendChild(taskBarFill);

            el.append(taskHeader, taskInfo, taskBar);

            // 失敗時顯示訊息和按鈕（完成的任務會自動消失，不需要按鈕）
            if (isFail) {
                // 錯誤訊息
                const message = document.createElement('div');
                message.className = 'ytdl-task-message error';
                message.textContent = task.error || '下載失敗';
                el.appendChild(message);

                // 操作按鈕
                const actions = document.createElement('div');
                actions.className = 'ytdl-task-actions';

                // 重試按鈕
                const retryBtn = document.createElement('button');
                retryBtn.className = 'ytdl-task-action-btn retry';
                retryBtn.textContent = '重試';
                retryBtn.onclick = (e) => {
                    e.stopPropagation();
                    retryTask(taskId, task);
                };
                actions.appendChild(retryBtn);

                // 關閉按鈕
                const dismissBtn = document.createElement('button');
                dismissBtn.className = 'ytdl-task-action-btn dismiss';
                dismissBtn.textContent = '關閉';
                dismissBtn.onclick = (e) => {
                    e.stopPropagation();
                    tasks.delete(taskId);
                    updatePanel();
                    updateButtonBadge(getActiveTaskCount());
                };
                actions.appendChild(dismissBtn);

                el.appendChild(actions);
            }

            body.appendChild(el);
        });
    }

    // 重試任務
    function retryTask(oldTaskId, oldTask) {
        // 移除舊任務
        tasks.delete(oldTaskId);
        updatePanel();

        // 用原本的 URL 重新下載
        const url = oldTask.url || location.href;
        const fmt = {
            format: oldTask.formatCode || 'best',
            label: (oldTask.format || '最佳畫質').replace(/ ✂ .*$/, ''),
            audioOnly: oldTask.audio_only || false
        };

        downloadViaYtify(fmt, url, oldTask.clip || null);
    }

    // 計算進行中的任務數
    function getActiveTaskCount() {
        let count = 0;
        tasks.forEach(task => {
            if (!['completed', 'failed'].includes(task.status)) {
                count++;
            }
        });
        return count;
    }

    function updateButtonBadge(count) {
        const badge = document.querySelector('.ytdl-btn .badge');
        if (badge) {
            badge.textContent = count;
            badge.style.display = count > 0 ? 'inline' : 'none';
        }
    }

    // ===== 下載邏輯 =====
    function triggerBrowserDownload(url, filename) {
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        link.style.display = 'none';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }

    function pollTaskStatus(taskId) {
        const startTime = Date.now();
        let fakeProgress = 0;

        const poll = async () => {
            const task = tasks.get(taskId);
            if (!task) return;

            if (Date.now() - startTime > CONFIG.POLL_TIMEOUT) {
                task.status = 'failed';
                task.error = '下載超時';
                updatePanel();
                return;
            }

            try {
                const status = await ytifyRequest('GET', `/api/status/${taskId}`);

                task.status = status.status;
                task.title = status.title || task.title;
                task.speed = status.speed || '';
                task.error = status.error;

                if (status.status === 'downloading' || status.status === 'processing') {
                    if (status.progress && status.progress > 0) {
                        task.progress = status.progress;
                    } else {
                        fakeProgress += fakeProgress < 30 ? 8 : (fakeProgress < 90 ? 2 : 0.5);
                        fakeProgress = Math.min(fakeProgress, 95);
                        task.progress = fakeProgress;
                    }
                } else if (status.status === 'completed') {
                    task.progress = 100;
                    task.filename = status.filename;
                    if (status.filename) {
                        const downloadUrl = `${CONFIG.YTIFY_API}/api/download-file/${encodeURIComponent(status.filename)}`;
                        triggerBrowserDownload(downloadUrl, status.filename);
                    }
                    // 下載完成後自動從面板移除
                    setTimeout(() => {
                        tasks.delete(taskId);
                        updatePanel();
                        updateButtonBadge(getActiveTaskCount());
                    }, 1500);
                } else if (status.status === 'failed') {
                    task.progress = 0;
                    // 不再自動刪除，讓用戶可以點「重試」按鈕
                }

                updatePanel();

                if (!['completed', 'failed'].includes(status.status)) {
                    setTimeout(poll, CONFIG.POLL_INTERVAL);
                }
            } catch {
                setTimeout(poll, CONFIG.POLL_INTERVAL * 2);
            }
        };

        poll();
    }

    async function downloadViaYtify(fmt, customUrl = null, clip = null) {
        if (!ytifyOnline) {
            alert('ytify 服務未連線');
            return;
        }

        const url = customUrl || location.href;
        const title = getTitle();
        const tempId = 'temp-' + Date.now();
        const clipLabel = clip ? ` ✂ ${secToClock(clip.start)}–${secToClock(clip.end)}` : '';

        tasks.set(tempId, {
            title: title,
            format: fmt.label + clipLabel,
            status: 'queued',
            progress: 0,
            url: url,
            formatCode: fmt.format,
            audio_only: fmt.audioOnly,
            clip: clip,
        });
        showPanel();
        updatePanel();

        try {
            // 直接提交下載，不再等待 /api/info（避免阻塞後續任務）
            // 標題會在 polling 時從伺服器取得
            const body = {
                url: url,
                format: fmt.format,
                audio_only: fmt.audioOnly
            };
            if (clip) {
                body.clip_start = clip.start;
                body.clip_end = clip.end;
            }
            const result = await ytifyRequest('POST', '/api/download', body, 60000);

            if (!result.task_id) throw new Error('無法建立下載任務');

            const taskData = tasks.get(tempId);
            tasks.delete(tempId);
            tasks.set(result.task_id, taskData);

            pollTaskStatus(result.task_id);

        } catch (e) {
            const task = tasks.get(tempId);
            if (task) {
                task.status = 'failed';
                task.error = e.message;
                updatePanel();
                // 不要自動刪除，讓用戶可以重試
            }
        }
    }

    // ===== Info Popup =====
    function createInfoPopup() {
        if (infoPopup) return { popup: infoPopup, overlay: infoOverlay };

        // Overlay
        infoOverlay = document.createElement('div');
        infoOverlay.className = 'ytdl-info-overlay';
        infoOverlay.onclick = () => hideInfoPopup();

        // Popup
        infoPopup = document.createElement('div');
        infoPopup.className = 'ytdl-info-popup';

        // Title
        const title = document.createElement('div');
        title.className = 'ytdl-info-popup-title';
        title.textContent = 'Ytify v10.8';
        infoPopup.appendChild(title);

        // Divider 1
        const divider1 = document.createElement('div');
        divider1.className = 'ytdl-info-popup-divider';
        infoPopup.appendChild(divider1);

        // Links
        const links = [
            { icon: '🌐', text: '官方網站', url: 'https://jeffrey0117.github.io/Ytify/' },
            { icon: '📖', text: '快速開始', url: 'https://jeffrey0117.github.io/Ytify/#quickstart' },
            { icon: '💻', text: 'GitHub', url: 'https://github.com/Jeffrey0117/Ytify' },
            { icon: '🐛', text: '回報問題', url: 'https://github.com/Jeffrey0117/Ytify/issues' },
        ];

        links.forEach(link => {
            const linkEl = document.createElement('a');
            linkEl.className = 'ytdl-info-popup-link';
            linkEl.href = link.url;
            linkEl.target = '_blank';
            linkEl.rel = 'noopener noreferrer';

            const iconSpan = document.createElement('span');
            iconSpan.className = 'ytdl-info-popup-link-icon';
            iconSpan.textContent = link.icon;

            const textSpan = document.createElement('span');
            textSpan.className = 'ytdl-info-popup-link-text';
            textSpan.textContent = link.text;

            linkEl.append(iconSpan, textSpan);
            infoPopup.appendChild(linkEl);
        });

        // Divider 2
        const divider2 = document.createElement('div');
        divider2.className = 'ytdl-info-popup-divider';
        infoPopup.appendChild(divider2);

        // Server info
        const serverBox = document.createElement('div');
        serverBox.className = 'ytdl-info-popup-server';

        const serverLabel = document.createElement('div');
        serverLabel.className = 'ytdl-info-popup-server-label';
        serverLabel.textContent = '目前伺服器';

        const serverRow = document.createElement('div');
        serverRow.className = 'ytdl-info-popup-server-row';

        const serverValue = document.createElement('div');
        serverValue.className = 'ytdl-info-popup-server-value';
        serverValue.id = 'ytdl-info-server-value';
        serverValue.textContent = CONFIG.YTIFY_API;

        const editBtn = document.createElement('button');
        editBtn.className = 'ytdl-info-popup-edit-btn';
        editBtn.textContent = '修改';
        editBtn.onclick = (e) => {
            e.stopPropagation();
            hideInfoPopup();
            showOfflinePopup();
        };

        serverRow.append(serverValue, editBtn);
        serverBox.append(serverLabel, serverRow);
        infoPopup.appendChild(serverBox);

        // Hint
        const hint = document.createElement('div');
        hint.className = 'ytdl-info-popup-hint';
        hint.textContent = '作者 Jeffrey0117';
        infoPopup.appendChild(hint);

        document.body.append(infoOverlay, infoPopup);
        return { popup: infoPopup, overlay: infoOverlay };
    }

    function showInfoPopup() {
        const { popup, overlay } = createInfoPopup();
        // Update server value dynamically
        const serverValueEl = document.getElementById('ytdl-info-server-value');
        if (serverValueEl) {
            serverValueEl.textContent = CONFIG.YTIFY_API;
        }
        overlay.classList.add('show');
        popup.classList.add('show');
    }

    function hideInfoPopup() {
        if (infoPopup) infoPopup.classList.remove('show');
        if (infoOverlay) infoOverlay.classList.remove('show');
    }

    // ===== Offline Popup =====
    function createOfflinePopup() {
        if (offlinePopup) return offlinePopup;

        offlinePopup = document.createElement('div');
        offlinePopup.className = 'ytdl-offline-popup';
        offlinePopup.style.display = 'none';

        const content = document.createElement('div');
        content.className = 'ytdl-offline-popup-content';

        // Header
        const header = document.createElement('div');
        header.className = 'ytdl-offline-popup-header';
        header.textContent = '⚠️ 無法連線到 Ytify 伺服器';
        content.appendChild(header);

        // URL label
        const urlLabel = document.createElement('div');
        urlLabel.className = 'ytdl-offline-popup-url-label';
        urlLabel.textContent = '伺服器網址（可直接修改）:';
        content.appendChild(urlLabel);

        // URL input
        const urlInput = document.createElement('input');
        urlInput.type = 'text';
        urlInput.className = 'ytdl-offline-popup-input';
        urlInput.value = CONFIG.YTIFY_API;
        urlInput.placeholder = 'http://localhost:8765';
        content.appendChild(urlInput);

        // Reasons
        const reasons = document.createElement('div');
        reasons.className = 'ytdl-offline-popup-reasons';

        const reasonsTitle = document.createElement('div');
        reasonsTitle.className = 'ytdl-offline-popup-reasons-title';
        reasonsTitle.textContent = '可能原因：';
        reasons.appendChild(reasonsTitle);

        const reasonsList = document.createElement('ul');
        const reasonItems = [
            { text: '伺服器未啟動 → 執行 ', code: 'run.bat' },
            { text: '網址設定錯誤 → 編輯腳本第 ', code: '38', suffix: ' 行' },
            { text: '防火牆阻擋 → 檢查網路設定', code: null }
        ];
        reasonItems.forEach(item => {
            const li = document.createElement('li');
            li.appendChild(document.createTextNode(item.text));
            if (item.code) {
                const code = document.createElement('code');
                code.textContent = item.code;
                li.appendChild(code);
            }
            if (item.suffix) {
                li.appendChild(document.createTextNode(item.suffix));
            }
            reasonsList.appendChild(li);
        });
        reasons.appendChild(reasonsList);
        content.appendChild(reasons);

        // Actions
        const actions = document.createElement('div');
        actions.className = 'ytdl-offline-popup-actions';

        const helpBtn = document.createElement('button');
        helpBtn.className = 'ytdl-offline-popup-btn secondary';
        helpBtn.textContent = '📖 查看教學';
        helpBtn.onclick = () => {
            window.open('https://jeffrey0117.github.io/Ytify/#quickstart', '_blank');
        };

        // Saved indicator
        const savedIndicator = document.createElement('span');
        savedIndicator.className = 'ytdl-offline-popup-saved';
        savedIndicator.textContent = '✓ 已儲存';

        const retryBtn = document.createElement('button');
        retryBtn.className = 'ytdl-offline-popup-btn primary';
        retryBtn.textContent = '🔄 重新連線';
        retryBtn.onclick = async () => {
            // Save new URL if changed
            const newUrl = urlInput.value.trim().replace(/\/+$/, ''); // Remove trailing slashes
            if (newUrl && newUrl !== CONFIG.YTIFY_API) {
                localStorage.setItem('ytify_api_url', newUrl);
                CONFIG.YTIFY_API = newUrl;
                // Show saved indicator
                savedIndicator.classList.add('show');
                setTimeout(() => savedIndicator.classList.remove('show'), 2000);
            }

            retryBtn.classList.add('reconnecting');
            retryBtn.textContent = '連線中...';
            await checkYtifyStatus();
            retryBtn.classList.remove('reconnecting');
            retryBtn.textContent = '🔄 重新連線';
            if (ytifyOnline) {
                hideOfflinePopup();
            }
        };

        actions.append(helpBtn, retryBtn, savedIndicator);
        content.appendChild(actions);

        offlinePopup.appendChild(content);

        // Close on background click
        offlinePopup.onclick = (e) => {
            if (e.target === offlinePopup) {
                hideOfflinePopup();
            }
        };

        document.body.appendChild(offlinePopup);
        return offlinePopup;
    }

    // ===== 剪片段 Popup =====
    function createClipPopup() {
        if (clipPopup) return clipPopup;

        clipPopup = document.createElement('div');
        clipPopup.className = 'ytdl-offline-popup';
        clipPopup.style.display = 'none';

        const content = document.createElement('div');
        content.className = 'ytdl-offline-popup-content';

        const header = document.createElement('div');
        header.className = 'ytdl-offline-popup-header';
        header.textContent = '✂️ 剪片段下載';
        content.appendChild(header);

        const hint = document.createElement('div');
        hint.className = 'ytdl-offline-popup-url-label';
        hint.textContent = '格式：秒數或 分:秒（如 83 或 1:23），最長 30 分鐘';
        content.appendChild(hint);

        // 起點 / 終點輸入列（各附「抓當前時間」按鈕）
        const makeTimeRow = (labelText, inputId) => {
            const row = document.createElement('div');
            row.className = 'ytdl-clip-row';

            const label = document.createElement('label');
            label.textContent = labelText;

            const input = document.createElement('input');
            input.type = 'text';
            input.className = 'ytdl-offline-popup-input';
            input.dataset.clipInput = inputId;
            input.placeholder = '0:00';

            const nowBtn = document.createElement('button');
            nowBtn.className = 'ytdl-clip-now-btn';
            nowBtn.textContent = '⏱ 目前時間';
            nowBtn.onclick = () => {
                const video = document.querySelector('video');
                if (video) input.value = secToClock(video.currentTime);
            };

            row.append(label, input, nowBtn);
            return row;
        };

        content.appendChild(makeTimeRow('起點', 'start'));
        content.appendChild(makeTimeRow('終點', 'end'));

        // 格式選擇
        const select = document.createElement('select');
        select.className = 'ytdl-clip-select';
        YTIFY_FORMATS.forEach((fmt, i) => {
            const opt = document.createElement('option');
            opt.value = String(i);
            opt.textContent = fmt.label;
            select.appendChild(opt);
        });
        content.appendChild(select);

        // 錯誤訊息
        const errorEl = document.createElement('div');
        errorEl.className = 'ytdl-clip-error';
        content.appendChild(errorEl);

        // 按鈕列
        const actions = document.createElement('div');
        actions.className = 'ytdl-offline-popup-actions';

        const cancelBtn = document.createElement('button');
        cancelBtn.className = 'ytdl-offline-popup-btn secondary';
        cancelBtn.textContent = '取消';
        cancelBtn.onclick = () => hideClipPopup();

        const submitBtn = document.createElement('button');
        submitBtn.className = 'ytdl-offline-popup-btn primary';
        submitBtn.textContent = '✂️ 下載片段';
        submitBtn.onclick = () => {
            const startInput = content.querySelector('[data-clip-input="start"]');
            const endInput = content.querySelector('[data-clip-input="end"]');
            const start = parseClipTime(startInput.value);
            const end = parseClipTime(endInput.value);

            if (isNaN(start) || isNaN(end)) {
                errorEl.textContent = '時間格式無效，請用秒數或 分:秒';
                return;
            }
            if (end <= start) {
                errorEl.textContent = '終點必須大於起點';
                return;
            }
            if (end - start > 1800) {
                errorEl.textContent = '片段最長 30 分鐘';
                return;
            }

            errorEl.textContent = '';
            hideClipPopup();
            const fmt = YTIFY_FORMATS[parseInt(select.value, 10)] || YTIFY_FORMATS[0];
            downloadViaYtify(fmt, null, { start, end });
        };

        actions.append(cancelBtn, submitBtn);
        content.appendChild(actions);

        clipPopup.appendChild(content);
        clipPopup.onclick = (e) => {
            if (e.target === clipPopup) hideClipPopup();
        };

        document.body.appendChild(clipPopup);
        return clipPopup;
    }

    function showClipPopup() {
        const popup = createClipPopup();
        // 打開時起點預填播放器當前時間
        const video = document.querySelector('video');
        const startInput = popup.querySelector('[data-clip-input="start"]');
        if (video && startInput && !startInput.value) {
            startInput.value = secToClock(video.currentTime);
        }
        popup.style.display = 'flex';
    }

    function hideClipPopup() {
        if (clipPopup) {
            clipPopup.style.display = 'none';
        }
    }

    function showOfflinePopup() {
        const popup = createOfflinePopup();
        // Update input value to current URL
        const urlInput = popup.querySelector('.ytdl-offline-popup-input');
        if (urlInput) {
            urlInput.value = CONFIG.YTIFY_API;
        }
        popup.style.display = 'flex';
    }

    function hideOfflinePopup() {
        if (offlinePopup) {
            offlinePopup.style.display = 'none';
        }
    }

    // ===== UI 建立（不使用 innerHTML）=====
    function createUI() {
        const wrap = document.createElement('div');
        wrap.className = 'ytdl-wrapper';

        // 主按鈕
        const btn = document.createElement('button');
        btn.className = 'ytdl-btn';
        btn.appendChild(createSvg(SVG_PATHS.download));
        const btnText = document.createTextNode(' 下載 ');
        btn.appendChild(btnText);
        const btnBadge = document.createElement('span');
        btnBadge.className = 'badge';
        btnBadge.style.display = 'none';
        btnBadge.textContent = '0';
        btn.appendChild(btnBadge);

        // 選單
        const menu = document.createElement('div');
        menu.className = 'ytdl-menu';

        // ytify header
        const ytifyHeader = document.createElement('div');
        ytifyHeader.className = 'ytdl-menu-header';

        const labelSpan = document.createElement('span');
        labelSpan.style.cssText = 'display:flex;align-items:center;gap:4px';
        labelSpan.appendChild(createSvg(SVG_PATHS.local));
        labelSpan.appendChild(document.createTextNode(' YTIFY'));

        const statusIndicator = document.createElement('span');
        statusIndicator.className = 'ytdl-ytify-status ytdl-ytify-indicator offline';
        statusIndicator.textContent = '檢查中';

        ytifyHeader.append(labelSpan, statusIndicator);
        menu.appendChild(ytifyHeader);

        // 格式選項
        YTIFY_FORMATS.forEach(fmt => {
            const item = document.createElement('div');
            item.className = 'ytdl-menu-item disabled';
            item.dataset.ytify = 'true';
            item.appendChild(createSvg(fmt.audioOnly ? SVG_PATHS.audio : SVG_PATHS.video));
            item.appendChild(document.createTextNode(' ' + fmt.label));
            item.onclick = (e) => {
                e.stopPropagation();
                if (!item.classList.contains('disabled')) {
                    menu.classList.remove('show');
                    downloadViaYtify(fmt);
                }
            };
            menu.appendChild(item);
        });

        // 剪片段（只下載某一段）
        const clipItem = document.createElement('div');
        clipItem.className = 'ytdl-menu-item disabled';
        clipItem.dataset.ytify = 'true';
        clipItem.appendChild(document.createTextNode('✂️ 剪片段'));
        clipItem.onclick = (e) => {
            e.stopPropagation();
            if (!clipItem.classList.contains('disabled')) {
                menu.classList.remove('show');
                showClipPopup();
            }
        };
        menu.appendChild(clipItem);

        // 分隔線
        const divider = document.createElement('div');
        divider.style.cssText = 'height:1px;background:#3a3a3a;margin:6px 0';
        menu.appendChild(divider);

        // 查看下載面板
        const panelItem = document.createElement('div');
        panelItem.className = 'ytdl-menu-item';
        panelItem.appendChild(createSvg(SVG_PATHS.download));
        panelItem.appendChild(document.createTextNode(' 查看下載面板'));
        panelItem.onclick = (e) => {
            e.stopPropagation();
            menu.classList.remove('show');
            showPanel();
        };
        menu.appendChild(panelItem);

        // 分隔線 - 官網連結區塊
        const linksDivider = document.createElement('div');
        linksDivider.style.cssText = 'height:1px;background:#3a3a3a;margin:6px 0';
        menu.appendChild(linksDivider);

        // 官方網站連結
        const websiteItem = document.createElement('div');
        websiteItem.className = 'ytdl-menu-item';
        websiteItem.appendChild(document.createTextNode('🌐 官方網站'));
        websiteItem.onclick = (e) => {
            e.stopPropagation();
            menu.classList.remove('show');
            window.open('https://jeffrey0117.github.io/Ytify/', '_blank');
        };
        menu.appendChild(websiteItem);

        // 使用說明連結
        const helpItem = document.createElement('div');
        helpItem.className = 'ytdl-menu-item';
        helpItem.appendChild(document.createTextNode('❓ 使用說明'));
        helpItem.onclick = (e) => {
            e.stopPropagation();
            menu.classList.remove('show');
            window.open('https://jeffrey0117.github.io/Ytify/#quickstart', '_blank');
        };
        menu.appendChild(helpItem);

        // Info 按鈕 (Powered by Ytify)
        const infoBtn = document.createElement('button');
        infoBtn.className = 'ytdl-info-btn';
        infoBtn.title = '關於 Ytify';
        infoBtn.textContent = 'Powered by Ytify';
        infoBtn.onclick = (e) => {
            e.stopPropagation();
            showInfoPopup();
        };

        wrap.append(btn, menu, infoBtn);

        btn.onclick = (e) => {
            e.stopPropagation();
            // If offline, show offline popup instead of menu
            if (!ytifyOnline && btn.classList.contains('offline')) {
                showOfflinePopup();
                return;
            }
            menu.classList.toggle('show');
            if (menu.classList.contains('show')) {
                checkYtifyStatus();
            }
        };

        document.addEventListener('click', () => menu.classList.remove('show'));

        return wrap;
    }

    function inject() {
        const vid = getVideoId();
        if (!vid) return;
        if (vid === videoId && container && document.contains(container)) return;

        container?.remove();

        const target = document.querySelector('#top-level-buttons-computed, #subscribe-button');
        if (target) {
            videoId = vid;
            container = createUI();
            target.parentNode.insertBefore(container, target.nextSibling);
        }
    }

    async function tryInject() {
        const vid = getVideoId();
        if (!vid) return;

        const checkTarget = () => document.querySelector('#top-level-buttons-computed, #subscribe-button');
        let attempts = 0;
        while (!checkTarget() && attempts < 20) {
            await new Promise(r => setTimeout(r, 400));
            attempts++;
        }
        if (checkTarget()) inject();
    }

    function init() {
        tryInject();

        let lastUrl = location.href;
        new MutationObserver(() => {
            if (location.href !== lastUrl) {
                lastUrl = location.href;
                videoId = null;
                container?.remove();
                container = null;
                setTimeout(tryInject, 500);
            }
        }).observe(document.body, { subtree: true, childList: true });

        document.addEventListener('yt-navigate-finish', () => {
            videoId = null;
            container?.remove();
            container = null;
            setTimeout(tryInject, 300);
        });

        setInterval(() => {
            const vid = getVideoId();
            if (vid && (!container || !document.contains(container))) {
                inject();
            }
        }, 1500);

        // Initial status check
        checkYtifyStatus();

        // Periodic health check every 30 seconds
        setInterval(checkYtifyStatus, 30000);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        setTimeout(init, 500);
    }
})();
