# Implement-Plan Handoff

Finish automated validation and configured reviews before final handoff.

At the end, report:

- what changed
- final branch and PR link, if applicable
- review depth requested, rounds completed, lenses run, lenses skipped, and why
- disposition totals by lens
- validation commands and results
- plan/docs updated
- residual risks, validation gaps, or human decisions
- commands the user can run locally

Do not create HTML explanation or browser QA artifacts by default in this repository.
Use a short Markdown explanation unless the user specifically asks for another artifact.

If any required review or validation step could not be completed for real, say so
plainly instead of treating the implementation as done.
