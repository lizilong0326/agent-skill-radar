# Agent Skill Radar · 开源工具雷达

每天从 GitHub 发现和更新开源 Skill、Agent、MCP 等工具，阅读实际说明文件后生成可追溯的多标签目录。[在线浏览](https://lizilong0326.github.io/agent-skill-radar/)

## 设计边界

- **仓库与条目分开**：一个仓库可以包含多个 Skill；Star、增长、最近推送时间属于仓库，不是单个 Skill 的使用量。
- **先读文件再分类**：Skill 优先读取自己的 `SKILL.md`；其他项目读取 README。标签保留来源路径与原文片段。仓库名称不参与分类规则。
- **增量更新**：每天更新仓库元数据；说明文件变化或仍处于规则初筛时，逐批调用 DeepSeek。没有 Key 也能进行规则初筛，网站会明确显示分类方式。
- **保留历史**：30 天无代码更新进入观察；60 天无更新，或已观测的 60 天内 Star 零增长，退出默认目录并归档。历史数据仍保留，避免新索引误判。

## 项目结构

| 路径 | 作用 |
| --- | --- |
| `radar/collector.py` | GitHub 搜索、采集、增量更新、生命周期判断 |
| `radar/classifier.py` | 文件内容分类、DeepSeek 归类和证据核验 |
| `radar/taxonomy.py` | 可复用的多标签分类表 |
| `data/catalog.json` | 可机器读取的公开索引及仓库 Star 快照 |
| `site/` | 无服务端依赖的搜索、筛选和详情网站 |
| `skills/agent-radar/` | 供其他智能体查询同一目录的只读 Skill |
| `.github/workflows/daily-refresh.yml` | 每日采集与 GitHub Pages 发布 |

## 本地运行

需要 Python 3.9+，以及已登录的 GitHub CLI；也可以通过环境变量提供 `GITHUB_TOKEN`。

```bash
python3 -m radar.collector --max-new 12 --max-repos 40
python3 -m http.server 8765 --directory site
```

浏览 `http://localhost:8765/`。`--max-new` 控制本次新增仓库，`--max-repos` 控制单次处理总量，`--max-items-per-repo` 限制大仓库**每次**读取的 Skill 数量，后续每日运行会接着补齐未收录条目或检查尚未复核的文件。先用较小值核对采集质量，再逐步扩大。

运行有意义的分类、归档规则测试：

```bash
python3 -m unittest discover -s tests -v
```

## 使用 DeepSeek

在仓库 Settings → Secrets and variables → Actions 中添加名为 `DEEPSEEK_API_KEY` 的 Repository secret。工作流会在新文档或文档更新时自动使用 `deepseek-flash`。Key 不要提交到仓库，也不要写进前端代码。

添加 Key 后，定时工作流会逐批把规则初筛的旧条目补做 AI 归类。也可手动运行 `Refresh catalog and publish site` 工作流并选中 `reclassify_all`，立即重查文件。每次运行最多进行 100 次 AI 分类；超出上限的条目留待下次运行，可通过 `--max-ai-calls` 调整。模型输出的标签必须属于已定义分类，且每个依据片段必须出现在引用的文件中，否则不会采纳。

## 作为 Skill 查询

`skills/agent-radar/` 是目录的只读查询入口。将这个文件夹放进智能体支持的 Skills 目录后，可让智能体按任务查找条目，并返回标签依据、说明文件链接和仓库热度。它读取本项目每天发布的 JSON 索引，使用者无需 GitHub 或 DeepSeek API Key。

在仓库内也可直接试用：

```bash
python3 skills/agent-radar/scripts/search.py "网页抓取" --kind skill --limit 5
```

## 发布

工作流每天 UTC 18:17（北京时间次日 02:17）自动运行，也可手动触发。它更新 `data/catalog.json` 与 `site/data/catalog.json`，然后部署 `site/` 到 GitHub Pages。需在仓库设置中启用 Pages，Source 选择 **GitHub Actions**。GitHub 定时任务可能延迟；网站显示最近同步时间，建议关注失败通知。

## 费用与限额

这个公开仓库使用的标准 [GitHub Actions runner](https://docs.github.com/en/billing/concepts/product-billing/github-actions) 和 [GitHub Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages) 可免费使用。DeepSeek 仅对需要归类的条目计费，且单次工作流最多 100 次调用。按 [DeepSeek Flash 当前人民币价格](https://api-docs.deepseek.com/zh-cn/quick_start/pricing/)和每次约 4,000 输入、400 输出 token 举例，100 次调用约 **0.56 元（低峰）至 1.12 元（高峰）**；实际金额随文件长度、缓存命中和价格调整而变。网站访问者只读取已生成索引，不触发模型调用。

## 数据说明

搜索发现使用多个 GitHub 查询，再对候选项目验证许可证、Star 门槛、文档内容。当前分类是任务用途标签，不是对代码质量或安全性的担保。标签仅展示说明文件能支持的能力；转载内容保留仓库和原文链接，不把项目 README 或 Skill 内容整体复制进页面。

初版重点验证分类、来源和更新流程。GitHub 搜索有速率和结果限制，因此索引是经过发现规则筛选的目录，不宣称覆盖 GitHub 上所有工具。可调整 `SEARCH_QUERIES`、`SEED_REPOS` 和 CLI 参数扩容。

代码以 MIT 许可开放；收录工具各自遵守原仓库许可。
