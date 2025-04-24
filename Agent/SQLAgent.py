import os
import json
from BaseAgent import *


class SQLAgent:
    def __init__(self):
        load_dotenv()
        self.client = OpenAI(
            api_key=os.getenv("API_KEY"),
            base_url=os.getenv("BASE_URL")
        )
        self.model = "deepseek-v3-250324"
            
    def generate_sql(self, description, info) -> str:
        """
        function:
            Receive a string containing a task description and generate the corresponding SQL;
        args:
            description: query like "Query the mailbox of the user named 'yqxv2'."
        return:
            str: SQL
        """

        user_message = f"""
        Generate SQL for the following task:  {description}
        Additional useful information: {info}
        Just return your SQL.Don return any other information like markdown format.It will make me trouble to parse.
        """

        messages = [
            {"role": "system", "content": "You can help user generate SQL."},
            {"role": "user", "content": user_message}
        ]

        response = self.client.chat.completions.create(
                        model=self.model,
                        messages=messages,
                    )
        print(response.choices[0].message.content)
        return response.choices[0].message.content
    
    def adjust_sql(self, sql: str, adjustment: str) -> str:
        """
        args:
            sql: "SELECT * FROM users WHERE username = 'yqxv2'"
            adjustment: "table users not in database.Maybe its name is user?"
        return:
            str: SQL
        """

        user_messages = f"""
        Modify the SQL statement based on the provided adjustment as follows:
        suggestions: {adjustment} 
        original SQL: {sql} 
        Just return your modified SQL.Don return any other information.It will make me trouble to parse.
        """

        messages = [
            {"role": "system", "content": "You can help user adjust SQL."},
            {"role": "user", "content": user_messages}
        ]

        response = self.client.chat.completions.create(
                        model=self.model,
                        messages=messages,
                    )
        print(response.choices[0].message.content)
        return response.choices[0].message.content


if __name__ == "__main__":
    sql = SQLAgent()
    
    # additional infomation needed
    sql.generate_sql(
                description="查询用户yqxv2的邮箱",
                info="数据库中的用户表名为user"
            )
    
    sql.adjust_sql(
                sql="SELECT * FROM users WHERE username = 'yqxv2'",
                adjustment="table users not in database.Maybe its name is user?"
            )



