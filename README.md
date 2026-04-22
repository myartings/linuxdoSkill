# linuxdo-links

给 `OpenClaw` / `Hermes` 用的 `linux.do` skill。

当前版本是本地 skill 形态，不是 MCP 服务。它主要做两件事：

1. 搜索公开的 `linux.do` 链接
2. 解析 `linux.do` 链接结构
3. 检测某个 `linux.do` 链接是否能被当前环境直接访问
4. 在浏览器已拿到 HTML 的前提下提取结构化帖子内容

## 适用场景

适合：

- “帮我找 `linux.do` 上关于 OpenAI 的帖子”
- “搜索 `linux.do` 里的邀请码相关链接”
- “测试这个 `linux.do` 链接当前能不能直接访问”

不适合：

- 直接当作 MCP server 注册到 `OpenClaw`
- 仅靠直连 HTTP 稳定抓取 `linux.do` 帖子正文
- 生成准备发布到 `linux.do` 的帖子、回复、私信内容

## 当前能力说明

这个 skill 目前通过公共搜索引擎结果页提取真实 `linux.do` 链接，并通过本地脚本完成：

- 搜索结果收集
- 链接结构解析
- 链接可访问性检测
- 浏览器导出的 HTML 结构化提取

由于 `linux.do` 当前会对程序化请求触发 Cloudflare challenge，直接请求某些页面时常见结果是：

- `403`
- `cf-mitigated: challenge`

所以这个 skill 的策略是：

1. 先搜索出真实链接
2. 再判断链接是不是被 challenge 挡住
3. 如果被挡住，就让宿主助手切到浏览器能力访问，而不是伪造正文

## 安装

把仓库放到 `OpenClaw` 的 skills 目录里，目录名建议就叫 `linuxdo-links`。

示例：

```bash
mkdir -p ~/.openclaw/skills
git clone https://github.com/myartings/linuxdoSkill.git ~/.openclaw/skills/linuxdo-links
```

如果你不是用 Git，也可以直接把整个目录复制到：

```bash
~/.openclaw/skills/linuxdo-links
```

## OpenClaw 使用方式

只要你的 `OpenClaw` / `Hermes` 能读取 `SKILL.md` 并允许执行本地 `python3` 脚本，这个 skill 就可以工作。

触发后主要会使用四个脚本：

### 1. 搜索 `linux.do` 链接

```bash
python3 <SKILL_DIR>/scripts/search_linuxdo.py "OpenAI"
python3 <SKILL_DIR>/scripts/search_linuxdo.py "邀请码" --limit 8
python3 <SKILL_DIR>/scripts/search_linuxdo.py "OpenAI" --json
```

### 2. 解析链接结构

```bash
python3 <SKILL_DIR>/scripts/parse_linuxdo_url.py "https://linux.do/t/topic/1588286/5" --pretty
```

### 3. 检测链接是否可直连

```bash
python3 <SKILL_DIR>/scripts/check_linuxdo_url.py "https://linux.do/t/topic/1588286/5"
```

可能输出：

- `ok`
- `cloudflare_challenge`
- `http_error`
- `network_error`

### 4. 从浏览器已拿到的 HTML 提取结构化内容

```bash
python3 <SKILL_DIR>/scripts/extract_linuxdo_structured.py /path/to/page.html --pretty
python3 <SKILL_DIR>/scripts/extract_linuxdo_structured.py /path/to/page.html --post-number 5 --pretty
```

这个脚本适合下面这种流程：

1. Hermes 发现直连 `linux.do` 被 Cloudflare challenge 挡住
2. Hermes 改用浏览器能力打开公开链接
3. Hermes 获取页面 HTML
4. 把 HTML 交给 `extract_linuxdo_structured.py` 输出结构化结果

## 目录结构

```text
.
├── .claude-plugin/
│   └── plugin.json
├── CLAUDE.md
├── README.md
├── SKILL.md
├── tests/
│   ├── fixtures/
│   └── test_linuxdo_skill.py
└── scripts/
    ├── extract_linuxdo_structured.py
    ├── parse_linuxdo_url.py
    ├── check_linuxdo_url.py
    └── search_linuxdo.py
```

## 已验证内容

本地已经验证过：

- `search_linuxdo.py` 可以返回真实 `linux.do` 链接
- `parse_linuxdo_url.py` 可以解析 topic id / 楼层号 / 分类 / 用户页
- `check_linuxdo_url.py` 可以识别 `403 + cf-mitigated=challenge`
- `extract_linuxdo_structured.py` 可以从测试 HTML 提取标题、分类和指定楼层内容

例如：

```bash
python3 scripts/check_linuxdo_url.py "https://linux.do/t/topic/1588286/5"
```

输出：

```text
cloudflare_challenge
status=403 cf_mitigated=challenge
```

## 测试

```bash
python3 -m unittest discover -s tests -p 'test_*.py'
```

## 限制

- 现在没有 MCP 服务
- 浏览器拿不到 HTML 时，不能承诺稳定读取帖子正文
- 搜索结果质量依赖公共搜索引擎
- 如果 `linux.do` 或搜索引擎策略变化，脚本可能需要调整

## License

MIT
