export type ToneDef = { id: string; zh: string };

export type StyleMode = "literal" | "native" | "expand";

export type Playbook = {
    id: string;
    platformZh: string;
    badgeZh: string;
    titleZh: string;
    mode: "en2zh" | "zh2en";
    inputLabel: string;
    placeholder: string;
    contextHint: string;
    tones: ToneDef[];
    maxOutputTokens: number;
    actionLabel: string;
};

export type GenerateResultItem = {
    labelZh: string;
    toneZh?: string;
    text: string;
    explanation?: string;
};

export type GenerateRequest = {
    playbookId: string;
    input: string;
    context?: string;
    toneId?: string;
    lengthLevel: 0 | 1 | 2;
    styleMode?: StyleMode; // ✅ 新增
};

export type GenerateResponse = {
    fromCache: boolean;
    model: string;
    playbookId: string;
    generationId: string;
    results: GenerateResultItem[];
};

export type HistoryItem = {
    id: string;
    playbookId: string;
    toneId: string | null;
    lengthLevel: 0 | 1 | 2;
    model: string;
    fromCache: boolean;
    input: string | null;
    context: string | null;
    results: GenerateResultItem[];
    createdAt: string;
};

export type FavoriteItem = HistoryItem;

export type PromptProfile = {
    playbookId: string;
    isActive: boolean;
    systemStyle: string;
    formatSpec: string;
    variationSpec: string;
    enableRewritePass: boolean;
    temperatureOverride: number | null;
    humanizerJson: string;
};
