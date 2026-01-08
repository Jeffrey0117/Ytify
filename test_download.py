# -*- coding: utf-8 -*-
"""
直接測試 yt-dlp 下載（不經過代理）
"""
import yt_dlp

url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # 測試影片

print("=" * 50)
print("直接測試 yt-dlp（無代理）")
print("=" * 50)

ydl_opts = {
    'format': 'best',
    'outtmpl': './downloads/test_%(title)s.%(ext)s',
    'quiet': False,
}

try:
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        print("\n取得影片資訊...")
        info = ydl.extract_info(url, download=False)
        print(f"標題: {info.get('title')}")
        print(f"時長: {info.get('duration')} 秒")
        print("\n開始下載...")
        ydl.download([url])
        print("\n下載成功!")
except Exception as e:
    print(f"\n錯誤: {e}")

input("\n按 Enter 結束...")
