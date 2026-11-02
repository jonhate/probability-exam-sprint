"""Deterministic, evidence-based task selection. No model calls or score predictions."""
from datetime import datetime, timedelta
import math
import re
from .store import TZ

ERRORS = {'concept', 'conditions', 'procedure', 'calculation', 'reading', 'time', 'unknown'}
LABELS = {'unseen': '待诊断', 'support': '需要辅助', 'independent': '独立完成过',
          'transfer': '不同题目通过', 'retained': '间隔复测通过'}

def checkpoints(q):
    """Use supplied scoring points, never invent a skill taxonomy from a question title."""
    return [s.strip() for s in re.split(r'[；;\n]+', str(q.get('rubric') or '')) if s.strip()][:12]

def number(value, default=0):
    try:
        value = float(value)
        return value if math.isfinite(value) else default
    except (TypeError, ValueError):
        return default

def timestamp(value):
    try:
        dt = datetime.fromisoformat(value)
        return dt.replace(tzinfo=TZ) if dt.tzinfo is None else dt.astimezone(TZ)
    except (ValueError, TypeError):
        return None

def minutes(q):
    return max(1, min(30, round(number(q.get('estimated_minutes'),
        3 if q.get('type') in ('single', 'multiple', 'judge') else 10))))

def evidence(attempt):
    # Old records did not capture assistance; do not reinterpret them as independent.
    return (attempt.get('correct') is True and attempt.get('assisted') is False
            and attempt.get('evidence_version') == 1 and not attempt.get('partial'))

