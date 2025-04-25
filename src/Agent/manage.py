import json
import os
from typing import Dict
from CheckAgent import CheckAgent
from SQLAgent import SQLAgent
import asyncio

class TaskManager:
    def __init__(self):
        self.sql_agent = SQLAgent()
        self.check_agent = CheckAgent()
        self.final_result = ""

    # def _load_tasks(self) -> Dict[str, Dict[str, str]]:
    #     with open(self.task_file, 'r', encoding='utf-8') as f:
    #         return json.load(f)


    def _save_tasks(self):
        with open(self.task_file, 'w', encoding='utf-8') as f:
            json.dump(self.tasks, f, ensure_ascii=False, indent=4)

    async def execute_tasks(self):
        """执行所有任务并保存结果"""
        for task_id, task_data in self.tasks.items():
            description = task_data["description"]
            print(f"执行任务: {task_id} - {description}")

            # 第一次生成sql没有额外信息
            sql = self.sql_agent.generate_sql(description, None)
            self.tasks[task_id]["sql"] = sql
            print(f"对于任务 {description} 生成的SQL: {sql}")

            try:
                await self.check_agent.connect_to_server(
                    command="uvx",
                    args=["--from", "mcp-alchemy==2025.04.16.110003", "--with", "pymysql", "--refresh-package", "mcp-alchemy", "mcp-alchemy"],
                    env={"DB_URL": os.getenv("DB_URL")},
                )

                max_attempts = 3
                current_sql = sql
                for attempt in range(max_attempts):
                    result, is_match, adjustment = await self.check_agent.run(description, current_sql)
                    self.tasks[task_id]["result"] = result

                    if is_match or not adjustment:
                        break  

                    current_sql = self.sql_agent.adjust_sql(current_sql, adjustment)
                    self.tasks[task_id]["sql"] = current_sql
                    print(f"第{attempt + 1}次调整后的SQL: {current_sql}")
            except Exception as e:
                print(f"执行任务 {task_id} 时出错: {str(e)}")
                self.tasks[task_id]["result"] = f"错误: {str(e)}"

            self._save_tasks()

        await self.check_agent.cleanup()
        print("所有任务执行完毕")
        # task中最后一个的sql是最终结果
        self.final_result = self.tasks[list(self.tasks.keys())[-1]]["sql"]
        return self.final_result
    
if __name__ == "__main__":
    manager = TaskManager()
    asyncio.run(manager.execute_tasks())
    print(manager.final_result)