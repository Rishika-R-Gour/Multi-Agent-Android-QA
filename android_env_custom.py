import android_world.registry as reg
from android_world import suite_utils

class AndroidEnv:
    def __init__(self, task_name="ClockTimerEntry", family="android_world"):
        # Load the task metadata
        reg_instance = reg.TaskRegistry()
        task_registry = reg_instance.get_registry(family)
        if task_name not in task_registry:
            raise ValueError(f"Task {task_name} not found in {family} tasks!")
        self.task = suite_utils._instantiate_task(task_registry[task_name])

    def reset(self):
        # Most tasks expose a 'reset_episode' or similar; fall back to start()
        if hasattr(self.task, "reset_episode"):
            return self.task.reset_episode()
        elif hasattr(self.task, "reset"):
            return self.task.reset()
        elif hasattr(self.task, "start"):
            return self.task.start()
        else:
            raise AttributeError("Task does not have a reset/start method!")

    def step(self, action):
        # Try to perform an action on the task
        if hasattr(self.task, "step"):
            return self.task.step(action)
        elif hasattr(self.task, "perform_action"):
            return self.task.perform_action(action)
        else:
            raise AttributeError("Task does not support step/action execution!")

    def close(self):
        if hasattr(self.task, "close"):
            self.task.close()
