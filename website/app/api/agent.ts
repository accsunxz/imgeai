// api/agent.ts
import { apiGet, apiPost } from '@/utils/api'

// 定义场景配置的类型，方便前端开发时获得代码补全
export interface Tone {
    id: string;
    name: string;
}

export interface Intent {
    id: string;
    name: string;
    tones: Tone[];
}

export interface Scene {
    id: string;
    name: string;
    icon: string;
    intents: Intent[];
}

export interface TranslatePayload {
    scene_id: string;
    intent_id: string;
    tone_id: string;
    text: string;
    api_key?: string;
}

export interface TranslateResult {
    english: string;
    chinese?: string;
    [key: string]: any;
}

/**
 * Agent 业务服务
 */
export const AgentApi = {
    /**
     * 获取全量场景结构化数据
     */
    async getScenarios() {
        return await apiGet<Scene[]>('/agent/scenarios')
    },

    /**
     * 执行原生化文本重构
     * @param payload 包含场景、意图、语气和文本的载荷
     */
    async translate(payload: TranslatePayload) {
        return await apiPost<TranslateResult>('/agent/translate', payload)
    }
}