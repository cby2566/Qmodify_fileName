<template>
  <div class="settings-panel">
    <el-form :model="settingsStore.settings" label-width="140px">
      <el-form-item label="可选扩展名管理">
        <div class="ext-pool">
          <el-tag
            v-for="ext in settingsStore.settings.available_extensions"
            :key="ext"
            closable
            :disable-transitions="true"
            @close="removeExtension(ext)"
            class="ext-tag"
          >
            {{ ext }}
          </el-tag>
          <span v-if="!settingsStore.settings.available_extensions.length" class="ext-empty">暂无可选项，请在下方添加</span>
        </div>
        <div class="ext-add">
          <el-input
            v-model="newExtension"
            placeholder="增加扩展名，如 .pdf"
            clearable
            :disabled="saving"
            @keyup.enter="addExtension"
          >
            <template #prepend>添加</template>
          </el-input>
          <el-button type="primary" :disabled="saving" @click="addExtension">添加</el-button>
        </div>
      </el-form-item>

      <el-form-item label="当前目标扩展名">
        <el-select-v2
          v-model="settingsStore.settings.target_extensions"
          multiple
          placeholder="选择本次扫描的目标扩展名"
          :options="poolOptions"
          @change="persistTargets"
        />
      </el-form-item>

      <el-form-item label="默认递归扫描">
        <el-switch v-model="settingsStore.settings.default_recursive" />
      </el-form-item>
      <el-form-item label="最大扫描深度">
        <el-input-number v-model="settingsStore.settings.max_scan_depth" :min="1" :max="10" />
      </el-form-item>
      <el-form-item label="日志保留天数">
        <el-input-number v-model="settingsStore.settings.log_retention_days" :min="1" :max="365" />
      </el-form-item>
      <el-form-item label="打开方式">
        <el-input
          v-model="settingsStore.settings.open_with"
          placeholder="留空使用系统默认，填写程序路径如 C:\Program Files\...\app.exe"
          clearable
        />
      </el-form-item>
      <el-form-item label="预览防抖(ms)">
        <el-input-number v-model="settingsStore.settings.preview_debounce_ms" :min="100" :max="2000" />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" :loading="saving" @click="saveSettings">保存设置</el-button>
      </el-form-item>
    </el-form>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useSettingsStore } from '../stores/settings'
import { ElMessage } from 'element-plus'

const settingsStore = useSettingsStore()
const newExtension = ref('')
const saving = ref(false)

const poolOptions = computed(() =>
  settingsStore.settings.available_extensions.map(ext => ({ value: ext, label: ext }))
)

async function addExtension() {
  const raw = newExtension.value.trim().toLowerCase()
  if (!raw) return
  // Normalize: ensure leading dot, strip unsafe characters.
  const ext = raw.startsWith('.') ? raw : '.' + raw
  const valid = /^\.[a-z0-9][a-z0-9.]{0,14}$/i
  if (!valid.test(ext)) {
    ElMessage.warning('扩展名格式无效，仅支持字母、数字与单个点号（如 .tar.gz）')
    return
  }
  const pool = settingsStore.settings.available_extensions
  if (pool.includes(ext)) {
    ElMessage.warning('该扩展名已存在')
    return
  }

  const nextAvail = [...pool, ext].sort()
  // Auto-select newly added extension so it becomes active immediately.
  const nextTargets = settingsStore.settings.target_extensions.includes(ext)
    ? settingsStore.settings.target_extensions
    : [...settingsStore.settings.target_extensions, ext]

  saving.value = true
  try {
    await settingsStore.save({ available_extensions: nextAvail, target_extensions: nextTargets })
    ElMessage.success('已添加 ' + ext)
    newExtension.value = ''
  } finally {
    saving.value = false
  }
}

// Persist both the available pool and the active targets in one shot.
// Single source of truth prevents stale server state from undoing local edits.
async function persistBoth(nextAvail, nextTargets) {
  if (nextAvail !== undefined) settingsStore.settings.available_extensions = nextAvail
  if (nextTargets !== undefined) settingsStore.settings.target_extensions = nextTargets
  saving.value = true
  try {
    await settingsStore.save({
      available_extensions: settingsStore.settings.available_extensions,
      target_extensions: settingsStore.settings.target_extensions,
    })
  } catch (e) {
    ElMessage.error('保存失败：' + (e?.message || e))
    // Roll back by re-fetching the authoritative server state.
    await settingsStore.fetch()
  } finally {
    saving.value = false
  }
}

function removeExtension(ext) {
  if (settingsStore.settings.available_extensions.length <= 1) {
    ElMessage.warning('至少需要保留一个扩展名')
    return
  }
  const nextAvail = settingsStore.settings.available_extensions.filter(e => e !== ext)
  const nextTargets = settingsStore.settings.target_extensions.filter(e => e !== ext)
  void persistBoth(nextAvail, nextTargets)
}

async function persistTargets() {
  await persistBoth(undefined, settingsStore.settings.target_extensions)
}

async function saveSettings() {
  saving.value = true
  try {
    await settingsStore.save(settingsStore.settings)
    ElMessage.success('设置已保存')
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  settingsStore.fetch()
})
</script>

<style scoped>
.settings-panel { padding: 20px; }
.ext-pool {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 8px;
  min-height: 32px;
}
.ext-tag { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }
.ext-empty { color: #909399; font-size: 12px; line-height: 32px; }
.ext-add { display: flex; gap: 8px; max-width: 420px; }
</style>