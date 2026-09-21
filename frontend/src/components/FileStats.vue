<template>
  <div class="file-stats">
    <el-space :size="24">
      <span>{{ countLabel }}: <strong>{{ fileStore.filteredFiles.length }}</strong></span>
      <span v-if="fileStore.dirCount > 0">文件夹: <strong>{{ fileStore.dirCount }}</strong></span>
      <span>已选中: <strong>{{ fileStore.selectedFiles.length }}</strong></span>
      <span>总大小: <strong>{{ fileStore.targetType === 'dir' ? '—' : formatSize(fileStore.totalSize) }}</strong></span>
      <span v-if="renameStore.previewResults.length">
        待重命名: <strong style="color: #67c23a">{{ renameStore.stats.toRename }}</strong>
      </span>
      <span v-if="renameStore.stats.conflicts > 0">
        冲突: <strong style="color: #f56c6c">{{ renameStore.stats.conflicts }}</strong>
      </span>
    </el-space>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useFileStore } from '../stores/files'
import { useRenameStore } from '../stores/rename'
import { formatSize } from '../utils'

const fileStore = useFileStore()
const renameStore = useRenameStore()

const countLabel = computed(() => {
  if (fileStore.targetType === 'dir') return '文件夹总数'
  if (fileStore.targetType === 'all') return '条目总数'
  return '文件总数'
})
</script>

<style scoped>
.file-stats { font-size: 13px; color: #606266; }
</style>
