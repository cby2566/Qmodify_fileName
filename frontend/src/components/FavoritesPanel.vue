<template>
  <div class="favorites-panel">
    <div class="panel-header">
      <h3>正则收藏夹</h3>
    </div>
    <el-scrollbar max-height="200px">
      <div
        v-for="fav in favoritesStore.favorites"
        :key="fav.id"
        class="favorite-item"
        @click="$emit('selectPattern', fav.pattern)"
      >
        <el-icon><Star /></el-icon>
        <span>{{ fav.name }}</span>
      </div>
      <el-empty v-if="!favoritesStore.favorites.length" description="暂无收藏" :image-size="50" />
    </el-scrollbar>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { Star } from '@element-plus/icons-vue'
import { useFavoritesStore } from '../stores/favorites'

defineEmits(['selectPattern'])
const favoritesStore = useFavoritesStore()

onMounted(() => {
  favoritesStore.fetch()
})
</script>

<style scoped>
.panel-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.panel-header h3 { font-size: 14px; color: #303133; }
.favorite-item { display: flex; align-items: center; gap: 8px; padding: 8px; border-radius: 4px; cursor: pointer; transition: background 0.2s; }
.favorite-item:hover { background: #ecf5ff; }
.favorite-item .el-icon { color: #e6a23c; }
</style>
