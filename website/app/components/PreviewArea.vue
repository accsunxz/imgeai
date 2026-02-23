<template>
  <main class="preview">
    <div v-if="!result && !uiState.loading" class="empty-state">
      <div class="watermark-icon">
        <Icon name="lucide:terminal-square" size="48" stroke-width="1.5" />
      </div>
      <h3 class="empty-title">系统待命</h3>
      <p class="empty-desc">请在左侧配置目标平台与意图，执行转化后在此查阅结果。</p>
    </div>

    <div v-else-if="uiState.loading" class="loading-state">
      <div class="pulse-line"></div>
      <el-skeleton animated :rows="6" />
    </div>

    <div v-else class="result-card">
      <div class="card-header">
        <div class="status-tag">
          <Icon name="lucide:check-circle-2" size="14" />
          <span>原生化重构</span>
        </div>
        <button class="action-btn" @click="copyText">
          <Icon name="lucide:copy" size="14" />
          <span>复制结果</span>
        </button>
      </div>

      <div class="card-body">
        <div class="primary-output">
          <div class="content-text font-mono">
            {{ result?.output_data?.english || result?.english || result?.text || displayRaw(result) }}
          </div>
        </div>

        <div v-if="result?.output_data?.chinese || result?.chinese || result?.explanation" class="secondary-output">
          <div class="section-label">
            <Icon name="lucide:quote" size="14" /> 语义对齐与注释
          </div>
          <p class="explanation-text">{{ result?.output_data?.chinese || result?.chinese || result?.explanation }}</p>
        </div>
      </div>
    </div>
  </main>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const workspace = useWorkspace()

const result = computed(() => workspace.result.value)
const uiState = computed(() => workspace.uiState.value)

const displayRaw = (data: any) => {
  if (!data) return ''
  return typeof data === 'string' ? data : JSON.stringify(data, null, 2)
}

const copyText = () => {
  if (!result.value) return

  const textToCopy =
      result.value.output_data?.english ||
      result.value.english ||
      result.value.text ||
      (typeof result.value === 'string' ? result.value : JSON.stringify(result.value))

  if (navigator.clipboard) {
    navigator.clipboard.writeText(textToCopy).then(() => {
      if (typeof window !== 'undefined' && window.ElMessage) {
        window.ElMessage.success('已复制到剪贴板')
      }
    })
  }
}
</script>

<style scoped lang="scss">
/* --- 布局底色 --- */
.preview {
  flex: 1;
  background: #f8fafc; /* 更清爽的极客灰白底色 */
  padding: 48px;
  overflow-y: auto;
  display: flex;
  justify-content: center;
  align-items: flex-start; /* 顶部对齐，防止内容少时居中显得奇怪 */
}

/* --- 空状态 (Empty State) --- */
.empty-state {
  margin-top: 12vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  user-select: none;

  .watermark-icon {
    color: #cbd5e1;
    margin-bottom: 24px;
  }

  .empty-title {
    font-size: 18px;
    font-weight: 800;
    color: #334155;
    margin: 0 0 8px 0;
    letter-spacing: 0.05em;
  }

  .empty-desc {
    font-size: 13px;
    color: #94a3b8;
    margin: 0;
  }
}

/* --- 加载状态 (Loading) --- */
.loading-state {
  width: 100%;
  max-width: 840px;
  padding: 40px;
  background: #fff;
  border-radius: 0;
  border: 1px solid #e2e8f0;
  position: relative;
  overflow: hidden;

  /* 顶部动态加载线 */
  .pulse-line {
    position: absolute;
    top: 0; left: 0; height: 2px; width: 30%;
    background: #4f46e5;
    animation: loading-slide 1.5s ease-in-out infinite;
  }
}

@keyframes loading-slide {
  0% { left: -30%; }
  100% { left: 100%; }
}

/* --- 结果展示卡片 (Result Card) --- */
.result-card {
  width: 100%;
  max-width: 840px;
  background: #fff;
  border-radius: 0;
  border: 1px solid #e2e8f0;
  /* 左侧科技紫强调线，提升工业感 */
  border-left: 4px solid #4f46e5;
  box-shadow: 0 20px 40px -8px rgba(0, 0, 0, 0.04);
}

/* --- 卡片头部 --- */
.card-header {
  padding: 16px 24px;
  border-bottom: 1px solid #f1f5f9;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #ffffff;

  .status-tag {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-size: 12px;
    font-weight: 800;
    color: #4f46e5;
    background: #eef2ff;
    padding: 4px 10px;
    border: 1px solid #c7d2fe;
    border-radius: 0; /* 零圆角 */
    letter-spacing: 0.05em;
  }
}

/* --- 操作按钮 --- */
.action-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: transparent;
  border: 1px solid #e2e8f0;
  color: #64748b;
  font-size: 12px;
  font-weight: 700;
  padding: 6px 14px;
  cursor: pointer;
  border-radius: 0;
  transition: all 0.2s cubic-bezier(0.25, 0.8, 0.25, 1);

  &:hover {
    background: #f8fafc;
    color: #4f46e5;
    border-color: #4f46e5;
    box-shadow: 0 2px 8px rgba(79, 70, 229, 0.1);
  }
}

/* --- 卡片内容区 --- */
.card-body {
  padding: 0; /* 移除外层 padding，通过内部区块控制 */
}

/* 核心输出：原生化英文 */
.primary-output {
  padding: 32px 32px 24px 32px;

  .content-text {
    font-size: 17px;
    line-height: 1.8;
    color: #0f172a;
    white-space: pre-wrap;
    font-family: 'JetBrains Mono', ui-monospace, SFMono-Regular, Consolas, monospace;
    font-weight: 500;
  }
}

/* 辅助输出：中文对照 (替代原先廉价的虚线框) */
.secondary-output {
  margin: 0 32px 32px 32px;
  padding: 16px 20px;
  background: #f8fafc; /* 浅灰底色区分层级 */
  border-left: 2px solid #cbd5e1; /* 左侧细灰线作为引用视觉 */

  .section-label {
    font-size: 12px;
    font-weight: 800;
    color: #64748b;
    margin-bottom: 8px;
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .explanation-text {
    margin: 0;
    font-size: 14px;
    color: #475569;
    line-height: 1.6;
  }
}
</style>