def build_learning(project, progress, now=None):
    now = now or datetime.now(TZ)
    a = project.get('analysis') or {}
    qs = a.get('questions') or []
    topics = a.get('topics') or []
    history = progress.get('questions') or {}
    session = max(5, min(60, int(number(progress.get('preferences', {}).get('session_minutes'), 15))))
    daily = max(30, min(960, round(number(project.get('hours_per_day'), 5) * 60)))
    spent = sum(min(7200, max(0, number(x.get('elapsed_seconds')))) / 60
                for q in qs for x in history.get(q['id'], {}).get('attempts', [])
                if timestamp(x.get('at')) and timestamp(x['at']).date() == now.date())
    remaining = max(0, int(daily - spent))
    started = timestamp(progress.get('preferences', {}).get('session_started_at'))
    session_spent = sum(min(7200, max(0, number(x.get('elapsed_seconds')))) / 60
                        for q in qs for x in history.get(q['id'], {}).get('attempts', [])
                        if timestamp(x.get('at')) and timestamp(x['at']).date() == now.date()
                        and (not started or timestamp(x['at']) >= started))
    session_remaining = max(0, int(session - session_spent))
    try:
        exam = datetime.strptime(project.get('exam_date', ''), '%Y-%m-%d').date()
        days = (exam - now.date()).days
    except (ValueError, TypeError):
        days = None
    budget = min(session_remaining, remaining)
    rows, candidates, waiting = [], [], []
    for topic in topics:
        pool = [q for q in qs if q.get('topic_id') == topic['id']]
        records = [(q, x) for q in pool for x in history.get(q['id'], {}).get('attempts', [])]
        latest = sorted(records, key=lambda item: timestamp(item[1].get('at')) or datetime.min.replace(tzinfo=TZ))
        successes = [(q, x) for q, x in latest if evidence(x)]
        distinct = {q['id'] for q, _ in successes}
        retained = any(timestamp(x.get('at')) and timestamp(y.get('at'))
                       and timestamp(y['at']) - timestamp(x['at']) >= timedelta(minutes=30)
                       for _, x in successes for _, y in successes)
        state = 'unseen' if not records else 'support'
        if successes:
            state = 'retained' if retained else 'transfer' if len(distinct) >= 2 else 'independent'
        if latest and not evidence(latest[-1][1]):
            state = 'support'
        row = {'topic_id': topic['id'], 'name': topic.get('name'), 'state': state,
               'label': LABELS[state], 'independent_questions': len(distinct), 'question_count': len(pool)}
        rows.append(row)
        if not pool:
            continue
        unseen = [q for q in pool if not history.get(q['id'], {}).get('attempts')]
        last_q, last = latest[-1] if latest else (None, {})
        phase = 'diagnose'
        reason = '尚无作答证据，先用一道题定位起点。'
        q = min(unseen or pool, key=minutes)
        if state == 'support':
            phase, q = 'repair', last_q
            reason = '最近作答仍需辅助；先核对条件和步骤，再尝试完成。'
            if last.get('partial'):
                missing = [text for i, text in enumerate(checkpoints(q)) if i not in last.get('completed_steps', [])]
                if missing:
                    reason = '上次未完成的评分点：' + '；'.join(missing[:2])
            if last.get('assisted') and last.get('correct') and unseen:
                phase, q = 'transfer', min(unseen, key=minutes)
                reason = '已经在辅助下完成，换一道未练题检查能否独立完成。'
        elif state in ('independent', 'transfer', 'retained'):
            if unseen:
                phase, q = 'transfer', min(unseen, key=minutes)
                reason = '已有独立完成记录，用另一道题检查能否迁移。'
            else:
                phase, q = 'retest', min(pool, key=lambda v: history.get(v['id'], {}).get('attempts', [{}])[-1].get('at', ''))
                reason = '题库暂无未练题；这是旧题间隔复测，不能作为新题验证。'
        last_time = timestamp(last.get('at'))
        failures = [x for _, x in latest[-2:] if not x.get('correct')]
        delay = 30 if phase == 'retest' or len(failures) == 2 else 0
        if last_time and delay and now < last_time + timedelta(minutes=delay):
            waiting.append((last_time + timedelta(minutes=delay)).isoformat())
            continue
        duration = minutes(q)
        task = {'topic_id': topic['id'], 'question_id': q['id'], 'phase': phase,
                'title': f"{topic.get('name', '')} · " + {'diagnose': '起点诊断', 'repair': '补关键步骤', 'transfer': '换题检查', 'retest': '间隔复测'}[phase],
                'minutes': duration, 'reason': reason,
                'criterion': '在本块时间内完成作答并核对评分点；用了提示也如实记录。',
                'guide': (topic.get('guide') or {}).get('two_minute') or topic.get('summary') or '',
                'example': (topic.get('guide') or {}).get('worked_example') or '',
                'formula': topic.get('formula') or '',
                'error_type': last.get('error_type', 'unknown')}
        # Transparent heuristic: priority, current need and estimated time. Not expected marks.
        need = {'diagnose': 1.2, 'repair': 1.35, 'transfer': 1.1, 'retest': 0.8}[phase]
        score = (20 + max(0, min(100, number(topic.get('priority'))))) * need / math.sqrt(duration)
        candidates.append((score, task))
    candidates.sort(key=lambda x: -x[0])
    plan, allocated = [], 0
    for _, task in candidates:
        if allocated + task['minutes'] <= budget:
            plan.append(task)
            allocated += task['minutes']
        if len(plan) == 3:
            break
    status = 'ready'
    if days is not None and days < 0:
        status, plan = 'expired', []
    elif not qs:
        status, plan = 'no_questions', []
    elif remaining <= 0:
        status, plan = 'rest', []
    elif session_remaining <= 0:
        status, plan = 'session_done', []
    elif not plan:
        status = 'waiting' if not candidates and waiting else 'short_budget'
    return {'status': status, 'tasks': plan, 'topics': rows, 'session_minutes': session, 'session_remaining': session_remaining,
            'daily_remaining': remaining, 'tracked_minutes': round(spent), 'days_left': days,
            'next_review_at': min(waiting) if waiting else None,
            'independent_topics': sum(r['state'] in ('independent', 'transfer', 'retained') for r in rows),
            'note': '排序综合资料重点、作答证据和预计用时；不是提分预测。主观题按评分点自评。'}
