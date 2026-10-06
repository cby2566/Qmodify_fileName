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

  // Merge consecutive same-type entries into segments
  function mergeSegments(list) {
    const merged = []
    let cur = null
    for (const item of list) {
      if (cur && cur.type === item.type) {
        cur.text += item.text
      } else {
        if (cur) merged.push(cur)
        cur = { type: item.type, text: item.text }
      }
    }
    if (cur) merged.push(cur)
    return merged
  }

  let segments = mergeSegments(ops.map(op => ({ type: op.type, text: op.char })))

  // Absorb short 'unchanged' islands inside a changed region: an unchanged segment
  // of <= 2 chars with a change on both sides (at least one of them 'added') is
  // folded into the change. This prevents coincidental single-char LCS anchors
  // (e.g. the "1" shared by "1080p" and a replacement text) from fragmenting one
  // logical replacement into misleading pieces.
  const ISLAND_MAX_LEN = 2
  for (let k = 1; k < segments.length - 1; k++) {
    if (segments[k].type !== 'unchanged' || segments[k].text.length > ISLAND_MAX_LEN) continue
    const prevType = segments[k - 1].type
    const nextType = segments[k + 1].type
    if (prevType === 'unchanged' || nextType === 'unchanged') continue
    if (prevType !== 'added' && nextType !== 'added') continue
    segments[k].type = 'added'
  }
  segments = mergeSegments(segments)

  // Refine: an 'added' segment that immediately follows a 'removed' segment may contain both
  // a prefix/suffix addition and a genuine replacement. Scan from both ends to separate them:
  //   - Leading chars in a different character block → prefix (added)
  //   - Trailing chars in a different character block → suffix (added)
  //   - Middle chars in the same block → replacement (modified)
  function charBlock(ch) {
    const c = ch.charCodeAt(0)
    if (c >= 0x4E00 && c <= 0x9FFF) return 'cjk'
    if (c >= 0x3040 && c <= 0x309F) return 'hiragana'
    if (c >= 0x30A0 && c <= 0x30FF) return 'katakana'
    if (c >= 0xAC00 && c <= 0xD7AF) return 'hangul'
    if (c >= 0x0020 && c <= 0x007E) return 'ascii'
    return 'other'
  }

  for (let k = 0; k < segments.length; k++) {
    if (segments[k].type === 'added' && k > 0 && segments[k - 1].type === 'removed') {
      const removedText = segments[k - 1].text
      const addedText = segments[k].text
      const removedBlock = charBlock(removedText[0])

      if (addedText.length > removedText.length) {
        // Scan from the LEFT for a distinguishable prefix
        let prefixEnd = 0
        for (let i = 0; i < addedText.length; i++) {
          if (charBlock(addedText[i]) !== removedBlock) {
            prefixEnd = i + 1
          } else {
            break
          }
        }

        // Scan from the RIGHT for a distinguishable suffix
        let suffixStart = addedText.length
        for (let i = addedText.length - 1; i >= 0; i--) {
          if (charBlock(addedText[i]) !== removedBlock) {
            suffixStart = i
          } else {
            break
          }
        }

        const prefix = addedText.slice(0, prefixEnd)
        const suffix = addedText.slice(suffixStart)
        const replacement = addedText.slice(prefixEnd, suffixStart)

        if (prefix || suffix) {
          if (replacement.length > 0) {
            // Replace current segment with the middle (replacement) part
            segments[k].text = replacement
            segments[k].type = 'modified'

            if (prefix) {
              segments.splice(k, 0, { type: 'added', text: prefix })
            }
            if (suffix) {
              // After prefix splice, modified shifts to k+1; without prefix, it stays at k
              const modifiedIdx = prefix ? k + 1 : k
              segments.splice(modifiedIdx + 1, 0, { type: 'added', text: suffix })
            }
          }
          // else: replacement is empty (entire added is prefix+suffix with no middle),
          //       keep the segment as 'added' with the full text — no split needed.
          continue
        }
      }
      // No distinguishable prefix/suffix. If the added text is longer than the
      // removed text, it is mostly a net insertion — keep it as 'added'. Marking
      // it 'modified' was misleading: with removed text hidden, a pure addition
      // (e.g. an appended suffix) looked like an in-place modification.
      // Only same-size or shorter text is treated as a genuine replacement.
      if (addedText.length <= removedText.length) {
        segments[k].type = 'modified'
      }
    }
  }

  // Remove 'removed' segments — we only display the new name — then merge again,
  // since dropping a removed segment can leave two adjacent 'added' segments.
  return mergeSegments(segments.filter(s => s.type !== 'removed'))
}

// Map a backend rule type (plan-C span) to a display segment type.
const SPAN_TYPE_MAP = {
  add_prefix: 'added',
  add_suffix: 'added',
  insert_text: 'added',
  sequence: 'added',
  find_replace: 'modified',
  template: 'modified',
  case_transform: 'modified',
}

/**
 * Build display segments from backend-provided rule spans (provenance from the
 * rename engine — exact by construction). Returns null when the spans are
 * malformed so callers can fall back to computeFilenameDiff.
 */
export function segmentsFromSpans(newName, spans) {
  if (typeof newName !== 'string' || !Array.isArray(spans)) return null
  const sorted = [...spans].sort((a, b) => a.start - b.start)
  const segments = []
  let pos = 0
  for (const span of sorted) {
    const { start, end, type } = span
    if (!Number.isInteger(start) || !Number.isInteger(end)) return null
    if (start < pos || start >= end || end > newName.length) return null
    if (start > pos) segments.push({ text: newName.slice(pos, start), type: 'unchanged' })
    segments.push({ text: newName.slice(start, end), type: SPAN_TYPE_MAP[type] || 'added' })
    pos = end
  }
  if (pos < newName.length) segments.push({ text: newName.slice(pos), type: 'unchanged' })
  if (segments.length === 0) segments.push({ text: newName, type: 'unchanged' })
  return segments
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
