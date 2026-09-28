const state = {
  catalog: null, repos: null, lang: 'zh', kind: 'all', capabilities: new Set(),
  query: '', sort: 'diverse', view: 'grid', limit: 24, loadError: false,
};
const $ = selector => document.querySelector(selector);
const kindLabels = {
  zh: { all: '全部', skill: 'Skill', agent: 'Agent', mcp: 'MCP', tool: '其他工具' },
  en: { all: 'All', skill: 'Skill', agent: 'Agent', mcp: 'MCP', tool: 'Other tools' },
};
const copy = {
  zh: {
    pageTitle: '工具目录 · Agent Skill Radar', pageDescription: '每天更新的开源 Skill、Agent 与 MCP 工具合集。按工具类型和能力筛选。',
    brandHome: 'Agent Skill Radar 首页', navLabel: '主导航', navHome: '首页', navCatalog: '工具目录', loadingCatalog: '正在读取目录…', viewGithub: 'GitHub ↗',
    browse: '浏览目录', filterHeading: '筛选工具', closeFilters: '关闭筛选', openFilters: '打开筛选',
    kindLabel: '工具类型', reviewAutomated: '自动核对', reviewPreliminary: '待进一步核对', industryHeading: '适用行业', workflowHeading: '业务流程', capabilityHeading: '工具能力',
    industryHint: '可多选', workflowHint: '可多选', capabilityHint: '可多选',
    facetNote: '能力标签来自项目说明，点击条目查看依据。',
    workspaceLabel: '搜索与筛选工具', searchLabel: '搜索工具、用途或仓库', searchPlaceholder: '搜索工具、用途或仓库…',
    sortLabel: '排序', sortDiverse: '均衡浏览', sortStars: 'GitHub Star', sortLikes: 'Space 点赞', sortAdded: '最近收录', sortUpdated: '最近维护', sortName: '名称',
    viewLabel: '视图', gridView: '网格视图', listView: '列表视图',
    catalogLabel: '统一目录', allTools: '全部工具', loading: '读取中…', clearAll: '清除筛选', loadMore: '显示更多', facetCoverage: '工具能力筛选只匹配有原文依据的标签；未标注条目仍可通过搜索和类型浏览。', originalDescription: '原文简介', descriptionHeading: '项目简介', candidateEvidence: '项目原文依据', openRegistry: '查看 Registry 登记 ↗', firstSeen: '收录时间', checkedAt: '最近核对', sourceMetric: '来源热度', reviewState: '核对状态',
    footerSync: 'Agent Skill Radar · 数据每天自动同步', footerStars: 'Star 和点赞属于来源项目，不代表单个工具的安装量。',
    unknown: '未知', lastSync: '最近同步', results: '个结果', noDescription: '暂无说明', translationPending: '中文翻译待生成，可切换英文查看原文。',
    noTags: '暂无标签', untagged: '待分类', growthPending: '增长数据待积累', growth30: '近 30 天', repoStars: '仓库 Star',
    archived: '已归档', watch: '观察中', emptyTitle: '没有找到匹配的工具', emptyBody: '试试减少筛选条件或换个关键词。',
    closeDetail: '关闭详情', capabilityEvidence: '工具能力与依据', workflowEvidence: '业务流程与依据', industryEvidence: '行业适用依据',
    explicit: '文档明确提及', inferred: '基于业务流程推断', noIndustry: '文档未显示具体行业用途，可按能力或业务流程判断。',
    inferredReason: '文档说明支持「{workflow}」，因此可能适用于「{industry}」项目；实际适配仍需检查功能。',
    source: '原文来源', repoData: '仓库数据', growthHistory: '暂无历史', lastCodeUpdate: '最近代码更新', license: '开源许可',
    unrecognized: '未识别', originalSources: '原始资料', openRepo: '打开项目 ↗', openSource: '查看说明文件 ↗',
    method: '能力分类方式', deepseekMethod: 'DeepSeek 文档归类', rulesMethod: '规则初筛，待 AI 核对', confidence: '置信度',
    classifiedAt: '分类时间', status: '状态', starDisclaimer: '来源热度不代表这个工具的安装量。',
    confidenceHigh: '高', confidenceMedium: '中', confidenceLow: '低', evidenceMissing: '当前没有足够的文档依据，等待进一步核对。',
    reasonGitHubArchived: 'GitHub 仓库已归档', reasonNoPush60: '超过 60 天没有代码更新',
    reasonNoStars60: '观察的 60 天内 Star 未增长', reasonNoPush30: '超过 30 天没有代码更新',
    loadFailure: '目录暂时不可用', readFailure: '读取失败', retryTitle: '目录暂时无法读取', retryBody: '请稍后刷新页面重试。',
    selectionNote: '同一维度多选为任一匹配；不同维度组合筛选。', industryUnverified: '适用场景建议，不代表该工具已在该行业部署。',
    usageCaution: '使用限制', viewEvidence: '查看原文与标签依据',
    useCaseLabel: '一句话用途', repoUpdated: '项目更新', updatedToday: '今天',
    capabilityPrefix: '能力', workflowPrefix: '流程', industryPrefix: '行业',
  },
  en: {
    pageTitle: 'Tool catalog · Agent Skill Radar', pageDescription: 'A daily collection of open-source Skills, Agents and MCP tools, filterable by type and capability.',
    brandHome: 'Agent Skill Radar home', navLabel: 'Main navigation', navHome: 'Home', navCatalog: 'Catalog', loadingCatalog: 'Loading catalog…', viewGithub: 'GitHub ↗',
    browse: 'Browse catalog', filterHeading: 'Filters', closeFilters: 'Close filters', openFilters: 'Open filters',
    kindLabel: 'Tool type', reviewAutomated: 'Automated review', reviewPreliminary: 'Needs further review', industryHeading: 'Industries', workflowHeading: 'Workflows', capabilityHeading: 'Capabilities',
    industryHint: 'Multi-select', workflowHint: 'Multi-select', capabilityHint: 'Multi-select',
    facetNote: 'Capability tags come from project documentation. Open an item to inspect the evidence.',
    workspaceLabel: 'Search and filter tools', searchLabel: 'Search tools, uses or repositories', searchPlaceholder: 'Search tools, uses or repositories…',
    sortLabel: 'Sort', sortDiverse: 'Balanced browse', sortStars: 'GitHub stars', sortLikes: 'Space likes', sortAdded: 'Recently added', sortUpdated: 'Recently maintained', sortName: 'Name',
    viewLabel: 'View', gridView: 'Grid view', listView: 'List view',
    catalogLabel: 'Unified catalog', allTools: 'All tools', loading: 'Loading…', clearAll: 'Clear filters', loadMore: 'Show more', facetCoverage: 'Capability filters match only tags supported by source text. Untagged entries remain searchable by name and type.', originalDescription: 'Source description', descriptionHeading: 'Project description', candidateEvidence: 'Source evidence', openRegistry: 'View Registry entry ↗', firstSeen: 'First listed', checkedAt: 'Last checked', sourceMetric: 'Source popularity', reviewState: 'Review status',
    footerSync: 'Agent Skill Radar · Data refreshes daily', footerStars: 'Stars and likes measure source projects, not installations of individual tools.',
    unknown: 'Unknown', lastSync: 'Last synced', results: 'results', noDescription: 'No description', translationPending: 'English translation pending. Switch to Chinese to view the original.',
    noTags: 'No tags yet', untagged: 'Unclassified', growthPending: 'Growth history pending', growth30: 'Last 30 days', repoStars: 'Repository stars',
    archived: 'Archived', watch: 'Watching', emptyTitle: 'No matching tools', emptyBody: 'Try fewer filters or a different keyword.',
    closeDetail: 'Close details', capabilityEvidence: 'Capabilities and evidence', workflowEvidence: 'Workflows and evidence', industryEvidence: 'Industry relevance',
    explicit: 'Named in documentation', inferred: 'Inferred from workflow', noIndustry: 'No specific industry is supported by the current documentation. Try capability or workflow filters.',
    inferredReason: 'The docs describe “{workflow}”, which may fit a “{industry}” project. Check actual feature fit.',
    source: 'Source', repoData: 'Repository data', growthHistory: 'No history yet', lastCodeUpdate: 'Last code update', license: 'Open-source license',
    unrecognized: 'Not identified', originalSources: 'Original sources', openRepo: 'Open project ↗', openSource: 'View source document ↗',
    method: 'Capability classification', deepseekMethod: 'DeepSeek document classification', rulesMethod: 'Rule screening; AI review pending', confidence: 'Confidence',
    classifiedAt: 'Classified on', status: 'Status', starDisclaimer: 'Source popularity does not indicate installations of this tool.',
    confidenceHigh: 'High', confidenceMedium: 'Medium', confidenceLow: 'Low', evidenceMissing: 'Not enough document evidence yet; awaiting further review.',
    reasonGitHubArchived: 'GitHub repository archived', reasonNoPush60: 'No code update for over 60 days',
    reasonNoStars60: 'No star growth over the observed 60 days', reasonNoPush30: 'No code update for over 30 days',
    loadFailure: 'Catalog unavailable', readFailure: 'Could not load', retryTitle: 'Could not load the catalog', retryBody: 'Please refresh the page later.',
    selectionNote: 'Selections within a group match any; groups are combined.', industryUnverified: 'Suggested relevance does not mean verified deployment in that industry.',
    usageCaution: 'Usage note', viewEvidence: 'View original text and tag evidence',
    useCaseLabel: 'Use case', repoUpdated: 'Project updated', updatedToday: 'Today',
    capabilityPrefix: 'Capability', workflowPrefix: 'Workflow', industryPrefix: 'Industry',
  },
};
const t = key => copy[state.lang][key] ?? key;
const escapeHtml = value => String(value ?? '').replace(/[&<>"']/g, char => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[char]);
function safeSourceUrl(value) {
  try { const url = new URL(value); return url.protocol === 'https:' && ['github.com', 'gitlab.com', 'codeberg.org', 'huggingface.co', 'registry.modelcontextprotocol.io'].includes(url.hostname) ? url.href : '#'; }
  catch { return '#'; }
}
const formatNumber = number => Number(number || 0).toLocaleString(state.lang === 'zh' ? 'zh-CN' : 'en-US');
function formatDate(value) {
  if (!value) return t('unknown');
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? t('unknown') : date.toLocaleDateString(state.lang === 'zh' ? 'zh-CN' : 'en-US', { year: 'numeric', month: '2-digit', day: '2-digit' });
}
function relativeUpdate(value) {
  const date = new Date(value);
  if (!value || Number.isNaN(date.getTime())) return t('unknown');
  const calendarDay = day => Date.UTC(day.getFullYear(), day.getMonth(), day.getDate());
  const days = Math.max(0, Math.round((calendarDay(new Date()) - calendarDay(date)) / 86400000));
  if (days === 0) return t('updatedToday');
  return state.lang === 'zh' ? formatNumber(days) + ' 天前' : formatNumber(days) + ' ' + (days === 1 ? 'day' : 'days') + ' ago';
}
const allItems = () => state.catalog?.items || [];
const repoMap = () => state.repos || new Map();
function labels(facet) {
  const keys = { capabilities: state.lang === 'zh' ? 'taxonomy' : 'taxonomy_en', workflows: state.lang === 'zh' ? 'workflow_labels' : 'workflow_labels_en', industries: state.lang === 'zh' ? 'industry_labels' : 'industry_labels_en' };
  return state.catalog?.[keys[facet]] || {};
}
const facetName = (facet, tag) => labels(facet)[tag] || tag;
function descriptionFor(record) {
  if (!record?.description) return t('noDescription');
  if (record[`description_${state.lang}`]) return record[`description_${state.lang}`];
  const originalIsChinese = /[\u3400-\u9fff]/.test(record.description);
  return (state.lang === 'zh') === originalIsChinese ? record.description : t('translationPending');
}
function useCaseFor(item) {
  const summary = item?.[`use_case_${state.lang}`];
  if (summary) return summary;
  if (state.lang === 'zh' && item?.summary_zh) return item.summary_zh;
  const description = descriptionFor(item).replace(/<[^>]*>/g, '').replace(/[`*#]/g, '').trim();
  const limit = state.lang === 'zh' ? 64 : 125;
  return description.length > limit ? description.slice(0, limit - 1).trimEnd() + '…' : description;
}
function popularityFor(item) {
  const metric = item.popularity || {};
  if (metric.metric === 'likes') return `${metric.platform || item.source_platform} ${state.lang === 'zh' ? '点赞' : 'likes'} ${formatNumber(metric.value)}`;
  if (metric.metric === 'stars') return `${metric.platform || item.source_platform} Star ${formatNumber(metric.value)}`;
  return t('unknown');
}
function reviewLabel(item) { return t(item.review_state === 'automated' ? 'reviewAutomated' : 'reviewPreliminary'); }
function matchesItem(item, skipCapabilities = false) {
  const repo = repoMap().get(item.repo_id);
  if (!repo || item.status !== 'active') return false;
  if (state.kind !== 'all' && item.kind !== state.kind) return false;
  if (!skipCapabilities && state.capabilities.size && ![...state.capabilities].some(tag => (item.tags || []).includes(tag))) return false;
  const query = state.query.trim().toLocaleLowerCase();
  if (!query) return true;
  const text = [item.name, item.description, item.description_zh, item.description_en, item.summary_zh, item.use_case_zh, item.use_case_en, item.evidence_excerpt,
    repo.full_name, repo.description, repo.description_zh, repo.description_en,
    ...(item.tags || []).flatMap(tag => [state.catalog.taxonomy?.[tag], state.catalog.taxonomy_en?.[tag]])].join(' ').toLocaleLowerCase();
  return text.includes(query);
}
function filteredItems() {
  const repos = repoMap();
  const items = allItems().filter(item => matchesItem(item));
  const score = item => {
    const query = state.query.trim().toLocaleLowerCase();
    if (!query) return 0;
    const name = item.name.toLocaleLowerCase();
    if (name === query) return 100;
    if (name.startsWith(query)) return 80;
    if (name.includes(query)) return 60;
    if ((item[`use_case_${state.lang}`] || '').toLocaleLowerCase().includes(query)) return 35;
    return 10;
  };
  items.sort((a, b) => {
    const ra = repos.get(a.repo_id), rb = repos.get(b.repo_id);
    if (state.sort === 'diverse' && state.query.trim()) return score(b) - score(a) || new Date(b.first_seen || 0) - new Date(a.first_seen || 0);
    if (state.sort === 'added') return new Date(b.first_seen || 0) - new Date(a.first_seen || 0);
    if (state.sort === 'updated') return new Date(rb.pushed_at || 0) - new Date(ra.pushed_at || 0);
    if (state.sort === 'stars') return (b.source_platform === 'GitHub' ? b.popularity?.value || 0 : -1) - (a.source_platform === 'GitHub' ? a.popularity?.value || 0 : -1);
    if (state.sort === 'likes') return (b.popularity?.metric === 'likes' ? b.popularity.value || 0 : -1) - (a.popularity?.metric === 'likes' ? a.popularity.value || 0 : -1);
    if (state.sort === 'name') return a.name.localeCompare(b.name, state.lang === 'zh' ? 'zh-CN' : 'en');
    return new Date(rb.pushed_at || 0) - new Date(ra.pushed_at || 0) || a.name.localeCompare(b.name, 'en');
  });
  if (state.sort === 'diverse' && !state.query.trim()) {
    const buckets = new Map();
    items.forEach(item => {
      const key = state.kind === 'all' ? item.kind : item.repo_id;
      if (!buckets.has(key)) buckets.set(key, []);
      buckets.get(key).push(item);
    });
    const spread = [];
    if (state.kind === 'all') {
      // Keep the three main categories visible together; "other" is supplementary.
      const primary = ['skill', 'agent', 'mcp'];
      while (spread.length < items.length) {
        for (let round = 0; round < 3; round++) {
          for (const kind of primary) {
            const bucket = buckets.get(kind);
            if (bucket?.length) spread.push(bucket.shift());
          }
        }
        const other = buckets.get('tool');
        if (other?.length) spread.push(other.shift());
      }
    } else {
      while (spread.length < items.length) {
        for (const bucket of buckets.values()) if (bucket.length) spread.push(bucket.shift());
      }
    }
    return spread;
  }
  return items;
}
function renderStatic() {
  document.documentElement.lang = state.lang === 'zh' ? 'zh-CN' : 'en';
  document.title = t('pageTitle');
  $('meta[name="description"]').content = t('pageDescription');
  document.querySelectorAll('[data-i18n]').forEach(node => { node.textContent = t(node.dataset.i18n); });
  document.querySelectorAll('[data-i18n-placeholder]').forEach(node => { node.placeholder = t(node.dataset.i18nPlaceholder); });
  document.querySelectorAll('[data-i18n-aria]').forEach(node => { node.setAttribute('aria-label', t(node.dataset.i18nAria)); });
  document.querySelectorAll('[data-lang]').forEach(node => node.setAttribute('aria-pressed', String(node.dataset.lang === state.lang)));
  document.querySelectorAll('[data-view]').forEach(node => node.setAttribute('aria-pressed', String(node.dataset.view === state.view)));
}
function renderSyncStatus() {
  $('#sync-status').textContent = `${t('lastSync')} ${formatDate(state.catalog.generated_at)}`;
}
function renderCapabilities() {
  const counts = {};
  allItems().filter(item => matchesItem(item, true)).forEach(item => (item.tags || []).forEach(tag => { counts[tag] = (counts[tag] || 0) + 1; }));
  const entries = Object.keys(labels('capabilities')).filter(tag => counts[tag] || state.capabilities.has(tag)).sort((a, b) => (counts[b] || 0) - (counts[a] || 0) || facetName('capabilities', a).localeCompare(facetName('capabilities', b), state.lang));
  $('#tag-filters').innerHTML = entries.length ? entries.map(tag => `<button type="button" data-facet="capabilities" data-tag="${escapeHtml(tag)}" class="sidebar-option" aria-pressed="${state.capabilities.has(tag)}"><span class="option-label">${escapeHtml(facetName('capabilities', tag))}</span><span class="option-count">${formatNumber(counts[tag] || 0)}</span></button>`).join('') : `<p class="no-options">${t('noTags')}</p>`;
}
function renderFilters() {
  const counts = { all: 0, skill: 0, agent: 0, mcp: 0, tool: 0 };
  allItems().filter(item => item.status === 'active').forEach(item => { counts.all++; counts[item.kind] = (counts[item.kind] || 0) + 1; });
  $('#kind-tabs').innerHTML = Object.entries(kindLabels[state.lang]).map(([kind, label]) => `<button type="button" class="type-option" data-kind="${kind}" aria-pressed="${state.kind === kind}"><span>${escapeHtml(label)}</span><strong>${formatNumber(counts[kind])}</strong></button>`).join('');
  renderCapabilities();
}
function renderSelected() {
  const chips = [];
  for (const tag of state.capabilities) chips.push(`<button type="button" data-remove-facet="capabilities" data-tag="${escapeHtml(tag)}" aria-label="${escapeHtml(t('clearAll') + ': ' + facetName('capabilities', tag))}">${escapeHtml(facetName('capabilities', tag))}<span aria-hidden="true">×</span></button>`);
  const coverage = state.capabilities.size ? `<span class="coverage-note">${t('facetCoverage')}</span>` : '';
  $('#active-filters').innerHTML = chips.length ? `<span class="selection-note">${t('selectionNote')}</span>${chips.join('')}${coverage}` : '';
  $('#clear-all').hidden = !chips.length && !state.query && state.kind === 'all';
}
function cardHtml(item, repo) {
  const capability = (item.tags || []).slice(0, 2).map(tag => `<span class="tag capability">${t('capabilityPrefix')} · ${escapeHtml(facetName('capabilities', tag))}</span>`);
  const tags = capability.join('') || `<span class="tag untagged">${t('untagged')}</span>`;
  const overviewLabel = item[`use_case_${state.lang}`] ? t('useCaseLabel') : t('originalDescription');
  return `<button type="button" class="card" data-id="${escapeHtml(item.id)}"><div class="card-top"><span class="kind-badge ${escapeHtml(item.kind)}">${escapeHtml(kindLabels[state.lang][item.kind] || kindLabels[state.lang].tool)}</span><span class="card-updated" title="${escapeHtml(formatDate(repo.pushed_at))}">${t('repoUpdated')} · ${relativeUpdate(repo.pushed_at)}</span></div><div class="card-identity"><h3>${escapeHtml(item.name)}</h3><div class="repo-name">${escapeHtml(item.source_platform || 'GitHub')} · ${escapeHtml(repo.full_name)}</div></div><div class="card-use-case"><span>${overviewLabel}</span><p>${escapeHtml(useCaseFor(item))}</p></div>${repo.usage_note_zh ? `<p class="usage-caution">${escapeHtml(repo['usage_note_' + state.lang] || repo.usage_note_zh)}</p>` : ''}<div class="card-tags">${tags}</div><div class="card-foot"><span>${escapeHtml(popularityFor(item))}</span><span>${escapeHtml(item.license || '')}</span></div></button>`;
}
function renderCards() {
  const items = filteredItems(), repos = repoMap();
  $('#results-title').textContent = state.kind === 'all' ? t('allTools') : kindLabels[state.lang][state.kind];
  $('#result-count').textContent = `${formatNumber(items.length)} ${t('results')}`;
  $('#cards').classList.toggle('list-view', state.view === 'list');
  $('#cards').innerHTML = items.length ? items.slice(0, state.limit).map(item => cardHtml(item, repos.get(item.repo_id))).join('') : `<div class="empty"><strong>${t('emptyTitle')}</strong><p>${t('emptyBody')}</p></div>`;
  $('#load-more').hidden = items.length <= state.limit;
  renderSelected();
}
function render() { if (!state.catalog) return; renderFilters(); renderCards(); }
function reasonFor(reason) {
  const keys = { 'GitHub 仓库已归档': 'reasonGitHubArchived', '超过 60 天没有代码更新': 'reasonNoPush60', '观察的 60 天内 Star 未增长': 'reasonNoStars60', '超过 30 天没有代码更新': 'reasonNoPush30' };
  return keys[reason] ? t(keys[reason]) : (state.lang === 'zh' ? reason : '');
}
function evidenceHtml(entry, item, facet) {
  return `<div class="evidence-row"><strong>${escapeHtml(facetName(facet, entry.tag))}</strong><blockquote>“${escapeHtml(entry.excerpt)}”</blockquote><a href="${safeSourceUrl(entry.url || item.source_url)}" target="_blank" rel="noopener noreferrer">${t('source')}: ${escapeHtml(entry.path)} ↗</a></div>`;
}
function showDetail(id) {
  const item = allItems().find(row => row.id === id), repo = item && repoMap().get(item.repo_id);
  if (!repo) return;
  const capabilities = (item.evidence || []).map(entry => evidenceHtml(entry, item, 'capabilities')).join('');
  const tagGroups = [
    (item.tags || []).length ? `<div class="detail-tag-group"><h3>${t('capabilityHeading')}</h3><div class="card-tags">${item.tags.map(tag => `<span class="tag capability">${escapeHtml(facetName('capabilities', tag))}</span>`).join('')}</div></div>` : '',
  ].filter(Boolean).join('');
  const reason = reasonFor(item.status_reason);
  const overviewLabel = item[`use_case_${state.lang}`] ? t('useCaseLabel') : t('originalDescription');
  const directEvidence = item.evidence_excerpt ? `<section class="detail-source"><h3>${t('candidateEvidence')}</h3><blockquote>“${escapeHtml(item.evidence_excerpt)}”</blockquote><a href="${safeSourceUrl(item.evidence_url || item.source_url)}" target="_blank" rel="noopener noreferrer">${t('openSource')}</a></section>` : '';
  const evidence = [directEvidence, capabilities ? `<section class="detail-section"><h3>${t('capabilityEvidence')}</h3>${capabilities}</section>` : ''].filter(Boolean).join('');
  const descriptionSection = `<section class="detail-description"><h3>${t('descriptionHeading')}</h3><p>${escapeHtml(descriptionFor(item))}</p></section>`;
  const registry = item.registry_url ? `<a href="${safeSourceUrl(item.registry_url)}" target="_blank" rel="noopener noreferrer">${t('openRegistry')}</a>` : '';
  $('#detail-content').innerHTML = `<div class="detail-head"><div><span class="kind-badge ${escapeHtml(item.kind)}">${escapeHtml(kindLabels[state.lang][item.kind] || kindLabels[state.lang].tool)}</span><span class="review-badge ${escapeHtml(item.review_state || 'preliminary')}">${escapeHtml(reviewLabel(item))}</span><h2 id="detail-title">${escapeHtml(item.name)}</h2><span class="repo-name">${escapeHtml(item.source_platform || 'GitHub')} · ${escapeHtml(repo.full_name)}</span></div><button type="button" class="detail-close" aria-label="${t('closeDetail')}">×</button></div><div class="detail-use-case"><span>${overviewLabel}</span><p>${escapeHtml(useCaseFor(item))}</p></div>${repo.usage_note_zh ? `<div class="detail-caution"><strong>${t('usageCaution')}</strong><p>${escapeHtml(repo['usage_note_' + state.lang] || repo.usage_note_zh)}</p><blockquote>${escapeHtml(repo.usage_note_excerpt || '')}</blockquote></div>` : ''}${descriptionSection}${tagGroups ? `<div class="detail-tag-groups">${tagGroups}</div>` : ''}<div class="detail-links"><a href="${safeSourceUrl(item.project_url || repo.url)}" target="_blank" rel="noopener noreferrer">${t('openRepo')}</a><a href="${safeSourceUrl(item.source_url)}" target="_blank" rel="noopener noreferrer">${t('openSource')}</a>${registry}</div><div class="detail-meta"><div><span>${t('sourceMetric')}</span><strong>${escapeHtml(popularityFor(item))}</strong></div><div><span>${t('lastCodeUpdate')}</span><strong>${formatDate(repo.pushed_at)}</strong></div><div><span>${t('firstSeen')}</span><strong>${formatDate(item.first_seen)}</strong></div><div><span>${t('license')}</span><strong>${escapeHtml(item.license || t('unrecognized'))}</strong></div></div>${evidence ? `<details class="detail-evidence"><summary>${t('viewEvidence')}</summary>${evidence}</details>` : ''}<p class="detail-note">${t('reviewState')}: ${escapeHtml(reviewLabel(item))} · ${t('checkedAt')}: ${formatDate(item.last_checked_at)}. ${t('starDisclaimer')}${reason ? ' ' + t('status') + ': ' + escapeHtml(reason) + '.' : ''}</p>`;
  $('#detail-dialog').showModal();
}
function setLanguage(language) {
  if (!copy[language]) return;
  state.lang = language;
  try { localStorage.setItem('agent-skill-radar-language', language); } catch { /* private browsing */ }
  renderStatic(); if (state.catalog) { renderSyncStatus(); render(); } else if (state.loadError) showLoadError();
  if ($('#detail-dialog').open) { const id = $('#detail-dialog').dataset.id; $('#detail-dialog').close(); showDetail(id); }
}
function updateUrl() {
  const params = new URLSearchParams();
  if (state.query) params.set('q', state.query);
  if (state.kind !== 'all') params.set('kind', state.kind);
  if (state.capabilities.size) params.set('tag', [...state.capabilities].join(','));
  if (state.sort !== 'diverse') params.set('sort', state.sort);
  if (state.view !== 'grid') params.set('view', state.view);
  history.replaceState(null, '', location.pathname + (params.size ? '?' + params : '') + location.hash);
}
function restoreUrl() {
  const params = new URLSearchParams(location.search);
  if (['inactive', 'review', 'industry', 'workflow', 'platform', 'top', 'new'].some(key => params.has(key))) {
    for (const key of ['inactive', 'review', 'industry', 'workflow', 'platform', 'top', 'new']) params.delete(key);
    history.replaceState(null, '', location.pathname + (params.size ? '?' + params : '') + location.hash);
  }
  state.query = params.get('q') || '';
  state.kind = ['all', 'skill', 'agent', 'mcp', 'tool'].includes(params.get('kind')) ? params.get('kind') : 'all';
  state.capabilities = new Set((params.get('tag') || '').split(',').filter(Boolean));
  state.sort = ['diverse', 'stars', 'likes', 'added', 'updated', 'name'].includes(params.get('sort')) ? params.get('sort') : 'diverse';
  state.view = params.get('view') === 'list' ? 'list' : 'grid';
  $('#search').value = state.query; $('#sort').value = state.sort;
}
function commitFilter() { state.limit = 24; updateUrl(); render(); }
function clearAll() {
  state.kind = 'all'; state.capabilities.clear();
  state.query = ''; $('#search').value = ''; commitFilter();
}
function setFilterDrawer(open) {
  document.body.classList.toggle('filters-open', open);
  $('#filter-backdrop').hidden = !open;
  $('#open-filters').setAttribute('aria-expanded', String(open));
}
function showLoadError() {
  $('#sync-status').textContent = t('loadFailure'); $('#result-count').textContent = t('readFailure');
  $('#cards').innerHTML = `<div class="empty"><strong>${t('retryTitle')}</strong><p>${t('retryBody')}</p></div>`;
}
document.addEventListener('click', event => {
  const language = event.target.closest('[data-lang]');
  if (language) { setLanguage(language.dataset.lang); return; }
  const kind = event.target.closest('[data-kind]');
  if (kind) { state.kind = kind.dataset.kind; commitFilter(); return; }
  const facet = event.target.closest('[data-facet][data-tag]');
  if (facet) { const set = state[facet.dataset.facet], tag = facet.dataset.tag; set.has(tag) ? set.delete(tag) : set.add(tag); commitFilter(); return; }
  const remove = event.target.closest('[data-remove-facet][data-tag]');
  if (remove) { state[remove.dataset.removeFacet].delete(remove.dataset.tag); commitFilter(); return; }
  const view = event.target.closest('[data-view]');
  if (view) { state.view = view.dataset.view; document.querySelectorAll('[data-view]').forEach(node => node.setAttribute('aria-pressed', String(node.dataset.view === state.view))); $('#cards').classList.toggle('list-view', state.view === 'list'); updateUrl(); return; }
  const card = event.target.closest('.card[data-id]');
  if (card) { $('#detail-dialog').dataset.id = card.dataset.id; showDetail(card.dataset.id); return; }
  if (event.target.closest('.detail-close')) $('#detail-dialog').close();
});
$('#search').addEventListener('input', event => { state.query = event.target.value; state.limit = 24; updateUrl(); if (state.catalog) { renderFilters(); renderCards(); } });
$('#sort').addEventListener('change', event => { state.sort = event.target.value; updateUrl(); renderCards(); });
$('#clear-all').addEventListener('click', clearAll);
$('#load-more').addEventListener('click', () => {
  const previousLimit = state.limit;
  state.limit += 24;
  const items = filteredItems(), repos = repoMap();
  $('#cards').insertAdjacentHTML('beforeend', items.slice(previousLimit, state.limit).map(item => cardHtml(item, repos.get(item.repo_id))).join(''));
  $('#load-more').hidden = items.length <= state.limit;
});
$('#open-filters').addEventListener('click', () => setFilterDrawer(true));
$('#close-filters').addEventListener('click', () => setFilterDrawer(false));
$('#filter-backdrop').addEventListener('click', () => setFilterDrawer(false));
$('#detail-dialog').addEventListener('click', event => { if (event.target === $('#detail-dialog')) $('#detail-dialog').close(); });
document.addEventListener('keydown', event => {
  if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') { event.preventDefault(); $('#search').focus(); $('#search').select(); }
  if (event.key === 'Escape' && document.body.classList.contains('filters-open')) setFilterDrawer(false);
});
try { state.lang = localStorage.getItem('agent-skill-radar-language') === 'en' ? 'en' : 'zh'; } catch { /* private browsing */ }
restoreUrl(); renderStatic();
fetch('./data/index.json', { cache: 'no-store' }).then(response => {
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json();
}).then(catalog => { state.catalog = catalog; state.repos = new Map((catalog.repositories || []).map(repo => [repo.id, repo])); renderSyncStatus(); render(); }).catch(() => { state.loadError = true; showLoadError(); });
