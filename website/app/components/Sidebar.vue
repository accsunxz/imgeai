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
                <span class="value">{{ currentToneLabel }}</span>
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
                  'is-loading': isLoading
                }"
                :disabled="!input || input.trim().length === 0 || isLoading"
                @click="handleGenerate"
            >
              <Icon
                  :name="isLoading ? 'lucide:loader-2' : 'lucide:sparkles'"
                  size="15"
                  class="btn-icon"
                  :class="{ 'spin': isLoading }"
              />
              <span class="btn-text">
                {{ isLoading ? '执行原生化重构...' : '立即生成' }}
              </span>
            </button>
          </div>
        </div>
      </section>
    </template>
  </aside>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { AgentApi } from '~/api/agent'

/**
 * @description 侧边栏组件脚本 - 采用 Prestige 风格逻辑
 * 对接后端 Res 类：数据存放在 body 字段，成功码判定为 0 或 '0000'
 */

const emit = defineEmits(['updateResult'])

// --- 1. UI 交互状态 ---
const isLoading = ref(false)
const isInputFocused = ref(false)
const input = ref('')

// --- 2. 状态游标 (IDs) ---
const currentSceneId = ref('')
const currentIntentId = ref('')
const currentToneId = ref('')

// --- 3. 数据拉取 (Nuxt 4 SSR 规范) ---
// 使用 useAsyncData 确保服务端拉取，避免客户端 Hydration 时的闪烁
const { data: apiResponse, status, error } = await useAsyncData(
    'agent-scenarios-config',
    () => AgentApi.getScenarios()
)

/**
 * 计算属性：从后端标准的 Res 结构中提取场景列表
 * 对齐后端：res.code (0/0000) & res.body
 */
const scenes = computed(() => {
  const res = apiResponse.value
  if (res && (res.code === 0 || res.code === '0000' || res.code === 200)) {
    return res.body || []
  }
  return []
})

// --- 4. 核心联动逻辑：数据映射 ---
const currentScene = computed(() => scenes.value.find(s => s.id === currentSceneId.value))
const currentIntents = computed(() => currentScene.value?.intents || [])
const currentIntent = computed(() => currentIntents.value.find(i => i.id === currentIntentId.value))
const currentTones = computed(() => currentIntent.value?.tones || [])

const currentToneLabel = computed(() => {
  const tone = currentTones.value.find(t => t.id === currentToneId.value)
  return tone ? tone.name : '标准直译'
})

// --- 5. 自动化默认值逻辑 (减少用户操作) ---

/**
 * 级联初始化：将游标指向各层级的第一个元素
 */
const resetToFirst = () => {
  if (scenes.value.length > 0) {
    // 默认选中第一个场景
    if (!currentSceneId.value) currentSceneId.value = scenes.value[0].id

    // 递归重置意图
    if (currentIntents.value.length > 0) {
      currentIntentId.value = currentIntents.value[0].id

      // 递归重置语气（默认为数组首位的“直译”）
      if (currentTones.value.length > 0) {
        currentToneId.value = currentTones.value[0].id
      }
    }
  }
}

// 监听数据就绪：当 SSR 数据注入或 API 返回后执行初始化
watch(scenes, (newVal) => {
  if (newVal.length > 0 && !currentSceneId.value) {
    resetToFirst()
  }
}, { immediate: true })

// --- 6. 交互处理方法 ---

const switchScene = (id: string) => {
  if (currentSceneId.value === id) return
  currentSceneId.value = id
  // 切换场景后，必须重置下级的意图和语气为默认值
  resetToFirst()
}

const switchIntent = (id: string) => {
  if (currentIntentId.value === id) return
  currentIntentId.value = id
  // 切换意图后，重置语气为第一个（直译）
  if (currentTones.value.length > 0) {
    currentToneId.value = currentTones.value[0].id
  }
}

/**
 * 核心执行：原生化文本重构
 */
