import os
import asyncio
import json
import re

from dotenv import load_dotenv

from Agent.Normalizer import Normalizer
from Agent.split_query import split_query
from Agent.manage import TaskManager

from lightrag.lightrag import LightRAG, QueryParam
from lightrag.llm.openai import (
    gpt_4o_mini_complete,
    gpt_4o_complete,
    openai_embed,
)
from lightrag.kg.shared_storage import initialize_pipeline_status
from lightrag.utils import setup_logger, TokenTracker

setup_logger("lightrag", level="INFO")

STORAGE_DIR = "./rag_storage"
if not os.path.exists(STORAGE_DIR):
    os.mkdir(STORAGE_DIR)


class Text2SQL:
    def __init__(self):
        self.rag = None
        self.normalizer = None
        self.task_manager = TaskManager()

    async def initialize(self):
        # Initialize RAG instance
        self.rag = LightRAG(
            working_dir=STORAGE_DIR,
            llm_model_func=gpt_4o_mini_complete,
            embedding_func=openai_embed,
        )
        await self.rag.initialize_storages()
        await initialize_pipeline_status()

        # Load context file
        context_file = "./data/db_doc.txt"
        with open(context_file, "r", encoding="utf-8") as f:
            await self.rag.ainsert(f.read())

        # Initialize rewriter
        self.normalizer = Normalizer()

    async def cleanup(self):
        if self.rag:
            await self.rag.finalize_storages()
            self.rag = None

    def normalize_query(self, query: str):
        # Normalize the query using the rewriter
        normalized_query = self.normalizer.normalize(query)
        return normalized_query

    async def retrive_context(
        self,
        query: str,
        retrieval_mode: str = "hybrid",
    ):
        print("Retrieving context...")
        # Retrieval mode:
        # - "local": Focuses on context-dependent information.
        # - "global": Utilizes global knowledge.
        # - "hybrid": Combines local and global retrieval methods.
        # - "naive": Performs a basic search without advanced techniques.
        # - "mix": Integrates knowledge graph and vector retrieval.

        query_param = QueryParam(
            mode=retrieval_mode,
            only_need_context=True,
        )

        token_tracker = TokenTracker()

        with token_tracker:
            # Context only
            context = await self.rag.aquery(
                query=query,
                param=query_param,
                system_prompt=None,
            )

        print("Token count:", token_tracker.get_usage())
        return context


async def main():
    load_dotenv()

    text2sql = Text2SQL()
    await text2sql.initialize()

    # 读取 jsonl
    with open("./data/queries.jsonl", "r", encoding="utf-8") as f:
        queries = [json.loads(line) for line in f.readlines()]

    query_idx = 2

    query = queries[query_idx]
    print(f"查询问题: {query['problem']}")

    normalized_query = text2sql.normalize_query(query["problem"])
    print("Normalized query:", normalized_query)

    retrieval_mode = "hybrid"
    context = await text2sql.retrive_context(
        normalized_query,
        retrieval_mode,
    )
    print("Retrieved context:", context)

    # Router
    tasks = split_query(normalized_query, context)
    tasks = re.sub(r"```json\s*(.*?)\s*```", r"\1", tasks, flags=re.DOTALL)

    # print("Raw tasks:", tasks)

    tasks = json.loads(tasks)
    sql, result = await text2sql.task_manager.execute_tasks(tasks, query_idx)

    print("Final SQL:", sql)
    print("Final result:", result)

    await text2sql.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
