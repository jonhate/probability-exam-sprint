/* ExamSprint front-end: local-first, no build step. */
(() => {
  "use strict";

  const ICONS = {
    home: '<path d="M3 10.5 12 3l9 7.5"/><path d="M5 9.5V21h14V9.5"/><path d="M9 21v-6h6v6"/>',
    map: '<path d="m3 6 6-3 6 3 6-3v15l-6 3-6-3-6 3z"/><path d="M9 3v15M15 6v15"/>',
    book: '<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>',
    pencil: '<path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4z"/>',
    clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    flag: '<path d="M5 22V3"/><path d="M5 4h11l-1.5 4L16 12H5"/>',
    folder: '<path d="M3 7a2 2 0 0 1 2-2h5l2 2h7a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>',
    settings: '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .34 1.88l.06.06-2.83 2.83-.06-.06A1.7 1.7 0 0 0 15 19.4a1.7 1.7 0 0 0-1 .6 1.7 1.7 0 0 0-.4 1.1V21h-4v-.09A1.7 1.7 0 0 0 8.6 19.4a1.7 1.7 0 0 0-1.88.34l-.06.06-2.83-2.83.06-.06A1.7 1.7 0 0 0 4.6 15a1.7 1.7 0 0 0-.6-1 1.7 1.7 0 0 0-1.1-.4H3v-4h.09A1.7 1.7 0 0 0 4.6 8.6a1.7 1.7 0 0 0-.34-1.88l-.06-.06 2.83-2.83.06.06A1.7 1.7 0 0 0 9 4.6a1.7 1.7 0 0 0 1-.6 1.7 1.7 0 0 0 .4-1.1V3h4v.09A1.7 1.7 0 0 0 15.4 4.6a1.7 1.7 0 0 0 1.88-.34l.06-.06 2.83 2.83-.06.06A1.7 1.7 0 0 0 19.4 9c.13.37.35.7.64.96.3.26.68.4 1.07.4H21v4h-.09A1.7 1.7 0 0 0 19.4 15z"/>',
    spark: '<path d="m12 3 1.7 5.3L19 10l-5.3 1.7L12 17l-1.7-5.3L5 10l5.3-1.7z"/><path d="m19 17 .8 2.2L22 20l-2.2.8L19 23l-.8-2.2L16 20l2.2-.8z"/>',
    download: '<path d="M12 3v12"/><path d="m7 10 5 5 5-5"/><path d="M5 21h14"/>',
    menu: '<path d="M4 6h16M4 12h16M4 18h16"/>',
    x: '<path d="m5 5 14 14M19 5 5 19"/>',
    upload: '<path d="M12 21V9"/><path d="m7 14 5-5 5 5"/><path d="M4 4h16"/>',
    check: '<path d="m4 12 5 5L20 6"/>',
    chevron: '<path d="m6 9 6 6 6-6"/>',
    arrow: '<path d="M5 12h14"/><path d="m14 7 5 5-5 5"/>',
    play: '<path d="m8 5 11 7-11 7z"/>',
    refresh: '<path d="M20 7v5h-5"/><path d="M4 17v-5h5"/><path d="M6.1 8a7 7 0 0 1 11.5-1L20 10M4 14l2.4 3a7 7 0 0 0 11.5-1"/>',
    trash: '<path d="M3 6h18"/><path d="M8 6V3h8v3M19 6l-1 15H6L5 6"/><path d="M10 11v6M14 11v6"/>',
    file: '<path d="M6 2h8l4 4v16H6z"/><path d="M14 2v5h5"/><path d="M9 13h6M9 17h6"/>',
    target: '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1"/>',
    layers: '<path d="m12 2 9 5-9 5-9-5z"/><path d="m3 12 9 5 9-5"/><path d="m3 17 9 5 9-5"/>',
    brain: '<path d="M9.5 4A3 3 0 0 0 6 7v.4A3.5 3.5 0 0 0 5 14a3.5 3.5 0 0 0 4.5 3.3V4z"/><path d="M14.5 4A3 3 0 0 1 18 7v.4a3.5 3.5 0 0 1 1 6.6 3.5 3.5 0 0 1-4.5 3.3V4z"/>',
    timer: '<circle cx="12" cy="13" r="8"/><path d="M12 9v4l2 2M9 2h6"/>',
    alert: '<path d="M10.3 3.8 2.2 18a2 2 0 0 0 1.8 3h16a2 2 0 0 0 1.8-3L13.7 3.8a2 2 0 0 0-3.4 0z"/><path d="M12 9v4M12 17h.01"/>',
    search: '<circle cx="11" cy="11" r="7"/><path d="m20 20-4-4"/>',
    send: '<path d="m22 2-7 20-4-9-9-4z"/><path d="M22 2 11 13"/>',
    key: '<circle cx="8" cy="15" r="4"/><path d="m11 12 8-8M16 4l4 4M14 6l3 3"/>',
    shield: '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="m9 12 2 2 4-4"/>',
    plus: '<path d="M12 5v14M5 12h14"/>',
    lightbulb: '<path d="M9 18h6M10 22h4"/><path d="M8.5 14.5A6 6 0 1 1 15.5 14.5C14.5 15.4 14 16.5 14 18h-4c0-1.5-.5-2.6-1.5-3.5z"/>',
    filetext: '<path d="M6 2h8l4 4v16H6z"/><path d="M14 2v5h5M9 12h6M9 16h6"/>',
    arrowleft: '<path d="M19 12H5"/><path d="m10 17-5-5 5-5"/>',
    external: '<path d="M15 3h6v6M10 14 21 3"/><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>',
    circle: '<circle cx="12" cy="12" r="9"/>'
  };

  const TYPE_LABEL = {
    single: "单选", multiple: "多选", judge: "判断", short: "简答",
    calculation: "计算", essay: "论述", mixed: "综合"
  };
  const KIND_LABEL = { slides: "课件", homework: "作业", exam: "真题", other: "其他" };
  const KIND_ORDER = ["slides", "homework", "exam", "other"];

  const S = {
    data: null,
    view: "dashboard",
    studyTab: "flashcards",
    selectedTopic: null,
    cardOrder: [],
    cardIndex: 0,
    cardRevealed: false,
    cardDueOnly: false,
    mapSort: "priority",
    openTopics: new Set(),
    practiceTopic: "all",
    practice: null,
    mock: null,
    modal: null,
    askHistory: [],
    uploadBusy: false,
    jobTimer: null,
    mockTimer: null,
    initialViewDone: false
  };

  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));
  const esc = (v) => String(v ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const clamp = (n, lo, hi) => Math.max(lo, Math.min(hi, n));
  const pct = (n) => clamp(Math.round(Number(n) || 0), 0, 100);

  function rich(text) {
    let s = esc(text || "");
    s = s.replace(/\*\*(.+?)\*\*/g, "<b>$1</b>");
    s = s.replace(/`([^`]+)`/g, '<span class="code">$1</span>');
    s = s.replace(/\n/g, "<br>");
    return s;
  }

  function icon(name) { return `<span data-icon="${name}"></span>`; }

  function hydrateIcons(root = document) {
    $$("[data-icon]", root).forEach((el) => {
      const name = el.getAttribute("data-icon");
      if (name && ICONS[name]) el.innerHTML = `<svg viewBox="0 0 24 24" aria-hidden="true">${ICONS[name]}</svg>`;
    });
  }

  function toast(message, type = "") {
    const stack = $("#toastStack");
    const el = document.createElement("div");
    el.className = `toast ${type}`;
    el.textContent = message;
    stack.appendChild(el);
    setTimeout(() => { el.style.opacity = "0"; el.style.transform = "translateY(4px)"; }, 3400);
    setTimeout(() => el.remove(), 3900);
  }

  async function api(path, opts = {}) {
    const init = { method: opts.method || "GET", headers: { ...(opts.headers || {}) } };
    if (opts.body !== undefined) {
      init.headers["Content-Type"] = "application/json";
      init.body = JSON.stringify(opts.body);
    }
    const res = await fetch(path, init);
    let data = {};
    try { data = await res.json(); } catch (_) {}
    if (!res.ok || data.ok === false) throw new Error(data.error || `请求失败（${res.status}）`);
    return data;
  }

  function loadingView() {
    return `<div class="empty-state"><div class="spinner" style="width:28px;height:28px;border-width:3px"></div><h3 style="margin-top:16px">正在载入冲刺舱…</h3><p>读取本地资料与学习进度</p></div>`;
  }

  async function load() {
    try {
      S.data = await api("/api/state");
      if (!S.initialViewDone) {
        const fresh = !(S.data.insights?.card_seen || 0) && !(S.data.insights?.attempts || 0);
        if (S.data.project.analysis?.zero_base?.enabled && fresh) S.view = "zero";
        S.initialViewDone = true;
      }
      if (!S.data.project.analysis && !["dashboard", "docs", "practice", "mock", "errors", "study", "map", "zero"].includes(S.view)) S.view = "dashboard";
      render();
      if (S.data.project.job && S.data.project.job.status === "running") startJobPolling();
    } catch (err) {
      $("#viewRoot").innerHTML = `<div class="empty-state"><div class="empty-icon">${icon("alert")}</div><h3>连不上本地服务</h3><p>${esc(err.message)}<br>请确认启动窗口没有关闭，然后刷新页面。</p><button class="btn" onclick="location.reload()">刷新</button></div>`;
      hydrateIcons();
    }
  }

  function analysis() { return S.data?.project?.analysis || null; }
  function progress() { return S.data?.progress || {}; }
  function insights() { return S.data?.insights || {}; }

  function currentExamDays() {
    const p = S.data?.project;
    if (!p?.exam_date) return null;
    const today = new Date(); today.setHours(0, 0, 0, 0);
    const exam = new Date(`${p.exam_date}T00:00:00`);
    return Math.round((exam - today) / 86400000);
  }

  function renderChrome() {
    const p = S.data?.project || {};
    const a = analysis();
    $("#courseLine").innerHTML = `${esc(a?.course || p.course || "我的课程")} <span class="course-caret">⌄</span>`;
    const modeLabel = a?.zero_base?.enabled ? "零基础模式" : a?.generation?.mode === "llm" ? "AI 已生成" : a?.generation?.mode === "curated" ? "真题精编" : "离线框架";
    $("#topbarSub").textContent = a
      ? `${a.topics?.length || 0} 个考点 · 准备度 ${insights().readiness || 0}% · ${modeLabel}`
      : (p.docs?.length ? `${p.docs.length} 份资料待生成` : "把课件变成考前作战图");
    const d = currentExamDays();
    $("#countdownDays").textContent = d === null ? "—" : (d < 0 ? "—" : d);
    $("#countdownNote").textContent = d === null ? "先上传资料" : d < 0 ? "考试已结束" : d === 0 ? "今天考试，稳住" : `每天 ${p.hours_per_day || 5} 小时冲刺`;
    $$(".nav-item").forEach((el) => el.classList.toggle("active", el.dataset.nav === S.view));
    const banner = $("#globalBanner");
    banner.innerHTML = "";
    const job = p.job || {};
    if (job.status === "running") {
      banner.innerHTML = `<div class="gen-progress" id="genProgress">
        <div class="gen-progress-head"><span><span class="spinner"></span> ${esc(job.message || "正在生成…")}</span><b>${Math.round(job.progress || 0)}%</b></div>
        <div class="bar"><span style="width:${clamp(job.progress || 0, 0, 100)}%"></span></div>
      </div>`;
    } else if (a && p.stale) {
      banner.innerHTML = `<div class="warn-box"><b>资料已变化。</b> 当前冲刺包还是旧版本，请到「资料箱」重新生成，否则考点可能缺页。</div>`;
    } else if (job.status === "error") {
      banner.innerHTML = `<div class="error-box"><b>上次生成失败：</b>${esc(job.error || job.message || "未知错误")} <button class="text-btn" data-action="open-settings">检查模型设置</button> 或到资料箱重新生成。</div>`;
    } else if (a?.zero_base?.enabled && S.view !== "zero") {
      banner.innerHTML = `<div class="info-box" style="display:flex;align-items:center;gap:10px;flex-wrap:wrap"><b>零基础模式已开启。</b> 不要从 S 级全部开始，先走 6 个工具 + M1–M4。 <button class="text-btn" data-nav="zero">回到零基础路线</button></div>`;
    }
    hydrateIcons(banner);
  }

  function render() {
    if (!S.data) return;
    stopMockTimer();
    renderChrome();
    const root = $("#viewRoot");
    if (!analysis() && !["docs"].includes(S.view)) {
      root.innerHTML = renderOnboarding();
    } else if (S.view === "dashboard") {
      root.innerHTML = analysis() ? renderDashboard() : renderOnboarding();
    } else if (S.view === "zero") {
      root.innerHTML = renderZeroBase();
    } else if (S.view === "map") {
      root.innerHTML = renderMap();
    } else if (S.view === "study") {
      root.innerHTML = renderStudy();
    } else if (S.view === "practice") {
      root.innerHTML = renderPractice();
    } else if (S.view === "mock") {
      root.innerHTML = renderMock();
    } else if (S.view === "errors") {
      root.innerHTML = renderErrors();
    } else if (S.view === "docs") {
      root.innerHTML = renderDocs();
    } else {
      root.innerHTML = renderOnboarding();
    }
    hydrateIcons(root);
    wireUploads(root);
    renderModal();
    renderAskMessages();
    if (S.view === "mock" && S.mock?.status === "active") startMockTimer();
  }

  // ------------------------------------------------------------------
  // Onboarding & dashboard
  // ------------------------------------------------------------------
  function setupFormHTML() {
    const p = S.data.project;
    const hasKey = S.data.settings.has_key;
    return `<div class="form-grid">
      <div class="field full"><label for="setupCourse">课程名称</label><input id="setupCourse" value="${esc(p.course === "我的课程" ? "" : p.course)}" placeholder="例如：宏观经济学"></div>
      <div class="field"><label for="setupDate">考试日期</label><input id="setupDate" type="date" value="${esc(p.exam_date || "")}"></div>
      <div class="field"><label for="setupDays">冲刺天数</label><input id="setupDays" type="number" min="1" max="14" value="${esc(p.days || 3)}"></div>
      <div class="field"><label for="setupHours">每天小时</label><input id="setupHours" type="number" min="0.5" max="16" step="0.5" value="${esc(p.hours_per_day || 5)}"></div>
      <div class="field full"><label>资料箱</label>
        <div class="dropzone" tabindex="0">
          <input type="file" class="hidden" multiple accept=".pptx,.pdf,.docx,.xlsx,.txt,.md,.csv">
          <div class="dropzone-icon">${icon("upload")}</div>
          <b>拖入 PPT / 作业 / 真题</b>
          <small>支持 PPTX、PDF、DOCX、XLSX、TXT；也可点此选择</small>
        </div>
        <div class="upload-list">${docMiniList(p.docs || [])}</div>
      </div>
    </div>
    <div class="ai-status ${hasKey ? "ready" : ""}">
      <span class="dot"></span>
      <span>${hasKey ? `模型已配置：${esc(S.data.settings.model)}` : "未配置模型：先生成离线框架，配置后可生成高质量讲解与仿真卷"}</span>
      <button class="text-btn" style="margin-left:auto" data-action="open-settings">${hasKey ? "修改" : "配置"}</button>
    </div>
    <div class="onboard-foot">
      <button class="btn btn-accent btn-lg" data-action="generate" ${p.docs?.length ? "" : "disabled"}>${p.job?.status === "running" ? "正在生成…" : "生成我的冲刺包"} ${icon("arrow")}</button>
      <div class="mini-note">${p.docs?.length ? `已加入 ${p.docs.length} 份资料 · ${totalPages()} 页/张` : "先放资料，10 分钟内拿到作战图"}</div>
    </div>`;
  }

  function totalPages() {
    return (S.data.project.docs || []).reduce((n, d) => n + (Number(d.page_count) || 0), 0);
  }

  function docMiniList(docs) {
    if (!docs.length) return `<div class="tiny muted" style="padding:4px 2px">还没有资料。PPT、作业、真题都可以一起放。</div>`;
    return docs.map((d) => `<div class="upload-item">
      <span class="badge ${d.kind === "exam" ? "badge-accent" : d.kind === "homework" ? "badge-gold" : "badge-blue"}">${KIND_LABEL[d.kind] || "资料"}</span>
      <span class="fname">${esc(d.name)}</span>
      <span class="meta">${d.page_count || 0} 页</span>
      <button class="rm" data-delete-doc="${esc(d.doc_id)}" title="移除">${icon("x")}</button>
    </div>`).join("");
  }

  function renderOnboarding() {
    const p = S.data.project;
    return `<div class="onboard-hero">
      <div>
        <div class="kicker"><span class="dot"></span> EVIDENCE-FIRST EXAM PREP</div>
        <h1 class="onboard-title">把课件，变成<br>考前 <em>72 小时</em><br>的作战图。</h1>
        <p class="onboard-lede">不是让 AI 把书再讲一遍。它会从你的 PPT、作业和真题里反推：老师会怎么考、哪些考点最值钱、你先学什么、哪些可以放弃。</p>
        <div class="onboard-points">
          <div class="onboard-point">${icon("target")}<div><b>真题反推</b><span>从题型、分值、重复考点倒推复习优先级，不做平均用力。</span></div></div>
          <div class="onboard-point">${icon("brain")}<div><b>主动回忆</b><span>每张卡只考一个点，先想再看答案，比反复看 PPT 有效。</span></div></div>
          <div class="onboard-point">${icon("clock")}<div><b>限时模拟</b><span>按真题卷型组一套仿真卷，暴露“会但做不对”的问题。</span></div></div>
          <div class="onboard-point">${icon("flag")}<div><b>错题闭环</b><span>错题回到对应考点，再测一次；只记录错因，不抄题。</span></div></div>
        </div>
        <div class="method-strip"><span> retrieval practice </span><span> spaced review </span><span> interleaving </span><span> worked examples </span><span> error log </span></div>
      </div>
      <div class="card onboard-card">
        <div class="onboard-card-head">
          <div class="eyebrow">SETUP / 01</div>
          <h2>先告诉我考什么</h2>
          <p class="muted small" style="margin:0">资料只在本机解析；调用模型时只发必要片段。</p>
        </div>
        <div class="onboard-card-body">${setupFormHTML()}</div>
      </div>
    </div>`;
  }

  function metricHTML(iconName, tone, value, label) {
    return `<div class="metric"><div class="metric-icon ${tone}">${icon(iconName)}</div><div><b>${value}</b><span>${label}</span></div></div>`;
  }

  function ringHTML(value) {
    const v = pct(value);
    const c = 2 * Math.PI * 50;
    return `<div class="ring"><svg viewBox="0 0 118 118"><circle class="ring-bg" cx="59" cy="59" r="50" fill="none" stroke-width="8"/><circle class="ring-fill" cx="59" cy="59" r="50" fill="none" stroke-dasharray="${c.toFixed(1)}" stroke-dashoffset="${(c * (1 - v / 100)).toFixed(1)}"/></svg><div class="ring-label"><b>${v}</b><span>准备度</span></div></div>`;
  }

  function renderDashboard() {
    const a = analysis();
    const ins = insights();
    const p = S.data.project;
    const days = currentExamDays();
    const today = a.plan?.[0];
    const plan = progress().plan || {};
    const topicMastery = Object.fromEntries((ins.topics || []).map((t) => [t.id, t.mastery]));
    const doneToday = (today?.blocks || []).filter((b) => plan[b.id]).length;
    let currentMarked = false;
    const warnings = a.generation?.warnings || [];
    return `
      <div class="dash-hero">
        <div>
          <div class="kicker"><span class="dot"></span> ${a.zero_base?.enabled ? "ZERO BASE · 60 → 80 → 100" : days === null ? "SPRINT MODE" : days <= 0 ? "EXAM DAY" : `T-${days} · SPRINT MODE`}</div>
          <h1>${a.zero_base?.enabled ? "零基础也能抢分：<br>先补工具，再背模板。" : `${esc(a.course)}：今天只学<br>最值钱的部分。`}</h1>
          <p>${a.zero_base?.enabled ? "不要从第一页 PPT 开始。先走 6 个数学工具 → 4 个保分模板；目标不是学完，是把能写的步骤写出来。" : esc(a.course_summary)}</p>
          <div class="hero-actions">
            ${a.zero_base?.enabled
              ? `<button class="btn btn-accent" data-nav="zero">${icon("play")} 零基础保命路线</button>`
              : `<button class="btn btn-accent" data-action="start-today">${icon("play")} 开始今日冲刺</button>`}
            <button class="btn" data-nav="map">${icon("map")} 看考点地图</button>
          </div>
        </div>
        <div class="hero-side">
          ${ringHTML(ins.readiness)}
          <div class="hero-mini-stats">
            <div class="hero-mini-stat"><b>${a.topics?.length || 0}</b><span>高产出考点</span></div>
            <div class="hero-mini-stat"><b>${ins.due_cards || 0}</b><span>待复习卡</span></div>
            <div class="hero-mini-stat"><b>${ins.last_mock || 0}</b><span>最近模考</span></div>
          </div>
        </div>
      </div>
      <div class="metric-grid">
        ${metricHTML("target", "accent", `${ins.readiness || 0}%`, "准备度（过程指标）")}
        ${metricHTML("brain", "green", `${ins.card_seen || 0}/${ins.card_total || 0}`, "回忆卡已过")}
        ${metricHTML("pencil", "gold", `${ins.attempts || 0} 题`, `练习正确率 ${ins.accuracy || 0}%`)}
        ${metricHTML("clock", "blue", `${ins.best_mock || 0}`, "模考最好成绩")}
      </div>
      ${renderTiers(a)}
      ${warnings.length ? `<div class="warn-box"><b>生成提示：</b><ul>${warnings.slice(0, 5).map((w) => `<li>${esc(w)}</li>`).join("")}</ul></div>` : ""}
      <div class="dash-grid">
        <div class="card plan-card">
          <div class="card-head"><div><h3>今天怎么打</h3><p>${today ? `${today.label} · ${today.theme} · 已做 ${doneToday}/${today.blocks.length} 块` : "暂无计划"}</p></div><span class="badge badge-gold">${p.hours_per_day || 5} 小时</span></div>
          <div class="card-body"><div class="timeline">
            ${(today?.blocks || []).map((b) => {
              const done = !!plan[b.id];
              const current = !done && !currentMarked;
              if (current) currentMarked = true;
              const related = (b.topic_ids || []).map((id) => a.topics.find((t) => t.id === id)?.name).filter(Boolean);
              return `<div class="tl-item ${done ? "done" : ""} ${current ? "current" : ""}">
                <div class="tl-time">${esc(b.time)}</div><div class="tl-rail"><span class="tl-dot"></span></div>
                <div class="tl-body"><div class="tl-title">${esc(b.activity)} <span class="mins">${b.minutes} min</span><button class="tl-check" data-plan-id="${esc(b.id)}" title="${done ? "标记未完成" : "标记完成"}">${done ? icon("check") : icon("circle")}</button></div>
                <div class="tl-meta">${related.length ? related.slice(0, 3).join(" · ") + " → " : ""}${esc(b.output)}</div></div></div>`;
            }).join("") || `<div class="empty-mini">还没有计划</div>`}
          </div></div>
        </div>
        <div>
          <div class="card next-card"><div class="card-body">
            <div class="eyebrow" style="color:#d7a55f">NEXT BEST ACTION</div>
            <h3>${esc(ins.next_action)}</h3>
            <p>不要从第一页开始看。先用题暴露漏洞，再回到考点补洞。准备度是过程指标，不是考试通过率。</p>
            <div class="next-action"><b>现在做：</b>${(ins.due_cards || 0) > 0 ? `打开回忆卡，先过 ${Math.min(ins.due_cards, 12)} 张到期卡。` : "做 10 道混合题，把不确定的题标出来。"}</div>
            <div class="next-buttons"><button class="btn btn-accent btn-sm" data-nav="study">${icon("brain")} 开始回忆</button><button class="btn btn-sm" data-action="quick-practice">${icon("pencil")} 10 题快刷</button></div>
          </div></div>
          <div class="card" style="margin-top:12px"><div class="card-head"><div><h3>最该先啃的考点</h3><p>按考试收益排序，不是章节顺序</p></div><button class="text-btn" data-nav="map">全部</button></div><div class="card-body topic-mini-list">
            ${(a.topics || []).slice(0, 5).map((t, i) => `<div class="topic-mini"><span class="topic-rank">${String(i + 1).padStart(2, "0")}</span><div class="topic-mini-main"><div class="topic-mini-name">${esc(t.name)}</div><div class="bar"><span style="width:${pct(topicMastery[t.id] || 0)}%"></span></div></div><span class="topic-mini-mastery">${pct(topicMastery[t.id] || 0)}%</span></div>`).join("") || `<div class="empty-mini">暂无考点</div>`}
          </div></div>
        </div>
      </div>
      <div class="section-head"><div><h2>你的考试蓝图</h2><p>从作业和真题反推；不是押题，考前请再核对老师范围</p></div><span class="badge ${a.exam_profile?.confidence === "高" ? "badge-green" : "badge-gold"}">置信度：${esc(a.exam_profile?.confidence || "低")}</span></div>
      <div class="card card-pad">
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:22px" class="blueprint-grid">
          <div><div class="guide-label">试卷结构</div><p class="guide-text">${esc(a.exam_profile?.paper_format || "资料不足，按常规期中考试推断。")}</p><div class="stat-strip" style="margin:10px 0 0"><div><b>${a.exam_profile?.duration_minutes || 120}</b><span>分钟</span></div><div><b>${a.exam_profile?.total_score || 100}</b><span>总分</span></div><div><b>${(a.mock?.sections || []).reduce((n, s) => n + (s.questions?.length || 0), 0)}</b><span>仿真题</span></div></div></div>
          <div><div class="guide-label">冲刺策略</div><p class="guide-text">${esc(a.exam_strategy)}</p><div style="margin-top:10px"><button class="btn btn-sm" data-nav="mock">${icon("clock")} 看仿真卷</button></div></div>
        </div>
      </div>`;
  }

  function tierOf(t) {
    if ((t.priority || 0) >= 94) return "s";
    if ((t.priority || 0) >= 84) return "a";
    return "b";
  }

  function renderTiers(a) {
    const topics = a.topics || [];
    const groups = [
      { key: "s", label: "S · 必拿", title: "6 个计算模板", note: "约 70 分；先练到闭眼能写步骤。", items: topics.filter((t) => tierOf(t) === "s") },
      { key: "a", label: "A · 补漏", title: "选择/填空高频", note: "约 25–30 分；只背概念、公式和陷阱。", items: topics.filter((t) => tierOf(t) === "a") },
      { key: "b", label: "B · 最后学", title: "低频 / 可战略放弃", note: "5–10 分；只学模板，复杂题直接跳过。", items: topics.filter((t) => tierOf(t) === "b") },
    ];
    return `<div class="section-head" style="margin-top:26px"><div><h2>按分数性价比分层</h2><p>“考试不是全考”：先保 S，再补 A；B 只在还有时间时学模板。${a.zero_base?.enabled ? " 零基础模式请只先学 M1–M4，不要一次全开。" : ""} 优先级 = 真题频率 35% + 作业 25% + 课件强调 25% + 基础带动 15%。</p></div><span class="badge badge-muted">估算分值 · 非押题</span></div>
      <div class="tier-grid">${groups.map((g) => `<div class="tier-card ${g.key}"><div class="tier-top"><span class="tier-label">${g.label}</span><b>${g.title}</b></div><p>${g.note}</p><div class="tier-chips">${g.items.map((t) => `<button class="tier-chip" data-topic-study="${esc(t.id)}">${esc(t.name)}</button>`).join("")}</div></div>`).join("")}</div>`;
  }

  // ------------------------------------------------------------------
  // Zero-foundation rescue route
  // ------------------------------------------------------------------
  function renderZeroBase() {
    const z = analysis()?.zero_base;
    if (!z) return `<div class="empty-state"><h3>零基础模式未加载</h3><p>请在资料箱重新生成。</p></div>`;
    const modules = z.modules || [];
    const route = [
      { n: "00", title: "数学急救", sub: "Σ / 积分 / 分段", cls: "core" },
      ...modules.map((m, i) => ({ n: String(i + 1).padStart(2, "0"), title: (m.title || "").split("：")[0], sub: `${m.score} · ${m.time}`, cls: (m.tag || "").includes("80 档") ? "optional" : "core" })),
    ];
    const best = Number(insights().best_mock || 0);
    const stage = best >= 95 ? "100" : best >= 60 ? "80" : "60";
    return `<div class="page-head"><div><div class="eyebrow">ZERO BASE / 00</div><h1>${esc(z.title || "零基础三级冲刺：60 → 80 → 100")}</h1><p>先用模板保 60，再用二维/变量函数冲 80，最后用“零失误”挑战 100。每一级有门槛，达不到不硬升。</p></div><span class="badge badge-accent">${esc(z.target)}</span></div>
    <div class="zero-hero">
      <div class="zero-main">
        <div class="kicker"><span class="dot"></span> 先接受现实，再开始抢分</div>
        <h1>先保 60，再拔 80，<br>最后才谈 100。</h1>
        <p>${esc(z.hard_truth)}</p>
        <div class="zero-kpis"><div class="zero-kpi"><b>6</b><span>个数学工具</span></div><div class="zero-kpi"><b>3</b><span>级分数门槛</span></div><div class="zero-kpi"><b>18h</b><span>3 天总投入</span></div><div class="zero-kpi"><b>60→100</b><span>晋级路线</span></div></div>
        <div class="hero-actions"><button class="btn btn-accent" data-action="start-zero">${icon("play")} 从数学急救开始</button><button class="btn" data-action="scroll-zero-diag">${icon("target")} 先做 10 题诊断</button></div>
      </div>
      <div class="truth-card"><div><div class="eyebrow" style="color:#d7a55f">HARD TRUTH</div><h2>100 分不是“再背几个技巧”</h2><p>60 分靠模板，80 分靠题型覆盖，100 分靠完整知识面 + 零失误。技巧能压缩时间，但不能替代理解与准确率。</p></div><div class="truth-quote">${(z.rules || []).slice(0, 3).map((r) => esc(r)).join("<br>")}</div></div>
    </div>
    <div class="zero-rules">${(z.rules || []).map((r, i) => `<div class="zero-rule"><b>RULE ${String(i + 1).padStart(2, "0")}</b>${esc(r)}</div>`).join("")}</div>
    <div class="section-head"><div><h2>你现在在哪一级</h2><p>当前目标按最近模考分判断；没有模考就先按 60 档走，不跳级。</p></div><span class="badge ${stage === "60" ? "badge-accent" : stage === "80" ? "badge-gold" : "badge-green"}">当前目标：${stage} 档</span></div>
    <div class="ladder-grid">${(z.ladder || []).map((lv) => {
      const cls = lv.level === stage ? "current" : (Number(lv.level) < Number(stage) ? "passed" : "future");
      const action = lv.level === "60" ? `<button class="btn btn-sm btn-accent" data-action="scroll-zero-diag">先做 10 题诊断</button>` : lv.level === "80" ? `<button class="btn btn-sm" data-topic-study="t04">学二维连续</button>` : `<button class="btn btn-sm" data-nav="mock">做限时模拟</button>`;
      return `<div class="ladder-card ${cls}"><div class="ladder-top"><span class="ladder-level">${esc(lv.level)}</span><div><b>${esc(lv.label)}</b><span>${esc(lv.score)} · ${esc(lv.time)}</span></div></div><p>${esc(lv.focus)}</p><div class="ladder-gate"><b>过关条件</b>${(lv.gate || []).map((g) => `<span>${esc(g)}</span>`).join("")}</div><div class="ladder-foot">${action}<em>${esc(lv.next)}</em></div></div>`;
    }).join("")}</div>
    <div class="warn-box"><b>关于 100 分的实话：</b>零基础 3 天冲 100 是低概率事件。真要冲，至少满足：三套真题全部重做无知识性错误、连续两次仿真卷 ≥95、错题本能解释每个陷阱。达不到就停在 80，先把能拿的分拿稳。</div>
    <div class="section-head"><div><h2>先走这条线，不要跳</h2><p>每一步都以前一步为前置；看不懂就回到上一张工具卡。</p></div><span class="badge badge-muted">${modules.length} 个模板</span></div>
    <div class="zero-route">${route.map((r) => `<div class="route-step ${r.cls}"><span class="rn">${r.n}</span><b>${esc(r.title)}</b><span>${esc(r.sub)}</span></div>`).join("")}</div>
    <div class="section-head" id="zeroTools"><div><h2>数学急救：6 个工具就够</h2><p>不学极限、不学证明。只要会加、会积、会看分段、会画区域。</p></div><span class="badge badge-gold">约 2.5 小时</span></div>
    <div class="zero-tools">${(z.tools || []).map((t, i) => `<details class="tool-card" id="tool-${esc(t.id)}"><summary><span class="tool-num">${String(i + 1).padStart(2, "0")}</span><b>${esc(t.title)}</b><span class="min">${t.minutes} min</span></summary><div class="tool-body"><p>${esc(t.plain)}</p><div class="tool-example"><b>最小例子：</b>${esc(t.example)}</div><p><b>检查：</b>${esc(t.check)}</p><div class="tool-wrong"><b>常见错：</b>${esc(t.wrong)}</div></div></details>`).join("")}</div>
    <div class="section-head" id="zeroModules"><div><h2>保分模板：照着写</h2><p>每个模板都给了“考试就写这几行”。先抄 3 遍，再合上书默写。</p></div><span class="badge badge-accent">60 档先学 4 个；80 档再加 2 个</span></div>
    <div class="zero-modules">${modules.map((m, i) => renderZeroModule(m, i)).join("")}</div>
    <div class="section-head" id="zeroDiag"><div><h2>零基础诊断：只测工具，不测智商</h2><p>不会就点“补工具”，不用内疚。10 题里会 6 题就可以开始 M1。</p></div><span class="badge badge-green">约 15 分钟</span></div>
    <div class="diag-grid">${(z.diagnostic || []).map((d, i) => `<div class="diag-card"><div class="dq"><b>${i + 1}.</b> ${esc(d.q)}</div><details><summary>看答案 / 补工具</summary><div class="da">${esc(d.a)} <button class="text-btn" data-zero-tool-open="${esc(d.tool)}">打开工具卡</button></div></details></div>`).join("")}</div>
    <div class="zero-footer-cta"><h3>今天只做一件事：把 M1 的 5 步抄 3 遍</h3><p>不要打开 PPT 第一页。M1 是 10 分，且完全不需要高数。</p><div style="display:flex;gap:8px;justify-content:center;flex-wrap:wrap"><button class="btn btn-accent" data-topic-study="t01">${icon("book")} 打开 Bayes 速学卡</button><button class="btn" data-topic-practice="t01">${icon("pencil")} 做 Bayes 基础题</button></div></div>`;
  }

  function renderZeroModule(m, index) {
    const optional = (m.tag || "").includes("80 档");
    const open = m.id === "m1";
    return `<details class="zero-module ${optional ? "optional" : ""}" ${open ? "open" : ""}>
      <summary class="zm-head"><span class="zm-order">${String(index + 1).padStart(2, "0")}</span><div><div class="eyebrow">${esc(m.tag || "保分模块")}</div><h3>${esc(m.title)}</h3><p>${esc(m.why)}</p></div><div class="zm-meta"><b>${esc(m.score)}</b><span>${esc(m.time)}</span></div></summary>
      <div class="zm-body"><p>${esc(m.plain)}</p>
        <ol class="zm-steps">${(m.steps || []).map((s) => `<li><span class="sn">${esc(s.n)}</span><div><b>${esc(s.do)}</b><div class="write">${esc(s.write)}</div></div></li>`).join("")}</ol>
        <div class="copybox"><h4>考试就这样写（填空版）</h4><pre>${esc(m.copy)}</pre></div>
        <div class="zm-columns"><div class="zm-box"><h5>必须背</h5><ul>${(m.must || []).map((x) => `<li>${esc(x)}</li>`).join("")}</ul></div><div class="zm-box skip"><h5>可以先放弃</h5><ul>${(m.skip || []).map((x) => `<li>${esc(x)}</li>`).join("")}</ul></div></div>
        <div class="zm-actions"><button class="btn btn-sm btn-accent" data-topic-study="${esc(m.topic_id)}">${icon("book")} 看对应速学卡</button><button class="btn btn-sm" data-topic-practice="${esc(m.topic_id)}">${icon("pencil")} 做这个模板的题</button><button class="btn btn-sm btn-ghost" data-action="open-ask">${icon("spark")} 问教练</button></div>
      </div>
    </details>`;
  }

  // ------------------------------------------------------------------
  // Topic map
  // ------------------------------------------------------------------
  function topicMastery(id) {
    return (insights().topics || []).find((t) => t.id === id)?.mastery || 0;
  }

  function renderMap() {
    const a = analysis();
    let topics = [...(a.topics || [])];
    if (S.mapSort === "mastery") topics.sort((x, y) => topicMastery(x.id) - topicMastery(y.id));
    else topics.sort((x, y) => (y.priority || 0) - (x.priority || 0));
    return `<div class="page-head"><div><div class="eyebrow">KNOWLEDGE MAP / 02</div><h1>考点地图</h1><p>每个考点都标了“为什么现在学”和原文位置。先攻高优先级、低掌握度的格子。</p></div>
      <div class="seg"><button class="${S.mapSort === "priority" ? "active" : ""}" data-map-sort="priority">按优先级</button><button class="${S.mapSort === "mastery" ? "active" : ""}" data-map-sort="mastery">按掌握度</button></div></div>
      <div class="topic-list">${topics.map((t, i) => renderTopicCard(t, i)).join("") || `<div class="empty-state"><h3>暂无考点</h3><p>回到资料箱重新生成。</p></div>`}</div>`;
  }

  function renderTopicCard(t, index) {
    const g = t.guide || {};
    const open = S.openTopics.has(t.id);
    const sources = t.sources || [];
    const tier = tierOf(t);
    return `<article class="card topic-card ${open ? "open" : ""}" data-topic-card="${esc(t.id)}">
      <div class="topic-summary" data-topic-toggle="${esc(t.id)}">
        <span class="topic-num">${String(index + 1).padStart(2, "0")}</span>
        <div class="topic-main"><h3>${esc(t.name)} <span class="badge ${tier === "s" ? "badge-accent" : tier === "a" ? "badge-green" : "badge-muted"}">${tier.toUpperCase()} · 优先级 ${t.priority || 0}</span></h3><p>${esc(t.why || "")}</p></div>
        <div class="topic-score"><div class="bar"><span style="width:${pct(topicMastery(t.id))}%"></span></div><span>${pct(topicMastery(t.id))}%</span></div>
        <span class="topic-chevron">${icon("chevron")}</span>
      </div>
      <div class="topic-detail">
        <div class="guide-grid">
          <div>
            <div class="guide-block"><div class="guide-label">2 分钟建立直觉</div><div class="guide-text">${rich(g.two_minute || "资料未展开。")}</div></div>
            <div class="guide-block"><div class="guide-label">考试必须掌握</div><ul class="guide-list">${(g.core || t.key_points || []).map((x) => `<li>${esc(x)}</li>`).join("") || "<li>资料未展开</li>"}</ul></div>
            ${g.formula || t.formula ? `<div class="guide-block"><div class="guide-label">公式 / 判定式</div><div class="formula-box">${esc(g.formula || t.formula)}</div></div>` : ""}
          </div>
          <div>
            <div class="guide-block"><div class="guide-label">最小例子 / 自检</div><div class="guide-text">${rich(g.worked_example || "资料未给出例题。")}</div></div>
            <div class="guide-block"><div class="guide-label">记忆钩子</div><div class="guide-text">${rich(g.memory_hook || "")}</div></div>
            <div class="guide-block"><div class="guide-label">易错点</div><div class="trap-box"><ul class="guide-list" style="padding-left:15px">${(g.traps || []).map((x) => `<li>${esc(x)}</li>`).join("") || "<li>注意适用条件。</li>"}</ul></div></div>
            ${g.answer_template ? `<div class="guide-block"><div class="guide-label">答题骨架</div><div class="guide-text">${rich(g.answer_template)}</div></div>` : ""}
          </div>
        </div>
        <div class="topic-actions">
          <button class="btn btn-sm btn-accent" data-topic-study="${esc(t.id)}">${icon("book")} 学这张卡</button>
          <button class="btn btn-sm" data-topic-practice="${esc(t.id)}">${icon("pencil")} 只练这个考点</button>
          <span class="badge badge-muted">${(t.question_types || []).map((x) => esc(x)).join(" · ") || "综合"}</span>
        </div>
        ${sources.length ? `<div class="source-list">${sources.map((s) => `<div class="source-item"><b>${esc(s.doc_name || s.doc_id)} · ${esc(s.locator)}</b><p>${esc(s.quote || "")}</p></div>`).join("")}</div>` : `<div class="warn-box">这个考点没有定位到可靠原文，可能是模型概括；复习时请以课件为准。</div>`}
      </div>
    </article>`;
  }

  // ------------------------------------------------------------------
  // Study / flashcards
  // ------------------------------------------------------------------
  function dueCard(c) {
    const st = progress().cards?.[c.id];
    if (!st?.seen) return true;
    try { return new Date(st.due) <= new Date(); } catch (_) { return true; }
  }

  function rebuildCardOrder() {
    const cards = analysis()?.cards || [];
    let pool = S.cardDueOnly ? cards.filter(dueCard) : cards;
    if (!pool.length) pool = cards;
    S.cardOrder = pool.map((c) => c.id);
    S.cardIndex = Math.min(S.cardIndex, Math.max(0, S.cardOrder.length - 1));
    S.cardRevealed = false;
  }

  function currentCard() {
    const id = S.cardOrder[S.cardIndex];
    return (analysis()?.cards || []).find((c) => c.id === id);
  }

  function renderStudy() {
    const a = analysis();
    const topics = a?.topics || [];
    if (!S.selectedTopic) S.selectedTopic = topics[0]?.id || null;
    return `<div class="study-head"><div><div class="eyebrow">LEARN / 03</div><h1>速学 / 回忆</h1><p class="muted small">先看懂，再合上资料复述。不要用“看过了”冒充“记住了”。</p></div>
      <div class="study-tabs seg"><button class="${S.studyTab === "guide" ? "active" : ""}" data-study-tab="guide">速学卡</button><button class="${S.studyTab === "flashcards" ? "active" : ""}" data-study-tab="flashcards">回忆卡</button></div></div>
      ${S.studyTab === "guide" ? renderGuideStudy(topics) : renderFlashcards()}`;
  }

  function renderGuideStudy(topics) {
    const t = topics.find((x) => x.id === S.selectedTopic) || topics[0];
    if (!t) return `<div class="empty-state"><h3>暂无速学卡</h3><p>重新生成冲刺包。</p></div>`;
    const g = t.guide || {};
    return `<div class="study-layout">
      <div class="card study-side">${topics.map((x, i) => `<button class="study-topic-btn ${x.id === t.id ? "active" : ""}" data-study-topic="${esc(x.id)}"><span class="num">${String(i + 1).padStart(2, "0")}</span><span>${esc(x.name)}</span><span class="st">${pct(topicMastery(x.id))}%</span></button>`).join("")}</div>
      <article class="card guide-panel">
        <div class="guide-panel-head"><div><div class="eyebrow">TOPIC ${esc(t.id?.replace("t", ""))} / PRIORITY ${t.priority}</div><h2>${esc(t.name)}</h2><p>${esc(t.why || "")}</p></div><span class="badge badge-accent">${pct(topicMastery(t.id))}% 掌握</span></div>
        <div class="guide-sections">
          <div class="guide-section full"><h4>2 分钟建立直觉</h4><div class="big-text">${rich(g.two_minute || "资料未展开。")}</div></div>
          <div class="guide-section"><h4>考试必须掌握</h4><ul class="guide-list">${(g.core || t.key_points || []).map((x) => `<li>${esc(x)}</li>`).join("")}</ul></div>
          <div class="guide-section"><h4>公式 / 判定式</h4>${g.formula || t.formula ? `<div class="formula-box">${esc(g.formula || t.formula)}</div>` : `<div class="muted small">资料未给出公式。</div>`}<h4 style="margin-top:15px">记忆钩子</h4><div class="big-text">${rich(g.memory_hook || "")}</div></div>
          <div class="guide-section full"><h4>最小例子 / 自检</h4><div class="big-text">${rich(g.worked_example || "资料未展开。")}</div></div>
          <div class="guide-section"><h4>易错点</h4><div class="trap-box"><ul class="guide-list" style="padding-left:15px">${(g.traps || []).map((x) => `<li>${esc(x)}</li>`).join("") || "<li>注意适用条件。</li>"}</ul></div></div>
          <div class="guide-section"><h4>简答 / 论述骨架</h4><div class="big-text">${rich(g.answer_template || "先结论，再条件，再应用。")}</div></div>
          ${(t.sources || []).length ? `<div class="guide-section full"><h4>原文位置</h4><div class="source-list">${t.sources.map((s) => `<div class="source-item"><b>${esc(s.doc_name || s.doc_id)} · ${esc(s.locator)}</b><p>${esc(s.quote || "")}</p></div>`).join("")}</div></div>` : ""}
        </div>
        <div class="study-actions"><button class="btn btn-accent" data-study-flash-topic="${esc(t.id)}">${icon("brain")} 练这个考点的回忆卡</button><button class="btn" data-topic-practice="${esc(t.id)}">${icon("pencil")} 做相关题</button><button class="btn btn-ghost" data-action="open-ask">${icon("spark")} 问教练</button></div>
      </article>
    </div>`;
  }

  function renderFlashcards() {
    const cards = analysis()?.cards || [];
    if (!cards.length) return `<div class="empty-state"><h3>还没有回忆卡</h3><p>到资料箱重新生成。</p></div>`;
    if (!S.cardOrder.length) rebuildCardOrder();
    const card = currentCard() || cards[0];
    if (!card) return "";
    const idx = Math.max(0, S.cardOrder.indexOf(card.id));
    const total = S.cardOrder.length;
    const seen = new Set((analysis().cards || []).filter((c) => progress().cards?.[c.id]?.seen).map((c) => c.id)).size;
    return `<div class="study-layout">
      <div class="card study-side"><button class="study-topic-btn ${!S.cardDueOnly ? "active" : ""}" data-card-filter="all"><span class="num">∞</span><span>全部卡片</span><span class="st">${cards.length}</span></button><button class="study-topic-btn ${S.cardDueOnly ? "active" : ""}" data-card-filter="due"><span class="num">!</span><span>只看到期 / 未看</span><span class="st">${insights().due_cards || 0}</span></button>
      <div style="border-top:1px solid var(--line);margin:8px 4px;padding:10px 5px 3px" class="tiny muted">已过 ${seen}/${cards.length} 张<br>评价越诚实，复习越准。</div></div>
      <div class="card-study">
        <div class="deck-bar"><span>${idx + 1} / ${total}</span><div class="deck-progress"><span style="width:${((idx + 1) / total) * 100}%"></span></div><span>${S.cardDueOnly ? "到期队列" : "全部卡片"}</span></div>
        <div class="flashcard card">
          <div class="fc-topic">${esc(card.topic)} · ${esc(card.type || "recall")}</div>
          <div class="fc-front">${rich(card.front)}</div>
          ${S.cardRevealed ? `<div class="fc-answer">${rich(card.back)}</div>` : `<button class="btn btn-accent reveal-btn" data-action="reveal-card">显示答案 ${icon("arrow")}</button>`}
        </div>
        ${S.cardRevealed ? `<div class="rating-row">
          <button class="rating-btn again" data-card-rate="again"><b>忘了</b><span>10 分钟后</span></button>
          <button class="rating-btn hard" data-card-rate="hard"><b>很吃力</b><span>明天</span></button>
          <button class="rating-btn good" data-card-rate="good"><b>想起来了</b><span>2 天后</span></button>
          <button class="rating-btn easy" data-card-rate="easy"><b>很熟</b><span>4 天后</span></button>
        </div><div class="kbd-hint"><kbd>1</kbd> 忘了 · <kbd>2</kbd> 吃力 · <kbd>3</kbd> 想起 · <kbd>4</kbd> 很熟</div>` : `<div class="kbd-hint">先在心里回答，再按 <kbd>空格</kbd> 看答案</div>`}
      </div>
    </div>`;
  }

  async function rateCard(rating) {
    const card = currentCard();
    if (!card) return;
    try {
      await api("/api/progress", { method: "POST", body: { type: "card", id: card.id, rating } });
      S.cardRevealed = false;
      S.cardOrder.splice(S.cardIndex, 1);
      if (S.cardIndex >= S.cardOrder.length) S.cardIndex = 0;
      if (!S.cardOrder.length) rebuildCardOrder();
      const fresh = await api("/api/state");
      S.data = fresh;
      render();
      toast(rating === "again" ? "已放回短间隔队列" : "记住了，继续", "success");
    } catch (err) { toast(err.message, "error"); }
  }

  // ------------------------------------------------------------------
  // Practice
  // ------------------------------------------------------------------
  function allQuestions() { return analysis()?.questions || []; }

  function renderPractice() {
    if (!S.practice) {
      const qs = allQuestions();
      const topics = analysis()?.topics || [];
      const wrong = wrongQuestions();
      return `<div class="page-head"><div><div class="eyebrow">DRILL / 04</div><h1>刷题</h1><p>一次只做一题，提交后立刻看解析。答错自动进错题本。</p></div></div>
      <div class="two-col">
        <div class="card card-pad">
          <div class="stat-strip"><div><b>${qs.length}</b><span>仿真练习题</span></div><div><b>${insights().accuracy || 0}%</b><span>历史正确率</span></div><div><b>${wrong.length}</b><span>待清理错题</span></div></div>
          <h2 style="font-size:26px;margin:6px 0 12px">选择训练方式</h2>
          <div class="field" style="max-width:300px"><label>限定考点</label><select id="practiceTopic"><option value="all">全部考点</option>${topics.map((t) => `<option value="${esc(t.id)}">${esc(t.name)}</option>`).join("")}</select></div>
          <div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:16px">
            <button class="btn btn-accent btn-lg" data-start-practice="10">${icon("pencil")} 10 题快刷</button>
            <button class="btn btn-lg" data-start-practice="20">20 题混合</button>
            <button class="btn btn-lg" data-start-practice="all">全部题</button>
          </div>
          <p class="muted small" style="margin-top:14px">建议：先做 10 题诊断，正确率低于 60% 就回速学卡；高于 80% 直接进模拟考。</p>
        </div>
        <div class="card card-pad">
          <div class="eyebrow">HOW TO USE</div><h2 style="font-size:24px;margin:7px 0 9px">刷题不是对答案</h2>
          <ol class="guide-list" style="font-size:12px"><li>先不查资料，写出你的第一反应。</li><li>提交后，用一句话解释“为什么”。</li><li>错题只记错因：概念、条件、计算、审题。</li><li>隔 10 分钟、睡前、明早各回炉一次。</li></ol>
          <div class="info-box" style="margin-top:14px">题目是仿真练习，不保证命中真题。遇到与老师范围冲突，以老师为准。</div>
        </div>
      </div>`;
    }
    const s = S.practice;
    if (s.done) return renderPracticeResult();
    const q = s.questions[s.index];
    const selected = s.selected || [];
    const isOpen = ["short", "calculation", "essay"].includes(q.type);
    const correctSet = correctLetters(q);
    const objective = !isOpen;
    return `<div class="practice-shell">
      <div class="practice-top"><button class="text-btn" data-action="exit-practice">← 退出</button><span>第 ${s.index + 1} / ${s.questions.length} 题</span><div class="bar"><span style="width:${((s.index) / s.questions.length) * 100}%"></span></div></div>
      <div class="card card-pad">
        <div class="qmeta"><span class="badge badge-accent">${TYPE_LABEL[q.type] || q.type}</span><span class="badge badge-muted">${esc(q.topic || "综合")}</span><span class="badge badge-gold">难度 ${q.difficulty || 2}/5</span></div>
        <div class="qstem">${rich(q.stem)}</div>
        ${isOpen ? `<div class="answer-area"><textarea id="practiceAnswer" placeholder="写出你的答案。先列关键词，再补成句子。" ${s.submitted ? "disabled" : ""}>${esc(s.openAnswer || "")}</textarea></div>` : `<div class="options">${optionHTML(q, selected, s.submitted, correctSet, objective)}</div>`}
        ${s.submitted ? practiceFeedbackHTML(q, s) : ""}
        <div class="qfooter"><span class="tiny muted">${isOpen ? "简答题提交后自评" : "提交后立即判分"}</span>
          ${!s.submitted ? `<button class="btn btn-accent" data-action="submit-practice">${icon("check")} 提交答案</button>` : (s.result === null && isOpen ? "" : `<button class="btn btn-dark" data-action="next-practice">${s.index + 1 >= s.questions.length ? "看结果" : "下一题"} ${icon("arrow")}</button>`)}
        </div>
      </div>
    </div>`;
  }

  function optionHTML(q, selected, submitted, correctSet, objective) {
    let options = q.options || [];
    if (q.type === "judge" && !options.length) options = ["对", "错"];
    return options.map((opt, i) => {
      const letter = q.type === "judge" ? (i === 0 ? "对" : "错") : String.fromCharCode(65 + i);
      let cls = selected.includes(letter) ? "selected" : "";
      if (submitted && objective) {
        if (correctSet.includes(letter)) cls += " correct";
        else if (selected.includes(letter)) cls += " wrong";
      }
      return `<button class="option ${cls}" data-practice-option="${esc(letter)}" ${submitted ? "disabled" : ""}><span class="opt-letter">${esc(letter)}</span><span>${esc(cleanOption(opt, i))}</span></button>`;
    }).join("");
  }

  function cleanOption(opt, i) {
    return String(opt || "").replace(new RegExp(`^${String.fromCharCode(65 + i)}[.、．)）]\\s*`), "");
  }

  function correctLetters(q) {
    if (q.type === "judge") {
      const a = String(q.answer ?? "").trim().toLowerCase();
      return ["对", "正确", "true", "t", "√", "是"].includes(a) ? ["对"] : ["错"];
    }
    let vals = Array.isArray(q.answer) ? q.answer : [q.answer];
    const out = [];
    vals.forEach((v) => {
      const matches = String(v ?? "").toUpperCase().match(/\b[A-F]\b/g);
      if (matches) matches.forEach((m) => out.push(m));
      else if (/^[A-F]$/.test(String(v).trim().toUpperCase())) out.push(String(v).trim().toUpperCase());
    });
    return [...new Set(out)];
  }

  function selectedDisplay(q, selected) {
    if (!selected?.length) return "（未作答）";
    return selected.map((letter) => {
      const options = q.options || [];
      const idx = q.type === "judge" ? (letter === "对" ? 0 : 1) : letter.charCodeAt(0) - 65;
      return options[idx] ? `${letter}. ${cleanOption(options[idx], idx)}` : letter;
    }).join("；");
  }

  function practiceFeedbackHTML(q, s) {
    const isOpen = ["short", "calculation", "essay"].includes(q.type);
    if (isOpen && s.result === null) {
      return `<div class="feedback correct"><h4>对照参考答案自评</h4><div class="model-answer">${rich(q.answer || "资料未给出答案")}</div>${q.rubric ? `<p><b>评分点：</b>${esc(q.rubric)}</p>` : ""}<div class="self-grade"><span class="small">你答到了吗？</span><button class="btn btn-sm btn-green" data-self-grade="1">答到了</button><button class="btn btn-sm btn-danger" data-self-grade="0">没答到</button></div></div>`;
    }
    const good = s.result === true;
    return `<div class="feedback ${good ? "correct" : "wrong"}"><h4>${good ? "答对了" : "这题要回炉"}</h4>
      <p><b>你的答案：</b>${esc(s.answerDisplay || "（未作答）")}</p>
      <p><b>参考答案：</b>${esc(Array.isArray(q.answer) ? q.answer.join("、") : q.answer)}</p>
      ${q.rubric ? `<p><b>评分点：</b>${esc(q.rubric)}</p>` : ""}
      ${q.explanation ? `<p><b>解析：</b>${esc(q.explanation)}</p>` : ""}</div>`;
  }

  function startPractice(mode = "10", topicId = null) {
    let qs = allQuestions();
    if (topicId) qs = qs.filter((q) => q.topic_id === topicId);
    else {
      const sel = $("#practiceTopic");
      if (sel && sel.value !== "all") qs = qs.filter((q) => q.topic_id === sel.value);
    }
    if (mode === "wrong") qs = wrongQuestions().map((x) => x.q);
    if (!qs.length) { toast("这个范围暂时没有题", "error"); return; }
    if (mode !== "all" && mode !== "wrong") qs = qs.slice(0, Number(mode) || 10);
    S.practice = { questions: qs, index: 0, selected: [], openAnswer: "", submitted: false, result: null, recorded: false, correct: 0, answered: 0, answerDisplay: "" };
    S.view = "practice";
    render();
  }

  function submitPractice() {
    const s = S.practice; if (!s || s.submitted) return;
    const q = s.questions[s.index];
    const isOpen = ["short", "calculation", "essay"].includes(q.type);
    if (!isOpen && !(s.selected || []).length) { toast("先选一个答案", "error"); return; }
    if (isOpen) {
      const ta = $("#practiceAnswer");
      s.openAnswer = ta?.value || "";
      if (!s.openAnswer.trim()) { toast("先写点什么，再自评", "error"); return; }
      s.submitted = true;
      s.result = null;
      s.answerDisplay = s.openAnswer;
      render();
      return;
    }
    const good = sameAnswer(s.selected, correctLetters(q));
    s.submitted = true;
    s.result = good;
    s.answerDisplay = selectedDisplay(q, s.selected);
    s.answered += 1;
    if (good) s.correct += 1;
    s.recorded = true;
    api("/api/progress", { method: "POST", body: { type: "question", id: q.id, correct: good, answer: s.answerDisplay } })
      .then((r) => { S.data.insights = r.insights; })
      .catch(() => {});
    render();
  }

  function sameAnswer(a, b) {
    const A = [...new Set(a)].sort().join("|");
    const B = [...new Set(b)].sort().join("|");
    return A === B;
  }

  function selfGradePractice(good) {
    const s = S.practice; if (!s || s.result !== null) return;
    const q = s.questions[s.index];
    s.result = !!good;
    s.answered += 1;
    if (good) s.correct += 1;
    s.recorded = true;
    const body = { type: "question", id: q.id, correct: !!good, answer: s.openAnswer || "" };
    api("/api/progress", { method: "POST", body }).then((r) => { S.data.insights = r.insights; }).catch(() => {});
    render();
  }

  function nextPractice() {
    const s = S.practice; if (!s) return;
    if (s.index + 1 >= s.questions.length) { s.done = true; render(); return; }
    s.index += 1; s.selected = []; s.openAnswer = ""; s.submitted = false; s.result = null; s.recorded = false; s.answerDisplay = ""; render();
  }

  function renderPracticeResult() {
    const s = S.practice;
    const acc = s.answered ? Math.round((s.correct / s.answered) * 100) : 0;
    return `<div class="practice-shell"><div class="card result-hero">
      <div class="eyebrow">SESSION COMPLETE</div><div class="score">${acc}<small>%</small></div>
      <h2 style="margin:10px 0 4px">${acc >= 80 ? "这组可以过" : acc >= 60 ? "有基础，但还不稳" : "先回速学卡补洞"}</h2>
      <p class="muted">${s.correct} / ${s.answered} 题答对。答错题已自动进入错题本。</p>
      <div class="result-stats"><div class="result-stat"><b>${s.questions.length}</b><span>本次题量</span></div><div class="result-stat"><b>${s.answered}</b><span>已判分</span></div><div class="result-stat"><b>${s.questions.length - s.answered}</b><span>未作答</span></div></div>
      <div class="result-actions"><button class="btn btn-accent" data-action="restart-practice">${icon("refresh")} 再来一组</button><button class="btn" data-nav="study">${icon("book")} 回速学卡</button><button class="btn" data-nav="errors">${icon("flag")} 看错题本</button></div>
    </div></div>`;
  }

  function wrongQuestions() {
    const qs = allQuestions();
    const qp = progress().questions || {};
    return qs.map((q) => {
      const st = qp[q.id];
      const attempts = st?.attempts || [];
      const last = attempts[attempts.length - 1];
      return last && !last.correct ? { q, last } : null;
    }).filter(Boolean);
  }

  // ------------------------------------------------------------------
  // Mock exam
  // ------------------------------------------------------------------
  function flattenMock(mock) {
    const out = [];
    (mock?.sections || []).forEach((sec) => {
      const n = Math.max(1, sec.questions?.length || 1);
      (sec.questions || []).forEach((q) => out.push({ ...q, section: sec.name, maxScore: Number(q.score) || Number(sec.score) / n || 1 }));
    });
    return out;
  }

  function renderMock() {
    const a = analysis();
    const mock = a?.mock;
    if (!mock || !(mock.sections || []).length) return `<div class="empty-state"><div class="empty-icon">${icon("clock")}</div><h3>还没有仿真卷</h3><p>重新生成冲刺包，或先在刷题里做一组混合题。</p><button class="btn btn-accent" data-nav="practice">去刷题</button></div>`;
    if (!S.mock) return renderMockIntro(mock);
    if (S.mock.status === "active") return renderMockExam();
    return renderMockResult();
  }

  function renderMockIntro(mock) {
    const qs = flattenMock(mock);
    const p = analysis().exam_profile || {};
    return `<div class="page-head"><div><div class="eyebrow">MOCK / 05</div><h1>模拟考</h1><p>严格计时，不查资料。分数不是目的，暴露“会在哪里丢分”才是。</p></div></div>
    <div class="mock-intro">
      <div class="card mock-paper">
        <div class="eyebrow">FULL-LENGTH SIMULATION</div><h2 style="margin:7px 0">${esc(mock.title || "期中仿真卷")}</h2>
        <p class="muted">${esc(p.paper_format || "按资料反推的卷型")} · 置信度 ${esc(p.confidence || "低")}</p>
        <div class="stat-strip"><div><b>${mock.duration_minutes || 120}</b><span>分钟</span></div><div><b>${mock.total_score || 100}</b><span>满分</span></div><div><b>${qs.length}</b><span>题目</span></div></div>
        <div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:19px"><button class="btn btn-accent btn-lg" data-action="start-mock">${icon("play")} 开始计时</button><button class="btn btn-lg" data-nav="practice">先热身</button></div>
        <div class="warn-box" style="margin-top:18px">这是仿真卷，不是原题。老师给的范围、题型和分值优先于本卷。</div>
      </div>
      <div class="card mock-instructions">
        <div class="eyebrow">RULES</div><h3>考试规则</h3>
        <ol class="instruction-list">${(mock.instructions || ["闭卷，限时完成。", "先易后难。"]).map((x) => `<li>${esc(x)}</li>`).join("")}<li>提交后客观题自动判分，主观题按参考答案自评。</li><li>建议先在草稿纸写关键词，再展开成答案。</li></ol>
        <div class="guide-label" style="margin-top:18px">卷面结构</div>
        ${(mock.sections || []).map((sec) => `<div class="blueprint-row"><span>${esc(sec.name)}</span><b>${sec.questions?.length || 0} 题 · ${sec.score || 0} 分</b></div>`).join("")}
      </div>
    </div>`;
  }

  function startMock() {
    const mock = analysis()?.mock;
    if (!mock) return;
    const sections = (mock.sections || []).map((sec) => ({
      ...sec,
      questions: (sec.questions || []).map((q) => ({ ...q }))
    }));
    const seconds = Math.max(10, Number(mock.duration_minutes) || 120) * 60;
    S.mock = {
      status: "active",
      sections,
      answers: {},
      selfScores: {},
      startedAt: Date.now(),
      endsAt: Date.now() + seconds * 1000,
      totalSeconds: seconds,
      lastRemaining: seconds
    };
    render();
  }

  function renderMockExam() {
    const s = S.mock;
    if (!s) return "";
    let n = 0;
    const total = s.sections.reduce((acc, sec) => acc + (sec.questions?.length || 0), 0);
    return `<div class="practice-shell">
      <div class="card mock-toolbar no-print"><div><div class="eyebrow">EXAM IN PROGRESS</div><div class="timer" id="mockTimer">--:--</div></div><div class="muted small">已答 <b id="mockAnswered">0</b> / ${total} 题</div><button class="btn btn-accent" data-action="submit-mock">交卷</button></div>
      <div class="card mock-paper" style="padding:30px">
        <div style="text-align:center;border-bottom:2px solid var(--ink);padding-bottom:15px;margin-bottom:20px"><h2 style="margin:0;font-size:28px">${esc(analysis().mock.title || "期中仿真卷")}</h2><div class="muted small">限时 ${analysis().mock.duration_minutes || 120} 分钟 · 满分 ${analysis().mock.total_score || 100} 分 · 闭卷</div></div>
        ${s.sections.map((sec) => `<section class="mock-section"><div class="mock-section-head"><h3>${esc(sec.name)}</h3><span>${sec.score || 0} 分</span></div>
          ${(sec.questions || []).map((q) => { n += 1; return renderMockQuestion(q, n, s); }).join("")}
        </section>`).join("")}
        <div style="text-align:center;padding-top:10px"><button class="btn btn-accent btn-lg" data-action="submit-mock">交卷并看解析</button></div>
      </div></div>`;
  }

  function renderMockQuestion(q, n, s) {
    const isOpen = ["short", "calculation", "essay"].includes(q.type);
    const ans = s.answers[q.id];
    if (isOpen) {
      return `<div class="mock-q"><div class="mock-q-head"><b>${n}.</b><span class="badge badge-muted">${TYPE_LABEL[q.type] || q.type}</span><span class="tiny muted">${esc(q.topic || "")}</span></div><div class="qstem">${rich(q.stem)}</div><textarea class="answer-area" style="width:100%;min-height:120px;border:1px solid var(--line-strong);border-radius:10px;padding:11px" data-mock-text="${esc(q.id)}" placeholder="写出答案要点…">${esc(ans || "")}</textarea></div>`;
    }
    const options = q.type === "judge" && !(q.options || []).length ? ["对", "错"] : (q.options || []);
    return `<div class="mock-q"><div class="mock-q-head"><b>${n}.</b><span class="badge badge-muted">${TYPE_LABEL[q.type] || q.type}</span><span class="tiny muted">${esc(q.topic || "")}</span></div><div class="qstem">${rich(q.stem)}</div><div class="options">${options.map((opt, i) => {
      const letter = q.type === "judge" ? (i === 0 ? "对" : "错") : String.fromCharCode(65 + i);
      const selected = q.type === "multiple" ? (ans || []).includes(letter) : ans === letter;
      return `<button class="option ${selected ? "selected" : ""}" data-mock-opt="${esc(letter)}" data-qid="${esc(q.id)}" data-qtype="${esc(q.type)}"><span class="opt-letter">${esc(letter)}</span><span>${esc(cleanOption(opt, i))}</span></button>`;
    }).join("")}</div></div>`;
  }

  function startMockTimer() {
    stopMockTimer();
    const tick = () => {
      if (!S.mock || S.mock.status !== "active") { stopMockTimer(); return; }
      const remain = Math.max(0, Math.ceil((S.mock.endsAt - Date.now()) / 1000));
      S.mock.lastRemaining = remain;
      const el = $("#mockTimer");
      if (el) {
        el.textContent = formatTime(remain);
        el.classList.toggle("warn", remain <= 300);
      }
      if (remain <= 0) { stopMockTimer(); submitMock(true); }
    };
    tick();
    S.mockTimer = setInterval(tick, 1000);
  }

  function stopMockTimer() {
    if (S.mockTimer) { clearInterval(S.mockTimer); S.mockTimer = null; }
  }

  function formatTime(sec) {
    const m = Math.floor(sec / 60), s = sec % 60;
    return `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
  }

  function updateMockAnswered() {
    if (!S.mock) return;
    const total = flattenMock(analysis().mock).length;
    const answered = Object.keys(S.mock.answers || {}).filter((k) => {
      const v = S.mock.answers[k];
      return Array.isArray(v) ? v.length > 0 : String(v || "").trim().length > 0;
    }).length;
    const el = $("#mockAnswered"); if (el) el.textContent = answered;
  }

  function submitMock(auto = false) {
    const s = S.mock; if (!s || s.status !== "active") return;
    const qs = flattenMock(analysis().mock);
    const unanswered = qs.filter((q) => {
      const v = s.answers[q.id];
      return Array.isArray(v) ? !v.length : !String(v || "").trim();
    }).length;
    if (!auto && unanswered && !window.confirm(`还有 ${unanswered} 题未作答，确定交卷吗？`)) return;
    const items = qs.map((q) => {
      const isOpen = ["short", "calculation", "essay"].includes(q.type);
      let correct = false, points = 0;
      if (!isOpen) {
        const ans = q.type === "multiple" ? (s.answers[q.id] || []) : [s.answers[q.id] || ""];
        correct = sameAnswer(ans, correctLetters(q));
        points = correct ? q.maxScore : 0;
      }
      return { q, isOpen, correct, points, userAnswer: s.answers[q.id] };
    });
    s.status = "review";
    s.result = { items, totalPossible: qs.reduce((n, q) => n + q.maxScore, 0) };
    stopMockTimer();
    render();
    if (auto) toast("时间到，已自动交卷", "error");
  }

  function renderMockResult() {
    const s = S.mock;
    const items = s.result?.items || [];
    const possible = s.result?.totalPossible || 1;
    const objectivePoints = items.filter((x) => !x.isOpen).reduce((n, x) => n + x.points, 0);
    const selfPoints = items.filter((x) => x.isOpen).reduce((n, x) => n + Number(s.selfScores?.[x.q.id] || 0), 0);
    const points = objectivePoints + selfPoints;
    const percent = Math.round((points / possible) * 100);
    const saved = s.status === "saved";
    return `<div class="practice-shell">
      <div class="card mock-paper" style="padding:0;overflow:hidden">
        <div class="mock-result-head"><div><div class="eyebrow">${saved ? "RESULT SAVED" : "SELF-SCORING"}</div><div class="big-score">${percent}<small style="font-size:20px;color:var(--muted)">%</small></div><div class="mock-result-meta"><span>客观题 ${Math.round(objectivePoints)} 分</span><span>主观题自评 ${Math.round(selfPoints)} 分</span><span>总分 ${Math.round(points)} / ${Math.round(possible)}</span></div></div>
          <div style="margin-left:auto;display:flex;gap:7px;flex-wrap:wrap"><button class="btn btn-sm" data-action="restart-mock">${icon("refresh")} 再做一次</button><button class="btn btn-sm btn-accent" data-action="save-mock" ${saved ? "disabled" : ""}>${saved ? "已记录" : "记录成绩"}</button></div></div>
        <div class="review-list">
          ${items.map((x, i) => `<div class="review-q"><div class="mock-q-head"><b>${i + 1}.</b><span class="badge ${x.isOpen ? "badge-gold" : x.correct ? "badge-green" : "badge-accent"}">${x.isOpen ? "待自评" : x.correct ? "正确" : "错误"}</span><span class="tiny muted">${esc(x.q.topic || "")}</span></div>
            <div class="qstem" style="font-size:15px">${rich(x.q.stem)}</div>
            <p class="small"><b>你的答案：</b>${esc(x.isOpen ? (x.userAnswer || "（未作答）") : selectedDisplay(x.q, Array.isArray(x.userAnswer) ? x.userAnswer : (x.userAnswer ? [x.userAnswer] : [])))}</p>
            <div class="review-answer"><b>参考答案：</b>${esc(Array.isArray(x.q.answer) ? x.q.answer.join("、") : x.q.answer)}${x.q.rubric ? `\n评分点：${x.q.rubric}` : ""}${x.q.explanation ? `\n解析：${x.q.explanation}` : ""}</div>
            ${x.isOpen ? `<div style="display:flex;align-items:center;gap:7px;margin-top:8px"><span class="small">自评得分</span><input class="score-input" type="number" min="0" max="${x.q.maxScore}" step="0.5" value="${s.selfScores?.[x.q.id] ?? 0}" data-mock-score="${esc(x.q.id)}" ${saved ? "disabled" : ""}><span class="tiny muted">/ ${x.q.maxScore} 分</span></div>` : ""}
          </div>`).join("")}
        </div>
      </div>
      <div style="display:flex;justify-content:center;gap:8px;margin-top:15px;flex-wrap:wrap"><button class="btn" data-nav="errors">${icon("flag")} 去错题本</button><button class="btn" data-nav="study">${icon("book")} 回高频考点</button></div>
    </div>`;
  }

  function saveMock() {
    const s = S.mock; if (!s || s.status === "saved") return;
    const items = s.result.items;
    const possible = s.result.totalPossible || 1;
    const obj = items.filter((x) => !x.isOpen).reduce((n, x) => n + x.points, 0);
    const self = items.filter((x) => x.isOpen).reduce((n, x) => n + Number(s.selfScores?.[x.q.id] || 0), 0);
    const percent = Math.round(((obj + self) / possible) * 100);
    const detail = {};
    items.forEach((x) => { detail[x.q.id] = { correct: x.correct, points: x.points, open: x.isOpen }; });
    api("/api/progress", { method: "POST", body: { type: "mock", score: percent, duration_minutes: (Date.now() - s.startedAt) / 60000, detail } })
      .then((r) => { S.data.insights = r.insights; s.status = "saved"; render(); toast("模考成绩已记录", "success"); })
      .catch((err) => toast(err.message, "error"));
  }

  // ------------------------------------------------------------------
  // Errors, docs
  // ------------------------------------------------------------------
  function renderErrors() {
    const wrong = wrongQuestions();
    const attempts = insights().attempts || 0, acc = insights().accuracy || 0;
    return `<div class="page-head"><div><div class="eyebrow">ERROR LOG / 06</div><h1>错题本</h1><p>只记录“错因”，不抄整题。每道错题至少二次作答，才算清掉。</p></div><button class="btn" data-nav="practice">${icon("pencil")} 继续刷题</button></div>
    <div class="stat-strip"><div><b>${wrong.length}</b><span>待清理错题</span></div><div><b>${attempts}</b><span>累计作答</span></div><div><b>${acc}%</b><span>正确率</span></div></div>
    <div class="card card-pad">${wrong.length ? wrong.map(({ q, last }, i) => `<div class="error-item"><div class="qmeta"><span class="badge badge-accent">${TYPE_LABEL[q.type] || q.type}</span><span class="badge badge-muted">${esc(q.topic || "")}</span><span class="tiny muted">${new Date(last.at).toLocaleString("zh-CN", { month: "numeric", day: "numeric", hour: "2-digit", minute: "2-digit" })}</span></div>
      <div class="stem">${rich(q.stem)}</div>
      <div class="error-compare"><div><b>你的答案</b><br>${esc(last.answer || "（未记录）")}</div><div><b>参考答案</b><br>${esc(Array.isArray(q.answer) ? q.answer.join("、") : q.answer)}</div></div>
      ${q.explanation ? `<p class="small muted" style="margin:8px 0 0"><b>解析：</b>${esc(q.explanation)}</p>` : ""}
      <div class="error-actions"><button class="btn btn-sm" data-error-redo="${esc(q.id)}">${icon("refresh")} 重做这题</button><button class="btn btn-sm btn-ghost" data-topic-study="${esc(q.topic_id)}">${icon("book")} 回考点</button></div></div>`).join("") : `<div class="empty-state"><div class="empty-icon">${icon("check")}</div><h3>错题本是空的</h3><p>要么你全对了，要么还没开始做题。建议先来一组 10 题诊断。</p><button class="btn btn-accent" data-nav="practice">开始诊断</button></div>`}</div>`;
  }

  function renderDocs() {
    const p = S.data.project;
    const a = analysis();
    const gen = a?.generation;
    return `<div class="page-head"><div><div class="eyebrow">MATERIALS / 07</div><h1>资料箱</h1><p>课件、作业、真题要分开标。真题越全，考点排序越准。</p></div><button class="btn btn-accent" data-action="generate">${icon("refresh")} ${a ? "重新生成" : "生成冲刺包"}</button></div>
    <div class="two-col">
      <div class="card card-pad">
        <div class="dropzone"><input type="file" class="hidden" multiple accept=".pptx,.pdf,.docx,.xlsx,.txt,.md,.csv"><div class="dropzone-icon">${icon("upload")}</div><b>拖入资料，或点击选择</b><small>PPTX / PDF / DOCX / XLSX / TXT / MD · 单文件 ≤80MB</small></div>
        <div class="upload-list" style="max-height:none">${(p.docs || []).map((d) => `<div class="doc-row"><div class="doc-icon ${esc(d.kind)}">${esc((d.ext || "").replace(".", "").toUpperCase())}</div><div><div class="doc-name">${esc(d.name)}</div><div class="doc-sub">${d.page_count || 0} 页 · ${Number(d.chars || 0).toLocaleString()} 字${d.warnings?.length ? " · 有解析提示" : ""}</div></div><select class="kind-select" data-doc-kind="${esc(d.doc_id)}">${KIND_ORDER.map((k) => `<option value="${k}" ${d.kind === k ? "selected" : ""}>${KIND_LABEL[k]}</option>`).join("")}</select><span class="doc-pages muted tiny">${esc(d.ext || "")}</span><span class="doc-chars muted tiny">${d.size ? Math.round(d.size / 1024) + " KB" : ""}</span><button class="icon-btn" data-delete-doc="${esc(d.doc_id)}" title="删除">${icon("trash")}</button></div>`).join("") || `<div class="empty-mini">还没有资料</div>`}</div>
        <div style="display:flex;gap:8px;margin-top:14px;flex-wrap:wrap"><button class="btn" data-action="import-inbox">${icon("folder")} 扫描资料夹</button><button class="btn btn-ghost" data-action="open-ask">${icon("spark")} 问教练</button></div>
        <div class="info-box">也可以把文件直接放进应用目录的 <span class="code">inbox/课件</span>、<span class="code">inbox/作业</span>、<span class="code">inbox/真题</span>，再点“扫描资料夹”。</div>
        <div class="info-box" style="margin-top:8px"><b>只有 PPT + 作业时：</b>系统把“作业重复出现 + PPT 明确强调”的考点排前面，其余标为背景/可暂缓。目标是先覆盖最可能考的 20%，不是把 100% 课件都学完。</div>
      </div>
      <div>
        <div class="card card-pad"><div class="eyebrow">EXAM SETTINGS</div><h2 style="font-size:23px;margin:5px 0 10px">考试设置</h2>
          <div class="form-grid">
            <div class="field full"><label>课程名称</label><input id="docCourse" value="${esc(p.course || "")}"></div>
            <div class="field"><label>考试日期</label><input id="docDate" type="date" value="${esc(p.exam_date || "")}"></div>
            <div class="field"><label>冲刺天数</label><input id="docDays" type="number" min="1" max="14" value="${esc(p.days || 3)}"></div>
            <div class="field"><label>每天小时</label><input id="docHours" type="number" min="0.5" max="16" step="0.5" value="${esc(p.hours_per_day || 5)}"></div>
          </div>
          <button class="btn btn-sm btn-dark" style="margin-top:10px" data-action="save-project-settings">${icon("check")} 保存考试设置</button>
        </div>
        <div class="card card-pad" style="margin-top:12px"><div class="eyebrow">MATERIAL HEALTH</div><h2 style="font-size:23px;margin:5px 0 10px">资料体检</h2>
          <div class="stat-strip" style="margin-bottom:10px"><div><b>${(p.docs || []).length}</b><span>文件</span></div><div><b>${totalPages()}</b><span>页/张</span></div><div><b>${((p.docs || []).reduce((n, d) => n + Number(d.chars || 0), 0) / 1000).toFixed(1)}k</b><span>可提取字</span></div></div>
          ${(p.docs || []).flatMap((d) => (d.warnings || []).map((w) => `<div class="warn-box"><b>${esc(d.name)}：</b>${esc(w)}</div>`)).join("") || `<div class="info-box">文字提取正常。公式、图片和扫描页不会自动识别，复习时请以原课件为准。</div>`}
          <div class="small muted" style="margin-top:10px">真题 ${(p.docs || []).filter((d) => d.kind === "exam").length} 份 · 作业 ${(p.docs || []).filter((d) => d.kind === "homework").length} 份 · 课件 ${(p.docs || []).filter((d) => d.kind === "slides").length} 份</div>
        </div>
        ${gen ? `<div class="card card-pad" style="margin-top:12px"><div class="eyebrow">GENERATION</div><h3 style="font-family:var(--sans);font-size:14px;margin:7px 0">生成记录</h3><div class="small muted">模式：${esc(gen.mode === "llm" ? "大模型增强" : gen.mode === "curated" ? "真题精编（本地）" : gen.mode === "fallback" ? "模型失败，离线降级" : "离线框架")}<br>模型：${esc(gen.provider || "—")} / ${esc(gen.model || "—")}<br>时间：${esc((gen.generated_at || "").replace("T", " ").slice(0, 16))}<br>资料覆盖：${(gen.doc_stats || []).length} 份 / ${(gen.total_chars || 0).toLocaleString()} 字</div>${(gen.warnings || []).length ? `<div class="warn-box" style="margin-top:9px"><b>提示</b><ul>${gen.warnings.slice(0, 5).map((w) => `<li>${esc(w)}</li>`).join("")}</ul></div>` : ""}</div>` : ""}
      </div>
    </div>`;
  }

  // ------------------------------------------------------------------
  // Upload & setup
  // ------------------------------------------------------------------
  function wireUploads(root) {
    $$(".dropzone", root).forEach((zone) => {
      const input = $("input[type=file]", zone);
      if (!input) return;
      zone.addEventListener("click", (e) => { if (e.target !== input) input.click(); });
      zone.addEventListener("dragover", (e) => { e.preventDefault(); zone.classList.add("dragover"); });
      zone.addEventListener("dragleave", () => zone.classList.remove("dragover"));
      zone.addEventListener("drop", (e) => {
        e.preventDefault(); zone.classList.remove("dragover");
        if (e.dataTransfer?.files?.length) uploadFiles(e.dataTransfer.files);
      });
      input.addEventListener("change", () => { if (input.files?.length) uploadFiles(input.files); input.value = ""; });
    });
  }

  async function uploadFiles(files) {
    if (S.uploadBusy) return;
    S.uploadBusy = true;
    const arr = Array.from(files);
    let ok = 0, fail = 0;
    for (let i = 0; i < arr.length; i++) {
      const f = arr[i];
      if (f.size > 80 * 1024 * 1024) { toast(`${f.name} 超过 80MB`, "error"); fail++; continue; }
      toast(`上传 ${i + 1}/${arr.length}：${f.name}`);
      try {
        const res = await fetch("/api/upload", {
          method: "POST",
          headers: { "X-Filename": encodeURIComponent(f.name), "X-Doc-Kind": "auto", "Content-Type": "application/octet-stream" },
          body: f
        });
        const data = await res.json();
        if (!res.ok || data.ok === false) throw new Error(data.error || "上传失败");
        ok++;
      } catch (err) { fail++; toast(`${f.name}：${err.message}`, "error"); }
    }
    S.uploadBusy = false;
    if (ok) toast(`已加入 ${ok} 份资料`, "success");
    if (fail) toast(`${fail} 份资料失败`, "error");
    await load();
  }

  async function saveSetup() {
    const body = {
      course: $("#setupCourse")?.value || S.data.project.course,
      exam_date: $("#setupDate")?.value || S.data.project.exam_date,
      days: Number($("#setupDays")?.value || 3),
      hours_per_day: Number($("#setupHours")?.value || 5)
    };
    const res = await api("/api/project", { method: "POST", body });
    S.data.project = { ...S.data.project, ...res.project, analysis: S.data.project.analysis };
  }

  async function saveProjectSettings() {
    try {
      const body = {
        course: $("#docCourse")?.value || S.data.project.course,
        exam_date: $("#docDate")?.value || S.data.project.exam_date,
        days: Number($("#docDays")?.value || 3),
        hours_per_day: Number($("#docHours")?.value || 5)
      };
      await api("/api/project", { method: "POST", body });
      await load();
      toast("考试设置已保存；计划会在重新生成时按新天数重排", "success");
    } catch (err) { toast(err.message, "error"); }
  }

  async function generatePack() {
    if (!S.data.project.docs?.length) { toast("先加入至少一份资料", "error"); return; }
    try {
      await saveSetup();
      const offline = !S.data.settings.has_key;
      if (offline && S.data.project.analysis?.generation?.mode === "curated") {
        toast("当前是真题精编版。离线重新生成会覆盖它且质量更低；要重做请先配置 API Key。", "error");
        openModal("settings");
        return;
      }
      if (offline && !window.confirm("还没有配置模型。现在会生成“离线框架”（结构完整，但讲解和题目质量有限）。继续吗？")) return;
      const res = await api("/api/analyze", { method: "POST", body: { force_offline: offline, allow_fallback: true } });
      S.data.project.job = res.job;
      S.data.project.status = "analyzing";
      render();
      toast("已开始生成，通常需要 2–6 分钟");
      startJobPolling();
    } catch (err) { toast(err.message, "error"); }
  }

  function startJobPolling() {
    if (S.jobTimer) clearInterval(S.jobTimer);
    const poll = async () => {
      try {
        const res = await api("/api/job");
        const job = res.job || {};
        S.data.project.job = job;
        renderChrome();
        const box = $("#genProgress");
        if (box) {
          box.querySelector(".gen-progress-head span").innerHTML = `<span class="spinner"></span> ${esc(job.message || "正在生成…")}`;
          box.querySelector(".gen-progress-head b").textContent = `${Math.round(job.progress || 0)}%`;
          box.querySelector(".bar > span").style.width = `${clamp(job.progress || 0, 0, 100)}%`;
        }
        if (job.status === "done") {
          clearInterval(S.jobTimer); S.jobTimer = null;
          await load();
          S.view = "dashboard"; render();
          toast("冲刺包已生成", "success");
        } else if (job.status === "error") {
          clearInterval(S.jobTimer); S.jobTimer = null;
          await load();
          toast(job.error || "生成失败", "error");
        }
      } catch (_) { /* transient */ }
    };
    poll();
    S.jobTimer = setInterval(poll, 1300);
  }

  async function importInbox() {
    try {
      const res = await api("/api/import-inbox", { method: "POST", body: {} });
      const n = res.added?.length || 0;
      toast(n ? `扫描到 ${n} 份新资料` : "没有发现新资料（可能已导入）", n ? "success" : "");
      if (res.errors?.length) toast(`${res.errors.length} 个文件读取失败`, "error");
      await load();
    } catch (err) { toast(err.message, "error"); }
  }

  async function deleteDoc(id) {
    if (!window.confirm("从资料箱移除这份资料？不会删除原文件。")) return;
    try { await api("/api/delete-doc", { method: "POST", body: { doc_id: id } }); await load(); toast("已移除", "success"); }
    catch (err) { toast(err.message, "error"); }
  }

  async function changeDocKind(id, kind) {
    try { await api("/api/doc-kind", { method: "POST", body: { doc_id: id, kind } }); await load(); toast("资料类型已更新", "success"); }
    catch (err) { toast(err.message, "error"); }
  }

  // ------------------------------------------------------------------
  // Modal / settings / export
  // ------------------------------------------------------------------
  function openModal(kind) { S.modal = kind; renderModal(); }
  function closeModal() { S.modal = null; renderModal(); }

  function renderModal() {
    const root = $("#modalRoot");
    if (!S.modal) { root.innerHTML = ""; return; }
    let body = "";
    if (S.modal === "settings") body = settingsModal();
    else if (S.modal === "courses") body = coursesModal();
    else if (S.modal === "export") body = exportModal();
    root.innerHTML = `<div class="modal-scrim" data-action="close-modal"><div class="modal" role="dialog" aria-modal="true" onclick="event.stopPropagation()">${body}</div></div>`;
    hydrateIcons(root);
  }

  function settingsModal() {
    const s = S.data.settings;
    return `<div class="modal-head"><div><div class="eyebrow">CONFIG</div><h2>模型与设置</h2><p>推荐 DeepSeek / 任意 OpenAI 兼容接口。Key 只保存在本机 data/settings.json。</p></div><button class="icon-btn" data-action="close-modal">${icon("x")}</button></div>
    <div class="modal-body">
      <div class="field"><label>API Base URL</label><input id="setBase" value="${esc(s.base_url)}" placeholder="https://api.deepseek.com/v1"></div>
      <div class="field"><label>模型名称</label><input id="setModel" value="${esc(s.model)}" placeholder="deepseek-chat"></div>
      <div class="field"><label>API Key ${s.has_key ? `<span class="badge badge-green">已配置 ${esc(s.key_hint)}</span>` : ""}</label><div class="key-row"><input id="setKey" type="password" autocomplete="off" placeholder="${s.has_key ? "留空则不修改" : "sk-..."}"><button class="btn btn-sm" data-action="test-settings">测试</button></div><div class="input-hint">DeepSeek 默认：Base URL https://api.deepseek.com/v1，模型 deepseek-chat。Ollama 可用 http://127.0.0.1:11434/v1。</div></div>
      <div class="info-box" id="testResult">调用模型时会发送：课程名、你上传的资料片段、生成提示。不会发送其他本地文件。</div>
      <div class="modal-section"><h3>危险操作</h3><div class="danger-row"><span>清空分析结果，保留资料与 API 设置</span><button class="btn btn-sm btn-danger" data-action="reset-analysis">清空分析</button></div><div class="danger-row"><span>清空所有卡片、刷题和模考进度</span><button class="btn btn-sm btn-danger" data-action="reset-progress">清空进度</button></div></div>
    </div>
    <div class="modal-foot"><button class="btn" data-action="close-modal">取消</button><button class="btn btn-accent" data-action="save-settings">${icon("check")} 保存设置</button></div>`;
  }

  function coursesModal() {
    const courses = S.data.courses || [];
    const active = S.data.active_course_id;
    return `<div class="modal-head"><div><div class="eyebrow">COURSE LIBRARY</div><h2>课程库</h2><p>每门课独立保存 PPT/作业/真题、分析结果和学习进度。</p></div><button class="icon-btn" data-action="close-modal">${icon("x")}</button></div>
    <div class="modal-body">
      <div class="course-list">${courses.map((c) => `<div class="course-row ${c.active ? "active" : ""}"><div class="course-dot">${c.active ? "●" : "○"}</div><div><b>${esc(c.name)}</b><span>${c.docs || 0} 份资料 · ${c.has_analysis ? "已生成冲刺包" : "待生成"}${c.active ? " · 当前" : ""}</span></div><button class="btn btn-sm ${c.active ? "btn-ghost" : "btn-accent"}" data-course-switch="${esc(c.id)}" ${c.active ? "disabled" : ""}>${c.active ? "当前" : "进入"}</button></div>`).join("") || `<div class="empty-mini">还没有课程</div>`}</div>
      <div class="modal-section"><h3>新建课程</h3><p class="setting-note">建好后进入课程，上传 PPT/作业/真题，再点“生成冲刺包”。没有真题也能生成，但会标记为低置信度。</p><div class="key-row"><input id="newCourseName" placeholder="例如：宏观经济学 / 数据结构"><button class="btn btn-accent" data-action="create-course">${icon("plus")} 新建</button></div></div>
      <div class="info-box">当前是单用户课程库：同一时间只打开一门课；API Key 是全局设置，所有课程共用。</div>
    </div>`;
  }

  async function switchCourse(id) {
    try {
      await api("/api/courses/switch", { method: "POST", body: { id } });
      closeModal();
      S.view = "dashboard";
      S.initialViewDone = true;
      await load();
      toast("已切换课程", "success");
    } catch (err) { toast(err.message, "error"); }
  }

  async function createCourse() {
    const name = $("#newCourseName")?.value?.trim();
    if (!name) { toast("先输入课程名称", "error"); return; }
    try {
      await api("/api/courses/create", { method: "POST", body: { name } });
      closeModal();
      S.view = "dashboard";
      S.initialViewDone = true;
      await load();
      toast("课程已创建，先上传资料", "success");
    } catch (err) { toast(err.message, "error"); }
  }

  function exportModal() {
    return `<div class="modal-head"><div><div class="eyebrow">EXPORT</div><h2>导出与打印</h2><p>导出的是纯 Markdown，可打印或导入笔记软件。</p></div><button class="icon-btn" data-action="close-modal">${icon("x")}</button></div>
    <div class="modal-body">
      <div class="export-option"><div class="eicon">${icon("filetext")}</div><div><b>完整冲刺包</b><span>考点、速学卡、计划、仿真卷与答案</span></div><button class="btn btn-sm btn-accent" data-export="md">下载 .md</button></div>
      <div class="export-option"><div class="eicon">${icon("layers")}</div><div><b>考前一张纸</b><span>只保留高频考点、公式和易错点</span></div><button class="btn btn-sm" data-export="sheet">下载 .md</button></div>
      <div class="export-option"><div class="eicon">${icon("file")}</div><div><b>浏览器打印 / 存 PDF</b><span>用系统打印对话框选择“另存为 PDF”</span></div><button class="btn btn-sm" data-action="print-page">打印</button></div>
      <div class="info-box">导出前建议先记录模考成绩；导出内容来自当前冲刺包。</div>
    </div>`;
  }

  async function saveSettings() {
    const body = { base_url: $("#setBase")?.value || "", model: $("#setModel")?.value || "", api_key: $("#setKey")?.value || "" };
    try {
      const res = await api("/api/settings", { method: "POST", body });
      S.data.settings = res.settings;
      closeModal();
      toast("设置已保存", "success");
      renderChrome();
    } catch (err) { toast(err.message, "error"); }
  }

  async function testSettings() {
    const box = $("#testResult");
    if (box) { box.className = "info-box"; box.innerHTML = `<span class="spinner"></span> 正在测试模型连接…`; }
    try {
      const body = { base_url: $("#setBase")?.value || "", model: $("#setModel")?.value || "", api_key: $("#setKey")?.value || "" };
      const res = await api("/api/settings/test", { method: "POST", body });
      if (box) { box.className = "info-box"; box.innerHTML = `连接成功：${esc(res.model || "")} · ${esc(res.reply || "pong")}`; }
      toast("模型连接成功", "success");
    } catch (err) {
      if (box) { box.className = "error-box"; box.textContent = err.message; }
      toast(err.message, "error");
    }
  }

  async function resetScope(scope) {
    const label = scope === "progress" ? "所有学习进度" : "当前分析结果";
    if (!window.confirm(`确定清空${label}？此操作不可撤销。`)) return;
    try { await api("/api/reset", { method: "POST", body: { scope } }); closeModal(); await load(); toast("已清空", "success"); }
    catch (err) { toast(err.message, "error"); }
  }

  // ------------------------------------------------------------------
  // Ask coach
  // ------------------------------------------------------------------
  function openAsk() {
    $("#askDrawer").classList.add("open");
    $("#askDrawer").setAttribute("aria-hidden", "false");
    $("#drawerScrim").classList.add("open");
    renderAskMessages();
    setTimeout(() => $("#askInput")?.focus(), 280);
  }
  function closeAsk() {
    $("#askDrawer").classList.remove("open");
    $("#askDrawer").setAttribute("aria-hidden", "true");
    $("#drawerScrim").classList.remove("open");
  }

  function renderAskMessages() {
    const box = $("#askMessages");
    if (!box) return;
    if (!S.askHistory.length) {
      box.innerHTML = `<div class="ask-empty">${icon("spark")}<div style="margin-top:9px">问一个具体问题，比如：<br>“这个公式在什么条件下不能用？”<br>“用一句话区分这两个概念。”</div><div style="display:flex;flex-wrap:wrap;gap:5px;justify-content:center;margin-top:12px"><button class="badge badge-muted" data-ask-suggestion="这门课最可能考什么？">最可能考什么</button><button class="badge badge-muted" data-ask-suggestion="用一道最小例子解释最难的考点">举个最小例子</button></div></div>`;
      hydrateIcons(box);
      return;
    }
    box.innerHTML = S.askHistory.map((m) => `<div class="ask-msg ${m.role === "user" ? "user" : "bot"}">${rich(m.text)}${(m.sources || []).length ? `<div class="src-list">${m.sources.map((s) => `<span class="src">${esc(s.name)} · ${esc(s.locator)}</span>`).join("")}</div>` : ""}</div>`).join("");
    box.scrollTop = box.scrollHeight;
  }

  async function askQuestion(text) {
    const q = String(text || "").trim();
    if (!q) return;
    S.askHistory.push({ role: "user", text: q });
    renderAskMessages();
    $("#askInput").value = "";
    $("#askSend").disabled = true;
    S.askHistory.push({ role: "bot", text: "正在翻你的资料…" });
    renderAskMessages();
    try {
      const res = await api("/api/ask", { method: "POST", body: { question: q } });
      S.askHistory[S.askHistory.length - 1] = { role: "bot", text: res.answer, sources: res.sources || [] };
      renderAskMessages();
    } catch (err) {
      S.askHistory[S.askHistory.length - 1] = { role: "bot", text: `调用失败：${err.message}` };
      renderAskMessages();
    } finally { $("#askSend").disabled = false; }
  }

  // ------------------------------------------------------------------
  // Events
  // ------------------------------------------------------------------
  document.addEventListener("click", async (e) => {
    const nav = e.target.closest("[data-nav]");
    if (nav) {
      const view = nav.dataset.nav;
      S.view = view;
      if (view !== "practice") { /* keep practice state when navigating back */ }
      if (view === "study" && S.studyTab === "flashcards") rebuildCardOrder();
      document.body.classList.remove("nav-open");
      render();
      window.scrollTo({ top: 0, behavior: "smooth" });
      return;
    }
    const courseSwitch = e.target.closest("[data-course-switch]");
    if (courseSwitch) {
      if (!courseSwitch.disabled) switchCourse(courseSwitch.dataset.courseSwitch);
      return;
    }
    const actionEl = e.target.closest("[data-action]");
    if (actionEl) {
      const action = actionEl.dataset.action;
      if (action === "open-settings") openModal("settings");
      else if (action === "open-courses") openModal("courses");
      else if (action === "open-export") openModal("export");
      else if (action === "close-modal") closeModal();
      else if (action === "open-ask") openAsk();
      else if (action === "close-ask") closeAsk();
      else if (action === "save-settings") saveSettings();
      else if (action === "create-course") createCourse();
      else if (action === "test-settings") testSettings();
      else if (action === "reset-analysis") resetScope("analysis");
      else if (action === "reset-progress") resetScope("progress");
      else if (action === "generate") generatePack();
      else if (action === "save-project-settings") saveProjectSettings();
      else if (action === "import-inbox") importInbox();
      else if (action === "reveal-card") { S.cardRevealed = true; render(); }
      else if (action === "submit-practice") submitPractice();
      else if (action === "next-practice") nextPractice();
      else if (action === "exit-practice") { S.practice = null; S.view = "practice"; render(); }
      else if (action === "restart-practice") { S.practice = null; render(); }
      else if (action === "start-today") { S.view = "study"; S.studyTab = "flashcards"; rebuildCardOrder(); render(); }
      else if (action === "start-zero") { document.getElementById("zeroTools")?.scrollIntoView({ behavior: "smooth", block: "start" }); }
      else if (action === "scroll-zero-diag") { document.getElementById("zeroDiag")?.scrollIntoView({ behavior: "smooth", block: "start" }); }
      else if (action === "quick-practice") startPractice("10");
      else if (action === "start-mock") startMock();
      else if (action === "submit-mock") submitMock(false);
      else if (action === "save-mock") saveMock();
      else if (action === "restart-mock") { S.mock = null; render(); }
      else if (action === "print-page") window.print();
      else if (action === "toggle-nav") document.body.classList.toggle("nav-open");
      else if (action === "close-nav") document.body.classList.remove("nav-open");
      else if (action === "ignore") {}
      return;
    }
    const planBtn = e.target.closest("[data-plan-id]");
    if (planBtn) {
      const id = planBtn.dataset.planId;
      const current = !!progress().plan?.[id];
      try {
        const res = await api("/api/progress", { method: "POST", body: { type: "plan", block_id: id, done: !current } });
        progress().plan[id] = !current;
        S.data.insights = res.insights;
        render();
      } catch (err) { toast(err.message, "error"); }
      return;
    }
    const topicToggle = e.target.closest("[data-topic-toggle]");
    if (topicToggle) {
      const id = topicToggle.dataset.topicToggle;
      if (S.openTopics.has(id)) S.openTopics.delete(id); else S.openTopics.add(id);
      const card = topicToggle.closest(".topic-card");
      card?.classList.toggle("open");
      return;
    }
    const sort = e.target.closest("[data-map-sort]");
    if (sort) { S.mapSort = sort.dataset.mapSort; render(); return; }
    const studyTab = e.target.closest("[data-study-tab]");
    if (studyTab) { S.studyTab = studyTab.dataset.studyTab; if (S.studyTab === "flashcards") rebuildCardOrder(); render(); return; }
    const studyTopic = e.target.closest("[data-study-topic]");
    if (studyTopic) { S.selectedTopic = studyTopic.dataset.studyTopic; S.studyTab = "guide"; render(); return; }
    const topicStudy = e.target.closest("[data-topic-study]");
    if (topicStudy) { S.selectedTopic = topicStudy.dataset.topicStudy; S.studyTab = "guide"; S.view = "study"; render(); return; }
    const topicPractice = e.target.closest("[data-topic-practice]");
    if (topicPractice) { startPractice("all", topicPractice.dataset.topicPractice); return; }
    const flashTopic = e.target.closest("[data-study-flash-topic]");
    if (flashTopic) {
      S.studyTab = "flashcards"; S.cardDueOnly = false;
      const cards = (analysis()?.cards || []).filter((c) => c.topic_id === flashTopic.dataset.studyFlashTopic);
      S.cardOrder = cards.map((c) => c.id); S.cardIndex = 0; S.cardRevealed = false;
      render(); return;
    }
    const filter = e.target.closest("[data-card-filter]");
    if (filter) { S.cardDueOnly = filter.dataset.cardFilter === "due"; S.cardIndex = 0; rebuildCardOrder(); render(); return; }
    const rate = e.target.closest("[data-card-rate]");
    if (rate) { S.cardRevealed = true; rateCard(rate.dataset.cardRate); return; }
    const opt = e.target.closest("[data-practice-option]");
    if (opt) {
      if (!S.practice || S.practice.submitted) return;
      const q = S.practice.questions[S.practice.index];
      const val = opt.dataset.practiceOption;
      if (q.type === "multiple") {
        const cur = new Set(S.practice.selected || []);
        if (cur.has(val)) cur.delete(val); else cur.add(val);
        S.practice.selected = [...cur];
      } else S.practice.selected = [val];
      render(); return;
    }
    const self = e.target.closest("[data-self-grade]");
    if (self) { selfGradePractice(self.dataset.selfGrade === "1"); return; }
    const start = e.target.closest("[data-start-practice]");
    if (start) { startPractice(start.dataset.startPractice); return; }
    const errRedo = e.target.closest("[data-error-redo]");
    if (errRedo) {
      const q = allQuestions().find((x) => x.id === errRedo.dataset.errorRedo);
      if (q) { S.practice = { questions: [q], index: 0, selected: [], openAnswer: "", submitted: false, result: null, recorded: false, correct: 0, answered: 0, answerDisplay: "" }; S.view = "practice"; render(); }
      return;
    }
    const del = e.target.closest("[data-delete-doc]");
    if (del) { deleteDoc(del.dataset.deleteDoc); return; }
    const exportBtn = e.target.closest("[data-export]");
    if (exportBtn) { window.location.href = `/api/export?format=${encodeURIComponent(exportBtn.dataset.export)}`; return; }
    const mockOpt = e.target.closest("[data-mock-opt]");
    if (mockOpt) {
      const qid = mockOpt.dataset.qid, val = mockOpt.dataset.mockOpt, type = mockOpt.dataset.qtype;
      if (!S.mock) return;
      if (type === "multiple") {
        const cur = new Set(S.mock.answers[qid] || []);
        if (cur.has(val)) cur.delete(val); else cur.add(val);
        S.mock.answers[qid] = [...cur];
      } else S.mock.answers[qid] = val;
      $$(`[data-qid="${qid}"]`).forEach((b) => b.classList.toggle("selected", type === "multiple" ? (S.mock.answers[qid] || []).includes(b.dataset.mockOpt) : b.dataset.mockOpt === val));
      updateMockAnswered();
      return;
    }
    const sug = e.target.closest("[data-ask-suggestion]");
    if (sug) { askQuestion(sug.dataset.askSuggestion); return; }
    const zeroTool = e.target.closest("[data-zero-tool-open]");
    if (zeroTool) {
      const el = document.getElementById(`tool-${zeroTool.dataset.zeroToolOpen}`);
      if (el) { el.open = true; el.scrollIntoView({ behavior: "smooth", block: "center" }); }
      return;
    }
  });

  document.addEventListener("change", (e) => {
    const kind = e.target.closest("[data-doc-kind]");
    if (kind) { changeDocKind(kind.dataset.docKind, kind.value); return; }
    const score = e.target.closest("[data-mock-score]");
    if (score && S.mock) {
      const qid = score.dataset.mockScore;
      S.mock.selfScores = S.mock.selfScores || {};
      S.mock.selfScores[qid] = Math.max(0, Number(score.value) || 0);
      // Re-render only the result header total is enough to keep inputs responsive.
      const possible = S.mock.result?.totalPossible || 1;
      const items = S.mock.result?.items || [];
      const pts = items.filter((x) => !x.isOpen).reduce((n, x) => n + x.points, 0) + items.filter((x) => x.isOpen).reduce((n, x) => n + Number(S.mock.selfScores?.[x.q.id] || 0), 0);
      const head = $(".big-score");
      if (head) head.innerHTML = `${Math.round((pts / possible) * 100)}<small style="font-size:20px;color:var(--muted)">%</small>`;
    }
  });

  document.addEventListener("input", (e) => {
    const ta = e.target.closest("[data-mock-text]");
    if (ta && S.mock) { S.mock.answers[ta.dataset.mockText] = ta.value; updateMockAnswered(); }
    if (e.target.id === "practiceAnswer" && S.practice) S.practice.openAnswer = e.target.value;
  });

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") { if (S.modal) closeModal(); if ($("#askDrawer").classList.contains("open")) closeAsk(); }
    if (S.modal || $("#askDrawer").classList.contains("open")) return;
    if (S.view === "study" && S.studyTab === "flashcards") {
      if (e.code === "Space" && !S.cardRevealed) { e.preventDefault(); S.cardRevealed = true; render(); }
      else if (S.cardRevealed && ["1", "2", "3", "4"].includes(e.key)) {
        e.preventDefault(); const map = { "1": "again", "2": "hard", "3": "good", "4": "easy" }; rateCard(map[e.key]);
      }
    }
  });

  $("#askForm").addEventListener("submit", (e) => { e.preventDefault(); askQuestion($("#askInput").value); });
  $("#askInput").addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); askQuestion($("#askInput").value); }
  });

  // Start
  $("#viewRoot").innerHTML = loadingView();
  hydrateIcons();
  load();
})();
