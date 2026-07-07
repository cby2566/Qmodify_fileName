<template>
  <div class="rules-panel">
    <div class="panel-header">
      <h3>重命名规则</h3>
      <el-dropdown @command="addRule">
        <el-button type="primary" size="small">
          <el-icon><Plus /></el-icon>
          添加规则
        </el-button>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item command="add_prefix">添加前缀</el-dropdown-item>
            <el-dropdown-item command="add_suffix">添加后缀</el-dropdown-item>
            <el-dropdown-item command="insert_text">插入字符串</el-dropdown-item>
            <el-dropdown-item command="find_replace">查找替换</el-dropdown-item>
            <el-dropdown-item command="sequence">序号编排</el-dropdown-item>
            <el-dropdown-item command="template">模板重组</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>

    <div class="regex-input">
      <el-input
        v-model="renameStore.regexPattern"
        placeholder="{{# 输入正则表达式，用于模板重组 }}&#10;例如: ^\[(?P&lt;group&gt;.+?)\]\s*(?P&lt;title&gt;.+?)&#10;.*$"
        type="textarea"
        :rows="3"
      />
    </div>
    <div class="regex-input-buttons">
      <el-button size="small" @click="validatePattern" :disabled="!renameStore.regexPattern">验证</el-button>
      <el-button size="small" @click="saveFavorite" :disabled="!renameStore.regexPattern">收藏</el-button>
    </div>

    <el-scrollbar max-height="300px">
      <draggable v-model="renameStore.rules" item-key="id" handle=".drag-handle">
        <template #item="{ element }">
          <rule-item :rule="element" @remove="renameStore.removeRule(element.id)" @toggle="renameStore.toggleRule(element.id)" @update="renameStore.updateRule(element.id, $event)" />
        </template>
      </draggable>
      <el-empty v-if="!renameStore.rules.length" description="暂无规则" :image-size="60" />
    </el-scrollbar>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { Plus } from '@element-plus/icons-vue'
import Draggable from 'vuedraggable'
import RuleItem from './RuleItem.vue'
import { useRenameStore } from '../stores/rename'
import { useFavoritesStore } from '../stores/favorites'
import { validateRegex, extractRegex } from '../api'
import { ElMessage, ElMessageBox } from 'element-plus'

const renameStore = useRenameStore()
const favoritesStore = useFavoritesStore()

function addRule(type) {
  const defaults = {
    add_prefix: { type: 'add_prefix', prefix: '', enabled: true, id: Date.now().toString() },
    add_suffix: { type: 'add_suffix', suffix: '', enabled: true, id: Date.now().toString() },
    insert_text: { type: 'insert_text', position: 0, text: '', enabled: true, id: Date.now().toString() },
    find_replace: { type: 'find_replace', search: '', replace: '', is_regex: false, enabled: true, id: Date.now().toString() },
    sequence: { type: 'sequence', start: 1, step: 1, padding: 2, position: 'suffix', enabled: true, id: Date.now().toString() },
    template: { type: 'template', template: '', enabled: true, id: Date.now().toString() }
  }
  renameStore.rules.push(defaults[type])
}

async function validatePattern() {
  const res = await validateRegex(renameStore.regexPattern)
  if (res.valid) {
    ElMessage.success('正则表达式有效')
  } else {
    ElMessage.error(`正则无效: ${res.error}`)
  }
}

async function saveFavorite() {
  try {
    const { value: name } = await ElMessageBox.prompt('请输入收藏名称', '收藏正则', {
      confirmButtonText: '保存',
      cancelButtonText: '取消'
    })
    await favoritesStore.add({
      name,
      pattern: renameStore.regexPattern,
      description: ''
    })
    ElMessage.success('已收藏')
  } catch (e) {
    // 取消
  }
}
</script>

<style scoped>
.rules-panel { margin-bottom: 20px; }
.panel-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.panel-header h3 { font-size: 14px; color: #303133; }
.regex-input { margin-bottom: 8px; }
.regex-input .el-textarea { width: 100%; }
.regex-input-buttons { display: flex; gap: 8px; justify-content: flex-end; margin-bottom: 12px; }
</style>
