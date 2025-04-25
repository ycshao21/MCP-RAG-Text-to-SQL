import os
import json
from BaseAgent import *


SYSTEM_PROMPT = {"SQLAgent_generate": {}, "SQLAgent_adjust": {}}
SYSTEM_PROMPT["SQLAgent_generate"][
    "cn"
] = """
您是专为 Text-to-SQL 系统设计的 SQL 生成专家。您的任务是根据用户提供的任务描述和相关信息，生成准确、简洁的 SQL 查询语句。输出必须严格为纯 SQL 语句，不包含任何注释、说明、Markdown 格式或其他非 SQL 内容，以确保直接解析和执行。
"""
SYSTEM_PROMPT["SQLAgent_generate"][
    "en"
] = """
You are an SQL generation expert designed for Text-to-SQL systems. Your task is to generate precise and concise SQL queries based on the user's task description and additional information. The output must strictly be a pure SQL statement, with no comments, explanations, Markdown formatting, or any non-SQL content, to ensure seamless parsing and execution.
"""

SYSTEM_PROMPT["SQLAgent_adjust"][
    "cn"
] = """
您是专为 Text-to-SQL 系统设计的 SQL 调整专家。您的任务是根据用户提供的调整建议，修改原始 SQL 查询语句。输出必须严格为纯 SQL 语句，不包含任何注释、说明、Markdown 格式或其他非 SQL 内容，以确保直接解析和执行。
"""
SYSTEM_PROMPT["SQLAgent_adjust"][
    "en"
] = """
You are an SQL adjustment expert designed for Text-to-SQL systems. Your task is to modify the original SQL query based on the suggestions. The output must strictly be a pure SQL statement, with no comments, explanations, Markdown formatting, or any non-SQL content, to ensure seamless parsing and execution.
"""


USER_PROMPT = {}
USER_PROMPT["SQLAgent_generate"][
    "cn"
] = """
请为以下任务生成 SQL 查询：
任务描述：{description}
上下文信息：{info}
输出要求：仅返回纯 SQL 语句，不包含任何注释、说明或格式化内容。
"""

USER_PROMPT["SQLAgent_generate"][
    "en"
] = """
Please generate an SQL query for the following task:
Task Description: {description}
Context Information: {info}
Output Requirement: Return only the pure SQL statement, without any comments, explanations, or formatting.
"""

USER_PROMPT["SQLAgent_adjust"][
    "cn"
] = """
请根据以下调整建议修改 SQL 查询：
原始 SQL：{sql}
反馈：{feedback}
输出要求：仅返回修改后的纯 SQL 语句，不包含任何注释、说明或格式化内容。
"""
USER_PROMPT["SQLAgent_adjust"][
    "en"
] = """
Please modify the SQL query based on the following adjustment suggestions:
Original SQL: {sql}
Feedback: {feedback}
Output Requirement: Return only the modified pure SQL statement, without any comments, explanations, or formatting.
"""


class SQLAgent:
    def __init__(self):

        self.client = OpenAI(
            api_key=os.getenv("API_KEY"),
            base_url=os.getenv("BASE_URL"),
        )
        self.model = "deepseek-v3-250324"

        self.language = os.getenv("LANGUAGE", "en")

    def generate_sql(self, description, info) -> str:
        """
        function:
            Receive a string containing a task description and generate the corresponding SQL;
        args:
            description: query like "Query the mailbox of the user named 'yqxv2'."
        return:
            str: SQL
        """

        system_prompt = SYSTEM_PROMPT["SQLAgent_generate"][self.language]
        user_message = USER_PROMPT["SQLAgent_generate"][self.language].format(
            description=description,
            info=info,
        )

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_message,
                },
            ],
        )

        sql = response.choices[0].message.content.strip()

        # if not sql.upper().startswith(('SELECT', 'INSERT', 'UPDATE', 'DELETE')):
        #     raise ValueError("Generated response is not a valid SQL query")

        print(sql)
        return sql

    def adjust_sql(self, sql: str, feedback: str) -> str:
        """
        args:
            sql: "SELECT * FROM users WHERE username = 'yqxv2'"
            feedback: "table users not in database.Maybe its name is user?"
        return:
            str: SQL
        """

        system_prompt = SYSTEM_PROMPT["SQLAgent_adjust"][self.language]
        user_message = USER_PROMPT["SQLAgent_adjust"][self.language].format(
            sql=sql,
            feedback=feedback,
        )

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_message,
                },
            ],
        )
        modified_sql = response.choices[0].message.content.strip()

        # if not modified_sql.upper().startswith(
        #     ("SELECT", "INSERT", "UPDATE", "DELETE")
        # ):
        #     raise ValueError("Generated response is not a valid SQL query")

        print(modified_sql)
        return modified_sql


if __name__ == "__main__":
    sql = SQLAgent()

    sql.generate_sql(description="查询用户yqxv2的邮箱", info="数据库中的用户表名为user")

    sql.adjust_sql(
        sql="SELECT * FROM users WHERE username = 'yqxv2'",
        suggestions="table users not in database.Maybe its name is user?",
    )
