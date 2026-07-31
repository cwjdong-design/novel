#!/usr/bin/env python3
"""番茄小说草稿箱投递脚本 — 自动解析 MD 章节并存入后台草稿箱

用法：
    python3 publish_chapter.py <章节号> --book <书名> [--book-id <ID>]

BOOK_ID 解析顺序：--book-id 参数 > 书配置.md 中的番茄BOOK_ID > 报错
KNOW_IDS 从 番茄章节ID.json 读取（不存在则空字典）
"""
import sys, os, json, time, argparse
from playwright.sync_api import sync_playwright

PROFILE = os.path.expanduser('~/.hermes/browser-profiles/fanqie')
BOOKS_DIR = os.path.expanduser('~/novels/books')


def load_book_id(book_name, explicit_id=None):
    """从 --book-id 参数或 书配置.md 读取 BOOK_ID"""
    if explicit_id:
        return explicit_id
    config_path = os.path.join(BOOKS_DIR, book_name, '02-设定文档', '书配置.md')
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith('番茄BOOK_ID:'):
                    return line.split(':', 1)[1].strip()
                if line.startswith('番茄BOOK_ID：'):
                    return line.split('：', 1)[1].strip()
    print(f'❌ 无法获取 BOOK_ID。请在 书配置.md 中添加「番茄BOOK_ID: xxx」或使用 --book-id 参数')
    sys.exit(1)


def load_know_ids(book_name):
    """从 番茄章节ID.json 读取已知章节ID（键为字符串，转为 int）"""
    ids_path = os.path.join(BOOKS_DIR, book_name, '02-设定文档', '番茄章节ID.json')
    if not os.path.exists(ids_path):
        return {}
    with open(ids_path, 'r') as f:
        raw = json.load(f)
    return {int(k): v for k, v in raw.items()}


def parse_md(path):
    """解析 MD 文件，返回 (章节号, 标题, HTML正文)"""
    with open(path, 'r') as f:
        lines = f.read().strip().split('\n')

    header = lines[0]
    ch_num = int(header.replace('## 第', '').split('章')[0].strip())
    rest = header.split('章', 1)[1].strip()
    if rest.startswith('「') and '」' in rest:
        title = rest[1:rest.index('」')]
    else:
        title = rest

    bi = next(i for i, l in enumerate(lines) if l.startswith('##')) + 1
    parts = [f'<p>{l.strip()}</p>' for l in lines[bi:] if l.strip()]

    return ch_num, title, ''.join(parts)


def dismiss_dialogs(page):
    """关闭编辑器弹窗"""
    page.keyboard.press('Escape'); time.sleep(0.5)
    page.keyboard.press('Escape'); time.sleep(0.5)
    for txt in ('我知道了', '继续编辑', '关闭'):
        for b in page.query_selector_all(f'button:has-text("{txt}")'):
            try:
                b.click(force=True, timeout=2000)
                time.sleep(0.5)
            except Exception:
                pass


def set_input_value(el, value):
    """安全设置 React 输入框值"""
    el.evaluate(f'''el=>{{
        const s=Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,"value").set;
        s.call(el,"{value}");
        el.dispatchEvent(new Event("input",{{bubbles:true}}));
        el.dispatchEvent(new Event("change",{{bubbles:true}}));
    }}''')


def fill_body(page, body_html):
    """填入正文到 ProseMirror 编辑器"""
    page.evaluate('''html=>{
        const e=document.querySelector('.serial-editor-container .ProseMirror[contenteditable="true"]');
        e.innerHTML=html;
        e.dispatchEvent(new Event("input",{bubbles:true,composed:true}));
        e.focus()
    }''', body_html)
    time.sleep(1)
    page.locator('.serial-editor-container .ProseMirror[contenteditable="true"]').click(force=True)
    page.keyboard.type(' ')
    page.keyboard.press('Backspace')
    time.sleep(3)


def publish(chapter_num, md_path, book_id=None, know_ids=None):
    """新建章节并存入草稿箱；本脚本不具备正式发布能力。"""
    if know_ids is None:
        know_ids = {}
    ch_num, title, body_html = parse_md(md_path)
    print(f'📄 第{ch_num}章「{title}」({len(body_html)}字符)')

    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(user_data_dir=PROFILE, headless=False)
        try:
            page = ctx.new_page()

            url = f'https://fanqienovel.com/main/writer/{book_id}/publish/?enter_from=newchapter'

            page.goto(url, wait_until='domcontentloaded')
            time.sleep(3)
            dismiss_dialogs(page)

            # 填序号
            num_input = page.locator('.serial-editor-title-left input[type="text"]')
            if num_input.count() > 0:
                set_input_value(num_input, str(ch_num))

            # 填标题
            ti = page.locator('input[placeholder*="标题"]')
            if ti.count() > 0:
                set_input_value(ti, title)

            # 填正文
            fill_body(page, body_html)

            # 只存草稿，绝不进入正式发布流程
            draft_btn = page.locator('button:has-text("存草稿")')
            if draft_btn.count() > 0:
                draft_btn.click(force=True)
                time.sleep(3)
                print(f'✅ 第{ch_num}章已存草稿')
            else:
                print(f'⚠️ 未找到存草稿按钮')

            print('🌐 浏览器保持打开，确认后手动关闭')
            time.sleep(10)
        finally:
            ctx.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='番茄小说草稿箱投递')
    parser.add_argument('chapter', type=int, help='章节号')
    parser.add_argument('--book', default='', help='书名（必填）')

    parser.add_argument('--book-id', default=None, help='番茄 BOOK_ID（覆盖书配置.md）')
    args = parser.parse_args()

    if not args.book:
        print('❌ --book 参数必填，请指定书名')
        sys.exit(1)

    md_path = os.path.join(BOOKS_DIR, args.book, '01-正文存稿', f'第{args.chapter}章.md')
    if not os.path.exists(md_path):
        print(f'❌ 文件不存在: {md_path}')
        sys.exit(1)

    book_id = load_book_id(args.book, args.book_id)
    know_ids = load_know_ids(args.book)

    print(f'📖 BOOK_ID={book_id}, 已知章节={len(know_ids)}个')
    publish(args.chapter, md_path, book_id, know_ids)
