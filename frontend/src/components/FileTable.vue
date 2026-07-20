<template>
  <div class="file-table-container">
    <el-table
      :data="paginatedFiles"
      :row-key="row => row.full_path"
      stripe
      height="100%"
      @selection-change="onSelectionChange"
      v-loading="fileStore.loading"
    >
      <el-table-column type="selection" width="50" :selectable="isSelectable" reserve-selection />
      <el-table-column prop="filename" label="当前文件名" min-width="250" show-overflow-tooltip />
      <el-table-column label="新文件名" min-width="250" show-overflow-tooltip>
        <template #default="{ row }">
          <span :class="getNewNameClass(row)">{{ getNewName(row) }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="size_display" label="大小" width="100" sortable />
      <el-table-column prop="extension" label="类型" width="70" />
      <el-table-column label="状态" width="90">
        <template #default="{ row }">
          <el-tag :type="getStatusType(row)" size="small">{{ getStatusText(row) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="250" fixed="right">
        <template #default="{ row }">
          <el-button type="warning" link size="small" @click="handleQuickAdd(row)">快速</el-button>
          <el-button type="primary" link size="small" @click="handleOpen(row)">
            {{ getOpenLabel(row) }}
          </el-button>
          <el-button type="danger" link size="small" @click="handleRemove(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>
    <div class="pagination">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[50, 100, 200, 500]"
        :total="fileStore.filteredFiles.length"
        layout="total, sizes, prev, pager, next"
        background
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useFileStore } from '../stores/files'
import { useRenameStore } from '../stores/rename'
import { useSettingsStore } from '../stores/settings'
import { openFile } from '../api'

const fileStore = useFileStore()
const renameStore = useRenameStore()
const openResults = ref({})

const currentPage = ref(1)
const pageSize = ref(100)

const paginatedFiles = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return fileStore.filteredFiles.slice(start, start + pageSize.value)
})

watch(
  () => fileStore.filteredFiles.length,
  total => {
    const maxPage = Math.max(1, Math.ceil(total / pageSize.value))
    if (currentPage.value > maxPage) {
      currentPage.value = maxPage
    }
  }
)

function onSelectionChange(selected) {
  fileStore.selectedFiles = selected
}

function findPreviewResult(row) {
  return renameStore.previewResults.find(r =>
    r.original_path === row.full_path || r.new_path === row.full_path
  )
}

function isSelectable(row) {
  const result = findPreviewResult(row)
  return !result || result.status === 'normal'
}

function getNewName(row) {
  const result = findPreviewResult(row)
  if (!result) return '-'
  if (result.status === 'renamed') return '(已重命名)'
  return result.new_name
}

function getNewNameClass(row) {
  const result = findPreviewResult(row)
  if (!result) return ''
  if (result.status === 'conflict') return 'text-danger'
  if (result.status === 'unchanged') return 'text-muted'
  if (result.status === 'renamed') return 'text-renamed'
  return 'text-success'
}

function getStatusType(row) {
  const result = findPreviewResult(row)
  if (!result) return 'info'
  if (result.status === 'conflict') return 'danger'
  if (result.status === 'unchanged') return 'info'
  if (result.status === 'renamed') return 'success'
  return 'success'
}

function getStatusText(row) {
  const result = findPreviewResult(row)
  if (!result) return '未预览'
  if (result.status === 'conflict') return '冲突'
  if (result.status === 'unchanged') return '无变化'
  if (result.status === 'renamed') return '已重命名'
  return '正常'
}
const settingsStore = useSettingsStore()

async function handleOpen(row) {
  openResults.value[row.full_path] = { status: 'loading' }
  const openWith = settingsStore.settings.open_with || ''
  try {
    await openFile(row.full_path, openWith)
    openResults.value[row.full_path] = { status: "opened" }
    ElMessage.success('已打开')
  } catch (e) {
    const message = e.message || '未知错误'
    openResults.value[row.full_path] = { status: "failed", message }
    ElMessage.error('打开失败: ' + message)
  }
}

function getOpenLabel(row) {
  const result = openResults.value[row.full_path]
  if (!result) return '打开'
  if (result.status === 'loading') return '打开中'
  if (result.status === 'opened') return '已打开'
  if (result.status === 'failed') return '打开失败'
  return '打开'
}

function handleQuickAdd(row) {
  renameStore.applyQuickAdd(row.full_path)
}

function handleRemove(row) {
  ElMessageBox.confirm(
    '确定要从列表中移除「' + row.filename + '」吗？',
    '确认移除',
    { confirmButtonText: '移除', cancelButtonText: '取消', type: 'warning' }
  ).then(() => {
    fileStore.removeFilesByPaths([row.full_path])
    ElMessage.success('已从列表中移除')
  }).catch(() => {})
}

</script>

<style scoped>
.file-table-container { flex: 1; display: flex; flex-direction: column; overflow: hidden; }
.pagination { padding: 12px; display: flex; justify-content: center; border-top: 1px solid #e4e7ed; }
.text-danger { color: #f56c6c; font-weight: 500; }
.text-success { color: #67c23a; }
.text-muted { color: #909399; }
.text-renamed { color: #409eff; font-style: italic; }
</style>
