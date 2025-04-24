from typing import Dict, List, Any, Tuple
from BaseAgent import *
import re

def parse_response(response: str):
    result_match = re.search(r"RESULT:\s*(.*?)(?=\nMATCH:|\Z)", response, re.DOTALL)
    result = result_match.group(1).strip() if result_match else ""

    match_match = re.search(r"MATCH:\s*(True|False)", response)
    is_match = match_match.group(1) == "True" if match_match else False

    adjustment_match = re.search(r"ADJUSTMENT:\s*(.*)", response, re.DOTALL)
    adjustment = adjustment_match.group(1).strip() if adjustment_match else ""

    return result, is_match, adjustment


class CheckAgent(BaseClient):
    async def run(self, description: str, sql: str) -> Tuple[str, bool, str]:
        system_prompt = f"""
        You are a SQL statement inspector. You can use the tools in MCP Server to execute SQL statements to obtain query results, and compare the query results with the original task to determine whether the SQL is correct.
        Please note the following points:
        1. If the SQL execution fails, it will directly return a mismatch and provide modification suggestions based on the SQL execution failure information
        2. Does the query only return the necessary fields related to the task description?
        3. Does the query result accurately reflect the intent of the task description?
        Please fill in your answer in the following format:
        Result: <query_result_here>
        Match: <True or False>
        Adjustment: <suggestion_for_adjusting_the_sql_statement_if_match_is_false>
        """

        query = f"""
        Task Description: {description}
        SQL Query: {sql}
        """

        response = await self.process_query(query, system_prompt=system_prompt)
        print(response)
        return response
    
if __name__ == "__main__":
    async def main():
        check = CheckAgent()
        await check.connect_to_server(
                command="uvx",
                args=["--from", "mcp-alchemy==2025.04.16.110003", "--with", "pymysql", "--refresh-package", "mcp-alchemy", "mcp-alchemy"],
                env={"DB_URL": "mysql+pymysql://zhtest:Zenx_2eetheeT6@192.168.10.232:3306/zhtest"},
            )
        
        await check.run(
            description="查询用户yqxv2的邮箱",
            sql="SELECT * FROM users WHERE username = 'yqxv2'"
        )

        await check.cleanup()

    asyncio.run(main())
