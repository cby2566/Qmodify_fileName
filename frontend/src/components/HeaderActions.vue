<template>
  <div class="header-actions">
    <el-autocomplete
      v-model="pathInput"
      :fetch-suggestions="queryHistory"
      placeholder="输入目录路径，如 D:\Downloads"
      style="width: 320px"
      clearable
      @keyup.enter="scanPath"
      @select="pathInput = $event.value"
    />
    <el-button type="primary" @click="scanPath" :loading="fileStore.loading">
      <el-icon><FolderOpened /></el-icon>
      扫描
    </el-button>
    <el-button @click="pickDirectory">
      <el-icon><Folder /></el-icon>
      浏览
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
import { Folder, FolderOpened, Document, Star, Setting } from '@element-plus/icons-vue'
import { useFileStore } from '../stores/files'
import { useSettingsStore } from '../stores/settings'
import { ElMessage } from 'element-plus'
import { getScanHistory, addScanHistory } from '../utils'

const emit = defineEmits(['showLogs', 'showFavorites', 'showSettings'])
const fileStore = useFileStore()
const settingsStore = useSettingsStore()
const pathInput = ref('')

function queryHistory(queryString, cb) {
  const history = getScanHistory()
  const results = queryString
    ? history.filter(p => p.toLowerCase().includes(queryString.toLowerCase()))
    : history
  cb(results.map(value => ({ value })))
}

async function scanPath() {
  if (!pathInput.value.trim()) {
    ElMessage.warning('请输入目录路径')
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

async function pickDirectory() {
  if ('showDirectoryPicker' in window) {
    try {
      const handle = await window.showDirectoryPicker()
      pathInput.value = handle.name
      // 注意：浏览器安全限制，showDirectoryPicker 返回的是 handle，不是路径
      // 这里需要用户手动输入完整路径
      ElMessage.info('由于浏览器安全限制，请手动输入完整路径后点击扫描')
    } catch (e) {
      // 用户取消
    }
  } else {
    ElMessage.warning('当前浏览器不支持目录选择，请手动输入路径')
  }
}
</script>

<style scoped>
.header-actions { display: flex; gap: 8px; align-items: center; }
</style>
