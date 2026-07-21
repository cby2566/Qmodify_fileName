<template>
  <div class="settings-panel">
    <!-- 固定顶部保存按钮 -->
    <div class="sticky-header">
      <el-button
        type="primary"
        size="large"
        :loading="saving"
        @click="saveSettings"
        class="save-btn"
      >
        <el-icon><Check /></el-icon>
        {{ saving ? '保存中...' : '保存所有设置' }}
      </el-button>
    </div>

    <!-- 扩展名管理卡片 -->
    <el-card class="setting-card" shadow="never">
      <template #header>
        <div class="card-header">
          <span class="card-title">
            <el-icon><Collection /></el-icon>
            可选扩展名管理
          </span>
          <el-tag type="info" size="small">{{ settingsStore.settings.available_extensions.length }} 个</el-tag>
        </div>
      </template>

      <div class="section-label">当前扩展名池：</div>
      <div class="ext-pool">
        <el-tag
          v-for="ext in settingsStore.settings.available_extensions"
          :key="ext"
          closable
          :disable-transitions="false"
          @close="removeExtension(ext)"
          class="ext-tag"
          effect="plain"
        >
          {{ ext }}
        </el-tag>
        <span v-if="!settingsStore.settings.available_extensions.length" class="ext-empty">
          <el-icon><InfoFilled /></el-icon> 暂无可选项，请在下方添加
        </span>
      </div>

      <div class="section-label">添加新扩展名：</div>
      <div class="ext-add">
        <el-input
          v-model="newExtension"
          placeholder="输入扩展名，如 .pdf"
          clearable
          :disabled="saving"
          @keyup.enter="addExtension"
          class="ext-input"
        >
          <template #prepend>
            <el-icon><Plus /></el-icon>
          </template>
        </el-input>
        <el-button
          type="primary"
          :disabled="saving || !newExtension.trim()"
          @click="addExtension"
          class="add-btn"
        >
          {{ saving ? '保存中...' : '添加' }}
        </el-button>
      </div>
    </el-card>

    <!-- 目标扩展名选择 -->
    <el-card class="setting-card" shadow="never">
      <template #header>
        <div class="card-header">
          <span class="card-title">
            <el-icon><Aim /></el-icon>
            当前扫描目标
          </span>
          <el-tag type="success" size="small">{{ settingsStore.settings.target_extensions.length }} 个已选</el-tag>
        </div>
      </template>
      <el-select-v2
        v-model="settingsStore.settings.target_extensions"
        multiple
        placeholder="选择本次扫描的目标扩展名"
        :options="poolOptions"
        @change="persistTargets"
        style="width: 100%"
      />
      <div class="setting-tip">💡 将从扩展名池中选择本次需要扫描的文件类型</div>
    </el-card>

    <!-- 扫描设置 -->
    <el-card class="setting-card" shadow="never">
      <template #header>
        <span class="card-title">
          <el-icon><Search /></el-icon>
          扫描设置
        </span>
      </template>

      <el-form
        :model="settingsStore.settings"
        label-width="120px"
        class="settings-form"
      >
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="默认递归扫描">
              <el-switch
                v-model="settingsStore.settings.default_recursive"
                active-text="启用"
                inactive-text="禁用"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="最大扫描深度">
              <el-input-number
                v-model="settingsStore.settings.max_scan_depth"
                :min="1"
                :max="10"
                controls-position="right"
                style="width: 120px"
              />
              <span class="input-tip">层</span>
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="日志保留天数">
          <el-input-number
            v-model="settingsStore.settings.log_retention_days"
            :min="1"
            :max="365"
            controls-position="right"
            style="width: 150px"
          />
          <span class="input-tip">天</span>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 高级设置 -->
    <el-card class="setting-card" shadow="never">
      <template #header>
        <span class="card-title">
          <el-icon><Setting /></el-icon>
          高级设置
        </span>
      </template>

      <el-form
        :model="settingsStore.settings"
        label-width="120px"
        class="settings-form"
      >
        <el-form-item label="打开方式">
          <el-input
            v-model="settingsStore.settings.open_with"
            placeholder="留空使用系统默认，填写程序路径"
            clearable
            class="full-width-input"
          >
            <template #prepend>
              <el-icon><FolderOpened /></el-icon>
            </template>
          </el-input>
        </el-form-item>

        <el-form-item label="预览防抖">
          <el-slider
            v-model="settingsStore.settings.preview_debounce_ms"
            :min="100"
            :max="2000"
            :step="100"
            show-input
            style="width: 300px"
          />
          <span class="input-tip">毫秒</span>
        </el-form-item>

        <el-divider content-position="left">快速添加功能</el-divider>

        <el-form-item label="快速添加文本">
          <el-input
            v-model="settingsStore.settings.quick_add_text"
            placeholder="_new"
            clearable
            style="width: 250px"
          >
            <template #prepend>
              <el-icon><EditPen /></el-icon>
            </template>
          </el-input>
        </el-form-item>

        <el-form-item label="快速添加模式">
          <el-radio-group v-model="settingsStore.settings.quick_add_mode">
            <el-radio-button value="prefix">加前缀</el-radio-button>
            <el-radio-button value="suffix">加后缀</el-radio-button>
          </el-radio-group>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import {
  Collection,
  InfoFilled,
  Plus,
  Aim,
  Search,
  Setting,
  FolderOpened,
  EditPen,
  Check
} from '@element-plus/icons-vue'
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
    ElMessage.success('设置已保存 ✅')

    // 添加成功脉冲动画
    const btn = document.querySelector('.save-btn')
    if (btn) {
      btn.classList.add('success-pulse')
      setTimeout(() => btn.classList.remove('success-pulse'), 600)
    }
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  settingsStore.fetch()
})
</script>

