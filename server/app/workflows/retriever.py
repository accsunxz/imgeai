import json
import random
from app.workflows.scenario_manager import scenario_manager

class ExampleRetriever:
    """
    RAG 检索模块。
    当前实现为静态 JSON 抽样，提供标准化的 get_dynamic_examples 接口。
    未来接入 Milvus/MongoDB Atlas 等向量数据库时，仅需重写此类的内部实现。
    """
    async def get_dynamic_examples(self, scene_id: str, intent_id: str) -> str:
        rag_config = scenario_manager.get_rag_config(scene_id, intent_id)

        if not rag_config.get("enabled", False):
            return ""

        corpus = rag_config.get("mock_corpus", [])
        top_k = rag_config.get("top_k", 3)
        if not corpus:
            return ""

        sampled = random.sample(corpus, min(top_k, len(corpus)))
        context_items = [
            f"Input: {res['input']}\nOutput: {json.dumps(res['output'], ensure_ascii=False)}"
            for res in sampled
        ]
        retrieved_text = "\n\n".join(context_items)
        fmt = rag_config.get("context_format", "{retrieved_context}")

        return fmt.replace("{retrieved_context}", retrieved_text)

retriever = ExampleRetriever()