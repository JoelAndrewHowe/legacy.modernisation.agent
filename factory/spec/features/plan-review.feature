Feature: Plan review

  Plan review is a bounded, resumable cost gate. Rejections and their findings
  survive process exits, so restarting a run cannot silently buy another set of
  review rounds or lose the reason work did not begin.

  Background:
    Given a copy of the factory
    And a new target, with a seed describing a game of Tetris
    And the target has the machines planner, doer and validator
    And the target has an assembly line "careful" on which the doer's work is validated
    And the plan is reviewed by the three big brains before the doer on the "careful" line
    And a run named "tetris", on the "careful" line, with that seed and target
    And the planner plans the tasks alpha and beta
    And the doer does the next task in the plan
    And the plan-review synthesiser is never satisfied
    And a plan with one task, not done

  Rule: Rejected plan reviews retain actionable diagnostics

    Example: The rejection limit records its findings
      When the factory runs the "tetris" run
      Then the factory refuses
      And it reports that the persisted plan-review limit was reached
      And three rejected plan reviews are retained
      And the latest plan-review findings are retained

  Rule: Restarting does not reset the cost bound

    Example: A resumed run does not purchase more rejected reviews
      When the factory runs the "tetris" run
      And the factory runs the "tetris" run, given only its name
      Then the factory refuses
      And the plan-review synthesiser has been called three times
      And three rejected plan reviews are retained
