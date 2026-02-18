<template>
  <nav class="navbar sanryu-prestige">
    <div class="brand-group">
      <div class="logo-box">
        <Icon name="lucide:cpu" size="20" class="logo-icon" />
      </div>

      <div class="brand-info">
        <div class="title-row">
          <span class="app-name">ImgeAI</span>
          <span class="version-tag">WORKSPACE</span>
        </div>
        <span class="subtitle">中文语境 · 沉浸式场景构建系统</span>
      </div>
    </div>

    <div class="system-tray">

      <button
          type="button"
          class="status-indicator"
          :class="{ 'is-connected': apiKey }"
          @click="uiState.apiDialog = true"
          title="点击配置 API Key"
      >
        <div class="status-dot"></div>
        <span class="status-text">{{ apiKey ? 'SYSTEM ONLINE' : 'API DISCONNECTED' }}</span>
      </button>

      <div class="tray-divider"></div>

      <el-dropdown trigger="click" popper-class="custom-dropdown-popper">
        <button class="icon-trigger" type="button">
          <Icon name="lucide:settings-2" size="18" />
        </button>

        <template #dropdown>
          <el-dropdown-menu class="custom-dropdown">
            <el-dropdown-item @click="uiState.apiDialog = true">
              <Icon name="lucide:key" class="icon-fix" />
              API 连接设置
            </el-dropdown-item>
            <el-dropdown-item @click="uiState.kwDialog = true">
              <Icon name="lucide:filter" class="icon-fix" />
              关键词过滤
            </el-dropdown-item>
            <el-dropdown-item @click="uiState.promptDialog = true">
              <Icon name="lucide:pen-tool" class="icon-fix" />
              场景预设管理
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </nav>
</template>

<script setup>
const { apiKey, uiState } = useWorkspace()
</script>

<style scoped lang="scss">
/* =========================================
   Global Navbar Structure
   ========================================= */
.navbar {
  height: 60px; /* 稍微压低高度，更显精致 */
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 24px;

  /* 玻璃拟态背景，保持通透感 */
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(16px);
  border-bottom: 1px solid var(--el-border-color);

  user-select: none;
}

/* =========================================
   1. Brand Group
   ========================================= */
.brand-group {
  display: flex;
  align-items: center;
  gap: 14px;
}

.logo-box {
  width: 34px;
  height: 34px;
  display: flex;
  align-items: center;
  justify-content: center;

  /* 零圆角，硬朗科技风 */
  border-radius: 0;

  /* 深邃的科技蓝紫渐变 */
  background: linear-gradient(135deg, #4f46e5 0%, #312e81 100%);
  color: #fff;
  box-shadow: 0 6px 16px rgba(79, 70, 229, 0.2);
}

.brand-info {
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 2px;
}

.title-row {
  display: flex;
  align-items: baseline;
  gap: 8px;
}

.app-name {
  font-family: system-ui, -apple-system, sans-serif;
  font-weight: 800;
  font-size: 16px;
  color: #111;
  letter-spacing: -0.01em;
}

.version-tag {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.05em;
  padding: 1px 5px;
  background: #f1f5f9;
  color: rgba(11,11,11,0.5);
  border: 1px solid transparent;
}

.subtitle {
  font-size: 11px;
  color: rgba(11, 11, 11, 0.45);
  font-weight: 500;
}

/* =========================================
   2. System Tray (右侧功能区)
   ========================================= */
.system-tray {
  display: flex;
  align-items: center;
  height: 32px; /* 统一高度 */
  gap: 4px;     /* 元素间距 */

  /* 这里的背景可以选填，目前保持透明 */
}

.tray-divider {
  width: 1px;
  height: 14px;
  background: var(--el-border-color);
  margin: 0 12px;
}

/* --- API Status Indicator --- */
.status-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 8px;
  height: 100%;

  background: transparent;
  border: 1px solid transparent;
  border-radius: 0;
  cursor: pointer;

  transition: all 0.2s ease;

  &:hover {
    background: #f8fafc;
  }
}

.status-dot {
  width: 6px;
  height: 6px;
  background: #9ca3af; /* 默认灰色 (Disconnected) */
  border-radius: 50%; /* 圆点保持圆形，除非你想做成方块像素点 */
  box-shadow: 0 0 0 0 rgba(0,0,0,0);
  transition: all 0.3s;
}

.status-text {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.05em;
  color: #6b7280; /* 默认灰色字 */
}

/* Connected State (Online) */
.status-indicator.is-connected {
  .status-dot {
    background: #10b981; /* 科技绿，或者是你的主色 purple */
    box-shadow: 0 0 8px rgba(16, 185, 129, 0.4);
    animation: pulse 2s infinite;
  }

  .status-text {
    color: #111; /* 连接后文字变黑，更清晰 */
  }

  &:hover {
    background: rgba(16, 185, 129, 0.06); /* 微微的绿色背景 hover */
  }
}

/* --- Settings Trigger --- */
.icon-trigger {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;

  background: transparent;
  border: 1px solid transparent;
  color: rgba(11,11,11,0.6);
  cursor: pointer;
  border-radius: 0;

  transition: all 0.2s;

  &:hover {
    color: var(--el-color-primary);
    background: var(--el-color-primary-light-9);
  }
}

/* 呼吸灯动画 */
@keyframes pulse {
  0% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.4); }
  70% { box-shadow: 0 0 0 4px rgba(16, 185, 129, 0); }
  100% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
}

/* Dropdown Menu 覆盖 (保持你喜欢的零圆角风格) */
.icon-fix { margin-right: 8px; vertical-align: middle; opacity: 0.7; }

:global(.custom-dropdown-popper .el-dropdown-menu) {
  border-radius: 0 !important;
  border: 1px solid var(--el-border-color) !important;
  box-shadow: 0 16px 40px rgba(0,0,0,0.08) !important;
  padding: 4px 0 !important;
}

:global(.custom-dropdown-popper .el-dropdown-menu__item) {
  border-radius: 0 !important;
  margin: 0 !important;
  height: 36px;
  line-height: 36px;
  font-size: 12px;
  font-weight: 600;
  color: rgba(11,11,11,0.7);
}

:global(.custom-dropdown-popper .el-dropdown-menu__item:hover) {
  background: var(--el-color-primary-light-9) !important;
  color: var(--el-color-primary) !important;
}
</style>