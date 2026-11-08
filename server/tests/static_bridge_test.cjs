// Regression checks for the browser-only bridge. No browser or server required.
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const path = require('node:path');

const root = path.join(__dirname, '..');
const store = new Map();
const localStorage = {
  fail: false,
  getItem(key) { return store.has(key) ? store.get(key) : null; },
  setItem(key, value) {
    if (this.fail) throw new Error('quota exceeded');
    store.set(key, String(value));
  },
  removeItem(key) { store.delete(key); },
};
const element = () => ({
  style: {}, classList: { add() {}, remove() {}, toggle() {} },
  appendChild() {}, remove() {}, addEventListener() {},
  set textContent(v) {}, get textContent() { return ''; },
});
const context = {
  console, setTimeout, clearTimeout, setInterval, clearInterval,
  Response,
  localStorage,
  navigator: {},
  location: { protocol: 'http:' },
  document: {
    createElement: element,
    head: { appendChild() {} },
    body: { classList: { add() {} }, appendChild() {} },
  },
  addEventListener() {},
  alert() {},
};
context.window = context;
vm.runInNewContext(fs.readFileSync(path.join(root, 'web/data.js'), 'utf8'), context);
vm.runInNewContext(fs.readFileSync(path.join(root, 'web/static_bridge.js'), 'utf8'), context);

(async () => {
  const initial = await (await context.fetch('/api/state')).json();
  assert.equal(initial.analysis_revision, context.__EXAMSPRINT_DATA__.analysis_revision, 'state exposes content revision');
  const request = (body) => context.fetch('/api/progress', { method: 'POST', body: JSON.stringify(body) });
  const invalid = await request({ type: 'question', id: 's2q02', assessment: 'self', correct: true, completed_steps: [] });
  assert.equal(invalid.status, 400, 'incomplete self-grade is rejected');
  const missing = await request({ type: 'question', id: 'missing', correct: true });
  assert.equal(missing.status, 404, 'unknown question is rejected');

  const validBody = {
    type: 'question', id: 's2q02', assessment: 'self', correct: true,
    completed_steps: [0, 1], assisted: false, answer_exposed: false,
  };
  const before = await (await context.fetch('/api/state')).json();
  localStorage.fail = true;
  const failed = await request(validBody);
  assert.equal(failed.status, 507, 'storage failure is explicit');
  const afterFailure = await (await context.fetch('/api/state')).json();
  assert.equal(afterFailure.progress.questions.s2q02, before.progress.questions.s2q02, 'failed write is rolled back');
  localStorage.fail = false;
  const saved = await request(validBody);
  assert.equal(saved.status, 200, 'retry succeeds after storage recovers');
  const after = await (await context.fetch('/api/state')).json();
  assert.equal(after.progress.questions.s2q02.attempts.length, 1, 'retry appends one record');
  console.log('STATIC BRIDGE TESTS PASSED (validation, explicit storage failure, retry)');
})().catch((err) => { console.error(err); process.exitCode = 1; });
