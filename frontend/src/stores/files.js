import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { scanDirectory, filterFiles, calculateDirSizes } from '../api'
import { useRenameStore } from './rename'

function basename(p) {
  const idx = p.replace(/\\/g, '/').lastIndexOf('/')
  return idx >= 0 ? p.substring(idx + 1) : p
}

function extname(p) {
  const name = basename(p)
  const dot = name.lastIndexOf('.')
  return dot > 0 ? name.substring(dot) : ''
}

export const useFileStore = defineStore('files', () => {
  const files = ref([])
  const filteredFiles = ref([])
  const selectedFiles = ref([])
  const currentPath = ref('')
  // "file" | "dir" | "all" — mirrors the backend target_type parameter.
  const targetType = ref('file')
  const loading = ref(false)
  const filters = ref({
    extensions: [],
    sizeMin: null,
    sizeMax: null,
    dateFrom: null,
    dateTo: null,
    regex: '',
    keywordInclude: '',
    keywordExclude: ''
  })

  // Directories carry no meaningful size, so they never count towards totals.
  const totalSize = computed(() =>
    filteredFiles.value.reduce((sum, f) => sum + (f.is_dir ? 0 : f.size_bytes || 0), 0)
  )

  const selectedSize = computed(() =>
    selectedFiles.value.reduce((sum, f) => sum + (f.is_dir ? 0 : f.size_bytes || 0), 0)
  )

  const dirCount = computed(() => filteredFiles.value.filter(f => f.is_dir).length)

  async function scan(path, extensions, recursive, maxDepth, target) {
    loading.value = true
    currentPath.value = path
    if (target) targetType.value = target
    try {
      const res = await scanDirectory(path, extensions, recursive, maxDepth, targetType.value)
      files.value = res.files || []
      filteredFiles.value = [...files.value]
      selectedFiles.value = []
      // A new scan invalidates every previously measured directory.
      dirSizeCache.value = {}
      useRenameStore().previewResults = []
    } finally {
      loading.value = false
    }
  }

  async function applyFilters(newFilters) {
    filters.value = { ...filters.value, ...newFilters }
    loading.value = true
    try {
      const res = await filterFiles({
        files: files.value,
        filters: filters.value
      })
      filteredFiles.value = res.files || []
    } finally {
      loading.value = false
    }
  }

  // Directory sizes are measured on demand and cached per path. The cache is a
  // record of a past measurement, never a claim that the value is current: a
  // folder's contents can change at any moment, so every click re-measures.
  // Each entry carries the timestamp of its measurement so the UI can show age.
  const dirSizeCache = ref({})
  const calculatingSize = ref(false)

  // Measure the given paths, always overwriting previous values.
  // `onlyPending` keeps the old behaviour of skipping already-measured paths.
  async function calculateSizes(paths, { onlyPending = false } = {}) {
    const targets = onlyPending
      ? paths.filter(p => dirSizeCache.value[p] === undefined)
      : [...paths]
    if (!targets.length) return { measured: 0, total: paths.length, failed: 0 }

    calculatingSize.value = true
    try {
      const res = await calculateDirSizes(targets)
      const results = res.results || []
      const next = { ...dirSizeCache.value }
      const byPath = new Map(files.value.map(f => [f.full_path, f]))
      const measuredAt = Date.now()
      let ok = 0
      let failed = 0
      for (const r of results) {
        if (!r.success) {
          failed += 1
          next[r.path] = { error: r.error || '计算失败', measured_at: measuredAt }
          continue
        }
        ok += 1
        next[r.path] = {
          size_bytes: r.size_bytes,
          size_display: r.size_display,
          file_count: r.file_count,
          truncated: r.truncated,
          measured_at: measuredAt
        }
        // Keep the row itself in sync so sorting and detail dialogs agree.
        const entry = byPath.get(r.path)
        if (entry) {
          entry.size_bytes = r.size_bytes
          entry.size_display = r.size_display
        }
      }
      dirSizeCache.value = next
      return { measured: ok, total: paths.length, failed }
    } finally {
      calculatingSize.value = false
    }
  }

  function sizeOf(fullPath) {
    return dirSizeCache.value[fullPath]
  }

  // When the given paths were measured. Returns null if none were, and the
  // OLDEST measurement time otherwise — the honest "how stale could this be"
  // answer when a page mixes freshly measured and long-cached folders.
  function lastMeasuredAt(paths) {
    let oldest = null
    for (const p of paths) {
      const at = dirSizeCache.value[p]?.measured_at
      if (typeof at !== 'number') continue
      if (oldest === null || at < oldest) oldest = at
    }
    return oldest
  }

  function clearDirSizeCache() {
    dirSizeCache.value = {}
  }

  function syncRenamedFiles(results) {
    let cacheChanged = false
    const nextCache = { ...dirSizeCache.value }
    for (const result of results) {
      if (result.status !== 'success') continue
      const oldPath = result.original_path
      const newPath = result.new_path
      const newFilename = basename(newPath)
      // A measured size belongs to a path, so a rename either moves the entry
      // with it (contents identical) or leaves a value under a path that no
      // longer exists. Renaming the folder itself keeps the measurement valid.
      if (nextCache[oldPath] !== undefined) {
        nextCache[newPath] = nextCache[oldPath]
        delete nextCache[oldPath]
        cacheChanged = true
      }
      for (const arr of [files.value, filteredFiles.value]) {
        const idx = arr.findIndex(f => f.full_path === oldPath)
        if (idx >= 0) {
          const entry = arr[idx]
          arr[idx] = {
            ...entry,
            full_path: newPath,
            filename: newFilename,
            // A directory has no extension; its "stem" is the whole name.
            extension: entry.is_dir ? '' : extname(newPath),
            stem: entry.is_dir ? newFilename : newFilename.replace(/\.[^.]*$/, '')
          }
        }
      }
      const selIdx = selectedFiles.value.findIndex(f => f.full_path === oldPath)
      if (selIdx >= 0) {
        const entry = selectedFiles.value[selIdx]
        selectedFiles.value[selIdx] = {
          ...entry,
          full_path: newPath,
          filename: newFilename,
          extension: entry.is_dir ? '' : extname(newPath),
          stem: entry.is_dir ? newFilename : newFilename.replace(/\.[^.]*$/, '')
        }
      }
    }
    if (cacheChanged) dirSizeCache.value = nextCache
  }

  function toggleFile(file) {
    const idx = selectedFiles.value.findIndex(f => f.full_path === file.full_path)
    if (idx >= 0) {
      selectedFiles.value.splice(idx, 1)
    } else {
      selectedFiles.value.push(file)
    }
  }

  function removeFilesByPaths(paths) {
    const pathSet = new Set(paths)
    files.value = files.value.filter(f => !pathSet.has(f.full_path))
    filteredFiles.value = filteredFiles.value.filter(f => !pathSet.has(f.full_path))
    selectedFiles.value = selectedFiles.value.filter(f => !pathSet.has(f.full_path))
    const renameStore = useRenameStore()
    renameStore.previewResults = renameStore.previewResults.filter(
      r => !pathSet.has(r.original_path) && !pathSet.has(r.new_path)
    )
  }

  return {
    files, filteredFiles, selectedFiles, currentPath, targetType, loading, filters,
    totalSize, selectedSize, dirCount,
    dirSizeCache, calculatingSize,
    scan, applyFilters, syncRenamedFiles, toggleFile, removeFilesByPaths,
    calculateSizes, sizeOf, lastMeasuredAt, clearDirSizeCache
  }
})
