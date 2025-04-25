from openai import OpenAI
from dotenv import load_dotenv
import os


def split_query(query, entities=None):
    """
    基于陈述性质的查询语句提取相关信息, 由大模型判断SQL的复杂程度
    """
    load_dotenv()

    client = OpenAI(
        api_key=os.getenv("DASHSCOPE_API_KEY"),
        base_url=os.getenv("DASHSCOPE_BASE_URL"),
        # api_key=os.getenv("API_KEY"),
        # base_url=os.getenv("BASE_URL"),
    )

    reasoning_content = ""  # 记录完整思考
    answer_content = ""  # 记录完整回复
    is_answering = False  # 是否结束思考

    system_prompt = f"""
    You are tasked with analyzing a given declarative query and determining whether it should be broken down into multiple subquery tasks when converting it into SQL. 
    Based on the input query and the retrieved information, you need to decide how many tasks are required and describe each task. 
    Follow the JSON format below for your response, but leave all fields except the task count and task descriptions empty.

    Input:
    Query: A declarative statement or question provided as input.
    Retrieved Information: Contextual or supplementary data related to the query.

    Output Format:
    {{
        "task1": {{ "description": "", "sql": "", "result": "" }},
        "task2": {{ "description": "", "sql": "", "result": "" }}
    }}

    Instructions:

    Analyze the complexity of the query and determine if it requires decomposition into multiple subqueries.
    If the query can be handled in a single SQL statement, return only one task with its description.
    If the query requires multiple subqueries, create additional tasks as needed, providing a brief description for each task.
    Leave the sql and result fields empty.

    Example Input:
    Query: "Find the total sales for products in category 'Electronics' where the price is above $100, and also list the top 5 customers who purchased the most from this category."
    Retrieved Information: {entities}

    Example Output:
    {{
        "task1": {{ "description": "Calculate the total sales for products in the 'Electronics' category with a price above $100.", "sql": "", "result": ""}},
        "task2": {{ "description": "Identify the top 5 customers who purchased the most from the 'Electronics' category.", "sql": "", "result": "" }}
    }}
    """

    # completion = client.chat.completions.create(
    #     model="deepseek-v3-250324",
    #     messages=[
    #         {"role": "system", "content": system_prompt},
    #         {"role": "user", "content": query},
    #     ],
    # )

    completion = client.chat.completions.create(
        model="qwq-plus-latest",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query},
        ],
        stream=True,
    )

    # answer_content = completion.choices[0].message.content

    for chunk in completion:
        if not chunk.choices:
            print("\nUsage:")
            print(chunk.usage)
        else:
            delta = chunk.choices[0].delta
            if hasattr(delta, "reasoning_content") and delta.reasoning_content != None:
                # print(delta.reasoning_content, end='', flush=True)
                reasoning_content += delta.reasoning_content
            else:
                if delta.content != "" and is_answering is False:
                    is_answering = True

                # print(delta.content, end='', flush=True)
                answer_content += delta.content

    return answer_content


if __name__ == "__main__":
    print(
        split_query(
            "查询上海过去一周中午12点的平均气温",
            "上海过去一周的气温表，记录每一天中午12点的温度",
        )
    )
