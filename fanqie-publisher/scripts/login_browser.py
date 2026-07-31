#!/usr/bin/env python3
"""番茄小说登录浏览器 — 保持打开，等待用户手动登录

用途：首次登录或登录态失效时，用此脚本启动 Chromium，
用户在浏览器中手动扫码/验证码登录，cookie 保存到固定 profile。
后续所有 Playwright 操作复用该 profile，自动携带登录态。

用法：
    python3 login_browser.py [--profile <profile路径>]

    登录完成后直接关闭浏览器窗口，或 Ctrl+C 终止。
"""
import os, signal, sys, time, argparse
from playwright.sync_api import sync_playwright

DEFAULT_PROFILE = os.path.expanduser('~/.hermes/browser-profiles/fanqie')
SITE = "https://fanqienovel.com"


def main():
    parser = argparse.ArgumentParser(description='番茄登录浏览器')
    parser.add_argument('--profile', default=DEFAULT_PROFILE, help='浏览器 profile 路径')
    args = parser.parse_args()

    profile = os.path.expanduser(args.profile)

    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir=profile,
            headless=False,
        )
        page = browser.pages[0] if browser.pages else browser.new_page()
        page.goto(SITE)
        print(f"浏览器已打开: {page.title()}", flush=True)
        print(f"URL: {page.url}", flush=True)
        print("请在浏览器中手动登录番茄小说。", flush=True)
        print("登录完成后，关闭浏览器窗口或在此终端按 Ctrl+C 退出。", flush=True)
        print("------", flush=True)

        stop = False

        def on_signal(sig, frame):
            nonlocal stop
            stop = True

        signal.signal(signal.SIGINT, on_signal)
        signal.signal(signal.SIGTERM, on_signal)

        while not stop:
            time.sleep(1)

        print("\n关闭浏览器...", flush=True)
        browser.close()


if __name__ == '__main__':
    main()
