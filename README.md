# linuxdo-links

给 `OpenClaw` / `Hermes` 用的 `linux.do` skill。

当前版本是本地 skill 形态，不是 MCP 服务。它主要做两件事：

1. 搜索公开的 `linux.do` 链接
2. 检测某个 `linux.do` 链接是否能被当前环境直接访问

## 适用场景

适合：

- “帮我找 `linux.do` 上关于 OpenAI 的帖子”
- “搜索 `linux.do` 里的邀请码相关链接”
- “测试这个 `linux.do` 链接当前能不能直接访问”

不适合：

- 直接当作 MCP server 注册到 `OpenClaw`
- 稳定抓取 `linux.do` 帖子正文
- 生成准备发布到 `linux.do` 的帖子、回复、私信内容

## 当前能力说明

这个 skill 目前通过公共搜索引擎结果页提取真实 `linux.do` 链接，并通过本地脚本检查链接访问状态。

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

触发后主要会使用两个脚本：

### 1. 搜索 `linux.do` 链接

```bash
python3 <SKILL_DIR>/scripts/search_linuxdo.py "OpenAI"
python3 <SKILL_DIR>/scripts/search_linuxdo.py "邀请码" --limit 8
```

### 2. 检测链接是否可直连

```bash
python3 <SKILL_DIR>/scripts/check_linuxdo_url.py "https://linux.do/t/topic/1588286/5"
```

可能输出：

- `ok`
- `cloudflare_challenge`
- `http_error`
- `network_error`

## 目录结构

```text
.
├── .claude-plugin/
│   └── plugin.json
├── CLAUDE.md
├── README.md
├── SKILL.md
└── scripts/
    ├── check_linuxdo_url.py
    └── search_linuxdo.py
```

## 已验证内容

本地已经验证过：

- `search_linuxdo.py` 可以返回真实 `linux.do` 链接
- `check_linuxdo_url.py` 可以识别 `403 + cf-mitigated=challenge`

例如：

```bash
python3 scripts/check_linuxdo_url.py "https://linux.do/t/topic/1588286/5"
```

输出：

```text
cloudflare_challenge
status=403 cf_mitigated=challenge
```

## 限制

- 现在没有 MCP 服务
- 不能承诺稳定读取帖子正文
- 搜索结果质量依赖公共搜索引擎
- 如果 `linux.do` 或搜索引擎策略变化，脚本可能需要调整

## License

MIT
