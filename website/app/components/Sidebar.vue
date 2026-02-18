<template>
  <aside class="sidebar sanryu-prestige">
    <section class="section-scenario">
      <div class="section-header">
        <span class="label">场景选择</span>
      </div>

      <div class="grid-menu">
        <div
            v-for="pb in playbooks"
            :key="pb.id"
            class="menu-item"
            :class="{ active: currentPbId === pb.id }"
            @click="currentPbId = pb.id"
        >
          <Icon
              :name="pb.mode === 'en2zh' ? 'lucide:languages' : 'lucide:layout-grid'"
              size="15"
          />
          <span class="menu-text">{{ pb.platformZh }}</span>

          <div v-if="currentPbId === pb.id" class="active-corner"></div>
        </div>
      </div>
    </section>

    <section class="monolith-wrapper" :class="{ 'is-focused': isInputFocused }">

      <div class="monolith-header">
        <el-dropdown trigger="click" @command="(val) => tone = val">
          <button class="tone-trigger" type="button">
            <span class="prefix">语气风格</span>
            <div class="divider-vertical"></div>
            <span class="value">{{ getToneLabel(tone) }}</span>
            <Icon name="lucide:chevron-down" size="12" class="icon-sub" />
          </button>

          <template #dropdown>
            <el-dropdown-menu class="custom-dropdown">
              <el-dropdown-item
                  v-for="t in playbook.tones"
                  :key="t.id"
                  :command="t.id"
                  :class="{ 'is-active': tone === t.id }"
              >
                {{ t.zh }}
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>

        <div class="header-tools">
          <button class="tool-btn" @click="input = playbook.placeholder" title="自动填入示例">
            <Icon name="lucide:wand-2" size="13" />
            <span>示例</span>
          </button>
        </div>
      </div>

      <div class="monolith-body">
        <textarea
            v-model="input"
            class="stealth-input"
            :placeholder="playbook.placeholder || '在此输入内容，AI 将为您生成...'"
            @focus="isInputFocused = true"
            @blur="isInputFocused = false"
            @keydown.enter.prevent="handleGenerate"
        ></textarea>

        <div class="action-anchor">
          <button
              class="unified-send-btn"
              :class="{
              'is-ready': input && input.trim().length > 0,
              'is-loading': uiState.loading
            }"
              :disabled="!input || input.trim().length === 0 || uiState.loading"
              @click="handleGenerate"
          >
            <Icon
                :name="uiState.loading ? 'lucide:loader-2' : 'lucide:sparkles'"
                size="15"
                class="btn-icon"
                :class="{ 'spin': uiState.loading }"
            />
            <span class="btn-text">
              {{ uiState.loading ? '正在生成...' : '立即生成' }}
            </span>
          </button>
        </div>
      </div>

    </section>
  </aside>
</template>

<script setup>
import { ref } from 'vue'
// 假设这是你的组合式函数
const { playbooks, currentPbId, playbook, input, tone, uiState, generate } = useWorkspace()

const isInputFocused = ref(false)

// 辅助函数：安全获取语气中文名
const getToneLabel = (id) => {
  if (!playbook.value || !playbook.value.tones) return id
  const t = playbook.value.tones.find(item => item.id === id)
  return t ? t.zh : id
}

const handleGenerate = () => {
  if (!input.value || !input.value.trim() || uiState.value.loading) return
  generate()
}
</script>

<style scoped lang="scss">
/* =========================================
   Global Layout & Reset
   ========================================= */
.sidebar {
  width: 380px;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #ffffff;
  border-right: 1px solid var(--el-border-color);
  padding: 24px;
  gap: 20px;
}

.label {
  font-size: 12px;
  font-weight: 700;
  color: rgba(11, 11, 11, 0.45);
  margin-bottom: 10px;
  display: block;
  user-select: none;
}

/* =========================================
   1. Scenario Grid (场景选择)
   ========================================= */
