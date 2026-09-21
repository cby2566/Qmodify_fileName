import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { scanDirectory, filterFiles } from '../api'
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

  function syncRenamedFiles(results) {
    for (const result of results) {
      if (result.status !== 'success') continue
      const oldPath = result.original_path
      const newPath = result.new_path
      const newFilename = basename(newPath)
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
    scan, applyFilters, syncRenamedFiles, toggleFile, removeFilesByPaths
  }
})
