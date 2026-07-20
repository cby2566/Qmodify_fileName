import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getSettings, updateSettings } from '../api'

export const useSettingsStore = defineStore('settings', () => {
  const settings = ref({
    available_extensions: ['.txt', '.zip', '.rar', '.7z'],
    target_extensions: ['.txt', '.zip', '.rar', '.7z'],
    default_recursive: false,
    max_scan_depth: 3,
    log_retention_days: 90,
    preview_debounce_ms: 300,
    open_with: "",
    quick_add_text: '_new',
    quick_add_mode: 'prefix'
  })
  const loading = ref(false)

  async function fetch() {
    loading.value = true
    try {
      const res = await getSettings()
      settings.value = { ...settings.value, ...res }
    } finally {
      loading.value = false
    }
  }

  async function save(data) {
    const res = await updateSettings(data)
    settings.value = { ...settings.value, ...res }
  }

  return { settings, loading, fetch, save }
})
