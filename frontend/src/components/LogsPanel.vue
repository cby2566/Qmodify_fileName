<template>
  <div class="logs-panel">
    <div class="panel-toolbar">
      <el-input v-model="searchKeyword" placeholder="搜索文件名" style="width: 200px" clearable />
      <el-select v-model="filterAction" placeholder="操作类型" clearable style="width: 120px">
        <el-option label="重命名" value="rename" />
        <el-option label="撤销" value="undo" />
        <el-option label="错误" value="error" />
      </el-select>
      <el-button type="danger" size="small" @click="handleClearLogs" :disabled="!logs.length">清空日志</el-button>
      <el-button size="small" @click="exportLogs">导出</el-button>
    </div>
    <el-table :data="filteredLogs" stripe height="100%">
      <el-table-column prop="created_at" label="时间" width="170" />
      <el-table-column prop="action_type" label="类型" width="80">
        <template #default="{ row }">
          <el-tag :type="actionType(row.action_type)" size="small">{{ actionLabel(row.action_type) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="原文件名" min-width="200" show-overflow-tooltip>
        <template #default="{ row }">
          <span>{{ basename(row.original_path) }}</span>
        </template>
      </el-table-column>
      <el-table-column label="新文件名" min-width="200" show-overflow-tooltip>
        <template #default="{ row }">
          <span>{{ basename(row.new_path) }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="80">
        <template #default="{ row }">
          <el-tag :type="statusType(row.status)" size="small">{{ row.status }}</el-tag>
        </template>
      </el-table-column>
    </el-table>
    <el-pagination
      v-model:current-page="currentPage"
      :page-size="50"
      :total="logs.length"
      layout="total, prev, pager, next"
      background
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getLogs, clearLogs as apiClearLogs, exportData } from '../api'
import { ElMessage, ElMessageBox } from 'element-plus'

const logs = ref([])
const searchKeyword = ref('')
const filterAction = ref('')
const currentPage = ref(1)

const filteredLogs = computed(() => {
  let result = logs.value
  if (searchKeyword.value) {
    const kw = searchKeyword.value.toLowerCase()
    result = result.filter(l => l.original_path?.toLowerCase().includes(kw) || l.new_path?.toLowerCase().includes(kw))
  }
  if (filterAction.value) {
    result = result.filter(l => l.action_type === filterAction.value)
  }
  const start = (currentPage.value - 1) * 50
  return result.slice(start, start + 50)
})

function basename(path) {
  if (!path) return ''
  const parts = path.replace(/\\/g, '/').split('/')
  return parts[parts.length - 1] || path
}

function actionType(t) {
  return { rename: 'primary', undo: 'warning', error: 'danger' }[t] || 'info'
}

function actionLabel(t) {
  return { rename: '重命名', undo: '撤销', error: '错误' }[t] || t
}

function statusType(s) {
  return { success: 'success', failed: 'danger', skipped: 'info' }[s] || 'info'
}

async function fetchLogs() {
  const res = await getLogs({ page: 1, page_size: 500 })
  logs.value = res.items || []
}

async function handleClearLogs() {
  try {
    await ElMessageBox.confirm('确定要清空所有日志吗？此操作不可恢复。', '确认清空', { type: 'warning' })
    await apiClearLogs()
    logs.value = []
    ElMessage.success('日志已清空')
  } catch (e) {
    // 取消
  }
}

async function exportLogs() {
  await exportData('logs', filteredLogs.value, 'csv')
  ElMessage.success('已导出')
}

onMounted(fetchLogs)
</script>

<style scoped>
.panel-toolbar { display: flex; gap: 8px; margin-bottom: 12px; align-items: center; }
</style>
