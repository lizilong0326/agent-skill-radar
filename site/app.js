const state = { catalog: null, kind: 'all', tags: new Set(), query: '', sort: 'stars', inactive: false, limit: 24 };
const $ = (selector) => document.querySelector(selector);
const kindLabels = { all: '全部', skill: 'Skill', agent: 'Agent', mcp: 'MCP', tool: '其他工具' };

function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>"']/g, char => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[char]);
}

function safeGithubUrl(value) {
  try {
    const url = new URL(value);
    return url.protocol === 'https:' && url.hostname === 'github.com' ? url.href : '#';
  } catch { return '#'; }
}

function formatNumber(number) { return Number(number || 0).toLocaleString('zh-CN'); }
function formatDate(value) {
  if (!value) return '未知';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? '未知' : date.toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit' });
}
function repoMap() { return new Map((state.catalog?.repositories || []).map(repo => [repo.id, repo])); }
function allItems() { return state.catalog?.items || []; }

function filteredItems() {
  const repos = repoMap();
  const query = state.query.trim().toLocaleLowerCase();
  const items = allItems().filter(item => {
    const repo = repos.get(item.repo_id);
    if (!repo || (!state.inactive && item.status !== 'active')) return false;
    if (state.kind !== 'all' && item.kind !== state.kind) return false;
    if (state.tags.size && ![...state.tags].every(tag => (item.tags || []).includes(tag))) return false;
    const tagNames = (item.tags || []).map(tag => state.catalog.taxonomy[tag] || tag).join(' ');
    const haystack = [item.name, item.description, item.summary_zh, repo.full_name, tagNames].join(' ').toLocaleLowerCase();
    return !query || haystack.includes(query);
  });
  items.sort((a, b) => {
    const repoA = repos.get(a.repo_id), repoB = repos.get(b.repo_id);
    if (state.sort === 'growth') return (repoB.stars_30d ?? -1) - (repoA.stars_30d ?? -1) || repoB.stars - repoA.stars;
    if (state.sort === 'updated') return new Date(repoB.pushed_at || 0) - new Date(repoA.pushed_at || 0);
    if (state.sort === 'name') return a.name.localeCompare(b.name, 'zh-CN');
    return repoB.stars - repoA.stars || a.name.localeCompare(b.name, 'zh-CN');
  });
  return items;
}

function renderMetrics() {
  const active = allItems().filter(item => item.status === 'active');
  const repoIds = new Set(active.map(item => item.repo_id));
  $('#metric-items').textContent = formatNumber(active.length);
  $('#metric-repos').textContent = formatNumber(repoIds.size);
  $('#metric-review').textContent = formatNumber(active.filter(item => item.method !== 'deepseek' || item.confidence === 'low').length);
  $('#sync-status').textContent = '最近同步 ' + formatDate(state.catalog.generated_at);
}

function renderKinds() {
  const counts = { all: 0, skill: 0, agent: 0, mcp: 0, tool: 0 };
  allItems().filter(item => state.inactive || item.status === 'active').forEach(item => { counts.all++; counts[item.kind] = (counts[item.kind] || 0) + 1; });
  $('#kind-tabs').innerHTML = Object.entries(kindLabels).map(([kind, label]) => `<button type="button" class="${state.kind === kind ? 'active' : ''}" data-kind="${kind}" aria-pressed="${state.kind === kind}">${label} <span>${counts[kind] || 0}</span></button>`).join('');
}

function renderTags() {
  const counts = {};
  allItems().filter(item => (state.inactive || item.status === 'active') && (state.kind === 'all' || item.kind === state.kind)).forEach(item => (item.tags || []).forEach(tag => counts[tag] = (counts[tag] || 0) + 1));
  const taxonomy = state.catalog.taxonomy || {};
  const tagGroups = state.catalog.tag_groups || {};
  const groups = state.catalog.group_labels || { general: '用途标签' };
  const entries = Object.entries(taxonomy).filter(([tag]) => counts[tag]).sort((a, b) => (counts[b[0]] || 0) - (counts[a[0]] || 0));
  $('#tag-filters').innerHTML = Object.entries(groups).map(([group, title]) => {
    const buttons = entries.filter(([tag]) => (tagGroups[tag] || 'general') === group).map(([tag, label]) => `<button type="button" data-tag="${escapeHtml(tag)}" class="${state.tags.has(tag) ? 'selected' : ''}" aria-pressed="${state.tags.has(tag)}"><span>${escapeHtml(label)}</span><span>${counts[tag]}</span></button>`).join('');
    return buttons ? `<div class="tag-group"><h3>${escapeHtml(title)}</h3>${buttons}</div>` : '';
  }).join('') || '<span class="repo-name">暂无标签</span>';
}

function cardHtml(item, repo) {
  const tags = (item.tags || []).length ? item.tags.map(tag => `<span>${escapeHtml(state.catalog.taxonomy[tag] || tag)}</span>`).join('') : '<span class="untagged">待分类</span>';
  const growth = repo.stars_30d == null ? '<span class="growth none">增长数据待积累</span>' : `<span class="growth">近 30 天 +${formatNumber(Math.max(0, repo.stars_30d))}</span>`;
  return `<button type="button" class="card" data-id="${escapeHtml(item.id)}">
    <div class="card-top"><span class="kind-badge ${escapeHtml(item.kind)}">${escapeHtml(kindLabels[item.kind] || '工具')}</span>${item.status !== 'active' ? `<span class="state-badge">${item.status === 'archived' ? '已归档' : '观察中'}</span>` : ''}</div>
    <h3>${escapeHtml(item.name)}</h3><div class="repo-name">${escapeHtml(repo.full_name)} · ${escapeHtml(item.source_path)}</div>
    <p class="card-description">${escapeHtml(item.summary_zh || item.description || repo.description || '暂无说明')}</p>
    <div class="card-tags">${tags}</div>
    <div class="card-foot"><span>仓库 Star <strong>${formatNumber(repo.stars)}</strong></span>${growth}</div>
  </button>`;
}

