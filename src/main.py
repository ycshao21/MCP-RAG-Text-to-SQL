import os
import asyncio

from dotenv import load_dotenv

from Agent.Normalizer import Normalizer

from LightRAG.lightrag import LightRAG, QueryParam
from LightRAG.lightrag.llm.openai import (
    gpt_4o_mini_complete,
    gpt_4o_complete,
    openai_embed,
)
from LightRAG.lightrag.kg.shared_storage import initialize_pipeline_status
from LightRAG.lightrag.utils import setup_logger, TokenTracker

setup_logger("lightrag", level="INFO")

STORAGE_DIR = "./rag_storage"
if not os.path.exists(STORAGE_DIR):
    os.mkdir(STORAGE_DIR)


class Text2SQL:
    def __init__(self):
        self.rag = None
        self.normalizer = None

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
        context_file = "../data/db_doc.txt"
        with open(context_file, "r", encoding="utf-8") as f:
            await self.rag.ainsert(f.read())

        # Initialize rewriter
        self.normalizer = Normalizer()

    async def cleanup(self):
        if self.rag:
            await self.rag.finalize_storages()
            self.rag = None

    async def normalize_query(self, query: str):
        # Normalize the query using the rewriter
        normalized_query = await self.normalizer.rewrite(query)
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

    user_query = "网站上有多少用户？"
    # user_query = "网站上发表文章最多且点击量最高的用户硬币数是多少？"

    normalized_query = text2sql.normalize_query(user_query)
    print("Normalized query:", normalized_query)

    retrieval_mode = "hybrid"
    context = text2sql.retrive_context(
        user_query,
        retrieval_mode,
    )
    print("Retrieved context:", context)

    # # Judge
    # tasks = []

    # task_manager.execute_tasks(tasks)

    await text2sql.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
