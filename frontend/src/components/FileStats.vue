<template>
  <div class="file-stats">
    <el-space :size="24">
      <span>文件总数: <strong>{{ fileStore.filteredFiles.length }}</strong></span>
      <span>已选中: <strong>{{ fileStore.selectedFiles.length }}</strong></span>
      <span>总大小: <strong>{{ formatSize(fileStore.totalSize) }}</strong></span>
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
import { useFileStore } from '../stores/files'
import { useRenameStore } from '../stores/rename'
import { formatSize } from '../utils'

const fileStore = useFileStore()
const renameStore = useRenameStore()
</script>

<style scoped>
.file-stats { font-size: 13px; color: #606266; }
</style>
