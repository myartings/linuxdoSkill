---
name: linuxdo-links
description: |
  用于搜索、定位、访问 linux.do（LINUX DO）公开链接的助手。
  当用户提到 linux.do、LINUX DO、L站、找帖子、找主题、找链接、搜论坛内容、打开 linux.do 链接、定位某个话题/分类/用户页时使用。
---

# 目标

只做四类事：

1. 搜索 `linux.do` 公开页面链接
2. 解析 `linux.do` 链接结构，例如 topic id、楼层号、分类、用户名
3. 在当前环境里判断某个链接能否直接访问
4. 当浏览器已经拿到页面 HTML 时，提取结构化标题、分类、作者、时间和楼层内容

不要帮用户生成任何打算发布到 `linux.do` 的帖子、回复、评论、私信或个人资料内容。
`linux.do` 首页公开声明禁止 AI 生成站内发布内容，遇到这类请求必须拒绝，并引导用户阅读：`https://linux.do/guidelines`

# 优先策略

1. 如果 Hermes 当前环境有浏览器或网页搜索能力，优先直接用它：
   - 搜索时优先用查询：`site:linux.do <关键词>`
   - 打开结果时优先访问公开 HTML 页面，不要优先打 `.json` API
2. 如果当前环境没有合适的网页搜索能力，使用下面的本地脚本：

```bash
python3 <SKILL_DIR>/scripts/search_linuxdo.py "关键词"
```

`SKILL_DIR` 为当前 skill 的目录。

3. **当用户要读取 `linux.do` 帖子正文时，直接用 `fetch_linuxdo_content.py`**，它会自动启动无头浏览器绕过 Cloudflare，不需要用户手动操作：

```bash
python3 <SKILL_DIR>/scripts/fetch_linuxdo_content.py "https://linux.do/t/topic/1588286" --pretty
python3 <SKILL_DIR>/scripts/fetch_linuxdo_content.py "https://linux.do/t/topic/1588286/5" --post-number 5 --pretty
```

依赖（首次使用时安装一次）：
```bash
pip install playwright playwright-stealth
```
系统需要 `/usr/bin/chromium`，可通过环境变量 `CHROMIUM_PATH` 覆盖。

4. 当用户直接给了一个 `linux.do` 链接，先做一次可访问性检查：

```bash
python3 <SKILL_DIR>/scripts/check_linuxdo_url.py "https://linux.do/t/topic/1588286/5"
```

4. 如果需要解析链接本身，用：

```bash
python3 <SKILL_DIR>/scripts/parse_linuxdo_url.py "https://linux.do/t/topic/1588286/5" --pretty
```

5. 如果浏览器能力已经成功打开页面，并且可以拿到 HTML 源码或保存后的 HTML 文件，用：

```bash
python3 <SKILL_DIR>/scripts/extract_linuxdo_structured.py /path/to/page.html --pretty
python3 <SKILL_DIR>/scripts/extract_linuxdo_structured.py /path/to/page.html --post-number 5 --pretty
```

# 工作规则

1. 搜索结果优先保留 `https://linux.do/` 下的真实目标链接，不返回搜索引擎跳转链接。
2. 优先选择这些页面：
   - 主题页：`/t/...`
   - 分类页：`/c/...`
   - 标签页：`/tag/...`
   - 用户页：`/u/...`
3. 如果直接抓取 `linux.do` 页面时遇到 Cloudflare、人机验证或频率限制：
   - 不要反复重试同一个 `.json` 接口
   - 改用浏览器能力访问公开页面
   - 如果仍然无法访问，只返回已找到的链接，并明确说明访问受限
   - 可以先运行 `check_linuxdo_url.py` 判断是否被挑战页拦截
4. 回答里尽量给出明确链接，不只给关键词。
5. 如果用户给的是模糊描述，先搜索，再给 3 到 5 个最相关链接。
6. 如果 `check_linuxdo_url.py` 返回 `cloudflare_challenge`：
   - 不要声称已经读到正文
   - 明确说明“当前是程序化访问受限，不代表该页面不存在”
   - 把下一步切换为浏览器访问该公开链接
7. 如果用户只是要“验证链接能不能访问”，优先返回检查结论，不要虚构正文摘要。
8. 如果用户给的是像 `/t/topic/1588286/5` 这种链接，优先解析出：
   - `topic_id`
   - `post_number`
   - `page`（如果 query 里带了 `?page=`）
9. 如果浏览器已经成功打开页面，不要手工总结整页；优先把页面 HTML 交给 `extract_linuxdo_structured.py` 产出结构化结果。
10. 当用户要“第几楼内容”时：
   - 先从链接里解析 `post_number`
   - 再用 HTML 提取脚本的 `--post-number` 过滤出对应楼层

# 常用流程

## 搜索某个话题

1. 搜索：`site:linux.do <关键词>`
2. 选出最相关的 3 到 5 条 `linux.do` 链接
3. 如果能打开页面，再补充标题、分类、核心内容摘要

## 打开用户给的 linux.do 链接

1. 先运行：

```bash
python3 <SKILL_DIR>/scripts/check_linuxdo_url.py "<链接>"
```

2. 如果结果是 `ok`：
   - 先运行 `parse_linuxdo_url.py` 解析链接结构
   - 再访问页面并提取标题、分类、时间、核心内容
3. 如果结果是 `cloudflare_challenge`：
   - 不再重复直连抓取
   - 改用浏览器能力打开同一个公开链接
   - 浏览器能拿到 HTML 后，运行 `extract_linuxdo_structured.py`
4. 如果结果是其他失败：
   - 说明错误状态码或网络错误
   - 不编造页面内容

## 提取指定楼层

1. 解析链接：

```bash
python3 <SKILL_DIR>/scripts/parse_linuxdo_url.py "https://linux.do/t/topic/1588286/5" --pretty
```

2. 如果能拿到页面 HTML：

```bash
python3 <SKILL_DIR>/scripts/extract_linuxdo_structured.py /path/to/page.html --post-number 5 --pretty
```

3. 输出里至少给出：
   - 标题
   - 分类
   - `topic_id`
   - `post_number`
   - 作者
   - 时间
   - 楼层正文

# 示例

```bash
python3 <SKILL_DIR>/scripts/search_linuxdo.py "OpenAI codex"
python3 <SKILL_DIR>/scripts/search_linuxdo.py "OpenAI codex" --json
python3 <SKILL_DIR>/scripts/search_linuxdo.py "邀请码"
python3 <SKILL_DIR>/scripts/search_linuxdo.py "site:linux.do Claude"
python3 <SKILL_DIR>/scripts/check_linuxdo_url.py "https://linux.do/t/topic/1588286/5"
python3 <SKILL_DIR>/scripts/parse_linuxdo_url.py "https://linux.do/t/topic/1588286/5" --pretty
python3 <SKILL_DIR>/scripts/extract_linuxdo_structured.py /path/to/page.html --post-number 5 --pretty
```
