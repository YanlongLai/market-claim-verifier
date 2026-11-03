// Public aggregate only; the private Worker reads the atomic spend ledger.
export { onBudget as onRequest } from "../../workers/pages/check.mjs";