.grid-menu {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.menu-item {
  position: relative;
  display: flex;
  align-items: center;
  gap: 8px;
  height: 40px;
  padding: 0 12px;

  background: #f8fafc;
  border: 1px solid transparent;
  cursor: pointer;

  /* Prestige Design: 零圆角 */
  border-radius: 0;

  color: rgba(11, 11, 11, 0.7);
  font-size: 13px;
  font-weight: 500;
  user-select: none;

  transition: all 0.2s cubic-bezier(0.25, 0.8, 0.25, 1);

  /* Hover 态 */
  &:hover {
    background: #fff;
    border-color: rgba(11, 11, 11, 0.1);
    box-shadow: 0 4px 12px rgba(0,0,0,0.04);
    color: var(--el-color-primary);
  }

  /* 激活态 */
  &.active {
    background: #fff;
    border-color: var(--el-color-primary);
    color: var(--el-color-primary);
    font-weight: 700;
    box-shadow: 0 8px 20px -4px rgba(79, 70, 229, 0.12);
  }
}

/* 激活时的三角标 */
.active-corner {
  position: absolute;
  top: 0; right: 0;
  width: 0; height: 0;
  border-style: solid;
  border-width: 0 8px 8px 0;
  border-color: transparent var(--el-color-primary) transparent transparent;
}

/* =========================================
   2. The Monolith (集成控制台)
   ========================================= */
.monolith-wrapper {
  /* 核心布局：自动填满侧边栏剩余高度 */
  flex: 1;
  min-height: 0;

  display: flex;
  flex-direction: column;

  border: 1px solid var(--el-border-color);
  background: #fff;
  transition: border-color 0.3s ease, box-shadow 0.3s ease;

  /* 聚焦时的高端光晕 */
  &.is-focused {
    border-color: var(--el-color-primary);
    box-shadow: 0 0 0 1px var(--el-color-primary), 0 12px 32px rgba(79, 70, 229, 0.08);
  }
}

/* --- Header: 顶部工具栏 --- */
.monolith-header {
  height: 42px;
  border-bottom: 1px solid var(--el-border-color);
  background: #fdfdfd;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-right: 12px;
}

.tone-trigger {
  height: 100%;
  padding: 0 16px;
  background: transparent;
  border: none;
  border-right: 1px solid var(--el-border-color);
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  transition: background 0.2s;

  &:hover { background: #f3f4f6; }

  .prefix {
    font-weight: 500;
    color: rgba(11,11,11,0.4);
    font-size: 12px;
  }

  .divider-vertical {
    width: 1px;
    height: 12px;
    background: rgba(0,0,0,0.1);
    margin: 0 2px;
  }

  .value {
    font-weight: 700;
    color: var(--el-color-primary);
  }

  .icon-sub { color: rgba(11,11,11,0.3); }
}

.tool-btn {
  background: transparent;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 500;
  color: rgba(11,11,11,0.5);
  padding: 6px 10px;
  border-radius: 0;

  &:hover {
    color: var(--el-color-primary);
    background: var(--el-color-primary-light-9);
  }
}

/* --- Body: 输入框容器 --- */
.monolith-body {
  position: relative;
  flex: 1; /* 填满 Monolith 剩余部分 */
  display: flex;
}

.stealth-input {
  width: 100%;
  height: 100%;
  resize: none;
  border: none;
  background: transparent;
  padding: 16px;
  /* 底部预留空间给悬浮按钮，防止遮挡文字 */
  padding-bottom: 64px;

  font-family: inherit;
  font-size: 14px;
  line-height: 1.7;
  color: rgba(11,11,11,0.9);
  outline: none;

  &::placeholder {
    color: rgba(11,11,11,0.35);
  }
}

/* --- Anchor: 统一风格的触发器按钮 --- */
.action-anchor {
  position: absolute;
  right: 16px;
  bottom: 16px;
  z-index: 5;
}

.unified-send-btn {
  /* 基础结构 */
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;

  height: 40px;
  padding: 0 20px;

  border: none;
  border-radius: 0; /* Prestige 核心：零圆角 */

  /* 默认禁用的外观 */
  background: #f3f4f6;
  color: rgba(11, 11, 11, 0.4);
  cursor: not-allowed;

  font-size: 13px;
  font-weight: 700;
  /* 中文无需过大 letter-spacing */

  /* 顺滑的高端过渡 */
  transition:
      background 0.3s cubic-bezier(0.25, 0.8, 0.25, 1),
      color 0.3s cubic-bezier(0.25, 0.8, 0.25, 1),
      transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1),
      box-shadow 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);

  /* 图标初始透明度 */
  .btn-icon {
    opacity: 0.8;
    transition: opacity 0.3s;
  }

  /* ✅ 就绪态 (Ready)：输入了内容 */
  &.is-ready {
    background: var(--el-color-primary);
    color: #fff;
    cursor: pointer;
    box-shadow: 0 8px 20px -4px rgba(var(--el-color-primary-rgb), 0.25);

    .btn-icon { opacity: 1; }

    /* Hover: 颜色加深，整体上浮 */
    &:hover {
      background: var(--el-color-primary-dark-2);
      transform: translateY(-2px) scale(1.02);
      box-shadow: 0 12px 28px -4px rgba(var(--el-color-primary-rgb), 0.35);
    }

    /* Active: 触感反馈 */
    &:active {
      transform: translateY(0) scale(0.98);
      box-shadow: 0 4px 12px -2px rgba(var(--el-color-primary-rgb), 0.25);
    }
  }

  /* ✅ 加载态 (Loading) */
  &.is-loading {
    background: var(--el-color-primary-light-3);
    color: rgba(255,255,255,0.95);
    cursor: wait;
    transform: none !important;
    box-shadow: none !important;
  }
}

/* 旋转动画 */
.spin { animation: rotate 1s linear infinite; }
@keyframes rotate { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }

/* Dropdown 覆盖样式 */
.custom-dropdown :deep(.el-dropdown-menu__item) {
  border-radius: 0;
  font-size: 13px;
  font-weight: 500;

  &.is-active {
    color: var(--el-color-primary);
    background: var(--el-color-primary-light-9);
    font-weight: 700;
  }
}
</style>