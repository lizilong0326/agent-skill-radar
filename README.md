# Agent Skill Radar · 开源工具雷达

每天从 GitHub 发现和更新开源工具，阅读实际说明文件后生成可追溯的多标签目录；Agent / MCP 候选另补充 Hugging Face Spaces 和有公开源码的 Registry 项目。Skill、Agent、MCP 在同一目录中浏览，也可单独筛选。网站默认中文，可切换英文。[在线浏览](https://lizilong0326.github.io/agent-skill-radar/) · [工具目录](https://lizilong0326.github.io/agent-skill-radar/catalog.html)

## 设计边界

- **仓库与条目分开**：一个仓库可以包含多个 Skill；Star、增长、最近推送时间属于仓库，不是单个 Skill 的使用量。
- **先读文件再分类**：Skill 优先读取自己的 `SKILL.md`；其他项目读取 README。统一索引会对尚无能力标签的条目继续检查项目简介和原文摘录，标签保留来源链接与原文片段。仓库名称和“Agent / MCP”类型本身不构成能力依据；证据不足时保留未分类。
- **来源标签**：数据中保留能力、业务流程和行业依据；网站只将工具能力作为筛选项。行业标签分为“文档明示”和“由具体流程推断”，推断只表示可考虑的项目场景，不代表已完成行业部署或通过行业合规验证。
- **双语简介**：保留来源文档的原始简介，同时存储中文和英文版本。缺少中文时调用 DeepSeek 翻译；中文原文缺少英文时也会补译。翻译失败或没有 Key 时显示待翻译状态，不把英文伪装成中文。详情默认显示当前语言的项目简介；原文引用收在可展开的依据区。
- **一句话用途**：网站卡片只展示“适合用来做什么”的简短中英文句子；DeepSeek 根据来源简介和有依据的业务流程生成，新条目缺少模型结果时暂用截短的译文。原始简介仍保存在索引中供检索与核对。
- **增量更新**：每天更新仓库元数据；说明文件变化或仍处于规则初筛时，逐批调用 DeepSeek。没有 Key 也能进行规则初筛，网站会明确显示分类方式。
- **保留历史**：30 天无代码更新进入观察；60 天无更新，或已观测的 60 天内 Star 零增长，退出默认目录并归档。历史数据仍保留，避免新索引误判。
- **统一入口与来源**：`data/catalog.json` 和 `data/rankings.json` 是采集输入；合并时按项目来源 URL 和类型去重，Skill 则保留文件路径，因此同一仓库的多个 Skill 不会被折叠。网站只读取生成后的统一索引。GitHub Star 与 Hugging Face 点赞分别展示，不混算成跨平台排名。

## 项目结构

| 路径 | 作用 |
| --- | --- |
| `radar/collector.py` | GitHub 搜索、采集、增量更新、生命周期判断 |
| `radar/ranked_collector.py` | Agent / MCP 候选发现、来源核对和平台内排名 |
| `radar/unified_index.py` | 合并、去重、保留历史译文并生成网站统一索引 |
| `radar/classifier.py` | 文件内容分类、DeepSeek 归类和证据核验 |
| `radar/enrich_tags.py` | 为缺标签条目补能力标签、核对引用并缓存已复核来源 |
| `radar/translation.py` | 双语简介生成、来源变更检测和批量补译 |
| `radar/use_cases.py` | 生成可在卡片上快速浏览的双语用途句 |
| `radar/taxonomy.py` | 工具能力分类表 |
| `radar/facets.py` | 业务流程、行业适用和来源依据 |
| `radar/reindex_facets.py` | 从原始文件并发复核现有目录的业务标签 |
| `data/catalog.json` | 可机器读取的公开索引及仓库 Star 快照 |
| `data/rankings.json` | Agent / MCP 候选及逐条项目、说明文件引用 |
| `data/index.json` | 合并后的公开索引；网站使用 `site/data/index.json` 副本 |
| `site/` | 无服务端依赖的双语首页、工具目录与详情网站 |
| `skills/agent-radar/` | 供其他智能体查询同一目录的只读 Skill |
| `.github/workflows/daily-refresh.yml` | 每日采集与 GitHub Pages 发布 |

## 本地运行

需要 Python 3.9+，以及已登录的 GitHub CLI；也可以通过环境变量提供 `GITHUB_TOKEN`。

```bash
python3 -m radar.collector --max-new 12 --max-repos 40
python3 -m radar.ranked_collector --agent-target 300 --mcp-target 200
python3 -m radar.unified_index --max-ai-calls 50
python3 -m http.server 8765 --directory site
```

浏览 `http://localhost:8765/` 进入首页，也可直接打开 `http://localhost:8765/catalog.html` 使用工具目录。首页搜索和 Skill、Agent、MCP 入口都进入同一个目录；旧榜单网址会带着分类参数跳转过来。目录顶部切换三种核心类型，侧栏只按工具能力筛选；来源平台保留在卡片和详情中，用于追溯原文。支持列表/网格切换、⌘K 聚焦搜索，筛选条件写进网址，方便分享。默认“均衡浏览”交错展示三种核心类型，其他工具间隔出现；需要比较热度时可按 GitHub Star 或 Hugging Face Space 点赞分别排序。详情保留项目主页、说明文件、来源片段及收录时间。`--max-new` 控制本次新增仓库，`--max-repos` 控制单次处理总量，`--max-items-per-repo` 限制大仓库**每次**读取的 Skill 数量，后续每日运行会接着补齐未收录条目或检查尚未复核的文件。先用较小值核对采集质量，再逐步扩大。

如果 8765 端口被占用，换一个空闲端口即可，例如 `python3 -m http.server 8899 --directory site`。语言切换会保存在浏览器本地。

运行有意义的分类、归档规则测试：

```bash
python3 -m unittest discover -s tests -v
```

## 使用 DeepSeek

如需调用 DeepSeek，在项目根目录新建本地 `.env` 文件并填入密钥：

```dotenv
DEEPSEEK_API_KEY=你的密钥
DEEPSEEK_MODEL=deepseek-v4-flash
```

`.env` 已被 Git 忽略，不要提交到仓库或写进前端代码。分类、翻译和用途句会读取同一个模型配置。DeepSeek [官方说明](https://api-docs.deepseek.com/updates/)：原版 V4 Flash 已退役；`deepseek-v4-flash` 作为兼容名称仍可请求，但实际由 V4.1 Flash 处理。要为线上定时任务启用 DeepSeek，还需在仓库 Settings → Secrets and variables → Actions 添加名为 `DEEPSEEK_API_KEY` 的 Repository secret。

只为现有目录批量补齐中英文简介及用途句、无需重新请求 GitHub 时运行：

```bash
python3 -m radar.collector --translate-only --max-ai-calls 100
```

翻译按每批最多 12 条描述调用 DeepSeek；用途句和缺失的能力标签按每批最多 16 个工具处理。简介、用途句及能力核对会在来源未变化时复用已有结果；没有 Key 时保留规则标签和原文，缺译条目继续标记为待翻译。

添加 Key 后，定时工作流会逐批把规则初筛的旧条目补做 AI 归类，并补译缺少的简介、生成用途句和能力标签。也可手动运行 `Refresh catalog and publish site` 工作流并选中 `reclassify_all`，立即重查文件。每次运行最多进行 100 次 AI 调用，分类、翻译、用途句和补标签共用这一限额；超出上限的条目留待下次运行，可通过 `--max-ai-calls` 调整。模型输出的标签必须属于已定义分类，且每个依据片段必须出现在引用的文件中，否则不会采纳。

调整业务流程或行业规则后，可在本地重新读取现有条目的原始文件。默认只更新业务标签及其依据，保留已有的能力分类；加 `--capabilities` 会同时重跑尚未经过 DeepSeek 复核的能力规则。若简介修正而产生缺译，会调用少量 DeepSeek 翻译：

```bash
python3 -m radar.reindex_facets --workers 8 --capabilities
```

## 作为 Skill 查询

`skills/agent-radar/` 是目录的只读查询入口。将这个文件夹放进智能体支持的 Skills 目录后，可让智能体按任务查找条目，并返回标签依据、说明文件链接和仓库热度。它读取本项目每天发布的 JSON 索引，使用者无需 GitHub 或 DeepSeek API Key。

在仓库内也可直接试用：

```bash
python3 skills/agent-radar/scripts/search.py "网页抓取" --kind skill --limit 5
python3 skills/agent-radar/scripts/search.py --industry beauty --workflow appointments --limit 5
```

## Agent / MCP 候选采集

首批目标暂定 Agent 300 条、MCP 200 条；每日任务在前次候选数量之上再尝试各增加 10 条，实际增长取决于符合条件的新项目。GitHub 使用 Agent/MCP 专项搜索，再读取 README、检查可识别的开源许可证；Agent 也从 Hugging Face Spaces 搜索公开、带许可证的项目，MCP 可从官方 Registry 补充有公开源码和许可证的非 GitHub 项目。每条保留项目主页、说明文件或 Registry 登记、来源片段及采集时间。配置 `DEEPSEEK_API_KEY` 时还会判断项目主要用途；未配置时新条目可通过 README 规则初筛进入目录，但明确标为“初筛待复核”。

“GitHub 前 200”仅指**本次查询命中并通过自动 README 初筛的候选**按仓库 Star 排序；Hugging Face 点赞和 GitLab/Codeberg Star 单独展示，不能合并为跨平台总榜。自动初筛不等于安装、安全或功能验证；不足目标数时会如实保留实际数量。

本地重新生成：

```bash
python3 -m radar.ranked_collector --agent-target 300 --mcp-target 200
python3 -m radar.unified_index --max-ai-calls 50
```

## 发布

提交网站文件到 `main` 后，`Deploy site` 工作流会直接发布 `site/` 到 GitHub Pages。另一个工作流每天 UTC 18:17（北京时间次日 02:17）更新目录和榜单 JSON 后重新发布，也可手动触发。需在仓库设置中启用 Pages，Source 选择 **GitHub Actions**。GitHub 定时任务可能延迟；网站显示最近同步时间，建议关注失败通知。

## 费用与限额

这个公开仓库使用的标准 [GitHub Actions runner](https://docs.github.com/en/billing/concepts/product-billing/github-actions) 和 [GitHub Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages) 可免费使用。DeepSeek 仅对需要归类、补译或生成用途句的条目计费；主目录单次刷新最多 100 次模型调用，候选榜单复核会额外调用模型。实际金额随文档长度、候选变化、缓存命中和[模型价格](https://api-docs.deepseek.com/zh-cn/quick_start/pricing/)变化。网站访问者只读取已生成索引，不触发模型调用。

## 数据说明

搜索发现使用多个 GitHub 查询，再对候选项目验证许可证、Star 门槛、文档内容。当前分类不是对代码质量或安全性的担保。能力与流程来自说明文件；行业可直接被文档提及，也可由预约等具体流程谨慎推断，详情中显示来源片段和判断方式。转载内容保留仓库和原文链接，不把项目 README 或 Skill 内容整体复制进页面。Cal.diy 的 README 明确说明其社区版面向个人自托管、建议仅用于非生产环境；目录收录不构成生产使用建议。

初版重点验证分类、来源和更新流程。GitHub 搜索有速率和结果限制，因此索引是经过发现规则筛选的目录，不宣称覆盖 GitHub 上所有工具。可调整 `SEARCH_QUERIES`、`SEED_REPOS` 和 CLI 参数扩容。

代码以 MIT 许可开放；收录工具各自遵守原仓库许可。
