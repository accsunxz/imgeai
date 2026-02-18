<template>
  <el-dialog
      v-model="uiState.promptDialog"
      title="场景 Prompt 编辑"
      width="760px"
      class="san-dialog"
      :close-on-click-modal="false"
  >
    <div class="topbar">
      <div class="label">选择场景</div>
      <el-select v-model="promptEditPbId" class="w-100" @change="onChangePb">
        <template #prefix><Icon name="lucide:layers" size="16" /></template>
        <el-option
            v-for="pb in playbooks"
            :key="pb.id"
            :label="pb.platformZh"
            :value="pb.id"
        />
      </el-select>
    </div>

    <div class="hint">
      可用变量：<code>{{ "{{tone}}" }}</code> <code>{{ "{{input}}" }}</code> <code>{{ "{{context}}" }}</code>
      （你模板里写这些占位符，生成时会自动替换）
    </div>

    <el-tabs class="tabs">
      <el-tab-pane label="System（系统提示）">
        <el-input
            v-model="promptDraft.sys"
            type="textarea"
            :rows="10"
            resize="none"
            class="editor"
            placeholder="系统提示：定义角色、目标、输出格式等…"
        />
      </el-tab-pane>

      <el-tab-pane label="User（用户提示）">
        <el-input
            v-model="promptDraft.user"
            type="textarea"
            :rows="10"
            resize="none"
            class="editor"
            placeholder="用户提示：把输入/上下文拼装成你希望的结构…"
        />
      </el-tab-pane>
    </el-tabs>

    <template #footer>
      <div class="footer-row">
        <button class="link-btn" type="button" @click="resetPrompt">恢复默认</button>
        <div class="right">
          <el-button @click="uiState.promptDialog = false">取消</el-button>
          <el-button type="primary" class="btn-primary" @click="savePrompt">保存</el-button>
        </div>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { watch } from "vue"

const {
  uiState,
  playbooks,
  promptDraft,
  promptEditPbId,
  loadPromptDraft,
  savePrompt,
  resetPrompt,
  currentPbId,
} = useWorkspace()

// 打开弹窗时：默认加载当前场景
watch(
    () => uiState.value.promptDialog,
    (open) => {
      if (open) loadPromptDraft(currentPbId.value)
    }
)

function onChangePb(pbId: string) {
  loadPromptDraft(pbId)
}
</script>

<style scoped lang="scss">
.w-100 { width: 100%; }

.topbar {
  display: grid;
  grid-template-columns: 110px 1fr;
  gap: 12px;
  align-items: center;
  margin-bottom: 10px;
}

.label {
  font-size: 12px;
  font-weight: 900;
  letter-spacing: 0.08em;
  color: rgba(11, 11, 11, 0.68);
  user-select: none;
}

.hint {
  font-size: 12px;
  color: rgba(11, 11, 11, 0.55);
  margin: 8px 0 12px;
  line-height: 1.6;
}
.hint code {
  padding: 2px 6px;
  border-radius: 0;
  border: 1px solid rgba(var(--el-color-primary-rgb), 0.20);
  background: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
  font-weight: 900;
}

.tabs { margin-top: 6px; }

.editor :deep(.el-textarea__inner) {
  border-radius: 0 !important;
  border: 1px solid var(--el-border-color) !important;
  box-shadow: none !important;
  padding: 12px 12px !important;
  font-size: 13px;
  line-height: 1.65;
}
.editor :deep(.el-textarea__inner:hover) {
  border-color: rgba(var(--el-color-primary-rgb), 0.35) !important;
}
.editor :deep(.el-textarea__inner:focus) {
  border-color: var(--el-color-primary) !important;
  box-shadow: var(--san-focus-ring) !important;
}

.footer-row {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.right { display: inline-flex; gap: 10px; }

.link-btn {
  height: 30px;
  padding: 0 10px;
  border: 1px solid rgba(var(--el-color-primary-rgb), 0.18);
  background: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
  border-radius: 0;
  cursor: pointer;
  font-size: 12px;
  font-weight: 900;
  letter-spacing: 0.06em;
}

/* Dialog：零圆角 + 紫蓝阴影 */
.san-dialog :deep(.el-dialog) {
  border-radius: 0 !important;
  border: 1px solid var(--el-border-color) !important;
  box-shadow: 0 18px 60px rgba(var(--el-color-primary-rgb), 0.12) !important;
}
:deep(.el-input__wrapper),
:deep(.el-select__wrapper),
:deep(.el-tabs__item),
:deep(.el-button) {
  border-radius: 0 !important;
}
:deep(.el-button--primary.btn-primary) {
  height: 46px;
  border-radius: 0 !important;
  font-weight: 900;
  letter-spacing: 0.08em;
  box-shadow: 0 12px 34px rgba(var(--el-color-primary-rgb), 0.14) !important;
}
</style>