function renderCards() {
  const items = filteredItems();
  const repos = repoMap();
  $('#results-title').textContent = state.kind === 'all' ? '全部工具' : kindLabels[state.kind];
  $('#result-count').textContent = `${formatNumber(items.length)} 个结果`;
  $('#cards').innerHTML = items.length ? items.slice(0, state.limit).map(item => cardHtml(item, repos.get(item.repo_id))).join('') : '<div class="empty"><strong>没有找到匹配的工具</strong>试试减少筛选条件或换个关键词。</div>';
  $('#load-more').hidden = items.length <= state.limit;
}

function render() { if (!state.catalog) return; renderMetrics(); renderKinds(); renderTags(); renderCards(); }

function showDetail(id) {
  const item = allItems().find(row => row.id === id);
  if (!item) return;
  const repo = repoMap().get(item.repo_id);
  if (!repo) return;
  const evidence = (item.evidence || []).map(entry => `<div class="evidence-row"><strong>${escapeHtml(state.catalog.taxonomy[entry.tag] || entry.tag)}</strong><blockquote>“${escapeHtml(entry.excerpt)}”</blockquote><a href="${safeGithubUrl(item.source_url)}" target="_blank" rel="noopener noreferrer">来源：${escapeHtml(entry.path)} ↗</a></div>`).join('') || '<p class="repo-name">当前没有足够的文档依据，等待进一步核对。</p>';
  $('#detail-content').innerHTML = `<div class="detail-content">
    <div class="detail-head"><div><span class="kind-badge ${escapeHtml(item.kind)}">${escapeHtml(kindLabels[item.kind] || '工具')}</span><h2 id="detail-title">${escapeHtml(item.name)}</h2><span class="repo-name">${escapeHtml(repo.full_name)}</span></div><button type="button" class="detail-close" aria-label="关闭详情">×</button></div>
    <p class="detail-description">${escapeHtml(item.description || repo.description || '暂无说明')}</p>
    ${item.summary_zh ? `<p class="detail-summary">${escapeHtml(item.summary_zh)}</p>` : ''}
    <div class="detail-section"><h3>标签依据</h3>${evidence}</div>
    <div class="detail-section"><h3>仓库数据</h3><div class="detail-meta"><div>仓库 Star<strong>${formatNumber(repo.stars)}</strong></div><div>近 30 天增长<strong>${repo.stars_30d == null ? '暂无历史' : '+' + formatNumber(Math.max(0, repo.stars_30d))}</strong></div><div>最近代码更新<strong>${formatDate(repo.pushed_at)}</strong></div><div>开源许可<strong>${escapeHtml(repo.license || '未识别')}</strong></div></div></div>
    <div class="detail-section"><h3>原始资料</h3><div class="detail-links"><a href="${safeGithubUrl(repo.url)}" target="_blank" rel="noopener noreferrer">打开仓库 ↗</a><a href="${safeGithubUrl(item.source_url)}" target="_blank" rel="noopener noreferrer">查看说明文件 ↗</a></div><p class="detail-note">分类方式：${item.method === 'deepseek' ? 'DeepSeek 文档归类' : '规则初筛，待 AI 核对'} · 置信度：${escapeHtml(item.confidence || '未知')} · 分类时间：${formatDate(item.classified_at)}。仓库 Star 不代表这个工具的安装量。${item.status_reason ? '状态：' + escapeHtml(item.status_reason) + '。' : ''}</p></div>
  </div>`;
  $('#detail-dialog').showModal();
}

document.addEventListener('click', event => {
  const kind = event.target.closest('[data-kind]');
  if (kind) { state.kind = kind.dataset.kind; state.limit = 24; render(); return; }
  const tag = event.target.closest('[data-tag]');
  if (tag) { const value = tag.dataset.tag; state.tags.has(value) ? state.tags.delete(value) : state.tags.add(value); state.limit = 24; render(); return; }
  const card = event.target.closest('.card[data-id]');
  if (card) { showDetail(card.dataset.id); return; }
  if (event.target.closest('.detail-close')) $('#detail-dialog').close();
});
$('#search').addEventListener('input', event => { state.query = event.target.value; state.limit = 24; renderCards(); });
$('#sort').addEventListener('change', event => { state.sort = event.target.value; renderCards(); });
$('#include-inactive').addEventListener('change', event => { state.inactive = event.target.checked; state.limit = 24; render(); });
$('#clear-tags').addEventListener('click', () => { state.tags.clear(); render(); });
$('#toggle-tags').addEventListener('click', () => {
  const expanded = $('#filters').classList.toggle('expanded');
  $('#toggle-tags').setAttribute('aria-expanded', String(expanded));
  $('#toggle-tags').textContent = expanded ? '收起标签' : '展开标签';
});
$('#load-more').addEventListener('click', () => { state.limit += 24; renderCards(); });
$('#detail-dialog').addEventListener('click', event => { if (event.target === $('#detail-dialog')) $('#detail-dialog').close(); });

fetch('./data/catalog.json', { cache: 'no-store' }).then(response => {
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json();
}).then(catalog => {
  state.catalog = catalog;
  render();
}).catch(() => {
  $('#sync-status').textContent = '目录暂时不可用';
  $('#result-count').textContent = '读取失败';
  $('#cards').innerHTML = '<div class="empty"><strong>目录暂时无法读取</strong>请稍后刷新页面重试。</div>';
});
