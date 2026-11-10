/* Static web bridge: makes the existing ExamSprint UI work without Python.
   Only the preloaded course pack is included. Progress lives in localStorage. */
(() => {
  "use strict";
  const BASE = window.__EXAMSPRINT_DATA__;
  if (!BASE) throw new Error("data.js missing");
  const KEY = "examsprint.static.progress.v1";
  const CONTENT_REV = String(BASE.analysis_revision || "legacy");
  const NOW = () => new Date().toISOString();
  const clone = (x) => JSON.parse(JSON.stringify(x));

  let progress;
  try { progress = JSON.parse(localStorage.getItem(KEY) || "null"); } catch (_) { progress = null; }
  if (!progress || typeof progress !== "object") progress = clone(BASE.progress || {});
  const hadVersionMeta = !!(progress.meta && progress.meta.analysis_revision);
  // A changed course pack must not silently inherit old question evidence.
  if (progress.meta && progress.meta.analysis_revision && progress.meta.analysis_revision !== CONTENT_REV) {
    try { localStorage.setItem(`${KEY}.archive.${progress.meta.analysis_revision}`, JSON.stringify(progress)); } catch (_) {}
    progress = clone(BASE.progress || {});
  }
  progress.cards = progress.cards || {};
  progress.questions = progress.questions || {};
  progress.mock = progress.mock || { attempts: [] };
  const legacyProgress = !hadVersionMeta && Object.values(progress.questions).some((row) => (row?.attempts || []).length);
  progress.meta = { course_id: "static", analysis_revision: CONTENT_REV, legacy: legacyProgress };
  if (legacyProgress) {
    Object.values(progress.questions).forEach((row) => {
      (row?.attempts || []).forEach((attempt) => { attempt.legacy = true; });
    });
  }
  progress.plan = progress.plan || {};
  progress.preferences = progress.preferences || {};
  const PROJECT_KEY = "examsprint.static.project.v1";
  try {
    const savedProject = JSON.parse(localStorage.getItem(PROJECT_KEY) || "null");
    if (savedProject && typeof savedProject === "object") Object.assign(BASE.project, savedProject);
  } catch (_) {}

  function save() {
    // Let storage failures reach the route so the UI never claims a record was saved.
    localStorage.setItem(KEY, JSON.stringify(progress));
  }

  function storageError() {
    return json({
      ok: false,
      code: "STORAGE_WRITE_FAILED",
      error: "本地存储写入失败，记录尚未保存。请清理浏览器空间后重试。",
    }, 507);
  }

  function dueNow(st) {
    if (!st || !st.seen) return true;
    try { return new Date(st.due).getTime() <= Date.now(); } catch (_) { return true; }
  }

  // Keep the static mobile build behavior-compatible with engine/learning.py.
  function numberValue(value, fallback = 0) {
    const n = Number(value);
    return Number.isFinite(n) ? n : fallback;
  }
  function checkpoints(q) {
    if (Array.isArray(q?.rubric_points)) {
      return q.rubric_points
        .filter((p) => p && typeof p === "object")
        .map((p) => String(p.text || p.label || "").trim())
        .filter(Boolean).slice(0, 12);
    }
    return String(q?.rubric || "").split(/[；;\n]+/).map((s) => s.trim()).filter(Boolean).slice(0, 12);
  }
  function questionMinutes(q) {
    const fallback = ["single", "multiple", "judge"].includes(q?.type) ? 3 : 10;
    return Math.max(1, Math.min(30, Math.round(numberValue(q?.estimated_minutes, fallback))));
  }
  function parsedTime(value) {
    if (!value) return null;
    const d = new Date(value);
    return Number.isNaN(d.getTime()) ? null : d;
  }
  function sameLocalDay(a, b) {
    return a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth() && a.getDate() === b.getDate();
  }
  function evidenceAttempt(x) {
    return x?.correct === true && x?.assisted === false && x?.evidence_version === 1
      && !x?.partial && !x?.answer_exposed && !x?.legacy;
  }
  function buildLearning(now = new Date()) {
    const a = BASE.project.analysis || {};
    const qs = a.questions || [];
    const topics = a.topics || [];
    const history = progress.questions || {};
    const prefs = progress.preferences || {};
    const session = Math.max(5, Math.min(60, Math.trunc(numberValue(prefs.session_minutes, 15))));
    const daily = Math.max(30, Math.min(960, Math.round(numberValue(BASE.project.hours_per_day, 5) * 60)));
    const elapsed = (x) => Math.min(7200, Math.max(0, numberValue(x?.elapsed_seconds))) / 60;
    const inToday = (d) => d && sameLocalDay(d, now);
    const spent = qs.reduce((sum, q) => sum + (history[q.id]?.attempts || []).reduce((n, x) => n + (inToday(parsedTime(x.at)) ? elapsed(x) : 0), 0), 0);
    const remaining = Math.max(0, Math.floor(daily - spent));
    const started = parsedTime(prefs.session_started_at);
    const sessionSpent = qs.reduce((sum, q) => sum + (history[q.id]?.attempts || []).reduce((n, x) => {
      const at = parsedTime(x.at);
      return n + (inToday(at) && (!started || at >= started) ? elapsed(x) : 0);
    }, 0), 0);
    const sessionRemaining = Math.max(0, Math.floor(session - sessionSpent));
    let days = null;
    if (BASE.project.exam_date) {
      const exam = new Date(`${BASE.project.exam_date}T00:00:00`);
      if (!Number.isNaN(exam.getTime())) {
        const today = new Date(now); today.setHours(0, 0, 0, 0);
        days = Math.round((exam - today) / 86400000);
      }
    }
    const budget = Math.min(sessionRemaining, remaining);
    const rows = [], candidates = [], waiting = [];
    const minBy = (arr, fn) => arr.reduce((best, item) => fn(item) < fn(best) ? item : best);
    topics.forEach((topic) => {
      const pool = qs.filter((q) => q.topic_id === topic.id);
      const records = [];
      pool.forEach((q) => (history[q.id]?.attempts || []).forEach((x) => records.push([q, x])));
      records.sort((u, v) => (parsedTime(u[1].at)?.getTime() || 0) - (parsedTime(v[1].at)?.getTime() || 0));
      const successes = records.filter(([, x]) => evidenceAttempt(x));
      const distinct = new Set(successes.map(([q]) => q.id));
      const families = new Set(successes.map(([q]) => String(q.family_id || q.pattern_id || q.id)));
      let retained = false;
      const byQuestion = new Map();
      successes.forEach(([q, attempt]) => {
        if (!byQuestion.has(q.id)) byQuestion.set(q.id, []);
        byQuestion.get(q.id).push(attempt);
      });
      byQuestion.forEach((attempts) => {
        const times = attempts.map((x) => parsedTime(x.at)).filter(Boolean).sort((a, b) => a - b);
        if (times.length >= 2 && times[times.length - 1] - times[0] >= 1800000) retained = true;
      });
      let state = records.length ? "support" : "unseen";
      if (successes.length) state = retained ? "retained" : families.size >= 2 ? "transfer" : "independent";
      const [lastQ, last] = records.length ? records[records.length - 1] : [null, {}];
      if (records.length && !evidenceAttempt(last)) state = "support";
      const labels = { unseen: "待诊断", support: "需要辅助", independent: "独立完成过", transfer: "不同题族通过", retained: "间隔复测通过" };
      rows.push({ topic_id: topic.id, name: topic.name, state, label: labels[state], independent_questions: distinct.size, independent_families: families.size, question_count: pool.length });
      if (!pool.length) return;
      const unseen = pool.filter((q) => !(history[q.id]?.attempts || []).length);
      let phase = "diagnose";
      let reason = "尚无作答证据，先用一道题定位起点。";
      let q = minBy(unseen.length ? unseen : pool, questionMinutes);
      if (state === "support") {
        phase = "repair"; q = lastQ;
        reason = "最近作答仍需辅助；先核对条件和步骤，再尝试完成。";
        if (last.partial) {
          const missing = checkpoints(q).filter((_, i) => !(last.completed_steps || []).includes(i));
          if (missing.length) reason = "上次未完成的评分点：" + missing.slice(0, 2).join("；");
        }
        if (last.assisted && last.correct && unseen.length) {
          phase = "transfer"; q = minBy(unseen, questionMinutes);
          reason = "已经在辅助下完成，换一道未练题检查能否独立完成。";
        }
      } else if (["independent", "transfer", "retained"].includes(state)) {
        if (unseen.length) {
          phase = "transfer"; q = minBy(unseen, questionMinutes);
          reason = "已有独立完成记录，用另一道题检查能否迁移。";
        } else {
          phase = "retest";
          q = minBy(pool, (item) => {
            const attempts = history[item.id]?.attempts || [];
            return parsedTime(attempts[attempts.length - 1]?.at)?.getTime() || 0;
          });
          reason = "题库暂无未练题；这是旧题间隔复测，不能作为新题验证。";
        }
      }
      const lastTime = parsedTime(last.at);
      const failures = records.slice(-2).filter(([, x]) => !x.correct);
      const delay = phase === "retest" || failures.length === 2 ? 30 : 0;
      if (lastTime && delay && now < new Date(lastTime.getTime() + delay * 60000)) {
        waiting.push(new Date(lastTime.getTime() + delay * 60000).toISOString());
        return;
      }
      const duration = questionMinutes(q);
      const guide = topic.guide || {};
      const task = {
        topic_id: topic.id, question_id: q.id, phase,
        title: `${topic.name || ""} · ${{ diagnose: "起点诊断", repair: "补关键步骤", transfer: "换题检查", retest: "间隔复测" }[phase]}`,
        minutes: duration, reason,
        criterion: "在本块时间内完成作答并核对评分点；用了提示也如实记录。",
        guide: guide.two_minute || topic.summary || "",
        example: guide.worked_example || "",
        formula: topic.formula || "",
        error_type: last.error_type || "unknown",
      };
      const need = { diagnose: 1.2, repair: 1.35, transfer: 1.1, retest: 0.8 }[phase];
      const homeworkWeight = Math.max(0.5, Math.min(2, numberValue(topic.homework_weight, 1)));
      const score = (20 + Math.max(0, Math.min(100, numberValue(topic.priority)))) * need * homeworkWeight / Math.sqrt(duration);
      candidates.push([score, task]);
    });
    candidates.sort((a, b) => b[0] - a[0]);
    const plan = [];
    let allocated = 0;
    for (const [, task] of candidates) {
      if (allocated + task.minutes <= budget) { plan.push(task); allocated += task.minutes; }
      if (plan.length === 3) break;
    }
    let status = "ready";
    if (days !== null && days < 0) { status = "expired"; plan.length = 0; }
    else if (!qs.length) { status = "no_questions"; plan.length = 0; }
    else if (remaining <= 0) { status = "rest"; plan.length = 0; }
    else if (sessionRemaining <= 0) { status = "session_done"; plan.length = 0; }
    else if (!plan.length) status = (!candidates.length && waiting.length) ? "waiting" : "short_budget";
    return {
      status, tasks: plan, topics: rows, session_minutes: session, session_remaining: sessionRemaining,
      daily_minutes: daily, daily_remaining: remaining, tracked_minutes: Math.round(spent), days_left: days,
      next_review_at: waiting.length ? waiting.sort()[0] : null,
      evidence_rule_version: 2,
      independent_topics: rows.filter((r) => ["independent", "transfer", "retained"].includes(r.state)).length,
      note: "排序综合资料重点、作答证据和预计用时；不是提分预测。主观题按评分点自评。",
    };
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
    const learning = buildLearning();
    const daysLeft = learning.days_left;
    let nextAction = "先做 10 题诊断，完成起点诊断";
    if (attempts || ma.length) {
      nextAction = due ? `先复习 ${due} 张到期/未看卡片` : "继续 M1–M4 模板训练";
      if (best >= 60 && best < 95 && due === 0) nextAction = "冲 80：补二维连续和变量函数";
      if (best >= 95) nextAction = "冲 100：三套真题重做 + 零失误检查";
    }
    if (learning.tasks?.length) nextAction = learning.tasks[0].title;
    return {
      readiness, card_total: cards.length, card_seen: seen, card_mastery: seen ? Math.round(masterySum / seen) : 0,
      due_cards: due, questions_total: questions.length, attempts, accuracy: Math.round(correct / Math.max(1, attempts) * 100),
      mock_count: ma.length, last_mock: Math.round(last), best_mock: Math.round(best),
      plan_total: planTotal, plan_done: planDone, topics: topicRows, days_left: daysLeft, next_action: nextAction,
      learning,
    };
  }

  function state() {
    return {
      project: BASE.project,
      settings: { ...BASE.settings, has_key: false, key_hint: "" },
      progress,
      courses: [{ id: "static", name: BASE.project.course || "我的课程", status: BASE.project.status || "ready", docs: (BASE.project.docs || []).length, has_analysis: true, active: true }],
      active_course_id: "static",
      analysis_revision: CONTENT_REV,
      legacy_progress: !!progress.meta.legacy,
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
    if (path.endsWith("/api/project")) {
      let body = {};
      try { body = JSON.parse(init?.body || "{}"); } catch (_) {}
      const beforeProject = {
        course: BASE.project.course, exam_date: BASE.project.exam_date,
        days: BASE.project.days, hours_per_day: BASE.project.hours_per_day,
      };
      if (body.course !== undefined) BASE.project.course = String(body.course).slice(0, 80);
      if (body.exam_date !== undefined) BASE.project.exam_date = String(body.exam_date).slice(0, 10);
      if (body.days !== undefined) BASE.project.days = Math.max(1, Math.min(14, Number(body.days) || 3));
      if (body.hours_per_day !== undefined) BASE.project.hours_per_day = Math.max(0.5, Math.min(16, Number(body.hours_per_day) || 5));
      try {
        localStorage.setItem(PROJECT_KEY, JSON.stringify({
          course: BASE.project.course, exam_date: BASE.project.exam_date,
          days: BASE.project.days, hours_per_day: BASE.project.hours_per_day,
        }));
      } catch (_) {
        Object.assign(BASE.project, beforeProject);
        return storageError();
      }
      return json({ ok: true, project: BASE.project });
    }
    if (path.endsWith("/api/progress")) {
      let body = {};
      try { body = JSON.parse(init?.body || "{}"); } catch (_) {}
      const beforeProgress = clone(progress);
      const type = body.type;
      if (type === "preferences") {
        const session = Number(body.session_minutes);
        if (![5, 10, 15, 25, 45, 60].includes(session)) return json({ ok: false, error: "请选择5、10、15、25、45或60分钟" }, 400);
        progress.preferences = { ...(progress.preferences || {}), session_minutes: session, session_started_at: NOW() };
      } else if (type === "card") {
        const st = progress.cards[body.id] || (progress.cards[body.id] = { seen: 0, mastery: 0, correct: 0 });
        st.seen = (Number(st.seen) || 0) + 1;
        st.last = NOW();
        const rating = body.rating || "good";
        if (rating === "again") { st.mastery = Math.max(0, (Number(st.mastery) || 0) - 8); st.due = new Date(Date.now() + 600000).toISOString(); }
        else if (rating === "hard") { st.mastery = Math.min(100, (Number(st.mastery) || 0) + 4); st.due = new Date(Date.now() + 86400000).toISOString(); }
        else if (rating === "easy") { st.mastery = Math.min(100, (Number(st.mastery) || 0) + 20); st.correct = (Number(st.correct) || 0) + 1; st.due = new Date(Date.now() + 4 * 86400000).toISOString(); }
        else { st.mastery = Math.min(100, (Number(st.mastery) || 0) + 12); st.correct = (Number(st.correct) || 0) + 1; st.due = new Date(Date.now() + 2 * 86400000).toISOString(); }
      } else if (type === "question") {
        const qid = String(body.id || "");
        const q = (BASE.project.analysis?.questions || []).find((item) => item.id === qid);
        if (!qid) return json({ ok: false, error: "缺少题目 id" }, 400);
        if (!q) return json({ ok: false, error: "题目不存在，请刷新冲刺包" }, 404);
        if (body.completed_steps !== undefined && !Array.isArray(body.completed_steps)) {
          return json({ ok: false, error: "评分点记录格式错误" }, 400);
        }
        const steps = Array.isArray(body.completed_steps)
          ? [...new Set(body.completed_steps.filter((i) => Number.isInteger(i) && i >= 0 && i < checkpoints(q).length))].sort((a, b) => a - b)
          : [];
        const validPointIds = new Set((q.rubric_points || []).map((p) => p?.id).filter(Boolean).map(String));
        const pointIds = Array.isArray(body.completed_point_ids)
          ? body.completed_point_ids.map(String).filter((id) => validPointIds.has(id)).slice(0, 12)
          : [];
        if (body.assessment === "self" && body.correct && steps.length < checkpoints(q).length) {
          return json({ ok: false, error: "请逐项核对评分点；未全部完成可记录为部分完成" }, 400);
        }
        const st = progress.questions[qid] || (progress.questions[qid] = { attempts: [] });
        const attempt = {
          at: NOW(), correct: !!body.correct, answer: String(body.answer || "").slice(0, 2000),
          assisted: typeof body.assisted === "boolean" ? body.assisted : null,
          elapsed_seconds: Math.max(0, Math.min(7200, Number(body.elapsed_seconds) || 0)),
          partial: body.partial === true, completed_steps: steps,
          completed_point_ids: pointIds,
          error_type: body.error_type || "unknown",
          evidence_version: typeof body.assisted === "boolean" ? 1 : 0,
          answer_exposed: body.answer_exposed === true,
          assessment: body.assessment === "self" ? "self" : "objective",
        };
        st.attempts = (st.attempts || []).concat(attempt).slice(-30);
      } else if (type === "mock") {
        progress.mock.attempts = (progress.mock.attempts || []).concat({ at: NOW(), score: Number(body.score) || 0, percent: Number(body.score) || 0, duration_minutes: Number(body.duration_minutes) || 0, detail: body.detail || {} }).slice(-50);
      } else if (type === "plan") {
        progress.plan[body.block_id || body.id] = !!body.done;
      } else return json({ ok: false, error: "未知进度类型" }, 400);
      try {
        save();
      } catch (_) {
        progress = beforeProgress;
        return storageError();
      }
      return json({ ok: true, progress, insights: insights() });
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
    body.static-mode .dropzone,
    body.static-mode [data-export] { display:none !important; }
    body.static-mode .topbar-sub::after { content:" · 静态网页（仅当前课程）"; color:var(--accent); }
    body.static-mode .course-line { pointer-events:none; cursor:default; }
    body.static-mode .course-caret { display:none; }
  `;
  document.head.appendChild(style);
  document.body.classList.add("static-mode");

  // PWA: installable on Android/Chrome and iPhone/iPad Safari.
  if ((location.protocol === "http:" || location.protocol === "https:") && "serviceWorker" in navigator) {
    navigator.serviceWorker.register("./service-worker.js").catch(() => {});
  }
  const standalone = window.matchMedia?.("(display-mode: standalone)")?.matches || window.navigator.standalone;
  if (!standalone && (location.protocol === "http:" || location.protocol === "https:")) {
    const installBtn = document.createElement("button");
    installBtn.type = "button";
    installBtn.className = "pwa-install";
    installBtn.textContent = "安装到桌面";
    let installEvent = null;
    window.addEventListener("beforeinstallprompt", (event) => {
      event.preventDefault();
      installEvent = event;
    });
    installBtn.addEventListener("click", async () => {
      if (installEvent) {
        installEvent.prompt();
        const choice = await installEvent.userChoice;
        installEvent = null;
        if (choice.outcome === "accepted") installBtn.remove();
        return;
      }
      alert("iPhone/iPad：点 Safari 底部分享按钮 → “添加到主屏幕”。\nAndroid：点浏览器菜单 → “安装应用 / 添加到主屏幕”。");
    });
    window.addEventListener("appinstalled", () => installBtn.remove());
    document.body.appendChild(installBtn);
  }
})();
