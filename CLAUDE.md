# linuxdo-links

`linux.do` Skill，面向 Hermes / Claude 一类助手。

当前仓库是“轻量 skill”形态，不提供 MCP 服务，不直接代理 `linux.do` API。
它目前解决四件事：

1. 搜索公开 `linux.do` 链接
2. 解析链接结构
3. 检测某个 `linux.do` 链接是否能被当前环境直接访问
4. 从浏览器拿到的 HTML 中提取结构化帖子数据

## 当前能力边界

- 支持：通过公共搜索引擎结果页提取 `linux.do` 链接
- 支持：解析 topic id、楼层号、分类、tag、用户页
- 支持：检测链接是否被 Cloudflare challenge 拦截
- 支持：从 HTML 中提取标题、分类、作者、时间、正文和指定楼层
- 不支持：仅靠直连 HTTP 稳定抓取 `linux.do` 主题正文
- 不支持：任何站内发帖、回帖、私信生成
- 不支持：MCP server / REST API

之所以不直接实现正文抓取，是因为当前环境下直接请求 `https://linux.do/...` 经常返回：

- `403`
- `cf-mitigated: challenge`

也就是 Cloudflare 挑战页。这个仓库的策略是：

1. 先搜出真实链接
2. 再检测链接是否可直连
3. 解析链接里的 topic id / post number
4. 如果被 challenge 挡住，交给浏览器能力访问
5. 浏览器拿到 HTML 后，用本地解析脚本输出结构化结果

## 文件结构

```text
├── .claude-plugin/plugin.json
├── CLAUDE.md
├── SKILL.md
├── tests/
└── scripts/
    ├── extract_linuxdo_structured.py
    ├── parse_linuxdo_url.py
    ├── check_linuxdo_url.py
    └── search_linuxdo.py
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
