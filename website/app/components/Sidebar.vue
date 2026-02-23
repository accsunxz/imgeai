<template>
  <aside class="sidebar sanryu-prestige">
    <div v-if="status === 'pending'" class="loading-overlay">
      <Icon name="lucide:loader-2" size="24" class="spin" />
      <span>正在同步引擎配置...</span>
    </div>

    <template v-else>
      <section class="config-panel">
        <div class="control-group">
          <label class="group-label">TARGET PLATFORM / 目标平台</label>
          <div class="scene-grid">
            <button
                v-for="scene in scenes"
                :key="scene.id"
                class="flat-btn"
                :class="{ active: currentSceneId === scene.id }"
                @click="switchScene(scene.id)"
            >
              <Icon :name="scene.icon || 'lucide:box'" size="14" class="btn-icon" />
              <span>{{ scene.name }}</span>
              <div v-if="currentSceneId === scene.id" class="active-corner"></div>
            </button>
          </div>
        </div>

        <div class="control-group">
          <label class="group-label">OBJECTIVE / 内容意图</label>
          <div class="intent-flex">
            <button
                v-for="intent in currentIntents"
                :key="intent.id"
                class="flat-btn intent-btn"
                :class="{ active: currentIntentId === intent.id }"
                @click="switchIntent(intent.id)"
            >
              {{ intent.name }}
            </button>
          </div>
        </div>
      </section>

      <section class="monolith-wrapper" :class="{ 'is-focused': isInputFocused }">
        <div class="monolith-header">
          <div class="header-selectors">
            <el-dropdown trigger="click" @command="(val) => currentToneId = val">
              <button class="tone-trigger" type="button">
                <span class="prefix">语气风格</span>
                <div class="divider-vertical"></div>
                <span class="value">{{ currentTone?.name || '标准直译' }}</span>
                <Icon name="lucide:chevron-down" size="12" class="icon-sub" />
              </button>
              <template #dropdown>
                <el-dropdown-menu class="custom-dropdown">
                  <el-dropdown-item
                      v-for="t in currentTones"
                      :key="t.id"
                      :command="t.id"
                      :class="{ 'is-active': currentToneId === t.id }"
                  >
                    {{ t.name }}
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>

          <div class="header-tools">
            <button class="tool-btn" @click="fillExample" title="载入原生语料示例">
              <Icon name="lucide:wand-2" size="13" />
              <span>示例</span>
            </button>
          </div>
        </div>

        <div class="monolith-body">
          <textarea
              v-model="input"
              class="stealth-input"
              placeholder="粘贴需要去 AI 味、地道化的内容..."
              @focus="isInputFocused = true"
              @blur="isInputFocused = false"
              @keydown.enter.exact.prevent="handleGenerate"
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
                {{ uiState.loading ? '执行原生化重构...' : '立即生成' }}
              </span>
            </button>
          </div>
        </div>
      </section>
    </template>
  </aside>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { AgentApi } from '~/api/agent'
import { ElMessage } from 'element-plus'

// 解构所有所需的全局状态
const {
  uiState, result, userSettings, scenes,
  currentSceneId, currentIntentId, currentToneId,
  currentScene, currentIntents, currentTones, currentTone
} = useWorkspace()

const isInputFocused = ref(false)
const input = ref('')

// 1. SSR 数据拉取
const { data: apiResponse, status } = await useAsyncData(
    'agent-scenarios-config',
    () => AgentApi.getScenarios()
)

watch(() => apiResponse.value, (res: any) => {
  if (res && (res.code === 0 || res.code === '0000' || res.code === 200)) {
    scenes.value = res.body || []
  }
}, { immediate: true })

// 2. 级联重置逻辑
const resetToFirst = () => {
  if (scenes.value.length > 0) {
    if (!currentSceneId.value) currentSceneId.value = scenes.value[0].id
    if (currentIntents.value.length > 0) {
      currentIntentId.value = currentIntents.value[0].id
      if (currentTones.value.length > 0) {
        currentToneId.value = currentTones.value[0].id
      }
    }
  }
}

watch(scenes, (newVal) => {
  if (newVal.length > 0 && !currentSceneId.value) resetToFirst()
}, { immediate: true })

const switchScene = (id: string) => {
  if (currentSceneId.value === id) return
  currentSceneId.value = id
  resetToFirst()
}

const switchIntent = (id: string) => {
  if (currentIntentId.value === id) return
  currentIntentId.value = id
  if (currentTones.value.length > 0) {
    currentToneId.value = currentTones.value[0].id
  }
}

