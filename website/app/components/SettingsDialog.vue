<template>
  <el-dialog
      v-model="uiState.apiDialog"
      title="API 连接设置"
      width="520px"
      class="san-dialog"
      :close-on-click-modal="false"
  >
    <div class="form">
      <!-- API Key -->
      <div class="form-item">
        <div class="label">SiliconFlow API Key</div>
        <el-input
            v-model="apiKey"
            type="password"
            show-password
            placeholder="sk-..."
            class="w-100"
        />
        <div class="hint">用于请求 SiliconFlow 接口；仅存本地浏览器。</div>
      </div>

      <!-- Model Select (from API) -->
      <div class="form-item">
        <div class="label row-between">
          <span>模型选择（从接口获取）</span>
          <button
              type="button"
              class="link-btn"
              :disabled="!apiKey || modelsLoading"
              @click="refreshModels(true)"
          >
            {{ modelsLoading ? '拉取中…' : '刷新模型列表' }}
          </button>
        </div>

        <el-select
            v-model="model"
            class="w-100"
            placeholder="请选择模型"
            filterable
            clearable
            :disabled="!apiKey"
            :loading="modelsLoading"
            loading-text="正在拉取模型列表…"
            no-match-text="无匹配模型"
        >
          <template #prefix>
            <Icon name="lucide:cpu" size="16" />
          </template>

          <el-option
              v-for="m in models"
              :key="m.id"
              :label="m.id"
              :value="m.id"
          />
        </el-select>

        <div v-if="!apiKey" class="hint">先填写 Key，才能拉取可用模型。</div>
        <div v-else-if="modelsError" class="hint hint-warn">
          拉取失败：{{ modelsError }}
        </div>
        <div v-else class="hint">选择后会作为默认模型用于生成。</div>

        <!-- 可选：自定义 Model（推荐保留，防止接口列表异常时没法用） -->
        <div class="toggle-row">
          <el-switch v-model="useCustomModel" />
          <span class="toggle-text">使用自定义 Model ID</span>
        </div>

        <el-input
            v-if="useCustomModel"
            v-model="model"
            placeholder="例如：Qwen/Qwen2.5-72B-Instruct"
            class="w-100 mt-10"
        />
      </div>
    </div>

    <template #footer>
      <el-button @click="uiState.apiDialog = false">取消</el-button>
      <el-button type="primary" class="btn-primary" @click="saveAndClose">
        保存
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch } from "vue"

const {
  uiState,
  apiKey,
  model,
  models,
  modelsLoading,
  modelsError,
  refreshModels,
  saveSettings,
} = useWorkspace()

const useCustomModel = ref(false)

/** 打开弹窗时自动拉取模型列表 */
watch(
    () => uiState.value.apiDialog,
    (open) => {
      if (open && apiKey.value) refreshModels(false)
    }
)

/** Key 变化时：如果弹窗开着，就重新拉取 */
watch(
    () => apiKey.value,
    (k) => {
      if (uiState.value.apiDialog && k) refreshModels(true)
    }
)

function saveAndClose() {
  saveSettings()
  uiState.value.apiDialog = false
}
</script>

<style scoped lang="scss">
.w-100 { width: 100%; }
.mt-10 { margin-top: 10px; }
.row-between { display: flex; align-items: center; justify-content: space-between; gap: 12px; }

.form { padding-top: 4px; }
.form-item { margin-bottom: 18px; }

.label {
  margin-bottom: 8px;
  font-size: 12px;
  font-weight: 900;
  letter-spacing: 0.08em;
  color: rgba(11, 11, 11, 0.68);
  user-select: none;
}

.hint {
  margin-top: 8px;
  font-size: 12px;
  color: rgba(11, 11, 11, 0.55);
  line-height: 1.5;
}
.hint-warn { color: rgba(120, 53, 15, 0.78); }

.link-btn {
  border: 1px solid rgba(var(--el-color-primary-rgb), 0.18);
  background: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
  height: 28px;
  padding: 0 10px;
  border-radius: 0;
  cursor: pointer;
  font-size: 12px;
  font-weight: 900;
  letter-spacing: 0.06em;
}
.link-btn:disabled { opacity: 0.55; cursor: not-allowed; }

.toggle-row {
  margin-top: 10px;
  display: flex;
  align-items: center;
  gap: 10px;
}
.toggle-text {
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.02em;
  color: rgba(11, 11, 11, 0.72);
}

/* ✅ Dialog：零圆角 + 紫蓝阴影 */
.san-dialog :deep(.el-dialog) {
  border-radius: 0 !important;
  border: 1px solid var(--el-border-color) !important;
  box-shadow: 0 18px 60px rgba(var(--el-color-primary-rgb), 0.12) !important;
}
.san-dialog :deep(.el-dialog__header) {
  border-bottom: 1px solid rgba(15, 23, 42, 0.08) !important;
  padding: 16px 18px !important;
}
.san-dialog :deep(.el-dialog__title) {
  font-weight: 900;
  letter-spacing: 0.06em;
}
.san-dialog :deep(.el-dialog__body) { padding: 18px !important; }
.san-dialog :deep(.el-dialog__footer) {
  padding: 14px 18px 18px !important;
  border-top: 1px solid rgba(15, 23, 42, 0.08) !important;
}

/* 输入/下拉：零圆角 */
.san-dialog :deep(.el-input__wrapper),
.san-dialog :deep(.el-select__wrapper) {
  border-radius: 0 !important;
  box-shadow: none !important;
}

/* 主按钮更高端 */
:deep(.el-button--primary.btn-primary) {
  height: 46px;
  border-radius: 0 !important;
  font-weight: 900;
  letter-spacing: 0.08em;
  box-shadow: 0 12px 34px rgba(var(--el-color-primary-rgb), 0.14) !important;
}
</style>
