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
