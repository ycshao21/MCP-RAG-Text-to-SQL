from typing import Dict, List, Any, Tuple
from CheckAgent import CheckAgent
from SQLAgent import SqlAgent
import json


class TaskManager:
    def __init__(self, task_file:str="task.json"):
        self.task_file = task_file
        self.tasks = self._load_tasks()
        self.sql_agent = SqlAgent()
        self.check_agent = CheckAgent()

    def _load_tasks(self) -> Dict[str, Dict[str, str]]:
        with open(self.task_file, 'r', encoding='utf-8') as f:
            return json.load(f)


    def _save_tasks(self):
        with open(self.task_file, 'w', encoding='utf-8') as f:
            json.dump(self.tasks, f, ensure_ascii=False, indent=4)

    async def execute_tasks(self):
        """执行所有任务并保存结果"""
        for task_id, task_data in self.tasks.items():
            description = task_data["description"]
            print(f"执行任务: {task_id} - {description}")

            # 生成SQL
            sql = await self.sql_agent.run(description)
            self.tasks[task_id]["sql"] = sql
            print(f"生成的SQL: {sql}")

            # 检查SQL
            try:
                result, is_match, adjustment = await self.check_agent.run(description, sql)
                self.tasks[task_id]["result"] = result

                # 如果SQL不匹配，尝试调整
                if not is_match and adjustment:
                    print(f"SQL需要调整: {adjustment}")
                    adjusted_sql = await self.sql_agent.run(description, result=result)
                    self.tasks[task_id]["sql"] = adjusted_sql
                    print(f"调整后的SQL: {adjusted_sql}")

                    # 再次检查调整后的SQL
                    new_result, new_is_match, _ = await self.check_agent.run(description, adjusted_sql)
                    self.tasks[task_id]["result"] = new_result
            except Exception as e:
                print(f"执行任务 {task_id} 时出错: {str(e)}")
                self.tasks[task_id]["result"] = f"错误: {str(e)}"

            # 保存当前进度
            self._save_tasks()

        # 关闭所有会话
        await self.sql_agent.client.close_all_sessions()
        await self.check_agent.client.close_all_sessions()

        return self.tasks