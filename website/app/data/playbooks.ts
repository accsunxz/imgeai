// data/playbooks.ts
export type Tone = { id: string; zh: string }
export type Playbook = {
    id: string
    title: string
    icon: string
    mode: 'en2zh' | 'zh2en'
    tones: Tone[]
    maxOut: number
    placeholder: string
    contextHint: string
}

export const PLAYBOOKS: Playbook[] = [
    { id:'en2zh_understand', title:'英文理解', icon:'ion:swap-horizontal', mode:'en2zh',
        tones:[{id:'natural',zh:'自然解释'},{id:'literal',zh:'逐句直译'},{id:'bullets',zh:'要点总结'}],
        maxOut:650, placeholder:'例如：I’m circling back on the proposal...', contextHint:'例如：邮件/合同场景、你关心的点…' },

    { id:'amazon_listing', title:'Amazon Listing', icon:'ion:cart-outline', mode:'zh2en',
        tones:[{id:'conversion',zh:'高转化'},{id:'compliant',zh:'合规克制'},{id:'premium',zh:'高端质感'}],
        maxOut:900, placeholder:'例如：折叠水壶，食品级硅胶，耐高温…', contextHint:'类目、目标人群、参数规格…' },

    { id:'email_cold', title:'Cold Email', icon:'ion:mail-outline', mode:'zh2en',
        tones:[{id:'direct',zh:'开门见山'},{id:'warm',zh:'温暖亲和'},{id:'executive',zh:'高管对话'}],
        maxOut:820, placeholder:'例如：给客户推销SEO服务，约个10分钟…', contextHint:'接收人职位、你的价值点…' },

    { id:'reddit_help', title:'Reddit 帖子', icon:'ion:chatbubbles-outline', mode:'zh2en',
        tones:[{id:'neutral',zh:'清晰直接'},{id:'humble',zh:'谦逊礼貌'},{id:'confident',zh:'专业讨论'}],
        maxOut:520, placeholder:'例如：SaaS注册率不错但留存很差…', contextHint:'板块/受众、你想要的具体建议…' },

    { id:'facebook_group', title:'Facebook 群组', icon:'ion:people-outline', mode:'zh2en',
        tones:[{id:'community',zh:'热心分享'},{id:'narrative',zh:'故事感'},{id:'expert',zh:'专家建议'}],
        maxOut:420, placeholder:'例如：发现个好工具想推荐给大家…', contextHint:'强调无利益相关、引发讨论…' },

    { id:'ig_caption', title:'Instagram 文案', icon:'ion:camera-outline', mode:'zh2en',
        tones:[{id:'aesthetic',zh:'氛围感'},{id:'friendly',zh:'像朋友'},{id:'influencer',zh:'种草风'}],
        maxOut:320, placeholder:'例如：海边日落，风很温柔…', contextHint:'emoji 风格、是否加标签…' },

    { id:'x_build', title:'X / Twitter', icon:'ion:flash-outline', mode:'zh2en',
        tones:[{id:'punchy',zh:'短促有力'},{id:'calm',zh:'冷静克制'},{id:'provocative',zh:'犀利观点'}],
        maxOut:280, placeholder:'例如：AI不会取代人，会用AI的人才会。', contextHint:'数据支持、呼吁行动…' },
]
