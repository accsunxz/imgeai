type ApiResult<T> = {
    code: string | number;
    message: string;
    body: T;
    data?: T;
};

export function getApiBase() {
    return useRuntimeConfig().public.apiBase as string;
}

export async function apiGet<T>(path: string, params?: Record<string, any>) {
    const baseURL = getApiBase();
    return await $fetch<ApiResult<T>>(path, {
        baseURL,
        method: "GET",
        params,
    });
}
