<template>
  <el-dialog
      v-model="uiState.configDialog"
      title="底层引擎配置检视"
      width="760px"
      class="san-dialog"
      :close-on-click-modal="false"
  >
    <div v-if="currentTone" class="config-container">
      <div class="header-info">
        <span class="path">{{ currentScene?.name }} / {{ currentIntent?.name }} / <strong style="color:#4f46e5">{{ currentTone.name }}</strong></span>
      </div>

      <div class="section">
        <div class="section-title">
          <Icon name="lucide:database" size="14" /> RAG Pipeline (检索增强生成)
          <span class="rag-badge" :class="effectiveRag.enabled ? 'is-active' : 'is-disabled'">
            {{ effectiveRag.enabled ? 'ENABLED' : 'DISABLED' }}
          </span>
        </div>

        <template v-if="effectiveRag.enabled">
          <div class="rag-grid" v-if="effectiveRag.collection_name || effectiveRag.search_type || effectiveRag.top_k">
            <div class="param-box" v-if="effectiveRag.collection_name">
              <label>Collection (知识库)</label>
              <div class="val">{{ effectiveRag.collection_name }}</div>
            </div>
            <div class="param-box" v-if="effectiveRag.search_type">
              <label>Search Type (策略)</label>
              <div class="val">{{ effectiveRag.search_type }}</div>
            </div>
            <div class="param-box" v-if="effectiveRag.top_k !== undefined">
              <label>Top K (召回量)</label>
              <div class="val">{{ effectiveRag.top_k }}</div>
            </div>
          </div>

          <div v-if="effectiveRag.context_format" class="param-box mt-2">
            <label>Context Format (上下文注入格式)</label>
            <div class="code-block context-code">
              {{ effectiveRag.context_format }}
            </div>
          </div>

          <div v-if="effectiveRag.mock_corpus && effectiveRag.mock_corpus.length > 0" class="param-box mt-2">
            <label>Mock Corpus (预设参考语料 / Few-Shot)</label>
            <div class="mock-list">
              <div v-for="(item, idx) in effectiveRag.mock_corpus" :key="idx" class="mock-item">
                <div class="mock-line" v-if="item.input">
                  <span class="mock-label input-label">Input</span>
                  <span class="mock-text">{{ item.input }}</span>
                </div>
                <div class="mock-line" v-if="item.output?.english">
                  <span class="mock-label en-label">Out (EN)</span>
                  <span class="mock-text">{{ item.output.english }}</span>
                </div>
                <div class="mock-line" v-if="item.output?.chinese">
                  <span class="mock-label zh-label">Out (ZH)</span>
                  <span class="mock-text">{{ item.output.chinese }}</span>
                </div>
              </div>
            </div>
          </div>
        </template>

        <div v-if="!effectiveRag.enabled" class="disabled-hint">
          <Icon name="lucide:info" size="14" style="margin-right: 4px; vertical-align: middle;" />
          当前意图已禁用 RAG 语料检索。引擎将直接基于<strong>「提示词指令」</strong>与<strong>「您的输入文本」</strong>执行零样本 (Zero-Shot) 转化。
        </div>
      </div>

      <div class="section" v-if="currentTone.llm_params && Object.keys(currentTone.llm_params).length > 0">
        <div class="section-title"><Icon name="lucide:sliders" size="14" /> LLM Hyperparameters</div>
        <div class="params-grid">
          <div class="param-box" v-if="currentTone.llm_params.temperature !== undefined">
            <label>Temperature (随机性)</label>
            <div class="val">{{ currentTone.llm_params.temperature }}</div>
          </div>
          <div class="param-box" v-if="currentTone.llm_params.presence_penalty !== undefined">
            <label>Presence Penalty (新词偏好)</label>
            <div class="val">{{ currentTone.llm_params.presence_penalty }}</div>
          </div>
        </div>
      </div>

      <div class="section" v-if="currentTone.prompts">
        <div class="section-title"><Icon name="lucide:terminal-square" size="14" /> Prompt Template</div>

        <div class="code-block system-code" v-if="currentTone.prompts.system">
          <div class="code-comment">// System Prompt</div>
          {{ currentTone.prompts.system }}
        </div>

        <div class="code-block human-code mt-2" v-if="currentTone.prompts.human">
          <div class="code-comment">// Human Prompt</div>
          {{ currentTone.prompts.human }}
        </div>
      </div>
    </div>

    <div v-else class="empty-hint">请先在左侧选择场景与意图</div>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const { uiState, currentScene, currentIntent, currentTone } = useWorkspace()

const effectiveRag = computed(() => {
  const global = currentScene.value?.global_rag || {}
  const localOverride = currentIntent.value?.local_rag_override || {}

  const isEnabled = localOverride.enabled !== undefined ? localOverride.enabled : global.enabled

  if (!isEnabled) {
    return { enabled: false }
  }

  return {
    enabled: true,
    collection_name: localOverride.collection_name || global.collection_name,
    search_type: localOverride.search_type || global.search_type,
    top_k: localOverride.top_k !== undefined ? localOverride.top_k : global.top_k,
    context_format: localOverride.context_format || global.context_format,
    mock_corpus: localOverride.mock_corpus || global.mock_corpus || []
  }
})
</script>

