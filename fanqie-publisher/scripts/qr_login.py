#!/usr/bin/env python3
"""扫码登录番茄后台 — 截图二维码 → 用户扫码 → 自动检测登录 → 保持运行

用法：
    python3 qr_login.py [--profile <profile路径>]
"""
import os, signal, tempfile, time, argparse
from playwright.sync_api import sync_playwright

DEFAULT_PROFILE = os.path.expanduser('~/.hermes/browser-profiles/fanqie')


def main():
    parser = argparse.ArgumentParser(description='番茄扫码登录')
    parser.add_argument('--profile', default=DEFAULT_PROFILE, help='浏览器 profile 路径')
    args = parser.parse_args()

    profile = os.path.expanduser(args.profile)

    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(user_data_dir=profile, headless=False)
        page = ctx.new_page()

        # 打开首页 → 点登录 → 切扫码
        page.goto("https://fanqienovel.com", wait_until="load")
        time.sleep(1.5)

        if page.query_selector('text=登录'):
            page.click('text=登录')
            time.sleep(1)
            page.click('text=扫码登录')
            time.sleep(2)

        qr_path = os.path.join(tempfile.gettempdir(), 'fanqie_qr.png')
        page.screenshot(path=qr_path)
        print(f"QR:{qr_path}", flush=True)

        # 等待登录（检测登录按钮消失）
        for i in range(120):
            time.sleep(1)
            if not page.query_selector('text=登录'):
                print("LOGGED_IN", flush=True)
                break
            if 'writer' in page.url:
                print(f"LOGGED_IN at {page.url}", flush=True)
                break
        else:
            print("TIMEOUT", flush=True)

        # 保持运行，等待用户退出
        print("KEEP_ALIVE — 按 Ctrl+C 退出", flush=True)
        stop = False

        def cleanup(sig, frame):
            nonlocal stop
            stop = True

        signal.signal(signal.SIGINT, cleanup)
        signal.signal(signal.SIGTERM, cleanup)

        while not stop:
            time.sleep(1)

        ctx.close()
        print("已退出", flush=True)


if __name__ == '__main__':
    main()
