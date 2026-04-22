# linuxdo-links

`linux.do` Skill，面向 Hermes / Claude 一类助手。

当前仓库是”轻量 skill”形态，不提供 MCP 服务。
它目前解决五件事：

1. 搜索公开 `linux.do` 链接
2. 解析链接结构
3. 检测某个 `linux.do` 链接是否能被当前环境直接访问
4. 从浏览器拿到的 HTML 中提取结构化帖子数据
5. **全自动抓取帖子正文**（无需用户操作，自动绕过 Cloudflare）

## 当前能力边界

- 支持：通过公共搜索引擎结果页提取 `linux.do` 链接
- 支持：解析 topic id、楼层号、分类、tag、用户页
- 支持：检测链接是否被 Cloudflare challenge 拦截
- 支持：从 HTML 中提取标题、分类、作者、时间、正文和指定楼层
- **支持：全自动抓取帖子正文**（Playwright + Stealth 绕过 CF，in-browser 调 Discourse JSON API）
- 不支持：任何站内发帖、回帖、私信生成
- 不支持：MCP server / REST API

## 自动化抓取策略

直接 HTTP 请求 `linux.do` 会被 Cloudflare 拦截（403 + cf-mitigated: challenge）。
Discourse JSON API 从外部调用也同样被拦截。

当前解决方案（`fetch_linuxdo_content.py`）：
1. 用 Playwright + playwright-stealth 启动无头 Chromium
2. 导航到目标页面，让浏览器通过 CF challenge
3. 在已建立的浏览器 session 内，用 `page.evaluate()` 调用 Discourse JSON API（`/t/{id}.json`）
4. CF 不会拦截来自已验证 session 的 API 请求
5. 解析 JSON，用 `clean_text()` 清理 cooked HTML，输出结构化数据

依赖：`pip install playwright playwright-stealth` + 系统 Chromium（`/usr/bin/chromium`）

## 文件结构

```text
├── .claude-plugin/plugin.json
├── CLAUDE.md
├── SKILL.md
├── tests/
└── scripts/
    ├── fetch_linuxdo_content.py      # 全自动抓取（Playwright + Discourse API）
    ├── extract_linuxdo_structured.py  # 从 HTML 提取结构化数据
    ├── parse_linuxdo_url.py           # 解析链接结构
    ├── check_linuxdo_url.py           # 检测链接可访问性
    └── search_linuxdo.py              # 搜索 linux.do 链接
```

## 脚本

### 搜索链接

```bash
python3 scripts/search_linuxdo.py "OpenAI"
python3 scripts/search_linuxdo.py "邀请码" --limit 8
python3 scripts/search_linuxdo.py "OpenAI" --json
```

输出是排序后的真实 `linux.do` URL，优先主题页。

### 检测链接可访问性

```bash
python3 scripts/parse_linuxdo_url.py "https://linux.do/t/topic/1588286/5" --pretty
python3 scripts/check_linuxdo_url.py "https://linux.do/t/topic/1588286/5"
```

可能返回：

- `ok`
- `cloudflare_challenge`
- `http_error`
- `network_error`

### 提取结构化 HTML

```bash
python3 scripts/extract_linuxdo_structured.py tests/fixtures/topic_page.html --pretty
python3 scripts/extract_linuxdo_structured.py tests/fixtures/topic_page.html --post-number 5 --pretty
```

## 修改约束

- 不要在 `SKILL.md` 中暗示已有正文抓取能力，除非你先验证过
- 不要添加任何会让助手生成 `linux.do` 站内发布内容的提示词
- 如果以后要加“正文提取”，优先走浏览器自动化或宿主浏览器能力，不要默认打 `.json`
- 修改 HTML 提取逻辑时，同时更新 `tests/fixtures` 和 `tests/test_linuxdo_skill.py`

## 已验证现状

本地已验证：

- `search_linuxdo.py` 能返回 `linux.do` 真实链接
- `parse_linuxdo_url.py` 能解析常见 `linux.do` 链接
- `check_linuxdo_url.py` 能识别 `403 + cf-mitigated=challenge`
- `extract_linuxdo_structured.py` 能从 fixture HTML 提取指定楼层
