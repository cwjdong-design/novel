#!/usr/bin/env python3
"""通用章节更新脚本 — 读本地MD → 填后台编辑器 → 自动保存

用法：
    python3 update_chapter.py --book-id <BOOK_ID> --chapter-id <CHAPTER_ID> \
        --md-path <MD文件路径> --title <章节标题>

登录态依赖 ~/.hermes/browser-profiles/fanqie 的持久化 profile。
"""
import sys, os, argparse, time, tempfile
from playwright.sync_api import sync_playwright

PROFILE = os.path.expanduser('~/.hermes/browser-profiles/fanqie')


def update_chapter(book_id, chapter_id, md_path, title):
    """更新已发布章节的标题和正文

    Args:
        book_id: 番茄书 ID
        chapter_id: 番茄章节 ID
        md_path: 本地 MD 文件路径
        title: 章节标题
    """
    md_path = os.path.expanduser(md_path)

    # 读本地MD
    with open(md_path, 'r') as f:
        md = f.read()
    lines = md.strip().split('\n')
    bi = next(i for i, l in enumerate(lines) if l.startswith('##')) + 1
    body_text = '\n'.join([l for l in lines[bi:] if l.strip()])

    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=PROFILE,
            headless=False,
        )
        try:
            page = ctx.new_page()
            page.goto(
                f'https://fanqienovel.com/main/writer/{book_id}/publish/{chapter_id}/?enter_from=modifychapter',
                wait_until='domcontentloaded'
            )
            time.sleep(3)

            # 关弹窗
            m = page.query_selector('[role="dialog"]')
            if m:
                bs = page.query_selector_all('button:has-text("我知道了"), button:has-text("继续编辑"), button:has-text("关闭")')
                if bs:
                    bs[0].click()
                else:
                    page.keyboard.press('Escape')
                time.sleep(1)

            # 填标题
            page.locator('input[placeholder*="标题"]').evaluate(
                'el=>{const s=Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,"value").set;s.call(el,"' + title + '");el.dispatchEvent(new Event("input",{bubbles:true}));}'
            )
            time.sleep(0.5)

            # 填正文 — 直接改DOM + 触发React
            page.evaluate('''v => {
                const ed = document.querySelector('.serial-editor-container .ProseMirror[contenteditable="true"]');
                if (!ed) return;
                ed.innerHTML = v.split("\\n").filter(p => p.trim()).map(p => `<p>${p}</p>`).join("");
                ed.dispatchEvent(new Event("input", {bubbles:true, composed:true}));
                ed.focus();
            }''', body_text)
            time.sleep(1)

            # 触发React感知变化 → 自动保存
            page.locator('.serial-editor-container .ProseMirror[contenteditable="true"]').click(force=True)
            time.sleep(0.5)
            page.keyboard.type(' ')
            time.sleep(0.5)
            page.keyboard.press('Backspace')
            time.sleep(1)

            # 验证
            e = page.locator('.serial-editor-container .ProseMirror[contenteditable="true"]')
            t = e.inner_text().strip()
            print(f'LEN:{len(t)} START:{t[:60]}', flush=True)

            # 检查自动保存
            body = page.inner_text('body')
            if '已保存' in body:
                print('AUTO_SAVED ✅', flush=True)
            else:
                print('CHECK_MANUALLY', flush=True)

            screenshot_path = os.path.join(tempfile.gettempdir(), 'chapter_update_result.png')
            page.screenshot(path=screenshot_path)
            print(f'SCREENSHOT:{screenshot_path}', flush=True)
        finally:
            ctx.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='番茄小说章节更新')
    parser.add_argument('--book-id', required=True, help='番茄书 ID')
    parser.add_argument('--chapter-id', required=True, help='番茄章节 ID')
    parser.add_argument('--md-path', required=True, help='本地 MD 文件路径')
    parser.add_argument('--title', required=True, help='章节标题')
    args = parser.parse_args()

    update_chapter(args.book_id, args.chapter_id, args.md_path, args.title)
