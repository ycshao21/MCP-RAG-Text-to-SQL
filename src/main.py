import os
import asyncio
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


async def initialize_rag():
    rag = LightRAG(
        working_dir=STORAGE_DIR,
        llm_model_func=gpt_4o_mini_complete,
        embedding_func=openai_embed,
    )

    await rag.initialize_storages()
    await initialize_pipeline_status()

    return rag


async def retrive_context(
    rag: LightRAG,
    query: str,
    retrieval_mode: str = "hybrid",
):
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
        context = await rag.aquery(
            query=query,
            param=query_param,
            system_prompt=None,
        )

    print("Context:")
    print(context)

    print("Token count:", token_tracker.get_usage())
    return context


async def main():
    try:
        # Initialize RAG instance
        rag = await initialize_rag()

        context_file = "../data/db_doc.txt"
        with open(context_file, "r", encoding="utf-8") as f:
            await rag.ainsert(f.read())

        # query = "网站上发表文章最多且点击量最高的用户硬币数是多少？"
        query = "网站上有多少用户？"

        retrieval_mode = "hybrid"
        retrive_context(
            rag,
            query,
            retrieval_mode,
        )

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if rag:
            await rag.finalize_storages()


if __name__ == "__main__":
    asyncio.run(main())