const handleGenerate = async () => {
  // 基础防御：空内容或正在生成中则拦截
  if (!input.value.trim() || isLoading.value) return

  isLoading.value = true
  try {
    const res = await AgentApi.translate({
      scene_id: currentSceneId.value,
      intent_id: currentIntentId.value,
      tone_id: currentToneId.value,
      text: input.value
    })

    // 对齐后端 Res 成功逻辑
    if (res && (res.code === 0 || res.code === '0000')) {
      // 将执行结果 (body) 抛给父组件渲染结果展示区
      emit('updateResult', res.body)
    } else {
      console.error('转化失败:', res.message)
    }
  } catch (e) {
    console.error("AI Engine API Failure:", e)
  } finally {
    isLoading.value = false
  }
}

/**
 * 载入示例：增强用户直观感受
 */
const fillExample = () => {
  const examples: Record<string, string> = {
    reddit: '老板快下班了又临时加需求，烦死了。',
    email: '附件是本月的报告，有问题随时联系。',
    x_twitter: '这个 AI 工具简直逆天，生产力爆表。',
    facebook: '今天天气不错，一会去哪吃饭？'
  }
  input.value = examples[currentSceneId.value] || '我不小心把生产库删了，是不是要被开除了？'
}
</script>

<style scoped lang="scss">
/* Prestige Purple 核心视觉：零圆角、硬朗、深邃 */
.sidebar {
  width: 380px; height: 100%; display: flex; flex-direction: column;
  background: #ffffff; border-right: 1px solid var(--el-border-color);
  padding: 24px; gap: 20px; flex-shrink: 0; box-sizing: border-box;
}

.loading-overlay {
  flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center;
  gap: 12px; color: rgba(11,11,11,0.4); font-size: 13px;
}

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
  &.active {
    background: #fff; border-color: #4f46e5; color: #4f46e5; font-weight: 700;
    box-shadow: 0 8px 20px -4px rgba(79, 70, 229, 0.12);
  }
}

.active-corner {
  position: absolute; top: 0; right: 0; width: 0; height: 0;
  border-style: solid; border-width: 0 8px 8px 0; border-color: transparent #4f46e5 transparent transparent;
}

.monolith-wrapper {
  flex: 1; display: flex; flex-direction: column; min-height: 0;
  border: 1px solid var(--el-border-color); background: #fff; border-radius: 0;
  transition: all 0.3s ease;
  &.is-focused { border-color: #4f46e5; box-shadow: 0 0 0 1px #4f46e5, 0 12px 32px rgba(79, 70, 229, 0.08); }
}

.monolith-header {
  height: 42px; border-bottom: 1px solid var(--el-border-color); background: #fdfdfd;
  display: flex; align-items: center; justify-content: space-between; padding: 0 12px;
}

.tone-trigger {
  height: 100%; display: flex; align-items: center; gap: 8px; background: transparent; border: none;
  cursor: pointer; font-size: 13px;
  .prefix { font-weight: 500; color: rgba(11,11,11,0.4); font-size: 12px; }
  .divider-vertical { width: 1px; height: 12px; background: rgba(0,0,0,0.1); margin: 0 2px; }
  .value { font-weight: 700; color: #4f46e5; }
}

.tool-btn { background: transparent; border: none; cursor: pointer; color: rgba(11,11,11,0.5); font-size: 12px; }

.monolith-body { position: relative; flex: 1; display: flex; }
.stealth-input {
  width: 100%; height: 100%; resize: none; border: none; padding: 16px; padding-bottom: 64px;
  font-size: 14px; line-height: 1.7; outline: none;
}

.action-anchor { position: absolute; right: 16px; bottom: 16px; }
.unified-send-btn {
  display: flex; align-items: center; justify-content: center; gap: 8px; height: 40px; padding: 0 20px;
  border: none; background: #f3f4f6; color: rgba(11, 11, 11, 0.4); font-weight: 700; cursor: not-allowed;
  &.is-ready { background: #4f46e5; color: #fff; cursor: pointer; box-shadow: 0 8px 20px -4px rgba(79, 70, 229, 0.25); }
}

.spin { animation: rotate 1s linear infinite; }
@keyframes rotate { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }

.custom-dropdown :deep(.el-dropdown-menu__item) {
  border-radius: 0; font-size: 13px;
  &.is-active { color: #4f46e5; background: #f5f3ff; font-weight: 700; }
}
</style>