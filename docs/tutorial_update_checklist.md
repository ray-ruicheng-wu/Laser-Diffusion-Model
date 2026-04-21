# Tutorial Update Checklist

Use this checklist at the end of every milestone before the milestone is considered fully closed.

## Active documentation targets

Refresh the documents that are actually used as current entry points:

- `docs/project_model_walkthrough_zh.md`
- `docs/project_model_walkthrough_en.md`
- `docs/current-model-summary.md`
- `docs/physics_user_quickstart_zh.md`
- `docs/physics_user_quickstart_en.md`
- `docs/physics_parameter_manual_zh.md`
- `docs/physics_parameter_manual_en.md`

## Required updates

1. Add or revise the milestone summary in the main walkthrough or session log.
2. Update the code-structure section if new files or entry points were added.
3. Update the physics section if new governing equations, assumptions, or boundary conditions were introduced.
4. Update the numerical-method section if solver behavior, discretization, threshold handling, or validation logic changed.
5. Update the practical run guide if commands, output directories, or post-processing steps changed.
6. Update the parameter manual if new CLI switches or new physics parameters were added.
7. Update cross-links so the active docs point to each other correctly.

## Archive check

If an older document has been fully superseded:

1. Move it under `docs/archive/`
2. Add a short note to `docs/archive/README.md`
3. Remove it from active-document lists so it no longer looks like the current entry point

## Minimum expected output after each milestone

1. The milestone report exists.
2. The active main walkthrough is refreshed.
3. The quickstart still matches the real commands.
4. The parameter manual still matches the real parameters.
5. The active docs and the milestone report do not contradict each other.
