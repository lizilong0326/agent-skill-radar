const homeCopy = {
  zh: {
    pageTitle: 'Agent Skill Radar · 找到适合项目的开源工具',
    pageDescription: '发现适合项目的开源 Skill、Agent 与 MCP 工具。每天更新，按文档判断用途与适用场景。',
    brandHome: 'Agent Skill Radar 首页', navLabel: '主导航', navHome: '首页', navCatalog: '工具目录', viewGithub: 'GitHub ↗',
    eyebrow: '每天更新 · 按真实文档整理', heroTitle: '找到适合你项目的<br><span>开源 AI 工具</span>',
    heroDescription: '从 GitHub 和其他开源社区收集 Skill、Agent、MCP。看一眼它能做什么，再按类型、能力和应用场景找到合适的项目。',
    searchLabel: '搜索开源工具', searchPlaceholder: '搜索工具、用途或仓库…', searchButton: '搜索工具', browseAll: '浏览全部工具 ↗',
    overviewLabel: '目录概况', updatedDaily: '每日更新', listedTools: '在列工具', openRepos: '来源项目',
    loading: '正在读取最新目录…', lastSync: '最近同步', loadFailure: '目录暂时无法读取，请稍后刷新。',
    reviewNote: count => count + ' 条仍待进一步核对；详情页保留当前分类依据。',
    startHere: '从这里开始', categoryTitle: '按工具类型浏览', categoryDescription: '三种核心类型都在同一目录中，也可以直接搜索工具或用途。',
    skillDescription: '可复用的任务说明与工作方法', agentDescription: '能执行多步任务的智能体项目',
    mcpDescription: '连接工具和数据的协议服务', otherTools: '其他工具', toolDescription: '相关开源应用、组件与资源',
    methodNote: '工具类型和能力标签依据项目说明与使用示例；打开条目可查看原文。',
    footerNote: 'Star 和点赞代表来源项目热度，不代表单个工具的安装量。',
  },
  en: {
    pageTitle: 'Agent Skill Radar · Find open-source tools for your project',
    pageDescription: 'Find open-source Skills, Agents and MCP tools for your project. Updated daily and categorized from documentation.',
    brandHome: 'Agent Skill Radar home', navLabel: 'Main navigation', navHome: 'Home', navCatalog: 'Catalog', viewGithub: 'GitHub ↗',
    eyebrow: 'Updated daily · Grounded in documentation', heroTitle: 'Find open-source tools<br><span>for your project</span>',
    heroDescription: 'Explore Skills, Agents and MCP servers from GitHub and other open-source communities. Find a fit by type, capability or use case.',
    searchLabel: 'Search open-source tools', searchPlaceholder: 'Search tools, uses or repositories…', searchButton: 'Search tools', browseAll: 'Browse all tools ↗',
    overviewLabel: 'Catalog overview', updatedDaily: 'Updated daily', listedTools: 'Listed tools', openRepos: 'Source projects',
    loading: 'Loading the latest catalog…', lastSync: 'Last synced', loadFailure: 'Catalog unavailable. Please refresh later.',
    reviewNote: count => count + ' entries still need further review; current classification evidence is available in their details.',
    startHere: 'Start here', categoryTitle: 'Browse by tool type', categoryDescription: 'All three core types share one catalog. You can also search by tool or use case.',
    skillDescription: 'Reusable task instructions and methods', agentDescription: 'Agent projects for multi-step tasks',
    mcpDescription: 'Protocol servers that connect tools and data', otherTools: 'Other tools', toolDescription: 'Related open-source apps, components and resources',
    methodNote: 'Tool types and capability tags come from project docs and examples. Open an entry to inspect the source.',
    footerNote: 'Stars and likes indicate source project interest, not installations of an individual tool.',
  },
};
let homeLang = 'zh';
let homeCatalog = null;
let homeLoadError = false;

function renderHome() {
  const copy = homeCopy[homeLang];
  document.documentElement.lang = homeLang === 'zh' ? 'zh-CN' : 'en';
  document.title = copy.pageTitle;
  document.querySelector('meta[name="description"]').content = copy.pageDescription;
  document.querySelectorAll('[data-i18n]').forEach(node => { node.textContent = copy[node.dataset.i18n]; });
  document.querySelectorAll('[data-i18n-html]').forEach(node => { node.innerHTML = copy[node.dataset.i18nHtml]; });
  document.querySelectorAll('[data-i18n-placeholder]').forEach(node => { node.placeholder = copy[node.dataset.i18nPlaceholder]; });
  document.querySelectorAll('[data-i18n-aria]').forEach(node => { node.setAttribute('aria-label', copy[node.dataset.i18nAria]); });
  document.querySelectorAll('[data-lang]').forEach(node => { node.setAttribute('aria-pressed', String(node.dataset.lang === homeLang)); });

  if (homeLoadError) {
    document.querySelector('#home-sync').textContent = copy.loadFailure;
    return;
  }
  if (!homeCatalog) return;
  const active = (homeCatalog.items || []).filter(item => item.status === 'active');
  const number = count => Number(count).toLocaleString(homeLang === 'zh' ? 'zh-CN' : 'en-US');
  const byKind = { skill: 0, agent: 0, mcp: 0, tool: 0 };
  active.forEach(item => { byKind[item.kind] = (byKind[item.kind] || 0) + 1; });
  document.querySelector('#home-count-items').textContent = number(active.length);
  document.querySelector('#home-count-repos').textContent = number(new Set(active.map(item => item.repo_id)).size);
  for (const kind of Object.keys(byKind)) document.querySelector('#home-count-' + kind).textContent = number(byKind[kind]);
  const date = new Date(homeCatalog.generated_at);
  document.querySelector('#home-sync').textContent = Number.isNaN(date.getTime()) ? '' : copy.lastSync + ' ' + date.toLocaleDateString(homeLang === 'zh' ? 'zh-CN' : 'en-US', { year: 'numeric', month: '2-digit', day: '2-digit' });
  const reviewCount = active.filter(item => item.review_state === 'preliminary').length;
  document.querySelector('#home-review').textContent = reviewCount ? copy.reviewNote(number(reviewCount)) : '';
}

const catalogParams = new URLSearchParams(location.search);
if (['q', 'kind', 'industry', 'workflow', 'tag', 'sort', 'inactive', 'view', 'platform', 'review', 'top', 'new'].some(key => catalogParams.has(key))) {
  location.replace('./catalog.html' + location.search + location.hash);
} else {
  document.querySelectorAll('[data-lang]').forEach(button => button.addEventListener('click', () => {
    homeLang = button.dataset.lang;
    try { localStorage.setItem('agent-skill-radar-language', homeLang); } catch { /* private browsing */ }
    renderHome();
  }));
  try { homeLang = localStorage.getItem('agent-skill-radar-language') === 'en' ? 'en' : 'zh'; } catch { /* private browsing */ }
  renderHome();
  fetch('./data/index.json', { cache: 'no-store' }).then(response => {
    if (!response.ok) throw new Error('HTTP ' + response.status);
    return response.json();
  }).then(catalog => { homeCatalog = catalog; renderHome(); }).catch(() => { homeLoadError = true; renderHome(); });
}
