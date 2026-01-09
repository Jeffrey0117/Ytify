// ==UserScript==
// @name         ytify Downloader
// @namespace    http://tampermonkey.net/
// @license MIT
// @version      10.0
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
// @homepageURL  https://github.com/Jeffrey0117/Ytify
// @supportURL   https://github.com/Jeffrey0117/Ytify/issues
// ==/UserScript==

/**
 * ytify Downloader v10.0
 * - 新增下載面板，支援同時多個下載任務
 * - 可展開/收起面板查看所有進行中的下載
 */

(function() {
    'use strict';

    // ╔════════════════════════════════════════════════════════════╗
    // ║                    🔧 使用者設定區                          ║
    // ╚════════════════════════════════════════════════════════════╝

    const YTIFY_API_URL = 'http://localhost:8765';

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
        @keyframes ytdl-pulse {
            0%, 100% { margin-left: 0; }
            50% { margin-left: 70%; }
        }
        .ytdl-task-bar-fill.done { background: #4caf50; }
        .ytdl-task-bar-fill.fail { background: #f44336; }

        /* 滾動條 */
        .ytdl-panel-body::-webkit-scrollbar { width: 6px; }
        .ytdl-panel-body::-webkit-scrollbar-track { background: #1a1a1a; }
        .ytdl-panel-body::-webkit-scrollbar-thumb { background: #444; border-radius: 3px; }
        .ytdl-panel-body::-webkit-scrollbar-thumb:hover { background: #555; }
    `);

    // ===== 狀態管理 =====
    let videoId = null;
    let container = null;
    let panel = null;
    let ytifyOnline = false;
    const tasks = new Map(); // taskId -> task info

    const getVideoId = () => new URLSearchParams(location.search).get('v');
    const getTitle = () => {
        const el = document.querySelector('h1 yt-formatted-string');
        return (el?.textContent?.trim() || 'video').replace(/[<>:"/\\|?*]/g, '');
    };

    // ===== SVG Icons =====
    const SVG = {
        download: '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 16l-5-5h3V4h4v7h3l-5 5zm-7 2h14v2H5v-2z"/></svg>',
        local: '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M20 18c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2H4c-1.1 0-2 .9-2 2v10c0 1.1.9 2 2 2H0v2h24v-2h-4zM4 6h16v10H4V6z"/></svg>',
        video: '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M18 4l2 4h-3l-2-4h-2l2 4h-3l-2-4H8l2 4H7L5 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V4h-4z"/></svg>',
        audio: '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 3v10.55c-.59-.34-1.27-.55-2-.55-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4V7h4V3h-6z"/></svg>',
        minimize: '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M19 13H5v-2h14v2z"/></svg>',
        close: '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/></svg>',
        expand: '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 8l-6 6 1.41 1.41L12 10.83l4.59 4.58L18 14z"/></svg>',
    };

    function createSvg(pathD) {
        const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        svg.setAttribute('viewBox', '0 0 24 24');
        svg.setAttribute('fill', 'currentColor');
        const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        path.setAttribute('d', pathD);
        svg.appendChild(path);
        return svg;
    }

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
    }

    // ===== 下載面板 =====
    function getPanel() {
        if (!panel) {
            panel = document.createElement('div');
            panel.className = 'ytdl-panel';
            panel.innerHTML = `
                <div class="ytdl-panel-header">
                    <div class="ytdl-panel-title">
                        ${SVG.download}
                        <span>下載任務</span>
                        <span class="ytdl-panel-badge">0</span>
                    </div>
                    <div class="ytdl-panel-actions">
                        <button class="ytdl-panel-btn ytdl-panel-minimize" title="最小化">${SVG.minimize}</button>
                        <button class="ytdl-panel-btn ytdl-panel-close" title="關閉">${SVG.close}</button>
                    </div>
                </div>
                <div class="ytdl-panel-body">
                    <div class="ytdl-panel-empty">沒有進行中的下載</div>
                </div>
            `;

            panel.querySelector('.ytdl-panel-header').onclick = () => {
                panel.classList.toggle('minimized');
            };
            panel.querySelector('.ytdl-panel-minimize').onclick = (e) => {
                e.stopPropagation();
                panel.classList.add('minimized');
            };
            panel.querySelector('.ytdl-panel-close').onclick = (e) => {
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

        if (tasks.size === 0) {
            body.innerHTML = '<div class="ytdl-panel-empty">沒有進行中的下載</div>';
            return;
        }

        body.innerHTML = '';
        tasks.forEach((task, taskId) => {
            const el = document.createElement('div');
            el.className = 'ytdl-task';
            el.dataset.taskId = taskId;

            const statusClass = task.status || 'queued';
            const statusText = {
                queued: '排隊中',
                downloading: '下載中',
                processing: '處理中',
                completed: '完成',
                failed: '失敗',
                retrying: '重試中'
            }[statusClass] || statusClass;

            const progress = task.progress || 0;
            const isLoading = ['queued', 'processing', 'retrying'].includes(task.status);
            const isDone = task.status === 'completed';
            const isFail = task.status === 'failed';

            el.innerHTML = `
                <div class="ytdl-task-header">
                    <div class="ytdl-task-title" title="${task.title || ''}">${task.title || '載入中...'}</div>
                    <div class="ytdl-task-status ${statusClass}">${statusText}</div>
                </div>
                <div class="ytdl-task-info">
                    <div class="ytdl-task-sub">${task.format || ''} ${task.speed || ''}</div>
                    <div class="ytdl-task-progress">${isDone ? '100%' : isFail ? '' : Math.round(progress) + '%'}</div>
                </div>
                <div class="ytdl-task-bar">
                    <div class="ytdl-task-bar-fill ${isLoading ? 'anim' : ''} ${isDone ? 'done' : ''} ${isFail ? 'fail' : ''}"
                         style="width: ${isDone ? 100 : isFail ? 100 : progress}%"></div>
                </div>
            `;
            body.appendChild(el);
        });
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
                    // 5 秒後移除完成的任務
                    setTimeout(() => {
                        tasks.delete(taskId);
                        updatePanel();
                    }, 5000);
                } else if (status.status === 'failed') {
                    task.progress = 0;
                    // 10 秒後移除失敗的任務
                    setTimeout(() => {
                        tasks.delete(taskId);
                        updatePanel();
                    }, 10000);
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

    async function downloadViaYtify(fmt) {
        if (!ytifyOnline) {
            alert('ytify 服務未連線');
            return;
        }

        const title = getTitle();

        // 建立任務
        const tempId = 'temp-' + Date.now();
        tasks.set(tempId, {
            title: title,
            format: fmt.label,
            status: 'queued',
            progress: 0,
        });
        showPanel();
        updatePanel();

        try {
            // 取得影片資訊
            const info = await ytifyRequest('POST', '/api/info', { url: location.href }, 60000);
            tasks.get(tempId).title = info.title || title;
            updatePanel();

            // 開始下載
            const result = await ytifyRequest('POST', '/api/download', {
                url: location.href,
                format: fmt.format,
                audio_only: fmt.audioOnly
            }, 60000);

            if (!result.task_id) throw new Error('無法建立下載任務');

            // 更新任務 ID
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
                setTimeout(() => {
                    tasks.delete(tempId);
                    updatePanel();
                }, 5000);
            }
        }
    }

    // ===== UI 建立 =====
    function createUI() {
        const wrap = document.createElement('div');
        wrap.className = 'ytdl-wrapper';

        const btn = document.createElement('button');
        btn.className = 'ytdl-btn';
        btn.innerHTML = SVG.download + ' 下載 <span class="badge" style="display:none">0</span>';

        const menu = document.createElement('div');
        menu.className = 'ytdl-menu';

        // ytify header
        const ytifyHeader = document.createElement('div');
        ytifyHeader.className = 'ytdl-menu-header';
        ytifyHeader.style.justifyContent = 'space-between';
        ytifyHeader.innerHTML = `
            <span style="display:flex;align-items:center;gap:4px">
                ${SVG.local} YTIFY
            </span>
            <span class="ytdl-ytify-status ytdl-ytify-indicator offline">檢查中</span>
        `;
        menu.appendChild(ytifyHeader);

        // 格式選項
        YTIFY_FORMATS.forEach(fmt => {
            const item = document.createElement('div');
            item.className = 'ytdl-menu-item disabled';
            item.dataset.ytify = 'true';
            item.innerHTML = (fmt.audioOnly ? SVG.audio : SVG.video) + ' ' + fmt.label;
            item.onclick = (e) => {
                e.stopPropagation();
                if (!item.classList.contains('disabled')) {
                    menu.classList.remove('show');
                    downloadViaYtify(fmt);
                }
            };
            menu.appendChild(item);
        });

        // 查看下載面板
        const divider = document.createElement('div');
        divider.style.cssText = 'height:1px;background:#3a3a3a;margin:6px 0';
        menu.appendChild(divider);

        const panelItem = document.createElement('div');
        panelItem.className = 'ytdl-menu-item';
        panelItem.innerHTML = SVG.download + ' 查看下載面板';
        panelItem.onclick = (e) => {
            e.stopPropagation();
            menu.classList.remove('show');
            showPanel();
        };
        menu.appendChild(panelItem);

        wrap.append(btn, menu);

        btn.onclick = (e) => {
            e.stopPropagation();
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

        checkYtifyStatus();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        setTimeout(init, 500);
    }
})();
