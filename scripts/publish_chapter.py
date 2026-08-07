#!/usr/bin/env python3
"""番茄小说草稿箱投递脚本 — 自动解析 MD 章节并存入后台草稿箱

用法：
    python3 publish_chapter.py <章节号> --book <书名> [--book-id <ID>]

BOOK_ID 解析顺序：--book-id 参数 > 书配置.md 中的番茄BOOK_ID > 报错
KNOW_IDS 从 番茄章节ID.json 读取（不存在则空字典）
"""
import sys, os, json, time, argparse, html, re
from urllib.parse import quote
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
    """解析 MD 文件，返回 (章节号, 标题, HTML正文)

    内部委托给 parse_and_validate_md，不做 expected_chapter 校验以保持兼容。
    """
    result = parse_and_validate_md(path, expected_chapter=None)
    return result['chapter'], result['title'], result['body_html']


def parse_and_validate_md(path, expected_chapter=None):
    """解析并校验 MD 章节文件。

    Args:
        path: MD 文件路径
        expected_chapter: 期望的章节号，None 则不校验

    Returns:
        dict: {chapter, title, body_html}

    Raises:
        ValueError: NUL 字节、空标题、空正文、章节号不匹配
    """
    # 二进制读取以检测 NUL
    with open(path, 'rb') as f:
        raw_bytes = f.read()

    if b'\x00' in raw_bytes:
        raise ValueError("文件包含 NUL 字节，拒绝处理")

    try:
        text = raw_bytes.decode('utf-8', errors='strict')
    except UnicodeDecodeError as exc:
        raise ValueError(f"文件不是有效 UTF-8: {exc}") from exc
    lines = text.strip().split('\n')

    # 跳过可能的 POLISH/prompt 残留行——找到第一个 ## 第N章 行
    first_marker_idx = None
    for i, line in enumerate(lines):
        if line.strip().startswith('## 第'):
            first_marker_idx = i
            break
    if first_marker_idx is None:
        raise ValueError("首行格式错误：未找到 ## 第N章 开头的行")
    if first_marker_idx > 0:
        # 文件首部有残留——自动修剪文件
        lines = lines[first_marker_idx:]
        with open(path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines) + '\n')

    # 解析首行：## 第N章「标题」 或 ## 第N章 标题
    header = lines[0].strip()
    match = re.fullmatch(r'##\s*第(\d+)章\s*(?:「([^」]*)」|(.*))', header)
    if not match:
        raise ValueError("首行格式错误，应为 ## 第N章「标题」")
    ch_num = int(match.group(1))

    # 章节号校验
    if expected_chapter is not None and ch_num != expected_chapter:
        raise ValueError(
            f"章节号不一致：文件为第{ch_num}章，参数为第{expected_chapter}章"
        )

    # 提取标题
    title = (match.group(2) if match.group(2) is not None else match.group(3) or '').strip()

    if not title.strip():
        raise ValueError("标题为空")

    # 提取正文
    body_lines = [l.strip() for l in lines[1:] if l.strip()]

    if not body_lines:
        raise ValueError("正文为空")

    parts = [f'<p>{html.escape(l)}</p>' for l in body_lines]

    return {
        'chapter': ch_num,
        'title': title,
        'body_html': ''.join(parts),
    }


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
    el.evaluate('''(el, value)=>{
        const s=Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,"value").set;
        s.call(el,value);
        el.dispatchEvent(new Event("input",{bubbles:true}));
        el.dispatchEvent(new Event("change",{bubbles:true}));
    }''', value)


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


def validate_editor_elements(page):
    """校验编辑器页面的关键元素是否存在且唯一。

    只检查选择器 count()，不执行任何点击操作。
    元素缺失或多于一个即抛异常（fail closed）。

    Raises:
        Exception: 元素缺失或不唯一
    """
    required = {
        '章节序号输入框': '.serial-editor-title-left input[type="text"]',
        '标题输入框': 'input[placeholder*="标题"]',
        '正文编辑器': '.serial-editor-container .ProseMirror[contenteditable="true"]',
        '存草稿按钮': 'button:has-text("存草稿")',
    }

    for name, selector in required.items():
        count = page.locator(selector).count()
        if count == 0:
            raise RuntimeError(f"页面缺少元素: {name} ({selector})")
        if count > 1:
            raise RuntimeError(f"页面元素不唯一: {name} ({selector})，找到 {count} 个")
        locator = page.locator(selector)
        if not locator.is_visible():
            raise RuntimeError(f"页面元素不可见: {name} ({selector})")
        if name == '存草稿按钮' and not locator.is_enabled():
            raise RuntimeError(f"页面元素不可用: {name} ({selector})")


