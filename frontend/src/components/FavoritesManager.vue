<template>
  <div class="favorites-manager">
    <el-table :data="favoritesStore.favorites" stripe>
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
    </el-table>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { useFavoritesStore } from '../stores/favorites'
import { ElMessage, ElMessageBox } from 'element-plus'

const favoritesStore = useFavoritesStore()

async function handleEdit(row) {
  try {
    const { value: name } = await ElMessageBox.prompt('修改名称', '编辑收藏', {
      confirmButtonText: '保存',
      cancelButtonText: '取消',
      inputValue: row.name
    })
    await favoritesStore.update(row.id, { name })
    ElMessage.success('已更新')
  } catch (e) {
    // 取消
  }
}

async function handleDelete(row) {
  try {
    await ElMessageBox.confirm(`确定删除收藏 "${row.name}" 吗？`, '确认删除', { type: 'warning' })
    await favoritesStore.remove(row.id)
    ElMessage.success('已删除')
  } catch (e) {
    // 取消
  }
}

onMounted(() => {
  favoritesStore.fetch()
})
</script>

<style scoped>
</style>
