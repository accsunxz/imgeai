// composables/useImgeaiPro.ts
import type { Playbook } from '~/data/playbooks'
import { PLAYBOOKS } from '~/data/playbooks'
import { ElMessage } from 'element-plus'

type Adv = { must: string[]; avoid: string[]; strength: 0|1|2; profileName: string }
type PromptTpl = { sys: string; user: string }
export type Result = { labelZh: string; text: string; explanation: string; fromCache?: boolean }

const LS = {
    key: 'imgeai_sf_key_v0',
    model: 'imgeai_sf_model_v0',
    cacheOn: 'imgeai_cache_on_v0',
    cache: 'imgeai_cache_v0',
    adv: 'imgeai_adv_v0',
    advProfiles: 'imgeai_adv_profiles_v0',
    tpl: 'imgeai_prompt_tpl_v0',
}

const CACHE_TTL = 7 * 24 * 3600 * 1000
const CACHE_MAX = 40

function safeJson<T>(raw: string | null, fallback: T): T {
    try { return raw ? (JSON.parse(raw) as T) : fallback } catch { return fallback }
}
function fnv1a(str: string) {
    let h = 0x811c9dc5
    for (let i = 0; i < str.length; i++) {
        h ^= str.charCodeAt(i)
        h = (h + ((h<<1)+(h<<4)+(h<<7)+(h<<8)+(h<<24))) >>> 0
    }
    return ('00000000' + h.toString(16)).slice(-8)
}
function splitKw(text: string) {
    return String(text || '')
        .split(/[,，\n]/)
        .map(s => s.trim())
        .filter(Boolean)
}