def find_duplicate_drafts(draft_list, expected_chapter, expected_title=None):
    """在草稿列表中查找与目标章节号+标题匹配的条目。

    Args:
        draft_list: 草稿列表，每项为 {chapter, title, ...}
        expected_chapter: 目标章节号
        expected_title: 目标标题

    Returns:
        list: 匹配的草稿条目（空列表表示无重复）
    """
    if not draft_list:
        return []
    return [d for d in draft_list if d.get('chapter') == expected_chapter and (
        expected_title is None or d.get('title') == expected_title
    )]


def normalize_draft_payload(payload):
    """规范化草稿箱 ``draft_list/v1`` 响应；不完整条目不参与判断。"""
    entries = ((payload or {}).get('data') or {}).get('draft_list') or []
    normalized = []
    for entry in entries:
        raw_title = entry.get('title')
        if not isinstance(raw_title, str):
            continue
        match = re.fullmatch(r'\s*第(\d+)章\s*(?:「([^」]+)」|(.+))\s*', raw_title)
        if not match:
            continue
        title = (match.group(2) or match.group(3) or '').strip()
        if not title:
            continue
        normalized.append({
            'chapter': int(match.group(1)),
            'title': title,
            'id': entry.get('item_id'),
            'word_count': entry.get('word_number'),
            'modify_time': entry.get('modify_time'),
        })
    return normalized


def snapshot_from_payload(payload):
    """将完整的单页 API 响应转为快照；任何歧义都 fail closed。"""
    data = (payload or {}).get('data') or {}
    entries = data.get('draft_list') or []
    total_count = data.get('total_count')
    if not isinstance(total_count, int) or total_count != len(entries):
        raise RuntimeError(
            f'草稿列表不完整：total_count={total_count!r}, entries={len(entries)}'
        )
    normalized = normalize_draft_payload(payload)
    if len(normalized) != len(entries):
        raise RuntimeError('草稿列表存在无法解析的章节号或标题，拒绝继续')
    return normalized


def reconcile_draft_result(before_drafts, after_drafts,
                           expected_chapter, expected_title):
    """用保存前后草稿快照对账；不从按钮点击推断保存成功。"""
    duplicates = find_duplicate_drafts(before_drafts, expected_chapter)
    if duplicates:
        return {
            'status': 'duplicate_detected',
            'chapter': expected_chapter,
            'title': expected_title,
            'platform_word_count': None,
            'duplicate_count': len(duplicates),
        }
    matches = find_duplicate_drafts(after_drafts, expected_chapter, expected_title)
    if matches:
        item = matches[0]
        return {
            'status': 'draft_saved_verified',
            'chapter': expected_chapter,
            'title': expected_title,
            'platform_word_count': item.get('word_count'),
            'draft_id': item.get('id'),
            'duplicate_count': 0,
        }
    return {
        'status': 'save_unverified',
        'chapter': expected_chapter,
        'title': expected_title,
        'platform_word_count': None,
        'duplicate_count': 0,
    }


def execute_draft_flow(before_drafts, chapter, title,
                       open_editor, click_save, postcheck):
    """可测试的副作用顺序：重复检查 → 打开编辑器 → 保存 → 后台对账。"""
    duplicate_result = reconcile_draft_result(before_drafts, before_drafts, chapter, title)
    if duplicate_result['status'] == 'duplicate_detected':
        return duplicate_result
    open_editor()
    click_save()
    after_drafts = postcheck()
    return reconcile_draft_result(before_drafts, after_drafts, chapter, title)


