<template>
  <el-dialog
    :model-value="modelValue"
    @update:model-value="$emit('update:modelValue', $event)"
    title="文件详情"
    width="800px"
    :close-on-click-modal="true"
  >
    <el-descriptions v-if="file" border column="1">
      <el-descriptions-item :label="file.is_dir ? '文件夹名' : '文件名'">{{ file.filename }}</el-descriptions-item>
      <el-descriptions-item label="完整路径">{{ file.full_path }}</el-descriptions-item>
      <el-descriptions-item label="父目录">{{ file.parent_dir }}</el-descriptions-item>
      <el-descriptions-item label="类型">{{ file.is_dir ? '文件夹' : (file.extension || '-') }}</el-descriptions-item>
      <el-descriptions-item label="大小">
        <span>{{ sizeText }}</span>
        <el-button
          v-if="file.is_dir"
          type="primary"
          link
          size="small"
          style="margin-left: 8px"
          :loading="fileStore.calculatingSize"
          :disabled="fileStore.calculatingSize"
          @click="measureNow"
        >
          {{ measured && !measured.error ? '重新测量' : '测量大小' }}
        </el-button>
      </el-descriptions-item>
      <el-descriptions-item v-if="file.is_dir" label="文件数量">
        {{ fileCountText }}
      </el-descriptions-item>
      <el-descriptions-item label="创建时间">{{ formatTime(file.created_time) }}</el-descriptions-item>
      <el-descriptions-item label="修改时间">{{ formatTime(file.modified_time) }}</el-descriptions-item>
    </el-descriptions>
  </el-dialog>
</template>

<script setup>
import { computed } from 'vue'
import { ElMessage } from 'element-plus'
import { useFileStore } from '../stores/files'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  file: { type: Object, default: null }
})

defineEmits(['update:modelValue'])

const fileStore = useFileStore()

// A directory has no size until it is measured on demand, so fall back to the
// cached measurement (if the user already calculated this page) rather than
// always showing a dash.
const measured = computed(() => {
  if (!props.file?.is_dir) return null
  return fileStore.sizeOf(props.file.full_path) || null
})

const sizeText = computed(() => {
  const f = props.file
  if (!f) return '-'
  if (!f.is_dir) return f.size_display || '-'
  const m = measured.value
  if (!m) return '—（未测量）'
  if (m.error) return '不可读'
  // A truncated walk only totalled part of the tree; mark it as a lower bound.
  return m.size_display + (m.truncated ? ' 以上' : '')
})

const fileCountText = computed(() => {
  const m = measured.value
  if (!m) return '—（未测量）'
  if (m.error) return '不可读'
  return m.truncated ? `${m.file_count} 个以上` : `${m.file_count} 个`
})

// Lets the owner size this one folder without leaving the dialog.
async function measureNow() {
  if (!props.file?.is_dir) return
  if (fileStore.calculatingSize) return
  try {
    const { measured: n, failed } = await fileStore.calculateSizes([props.file.full_path])
    if (failed) ElMessage.warning('读取失败，无法测量该文件夹')
    else if (!n) ElMessage.info('未获得结果')
  } catch (e) {
    ElMessage.error('计算失败: ' + (e?.message || e))
  }
}

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
