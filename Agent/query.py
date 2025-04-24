import os
from openai import OpenAI
from dotenv import load_dotenv

class Rewriter:
    """
    用于将用户输入转换为陈述句
    """
    def __init__(self):
        load_dotenv()
        api_key = os.getenv("API_KEY")
        base_url = os.getenv("BASE_URL")
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.system_prompt = """
        You are a helpful assistant. You can help user rewrite the sentence as a statement.
        For example, 
        Rewrite the following sentence as a statement: What is the capital of France?
        You can answer like this: Check the capital of France.
        If the sentence is already a statement, you can just return the original sentence.
        """

    def rewrite(self, query: str) -> str:
        """
        将用户输入转换为陈述句。

        args:
            query (str): 用户的输入语句

        return:
            str: 转换后的陈述句
        """
        completion = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": "Rewrite the following sentence as a statement: " + query},
            ],
        )
        return completion.choices[0].message.content



