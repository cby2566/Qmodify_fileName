import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { previewRename, executeRename, undoRename, getHistory } from '../api'
import { useSettingsStore } from './settings'
import { useFileStore } from './files'

export const useRenameStore = defineStore('rename', () => {
  const rules = ref([])
  const previewResults = ref([])
  const regexPattern = ref('')
  const history = ref([])
  const loading = ref(false)

  const stats = computed(() => {
    const total = previewResults.value.length
    const toRename = previewResults.value.filter(r => r.status === 'normal').length
    const conflicts = previewResults.value.filter(r => r.status === 'conflict').length
    const unchanged = previewResults.value.filter(r => r.status === 'unchanged').length
    const renamed = previewResults.value.filter(r => r.status === 'renamed').length
    return { total, toRename, conflicts, unchanged, renamed }
  })

  function addRule(rule) {
    rules.value.push({ ...rule, enabled: true, id: Date.now().toString() })
  }

  function removeRule(id) {
    rules.value = rules.value.filter(r => r.id !== id)
  }

  function updateRule(id, updates) {
    const idx = rules.value.findIndex(r => r.id === id)
    if (idx >= 0) {
      rules.value[idx] = { ...rules.value[idx], ...updates }
    }
  }

  function toggleRule(id) {
    const rule = rules.value.find(r => r.id === id)
    if (rule) rule.enabled = !rule.enabled
  }

  function reorderRules(fromIdx, toIdx) {
    const [moved] = rules.value.splice(fromIdx, 1)
    rules.value.splice(toIdx, 0, moved)
  }

  async function generatePreview(files) {
    if (!files.length) {
      previewResults.value = []
      return
    }
    loading.value = true
    try {
      const filePaths = files.map(f => f.full_path)
      const res = await previewRename(filePaths, rules.value, regexPattern.value)
      previewResults.value = res || []
    } finally {
      loading.value = false
    }
  }

  async function execute() {
    const operations = previewResults.value
      .filter(r => r.status === 'normal')
      .map(r => ({ original_path: r.original_path, new_path: r.new_path }))
    if (!operations.length) return { success: 0, failed: 0, results: [] }
    const res = await executeRename(operations)
    const results = res.results || []
    for (const result of results) {
      if (result.status === 'success') {
        const idx = previewResults.value.findIndex(r => r.original_path === result.original_path)
        if (idx >= 0) {
          previewResults.value[idx].status = 'renamed'
        }
      }
    }
    return { success: res.succeeded, failed: res.failed, batch_id: res.batch_id, results }
  }

  async function fetchHistory() {
    const res = await getHistory()
    history.value = res.batches || []
  }

  async function undo(batchId) {
    return undoRename(batchId)
  }

  function applyQuickAdd(filePath) {
    const settingsStore = useSettingsStore()

    // Extract just the filename from the full path
    const lastSep = Math.max(filePath.lastIndexOf('\\'), filePath.lastIndexOf('/'))
    const fileName = lastSep >= 0 ? filePath.slice(lastSep + 1) : filePath

    // Rename rules operate on the stem for files, but on the whole name for
    // directories (which have no extension concept). Mirrors the backend
    // _split_name() helper.
    const entry = findEntryByPath(filePath)
    const isDir = !!entry?.is_dir

    let basename, extension
    if (isDir) {
      basename = fileName
      extension = ''
    } else {
      const lastDot = fileName.lastIndexOf('.')
      if (lastDot > 0) {
        basename = fileName.slice(0, lastDot)
        extension = fileName.slice(lastDot)
      } else {
        basename = fileName
        extension = ''
      }
    }

    const text = settingsStore.settings.quick_add_text || ''
    const mode = settingsStore.settings.quick_add_mode || 'prefix'
    let newFileNameOnly
    if (mode === 'prefix') {
      newFileNameOnly = text + basename + extension
    } else {
      newFileNameOnly = basename + text + extension
    }

    const lastSepIdx = Math.max(filePath.lastIndexOf('\\'), filePath.lastIndexOf('/'))
    const parentDir = lastSepIdx >= 0 ? filePath.slice(0, lastSepIdx) : ''
    const newFullPath = parentDir ? parentDir + filePath[lastSepIdx] + newFileNameOnly : newFileNameOnly

    const preview = {
      original_path: filePath,
      new_path: newFullPath,
      original_name: fileName,
      new_name: newFileNameOnly,
      is_dir: isDir,
      status: 'normal'
    }

    const idx = previewResults.value.findIndex(r => r.original_path === filePath)
    if (idx >= 0) {
      previewResults.value[idx] = { ...previewResults.value[idx], ...preview }
    } else {
      previewResults.value.push(preview)
    }
  }

  function findEntryByPath(fullPath) {
    const fileStore = useFileStore()
    const pools = [fileStore.files, fileStore.filteredFiles, fileStore.selectedFiles]
    for (const pool of pools) {
      const hit = pool?.find(f => f.full_path === fullPath)
      if (hit) return hit
    }
    return null
  }

  function resetPreview(filePath) {
    const idx = previewResults.value.findIndex(r => r.original_path === filePath)
    if (idx >= 0) {
      previewResults.value.splice(idx, 1)
    }
  }

  function resetPreviews(filePaths) {
    const pathSet = new Set(filePaths)
    previewResults.value = previewResults.value.filter(r => !pathSet.has(r.original_path))
  }

  return {
    rules, previewResults, regexPattern, history, loading, stats,
    addRule, removeRule, updateRule, toggleRule, reorderRules,
    generatePreview, execute, fetchHistory, undo, applyQuickAdd, resetPreview, resetPreviews
  }
})