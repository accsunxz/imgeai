<template>
  <nav class="navbar sanryu-prestige">
    <div class="brand-group">
      <div class="logo-box">
        <Icon name="lucide:cpu" size="20" class="logo-icon" />
      </div>

      <div class="brand-info">
        <div class="title-row">
          <span class="app-name">Context Engine</span>
          <span class="version-tag">ENTERPRISE</span>
        </div>
        <span class="subtitle">中文语境 · 沉浸式原生化构建系统</span>
      </div>
    </div>

    <div class="system-tray">
      <div class="status-indicator" :class="userSettings.apiKey ? 'is-connected' : 'is-disconnected'">
        <div class="status-dot"></div>
        <span class="status-text">{{ userSettings.apiKey ? 'API CONNECTED' : 'KEY REQUIRED' }}</span>
      </div>

      <div class="tray-divider"></div>

      <button class="icon-trigger" type="button" @click="uiState.apiDialog = true" title="全局 API 设置">
        <Icon name="lucide:key" size="18" />
      </button>

      <button class="icon-trigger" type="button" @click="uiState.configDialog = true" title="查看底层配置">
        <Icon name="lucide:settings-2" size="18" />
      </button>
    </div>
  </nav>
</template>

<script setup lang="ts">
// 引入全局工作区状态（包含 UI 状态和本地持久化的用户配置）
const { uiState, userSettings } = useWorkspace()
</script>

<style scoped lang="scss">
.navbar {
  height: 60px; display: flex; justify-content: space-between; align-items: center;
  padding: 0 24px; background: rgba(255, 255, 255, 0.95); backdrop-filter: blur(16px);
  border-bottom: 1px solid #e4e4e7; user-select: none;
}

.brand-group { display: flex; align-items: center; gap: 14px; }
.logo-box {
  width: 34px; height: 34px; display: flex; align-items: center; justify-content: center;
  border-radius: 0; background: linear-gradient(135deg, #4f46e5 0%, #312e81 100%);
  color: #fff; box-shadow: 0 6px 16px rgba(79, 70, 229, 0.2);
}

.brand-info { display: flex; flex-direction: column; justify-content: center; gap: 2px; }
.title-row { display: flex; align-items: baseline; gap: 8px; }
.app-name { font-weight: 800; font-size: 16px; color: #09090b; letter-spacing: -0.01em; }
.version-tag { font-size: 10px; font-weight: 800; letter-spacing: 0.05em; padding: 2px 6px; background: #eef2ff; color: #4f46e5; }
.subtitle { font-size: 11px; color: #71717a; font-weight: 500; }

.system-tray { display: flex; align-items: center; height: 32px; gap: 4px; }
.tray-divider { width: 1px; height: 14px; background: #e4e4e7; margin: 0 12px; }

/* 在线 / 离线状态呼吸灯 */
.status-indicator {
  display: flex; align-items: center; gap: 8px; padding: 0 12px; height: 100%; border-radius: 4px; border: 1px solid transparent;

  &.is-connected {
    background: #ecfccb; border-color: #d9f99d;
    .status-dot { background: #65a30d; box-shadow: 0 0 8px rgba(101, 163, 13, 0.4); animation: pulse 2s infinite; }
    .status-text { color: #3f6212; }
  }

  &.is-disconnected {
    background: #fef2f2; border-color: #fecaca;
    .status-dot { background: #ef4444; }
    .status-text { color: #991b1b; }
  }
}

.status-dot { width: 6px; height: 6px; border-radius: 50%; }
.status-text { font-size: 11px; font-weight: 800; letter-spacing: 0.05em; }

@keyframes pulse {
  0% { box-shadow: 0 0 0 0 rgba(101, 163, 13, 0.4); }
  70% { box-shadow: 0 0 0 4px rgba(101, 163, 13, 0); }
  100% { box-shadow: 0 0 0 0 rgba(101, 163, 13, 0); }
}

/* 右侧图标按钮 */
.icon-trigger {
  width: 32px; height: 32px; display: flex; align-items: center; justify-content: center;
  background: transparent; border: 1px solid transparent; color: #71717a; cursor: pointer; border-radius: 0; transition: all 0.2s;
  &:hover { color: #4f46e5; background: #eef2ff; }
}
</style>