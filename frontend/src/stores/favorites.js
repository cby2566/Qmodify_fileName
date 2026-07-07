import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getFavorites, addFavorite, updateFavorite, deleteFavorite } from '../api'

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

  return { favorites, loading, fetch, add, update, remove }
})
