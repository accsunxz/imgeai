<!-- /components/PersonaPanel.vue -->
<template>
  <el-card class="neo" shadow="never">
    <div class="row">
      <div class="title">个性化「人设」</div>
      <el-switch v-model="enabled" active-text="启用" inactive-text="关闭" />
    </div>

    <div class="grid" v-if="enabled">
      <div>
        <div class="label">预设人设</div>
        <el-select v-model="presetId" filterable class="w-full">
          <el-option
              v-for="p in presets"
              :key="p.id"
              :label="`${p.name}｜${p.desc}`"
              :value="p.id"
          />
        </el-select>
      </div>

      <div>
        <div class="label">自定义人设（可选）</div>
        <el-input
            v-model="custom"
            type="textarea"
            :rows="4"
            placeholder="例：我说话更像一个云南本地的技术创业者，英文简单一点；不要太官腔；可以带点轻微口语缩写。"
        />
      </div>

      <div>
        <div class="label">最终注入到 context 的内容（预览）</div>
        <el-input :model-value="personaContext" type="textarea" :rows="6" readonly />
        <div class="hint">
          说明：这里会拼进你请求的 context，直接影响输出风格（不用改后端也能生效）。
        </div>
      </div>
    </div>
  </el-card>
</template>

<script setup lang="ts">
const props = defineProps<{
  enabled: boolean;
  presetId: string;
  custom: string;
  presets: any[];
  personaContext: string;
}>();

const emit = defineEmits<{
  (e: "update:enabled", v: boolean): void;
  (e: "update:presetId", v: string): void;
  (e: "update:custom", v: string): void;
}>();

const enabled = computed({
  get: () => props.enabled,
  set: (v) => emit("update:enabled", v),
});
const presetId = computed({
  get: () => props.presetId,
  set: (v) => emit("update:presetId", v),
});
const custom = computed({
  get: () => props.custom,
  set: (v) => emit("update:custom", v),
});

const presets = computed(() => props.presets);
const personaContext = computed(() => props.personaContext);
</script>

<style scoped>
.neo { border-radius: 14px; border: 1px solid #111; }
.row { display:flex; align-items:center; justify-content:space-between; gap:12px; }
.title { font-weight: 800; font-size: 14px; }
.grid { display:grid; gap: 12px; margin-top: 10px; }
.label { font-size: 12px; color: #111; font-weight: 700; margin-bottom: 6px; }
.hint { margin-top: 6px; font-size: 12px; color: #666; }
.w-full { width: 100%; }
</style>
