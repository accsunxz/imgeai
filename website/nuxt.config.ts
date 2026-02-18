// https://nuxt.com/docs/api/configuration/nuxt-config
import { defineNuxtConfig } from 'nuxt/config'
export default defineNuxtConfig({
  compatibilityDate: '2025-07-15',
    // 站点全局网址配置（Sitemap 必需）
    site: {
        url: 'https://imgeai.com/'
    },

    modules: [
        '@nuxt/icon',
        '@vant/nuxt',
        'dayjs-nuxt',
        '@element-plus/nuxt',
        '@nuxtjs/tailwindcss',
        '@nuxtjs/i18n',
        '@nuxtjs/sitemap',
        '@nuxtjs/robots',
        // 1. 引入 Pinia
        '@pinia/nuxt',
        // 2. 引入持久化插件 (注意这里通常不需要写全称，看下文配置)
        'pinia-plugin-persistedstate/nuxt',
    ],


// 3. Pinia 持久化全局配置
    piniaPersistedstate: {
        storage: 'localStorage', // 强制默认存到 LocalStorage (适合存大段文本)
        debug: true, // 开发模式下可以看到 log
    },
    // ✅ 关键：你来决定样式加载顺序：先 EP 默认，再你的覆盖（你的必须最后）
    css: [
        'element-plus/dist/index.css',
        '~/assets/scss/theme.scss'
    ],


    app: {
        head: {
            title: 'ImgeAI Pro - 智能工作台',
            meta: [
                { name: 'viewport', content: 'width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no' },
                { name: 'theme-color', content: '#ffffff' }
            ],
            link: [
                // 引入 Inter 字体，字重包含 400, 500, 600, 700
                { rel: 'stylesheet', href: 'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap' }
            ]
        }
    },
    // Element Plus 配置
    elementPlus: {
        importStyle: 'scss', // 允许我们通过 SCSS 变量覆盖默认样式
    },
    // Icon 配置 (使用 Lucide 图标集，更现代)
    icon: {
        size: '18px',
        class: 'icon',
        mode: 'svg'
    },
    ssr: false, // 纯客户端应用模式，避免 LocalStorage 水合问题
    devtools: { enabled: false }
})