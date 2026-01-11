import asyncio
from pathlib import Path

from packages.workflow.resume_manager import ResumeManager
from packages.workflow.step_executor import IdempotentStepExecutor
from packages.workflow.progress_tracker import ProgressTracker


def test_idempotent_step_executor_skips_on_same_input(tmp_path: Path):
    resume = ResumeManager(tmp_path / "state.json")
    state = resume.load()

    calls = {"n": 0}

    async def action(inputs):
        calls["n"] += 1
        await asyncio.sleep(0)
        return {"ok": True, "inputs": inputs}

    events = []
    tracker = ProgressTracker(on_event=lambda e: events.append(e), publish_to_bus=False)
    exec = IdempotentStepExecutor(resume, tracker=tracker)

    step_cfg = {"id": "demo", "action": action, "inputs": {"a": 1}}

    asyncio.run(exec.execute_step(state, step_cfg))
    assert calls["n"] == 1

    # Reload state and run again with same inputs -> should skip
    state2 = resume.load()
    asyncio.run(exec.execute_step(state2, step_cfg))
    assert calls["n"] == 1

    skipped = [e for e in events if e.get("event") == "step.skipped" and e.get("step_id") == "demo"]
    assert skipped


def test_idempotent_step_executor_reruns_on_input_change(tmp_path: Path):
    resume = ResumeManager(tmp_path / "state.json")
    state = resume.load()

    calls = {"n": 0}

    def action(inputs):
        calls["n"] += 1
        return inputs

    exec = IdempotentStepExecutor(resume, tracker=ProgressTracker(publish_to_bus=False))

    asyncio.run(exec.execute_step(state, {"id": "demo", "action": action, "inputs": {"a": 1}}))
    assert calls["n"] == 1

    state2 = resume.load()
    asyncio.run(exec.execute_step(state2, {"id": "demo", "action": action, "inputs": {"a": 2}}))
    assert calls["n"] == 2

