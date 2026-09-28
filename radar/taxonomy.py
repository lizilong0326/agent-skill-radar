"""Stable, multi-label taxonomy used by the collector and website."""

TAXONOMY = {
    "design": {"label": "设计", "patterns": [r"\bdesign system\b", r"\bui[/ -]?ux\b", r"\bfigma\b", r"界面设计", r"设计系统", r"视觉设计"]},
    "frontend": {"label": "前端开发", "patterns": [r"\breact\b", r"\bvue\b", r"\bfrontend\b", r"\bfront-end\b", r"\bcss\b", r"前端开发"]},
    "backend": {"label": "后端开发", "patterns": [r"\bbackend\b", r"\bback-end\b", r"\bfastapi\b", r"\bdjango\b", r"\bapi server\b", r"后端开发"]},
    "testing": {"label": "测试与质量", "patterns": [r"\btest[- ]driven\b", r"\bplaywright\b", r"\bunit tests?\b", r"\be2e\b", r"\bbehavioral evals?\b", r"测试用例", r"自动化测试"]},
    "security": {"label": "安全", "patterns": [r"\bsecurity audit\b", r"\bvulnerabilit", r"\bpenetration test", r"安全审计", r"漏洞扫描"]},
    "devops": {"label": "部署与运维", "patterns": [r"\bdevops\b", r"\bkubernetes\b", r"\bdocker\b", r"\bci[/ -]?cd\b", r"部署", r"运维"]},
    "data": {"label": "数据处理", "patterns": [r"\bdata analysis\b", r"\betl\b", r"\bsql\b", r"\bspreadsheet\b", r"数据分析", r"数据清洗"]},
    "research": {"label": "研究与检索", "patterns": [r"\bresearch\b", r"\bweb search\b", r"\bsearch (results|the web)\b", r"\bliterature review\b", r"资料检索", r"文献综述"]},
    "writing": {"label": "写作与内容", "patterns": [r"\bcopywriting\b", r"\bcontent writing\b", r"\bblog post\b", r"\bchangelog\b", r"\bux writer\b", r"\bwriting.{0,20}docs\b", r"文章写作", r"文案", r"内容创作"]},
    "product": {"label": "产品与规划", "patterns": [r"\bproduct management\b", r"\bprd\b", r"\broadmap\b", r"\buser stories\b", r"产品规划", r"需求分析"]},
    "marketing": {"label": "营销与增长", "patterns": [r"\bseo\b", r"\bmarketing\b", r"\bconversion rate\b", r"\bgrowth\b", r"营销", r"增长实验"]},
    "automation": {"label": "自动化", "patterns": [r"\bworkflow automation\b", r"\bautomate\b", r"\bautomation\b", r"自动化流程", r"工作流编排"]},
    "media": {"label": "图片与音视频", "patterns": [r"\bimage generation\b", r"\bvideo editing\b", r"\btranscription\b", r"\baudio processing\b", r"图像生成", r"视频剪辑", r"语音转写"]},
    "documents": {"label": "文档与知识", "patterns": [r"\bpdf\b", r"\bdocx\b", r"\bknowledge base\b", r"\bmarkdown document", r"文档处理", r"知识库"]},
    "agents": {"label": "Agent 开发", "patterns": [r"\bagent orchestration\b", r"\bmulti-agent\b", r"\bagent framework\b", r"智能体编排", r"多智能体"]},
    "agent-workflow": {"label": "Agent 工作流", "patterns": [r"\bsubagents?\b", r"\bagent workflow\b", r"\bparallel agents\b", r"\bagent session\b", r"智能体工作流"]},
    "code-review": {"label": "代码评审", "patterns": [r"\bcode review\b", r"\breview (a |the )?diff\b", r"\breviewing code\b", r"代码审查", r"代码评审"]},
    "debugging": {"label": "调试排错", "patterns": [r"\bdebugging\b", r"\bdiagnos(e|ing) bugs?\b", r"\broot cause analysis\b", r"故障排查", r"调试"]},
    "planning": {"label": "规划与拆解", "patterns": [r"\bimplementation plan\b", r"\bbrainstorming\b", r"\brequirements analysis\b", r"\bplanning\b", r"实施计划", r"任务拆解"]},
    "browser": {"label": "浏览器操作", "patterns": [r"\bbrowser automation\b", r"\bbrowser actions?\b", r"\bheadless brows", r"\bbrowser testing\b", r"\bchrome devtools\b", r"浏览器自动化", r"网页操作"]},
    "skill-management": {"label": "Skill 管理", "patterns": [r"\bdiscover (and install )?(agent )?skills\b", r"\bfind skills\b", r"\bskill install", r"\bskill creator\b", r"查找.{0,4}技能", r"管理.{0,4}Skill"]},
    "web-scraping": {"label": "网页抓取", "patterns": [r"\bscrap(e|ing)\b", r"\bweb crawl", r"\bsingle-page extraction\b", r"\bpage extraction\b", r"网页抓取", r"网页采集"]},
    "integration": {"label": "API 与集成", "patterns": [r"\bapi integration\b", r"\bsdk setup\b", r"\bintegrate.{0,25}(api|sdk|service)\b", r"\bexternal services\b", r"接口集成", r"接入.{0,8}API"]},
    "developer-workflow": {"label": "开发流程", "patterns": [r"\bpull request\b", r"\bgit worktrees?\b", r"\bgithub issues?\b", r"\bdevelopment branch\b", r"代码提交", r"开发流程"]},
    "diagrams": {"label": "图表与可视化", "patterns": [r"\barchitecture diagrams?\b", r"\binfographics?\b", r"\bdata visuali[sz]ation\b", r"\bflowcharts?\b", r"架构图", r"信息图", r"数据可视化"]},
    "communication": {"label": "沟通与协作", "patterns": [r"\bmessages?\b", r"\bemail\b", r"\bimessages?\b", r"\bteam collaboration\b", r"消息发送", r"团队协作"]},
    "market-data": {"label": "市场与金融数据", "patterns": [r"\bstock (market|prices?|quotes?)\b", r"\bmarket quotes?\b", r"\bprediction markets?\b", r"\bfinancial data\b", r"股票行情", r"市场数据"]},
    "monitoring": {"label": "监测与预警", "patterns": [r"\bmonitor(ing)?\b", r"\blive (disruption|status|alerts?)\b", r"\bcurrent .{0,25} alerts?\b", r"监测", r"预警"]},
    "mcp-development": {"label": "MCP 开发", "patterns": [r"\bbuild mcp\b", r"\bcreate an? mcp server\b", r"\bmodel context protocol servers?\b", r"开发.{0,8}MCP"]},
}

KINDS = {"skill": "Skill", "agent": "Agent", "mcp": "MCP", "tool": "工具"}

GROUP_LABELS = {
    "design-content": "设计与内容",
    "development": "开发与 Agent",
    "research-data": "研究与数据",
    "operations": "运营与通用工具",
}

TAG_GROUPS = {
    "design": "design-content", "writing": "design-content", "media": "design-content", "diagrams": "design-content", "documents": "design-content",
    "frontend": "development", "backend": "development", "testing": "development", "security": "development", "devops": "development",
    "agents": "development", "agent-workflow": "development", "code-review": "development", "debugging": "development",
    "planning": "development", "browser": "development", "skill-management": "development", "web-scraping": "development",
    "integration": "development", "developer-workflow": "development", "mcp-development": "development",
    "data": "research-data", "research": "research-data", "market-data": "research-data", "monitoring": "research-data",
    "product": "operations", "marketing": "operations", "automation": "operations", "communication": "operations",
}
