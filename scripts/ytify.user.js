// ==UserScript==
// @name         ytify - YouTube 一鍵下載
// @namespace    https://github.com/Jeffrey0117/ytify
// @version      1.0.0
// @description  透過本地 ytify API 下載 YouTube 影片
// @author       Jeffrey
// @match        https://www.youtube.com/*
// @match        https://youtube.com/*
// @match        https://m.youtube.com/*
// @icon         https://www.youtube.com/favicon.ico
// @grant        GM_xmlhttpRequest
// @grant        GM_notification
// @grant        GM_addStyle
// @grant        GM_registerMenuCommand
// @connect      localhost
// @connect      127.0.0.1
// ==/UserScript==

(function() {
    'use strict';

    // ===== 設定 =====
    const CONFIG = {
        API_BASE: 'http://localhost:8765',
        DEFAULT_FORMAT: 'best',  // best | 1080p | 720p | 480p
        POLL_INTERVAL: 1500,     // 狀態輪詢間隔 (ms)
        POLL_TIMEOUT: 600000,    // 輪詢超時 (10分鐘)
    };

    // ===== 樣式 =====
    GM_addStyle(`
        #ytify-btn {
            position: fixed;
            bottom: 24px;
            right: 24px;
            z-index: 99999;
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 12px 20px;
            background: linear-gradient(135deg, #ff0000 0%, #cc0000 100%);
            color: white;
            border: none;
            border-radius: 50px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            box-shadow: 0 4px 15px rgba(255, 0, 0, 0.4);
            transition: all 0.3s ease;
            font-family: 'YouTube Sans', 'Roboto', sans-serif;
        }

        #ytify-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(255, 0, 0, 0.5);
        }

        #ytify-btn:active {
            transform: translateY(0);
        }

        #ytify-btn.loading {
            background: linear-gradient(135deg, #666 0%, #444 100%);
            cursor: wait;
        }

        #ytify-btn.success {
            background: linear-gradient(135deg, #00c853 0%, #009624 100%);
        }

        #ytify-btn.error {
            background: linear-gradient(135deg, #ff5252 0%, #d50000 100%);
        }

        #ytify-btn svg {
            width: 18px;
            height: 18px;
            fill: currentColor;
        }

        #ytify-btn.loading svg {
            animation: ytify-spin 1s linear infinite;
        }

        @keyframes ytify-spin {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
        }

        #ytify-toast {
            position: fixed;
            bottom: 90px;
            right: 24px;
            z-index: 99998;
            padding: 12px 20px;
            background: rgba(0, 0, 0, 0.9);
            color: white;
            border-radius: 8px;
            font-size: 13px;
            max-width: 300px;
            opacity: 0;
            transform: translateY(10px);
            transition: all 0.3s ease;
            pointer-events: none;
        }

        #ytify-toast.show {
            opacity: 1;
            transform: translateY(0);
        }

        #ytify-progress {
            position: fixed;
            bottom: 90px;
            right: 24px;
            z-index: 99998;
            padding: 16px 20px;
            background: rgba(0, 0, 0, 0.95);
            color: white;
            border-radius: 12px;
            font-size: 13px;
            min-width: 250px;
            display: none;
        }

        #ytify-progress.show {
            display: block;
        }

        #ytify-progress-title {
            font-weight: 600;
            margin-bottom: 8px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }

        #ytify-progress-bar-bg {
            height: 6px;
            background: rgba(255, 255, 255, 0.2);
            border-radius: 3px;
            overflow: hidden;
            margin-bottom: 8px;
        }

        #ytify-progress-bar {
            height: 100%;
            background: #ff0000;
            border-radius: 3px;
            transition: width 0.3s ease;
            width: 0%;
        }

        #ytify-progress-info {
            display: flex;
            justify-content: space-between;
            font-size: 11px;
            color: rgba(255, 255, 255, 0.7);
        }

        /* 選單 */
        #ytify-menu {
            position: fixed;
            bottom: 80px;
            right: 24px;
            z-index: 99997;
            background: white;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
            overflow: hidden;
            display: none;
            min-width: 180px;
        }

        #ytify-menu.show {
            display: block;
        }

        .ytify-menu-item {
            padding: 12px 16px;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 10px;
            transition: background 0.2s;
            color: #333;
            font-size: 14px;
        }

        .ytify-menu-item:hover {
            background: #f5f5f5;
        }

        .ytify-menu-item svg {
            width: 16px;
            height: 16px;
            opacity: 0.7;
        }
    `);

    // ===== SVG Icons =====
    const ICONS = {
        download: '<svg viewBox="0 0 24 24"><path d="M19 9h-4V3H9v6H5l7 7 7-7zM5 18v2h14v-2H5z"/></svg>',
        loading: '<svg viewBox="0 0 24 24"><path d="M12 4V2A10 10 0 0 0 2 12h2a8 8 0 0 1 8-8z"/></svg>',
        check: '<svg viewBox="0 0 24 24"><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/></svg>',
        error: '<svg viewBox="0 0 24 24"><path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/></svg>',
        video: '<svg viewBox="0 0 24 24"><path d="M18 4l2 4h-3l-2-4h-2l2 4h-3l-2-4H8l2 4H7L5 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V4h-4z"/></svg>',
        audio: '<svg viewBox="0 0 24 24"><path d="M12 3v10.55c-.59-.34-1.27-.55-2-.55-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4V7h4V3h-6z"/></svg>',
    };

    // ===== 元素建立 =====
    function createElements() {
        // 主按鈕
        const btn = document.createElement('button');
        btn.id = 'ytify-btn';
        btn.innerHTML = `${ICONS.download}<span>下載</span>`;
        btn.onclick = (e) => {
            e.stopPropagation();
            toggleMenu();
        };
        document.body.appendChild(btn);

        // 選單
        const menu = document.createElement('div');
        menu.id = 'ytify-menu';
        menu.innerHTML = `
            <div class="ytify-menu-item" data-format="best">${ICONS.video} 最佳畫質</div>
            <div class="ytify-menu-item" data-format="1080p">${ICONS.video} 1080p</div>
            <div class="ytify-menu-item" data-format="720p">${ICONS.video} 720p</div>
            <div class="ytify-menu-item" data-format="480p">${ICONS.video} 480p</div>
            <div class="ytify-menu-item" data-format="audio">${ICONS.audio} 僅音訊 (MP3)</div>
        `;
        menu.querySelectorAll('.ytify-menu-item').forEach(item => {
            item.onclick = () => {
                const format = item.dataset.format;
                hideMenu();
                downloadVideo(format === 'audio' ? 'best' : format, format === 'audio');
            };
        });
        document.body.appendChild(menu);

        // Toast
        const toast = document.createElement('div');
        toast.id = 'ytify-toast';
        document.body.appendChild(toast);

        // 進度條
        const progress = document.createElement('div');
        progress.id = 'ytify-progress';
        progress.innerHTML = `
            <div id="ytify-progress-title">準備下載...</div>
            <div id="ytify-progress-bar-bg"><div id="ytify-progress-bar"></div></div>
            <div id="ytify-progress-info">
                <span id="ytify-progress-percent">0%</span>
                <span id="ytify-progress-speed"></span>
            </div>
        `;
        document.body.appendChild(progress);

        // 點擊其他地方關閉選單
        document.addEventListener('click', hideMenu);
    }

    // ===== 選單控制 =====
    function toggleMenu() {
        const menu = document.getElementById('ytify-menu');
        menu.classList.toggle('show');
    }

    function hideMenu() {
        const menu = document.getElementById('ytify-menu');
        if (menu) menu.classList.remove('show');
    }

    // ===== Toast =====
    let toastTimer = null;
    function showToast(message, duration = 3000) {
        const toast = document.getElementById('ytify-toast');
        toast.textContent = message;
        toast.classList.add('show');

        if (toastTimer) clearTimeout(toastTimer);
        toastTimer = setTimeout(() => {
            toast.classList.remove('show');
        }, duration);
    }

    // ===== 進度條 =====
    function showProgress(title) {
        const progress = document.getElementById('ytify-progress');
        document.getElementById('ytify-progress-title').textContent = title || '準備下載...';
        document.getElementById('ytify-progress-bar').style.width = '0%';
        document.getElementById('ytify-progress-percent').textContent = '0%';
        document.getElementById('ytify-progress-speed').textContent = '';
        progress.classList.add('show');
    }

    function updateProgress(percent, speed) {
        document.getElementById('ytify-progress-bar').style.width = percent + '%';
        document.getElementById('ytify-progress-percent').textContent = Math.round(percent) + '%';
        if (speed) {
            document.getElementById('ytify-progress-speed').textContent = speed;
        }
    }

    function hideProgress() {
        document.getElementById('ytify-progress').classList.remove('show');
    }

    // ===== 按鈕狀態 =====
    function setButtonState(state, text) {
        const btn = document.getElementById('ytify-btn');
        btn.className = '';
        btn.id = 'ytify-btn';

        switch (state) {
            case 'loading':
                btn.classList.add('loading');
                btn.innerHTML = `${ICONS.loading}<span>${text || '處理中...'}</span>`;
                break;
            case 'success':
                btn.classList.add('success');
                btn.innerHTML = `${ICONS.check}<span>${text || '完成'}</span>`;
                setTimeout(() => setButtonState('normal'), 3000);
                break;
            case 'error':
                btn.classList.add('error');
                btn.innerHTML = `${ICONS.error}<span>${text || '失敗'}</span>`;
                setTimeout(() => setButtonState('normal'), 3000);
                break;
            default:
                btn.innerHTML = `${ICONS.download}<span>下載</span>`;
        }
    }

    // ===== API 請求 =====
    function apiRequest(method, path, data = null) {
        return new Promise((resolve, reject) => {
            GM_xmlhttpRequest({
                method: method,
                url: CONFIG.API_BASE + path,
                headers: { 'Content-Type': 'application/json' },
                data: data ? JSON.stringify(data) : null,
                timeout: 30000,
                onload: function(response) {
                    try {
                        const result = JSON.parse(response.responseText);
                        if (response.status >= 400) {
                            reject(new Error(result.detail || result.error || '請求失敗'));
                        } else {
                            resolve(result);
                        }
                    } catch {
                        if (response.status === 200) {
                            resolve({ status: 'ok' });
                        } else {
                            reject(new Error('解析回應失敗'));
                        }
                    }
                },
                onerror: function() {
                    reject(new Error('無法連接到 ytify 服務'));
                },
                ontimeout: function() {
                    reject(new Error('請求超時'));
                }
            });
        });
    }

    // ===== 狀態輪詢 =====
    function pollStatus(taskId, onProgress, onComplete, onError) {
        const startTime = Date.now();

        const poll = async () => {
            if (Date.now() - startTime > CONFIG.POLL_TIMEOUT) {
                onError(new Error('下載超時'));
                return;
            }

            try {
                const status = await apiRequest('GET', `/api/status/${taskId}`);

                if (status.status === 'downloading' || status.status === 'processing') {
                    onProgress(status.progress || 0, status.speed);
                    setTimeout(poll, CONFIG.POLL_INTERVAL);
                } else if (status.status === 'completed') {
                    onComplete(status);
                } else if (status.status === 'failed') {
                    onError(new Error(status.error || '下載失敗'));
                } else {
                    setTimeout(poll, CONFIG.POLL_INTERVAL);
                }
            } catch (e) {
                // 網路錯誤時繼續重試
                setTimeout(poll, CONFIG.POLL_INTERVAL * 2);
            }
        };

        poll();
    }

    // ===== 下載影片 =====
    async function downloadVideo(format = CONFIG.DEFAULT_FORMAT, audioOnly = false) {
        const url = window.location.href;

        // 檢查是否在影片頁面
        if (!url.includes('watch?v=') && !url.includes('/shorts/')) {
            showToast('請在影片頁面使用');
            return;
        }

        setButtonState('loading', '連接中...');

        try {
            // 1. 檢查服務狀態
            await apiRequest('GET', '/health');

            // 2. 取得影片資訊
            setButtonState('loading', '解析中...');
            const info = await apiRequest('POST', '/api/info', { url });
            showProgress(info.title || '下載中...');

            // 3. 開始下載
            setButtonState('loading', '下載中...');
            const result = await apiRequest('POST', '/api/download', {
                url: url,
                format: format,
                audio_only: audioOnly
            });

            if (!result.task_id) {
                throw new Error('無法建立下載任務');
            }

            // 4. 輪詢狀態
            pollStatus(
                result.task_id,
                // onProgress
                (progress, speed) => {
                    updateProgress(progress, speed);
                },
                // onComplete
                (status) => {
                    hideProgress();
                    setButtonState('success', '完成!');
                    showToast(`下載完成: ${status.filename || info.title}`);
                    GM_notification({
                        title: 'ytify',
                        text: `下載完成: ${status.filename || info.title}`,
                        timeout: 5000
                    });
                },
                // onError
                (error) => {
                    hideProgress();
                    setButtonState('error', '失敗');
                    showToast('下載失敗: ' + error.message);
                }
            );

        } catch (e) {
            hideProgress();
            setButtonState('error', '失敗');

            if (e.message.includes('無法連接')) {
                showToast('請先啟動 ytify 服務 (python main.py)');
            } else {
                showToast('錯誤: ' + e.message);
            }
        }
    }

    // ===== 右鍵選單 =====
    GM_registerMenuCommand('下載影片 (最佳畫質)', () => downloadVideo('best', false));
    GM_registerMenuCommand('下載影片 (720p)', () => downloadVideo('720p', false));
    GM_registerMenuCommand('下載音訊 (MP3)', () => downloadVideo('best', true));

    // ===== 初始化 =====
    function init() {
        if (document.getElementById('ytify-btn')) return;
        createElements();
    }

    // YouTube SPA 路由變化監聽
    let lastUrl = location.href;
    const observer = new MutationObserver(() => {
        if (location.href !== lastUrl) {
            lastUrl = location.href;
            // 確保按鈕存在
            if (!document.getElementById('ytify-btn')) {
                init();
            }
        }
    });

    observer.observe(document.body, { subtree: true, childList: true });

    // 頁面載入
    if (document.readyState === 'complete') {
        init();
    } else {
        window.addEventListener('load', init);
    }
})();
