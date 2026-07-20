export function computeFilenameDiff(originalName, newName) {
  if (!originalName || !newName) {
    return [{ text: newName || '', type: 'unchanged' }]
  }
  if (originalName === newName) {
    return [{ text: newName, type: 'unchanged' }]
  }

  const m = originalName.length
  const n = newName.length

  // Build LCS DP table
  const dp = Array.from({ length: m + 1 }, () => Array(n + 1).fill(0))
  for (let i = 1; i <= m; i++) {
    for (let j = 1; j <= n; j++) {
      if (originalName[i - 1] === newName[j - 1]) {
        dp[i][j] = dp[i - 1][j - 1] + 1
      } else {
        dp[i][j] = Math.max(dp[i - 1][j], dp[i][j - 1])
      }
    }
  }

  // Backtrack to produce diff operations
  const ops = []
  let i = m
  let j = n
  while (i > 0 || j > 0) {
    if (i > 0 && j > 0 && originalName[i - 1] === newName[j - 1]) {
      ops.unshift({ type: 'unchanged', char: originalName[i - 1] })
      i--
      j--
    } else if (j > 0 && (i === 0 || dp[i][j - 1] >= dp[i - 1][j])) {
      ops.unshift({ type: 'added', char: newName[j - 1] })
      j--
    } else if (i > 0) {
      ops.unshift({ type: 'removed', char: originalName[i - 1] })
      i--
    }
  }

  // Merge consecutive same-type operations into segments
  const segments = []
  let cur = null
  for (const op of ops) {
    if (cur && cur.type === op.type) {
      cur.text += op.char
    } else {
      if (cur) segments.push(cur)
      cur = { type: op.type, text: op.char }
    }
  }
  if (cur) segments.push(cur)

  // Refine: an 'added' segment that immediately follows a 'removed' segment is a genuine
  // replacement (modified). This covers both mid-text replacements (surrounded by unchanged)
  // and full-text replacements (no unchanged neighbors), ensuring replace rules render as orange.
  for (let k = 0; k < segments.length; k++) {
    if (segments[k].type === 'added' && k > 0 && segments[k - 1].type === 'removed') {
      segments[k].type = 'modified'
    }
  }

  // Remove 'removed' segments — we only display the new name
  return segments.filter(s => s.type !== 'removed')
}

export function formatSize(bytes) {
  if (bytes === 0) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(1024))
  const value = bytes / Math.pow(1024, i)
  return `${value.toFixed(i > 0 ? 1 : 0)} ${units[i]}`
}

export function debounce(fn, delay = 300) {
  let timer = null
  return function (...args) {
    clearTimeout(timer)
    timer = setTimeout(() => fn.apply(this, args), delay)
  }
}

export function downloadFile(content, filename, mimeType = 'text/plain;charset=utf-8') {
  const blob = new Blob([content], { type: mimeType })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

const SCAN_HISTORY_KEY = 'scan_path_history'
const MAX_HISTORY = 20

export function getScanHistory() {
  try {
    const raw = localStorage.getItem(SCAN_HISTORY_KEY)
    return raw ? JSON.parse(raw) : []
  } catch {
    return []
  }
}

export function addScanHistory(path) {
  if (!path) return
  let history = getScanHistory()
  history = history.filter(p => p !== path)
  history.unshift(path)
  if (history.length > MAX_HISTORY) history = history.slice(0, MAX_HISTORY)
  localStorage.setItem(SCAN_HISTORY_KEY, JSON.stringify(history))
}

export function removeScanHistory(path) {
  let history = getScanHistory().filter(p => p !== path)
  localStorage.setItem(SCAN_HISTORY_KEY, JSON.stringify(history))
}

export function clearScanHistory() {
  localStorage.removeItem(SCAN_HISTORY_KEY)
}
