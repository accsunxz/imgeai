import { ref, computed, onMounted, watch } from "vue"
import { ElMessage } from "element-plus"

// === 1. 类型定义 ===
export type Tone = { id: string; zh: string }
export type Playbook = {
    id: string
    platformZh: string
    mode: "en2zh" | "zh2en" | "zh2zh"
    tones: Tone[]
    maxOutputTokens: number
    placeholder: string
    contextHint: string
}

export type AdvConfig = {
    mustKeywords: string[]
    avoidWords: string[]
    strength: number
    profileName: string
}

export type PromptTpl = { sys: string; user: string }

export type GenerateResult = {
    labelZh: string
    toneZh: string
    text: string
    explanation: string
    fromCache?: boolean
    raw?: boolean
}

// === 2. 静态常量配置 ===
const SF_BASE = "https://api.siliconflow.cn/v1"
const LS_KEYS = {
    KEY: "imgeai_sf_key_ep_v1",
    MODEL: "imgeai_sf_model_ep_v1",
    CACHE_ENABLED: "imgeai_cache_enabled_ep_v1",
    CACHE: "imgeai_cache_ep_v1",
    ADV: "imgeai_adv_ep_v1",
    ADV_PROFILES: "imgeai_adv_profiles_ep_v1",
    TPLS: "imgeai_prompt_tpls_ep_v1",
}

const PLAYBOOKS: Playbook[] = [
    { id: 'en2zh_understand', platformZh: '英文理解', tones: [{ id: 'natural', zh: '自然解释' }, { id: 'literal', zh: '逐句直译' }, { id: 'bullets', zh: '要点总结' }], mode: 'en2zh', maxOutputTokens: 650, placeholder: '例如：I’m circling back on the proposal...', contextHint: '例如：邮件/合同场景、你关心的点…' },
    { id: 'amazon_listing', platformZh: 'Amazon Listing', tones: [{ id: 'conversion', zh: '高转化' }, { id: 'compliant', zh: '合规克制' }, { id: 'premium', zh: '高端质感' }], mode: 'zh2en', maxOutputTokens: 900, placeholder: '例如：折叠水壶，食品级硅胶，耐高温…', contextHint: '类目、目标人群、参数规格…' },
    { id: 'email_cold', platformZh: 'Cold Email', tones: [{ id: 'direct', zh: '开门见山' }, { id: 'warm', zh: '温暖亲和' }, { id: 'executive', zh: '高管对话' }], mode: 'zh2en', maxOutputTokens: 820, placeholder: '例如：给客户推销SEO服务，约个10分钟…', contextHint: '接收人职位、你的价值点…' },
    { id: 'reddit_help', platformZh: 'Reddit 帖子', tones: [{ id: 'neutral', zh: '清晰直接' }, { id: 'humble', zh: '谦逊礼貌' }, { id: 'confident', zh: '专业讨论' }], mode: 'zh2en', maxOutputTokens: 520, placeholder: '例如：SaaS注册率不错但留存很差…', contextHint: '板块/受众、你想要的具体建议…' },
    { id: 'facebook_group', platformZh: 'Facebook 群组', tones: [{ id: 'community', zh: '热心分享' }, { id: 'narrative', zh: '故事感' }, { id: 'expert', zh: '专家建议' }], mode: 'zh2en', maxOutputTokens: 420, placeholder: '例如：发现个好工具想推荐给大家…', contextHint: '强调无利益相关、引发讨论…' },
    { id: 'ig_caption', platformZh: 'Instagram 文案', tones: [{ id: 'aesthetic', zh: '氛围感' }, { id: 'friendly', zh: '像朋友' }, { id: 'influencer', zh: '种草风' }], mode: 'zh2en', maxOutputTokens: 320, placeholder: '例如：海边日落，心情很放松…', contextHint: 'emoji 风格、是否加标签…' },
    { id: 'x_build', platformZh: 'X / Twitter', tones: [{ id: 'punchy', zh: '短促有力' }, { id: 'calm', zh: '冷静克制' }, { id: 'provocative', zh: '犀利观点' }], mode: 'zh2en', maxOutputTokens: 280, placeholder: '例如：AI不会取代人，会用AI的人才会…', contextHint: '数据支持、呼吁行动…' }
]

