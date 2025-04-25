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
        You are a SQL statement inspector. You can use the tools in MCP Server to execute SQL statements to obtain query results, and compare the query results with the original task to determine whether the SQL is correct.

        You have four tools available:
        1. all_table_names : return all table names in the database
        2. filter_table_names : return all table names in the database that contain the specified keyword
        3. schema_definitions : Get detailed schema for specified tables
        4. execute_query : run sql in database

        Please note the following points:
        1. If the SQL execution fails, it will directly return a mismatch and provide modification suggestions based on the SQL execution failure information
        2. Does the query only return the necessary fields related to the task description?
        3. Does the query result accurately reflect the intent of the task description?
        You don't need to rewrite the SQL statement.
        If the original SQL is incorrect, please give the reasons and suggestions for modification.
        Sometimes the SQL is correct, but there may no rows returned because there is no data in the database.

        Please fill in your answer in the following format:
        Result: <query_result_here>
        Match: <True or False>
        Check completed: <True or False if there are other tools to use for getting more information>
        Adjustment: <suggestion_for_adjusting_the_sql_statement_if_match_is_false>
        """

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
