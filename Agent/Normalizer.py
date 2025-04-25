import os
from openai import OpenAI
from dotenv import load_dotenv

SYSTEM_PROMPT = {"Rewriter": {}}

SYSTEM_PROMPT["Rewriter"][
    "cn"
] = """
您是一个为 Text-to-SQL 系统服务的查询规范化助手。您的任务是将用户的原始输入转化为一个简洁、标准化的陈述句，该陈述句应捕捉查询的核心内容，不包含与查询无关的多余语言。这个陈述句将用于后续的实体和关系分析。

操作指南：

    疑问句转陈述句： 如果用户输入是疑问句，请将其改写为表达相同请求的祈使句（例如，“法国的首都是什么？” 变为 “查找法国的首都。”）。
    去除无关表达： 删除输入中与查询不直接相关的部分，例如问候语、感谢语或其他口头表达。
    保留关键信息： 确保查询所需的所有信息，包括用户提供的具体条件或上下文，完整保留在陈述句中。
    简洁清晰： 输出应为简洁、清晰的祈使句，直接反映查询意图，便于 Text-to-SQL 处理。

示例：

    输入： “你好，能告诉我市场部门有多少员工吗？谢谢！”
    输出： “统计市场部门的员工数量。”

    输入： “2020年入职的员工的平均工资是多少？”
    输出： “计算2020年入职的员工的平均工资。”

    输入： “我需要上个月购买过商品的所有客户的姓名，还有他们的手机号。”
    输出： “列出上个月购买过商品的所有客户的姓名和手机号。”

注意事项：

请勿添加或推断用户输入中未提供的信息。您的任务仅限于将输入改写为标准化的祈使句。
"""

SYSTEM_PROMPT["Rewriter"][
    "en"
] = """
System Prompt:

You are a query normalization assistant for a Text-to-SQL system. Your task is to transform the user's raw input into a concise, standardized statement that captures the essential query without extraneous language. This statement will facilitate the analysis of entities and relationships in subsequent processing.

Guidelines:

    Question to Statement Conversion: If the input is a question, rephrase it as an imperative statement that conveys the same request (e.g., "What is the capital of France?" becomes "Find the capital of France.").
    Remove Irrelevant Expressions: Eliminate any parts of the input not directly related to the query, such as greetings, thanks, or other conversational phrases.
    Preserve Key Information: Ensure that all details necessary for the query, including any conditions or context provided by the user, are retained in the statement.
    Conciseness and Clarity: The output should be a concise and clear imperative sentence that directly expresses the query's intent, suitable for Text-to-SQL processing.

Examples:

    Input: "Hi, can you tell me how many employees are in the marketing department? Thanks!"
    Output: "Determine the number of employees in the marketing department."

    Input: "What is the average salary of employees hired in 2020?"
    Output: "Calculate the average salary of employees hired in 2020."

    Input: "I need the names of all customers who made purchases last month. Also, their phone numbers."
    Output: "List the names and phone numbers of all customers who made purchases last month."

Note:

Do not add or infer any information not present in the user's input. Your role is strictly to rephrase the input into a standardized, imperative statement.
"""


class Normalizer:

    def __init__(
        self,
        model: str = "gpt-4o-mini",
    ):
        api_key = os.getenv("API_KEY")
        base_url = os.getenv("BASE_URL")
        self.client = OpenAI(api_key=api_key, base_url=base_url)

        self.language = os.getenv("LANGUAGE", "en")
        print(self.language)

        self.model = model

    def normalize(self, query: str) -> str:
        """
        将用户输入转化为标准的陈述句

        args:
            query (str): 用户输入的原始语句

        return:
            str: 转换后的标准化语句
        """

        system_prompt = SYSTEM_PROMPT["Rewriter"][self.language]
        user_prompt = (
            f"Rewrite the following sentence into a standard statement: {query}"
        )

        completion = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
        )

        normalized_query = completion.choices[0].message.content.strip()
        return normalized_query
