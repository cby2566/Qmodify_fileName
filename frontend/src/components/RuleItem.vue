<template>
  <div class="rule-item" :class="{ disabled: !rule.enabled }">
    <el-icon class="drag-handle"><Rank /></el-icon>
    <el-checkbox :checked="rule.enabled" @change="$emit('toggle')" />
    <span class="rule-type">{{ typeLabel }}</span>
    <div class="rule-params">
      <template v-if="rule.type === 'add_prefix'">
        <el-input v-model="rule.prefix" placeholder="前缀文本" size="small" @input="$emit('update', rule)" />
      </template>
      <template v-else-if="rule.type === 'add_suffix'">
        <el-input v-model="rule.suffix" placeholder="后缀文本" size="small" @input="$emit('update', rule)" />
      </template>
      <template v-else-if="rule.type === 'insert_text'">
        <el-input-number v-model="rule.position" :min="0" size="small" />
        <el-input v-model="rule.text" placeholder="插入文本" size="small" @input="$emit('update', rule)" />
      </template>
      <template v-else-if="rule.type === 'find_replace'">
        <el-input v-model="rule.search" placeholder="查找" size="small" @input="$emit('update', rule)" />
        <el-input v-model="rule.replace" placeholder="替换为" size="small" @input="$emit('update', rule)" />
        <el-checkbox v-model="rule.is_regex" @change="$emit('update', rule)">正则</el-checkbox>
      </template>
      <template v-else-if="rule.type === 'sequence'">
        <el-input-number v-model="rule.start" :min="0" size="small" />
        <span>步长</span>
        <el-input-number v-model="rule.step" :min="1" size="small" />
        <span>位数</span>
        <el-input-number v-model="rule.padding" :min="1" :max="10" size="small" />
        <el-select v-model="rule.position" size="small" style="width: 70px">
          <el-option label="前缀" value="prefix" />
          <el-option label="后缀" value="suffix" />
        </el-select>
      </template>
      <template v-else-if="rule.type === 'template'">
        <el-input v-model="rule.template" placeholder="{group} - {title} [{quality}]" size="small" @input="$emit('update', rule)" />
      </template>
    </div>
    <el-button type="danger" size="small" circle @click="$emit('remove')">
      <el-icon><Close /></el-icon>
    </el-button>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Rank, Close } from '@element-plus/icons-vue'

const props = defineProps({ rule: { type: Object, required: true } })
defineEmits(['remove', 'toggle', 'update'])

const typeLabels = {
  add_prefix: '前缀',
  add_suffix: '后缀',
  insert_text: '插入',
  find_replace: '替换',
  sequence: '序号',
  template: '模板'
}

const typeLabel = computed(() => typeLabels[props.rule.type] || props.rule.type)
</script>

<style scoped>
.rule-item { display: flex; align-items: center; gap: 8px; padding: 8px; border: 1px solid #e4e7ed; border-radius: 4px; margin-bottom: 6px; background: #fff; }
.rule-item.disabled { opacity: 0.5; }
.drag-handle { cursor: move; color: #909399; }
.rule-type { font-size: 12px; color: #409eff; background: #ecf5ff; padding: 2px 6px; border-radius: 3px; min-width: 32px; text-align: center; }
.rule-params { flex: 1; display: flex; gap: 6px; align-items: center; flex-wrap: wrap; }
</style>
