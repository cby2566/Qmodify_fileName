<template>
  <div class="favorites-manager">
    <div class="manager-toolbar">
      <el-button type="primary" size="small" @click="handleCreate">
        <el-icon><Plus /></el-icon>
        新增收藏
      </el-button>
      <span class="toolbar-hint">共 {{ favoritesStore.favorites.length }} 条</span>
    </div>

    <el-table :data="favoritesStore.favorites" stripe v-loading="favoritesStore.loading">
      <el-table-column prop="name" label="名称" width="150" />
      <el-table-column prop="pattern" label="正则表达式" min-width="250" show-overflow-tooltip />
      <el-table-column prop="description" label="说明" width="150" show-overflow-tooltip />
      <el-table-column prop="last_used_at" label="最近使用" width="170" />
      <el-table-column label="操作" width="150">
        <template #default="{ row }">
          <el-button type="primary" size="small" @click="handleEdit(row)">编辑</el-button>
          <el-button type="danger" size="small" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
      <template #empty>
        <el-empty description="暂无收藏" :image-size="60" />
      </template>
    </el-table>

    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑收藏' : '新增收藏'"
      width="560px"
      append-to-body
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
        <el-form-item label="名称" prop="name">
          <el-input v-model="form.name" placeholder="给这条正则起个名字" />
        </el-form-item>
        <el-form-item label="正则表达式" prop="pattern">
          <el-input
            v-model="form.pattern"
            type="textarea"
            :rows="4"
            placeholder="例如: ^\[(?P<group>.+?)\]\s*(?P<title>.+?)"
          />
        </el-form-item>
        <el-form-item label="说明" prop="description">
          <el-input v-model="form.description" type="textarea" :rows="2" placeholder="选填，记录适用场景" />
        </el-form-item>
      </el-form>
      <div class="edit-actions">
        <el-button size="small" @click="validateFormPattern" :disabled="!form.pattern">验证正则</el-button>
      </div>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submit">
          {{ isEdit ? '保存' : '收藏' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { Plus } from '@element-plus/icons-vue'
import { useFavoritesStore } from '../stores/favorites'
import { useRenameStore } from '../stores/rename'
import { validateRegex } from '../api'
import { ElMessage, ElMessageBox } from 'element-plus'

const favoritesStore = useFavoritesStore()
const renameStore = useRenameStore()

const dialogVisible = ref(false)
const saving = ref(false)
const formRef = ref(null)
const editingId = ref(null)
const form = reactive({ name: '', pattern: '', description: '' })
const rules = {
  name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
  pattern: [{ required: true, message: '请输入正则表达式', trigger: 'blur' }]
}

const isEdit = computed(() => Boolean(editingId.value))

function openDialog(row) {
  editingId.value = row?.id || null
  form.name = row?.name || ''
  // 新增时预填当前正则输入框的内容，与侧边栏「收藏」行为保持一致
  form.pattern = row?.pattern || renameStore.regexPattern || ''
  form.description = row?.description || ''
  dialogVisible.value = true
  formRef.value?.clearValidate()
}

function handleEdit(row) {
  openDialog(row)
}

function handleCreate() {
  openDialog(null)
}

async function submit() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  saving.value = true
  try {
    const payload = { name: form.name, pattern: form.pattern, description: form.description }
    if (isEdit.value) {
      await favoritesStore.update(editingId.value, payload)
      ElMessage.success('已更新')
    } else {
      await favoritesStore.add(payload)
      ElMessage.success('已收藏')
    }
    dialogVisible.value = false
  } catch (e) {
    ElMessage.error(`${isEdit.value ? '更新' : '新增'}失败：${e?.message || e}`)
  } finally {
    saving.value = false
  }
}

async function validateFormPattern() {
  try {
    const res = await validateRegex(form.pattern)
    if (res.valid) {
      ElMessage.success('正则表达式有效')
    } else {
      ElMessage.error(`正则无效: ${res.error}`)
    }
  } catch (e) {
    ElMessage.error(`验证失败：${e?.message || e}`)
  }
}

async function handleDelete(row) {
  try {
    await ElMessageBox.confirm(`确定删除收藏 "${row.name}" 吗？`, '确认删除', { type: 'warning' })
  } catch (e) {
    if (e !== 'cancel' && e !== 'close') {
      ElMessage.error(`操作失败：${e?.message || e}`)
    }
    return
  }
  try {
    await favoritesStore.remove(row.id)
    ElMessage.success('已删除')
  } catch (e) {
    ElMessage.error(`删除失败：${e?.message || e}`)
  }
}

onMounted(() => {
  favoritesStore.fetch().catch((e) => {
    ElMessage.error(`加载收藏失败：${e?.message || e}`)
  })
})
</script>

<style scoped>
.manager-toolbar { display: flex; align-items: center; gap: 12px; margin-bottom: 12px; }
.toolbar-hint { font-size: 12px; color: #909399; }
.edit-actions { display: flex; justify-content: flex-end; margin-top: 8px; }
</style>
