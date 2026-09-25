# ADR 004: Authorization in application code

## Decision

Every submission read, and every tool execution, checks a principal in Python before data is loaded for the model. The system prompt is not part of that control. Cross-tenant submission reads return 404.

Roles:

- `UNDERWRITER` reads submissions assigned to them.
- `MANAGER` reads submissions in their team.
- `ADMIN` reads all.

`get_company` and `get_company_claims` are allowed only when the principal can read a submission for that company, or is an admin.

## Why

A model will follow instructions found in a submission or a guideline. Those instructions must not be able to widen a query. Section 8 of the requirements asks for a test where user A cannot read user B's submission.

## Alternatives

- Row filters described only in the prompt. This fails the security requirement and fails open under injection.
- Enforce entitlement only at the HTTP layer. Tool calls would become a second, unchecked path.

## Trade-off

404 hides whether an id exists. That is what we want for submissions. Admin-only maintenance routes can still return 403, because the caller already knows the route exists.
