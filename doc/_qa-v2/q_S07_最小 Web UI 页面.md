# q_S07 · 最小 Web UI 页面

| 项 | 内容 |
| --- | --- |
| 用例编号 | `q_S07` |
| 分组 | A 核心工作流 S0-S14 |
| 采集时间 | 2026-11-07 08:06:47 +0800 |
| 证据完整性 | **COMPLETE** |
| 原始 verdict（历史，仅参考） | `PASS` |
| 本次判定 | **PENDING_REJUDGE** |
| 完整原始输出 | `evidence/q_S07.txt` |

> 原始 `verdict` / `reason` 不作为本次结论。本次只判断证据是否完整：
> `truncated=true` → `EVIDENCE_INSUFFICIENT`（既非通过也非失败）；
> `truncated=false` → `PENDING_REJUDGE`（仍需按证据重新推导，不得直接沿用历史 verdict）。

## 1 测试目标

验证原生 HTML 前端页面可访问（无构建链），且关键 tab 页面存在。

## 2 输入

- `GET /ui/index.html`
- `GET /ui/browse.html`
- `GET /ui/entity.html`
- `GET /ui/health.html`

## 3 期待输出

四个页面 HTTP 200 且返回 HTML 文本，非 404 / 非空白。

## 4 真实输出

```
$ GET /ui/index.html
  HTTP 200  1373 bytes  head=<!doctype html>
 <html lang="zh-CN">
 <head>
   <meta charset="utf-8">
   <meta name="viewport" content="width ...(截断)
$ GET /ui/browse.html
  HTTP 200  11387 bytes  head=<!doctype html>
 <html lang="zh-CN">
 <head>
   <meta charset="utf-8">
   <meta name="viewport" content="width ...(截断)
$ GET /ui/entity.html
  HTTP 200  2628 bytes  head=<!doctype html>
 <html lang="zh-CN">
 <head>
   <meta charset="utf-8">
   <meta name="viewport" content="width ...(截断)
$ GET /ui/health.html
  HTTP 200  2439 bytes  head=<!doctype html> <html lang="zh-CN"> <head>   <meta charset="utf-8">   <meta name="viewport" content="width=dev ...(截断)
```

## 5 结论

**PENDING_REJUDGE** — 证据完整，待按证据重判；本轮不给出 PASS/FAIL。