<style scoped>
.settings-panel {
  padding: 0 20px 20px;
  background: transparent;
}

/* 固定顶部保存按钮 */
.sticky-header {
  position: sticky;
  top: -20px;
  z-index: 100;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.98) 0%, rgba(255, 255, 255, 0.95) 100%);
  padding: 20px;
  margin: 0;
  border-bottom: 2px solid #e4e7ed;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  display: flex;
  justify-content: center;
  align-items: center;
  backdrop-filter: blur(12px);
}

.save-btn {
  font-size: 15px;
  font-weight: 600;
  padding: 12px 36px;
  min-width: 220px;
  height: 44px;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.3);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  letter-spacing: 0.5px;
}

.save-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(64, 158, 255, 0.4);
  background: linear-gradient(135deg, #409eff 0%, #337ecc 100%);
}

.save-btn:active:not(:disabled) {
  transform: translateY(0);
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.3);
}

.save-btn:disabled {
  cursor: not-allowed;
  opacity: 0.7;
}

.save-btn.el-button--primary {
  background: linear-gradient(135deg, #409eff 0%, #337ecc 100%);
  border: none;
}

.save-btn.el-button--primary:hover {
  background: linear-gradient(135deg, #337ecc 0%, #2a6bb0 100%);
  border: none;
}

/* Loading 状态优化 */
.save-btn :deep(.el-icon) {
  margin-right: 6px;
  font-size: 16px;
}

/* 焦点状态 - 提升可访问性 */
.save-btn:focus-visible {
  outline: 2px solid #409eff;
  outline-offset: 2px;
}

/* 保存成功脉冲动画 */
@keyframes success-pulse {
  0% {
    box-shadow: 0 4px 12px rgba(64, 158, 255, 0.3);
  }
  50% {
    box-shadow: 0 4px 20px rgba(64, 158, 255, 0.6), 0 0 0 8px rgba(64, 158, 255, 0.1);
  }
  100% {
    box-shadow: 0 4px 12px rgba(64, 158, 255, 0.3);
  }
}

.save-btn.success-pulse {
  animation: success-pulse 0.6s ease-in-out;
}

.setting-card {
  margin-bottom: 16px;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  overflow: hidden;
  transition: box-shadow 0.3s ease, transform 0.2s ease;
}

.setting-card:hover {
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  transform: translateY(-1px);
}

.setting-card :deep(.el-card__header) {
  padding: 14px 18px;
  font-weight: 600;
  border-bottom: 1px solid #e4e7ed;
  background: linear-gradient(180deg, #fafbfc 0%, #ffffff 100%);
}

.setting-card :deep(.el-card__body) {
  padding: 20px;
}

.card-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #303133;
}

.section-label {
  font-size: 12px;
  color: #606266;
  margin-bottom: 8px;
  margin-top: 12px;
  font-weight: 500;
}

.section-label:first-of-type {
  margin-top: 0;
}

.ext-pool {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 12px;
  padding: 10px;
  background: #f8f9fa;
  border-radius: 4px;
  min-height: 36px;
  align-items: center;
  border: 1px dashed #dcdfe6;
}

.ext-tag {
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 12px;
  padding: 2px 8px;
}

.ext-empty {
  color: #909399;
  font-size: 12px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.ext-add {
  display: flex;
  gap: 8px;
  align-items: center;
}

.ext-input {
  flex: 1;
}

.add-btn {
  min-width: 70px;
}

.settings-form {
  padding: 8px 0;
}

.full-width-input {
  width: 100%;
}

.input-tip {
  margin-left: 8px;
  color: #909399;
  font-size: 12px;
}

.setting-tip {
  margin-top: 8px;
  padding: 8px 10px;
  background: #f0f7ff;
  border-left: 3px solid #409eff;
  border-radius: 4px;
  font-size: 12px;
  color: #606266;
  line-height: 1.5;
}

@media (max-width: 768px) {
  .sticky-header {
    top: -16px;
    padding: 16px;
    margin: 0 -16px;
  }

  .save-btn {
    width: 100%;
    min-width: auto;
    height: 42px;
    font-size: 14px;
    padding: 10px 24px;
  }

  .setting-card :deep(.el-card__body) {
    padding: 16px;
  }
}

.ext-pool::-webkit-scrollbar {
  height: 6px;
}

.ext-pool::-webkit-scrollbar-thumb {
  background: #dcdfe6;
  border-radius: 3px;
}

.ext-pool::-webkit-scrollbar-thumb:hover {
  background: #909399;
}
</style>