// === 3. 工具函数 ===
// FNV1a Hash 算法 (用于缓存 Key)
function fnv1a(str: string) {
    let h = 0x811c9dc5
    for (let i = 0; i < str.length; i++) {
        h ^= str.charCodeAt(i)
        h = (h + ((h << 1) + (h << 4) + (h << 7) + (h << 8) + (h << 24))) >>> 0
    }
    return ('00000000' + h.toString(16)).slice(-8)
}

// 简单的模板替换 {{key}}
function renderTpl(tpl: string, vars: Record<string, any>) {
    return (tpl || '').replace(/\{\{\s*([a-zA-Z0-9_]+)\s*\}\}/g, (_, k) => {
        const v = vars[k]
        return (v === undefined || v === null) ? '' : String(v)
    })
}

export const useWorkspace = () => {
    // === 4. 核心状态 (State) ===
    // 设置相关
    const apiKey = useState<string>('imgeai_apiKey', () => '')
    const model = useState<string>('imgeai_model', () => 'Qwen/Qwen2.5-72B-Instruct')
    const cacheEnabled = useState<boolean>('imgeai_cacheEnabled', () => true)

    // 界面状态
    const uiState = useState('imgeai_uiState', () => ({
        apiDialog: false,
        kwDialog: false,
        promptDialog: false,
        payloadDialog: false, // 查看 payload
        profilesDialog: false, // 关键词配置集
        showContext: false,
        loading: false,
        loadingModels: false, // 拉取模型列表 loading
    }))

    // 工作区数据
    const currentPbId = useState<string>('imgeai_currentPbId', () => PLAYBOOKS[0].id)
    const tone = useState<string>('imgeai_tone', () => 'natural')
    const lengthLevel = useState<number>('imgeai_lengthLevel', () => 1) // 0:短, 1:中, 2:长
    const input = useState<string>('imgeai_input', () => '')
    const context = useState<string>('imgeai_context', () => '')
    const result = useState<GenerateResult | null>('imgeai_result', () => null)

    // 关键词高级配置
    const adv = useState<AdvConfig>('imgeai_adv', () => ({
        mustKeywords: [],
        avoidWords: [],
        strength: 1,
        profileName: 'default'
    }))
    const profiles = useState<Record<string, AdvConfig>>('imgeai_profiles', () => ({
        default: { mustKeywords: [], avoidWords: [], strength: 1, profileName: 'default' }
    }))

    // Prompt 模板
    const tpls = useState<Record<string, PromptTpl>>('imgeai_tpls', () => ({}))

    // 模型列表缓存
    const modelList = useState<string[]>('imgeai_modelList', () => [])

    // 编辑器临时状态
    const promptEditPbId = useState('imgeai_promptEditPbId', () => PLAYBOOKS[0].id)
    const promptDraft = useState('imgeai_promptDraft', () => ({ sys: '', user: '' }))

    // === 5. 计算属性 (Computed) ===
    const playbook = computed(() => PLAYBOOKS.find(p => p.id === currentPbId.value) || PLAYBOOKS[0])

    const lengthLabelZh = computed(() => ['短', '中', '长'][lengthLevel.value] || '中')

    const keywordRulesText = computed(() => {
        const { mustKeywords, avoidWords, strength } = adv.value
        const sStr = ['弱', '中', '强'][strength] || '中'
        return `关键词规则（内部）：\n- 必须包含：${mustKeywords.join('、') || '（无）'}\n- 避免出现：${avoidWords.join('、') || '（无）'}\n- 强度：${sStr}`
    })

    const reservedCompletionTokens = computed(() => {
        const cap = playbook.value.maxOutputTokens || 300
        const mult = [0.55, 0.85, 1.15][lengthLevel.value] || 0.85
        return Math.ceil(cap * mult)
    })

    // === 6. 初始化与持久化 (Lifecycle) ===
    onMounted(() => {
        // 加载 LocalStorage
        apiKey.value = localStorage.getItem(LS_KEYS.KEY) || ''
        model.value = localStorage.getItem(LS_KEYS.MODEL) || 'Qwen/Qwen2.5-72B-Instruct'
        cacheEnabled.value = localStorage.getItem(LS_KEYS.CACHE_ENABLED) !== '0'

        try { adv.value = JSON.parse(localStorage.getItem(LS_KEYS.ADV) || '') || adv.value } catch { }
        try { profiles.value = JSON.parse(localStorage.getItem(LS_KEYS.ADV_PROFILES) || '') || profiles.value } catch { }
        try { tpls.value = JSON.parse(localStorage.getItem(LS_KEYS.TPLS) || '{}') || {} } catch { }

        ensurePromptDefaults()
    })

    // === 7. 核心逻辑方法 ===

    // --- API 设置 ---
    function saveSettings(key: string, mod: string, cache: boolean) {
        apiKey.value = key.trim()
        model.value = mod.trim()
        cacheEnabled.value = cache
        localStorage.setItem(LS_KEYS.KEY, apiKey.value)
        localStorage.setItem(LS_KEYS.MODEL, model.value)
        localStorage.setItem(LS_KEYS.CACHE_ENABLED, cache ? '1' : '0')
        ElMessage.success('设置已保存')
    }

    async function fetchModels() {
        if (!apiKey.value) return ElMessage.warning('请先配置 API Key')
        uiState.value.loadingModels = true
        try {
            const res = await fetch(`${SF_BASE}/models?sub_type=chat`, {
                headers: { Authorization: `Bearer ${apiKey.value}` }
            })
            const json = await res.json()
            modelList.value = (json.data || []).map((x: any) => x.id)
            ElMessage.success(`加载了 ${modelList.value.length} 个模型`)
        } catch (e) {
            ElMessage.error('模型列表加载失败')
        } finally {
            uiState.value.loadingModels = false
        }
    }

    // --- 关键词管理 ---
    function addKw(type: 'must' | 'avoid', text: string) {
        const list = text.split(/[,，\n]/).map(s => s.trim()).filter(Boolean)
        if (!list.length) return
        const target = type === 'must' ? adv.value.mustKeywords : adv.value.avoidWords
        const merged = [...new Set([...target, ...list])]
        if (type === 'must') adv.value.mustKeywords = merged
        else adv.value.avoidWords = merged
        persistAdv()
    }

    function removeKw(type: 'must' | 'avoid', index: number) {
        if (type === 'must') adv.value.mustKeywords.splice(index, 1)
        else adv.value.avoidWords.splice(index, 1)
        persistAdv()
    }

    function persistAdv() {
        localStorage.setItem(LS_KEYS.ADV, JSON.stringify(adv.value))
    }

    function saveProfile(name: string) {
        adv.value.profileName = name
        profiles.value[name] = JSON.parse(JSON.stringify(adv.value))
        localStorage.setItem(LS_KEYS.ADV_PROFILES, JSON.stringify(profiles.value))
        persistAdv()
        ElMessage.success(`配置集 "${name}" 已保存`)
    }

    function loadProfile(name: string) {
        if (!profiles.value[name]) return
        adv.value = JSON.parse(JSON.stringify(profiles.value[name]))
        persistAdv()
        ElMessage.success('配置集已加载')
    }

    // --- Prompt 模板引擎 ---
    function safeJsonObjSpec(toneZh: string) {
        return `严格要求：只输出一个 JSON 对象（不要数组/不要Markdown/不要代码块）。\n对象结构：\n{ "labelZh":"结果", "toneZh":"${toneZh}", "text":"", "explanation":"" }\n只允许返回合法 JSON。`
    }

    function defaultPromptFor(pb: Playbook): PromptTpl {
        const toneObj = pb.tones.find(t => t.id === tone.value) || pb.tones[0]
        const toneZh = toneObj?.zh || '默认'

        if (pb.mode === 'en2zh') {
            return {
                sys: `你是一个严谨的双语助手，擅长把英文内容解释成中文用户容易理解的表达。\n${safeJsonObjSpec(toneZh)}\n输出语言：中文。\n风格：{{toneZh}}。\n要求：准确、清晰、不瞎猜。`,
                user: `任务：把英文解释/翻译成中文（按当前风格输出）。\n英文原文：\n{{input}}\n\n补充上下文（可选）：\n{{context}}`
            }
        }
        return {
            sys: `你是一位资深文案编辑，面向真实用户写作，避免“AI味”。\n${safeJsonObjSpec(toneZh)}\n平台：{{platformZh}}\n语气：{{toneZh}}\n长度：{{lengthLabelZh}}\n{{keywordRules}}\n{{formatHint}}`,
            user: `中文输入：\n{{input}}\n\n补充上下文（可选）：\n{{context}}`
        }
    }

    function ensurePromptDefaults() {
        PLAYBOOKS.forEach(pb => {
            if (!tpls.value[pb.id]) {
                tpls.value[pb.id] = defaultPromptFor(pb)
            }
        })
    }

    function loadPromptDraft() {
        const id = promptEditPbId.value
        // 如果没有模板，生成默认
        if (!tpls.value[id]) tpls.value[id] = defaultPromptFor(PLAYBOOKS.find(p => p.id === id)!)
        promptDraft.value = { ...tpls.value[id] }
    }

    function savePromptTemplate() {
        tpls.value[promptEditPbId.value] = { ...promptDraft.value }
        localStorage.setItem(LS_KEYS.TPLS, JSON.stringify(tpls.value))
        ElMessage.success('Prompt 模板已保存')
    }

    function resetPromptToDefault() {
        const pb = PLAYBOOKS.find(p => p.id === promptEditPbId.value)!
        const def = defaultPromptFor(pb)
        promptDraft.value = def
        ElMessage.info('已重置为默认值（需点击保存）')
    }

    // --- 构建 Payload (关键) ---
    function buildPayload() {
        const pb = playbook.value
        const toneObj = pb.tones.find(t => t.id === tone.value) || pb.tones[0]

        // 准备变量
        const vars = {
            toneZh: toneObj.zh,
            toneId: tone.value,
            lengthLabelZh: lengthLabelZh.value,
            platformZh: pb.platformZh,
            mode: pb.mode,
            keywordRules: keywordRulesText.value,
            formatHint: pb.id === 'amazon_listing' ? '输出格式建议：Title、Bullet Points、Description。' : '',
            input: input.value,
            context: context.value
        }

        // 获取或回退模板
        const tpl = tpls.value[pb.id] || defaultPromptFor(pb)

        // 渲染
        const sysMsg = renderTpl(tpl.sys, vars)
        const userMsg = renderTpl(tpl.user, vars)

        return {
            model: model.value,
            messages: [
                { role: 'system', content: sysMsg },
                { role: 'user', content: userMsg }
            ],
            max_tokens: reservedCompletionTokens.value,
            temperature: pb.mode === 'en2zh' ? 0.35 : 0.7
        }
    }

    // --- 缓存逻辑 ---
    const CACHE_TTL = 7 * 24 * 3600 * 1000 // 7天
    function getCacheStore() {
        try { return JSON.parse(localStorage.getItem(LS_KEYS.CACHE) || '{"items":{}}') }
        catch { return { items: {} } }
    }

    function saveToCache(key: string, data: GenerateResult) {
        if (!cacheEnabled.value) return
        const store = getCacheStore()
        store.items[key] = { ts: Date.now(), data }

        // 简单清理：超过40条删掉旧的
        const keys = Object.keys(store.items)
        if (keys.length > 40) {
            keys.sort((a, b) => (store.items[b].ts || 0) - (store.items[a].ts || 0))
            const keep = keys.slice(0, 40)
            const nextItems: any = {}
            keep.forEach(k => nextItems[k] = store.items[k])
            store.items = nextItems
        }

        localStorage.setItem(LS_KEYS.CACHE, JSON.stringify(store))
    }

    // --- 核心生成方法 ---
    async function generate() {
        if (!apiKey.value) {
            uiState.value.apiDialog = true
            return ElMessage.warning('请配置 API Key')
        }
        if (!input.value.trim()) return

        uiState.value.loading = true
        result.value = null

        try {
            const payload = buildPayload()

            // 1. 计算 Cache Key (包含所有影响因子的 Hash)
            const seed = JSON.stringify({
                ...payload,
                adv: adv.value,
                pb: currentPbId.value
            })
            const cacheKey = fnv1a(seed)

            // 2. 查缓存
            if (cacheEnabled.value) {
                const store = getCacheStore()
                const hit = store.items[cacheKey]
                if (hit && (Date.now() - hit.ts < CACHE_TTL)) {
                    result.value = { ...hit.data, fromCache: true }
                    uiState.value.loading = false
                    return
                }
            }

            // 3. 请求 API
            const res = await fetch(`${SF_BASE}/chat/completions`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${apiKey.value}`,
                },
                body: JSON.stringify(payload),
            })

            const json = await res.json()
            if (json.error) throw new Error(json.error.message)

            // 4. 解析结果
            let rawContent = json.choices?.[0]?.message?.content || ''
            // 清理 Markdown 代码块
            rawContent = rawContent.replace(/^```json\s*/i, '').replace(/^```\s*/i, '').replace(/```$/i, '').trim()

            let parsed: GenerateResult
            try {
                const obj = JSON.parse(rawContent)
                // 兼容数组或对象
                const one = Array.isArray(obj) ? obj[0] : obj
                parsed = {
                    labelZh: one.labelZh || '结果',
                    toneZh: one.toneZh || '',
                    text: one.text || one.content || rawContent,
                    explanation: one.explanation || '',
                    raw: false
                }
            } catch (e) {
                // 解析失败，回退到原文显示
                parsed = {
                    labelZh: 'Raw',
                    toneZh: 'Unknown',
                    text: rawContent,
                    explanation: '未能解析为标准 JSON，显示原始结果。',
                    raw: true
                }
            }

            // 5. 存缓存并显示
            result.value = parsed
            saveToCache(cacheKey, parsed)

        } catch (e: any) {
            ElMessage.error(e.message || '生成请求失败')
        } finally {
            uiState.value.loading = false
        }
    }

    // 示例一键填入
    function diceRoll() {
        const examples: Record<string, string> = {
            en2zh_understand: 'I’m circling back on the proposal and wanted to clarify the timeline...',
            amazon_listing: '便携折叠水壶，食品级硅胶，耐高温，适合露营和旅行。',
            email_cold: '给潜在客户推销SEO服务，想约个10分钟电话沟通。',
            reddit_help: 'SaaS注册率不错但留存很差，可能是什么原因？',
            facebook_group: '想在群里分享一个对跨境卖家有用的小工具。',
            ig_caption: '海边日落，风很温柔，今天状态很好。',
            x_build: 'AI不会取代人，会用AI的人才会。'
        }
        input.value = examples[currentPbId.value] || '...'
    }

    // 计算属性：当前 Payload JSON (用于展示)
    const promptPayloadJson = computed(() => JSON.stringify(buildPayload(), null, 2))

    return {
        // State
        apiKey, model, cacheEnabled, modelList,
        uiState,
        playbooks: PLAYBOOKS,
        currentPbId, playbook,
        tone, lengthLevel, lengthLabelZh, reservedCompletionTokens,
        input, context, result,
        adv, profiles, keywordRulesText,
        promptDraft, promptEditPbId, promptPayloadJson,

        // Actions
        saveSettings, fetchModels,
        addKw, removeKw, saveProfile, loadProfile,
        loadPromptDraft, savePromptTemplate, resetPromptToDefault,
        diceRoll, generate
    }
}