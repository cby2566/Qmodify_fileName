<template>
  <div class="app-container">
    <header class="app-header">
      <div class="header-title">
        <el-tooltip :content="sidebarCollapsed ? '打开侧边栏' : '关闭侧边栏'" placement="bottom">
          <el-button circle @click="toggleSidebar">
            <el-icon>
              <Expand v-if="sidebarCollapsed" />
              <Fold v-else />
            </el-icon>
          </el-button>
        </el-tooltip>
        <h1>文件批量重命名工具</h1>
      </div>
      <header-actions @show-logs="showLogs = true" @show-favorites="showFavorites = true" @show-settings="showSettings = true" />
    </header>

    <main class="app-main">
      <aside v-show="!sidebarCollapsed" class="app-sidebar" :style="{ width: `${sidebarWidth}px` }">
        <favorites-panel @select-pattern="onSelectPattern" />
        <rules-panel />
      </aside>
      <div v-show="!sidebarCollapsed" class="sidebar-resizer" @mousedown="startResize" />

      <section class="app-content">
        <toolbar />
        <file-table />
      </section>
    </main>

    <footer class="app-footer">
      <file-stats />
    </footer>

    <el-drawer v-model="showLogs" title="操作日志" size="60%">
      <logs-panel />
    </el-drawer>

    <el-drawer v-model="showFavorites" title="正则收藏夹" size="50%">
      <favorites-manager />
    </el-drawer>

    <el-drawer v-model="showSettings" title="设置" size="40%">
      <settings-panel />
    </el-drawer>
  </div>
</template>

<script setup>
import { onBeforeUnmount, ref } from 'vue'
import HeaderActions from './components/HeaderActions.vue'
import { Expand, Fold } from '@element-plus/icons-vue'
import FavoritesPanel from './components/FavoritesPanel.vue'
import RulesPanel from './components/RulesPanel.vue'
import Toolbar from './components/Toolbar.vue'
import FileTable from './components/FileTable.vue'
import FileStats from './components/FileStats.vue'
import LogsPanel from './components/LogsPanel.vue'
import FavoritesManager from './components/FavoritesManager.vue'
import SettingsPanel from './components/SettingsPanel.vue'
import { useRenameStore } from './stores/rename'

const renameStore = useRenameStore()
const showLogs = ref(false)
const showFavorites = ref(false)
const showSettings = ref(false)
const sidebarWidth = ref(Number(localStorage.getItem('sidebar_width')) || 360)
const sidebarCollapsed = ref(localStorage.getItem('sidebar_collapsed') === 'true')

let resizing = false
const minSidebarWidth = 280
const maxSidebarWidth = 520

function clampSidebarWidth(width) {
  return Math.min(maxSidebarWidth, Math.max(minSidebarWidth, width))
}

function startResize(event) {
  resizing = true
  document.body.classList.add('is-resizing-sidebar')
  resizeSidebar(event)
  window.addEventListener('mousemove', resizeSidebar)
  window.addEventListener('mouseup', stopResize)
}

function resizeSidebar(event) {
  if (!resizing) return
  sidebarWidth.value = clampSidebarWidth(event.clientX)
}

function stopResize() {
  if (!resizing) return
  resizing = false
  document.body.classList.remove('is-resizing-sidebar')
  localStorage.setItem('sidebar_width', String(sidebarWidth.value))
  window.removeEventListener('mousemove', resizeSidebar)
  window.removeEventListener('mouseup', stopResize)
}

function toggleSidebar() {
  sidebarCollapsed.value = !sidebarCollapsed.value
  localStorage.setItem('sidebar_collapsed', String(sidebarCollapsed.value))
}

function onSelectPattern(pattern) {
  renameStore.regexPattern = pattern
}

onBeforeUnmount(() => {
  window.removeEventListener('mousemove', resizeSidebar)
  window.removeEventListener('mouseup', stopResize)
  document.body.classList.remove('is-resizing-sidebar')
})
</script>

<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
html, body, #app { height: 100%; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }
body { background: #f5f7fa; }
.app-container { display: flex; flex-direction: column; height: 100vh; }
.app-header { display: flex; justify-content: space-between; align-items: center; gap: 16px; padding: 12px 20px; background: #ffffff; border-bottom: 1px solid #e4e7ed; }
.header-title { display: flex; align-items: center; gap: 10px; flex: 0 0 auto; }
.app-header h1 { font-size: 18px; color: #303133; font-weight: 600; }
.app-main { display: flex; flex: 1; overflow: hidden; }
.app-sidebar { flex: 0 0 auto; min-width: 280px; max-width: 520px; background: #ffffff; overflow-y: auto; padding: 16px; }
.sidebar-resizer { flex: 0 0 6px; cursor: col-resize; background: #ffffff; border-left: 1px solid #e4e7ed; border-right: 1px solid #e4e7ed; transition: background-color 0.15s ease; }
.sidebar-resizer:hover,
body.is-resizing-sidebar .sidebar-resizer { background: #d9ecff; }
body.is-resizing-sidebar { cursor: col-resize; user-select: none; }
.app-content { flex: 1; display: flex; flex-direction: column; overflow: hidden; }
.app-footer { padding: 10px 20px; background: #ffffff; border-top: 1px solid #e4e7ed; }
</style>
