import type {
    Playbook,
    GenerateRequest,
    GenerateResponse,
    HistoryItem,
    FavoriteItem,
    PromptProfile,
} from "~/types/imgeai";

type AnyResp = any;

function isOk(r: AnyResp) {
    // 兼容：{ success: true } 和 { status:'ok', code:'0000' }
    if (r?.success === true) return true;
    if (r?.status === "ok") return true;
    if (r?.code === "0000" || r?.code === 0) return true;
    return false;
}

function getMsg(r: AnyResp) {
    return r?.msg || r?.message || r?.error?.message || "请求失败";
}

function getBody<T>(r: AnyResp): T {
    // 兼容常见字段：body / data / result
    return (r?.body ?? r?.data ?? r?.result) as T;
}

async function unwrap<T>(p: Promise<any>): Promise<T> {
    const r = await p;
    if (!isOk(r)) throw new Error(getMsg(r));
    return getBody<T>(r);
}

export function useImgeaiApi() {
    const baseURL = "/public/imgeai";

    const req = $fetch.create({
        baseURL,
        credentials: "include",
    });

    return {
        async getPlaybooks() {
            // ✅ 不要 silent fail，失败直接抛错，方便你看问题
            return await unwrap<Playbook[]>(req("/playbooks"));
        },

        async generate(payload: GenerateRequest) {
            return await unwrap<GenerateResponse>(req("/generate", { method: "POST", body: payload }));
        },

        async getHistory(limit = 50) {
            return await unwrap<HistoryItem[]>(req(`/history?limit=${limit}`));
        },

        async deleteHistory(id: string) {
            await unwrap<boolean>(req(`/history/${id}`, { method: "DELETE" }));
            return true;
        },

        async clearHistory() {
            await unwrap<boolean>(req(`/history`, { method: "DELETE" }));
            return true;
        },

        async getFavorites(limit = 50) {
            return await unwrap<FavoriteItem[]>(req(`/favorites?limit=${limit}`));
        },

        async addFavorite(generationId: string) {
            await unwrap<boolean>(req(`/favorites`, { method: "POST", body: { generationId } }));
            return true;
        },

        async removeFavorite(generationId: string) {
            await unwrap<boolean>(req(`/favorites/${generationId}`, { method: "DELETE" }));
            return true;
        },

        async adminMe() {
            try {
                return await unwrap<{ isAdmin: boolean }>(req(`/admin/me`));
            } catch {
                return { isAdmin: false };
            }
        },

        async adminLogin(key: string) {
            return await unwrap<{ isAdmin: boolean }>(req(`/admin/login`, { method: "POST", body: { key } }));
        },

        async adminLogout() {
            try {
                return await unwrap<{ isAdmin: boolean }>(req(`/admin/logout`, { method: "POST" }));
            } catch {
                return { isAdmin: false };
            }
        },

        async getProfile(playbookId: string) {
            return await unwrap<PromptProfile | null>(req(`/admin/profiles/${playbookId}`));
        },

        async saveProfile(playbookId: string, body: any) {
            await unwrap<boolean>(req(`/admin/profiles/${playbookId}`, { method: "PUT", body }));
            return true;
        },
    };
}