export function useImgeaiPro() {
    const sfBase = useRuntimeConfig().public.sfBase as string

    // ===== state =====
    const apiKey = ref('')
    const model = ref('Qwen/Qwen2.5-72B-Instruct')
    const cacheEnabled = ref(true)

    const playbooks = readonly(PLAYBOOKS)
    const currentId = ref(playbooks[0].id)
    const tone = ref(playbooks[0].tones[0].id)
    const lengthLevel = ref<0|1|2>(1)

    const input = ref('')
    const context = ref('')
    const showContext = ref(false)

    const loading = ref(false)
    const loadingModels = ref(false)
    const modelList = ref<string[]>([])

    const result = ref<Result | null>(null)

    // dialogs
    const dlgApi = ref(false)
    const dlgKw = ref(false)
    const dlgPayload = ref(false)
    const dlgPrompt = ref(false)
    const dlgProfiles = ref(false)

    // drafts
    const apiKeyDraft = ref('')
    const modelDraft = ref('')
    const cacheEnabledDraft = ref(true)

    // keywords adv
    const defaultAdv = (): Adv => ({ must: [], avoid: [], strength: 1, profileName: 'default' })
    const adv = ref<Adv>(defaultAdv())
    const profiles = ref<Record<string, Adv>>({ default: defaultAdv() })
    const profilePick = ref('default')
    const quickMust = ref('')
    const quickAvoid = ref('')

    // prompt templates
    const promptTpls = ref<Record<string, PromptTpl>>({})
    const promptEditId = ref(currentId.value)
    const promptSysDraft = ref('')
    const promptUserDraft = ref('')

    // ===== computed =====
    const playbook = computed<Playbook>(() => playbooks.find(p => p.id === currentId.value) || playbooks[0])

    watch(playbook, (b) => {
        if (!b.tones.some(t => t.id === tone.value)) tone.value = b.tones[0].id
    }, { immediate: true })

    const lengthLabelZh = computed(() => (['短','中','长'][Number(lengthLevel.value)] || '中'))
    const reservedTokens = computed(() => {
        const cap = playbook.value.maxOut || 300
        const mult = ([0.55, 0.85, 1.15][Number(lengthLevel.value)] ?? 0.85)
        return Math.ceil(cap * mult)
    })

    const keywordRulesText = computed(() => {
        const s = adv.value.strength ?? 1
        const strengthZh = (['弱','中','强'][s] || '中')
        const must = adv.value.must.length ? adv.value.must.join('、') : '（无）'
        const avoid = adv.value.avoid.length ? adv.value.avoid.join('、') : '（无）'
        return `关键词规则（内部）：\n- 必须包含：${must}\n- 避免出现：${avoid}\n- 强度：${strengthZh}`
    })

    function safeJsonObjSpec(toneZh: string) {
        return (
            '严格要求：只输出一个 JSON 对象（不要数组/不要Markdown/不要代码块）。\n' +
            `{ "labelZh":"结果", "toneZh":"${toneZh}", "text":"", "explanation":"" }\n` +
            '只允许返回合法 JSON。'
        )
    }

    function defaultPromptFor(pb: Playbook): PromptTpl {
        const toneZh = pb.tones.find(t => t.id === tone.value)?.zh || pb.tones[0]?.zh || ''
        if (pb.mode === 'en2zh') {
            return {
                sys:
                    '你是一个严谨的双语助手，擅长把英文解释成中文用户容易理解的表达。\n' +
                    safeJsonObjSpec(toneZh) + '\n' +
                    '输出语言：中文。\n' +
                    '要求：准确、清晰、不瞎猜。',
                user:
                    '任务：把英文解释/翻译成中文（按当前风格输出）。\n' +
                    '英文原文：\n{{input}}\n\n' +
                    '补充上下文（可选）：\n{{context}}'
            }
        }
        return {
            sys:
                '你是一位资深英文文案编辑，面向真实海外用户写作，避免“AI味”和生硬直译。\n' +
                safeJsonObjSpec(toneZh) + '\n' +
                '平台/场景：{{platformZh}}\n' +
                '语气：{{toneZh}}（toneId={{toneId}}）\n' +
                '长度：{{lengthLabelZh}}\n' +
                '输出语言：只输出英文（text 字段内）。\n' +
                '{{keywordRules}}',
            user:
                '中文输入：\n{{input}}\n\n补充上下文（可选）：\n{{context}}'
        }
    }

    function renderTpl(tpl: string, vars: Record<string, any>) {
        return String(tpl || '').replace(/\{\{\s*([a-zA-Z0-9_]+)\s*\}\}/g, (_, k) => {
            const v = vars[k]
            return (v === undefined || v === null) ? '' : String(v)
        })
    }

    function ensureTplDefaults() {
        for (const pb of playbooks) {
            if (!promptTpls.value[pb.id]) promptTpls.value[pb.id] = defaultPromptFor(pb)
            else {
                const d = defaultPromptFor(pb)
                promptTpls.value[pb.id].sys ||= d.sys
                promptTpls.value[pb.id].user ||= d.user
            }
        }
        localStorage.setItem(LS.tpl, JSON.stringify(promptTpls.value))
    }

    function buildPayload() {
        const pb = playbook.value
        const toneZh = pb.tones.find(t => t.id === tone.value)?.zh || pb.tones[0]?.zh || ''
        const vars = {
            toneZh,
            toneId: tone.value,
            lengthLabelZh: lengthLabelZh.value,
            platformZh: pb.title,
            keywordRules: keywordRulesText.value,
            input: input.value || '',
            context: context.value || '',
        }
        const tpl = promptTpls.value[pb.id] || defaultPromptFor(pb)
        const sysMsg = renderTpl(tpl.sys, vars)
        const userMsg = renderTpl(tpl.user, vars)

        return {
            payload: {
                model: model.value,
                messages: [
                    { role: 'system', content: sysMsg },
                    { role: 'user', content: userMsg },
                ],
                max_tokens: reservedTokens.value,
                temperature: (pb.mode === 'en2zh') ? 0.35 : 0.7,
            },
            sysMsg,
            userMsg,
        }
    }

    const payloadJson = computed(() => JSON.stringify(buildPayload().payload, null, 2))

    // ===== local cache =====
    function getCacheStore() {
        return safeJson(localStorage.getItem(LS.cache), { items: {} as Record<string, { ts: number; data: Result }> })
    }
    function setCacheStore(s: any) { localStorage.setItem(LS.cache, JSON.stringify(s)) }
    function pruneCache(store: any) {
        const keys = Object.keys(store.items || {})
        if (keys.length <= CACHE_MAX) return store
        keys.sort((a,b) => (store.items[b].ts||0) - (store.items[a].ts||0))
        const keep = keys.slice(0, CACHE_MAX)
        const next: any = { items: {} }
        for (const k of keep) next.items[k] = store.items[k]
        return next
    }

    // ===== actions =====
    function openApiDialog() {
        apiKeyDraft.value = apiKey.value
        modelDraft.value = model.value
        cacheEnabledDraft.value = cacheEnabled.value
        dlgApi.value = true
    }
    function saveApiSettings() {
        apiKey.value = String(apiKeyDraft.value || '').trim()
        model.value = String(modelDraft.value || '').trim() || 'Qwen/Qwen2.5-72B-Instruct'
        cacheEnabled.value = !!cacheEnabledDraft.value
        localStorage.setItem(LS.key, apiKey.value)
        localStorage.setItem(LS.model, model.value)
        localStorage.setItem(LS.cacheOn, cacheEnabled.value ? '1' : '0')
        dlgApi.value = false
        ElMessage.success('已保存')
    }
    function clearCache() {
        localStorage.removeItem(LS.cache)
        ElMessage.success('缓存已清空')
    }

    async function loadModels() {
        const key = String(apiKeyDraft.value || '').trim()
        if (!key) return ElMessage.warning('请先输入 Key')

        loadingModels.value = true
        try {
            const r = await fetch(`${sfBase}/models?sub_type=chat`, {
                headers: { Authorization: `Bearer ${key}` }
            })
            const j = await r.json()
            modelList.value = (j.data || []).map((x: any) => x.id).filter(Boolean)
            if (!modelDraft.value && modelList.value.length) modelDraft.value = modelList.value[0]
            ElMessage.success('模型列表已加载')
        } catch {
            ElMessage.error('加载失败')
        } finally {
            loadingModels.value = false
        }
    }

    function selectScene(id: string) {
        currentId.value = id
        result.value = null
    }
    function diceRoll() {
        const map: Record<string, string> = {
            en2zh_understand: 'I’m circling back on the proposal and wanted to clarify the timeline...',
            amazon_listing: '便携折叠水壶，食品级硅胶，耐高温，适合露营和旅行。',
            email_cold: '给潜在客户推销SEO服务，想约个10分钟电话沟通。',
            reddit_help: 'SaaS注册率不错但留存很差，可能是什么原因？',
            facebook_group: '想在群里分享一个对跨境卖家有用的小工具。',
            ig_caption: '海边日落，风很温柔，今天状态很好。',
            x_build: 'AI不会取代人，会用AI的人才会。'
        }
        input.value = map[currentId.value] || '示例…'
    }

    async function copy(text: string) {
        try {
            await navigator.clipboard.writeText(String(text || ''))
            ElMessage.success('已复制')
        } catch {
            ElMessage.warning('复制失败')
        }
    }

    // keywords
    function addKw(type: 'must'|'avoid') {
        const box = type === 'must' ? quickMust : quickAvoid
        const items = splitKw(box.value)
        if (!items.length) return
        const arr = type === 'must' ? adv.value.must : adv.value.avoid
        const merged = Array.from(new Set(arr.concat(items)))
        if (type === 'must') adv.value.must = merged
        else adv.value.avoid = merged
        box.value = ''
        localStorage.setItem(LS.adv, JSON.stringify(adv.value))
    }
    function removeKw(type:'must'|'avoid', idx:number) {
        const arr = type === 'must' ? adv.value.must : adv.value.avoid
        arr.splice(idx, 1)
        localStorage.setItem(LS.adv, JSON.stringify(adv.value))
    }
    function saveKeywordState() {
        localStorage.setItem(LS.adv, JSON.stringify(adv.value))
        ElMessage.success('已保存')
    }
    function openProfilesDialog() {
        profilePick.value = adv.value.profileName || 'default'
        dlgProfiles.value = true
    }
    function saveProfile() {
        const name = window.prompt('配置集名称：', adv.value.profileName || 'default')
        if (!name) return
        adv.value.profileName = name
        profiles.value[name] = JSON.parse(JSON.stringify(adv.value))
        profilePick.value = name
        localStorage.setItem(LS.advProfiles, JSON.stringify(profiles.value))
        localStorage.setItem(LS.adv, JSON.stringify(adv.value))
        ElMessage.success('配置集已保存')
    }
    function loadProfile(name: string) {
        if (!profiles.value[name]) return
        adv.value = JSON.parse(JSON.stringify(profiles.value[name]))
        profilePick.value = name
        localStorage.setItem(LS.adv, JSON.stringify(adv.value))
        ElMessage.success('配置集已加载')
    }

    // prompt editor
    function openPromptDialog() {
        promptEditId.value = currentId.value
        const tpl = promptTpls.value[promptEditId.value]
        promptSysDraft.value = tpl?.sys || ''
        promptUserDraft.value = tpl?.user || ''
        dlgPrompt.value = true
    }
    function savePromptTpl() {
        const id = promptEditId.value
        promptTpls.value[id] = { sys: String(promptSysDraft.value||''), user: String(promptUserDraft.value||'') }
        localStorage.setItem(LS.tpl, JSON.stringify(promptTpls.value))
        ElMessage.success('模板已保存')
    }
    function resetPromptTpl() {
        const pb = playbooks.find(p => p.id === promptEditId.value) || playbooks[0]
        const d = defaultPromptFor(pb)
        promptSysDraft.value = d.sys
        promptUserDraft.value = d.user
        ElMessage.success('已恢复默认（记得保存）')
    }

    async function generate() {
        if (!apiKey.value) return openApiDialog()
        if (!String(input.value || '').trim()) return

        loading.value = true
        result.value = null

        try {
            const built = buildPayload()
            const payload = built.payload

            const seed = JSON.stringify({
                model: payload.model,
                playbook: playbook.value.id,
                tone: tone.value,
                len: lengthLevel.value,
                input: input.value,
                context: context.value,
                adv: adv.value,
                tpl: promptTpls.value[playbook.value.id] || null
            })
            const cacheKey = fnv1a(seed)

            if (cacheEnabled.value) {
                const store = getCacheStore()
                const hit = store.items[cacheKey]
                if (hit && (Date.now() - hit.ts < CACHE_TTL)) {
                    result.value = { ...hit.data, fromCache: true }
                    loading.value = false
                    return
                }
            }

            const res = await fetch(`${sfBase}/chat/completions`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    Authorization: `Bearer ${apiKey.value}`
                },
                body: JSON.stringify(payload)
            })
            const json = await res.json()
            if (json?.error) throw new Error(json.error.message || '请求错误')

            let content = String(json?.choices?.[0]?.message?.content || '')
            content = content.replace(/^```json\s*/i,'').replace(/^```\s*/i,'').replace(/```$/i,'').trim()

            let parsed: any
            try { parsed = JSON.parse(content) }
            catch { parsed = { labelZh:'Raw', text: content, explanation:'未能解析为 JSON（你可能改了模板输出格式）' } }

            const one = Array.isArray(parsed) ? (parsed[0] || {}) : (parsed || {})
            const out: Result = {
                labelZh: one.labelZh || '结果',
                text: one.text || String(one.text || one.content || ''),
                explanation: one.explanation || ''
            }
            result.value = out

            if (cacheEnabled.value) {
                let store2 = getCacheStore()
                store2.items[cacheKey] = { ts: Date.now(), data: { ...out } }
                store2 = pruneCache(store2)
                setCacheStore(store2)
            }
        } catch (e: any) {
            ElMessage.error(e?.message || '生成失败')
        } finally {
            loading.value = false
        }
    }

    // init
    onMounted(() => {
        apiKey.value = localStorage.getItem(LS.key) || ''
        model.value = localStorage.getItem(LS.model) || 'Qwen/Qwen2.5-72B-Instruct'
        cacheEnabled.value = localStorage.getItem(LS.cacheOn) !== '0'

        adv.value = safeJson(localStorage.getItem(LS.adv), defaultAdv())
        profiles.value = safeJson(localStorage.getItem(LS.advProfiles), { default: defaultAdv() })

        promptTpls.value = safeJson(localStorage.getItem(LS.tpl), {})
        ensureTplDefaults()
    })

    return {
        // state
        sfBase,
        apiKey, model, cacheEnabled,
        playbooks, currentId, playbook,
        tone, lengthLevel, lengthLabelZh, reservedTokens,
        input, context, showContext,
        loading, loadingModels, modelList,
        result,

        // dialogs
        dlgApi, dlgKw, dlgPayload, dlgPrompt, dlgProfiles,

        // drafts
        apiKeyDraft, modelDraft, cacheEnabledDraft,

        // keyword
        adv, profiles, profilePick, quickMust, quickAvoid, keywordRulesText,

        // prompt editor
        promptEditId, promptSysDraft, promptUserDraft,
        payloadJson,

        // actions
        openApiDialog, saveApiSettings, clearCache, loadModels,
        selectScene, diceRoll, generate, copy,
        addKw, removeKw, saveKeywordState,
        openProfilesDialog, saveProfile, loadProfile,
        openPromptDialog, savePromptTpl, resetPromptTpl,
    }
}
