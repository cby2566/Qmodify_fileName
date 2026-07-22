<template>
  <div class="toolbar">
    <div class="toolbar-row">
      <el-select v-model="filterExtensions" multiple placeholder="扩展名" style="width: 200px" @change="applyFilters">
        <el-option v-for="ext in availableExtensions" :key="ext" :label="ext" :value="ext" />
      </el-select>
      <el-input v-model="filterKeyword" placeholder="文件名关键词" style="width: 180px" clearable @input="onKeywordInput" />
      <el-select v-model="filterMode" style="width: 80px" @change="applyFilters">
        <el-option label="包含" value="include" />
        <el-option label="排除" value="exclude" />
      </el-select>
      <el-button type="danger" plain @click="removeSelected" :disabled="!fileStore.selectedFiles.length">
        <el-icon><Delete /></el-icon>
        移除已选({{ fileStore.selectedFiles.length }})
      </el-button>
      <el-button type="info" @click="resetSelectedPreviews" :disabled="!hasSelectedPreviews">
        <el-icon><RefreshLeft /></el-icon>
        撤销预览({{ selectedPreviewCount }})
      </el-button>
      <el-divider direction="vertical" />
      <el-button type="success" @click="generatePreview" :disabled="!renameStore.rules.length">
        <el-icon><Refresh /></el-icon>
        刷新预览
      </el-button>
      <el-button type="danger" @click="executeRename" :disabled="renameStore.stats.toRename === 0">
        <el-icon><Check /></el-icon>
        执行重命名 ({{ renameStore.stats.toRename }})
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { Refresh, RefreshLeft, Check, Delete } from '@element-plus/icons-vue'
import { useFileStore } from '../stores/files'
import { useRenameStore } from '../stores/rename'
import { useSettingsStore } from '../stores/settings'
import { debounce } from '../utils'
import { ElMessage, ElMessageBox } from 'element-plus'

const fileStore = useFileStore()
const renameStore = useRenameStore()
const settingsStore = useSettingsStore()

const filterExtensions = ref([])
const filterKeyword = ref('')
const filterMode = ref('include')

const availableExtensions = computed(() => {
  const exts = new Set(fileStore.files.map(f => f.extension))
  return Array.from(exts).sort()
})

const selectedPreviewCount = computed(() => {
  return fileStore.selectedFiles.filter(f =>
    renameStore.previewResults.some(r => r.original_path === f.full_path)
  ).length
})

const hasSelectedPreviews = computed(() => selectedPreviewCount.value > 0)

const onKeywordInput = debounce(() => {
  applyFilters()
}, 300)

function applyFilters() {
  fileStore.applyFilters({
    extensions: filterExtensions.value,
    keywordInclude: filterMode.value === 'include' ? filterKeyword.value : '',
    keywordExclude: filterMode.value === 'exclude' ? filterKeyword.value : ''
  })
}

async function generatePreview() {
  try {
    await renameStore.generatePreview(fileStore.selectedFiles)
    ElMessage.success('预览生成完成，共 ' + renameStore.stats.total + ' 个文件')
  } catch (e) {
    ElMessage.error(e?.message || String(e))
  }
}

async function resetSelectedPreviews() {
  const selectedWithPreview = fileStore.selectedFiles.filter(f =>
    renameStore.previewResults.some(r => r.original_path === f.full_path)
  )

  if (!selectedWithPreview.length) return

  try {
    await ElMessageBox.confirm(
      '确定要撤销已选的 ' + selectedWithPreview.length + ' 个文件的预览修改吗？此操作不可恢复。',
      '确认批量撤销',
      {
        confirmButtonText: '撤销',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    const filePaths = selectedWithPreview.map(f => f.full_path)
    renameStore.resetPreviews(filePaths)
    ElMessage.success('已撤销 ' + selectedWithPreview.length + ' 个文件的预览修改')
  } catch (e) {
    if (e !== 'cancel' && e !== 'close') {
      ElMessage.error(e?.message || String(e))
    }
  }
}

async function removeSelected() {
  const count = fileStore.selectedFiles.length
  if (!count) return
  try {
    await ElMessageBox.confirm(
      '确定要从列表中移除已选的 ' + count + ' 个文件吗？此操作不会删除磁盘文件。',
      '确认批量移除',
      { confirmButtonText: '移除', cancelButtonText: '取消', type: 'warning' }
    )
    fileStore.removeFilesByPaths(fileStore.selectedFiles.map(f => f.full_path))
    ElMessage.success('已从列表中移除 ' + count + ' 个文件')
  } catch (e) {
    if (e !== 'cancel' && e !== 'close') {
      ElMessage.error(e?.message || String(e))
    }
  }
}


async function executeRename() {
  if (renameStore.stats.conflicts > 0) {
    ElMessage.warning('存在 ' + renameStore.stats.conflicts + ' 个冲突，请先解决')
    return
  }
  try {
    await ElMessageBox.confirm(
      '确定要重命名 ' + renameStore.stats.toRename + ' 个文件吗？此操作可撤销。',
      '确认重命名',
      { type: 'warning' }
    )
    const result = await renameStore.execute()
    if (result.results) {
      fileStore.syncRenamedFiles(result.results)
    }
    if (result.failed > 0) {
      ElMessage.error('成功: ' + result.succeeded + ', 失败: ' + result.failed)
    } else {
      ElMessage.success('成功: ' + result.succeeded + ', 失败: ' + result.failed)
    }
  } catch (e) {
    if (e !== 'cancel' && e !== 'close') {
      ElMessage.error(e?.message || String(e))
    }
  }
}

onMounted(() => {
  settingsStore.fetch()
})
</script>

<style scoped>
.toolbar { padding: 12px 16px; background: #fafafa; border-bottom: 1px solid #e4e7ed; }
.toolbar-row { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
</style>
