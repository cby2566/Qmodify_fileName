import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getFavorites, addFavorite, updateFavorite, deleteFavorite, touchFavorite } from '../api'

export const useFavoritesStore = defineStore('favorites', () => {
  const favorites = ref([])
  const loading = ref(false)

  async function fetch() {
    loading.value = true
    try {
      const res = await getFavorites()
      favorites.value = res.favorites || []
    } finally {
      loading.value = false
    }
  }

  async function add(data) {
    const res = await addFavorite(data)
    await fetch()
    return res
  }

  async function update(id, data) {
    const res = await updateFavorite(id, data)
    await fetch()
    return res
  }

  async function remove(id) {
    await deleteFavorite(id)
    await fetch()
  }

  async function touch(id) {
    try {
      const res = await touchFavorite(id)
      const item = favorites.value.find((f) => f.id === id)
      if (item && res && res.last_used_at) {
        item.last_used_at = res.last_used_at
      }
    } catch (e) {
      // 使用统计失败不应阻断主流程，静默忽略
    }
  }

  return { favorites, loading, fetch, add, update, remove, touch }
})
