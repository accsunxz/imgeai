// composables/useWorkspace.ts
import { useState } from '#app'
import { computed } from 'vue'
import { useLocalStorage } from '@vueuse/core' // 🌟 引入持久化工具

export const useWorkspace = () => {
    // 1. 全局 UI 状态
    const uiState = useState('workspace_uiState', () => ({
        loading: false,
        configDialog: false, // 控制底层配置弹窗
        apiDialog: false     // 🌟 新增：控制 API Key 设置弹窗
    }))
    const result = useState<any>('workspace_result', () => null)

    // 🌟 2. 新增：用户私有配置 (保存在浏览器本地缓存)
    const userSettings = useLocalStorage('imgeai_user_settings', {
        apiKey: '' // 默认空
    })

    // 3. 场景数据与游标状态
    const scenes = useState<any[]>('workspace_scenes', () => [])
    const currentSceneId = useState<string>('workspace_scene_id', () => '')
    const currentIntentId = useState<string>('workspace_intent_id', () => '')
    const currentToneId = useState<string>('workspace_tone_id', () => '')

    // 4. 实时计算
    const currentScene = computed(() => scenes.value.find(s => s.id === currentSceneId.value))
    const currentIntents = computed(() => currentScene.value?.intents || [])
    const currentIntent = computed(() => currentIntents.value.find(i => i.id === currentIntentId.value))
    const currentTones = computed(() => currentIntent.value?.tones || [])
    const currentTone = computed(() => currentTones.value.find(t => t.id === currentToneId.value))

    return {
        uiState,
        result,
        userSettings, // 🌟 暴露出用户配置
        scenes,
        currentSceneId,
        currentIntentId,
        currentToneId,
        currentScene,
        currentIntents,
        currentIntent,
        currentTones,
        currentTone
    }
}