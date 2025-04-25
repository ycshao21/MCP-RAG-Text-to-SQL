import json
import os
from typing import Dict
from .CheckAgent import CheckAgent
from .SQLAgent import SQLAgent
import asyncio


class TaskManager:
    def __init__(self):
        self.sql_agent = SQLAgent()
        self.check_agent = CheckAgent()

        self.final_sql = ""
        self.final_result = ""

        self.save_path = "./outputs/tasks_{query_idx}.json"

    def _save_tasks(self, tasks, query_idx=None):
        """保存任务到文件"""
        save_path = self.save_path.format(query_idx=query_idx)
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(tasks, f, ensure_ascii=False, indent=4)

    async def execute_tasks(self, tasks: dict, context: str, query_idx=None):
        """执行所有任务并保存结果"""
        descriptions = [task["description"] for task in tasks.values()]
        sqls = []
        for i, (task_id, _) in enumerate(tasks.items()):
            description = descriptions[i]
            print(f"执行任务: {task_id} - {description}")

            # 第一次生成sql没有额外信息
            sql = self.sql_agent.generate_sql(
                descriptions=descriptions,
                prev_sqls=sqls,
                index=i,
                context=context,
            )
            tasks[task_id]["sql"] = sql
            sqls.append(sql)
            print(f"对于任务 {description} 生成的SQL: {sql}")

            try:
                await self.check_agent.connect_to_server(
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

                max_attempts = 3
                current_sql = sql
                for attempt in range(max_attempts):
                    result, is_match, check_completed, adjustment = (
                        await self.check_agent.run(description, current_sql)
                    )

                    if is_match:
                        tasks[task_id]["sql"] = current_sql
                        tasks[task_id]["result"] = result
                        print(f"Current SQL: {current_sql}")
                        break
                    else:
                        current_sql = self.sql_agent.adjust_sql(current_sql, adjustment)
                        tasks[task_id]["sql"] = current_sql
                        print(f"第{attempt + 1}次调整后的SQL: {current_sql}")
            except Exception as e:
                print(f"执行任务 {task_id} 时出错: {str(e)}")
                tasks[task_id]["result"] = f"错误: {str(e)}"

            self._save_tasks(tasks, query_idx)

        await self.check_agent.cleanup()

        print("所有任务执行完毕")

        self.final_sql = tasks[list(tasks.keys())[-1]]["sql"]
        self.final_result = tasks[list(tasks.keys())[-1]]["result"]
        return (self.final_sql, self.final_result)


if __name__ == "__main__":
    manager = TaskManager()
    asyncio.run(manager.execute_tasks())
    print(manager.final_sql)
