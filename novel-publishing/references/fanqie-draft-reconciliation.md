# 番茄草稿箱核对

## 直接进入草稿箱

不要为了核对而再次打开“新建章节”编辑器。该页面会调用 `POST /api/author/article/new_article/v0/`，即使不填写内容，也可能新增一个 0 字的“未命名草稿”。

已验证的草稿箱路由：

```text
https://fanqienovel.com/main/writer/chapter-manage/<BOOK_ID>&<URL编码书名>?type=2&from=chapter
```

已发布章节页使用同一路由并改为 `type=1`。

## 核对依据

页面表格至少核对：

- 草稿总数；
- 章节号与标题；
- 平台统计字数；
- 最近修改时间。

底层接口为：

```text
GET /api/author/chapter/draft_list/v1
```

关键返回字段：

```text
data.total_count
data.draft_list[].item_id
data.draft_list[].title
data.draft_list[].word_number
data.draft_list[].modify_time
```

优先以页面表格或该接口返回作为 `draft_saved_verified` 的证据，不以投递脚本打印的“已存草稿”单独作为最终证据。

## 多章投递

1. 逐章执行投递脚本，避免共用编辑器状态。
2. 全部投递完成后，只打开一次草稿箱路由统一对账。
3. 核对目标章节数量、标题和字数均匹配。
4. 保存草稿箱截图作为留痕。
5. 若发现自动生成的 0 字“未命名草稿”，仅报告；删除属于额外副作用，需得到用户明确授权。

## 字数口径

平台字数可能比本地按字符统计少 1 字或存在少量差异，应记录后台显示值，不要据此擅自修改正文。