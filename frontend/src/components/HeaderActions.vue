<template>
  <div class="header-actions">
    <div class="path-input-wrap">
      <el-autocomplete
        v-model="pathInput"
        :fetch-suggestions="queryPaths"
        placeholder="输入目录路径，如 D:\Downloads"
        class="path-input"
        clearable
        :trigger-on-focus="true"
        @keyup.enter="scanPath"
        @select="handlePathSelect"
        @blur="validatePathInput"
      >
        <template #default="{ item }">
          <div class="path-option">
            <span class="path-option-label">{{ item.label }}</span>
            <span class="path-option-value">{{ item.value }}</span>
          </div>
        </template>
      </el-autocomplete>
      <span v-if="pathStatus.message" class="path-status" :class="pathStatus.type">
        {{ pathStatus.message }}
      </span>
    </div>
    <el-button type="primary" @click="scanPath" :loading="fileStore.loading">
      <el-icon><FolderOpened /></el-icon>
      扫描
    </el-button>
    <el-divider direction="vertical" />
    <el-button @click="$emit('showLogs')">
      <el-icon><Document /></el-icon>
      日志
    </el-button>
    <el-button @click="$emit('showFavorites')">
      <el-icon><Star /></el-icon>
      收藏夹
    </el-button>
    <el-button @click="$emit('showSettings')">
      <el-icon><Setting /></el-icon>
      设置
    </el-button>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { FolderOpened, Document, Star, Setting } from '@element-plus/icons-vue'
import { useFileStore } from '../stores/files'
import { useSettingsStore } from '../stores/settings'
import { ElMessage } from 'element-plus'
import { getCommonDirectories, getPathSuggestions, validateDirectory } from '../api'
import { getScanHistory, addScanHistory } from '../utils'

const emit = defineEmits(['showLogs', 'showFavorites', 'showSettings'])
const fileStore = useFileStore()
const settingsStore = useSettingsStore()
const pathInput = ref('')
const commonDirectories = ref([])
const pathStatus = ref({ type: '', message: '' })

function formatSuggestion(value, label, kind) {
  return {
    value,
    label: label || value,
    kind
  }
}

function historySuggestions(queryString) {
  const query = queryString.toLowerCase()
  return getScanHistory()
    .filter(p => !query || p.toLowerCase().includes(query))
    .map(path => formatSuggestion(path, '历史记录', 'history'))
}

async function queryPaths(queryString, cb) {
  const history = historySuggestions(queryString)
  try {
    const { suggestions = [] } = await getPathSuggestions(queryString, 12)
    const merged = [...history, ...suggestions]
    const seen = new Set()
    cb(merged.filter(item => {
      const key = item.value.toLowerCase()
      if (seen.has(key)) return false
      seen.add(key)
      return true
    }))
  } catch {
    const shortcuts = commonDirectories.value
      .filter(item => !queryString || item.path.toLowerCase().includes(queryString.toLowerCase()))
      .map(item => formatSuggestion(item.path, item.label, item.kind))
    cb([...history, ...shortcuts])
  }
}

function handlePathSelect(item) {
  pathInput.value = item.value
  validatePathInput()
}

async function validatePathInput() {
  const path = pathInput.value.trim()
  if (!path) {
    pathStatus.value = { type: '', message: '' }
    return false
  }
  try {
    const result = await validateDirectory(path)
    pathStatus.value = {
      type: result.exists && result.is_directory ? 'valid' : 'invalid',
      message: result.message
    }
    if (result.path) pathInput.value = result.path
    return result.exists && result.is_directory
  } catch {
    pathStatus.value = { type: 'invalid', message: '无法校验目录' }
    return false
  }
}

async function scanPath() {
  if (!pathInput.value.trim()) {
    ElMessage.warning('请输入目录路径')
    return
  }
  const valid = await validatePathInput()
  if (!valid) {
    ElMessage.warning(pathStatus.value.message || '目录不可用')
    return
  }
  const exts = settingsStore.settings.target_extensions
  const recursive = settingsStore.settings.default_recursive
  const maxDepth = settingsStore.settings.max_scan_depth
  await fileStore.scan(pathInput.value.trim(), exts, recursive, maxDepth)
  addScanHistory(pathInput.value.trim())
  console.log(fileStore.files)
  ElMessage.success(`已扫描 ${fileStore.files.length} 个文件`)
}

onMounted(async () => {
  try {
    const { directories = [] } = await getCommonDirectories()
    commonDirectories.value = directories
  } catch {
    commonDirectories.value = []
  }
})
</script>

<style scoped>
.header-actions {
  display: flex;
  flex: 1;
  gap: 8px;
  align-items: center;
  justify-content: flex-end;
  min-width: 0;
}
.path-input-wrap {
  display: flex;
  flex-direction: column;
  gap: 3px;
  flex: 1 1 560px;
  min-width: 420px;
  max-width: 760px;
}
.path-input {
  width: 100%;
}
.path-status {
  font-size: 12px;
  line-height: 14px;
}
.path-status.valid {
  color: #529b2e;
}
.path-status.invalid {
  color: #c45656;
}
.path-option {
  display: grid;
  gap: 2px;
  line-height: 1.3;
  padding: 3px 0;
}
.path-option-label {
  font-size: 12px;
  color: #606266;
}
.path-option-value {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

@media (max-width: 1100px) {
  .header-actions {
    flex-wrap: wrap;
  }

  .path-input-wrap {
    flex-basis: 100%;
    max-width: none;
  }
}
</style>
