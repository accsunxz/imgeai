<template>
  <el-dialog
      v-model="uiState.apiDialog"
      title="全局 API 鉴权设置"
      width="480px"
      class="san-dialog"
      :close-on-click-modal="false"
  >
    <div class="settings-container">
      <div class="form-item">
        <label>SiliconFlow API Key</label>
        <el-input
            v-model="userSettings.apiKey"
            type="password"
            show-password
            placeholder="sk-..."
            class="custom-input"
        >
          <template #prefix>
            <Icon name="lucide:key" size="16" />
          </template>
        </el-input>
      </div>

      <div class="security-hint">
        <Icon name="lucide:shield-check" size="14" />
        您的 API 密钥仅加密保存在当前浏览器的本地缓存中，不会上传至任何云端服务器，保障绝对的资产安全。
      </div>
    </div>
  </el-dialog>
</template>

<script setup lang="ts">
const { uiState, userSettings } = useWorkspace()
</script>

<style scoped lang="scss">
.settings-container { display: flex; flex-direction: column; gap: 20px; }

.form-item {
  display: flex; flex-direction: column; gap: 8px;
  label { font-size: 12px; font-weight: 800; color: #0f172a; text-transform: uppercase; letter-spacing: 0.05em; }
}

.security-hint {
  display: flex; align-items: flex-start; gap: 8px;
  padding: 12px; background: #f0fdf4; border: 1px solid #bbf7d0; color: #166534;
  font-size: 12px; line-height: 1.6;
}

/* 覆盖 Element Input 圆角 */
.custom-input :deep(.el-input__wrapper) {
  border-radius: 0; box-shadow: 0 0 0 1px #e2e8f0 inset; padding: 4px 12px;
}
.custom-input :deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px #4f46e5 inset !important;
}

/* 弹窗零圆角极客风 */
.san-dialog :deep(.el-dialog) { border-radius: 0 !important; border: 1px solid var(--el-border-color) !important; box-shadow: 0 24px 80px rgba(0, 0, 0, 0.12) !important; margin-top: 20vh !important; }
.san-dialog :deep(.el-dialog__header) { border-bottom: 1px solid #e2e8f0 !important; padding: 16px 24px !important; margin-right: 0 !important; }
.san-dialog :deep(.el-dialog__title) { font-weight: 900; letter-spacing: 0.06em; font-size: 15px; color: #0f172a; }
.san-dialog :deep(.el-dialog__body) { padding: 24px !important; }
</style>