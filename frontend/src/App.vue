<template>
  <div class="app-container">
    <header class="app-header">
      <h1>文件批量重命名工具</h1>
      <header-actions @show-logs="showLogs = true" @show-favorites="showFavorites = true" @show-settings="showSettings = true" />
    </header>

    <main class="app-main">
      <aside class="app-sidebar">
        <favorites-panel @select-pattern="onSelectPattern" />
        <rules-panel />
      </aside>

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
import { ref } from 'vue'
import HeaderActions from './components/HeaderActions.vue'
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

function onSelectPattern(pattern) {
  renameStore.regexPattern = pattern
}
</script>

<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
html, body, #app { height: 100%; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }
body { background: #f5f7fa; }
.app-container { display: flex; flex-direction: column; height: 100vh; }
.app-header { display: flex; justify-content: space-between; align-items: center; padding: 12px 20px; background: #ffffff; border-bottom: 1px solid #e4e7ed; }
.app-header h1 { font-size: 18px; color: #303133; font-weight: 600; }
.app-main { display: flex; flex: 1; overflow: hidden; }
.app-sidebar { width: 280px; background: #ffffff; border-right: 1px solid #e4e7ed; overflow-y: auto; padding: 16px; }
.app-content { flex: 1; display: flex; flex-direction: column; overflow: hidden; }
.app-footer { padding: 10px 20px; background: #ffffff; border-top: 1px solid #e4e7ed; }
</style>
