from harness_ai_learning.domain import ActionHandler, ActionRegistry, ActionRequest, ActionResult, AgentState, IterationPolicy, LoopActor, LoopEvaluator, LoopResult, RunContext, StepResult


class RegisteredActionRegistry:
    def __init__(self, handlers: dict[str, ActionHandler]) -> None:
        self._handlers = handlers

    def get(self, action_name: str) -> ActionHandler:
        handler = self._handlers.get(action_name)
        if handler is None:
            raise KeyError(f"未注册的动作: {action_name}")
        return handler


class ActionExecutor:
    def __init__(self, registry: ActionRegistry) -> None:
        self._registry = registry

    def execute(self, request: ActionRequest, context: RunContext, state: AgentState) -> ActionResult:
        handler = self._registry.get(request.action_name)
        return handler.execute(request, context, state)


class HarnessLoop:
    def __init__(self, *, actor: LoopActor, executor: ActionExecutor, evaluator: LoopEvaluator, policy: IterationPolicy) -> None:
        self._actor = actor
        self._executor = executor
        self._evaluator = evaluator
        self._policy = policy

    def run(self, context: RunContext) -> LoopResult:
        state = AgentState()

        while True:
            state.iteration += 1
            state.latest_step = "observe"
            state.latest_observation = f"准备分析文件: {context.input_path.name}"
            state.history.append(StepResult(step_name="observe", status="success", message=state.latest_observation))

            state.latest_step = "decide"
            request = self._actor.build_request(context, state)
            state.latest_request = request
            state.latest_plan = f"计划执行动作: {request.action_name}"
            state.history.append(
                StepResult(
                    step_name="decide",
                    status="success",
                    message=state.latest_plan,
                    payload={
                        "action_name": request.action_name,
                        "mode": request.arguments.get("mode"),
                        "feedback_tags": request.arguments.get("feedback_tags", []),
                    },
                )
            )

            state.latest_step = "act"
            action_result = self._executor.execute(request, context, state)
            state.latest_action_result = action_result
            state.latest_action = action_result.action_name
            if action_result.output is not None:
                state.final_output = action_result.output
            state.history.append(
                StepResult(
                    step_name="act",
                    status="success" if action_result.status == "success" else "error",
                    message=action_result.message,
                    payload={"action_name": action_result.action_name, **action_result.metadata},
                )
            )

            state.latest_step = "verify"
            evaluation = self._evaluator.evaluate(context, state)
            state.latest_evaluation = evaluation
            state.history.append(
                StepResult(
                    step_name="verify",
                    status="success",
                    message=evaluation.summary,
                    payload={
                        "score": evaluation.score,
                        "passed": evaluation.passed,
                        "feedback_tags": evaluation.feedback_tags,
                    },
                )
            )

            state.latest_step = "update_state"
            state.history.append(
                StepResult(step_name="update_state", status="success", message="已根据本轮执行结果更新状态")
            )

            state.latest_step = "continue_or_stop"
            decision = self._policy.decide(context, state)
            state.history.append(
                StepResult(
                    step_name="continue_or_stop",
                    status="success",
                    message=decision.reason,
                    payload={"should_continue": decision.should_continue},
                )
            )

            if not decision.should_continue:
                return LoopResult(context=context, state=state, decision=decision)
