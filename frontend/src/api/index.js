export const API_BASE = '/api'

export async function scanDirectory(path, extensions, recursive = false, maxDepth = 3) {
  const res = await fetch(`${API_BASE}/files/scan`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ path, extensions, recursive, max_depth: maxDepth })
  })
  const data = await res.json()
  return Array.isArray(data) ? { files: data } : data
}

export async function pickDirectory(initialDir = '') {
  const res = await fetch(`${API_BASE}/desktop/pick-directory`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ initial_dir: initialDir || null })
  })
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new Error(data.detail || '打开文件夹选择器失败')
  }
  return res.json()
}

export async function getCommonDirectories() {
  const res = await fetch(`${API_BASE}/desktop/common-directories`)
  if (!res.ok) throw new Error('获取常用目录失败')
  return res.json()
}

export async function getPathSuggestions(query, limit = 12) {
  const res = await fetch(`${API_BASE}/desktop/path-suggestions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, limit })
  })
  if (!res.ok) throw new Error('获取路径建议失败')
  return res.json()
}

export async function validateDirectory(path) {
  const res = await fetch(`${API_BASE}/desktop/validate-directory`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ path })
  })
  if (!res.ok) throw new Error('校验目录失败')
  return res.json()
}

export async function filterFiles(filters) {
  const res = await fetch(`${API_BASE}/files/filter`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(filters)
  })
  const data = await res.json()
  return Array.isArray(data) ? { files: data } : data
}

export async function extractRegex(files, pattern) {
  const res = await fetch(`${API_BASE}/regex/extract`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ files, pattern })
  })
  return res.json()
}

export async function groupByField(files, pattern, field) {
  const res = await fetch(`${API_BASE}/regex/group`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ files, pattern, field })
  })
  return res.json()
}

export async function validateRegex(pattern) {
  const res = await fetch(`${API_BASE}/regex/validate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ pattern })
  })
  return res.json()
}

function transformRuleForBackend(rule) {
  // Frontend uses `type`, backend uses `rule_type`
  const backend = { ...rule }
  if (backend.type) {
    backend.rule_type = backend.type
    delete backend.type
  }
  // Frontend uses `position` for sequence location, backend uses `sequence_position`
  if (backend.rule_type === 'sequence' && backend.position && !backend.sequence_position) {
    backend.sequence_position = backend.position
    delete backend.position
  }
  // Remove frontend-only fields
  delete backend.id
  delete backend.enabled
  return { ...backend, enabled: rule.enabled !== false }
}

export async function previewRename(files, rules, regexPattern) {
  const backendRules = rules.map(transformRuleForBackend)
  const res = await fetch(`${API_BASE}/rename/preview`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ files, rules: backendRules, regex_pattern: regexPattern })
  })
  return res.json()
}

export async function executeRename(operations) {
  const res = await fetch(`${API_BASE}/rename/execute`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ operations })
  })
  return res.json()
}

export async function undoRename(batchId) {
  const res = await fetch(`${API_BASE}/rename/undo/${batchId}`, { method: 'POST' })
  return res.json()
}

export async function getHistory() {
  const res = await fetch(`${API_BASE}/rename/history`)
  return res.json()
}

export async function getFavorites() {
  const res = await fetch(`${API_BASE}/favorites`)
  const data = await res.json()
  return Array.isArray(data) ? { favorites: data } : data
}

export async function addFavorite(data) {
  const res = await fetch(`${API_BASE}/favorites`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  })
  return res.json()
}

export async function updateFavorite(id, data) {
  const res = await fetch(`${API_BASE}/favorites/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  })
  return res.json()
}

export async function deleteFavorite(id) {
  const res = await fetch(`${API_BASE}/favorites/${id}`, { method: 'DELETE' })
  return res.json()
}

export async function getLogs(params = {}) {
  const query = new URLSearchParams(params).toString()
  const res = await fetch(`${API_BASE}/logs?${query}`)
  return res.json()
}

export async function clearLogs() {
  const res = await fetch(`${API_BASE}/logs`, { method: 'DELETE' })
  return res.json()
}

export async function exportData(type, data, format) {
  const res = await fetch(`${API_BASE}/export`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ type, data, format })
  })
  return res.json()
}

export async function getSettings() {
  const res = await fetch(`${API_BASE}/settings`)
  return res.json()
}

export async function updateSettings(data) {
  const res = await fetch(`${API_BASE}/settings`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  })
  return res.json()
}

export async function openFile(filePath, openWith) {
  const res = await fetch(`${API_BASE}/open/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ file_path: filePath, open_with: openWith || '' })
  })
  return res.json()
}
