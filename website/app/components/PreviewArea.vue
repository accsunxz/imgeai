<template>
  <main class="preview">
    <div v-if="!result && !uiState.loading" class="empty">
      <div class="icon-circle">
        <Icon name="lucide:file-edit" size="32" color="#94a3b8"/>
      </div>
      <h3>Ready to Create</h3>
      <p>Select a scenario and click generate.</p>
    </div>

    <div v-else-if="uiState.loading" class="loading-state">
      <el-skeleton animated :rows="5" />
    </div>

    <div v-else class="result-card">
      <div class="card-header">
        <span class="tag">
          <Icon name="lucide:check-circle-2" size="14"/> Result
        </span>
        <button class="tool-btn" @click="copy">
          <Icon name="lucide:copy" size="16"/>
        </button>
      </div>
      <div class="card-body">
        <div class="content font-mono">{{ result.text }}</div>
        <div v-if="result.explanation" class="explanation">
          <div class="title"><Icon name="lucide:info" size="14"/> AI Note</div>
          <p>{{ result.explanation }}</p>
        </div>
      </div>
    </div>
  </main>
</template>

<script setup>
const { result, uiState } = useWorkspace()
const copy = () => {
  navigator.clipboard.writeText(result.value.text)
  ElMessage.success('已复制')
}
</script>

<style scoped lang="scss">
.preview { flex: 1; background: var(--bg-app); padding: 40px; overflow-y: auto; display: flex; justify-content: center; }
.empty { text-align: center; margin-top: 100px; .icon-circle { width: 80px; height: 80px; background: #fff; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto 20px; box-shadow: var(--shadow-sm); } }
.result-card { width: 100%; max-width: 800px; background: #fff; border-radius: 16px; box-shadow: var(--shadow-md); overflow: hidden; height: fit-content; border: 1px solid var(--border-color); }
.card-header { padding: 16px 24px; border-bottom: 1px solid var(--border-color); display: flex; justify-content: space-between; align-items: center; background: #fff; .tag { font-size: 12px; font-weight: 600; color: #059669; background: #ecfdf5; padding: 4px 10px; border-radius: 6px; display: flex; align-items: center; gap: 6px; } }
.card-body { padding: 32px; }
.content { font-size: 15px; line-height: 1.8; white-space: pre-wrap; color: var(--text-main); }
.explanation { margin-top: 32px; padding: 20px; background: var(--bg-app); border-radius: 8px; .title { font-size: 12px; font-weight: 700; color: var(--brand-primary); margin-bottom: 8px; display: flex; align-items: center; gap: 6px; } p { margin: 0; font-size: 13px; color: var(--text-regular); } }
.tool-btn { background: none; border: none; cursor: pointer; padding: 8px; border-radius: 6px; color: var(--text-secondary); &:hover { background: var(--bg-app); color: var(--brand-primary); } }
.loading-state { width: 100%; max-width: 800px; padding: 40px; background: #fff; border-radius: 16px; }
</style>