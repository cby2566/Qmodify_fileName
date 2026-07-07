<template>
  <div class="settings-panel">
    <el-form :model="settingsStore.settings" label-width="140px">
      <el-form-item label="目标扩展名">
        <el-select-v2
          v-model="settingsStore.settings.target_extensions"
          multiple
          placeholder="选择扩展名"
          :options="extensionOptions"
          allow-create
          filterable
        />
      </el-form-item>
      <el-form-item label="默认递归扫描">
        <el-switch v-model="settingsStore.settings.default_recursive" />
      </el-form-item>
      <el-form-item label="最大扫描深度">
        <el-input-number v-model="settingsStore.settings.max_scan_depth" :min="1" :max="10" />
      </el-form-item>
      <el-form-item label="日志保留天数">
        <el-input-number v-model="settingsStore.settings.log_retention_days" :min="1" :max="365" />
      </el-form-item>
      <el-form-item label="打开方式">
        <el-input
          v-model="settingsStore.settings.open_with"
          placeholder="留空使用系统默认，填写程序路径如 C:\Program Files\...\app.exe"
          clearable
        />
      </el-form-item>
      <el-form-item label="预览防抖(ms)">
        <el-input-number v-model="settingsStore.settings.preview_debounce_ms" :min="100" :max="2000" />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="saveSettings">保存设置</el-button>
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useSettingsStore } from '../stores/settings'
import { ElMessage } from 'element-plus'

const settingsStore = useSettingsStore()

const extensionOptions = [
  { value: '.zip', label: '.zip' },
  { value: '.rar', label: '.rar' },
  { value: '.7z', label: '.7z' },
  { value: '.tar', label: '.tar' },
  { value: '.gz', label: '.gz' },
  { value: '.bz2', label: '.bz2' },
  { value: '.xz', label: '.xz' },
  { value: '.tar.gz', label: '.tar.gz' },
  { value: '.tar.bz2', label: '.tar.bz2' },
  { value: '.tar.xz', label: '.tar.xz' }
]

async function saveSettings() {
  await settingsStore.save(settingsStore.settings)
  ElMessage.success('设置已保存')
}

onMounted(() => {
  settingsStore.fetch()
})
</script>

<style scoped>
.settings-panel { padding: 20px; }
</style>
