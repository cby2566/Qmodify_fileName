import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { scanDirectory, filterFiles } from '../api'

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

  const totalSize = computed(() =>
    filteredFiles.value.reduce((sum, f) => sum + f.size_bytes, 0)
  )

  const selectedSize = computed(() =>
    selectedFiles.value.reduce((sum, f) => sum + f.size_bytes, 0)
  )

  async function scan(path, extensions, recursive, maxDepth) {
    loading.value = true
    currentPath.value = path
    try {
      const res = await scanDirectory(path, extensions, recursive, maxDepth)
      files.value = res.files || []
      filteredFiles.value = [...files.value]
      selectedFiles.value = []
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
      const newExtension = extname(newPath)
      for (const arr of [files.value, filteredFiles.value]) {
        const idx = arr.findIndex(f => f.full_path === oldPath)
        if (idx >= 0) {
          arr[idx] = {
            ...arr[idx],
            full_path: newPath,
            filename: newFilename,
            extension: newExtension
          }
        }
      }
      const selIdx = selectedFiles.value.findIndex(f => f.full_path === oldPath)
      if (selIdx >= 0) {
        selectedFiles.value[selIdx] = {
          ...selectedFiles.value[selIdx],
          full_path: newPath,
          filename: newFilename,
          extension: newExtension
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
  }

  return {
    files, filteredFiles, selectedFiles, currentPath, loading, filters,
    totalSize, selectedSize,
    scan, applyFilters, syncRenamedFiles, toggleFile, removeFilesByPaths
  }
})
