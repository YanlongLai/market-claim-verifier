// Public aggregate only; the Access-protected origin reads the SQLite ledger.
export { onBudget as onRequest } from "../../workers/pages/check.mjs";
