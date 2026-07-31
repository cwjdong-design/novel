#!/usr/bin/env python3
"""章节备份 — 修改前自动归档到 03-版本备份/正文历史/"""
import sys, os, shutil
from datetime import datetime

BOOKS_DIR = os.path.expanduser("~/novels/books")

def backup_chapter(chapter_path: str):
    """备份章节到对应书籍的 正文历史/ 目录"""
    if not os.path.isfile(chapter_path):
        print(f"[ERROR] 文件不存在: {chapter_path}")
        sys.exit(1)
    
    # 解析路径: ~/novels/books/<书名>/01-正文存稿/第X章.md
    rel = os.path.relpath(chapter_path, BOOKS_DIR)
    parts = rel.split(os.sep)
    if len(parts) < 3:
        print(f"[ERROR] 无法解析书籍路径: {chapter_path}")
        sys.exit(1)
    
    book_name = parts[0]
    filename = parts[-1]
    name_no_ext = os.path.splitext(filename)[0]
    
    backup_dir = os.path.join(BOOKS_DIR, book_name, "03-版本备份", "正文历史")
    os.makedirs(backup_dir, exist_ok=True)
    
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"{name_no_ext}_{ts}.md"
    backup_path = os.path.join(backup_dir, backup_name)
    
    shutil.copy2(chapter_path, backup_path)
    print(f"[OK] {filename} → {backup_name}")
    return backup_path

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python backup_chapter.py <章节文件路径>")
        sys.exit(1)
    backup_chapter(sys.argv[1])
