<template>
  <div class="file-table-container">
    <el-table
      ref="tableRef"
      :data="paginatedFiles"
      :row-key="row => row.full_path"
      stripe
      height="100%"
      @selection-change="onSelectionChange"
      v-loading="fileStore.loading"
    >
      <el-table-column type="selection" width="50" :selectable="isSelectable" reserve-selection />
      <el-table-column prop="filename" label="当前名称" min-width="250" show-overflow-tooltip>
        <template #default="{ row }">
          <span class="name-cell">
            <el-icon v-if="row.is_dir" class="dir-icon"><Folder /></el-icon>
            <span
              :class="['clickable-name', { 'copied-flash': copiedKey === row.full_path }]"
              :title="isCopyableName(row.filename) ? '点击复制' : ''"
              @click="copyName(row.filename, row)"
            >{{ row.filename }}</span>
          </span>
        </template>
      </el-table-column>
      <el-table-column label="新名称" min-width="250" show-overflow-tooltip>
        <template #default="{ row }">
          <span
            :class="[getNewNameClass(row), 'clickable-name', { 'copied-flash': copiedKey === row.full_path }]"
            :title="isCopyableName(getNewName(row)) ? '点击复制' : ''"
            @click="copyName(getNewName(row), row)"
          >
            <span v-for="(seg, idx) in getNewNameSegments(row)" :key="idx" :class="'diff-' + seg.type">{{ seg.text }}</span>
          </span>
        </template>
      </el-table-column>
      <el-table-column label="大小" width="100" sortable :sort-by="sortBySize">
        <template #default="{ row }">
          <span :class="{ 'text-muted': row.is_dir && !sizeCell(row).value }">{{ sizeCell(row).text }}</span>
        </template>
      </el-table-column>
      <el-table-column label="类型" width="80">
        <template #default="{ row }">
          <span v-if="row.is_dir" class="clickable-ext" @click="showDetail(row)">文件夹</span>
          <span v-else class="clickable-ext" @click="showDetail(row)">{{ row.extension || '-' }}</span>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="90">
        <template #default="{ row }">
          <el-tag
            :type="getStatusType(row)"
            size="small"
            :class="{ 'clickable-status': isStatusClickable(row) }"
            @click="handleStatusClick(row)"
          >{{ getStatusText(row) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200" fixed="right">
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
      <div class="pagination-left">
        <el-button
          v-if="fileStore.targetType === 'dir'"
          type="primary"
          plain
          size="small"
          :loading="fileStore.calculatingSize"
          :disabled="!pageDirs.length"
          @click="calculatePageSizes"
        >
          <el-icon v-if="!fileStore.calculatingSize"><Odometer /></el-icon>
          {{ sizeButtonLabel }}
        </el-button>
        <span v-if="fileStore.targetType === 'dir' && pageDirs.length" class="pagination-hint">
          本页 {{ pageDirs.length }} 个文件夹 ·
          <template v-if="pageMeasuredAt">
            已测量 {{ pageDirsCalculated }}/{{ pageDirs.length }}（{{ measuredAgo }}）
          </template>
          <template v-else>尚未测量大小</template>
        </span>
      </div>
      <el-pagination
        @current-page="currentPage"
        @page-size="pageSize"
        :page-sizes="[50, 100, 200, 500]"
        :total="fileStore.filteredFiles.length"
        layout="total, sizes, prev, pager, next"
        background
      />
    </div>

    <FileDetailDialog v-model="detailVisible" :file="detailFile" />
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Folder, Odometer } from '@element-plus/icons-vue'
import { useFileStore } from '../stores/files'
import { useRenameStore } from '../stores/rename'
import { useSettingsStore } from '../stores/settings'
import { openFile } from '../api'
import { computeFilenameDiff, segmentsFromSpans } from '../utils/index'
import FileDetailDialog from './FileDetailDialog.vue'

const fileStore = useFileStore()
const renameStore = useRenameStore()
const openResults = ref({})
const copiedKey = ref('')
const detailVisible = ref(false)
const detailFile = ref(null)

const currentPage = ref(1)
const pageSize = ref(100)
const tableRef = ref(null)

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

// 监听 selectedFiles 变化，当它被清空时，同步清除表格选择状态
watch(
  () => fileStore.selectedFiles.length,
  (newLength, oldLength) => {
    if (newLength === 0 && oldLength > 0 && tableRef.value) {
      tableRef.value.clearSelection()
    }
  }
)

function onSelectionChange(selected) {
  fileStore.selectedFiles = selected
}

function findPreviewResult(row) {
  return renameStore.previewResults.find(r => r.original_path === row.full_path)
}

function isSelectable(row) {
  const result = findPreviewResult(row)
  return !result || result.status === 'normal'
}

// Directories sort below files of the same "size"; they have no real size.
function sortBySize(row) {
  return row.is_dir ? -1 : (row.size_bytes || 0)
}

// Directories show a placeholder until the user asks for their size.
function sizeCell(row) {
  if (!row.is_dir) return { text: row.size_display, value: row.size_bytes || 0 }
  const cached = fileStore.sizeOf(row.full_path)
  if (!cached) return { text: '—', value: 0 }
  if (cached.error) return { text: cached.error === '计算失败' ? '计算失败' : '不可读', value: 0 }
  return { text: cached.size_display + (cached.truncated ? '+' : ''), value: cached.size_bytes }
}

// Only the rows the user can actually see are ever measured.
const pageDirs = computed(() => paginatedFiles.value.filter(f => f.is_dir))

const pageDirsCalculated = computed(
  () => pageDirs.value.filter(f => !!fileStore.sizeOf(f.full_path)).length
)

// Ticking clock so the "measured N minutes ago" label stays honest without
// the user having to re-render anything. Cheap: 1 timer per 30s.
const now = ref(Date.now())
let clockTimer = null
onMounted(() => {
  clockTimer = setInterval(() => { now.value = Date.now() }, 30_000)
})
onUnmounted(() => {
  if (clockTimer) clearInterval(clockTimer)
  clockTimer = null
})

// When this page was last measured. Shown to the user because a folder's size
// is a snapshot, not a live value — contents may have changed since.
const pageMeasuredAt = computed(() =>
  fileStore.lastMeasuredAt(pageDirs.value.map(f => f.full_path))
)

const measuredAgo = computed(() => {
  if (!pageMeasuredAt.value) return ''
  const secs = Math.max(0, Math.round((now.value - pageMeasuredAt.value) / 1000))
  if (secs < 45) return '刚刚'
  if (secs < 3600) return `${Math.round(secs / 60)} 分钟前`
  return `${Math.round(secs / 3600)} 小时前`
})

const sizeButtonLabel = computed(() => {
  if (fileStore.calculatingSize) return '计算中...'
  const total = pageDirs.value.length
  if (!total) return '计算本页大小'
  // Once measured, the button re-measures: a cached value is never assumed
  // to still be current, because folder contents change under our feet.
  if (pageDirsCalculated.value >= total) return '重新计算本页'
  return `计算本页大小 (${total - pageDirsCalculated.value})`
})

async function calculatePageSizes() {
  const paths = pageDirs.value.map(f => f.full_path)
  if (!paths.length) return
  try {
    // Always measure the whole page; never skip paths just because a stale
    // value happens to be cached.
    const { measured, failed } = await fileStore.calculateSizes(paths)
    if (failed) {
      ElMessage.warning(`已重算 ${measured} 个文件夹，${failed} 个读取失败`)
    } else {
      ElMessage.success(`已重算本页 ${measured} 个文件夹的大小`)
    }
  } catch (e) {
    ElMessage.error('计算失败: ' + (e?.message || e))
  }
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

function getNewNameSegments(row) {
  const result = findPreviewResult(row)
  if (!result) return [{ text: '-', type: 'unchanged' }]
  if (result.status === 'renamed') return [{ text: '(已重命名)', type: 'unchanged' }]
  // Prefer engine-provided rule spans (plan C); fall back to string diff for
  // legacy payloads, deletion-only results, or malformed spans.
  if (Array.isArray(result.spans) && result.spans.length > 0) {
    const segs = segmentsFromSpans(result.new_name, result.spans)
    if (segs) return segs
  }
  return computeFilenameDiff(result.original_name, result.new_name)
}

function isCopyableName(name) {
  return !!name && name !== '-' && name !== '无变化'
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

function isStatusClickable(row) {
  const result = findPreviewResult(row)
  // 只有"正常"、"冲突"、"无变化"状态可以点击撤销
  return result && result.status !== 'renamed'
}

function handleStatusClick(row) {
  if (!isStatusClickable(row)) return

  renameStore.resetPreview(row.full_path)
  ElMessage.success('已撤销预览修改')
}

const settingsStore = useSettingsStore()

async function handleOpen(row) {
  openResults.value[row.full_path] = { status: 'loading' }
  // Files and directories have independent open-with settings: a program
  // chosen for previewing files must not be used to open a folder.
  const openWith = row.is_dir
    ? (settingsStore.settings.open_dir_with || '')
    : (settingsStore.settings.open_with || '')
  try {
    await openFile(row.full_path, openWith, !!row.is_dir)
    openResults.value[row.full_path] = { status: "opened" }
    const target = openWith ? '已用指定程序打开' : (row.is_dir ? '已在资源管理器中打开' : '已打开')
    ElMessage.success(target)
  } catch (e) {
    const message = e.message || '未知错误'
    openResults.value[row.full_path] = { status: "failed", message }
    ElMessage.error('打开失败: ' + message)
  }
}

function getOpenLabel(row) {
  const result = openResults.value[row.full_path]
  const noun = row.is_dir ? '打开目录' : '打开'
  if (!result) return noun
  if (result.status === 'loading') return '打开中'
  if (result.status === 'opened') return '已打开'
  if (result.status === 'failed') return '打开失败'
  return noun
}

function handleQuickAdd(row) {
  renameStore.applyQuickAdd(row.full_path)
}

function copyName(name, row) {
  if (!isCopyableName(name)) {
    ElMessage.warning('无可复制的内容')
    return
  }
  copiedKey.value = row.full_path
  setTimeout(() => { copiedKey.value = '' }, 500)
  writeToClipboard(name)
}

function writeToClipboard(text) {
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(text)
      .then(() => ElMessage.info('已复制: ' + text))
      .catch(() => fallbackCopy(text))
  } else {
    fallbackCopy(text)
  }
}

function fallbackCopy(text) {
  const ta = document.createElement('textarea')
  ta.value = text
  ta.style.position = 'fixed'
  ta.style.opacity = '0'
  document.body.appendChild(ta)
  ta.select()
  try {
    // eslint-disable-next-line deprecation
    document.execCommand('copy')
    ElMessage.info('已复制: ' + text)
  } catch {
    ElMessage.error('复制失败，请手动复制')
  }
  document.body.removeChild(ta)
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

function showDetail(row) {
  detailFile.value = row
  detailVisible.value = true
}

</script>

<style scoped>
.file-table-container { flex: 1; display: flex; flex-direction: column; overflow: hidden; }
.pagination { padding: 12px; display: flex; justify-content: center; align-items: center; gap: 16px; border-top: 1px solid #e4e7ed; }
.pagination-left { display: flex; align-items: center; gap: 10px; min-width: 0; }
.pagination-hint { font-size: 12px; color: #909399; white-space: nowrap; }
.text-danger { color: #f56c6c; font-weight: 500; }
.text-success { color: #3595f5; }
.text-muted { color: #909399; }
.text-renamed { color: #409eff; font-style: italic; }
.diff-added { color: #67c23a; font-weight: 500; }
.diff-modified { color: #e6a23c; font-weight: 500; }
.clickable-name { cursor: pointer; }
.clickable-name:hover { color: #409eff; }
.clickable-name:not(.clickable-name:hover) { cursor: default; }
.clickable-ext { cursor: pointer; color: #409eff; }
.name-cell { display: inline-flex; align-items: center; gap: 5px; min-width: 0; }
.dir-icon { color: #e6a23c; flex: 0 0 auto; }
.copied-flash { background-color: #ecf5ff; border-radius: 2px; }
.clickable-status { cursor: pointer; transition: all 0.3s; }
.clickable-status:hover { opacity: 0.7; transform: scale(1.05); }
</style>