def clean_dirty_drafts(ctx, book_id, book_name):
    """发布前自动清理草稿箱中的0字/未命名脏草稿，防止严格校验被阻断。"""
    route = (
        f'https://fanqienovel.com/main/writer/chapter-manage/'
        f'{book_id}&{quote(book_name)}?type=2&from=chapter'
    )
    page = ctx.new_page()
    try:
        with page.expect_response(
            lambda r: '/api/author/chapter/draft_list/v1' in r.url and r.request.method == 'GET',
            timeout=15000,
        ) as pending:
            page.goto(route, wait_until='domcontentloaded')
        raw_entries = ((pending.value.json() or {}).get('data') or {}).get('draft_list') or []
    except Exception:
        page.close()
        return 0
    finally:
        try:
            page.close()
        except Exception:
            pass

    # 找脏草稿：0字 或 标题不含有效章节号 或 含"未命名"
    dirty_count = sum(
        1 for e in raw_entries
        if e.get('word_number', 0) == 0
        or '未命名' in e.get('title', '')
        or not re.match(r'\s*第\d+章', e.get('title', ''))
    )
    if dirty_count == 0:
        return 0

    # 打开草稿管理页逐个删除
    page = ctx.new_page()
    try:
        page.goto(route, wait_until='domcontentloaded')
        time.sleep(3)
        for _ in range(dirty_count + 1):
            del_btn = page.locator('.tomato-delete, .icon-delete')
            if del_btn.count() == 0:
                break
            del_btn.first.click(force=True)
            time.sleep(1)
            confirm = page.locator('button:has-text("确认"), button:has-text("删除")')
            if confirm.count() > 0:
                confirm.first.click(force=True)
                time.sleep(2)
    finally:
        page.close()
    return dirty_count


def fetch_draft_snapshot(ctx, book_id, book_name):
    """从草稿箱页面自身发出的已验证 API 响应获取结构化快照。"""
    route = (
        f'https://fanqienovel.com/main/writer/chapter-manage/'
        f'{book_id}&{quote(book_name)}?type=2&from=chapter'
    )
    page = ctx.new_page()
    try:
        with page.expect_response(
            lambda response: (
                '/api/author/chapter/draft_list/v1' in response.url
                and response.request.method == 'GET'
            ),
            timeout=15000,
        ) as pending:
            page.goto(route, wait_until='domcontentloaded')
        response = pending.value
        if not response.ok:
            raise RuntimeError(f'草稿列表接口返回 HTTP {response.status}')
        return snapshot_from_payload(response.json())
    except Exception as exc:
        raise RuntimeError(f'无法取得草稿箱结构化证据: {exc}') from exc
    finally:
        page.close()


def save_draft(chapter_num, md_path, book_name, book_id=None, know_ids=None):
    """新建单章草稿，并以前后草稿箱 API 快照完成对账。"""
    if know_ids is None:
        know_ids = {}

    parsed = parse_and_validate_md(md_path, expected_chapter=chapter_num)
    ch_num = parsed['chapter']
    title = parsed['title']
    body_html = parsed['body_html']

    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(user_data_dir=PROFILE, headless=False)
        editor = None
        try:
            # 清理草稿箱中的0字/未命名脏草稿（防止严格校验被阻断）
            try:
                clean_dirty_drafts(ctx, book_id, book_name)
            except Exception:
                pass  # 清理失败不阻塞主流程

            # 必须先查草稿箱；同章节号已存在即停止，不打开新建页。
            before_drafts = fetch_draft_snapshot(ctx, book_id, book_name)

            def open_editor():
                nonlocal editor
                editor = ctx.new_page()
                url = f'https://fanqienovel.com/main/writer/{book_id}/publish/?enter_from=newchapter'
                editor.goto(url, wait_until='domcontentloaded')
                time.sleep(3)
                dismiss_dialogs(editor)
                validate_editor_elements(editor)
                set_input_value(
                    editor.locator('.serial-editor-title-left input[type="text"]'),
                    str(ch_num),
                )
                set_input_value(editor.locator('input[placeholder*="标题"]'), title)
                fill_body(editor, body_html)

            def click_save():
                if editor is None:
                    raise RuntimeError('编辑器尚未打开，拒绝保存')
                editor.locator('button:has-text("存草稿")').click(force=True)
                time.sleep(3)

            def postcheck():
                return fetch_draft_snapshot(ctx, book_id, book_name)

            result = execute_draft_flow(
                before_drafts,
                ch_num,
                title,
                open_editor=open_editor,
                click_save=click_save,
                postcheck=postcheck,
            )
            print(json.dumps(result, ensure_ascii=False))
            return result
        finally:
            if editor is not None:
                editor.close()
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

    try:
        result = save_draft(args.chapter, md_path, args.book, book_id, know_ids)
    except Exception as exc:
        print(json.dumps({
            'status': 'failed_needs_review',
            'chapter': args.chapter,
            'error': str(exc),
        }, ensure_ascii=False))
        sys.exit(1)
    if result['status'] not in {'draft_saved_verified', 'duplicate_detected'}:
        sys.exit(2)
