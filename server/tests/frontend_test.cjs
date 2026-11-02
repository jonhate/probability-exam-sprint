// No browser dependencies: exercise the UI state and persistence logic in a VM.
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const path = require('node:path');
let source = fs.readFileSync(path.join(__dirname, '../static/app.js'), 'utf8');
source = source.slice(0, source.indexOf('  document.addEventListener("click"'));
source = source.replace('  function render() {', '  function render() { return;');
source = source.replace('  function toast(message, type = "") {', '  function toast(message, type = "") { return;');
source += '\nglobalThis.testUI = { S, load, startPractice, submitPractice, selfGradePractice, wrongQuestions, dueCard, renderFlashcards, renderMockResult, saveMock }; })();';
let fail = false;
let response = {};
let lastRequest;
const context = {
  document: { querySelector: () => null, querySelectorAll: () => [], addEventListener() {} },
  fetch: async (url, init) => {
    lastRequest = { url, init };
    if (fail) throw new Error('offline');
    return { ok: true, json: async () => response };
  },
  console, setTimeout, clearTimeout, setInterval, clearInterval,
};
vm.runInNewContext(source, context);
const ui = context.testUI;
const data = () => ({ active_course_id: '课程一', analysis_revision: 'rev1', project: { analysis: {
  topics: [{ id: 't1', priority: 90 }],
  cards: [{ id: 'c1' }],
  questions: [
    { id: 'q1', topic_id: 't1', type: 'single', answer: 'A', options: ['yes', 'no'] },
    { id: 'q2', topic_id: 't1', type: 'single', answer: 'B', options: ['yes', 'no'] },
  ],
}}, progress: { cards: {}, questions: { q1: { attempts: [{ correct: true }] } } }, insights: {} });

(async () => {
  ui.S.data = data();
  ui.startPractice('1');
  assert.equal(ui.S.practice.questions[0].id, 'q2', 'unseen questions come before previously correct questions');
  ui.S.practice.selected = ['A'];
  response = { insights: {}, progress: { cards: {}, questions: { q2: { attempts: [{ correct: false }] } } } };
  await ui.submitPractice();
  assert.equal(ui.wrongQuestions()[0].q.id, 'q2', 'wrong book updates without refresh');
  assert.equal(lastRequest.init.headers['X-Course-ID'], encodeURIComponent('课程一'));
  assert.equal(lastRequest.init.headers['X-Analysis-Revision'], 'rev1');
  ui.startPractice('1');
  ui.S.practice.selected = ['A'];
  fail = true;
  await ui.submitPractice();
  assert.equal(ui.S.practice.submitted, false, 'failed save remains retryable');
  assert.equal(ui.S.practice.answered, 0);
  fail = false;

  ui.S.data.progress.cards.c1 = { seen: 1, due: new Date(Date.now() + 86400000).toISOString() };
  ui.S.cardDueOnly = true;
  ui.S.cardOrder = [];
  assert.match(ui.renderFlashcards(), /本轮到期卡片已复习完/);
  ui.S.data.progress.cards.c1.due = 'bad date';
  assert.equal(ui.dueCard({ id: 'c1' }), true);

  const q = { id: 'm1', type: 'short', maxScore: 10, stem: 'test', rubric: '<img src=x onerror=alert(1)>', explanation: '<script>bad</script>' };
  ui.S.mock = { status: 'submitted', selfScores: { m1: 10000 }, result: { totalPossible: 10, items: [{ q, isOpen: true, points: 0 }] } };
  const html = ui.renderMockResult();
  assert.match(html, /100<small/);
  assert(!html.includes('<img src=x'));
  assert(!html.includes('<script>bad'));
  assert(html.includes('&lt;img'));

  response = { ...data(), active_course_id: '课程二', analysis_revision: 'rev2' };
  ui.S.practice = { questions: [] };
  ui.S.askHistory = [{ text: 'old course' }];
  await ui.load();
  assert.equal(ui.S.mock, null);
  assert.equal(ui.S.practice, null);
  assert.equal(ui.S.askHistory.length, 0);
  console.log('FRONTEND TESTS PASSED (selection, persistence, due queue, scoring, escaping, course reset)');
})().catch((err) => { console.error(err); process.exitCode = 1; });
