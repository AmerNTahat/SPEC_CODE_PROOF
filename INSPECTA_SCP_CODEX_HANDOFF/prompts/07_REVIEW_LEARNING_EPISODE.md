# Astra prompt contract — selective episode lesson (v1)
At an approved capture point (expert example, significant human correction, novel diagnostic, verified repair or scope proposal), identify at most the useful new engineering decisions supported by the episode. Avoid repeatedly restating existing rules or collecting expansive reflection after every command.

Record whether the episode outcome was already visible. Extract source-linked trigger, semantic choice, placement and repair gate, plus a candidate counterexample. Separate the correction that happened to work from the reason to expect transfer. If no reusable lesson is supported, return NO_NEW_RULE.

User Mode queues candidate lessons for a future release; it does not mutate current shared knowledge. All elicitation/re-elicitation draws from the existing parent budget.


Integrated contract:
Use workflow_goals and WORKFLOW_CONTRACT.md. Full-stack patterns and operation-specific preservation are required. All calls share the controller budget. Source/result/forecast identity and timing must be recorded. Do not publish or modify User releases without approval.
