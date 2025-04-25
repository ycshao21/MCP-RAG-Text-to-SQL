from typing import Dict, List, Any, Tuple
from .BaseAgent import *
import re
import os


def parse_response(response: str):
    result_match = re.search(r"Result:\s*(.*?)(?=\nMATCH:|\Z)", response, re.DOTALL)
    result = result_match.group(1).strip() if result_match else ""

    match_match = re.search(r"Match:\s*(True|False)", response)
    is_match = match_match.group(1) == "True" if match_match else False

    Check_completed_match = re.search(r"Check completed:\s*(True|False)", response)
    Check_completed = (
        Check_completed_match.group(1) == "True" if Check_completed_match else False
    )

    adjustment_match = re.search(r"Adjustment:\s*(.*)", response, re.DOTALL)
    adjustment = adjustment_match.group(1).strip() if adjustment_match else ""

    return result, is_match, Check_completed, adjustment


class CheckAgent(BaseClient):
    async def run(self, description: str, sql: str):
        system_prompt = f"""
        您是一个 SQL 语句检查器。您的任务是使用 MCP Server 中的工具执行给定的 SQL 语句，获取查询结果，并将其与原始任务描述进行比较，以判断 SQL 是否正确。您不得修改或重写给定的 SQL 语句，即使您认为它可能有错误。

        您可以使用以下四种工具：
        1. all_table_names：返回数据库中所有表名
        2. filter_table_names：返回数据库中包含指定关键字的所有表名
        3. schema_definitions：获取指定表的详细架构
        4. execute_query：在数据库中运行 SQL

        请遵循以下指导原则：
        1. 如果 SQL 执行失败，立即判定 SQL 不正确，并根据错误信息报告问题原因。不要尝试修正 SQL。
        2. 检查 SQL 是否仅返回与任务描述相关的必要字段。
        3. 验证查询结果是否准确反映任务描述的意图。
        4. 如果查询返回空结果，考虑任务描述是否允许这种情况。例如，如果任务是查找符合条件的记录，且没有匹配的数据，空结果可能是正确的；但如果任务要求返回数据（如计算平均值），空结果可能表明 SQL 有误。

        重要说明：您不得重写或修正 SQL 语句。如果 SQL 不正确，请提供描述性的建议，说明可能的问题及如何调整，但不要提供新的 SQL 语句。

        示例 1：
        任务：查找 2020 年后入职的所有员工
        SQL：SELECT * FROM employees WHERE join_date > '2020-01-01'
        结果：[员工列表]
        匹配：True
        检查完成：True
        调整建议：无

        示例 2：
        任务：计算员工的平均薪资
        SQL：SELECT AVG(salary) FROM employees WHERE department = 'Sales'
        结果：错误：表 'employees' 中不存在 'department' 列
        匹配：False
        检查完成：True
        调整建议：SQL 假定存在 'department' 列，但实际不存在。建议检查表架构以确认可用列，并相应调整查询。

        请按以下格式填写您的回答：
        Result: <查询结果>
        Match: <True 或 False>
        Check completed: <True 或 False，如果需要更多工具获取信息则为 False>
        Adjustment: <如果匹配为 False，描述可能的问题及调整建议>
        """

        # system_prompt = f"""
        # You are a SQL statement inspector. You can use the tools in MCP Server to execute SQL statements to obtain query results, and compare the query results with the original task to determine whether the SQL is correct.

        # You have four tools available:
        # 1. all_table_names : return all table names in the database
        # 2. filter_table_names : return all table names in the database that contain the specified keyword
        # 3. schema_definitions : Get detailed schema for specified tables
        # 4. execute_query : run sql in database

        # Please note the following points:
        # 1. If the SQL execution fails, it will directly return a mismatch and provide modification suggestions based on the SQL execution failure information
        # 2. Does the query only return the necessary fields related to the task description?
        # 3. Does the query result accurately reflect the intent of the task description?
        # You don't need to rewrite the SQL statement.
        # If the original SQL is incorrect, please give the reasons and suggestions for modification.
        # Sometimes the SQL is correct, but there may no rows returned because there is no data in the database.

        # Please fill in your answer in the following format:
        # Result: <query_result_here>
        # Match: <True or False>
        # Check completed: <True or False if there are other tools to use for getting more information>
        # Adjustment: <suggestion_for_adjusting_the_sql_statement_if_match_is_false>
        # """

        base_query = f"""
        Task Description: {description}
        SQL Query: {sql}
        """

        response = await self.process_query(base_query, system_prompt=system_prompt)
        result, is_match, check_completed, adjustment = parse_response(response)
        print(
            f"Initial result: {result}, Match: {is_match}, Check completed: {check_completed}, Adjustment: {adjustment}"
        )

        if check_completed:
            return result, is_match, check_completed, adjustment

        # Now retry with adjustments if available
        max_attempts = 3
        attempt = 0
        while not check_completed and attempt < max_attempts:
            if not adjustment:
                break

            # Append adjustment to query
            adjusted_query = base_query + f"\nAdjustment: {adjustment}"
            response = await self.process_query(
                adjusted_query, system_prompt=system_prompt
            )
            result, is_match, check_completed, adjustment = parse_response(response)

            if check_completed:
                break

            attempt += 1
            print(
                f"Attempt {attempt}: Result: {result}, Match: {is_match}, Check completed: {check_completed}, Adjustment: {adjustment}"
            )

        return result, is_match, check_completed, adjustment


if __name__ == "__main__":
    load_dotenv()

    async def main():
        check = CheckAgent()
        await check.connect_to_server(
            command="uvx",
            args=[
                "--from",
                "mcp-alchemy==2025.04.16.110003",
                "--with",
                "pymysql",
                "--refresh-package",
                "mcp-alchemy",
                "mcp-alchemy",
            ],
            env={"DB_URL": os.getenv("DB_URL")},
        )

        await check.run(
            description="查询用户yqxv2的邮箱",
            # sql="SELECT * FROM users WHERE username = 'yqxv2'"
            sql="SELECT * FROM email WHERE username = 'yqxv2';",
        )

        await check.cleanup()

    asyncio.run(main())