// 3. 业务执行（含安全拦截）
const handleGenerate = async () => {
  if (!input.value.trim() || uiState.value.loading) return

  // 🌟 API Key 验证拦截
  if (!userSettings.value.apiKey) {
    ElMessage.warning('请先在顶部设置中配置 SiliconFlow API Key')
    uiState.value.apiDialog = true
    return
  }

  uiState.value.loading = true
  result.value = null

  try {
    const res = await AgentApi.translate({
      scene_id: currentSceneId.value,
      intent_id: currentIntentId.value,
      tone_id: currentToneId.value,
      text: input.value,
      api_key: userSettings.value.apiKey // 🌟 随请求发送到后端
    })

    if (res && (res.code === 0 || res.code === '0000' || res.code === 200)) {
      result.value = res.body || res.data
    } else {
      ElMessage.error(res.message || '生成异常')
    }
  } catch (e) {
    ElMessage.error('服务连接失败，请检查网络或后端引擎')
  } finally {
    uiState.value.loading = false
  }
}

const fillExample = () => {
  input.value = '老板快下班了又临时加需求，烦死了。'
}
</script>

<style scoped lang="scss">
/* 零圆角工业科技风 */
.sidebar { width: 380px; height: 100%; display: flex; flex-direction: column; background: #ffffff; border-right: 1px solid var(--el-border-color); padding: 24px; gap: 20px; flex-shrink: 0; box-sizing: border-box; }
.loading-overlay { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 12px; color: rgba(11,11,11,0.4); font-size: 13px; }
.config-panel { display: flex; flex-direction: column; gap: 20px; }
.control-group { display: flex; flex-direction: column; gap: 10px; }
.group-label { font-size: 11px; font-weight: 700; color: rgba(11, 11, 11, 0.45); text-transform: uppercase; }
.scene-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
.intent-flex { display: flex; flex-wrap: wrap; gap: 8px; }

.flat-btn {
  position: relative; display: flex; align-items: center; justify-content: center; gap: 8px;
  height: 38px; padding: 0 12px; background: #f8fafc; border: 1px solid transparent;
  border-radius: 0; color: rgba(11, 11, 11, 0.7); font-size: 13px; font-weight: 500;
  cursor: pointer; transition: all 0.2s;
  &:hover { background: #fff; border-color: rgba(11, 11, 11, 0.1); color: #4f46e5; }
  &.active { background: #fff; border-color: #4f46e5; color: #4f46e5; font-weight: 700; box-shadow: 0 8px 20px -4px rgba(79, 70, 229, 0.12); }
}
.active-corner { position: absolute; top: 0; right: 0; width: 0; height: 0; border-style: solid; border-width: 0 8px 8px 0; border-color: transparent #4f46e5 transparent transparent; }

.monolith-wrapper { flex: 1; display: flex; flex-direction: column; min-height: 0; border: 1px solid var(--el-border-color); background: #fff; border-radius: 0; transition: all 0.3s ease; &.is-focused { border-color: #4f46e5; box-shadow: 0 0 0 1px #4f46e5, 0 12px 32px rgba(79, 70, 229, 0.08); } }
.monolith-header { height: 42px; border-bottom: 1px solid var(--el-border-color); background: #fdfdfd; display: flex; align-items: center; justify-content: space-between; padding: 0 12px; }
.tone-trigger { height: 100%; display: flex; align-items: center; gap: 8px; background: transparent; border: none; cursor: pointer; font-size: 13px; .prefix { font-weight: 500; color: rgba(11,11,11,0.4); font-size: 12px; } .divider-vertical { width: 1px; height: 12px; background: rgba(0,0,0,0.1); margin: 0 2px; } .value { font-weight: 700; color: #4f46e5; } }
.tool-btn { background: transparent; border: none; cursor: pointer; color: rgba(11,11,11,0.5); font-size: 12px; }

.monolith-body { position: relative; flex: 1; display: flex; }
.stealth-input { width: 100%; height: 100%; resize: none; border: none; padding: 16px; padding-bottom: 64px; font-size: 14px; line-height: 1.7; outline: none; }

.action-anchor { position: absolute; right: 16px; bottom: 16px; }
.unified-send-btn {
  display: flex; align-items: center; justify-content: center; gap: 8px; height: 40px; padding: 0 20px;
  border: none; background: #f3f4f6; color: rgba(11, 11, 11, 0.4); font-weight: 700; cursor: not-allowed;
  &.is-ready { background: #4f46e5; color: #fff; cursor: pointer; box-shadow: 0 8px 20px -4px rgba(79, 70, 229, 0.25); }
}

.spin { animation: rotate 1s linear infinite; }
@keyframes rotate { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
.custom-dropdown :deep(.el-dropdown-menu__item) { border-radius: 0; font-size: 13px; &.is-active { color: #4f46e5; background: #f5f3ff; font-weight: 700; } }
</style>