<style scoped lang="scss">
.config-container { display: flex; flex-direction: column; gap: 24px; }

.header-info {
  background: #f8fafc; padding: 12px 16px; border-left: 3px solid #4f46e5;
  font-size: 13px; font-weight: 600; color: #475569;
}

.section { display: flex; flex-direction: column; gap: 10px; }

.section-title {
  font-size: 12px; font-weight: 800; color: #0f172a; text-transform: uppercase;
  letter-spacing: 0.05em; display: flex; align-items: center; gap: 8px;
}

.rag-badge {
  font-size: 10px; padding: 2px 6px; border-radius: 2px; font-weight: 800;
  &.is-active { background: #ecfccb; color: #4d7c0f; border: 1px solid #bef264; }
  &.is-disabled { background: #f1f5f9; color: #94a3b8; border: 1px solid #e2e8f0; }
}

.rag-grid, .params-grid { display: flex; gap: 12px; flex-wrap: wrap; }

.param-box {
  flex: 1; min-width: 120px; border: 1px solid #e2e8f0; padding: 12px; background: #fff;
  label { font-size: 11px; font-weight: 700; color: #64748b; display: block; margin-bottom: 6px; }
  .val { font-size: 14px; font-weight: 800; color: #4f46e5; font-family: 'JetBrains Mono', Consolas, monospace; }
}

/* Mock Corpus 渲染样式 */
.mock-list { display: flex; flex-direction: column; gap: 8px; margin-top: 6px; }
.mock-item {
  background: #f8fafc; border: 1px solid #e2e8f0; padding: 12px; border-left: 3px solid #10b981;
  font-family: 'JetBrains Mono', Consolas, monospace; font-size: 12px;
}
.mock-line {
  display: flex; align-items: flex-start; gap: 10px; margin-bottom: 8px;
  &:last-child { margin-bottom: 0; }
}
.mock-label {
  flex-shrink: 0; font-size: 10px; font-weight: 800; padding: 2px 6px; color: #fff; width: 64px; text-align: center; border-radius: 2px;
  &.input-label { background: #64748b; }
  &.en-label { background: #4f46e5; }
  &.zh-label { background: #0ea5e9; }
}
.mock-text { color: #334155; line-height: 1.5; padding-top: 1px; }

.disabled-hint {
  font-size: 12px; color: #64748b; background: #f8fafc; padding: 12px; border: 1px dashed #cbd5e1;
}

.mt-2 { margin-top: 8px; }

.code-block {
  font-family: 'JetBrains Mono', Consolas, monospace; font-size: 13px; line-height: 1.6;
  padding: 16px; white-space: pre-wrap; word-break: break-all;
  border: 1px solid #e2e8f0; background: #f8fafc; color: #334155;
}
.code-comment { color: #64748b; margin-bottom: 6px; font-weight: 600; font-size: 11px; }

.system-code { background: #0f172a; color: #38bdf8; border-color: #0f172a; .code-comment { color: #94a3b8; } }
.human-code { background: #f1f5f9; color: #475569; border-color: #cbd5e1; }
.context-code { color: #d97706; background: #fffbeb; border-color: #fde68a; .code-comment { color: #b45309; } }

.empty-hint { text-align: center; color: #94a3b8; padding: 40px 0; }

/* =========================================
   核心修复：限制 el-dialog 内容区最大高度与滚动条
   ========================================= */
.san-dialog :deep(.el-dialog) {
  border-radius: 0 !important;
  border: 1px solid var(--el-border-color) !important;
  box-shadow: 0 24px 80px rgba(0, 0, 0, 0.12), 0 0 0 1px rgba(79, 70, 229, 0.05) !important;
  margin-top: 10vh !important; /* 保证距离屏幕顶部有安全距离 */
}

.san-dialog :deep(.el-dialog__header) {
  border-bottom: 1px solid #e2e8f0 !important;
  padding: 16px 24px !important;
  margin-right: 0 !important;
}

.san-dialog :deep(.el-dialog__title) {
  font-weight: 900;
  letter-spacing: 0.06em;
  font-size: 15px;
  color: #0f172a;
}

/* 🌟 关键点：只限制 Body 的高度并触发内部滚动 */
.san-dialog :deep(.el-dialog__body) {
  padding: 24px !important;
  max-height: 60vh !important; /* 限制最高占屏幕高度的 60% */
  overflow-y: auto !important; /* 超出 60vh 后内部优雅滚动 */
}

/* 🌟 内部滚动条专属美化 (科技纤细风) */
.san-dialog :deep(.el-dialog__body)::-webkit-scrollbar {
  width: 6px;
}
.san-dialog :deep(.el-dialog__body)::-webkit-scrollbar-track {
  background: transparent;
}
.san-dialog :deep(.el-dialog__body)::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 3px;
}
.san-dialog :deep(.el-dialog__body)::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}
</style>