<template>
  <div class="toolbar">
    <div class="toolbar-row">
      <el-select v-model="filterExtensions" multiple placeholder="扩展名" style="width: 200px" @change="applyFilters">
        <el-option v-for="ext in availableExtensions" :key="ext" :label="ext" :value="ext" />
      </el-select>
      <el-input v-model="filterKeyword" placeholder="文件名关键词" style="width: 180px" clearable @input="onKeywordInput" />
      <el-select v-model="filterMode" style="width: 80px">
        <el-option label="包含" value="include" />
        <el-option label="排除" value="exclude" />
      </el-select>
      <el-divider direction="vertical" />
      <el-button-group>
        <el-button @click="fileStore.selectAll()">全选</el-button>
        <el-button @click="fileStore.selectNone()">全不选</el-button>
        <el-button @click="fileStore.invertSelection()">反选</el-button>
      </el-button-group>
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
import { Refresh, Check } from '@element-plus/icons-vue'
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
