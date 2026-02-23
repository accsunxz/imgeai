import json
import re
from pathlib import Path
from langchain_core.prompts import ChatPromptTemplate

class ScenarioManager:
    """
    配置解析引擎。
    核心职责：将底层的 JSON 结构映射为内存中的配置对象，并提供 RAG 覆盖和提示词动态组装规则。
    不直接参与业务调用，作为数据提供方被 MCP Server 依赖。
    """

    def __init__(self, config_filename: str = "scenarios.json"):
        self.config_file = Path(__file__).parent / config_filename
        self.scenes = self._load_config().get("scenes", [])

    def _load_config(self) -> dict:
        if not self.config_file.exists():
            alt_path = self.config_file.parent.parent / self.config_file.name
            if alt_path.exists():
                self.config_file = alt_path
            else:
                raise FileNotFoundError(f"配置文件缺失: {self.config_file}")
        with open(self.config_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def get_scene(self, scene_id: str) -> dict:
        return next((s for s in self.scenes if s.get("id") == scene_id), {})

    def get_intent(self, scene_id: str, intent_id: str) -> dict:
        scene = self.get_scene(scene_id)
        return next((i for i in scene.get("intents", []) if i.get("id") == intent_id), {})

    def get_tone(self, scene_id: str, intent_id: str, tone_id: str) -> dict:
        intent = self.get_intent(scene_id, intent_id)
        return next((t for t in intent.get("tones", []) if t.get("id") == tone_id), {})

    def get_rag_config(self, scene_id: str, intent_id: str) -> dict:
        scene = self.get_scene(scene_id)
        intent = self.get_intent(scene_id, intent_id)
        rag_config = scene.get("global_rag", {}).copy()
        rag_config.update(intent.get("local_rag_override", {}))
        return rag_config

    def get_prompt_template(self, scene_id: str, intent_id: str, tone_id: str) -> ChatPromptTemplate:
        """组装三段式 Prompt 模板 (Prefix + Instruction + Suffix)"""
        intent = self.get_intent(scene_id, intent_id)
        tone = self.get_tone(scene_id, intent_id, tone_id)

        sys_prompt = tone.get("prompts", {}).get("system", "")

        layout = intent.get("human_layout", {})
        prefix = layout.get("prefix", "Context:\n{few_shot_context}\n\n")
        suffix = layout.get("suffix", "\nInput: {input_text}\nOutput:")
        instruction = tone.get("prompts", {}).get("instruction", "Process this:")

        final_human_prompt = f"{prefix}{instruction}{suffix}"

        return ChatPromptTemplate.from_messages([
            ("system", sys_prompt),
            ("human", final_human_prompt)
        ])

    @staticmethod
    def post_clean(text: str) -> str:
        s = (text or "").strip().strip('"').strip("'")
        s = re.sub(r"^(Here is|Sure,|Here's|Okay,).+?:\s*", "", s, flags=re.IGNORECASE)
        s = re.sub(r"```json\s*|\s*```", "", s)
        return s.strip()

scenario_manager = ScenarioManager()