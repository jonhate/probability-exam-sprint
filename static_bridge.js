/* Static web bridge: makes the existing ExamSprint UI work without Python.
   Only the preloaded course pack is included. Progress lives in localStorage. */
(() => {
  "use strict";
  const BASE = window.__EXAMSPRINT_DATA__;
  if (!BASE) throw new Error("data.js missing");
  const KEY = "examsprint.static.progress.v1";
  const NOW = () => new Date().toISOString();
  const clone = (x) => JSON.parse(JSON.stringify(x));

  let progress;
  try { progress = JSON.parse(localStorage.getItem(KEY) || "null"); } catch (_) { progress = null; }
  if (!progress || typeof progress !== "object") progress = clone(BASE.progress || {});
  progress.cards = progress.cards || {};
  progress.questions = progress.questions || {};
  progress.mock = progress.mock || { attempts: [] };
  progress.plan = progress.plan || {};

  function save() {
    try { localStorage.setItem(KEY, JSON.stringify(progress)); } catch (_) {}
  }

  function dueNow(st) {
    if (!st || !st.seen) return true;
    try { return new Date(st.due).getTime() <= Date.now(); } catch (_) { return true; }
  }

  function insights() {
    const a = BASE.project.analysis || {};
    const cards = a.cards || [];
    const questions = a.questions || [];
    const cp = progress.cards || {};
    const qp = progress.questions || {};
    let due = 0, seen = 0, masterySum = 0;
    cards.forEach((c) => {
      const st = cp[c.id] || {};
      if (st.seen) { seen += 1; masterySum += Number(st.mastery) || 0; }
      if (dueNow(st)) due += 1;
    });
    let attempts = 0, correct = 0;
    questions.forEach((q) => {
      (qp[q.id]?.attempts || []).forEach((x) => { attempts += 1; if (x.correct) correct += 1; });
    });
    const ma = progress.mock?.attempts || [];
    const last = Number(ma[ma.length - 1]?.percent || 0);
    const best = Math.max(0, ...ma.map((x) => Number(x.percent) || 0));
    const readiness = Math.max(0, Math.min(100, Math.round(
      0.30 * (seen / Math.max(1, cards.length) * 100) +
      0.30 * (masterySum / Math.max(1, seen)) +
      0.20 * (correct / Math.max(1, attempts) * 100) +
      0.20 * (last * .6 + best * .4)
    )));
    const topicRows = (a.topics || []).map((t) => {
      const tc = cards.filter((c) => c.topic_id === t.id).map((c) => cp[c.id] || {});
      const tm = tc.reduce((n, x) => n + (Number(x.mastery) || 0), 0) / Math.max(1, tc.length);
      const ta = questions.filter((q) => q.topic_id === t.id).flatMap((q) => qp[q.id]?.attempts || []);
      const acc = ta.filter((x) => x.correct).length / Math.max(1, ta.length) * 100;
      return { id: t.id, name: t.name, priority: t.priority, mastery: Math.round(.65 * tm + .35 * acc), cards_seen: tc.filter((x) => x.seen).length, cards_total: tc.length, answers: ta.length };
    });
    const planTotal = (a.plan || []).reduce((n, d) => n + (d.blocks?.length || 0), 0);
    const planDone = Object.values(progress.plan || {}).filter(Boolean).length;
    let daysLeft = null;
    try {
      const exam = new Date(`${BASE.project.exam_date}T00:00:00`);
      const today = new Date(); today.setHours(0, 0, 0, 0);
      daysLeft = Math.round((exam - today) / 86400000);
    } catch (_) {}
    let nextAction = "先做 10 题诊断，完成起点诊断";
    if (attempts || ma.length) {
      nextAction = due ? `先复习 ${due} 张到期/未看卡片` : "继续 M1–M4 模板训练";
      if (best >= 60 && best < 95 && due === 0) nextAction = "冲 80：补二维连续和变量函数";
      if (best >= 95) nextAction = "冲 100：三套真题重做 + 零失误检查";
    }
    return {
      readiness, card_total: cards.length, card_seen: seen, card_mastery: seen ? Math.round(masterySum / seen) : 0,
      due_cards: due, questions_total: questions.length, attempts, accuracy: Math.round(correct / Math.max(1, attempts) * 100),
      mock_count: ma.length, last_mock: Math.round(last), best_mock: Math.round(best),
      plan_total: planTotal, plan_done: planDone, topics: topicRows, days_left: daysLeft, next_action: nextAction,
    };
  }

  function state() {
    return {
      project: BASE.project,
      settings: { ...BASE.settings, has_key: false, key_hint: "" },
      progress,
      courses: [{ id: "static", name: BASE.project.course || "我的课程", status: BASE.project.status || "ready", docs: (BASE.project.docs || []).length, has_analysis: true, active: true }],
      active_course_id: "static",
      insights: insights(),
      server: { time: new Date().toISOString(), version: "static-1.0", active_job: false },
    };
  }

  function search(question) {
    const docs = BASE.corpus?.docs || [];
    const cjk = (question.match(/[\u4e00-\u9fff]/g) || []).join("");
    const tokens = new Set();
    (question.toLowerCase().match(/[a-z0-9]{2,}/g) || []).forEach((x) => tokens.add(x));
    for (let i = 0; i < cjk.length - 1; i++) tokens.add(cjk.slice(i, i + 2));
    const out = [];
    docs.forEach((doc) => (doc.pages || []).forEach((page) => {
      const text = page.text || "";
      if (text.length < 10) return;
      let score = 0;
      tokens.forEach((t) => { if (t && text.toLowerCase().includes(t)) score += 1; });
      if (question.length >= 3 && text.includes(question)) score += 4;
      if (score > 0) out.push({ score, doc_id: doc.doc_id, name: doc.name, locator: page.locator, text });
    }));
    out.sort((a, b) => b.score - a.score);
    return out.slice(0, 6);
  }

  function json(obj, status = 200) {
    return Promise.resolve(new Response(JSON.stringify(obj), { status, headers: { "Content-Type": "application/json; charset=utf-8" } }));
  }

  window.fetch = function (input, init) {
    const raw = typeof input === "string" ? input : (input && input.url) || "";
    const path = raw.split("?")[0];
    if (path.endsWith("/api/state")) return json({ ok: true, ...state() });
    if (path.endsWith("/api/health")) return json({ ok: true, time: NOW(), version: "static-1.0" });
    if (path.endsWith("/api/progress")) {
      let body = {};
      try { body = JSON.parse(init?.body || "{}"); } catch (_) {}
      const type = body.type;
      if (type === "card") {
        const st = progress.cards[body.id] || (progress.cards[body.id] = { seen: 0, mastery: 0, correct: 0 });
        st.seen = (Number(st.seen) || 0) + 1;
        st.last = NOW();
        const rating = body.rating || "good";
        if (rating === "again") { st.mastery = Math.max(0, (Number(st.mastery) || 0) - 8); st.due = new Date(Date.now() + 600000).toISOString(); }
        else if (rating === "hard") { st.mastery = Math.min(100, (Number(st.mastery) || 0) + 4); st.due = new Date(Date.now() + 86400000).toISOString(); }
        else if (rating === "easy") { st.mastery = Math.min(100, (Number(st.mastery) || 0) + 20); st.correct = (Number(st.correct) || 0) + 1; st.due = new Date(Date.now() + 4 * 86400000).toISOString(); }
        else { st.mastery = Math.min(100, (Number(st.mastery) || 0) + 12); st.correct = (Number(st.correct) || 0) + 1; st.due = new Date(Date.now() + 2 * 86400000).toISOString(); }
      } else if (type === "question") {
        const st = progress.questions[body.id] || (progress.questions[body.id] = { attempts: [] });
        st.attempts = (st.attempts || []).concat({ at: NOW(), correct: !!body.correct, answer: String(body.answer || "").slice(0, 2000) }).slice(-30);
      } else if (type === "mock") {
        progress.mock.attempts = (progress.mock.attempts || []).concat({ at: NOW(), score: Number(body.score) || 0, percent: Number(body.score) || 0, duration_minutes: Number(body.duration_minutes) || 0, detail: body.detail || {} }).slice(-50);
      } else if (type === "plan") {
        progress.plan[body.block_id || body.id] = !!body.done;
      } else return json({ ok: false, error: "未知进度类型" }, 400);
      save();
      return json({ ok: true, insights: insights() });
    }
    if (path.endsWith("/api/ask")) {
      let body = {};
      try { body = JSON.parse(init?.body || "{}"); } catch (_) {}
      const contexts = search(String(body.question || ""));
      if (!contexts.length) return json({ ok: true, answer: "资料中没有检索到相关内容。换一个更具体的术语试试。", sources: [] });
      const answer = "静态网页版没有接入大模型，先把资料原文给你：\n\n" + contexts.slice(0, 3).map((c) => `**${c.name} · ${c.locator}**\n${c.text.slice(0, 700)}`).join("\n\n");
      return json({ ok: true, answer, sources: contexts.slice(0, 5).map((c) => ({ name: c.name, locator: c.locator, quote: c.text.slice(0, 260) })) , offline: true });
    }
    return json({ ok: false, error: "静态网页版只包含已生成课程；上传、重新生成和修改设置请使用本地完整版。" }, 400);
  };

  // Hide controls that need the Python backend; keep print/export UI.
  const style = document.createElement("style");
  style.textContent = `
    body.static-mode [data-action="open-settings"],
    body.static-mode [data-action="generate"],
    body.static-mode [data-action="import-inbox"],
    body.static-mode [data-action="save-project-settings"],
    body.static-mode .dropzone,
    body.static-mode [data-export] { display:none !important; }
    body.static-mode .topbar-sub::after { content:" · 静态网页"; color:var(--accent); }
    body.static-mode .course-line { pointer-events:none; cursor:default; }
    body.static-mode .course-caret { display:none; }
  `;
  document.head.appendChild(style);
  document.body.classList.add("static-mode");
})();
