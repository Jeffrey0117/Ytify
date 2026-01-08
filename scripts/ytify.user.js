// ==UserScript==
// @name         ytify Downloader
// @namespace    http://tampermonkey.net/
// @version      9.0
// @description  在 YouTube 影片頁面添加下載按鈕，透過 ytify API 下載影片
// @author       Jeffrey
// @match        https://www.youtube.com/*
// @match        https://youtube.com/*
// @grant        GM_xmlhttpRequest
// @grant        GM_addStyle
// @connect      localhost
// @connect      127.0.0.1
// @connect      *.trycloudflare.com
// @connect      ytify.isnowfriend.com
// @connect      isnowfriend.com
// @connect      *
// @run-at       document-idle
// ==/UserScript==

(function() {
    'use strict';

    // ╔════════════════════════════════════════════════════════════╗
    // ║                    🔧 使用者設定區                          ║
    // ║          修改下方網址為你的 ytify 服務位置                   ║
    // ╚════════════════════════════════════════════════════════════╝

    const YTIFY_API_URL = 'http://localhost:8765';
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

    // ytify 格式選項
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
        .ytdl-menu-divider {
            height: 1px;
            background: #3a3a3a;
            margin: 6px 0;
        }
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
        .ytdl-menu-item.disabled {
            color: #666;
            cursor: not-allowed;
        }
        .ytdl-menu-item.disabled:hover { background: transparent; }
        .ytdl-menu-item svg { width: 14px; height: 14px; opacity: 0.7; }
        .ytdl-wrapper { position: relative; display: inline-block; }

        .ytdl-toast {
            position: fixed;
            bottom: 24px;
            right: 24px;
            background: #282828;
            color: white;
            padding: 16px 20px;
            border-radius: 12px;
            font-size: 14px;
            z-index: 999999;
            box-shadow: 0 8px 32px rgba(0,0,0,0.5);
            min-width: 280px;
            transform: translateX(400px);
            transition: transform 0.3s ease;
        }
        .ytdl-toast.show { transform: translateX(0); }
        .ytdl-toast-title { font-weight: 600; margin-bottom: 6px; }
        .ytdl-toast-sub { color: #aaa; font-size: 13px; margin-bottom: 12px; }
        .ytdl-toast-bar-wrap { height: 4px; background: #444; border-radius: 2px; overflow: hidden; }
        .ytdl-toast-bar { height: 100%; width: 0%; background: #3ea6ff; transition: width 0.3s; }
        .ytdl-toast-bar.anim { animation: ytdl-pulse 1.5s ease-in-out infinite; }
        @keyframes ytdl-pulse {
            0%, 100% { width: 20%; margin-left: 0; }
            50% { width: 40%; margin-left: 60%; }
        }
        .ytdl-toast.done .ytdl-toast-bar { background: #4caf50; width: 100%; }
        .ytdl-toast.fail .ytdl-toast-bar { background: #f44336; width: 100%; }
        .ytdl-toast.warn .ytdl-toast-bar { background: #ff9800; }
        .ytdl-toast-actions {
            margin-top: 12px;
            display: flex;
            gap: 8px;
        }
        .ytdl-toast-btn {
            padding: 6px 14px;
            background: #444;
            border: none;
            border-radius: 6px;
            color: white;
            cursor: pointer;
            font-size: 13px;
        }
        .ytdl-toast-btn:hover { background: #555; }
        .ytdl-toast-btn.primary { background: #065fd4; }
        .ytdl-toast-btn.primary:hover { background: #0056b8; }

        /* ytify 專用狀態指示 */
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
    `);

    let videoId = null;
    let container = null;
    let toast = null;
    let pollTimer = null;
    let autoHideTimer = null;
    let ytifyOnline = false;

    const getVideoId = () => new URLSearchParams(location.search).get('v');

    const getTitle = () => {
        const el = document.querySelector('h1 yt-formatted-string');
        return (el?.textContent?.trim() || 'video').replace(/[<>:"/\\|?*]/g, '');
    };

    // ===== Toast 系統 =====
    function getToast() {
        if (!toast) {
            toast = document.createElement('div');
            toast.className = 'ytdl-toast';

            const title = document.createElement('div');
            title.className = 'ytdl-toast-title';

            const sub = document.createElement('div');
            sub.className = 'ytdl-toast-sub';

            const barWrap = document.createElement('div');
            barWrap.className = 'ytdl-toast-bar-wrap';

            const bar = document.createElement('div');
            bar.className = 'ytdl-toast-bar';
            barWrap.appendChild(bar);

            const actions = document.createElement('div');
            actions.className = 'ytdl-toast-actions';

            toast.append(title, sub, barWrap, actions);
            document.body.appendChild(toast);
        }
        return toast;
    }

    function showToast(opts) {
        const t = getToast();
        t.querySelector('.ytdl-toast-title').textContent = opts.title || '';
        t.querySelector('.ytdl-toast-sub').textContent = opts.sub || '';

        const bar = t.querySelector('.ytdl-toast-bar');
        const actions = t.querySelector('.ytdl-toast-actions');

        t.classList.remove('done', 'fail', 'warn');
        bar.classList.remove('anim');

        if (opts.progress === 'loading') {
            bar.classList.add('anim');
        } else if (typeof opts.progress === 'number') {
            bar.style.width = opts.progress + '%';
        }

        if (opts.state === 'done') t.classList.add('done');
        if (opts.state === 'fail') t.classList.add('fail');
        if (opts.state === 'warn') t.classList.add('warn');

        actions.textContent = '';
        if (opts.buttons) {
            opts.buttons.forEach(btn => {
                const el = document.createElement('button');
                el.className = 'ytdl-toast-btn' + (btn.primary ? ' primary' : '');
                el.textContent = btn.text;
                el.onclick = btn.onClick;
                actions.appendChild(el);
            });
        }

        t.classList.add('show');

        // 清除舊的 autoHide timer
        if (autoHideTimer) {
            clearTimeout(autoHideTimer);
            autoHideTimer = null;
        }

        if (opts.autoHide) {
            autoHideTimer = setTimeout(hideToast, opts.autoHide);
        }
    }

    function hideToast() {
        if (autoHideTimer) {
            clearTimeout(autoHideTimer);
            autoHideTimer = null;
        }
        toast?.classList.remove('show');
    }

    function clearTimers() {
        clearTimeout(pollTimer);
        pollTimer = null;
        if (autoHideTimer) {
            clearTimeout(autoHideTimer);
            autoHideTimer = null;
        }
    }

    function cancelDownload() {
        clearTimers();
        hideToast();
    }

    // ===== 觸發瀏覽器下載 =====
    function triggerBrowserDownload(url, filename) {
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        link.style.display = 'none';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }

    // ===== ytify API 請求 =====
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

    // 檢查 ytify 服務狀態
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
            indicator.className = 'ytdl-ytify-status ' + (ytifyOnline ? 'online' : 'offline');
            indicator.textContent = ytifyOnline ? '已連線' : '離線';
        }

        document.querySelectorAll('.ytdl-menu-item[data-ytify]').forEach(item => {
            if (ytifyOnline) {
                item.classList.remove('disabled');
            } else {
                item.classList.add('disabled');
            }
        });
    }

    // ===== ytify 狀態輪詢 =====
    function pollYtifyStatus(taskId, onProgress, onComplete, onError) {
        const startTime = Date.now();
        let fakeProgress = 0;

        const poll = async () => {
            if (Date.now() - startTime > CONFIG.POLL_TIMEOUT) {
                onError(new Error('下載超時'));
                return;
            }

            try {
                const status = await ytifyRequest('GET', `/api/status/${taskId}`);

                // 排隊中
                if (status.status === 'queued') {
                    onProgress(0, null, 'queued', status.message || `排隊中（第 ${status.queue_position || '?'} 位）`);
                    pollTimer = setTimeout(poll, CONFIG.POLL_INTERVAL);
                    return;
                }

                // 重試中
                if (status.status === 'retrying') {
                    onProgress(0, null, 'retrying', status.message || `重試中 (${status.retry_count || 1}/3)`);
                    pollTimer = setTimeout(poll, CONFIG.POLL_INTERVAL);
                    return;
                }

                if (status.status === 'downloading' || status.status === 'processing') {
                    // 如果 API 有回傳真實進度就用，沒有就用假進度
                    let progress = status.progress;
                    if (!progress || progress === 0) {
                        // 假進度：快速增到 30%，然後慢慢爬到 90%
                        fakeProgress += fakeProgress < 30 ? 8 : (fakeProgress < 90 ? 2 : 0.5);
                        fakeProgress = Math.min(fakeProgress, 95);
                        progress = fakeProgress;
                    }
                    // 傳遞完整狀態資訊
                    onProgress(progress, status.speed, status.status, status.message);
                    pollTimer = setTimeout(poll, CONFIG.POLL_INTERVAL);
                } else if (status.status === 'completed') {
                    onComplete(status);
                } else if (status.status === 'failed') {
                    onError(new Error(status.error || '下載失敗'));
                } else {
                    // 其他狀態（如 pending）也跑假進度
                    fakeProgress += 3;
                    fakeProgress = Math.min(fakeProgress, 20);
                    onProgress(fakeProgress, null, status.status, status.message);
                    pollTimer = setTimeout(poll, CONFIG.POLL_INTERVAL);
                }
            } catch {
                pollTimer = setTimeout(poll, CONFIG.POLL_INTERVAL * 2);
            }
        };

        poll();
    }

    // ===== ytify 下載 =====
    async function downloadViaYtify(fmt) {
        cancelDownload();

        const title = getTitle();

        showToast({
            title: `⚡ ytify ${fmt.label}`,
            sub: '連接服務中...',
            progress: 'loading',
            buttons: [{ text: '取消', onClick: cancelDownload }]
        });

        try {
            await ytifyRequest('GET', '/health');

            showToast({
                title: `⚡ ytify ${fmt.label}`,
                sub: '解析影片資訊...',
                progress: 'loading',
                buttons: [{ text: '取消', onClick: cancelDownload }]
            });

            // /api/info 可能需要較長時間，給 60 秒
            const info = await ytifyRequest('POST', '/api/info', { url: location.href }, 60000);

            showToast({
                title: info.title || title,
                sub: '開始下載...',
                progress: 0,
                buttons: [{ text: '取消', onClick: cancelDownload }]
            });

            // /api/download 開始下載任務，給 60 秒
            const result = await ytifyRequest('POST', '/api/download', {
                url: location.href,
                format: fmt.format,
                audio_only: fmt.audioOnly
            }, 60000);

            if (!result.task_id) throw new Error('無法建立下載任務');

            pollYtifyStatus(
                result.task_id,
                (progress, speed, status, message) => {
                    // 根據狀態顯示不同訊息
                    let toastConfig = {
                        buttons: [{ text: '取消', onClick: cancelDownload }]
                    };

                    switch (status) {
                        case 'queued':
                            toastConfig.title = '⏳ 排隊中';
                            toastConfig.sub = message || '等待處理...';
                            toastConfig.progress = 'loading';
                            break;

                        case 'retrying':
                            toastConfig.title = '🔄 重試中';
                            toastConfig.sub = message || '正在重新嘗試...';
                            toastConfig.progress = 'loading';
                            toastConfig.state = 'warn';
                            break;

                        case 'processing':
                            toastConfig.title = '🔄 處理中...';
                            toastConfig.sub = message || '正在轉換格式...';
                            toastConfig.progress = 'loading';
                            break;

                        case 'downloading':
                            toastConfig.title = `下載中 ${Math.round(progress)}%`;
                            toastConfig.sub = `${info.title || title}${speed ? '　' + speed : ''}`;
                            toastConfig.progress = progress;
                            break;

                        default:
                            toastConfig.title = '處理中...';
                            toastConfig.sub = message || info.title || title;
                            toastConfig.progress = 'loading';
                    }

                    showToast(toastConfig);
                },
                (status) => {
                    clearTimers();

                    // 自動觸發檔案下載到使用者電腦
                    if (status.filename) {
                        const downloadUrl = `${CONFIG.YTIFY_API}/api/download-file/${encodeURIComponent(status.filename)}`;
                        triggerBrowserDownload(downloadUrl, status.filename);
                    }

                    showToast({
                        title: '✓ 下載完成',
                        sub: status.filename || info.title || title,
                        progress: 100,
                        state: 'done',
                        autoHide: 4000
                    });
                },
                (error) => {
                    clearTimers();
                    showToast({
                        title: '❌ 下載失敗',
                        sub: error.message,
                        progress: 100,
                        state: 'fail',
                        autoHide: 4000
                    });
                }
            );

        } catch (e) {
            clearTimers();
            const isConnectionError = e.message.includes('無法連接');
            showToast({
                title: '❌ ' + (isConnectionError ? '無法連接 ytify' : '下載失敗'),
                sub: isConnectionError ? '請確認服務已啟動：' + CONFIG.YTIFY_API : e.message,
                progress: 100,
                state: 'fail',
                autoHide: 5000
            });
        }
    }

    // ===== UI 建立 =====
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
    };

    function createMenuItem(iconPath, label) {
        const item = document.createElement('div');
        item.className = 'ytdl-menu-item';
        item.appendChild(createSvg(iconPath));
        item.appendChild(document.createTextNode(' ' + label));
        return item;
    }

    function createUI() {
        const wrap = document.createElement('div');
        wrap.className = 'ytdl-wrapper';

        // 主按鈕
        const btn = document.createElement('button');
        btn.className = 'ytdl-btn';
        btn.appendChild(createSvg(SVG_PATHS.download));
        btn.appendChild(document.createTextNode(' 下載'));

        // 選單
        const menu = document.createElement('div');
        menu.className = 'ytdl-menu';

        // ytify 區塊
        const ytifyHeader = document.createElement('div');
        ytifyHeader.className = 'ytdl-menu-header';
        ytifyHeader.style.justifyContent = 'space-between';

        const ytifyLabel = document.createElement('span');
        ytifyLabel.style.display = 'flex';
        ytifyLabel.style.alignItems = 'center';
        ytifyLabel.style.gap = '4px';
        ytifyLabel.appendChild(createSvg(SVG_PATHS.local));
        ytifyLabel.appendChild(document.createTextNode(' YTIFY'));
        ytifyHeader.appendChild(ytifyLabel);

        const statusIndicator = document.createElement('span');
        statusIndicator.className = 'ytdl-ytify-status ytdl-ytify-indicator offline';
        statusIndicator.textContent = '檢查中';
        ytifyHeader.appendChild(statusIndicator);
        menu.appendChild(ytifyHeader);

        YTIFY_FORMATS.forEach(fmt => {
            const iconPath = fmt.audioOnly ? SVG_PATHS.audio : SVG_PATHS.video;
            const item = createMenuItem(iconPath, fmt.label);
            item.classList.add('disabled');
            item.dataset.ytify = 'true';
            item.onclick = (e) => {
                e.stopPropagation();
                if (item.classList.contains('disabled')) {
                    showToast({
                        title: '⚠️ ytify 服務未連線',
                        sub: '請確認服務已啟動且網址設定正確',
                        progress: 0,
                        state: 'warn',
                        autoHide: 4000
                    });
                    return;
                }
                menu.classList.remove('show');
                downloadViaYtify(fmt);
            };
            menu.appendChild(item);
        });

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

        // 如果已經注入過這個影片，檢查按鈕是否還在
        if (vid === videoId && container && document.contains(container)) return;

        container?.remove();

        const target = document.querySelector('#top-level-buttons-computed, #subscribe-button');
        if (target) {
            videoId = vid;
            container = createUI();
            target.parentNode.insertBefore(container, target.nextSibling);
        }
    }

    // 等待元素出現
    function waitForElement(selector, timeout = 10000) {
        return new Promise((resolve) => {
            const el = document.querySelector(selector);
            if (el) return resolve(el);

            const observer = new MutationObserver(() => {
                const el = document.querySelector(selector);
                if (el) {
                    observer.disconnect();
                    resolve(el);
                }
            });

            observer.observe(document.body, { subtree: true, childList: true });

            setTimeout(() => {
                observer.disconnect();
                resolve(null);
            }, timeout);
        });
    }

    async function tryInject() {
        const vid = getVideoId();
        if (!vid) return;

        // 等待按鈕區域出現
        const target = await waitForElement('#top-level-buttons-computed, #subscribe-button', 8000);
        if (target) {
            inject();
        }
    }

    function init() {
        // 初始嘗試注入
        tryInject();

        // URL 變化監聽
        let lastUrl = location.href;
        new MutationObserver(() => {
            if (location.href !== lastUrl) {
                lastUrl = location.href;
                videoId = null;
                container?.remove();
                container = null;
                // 延遲後嘗試注入
                setTimeout(tryInject, 500);
            }
        }).observe(document.body, { subtree: true, childList: true });

        // 監聽 YouTube 的導航事件
        document.addEventListener('yt-navigate-finish', () => {
            videoId = null;
            container?.remove();
            container = null;
            setTimeout(tryInject, 300);
        });

        // 備用：定期檢查（確保按鈕存在）
        setInterval(() => {
            const vid = getVideoId();
            if (vid && (!container || !document.contains(container))) {
                inject();
            }
        }, 1500);

        // 初始檢查 ytify 狀態
        checkYtifyStatus();
    }

    // 頁面載入後啟動
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        setTimeout(init, 500);
    }
})();
