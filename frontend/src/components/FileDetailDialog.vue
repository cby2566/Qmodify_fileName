<template>
  <el-dialog
    :model-value="modelValue"
    @update:model-value="$emit('update:modelValue', $event)"
    title="文件详情"
    width="800px"
    :close-on-click-modal="true"
  >
    <el-descriptions v-if="file" border column="1">
      <el-descriptions-item label="文件名">{{ file.filename }}</el-descriptions-item>
      <el-descriptions-item label="完整路径">{{ file.full_path }}</el-descriptions-item>
      <el-descriptions-item label="父目录">{{ file.parent_dir }}</el-descriptions-item>
      <el-descriptions-item label="类型">{{ file.extension || '-' }}</el-descriptions-item>
      <el-descriptions-item label="大小">{{ file.size_display }}</el-descriptions-item>
      <el-descriptions-item label="创建时间">{{ formatTime(file.created_time) }}</el-descriptions-item>
      <el-descriptions-item label="修改时间">{{ formatTime(file.modified_time) }}</el-descriptions-item>
    </el-descriptions>
  </el-dialog>
</template>

<script setup>
defineProps({
  modelValue: { type: Boolean, default: false },
  file: { type: Object, default: null }
})

defineEmits(['update:modelValue'])

function formatTime(iso) {
  if (!iso) return '-'
  try {
    const d = new Date(iso)
    if (isNaN(d.getTime())) return iso
    const pad = n => String(n).padStart(2, '0')
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
  } catch {
    return iso
  }
}
</script>
