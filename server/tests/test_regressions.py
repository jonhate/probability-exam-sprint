"""Isolated integration tests: never modify the user's course data."""
from __future__ import annotations

import base64
import concurrent.futures
import http.client
import json
import shutil
import sys
import tempfile
import threading
import unittest
import urllib.parse
import uuid
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import app
from engine import offline, store
from engine.pipeline import Pipeline, _sanitize_mock


class RegressionTests(unittest.TestCase):
    def setUp(self):
        # A normal mkdir (not TemporaryDirectory's 0700 ACL) works under
        # restricted Windows runners as well as normal Windows/macOS/Linux.
        self.tmp = Path(tempfile.gettempdir()) / f"examsprint-test-{uuid.uuid4().hex}"
        self.tmp.mkdir(parents=True)
        root = self.tmp
        self.patches = []
        for name, value in {
            'DATA': root / 'data', 'COURSES': root / 'data/courses',
            'ACTIVE': root / 'data/active_course.json', 'COURSES_META': root / 'data/courses.json',
            'UPLOADS': root / 'uploads', 'EXPORTS': root / 'exports', 'INBOX': root / 'inbox',
        }.items():
            p = patch.object(store, name, value)
            p.start()
            self.patches.append(p)
        app._JOB_THREAD = None
        self.auth = patch.object(app, 'ACCESS_TOKEN', '')
        self.auth.start()
        store.ensure_dirs()
        self.cid = store.active_course_id()
        self.server = app.ExamSprintServer(('127.0.0.1', 0), app.Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        if app._JOB_THREAD:
            app._JOB_THREAD.join(5)
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(2)
        self.auth.stop()
        for p in reversed(self.patches):
            p.stop()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def request(self, path, body=None, headers=None, raw=None):
        conn = http.client.HTTPConnection(*self.server.server_address, timeout=5)
        try:
            data = raw if raw is not None else json.dumps(body).encode() if body is not None else None
            conn.request('POST' if body is not None or raw is not None else 'GET', path, data, headers or {})
            response = conn.getresponse()
            payload = response.read()
            return response.status, json.loads(payload) if payload else {}
        finally:
            conn.close()

    def pack(self):
        p = store.read('project')
        p['analysis'] = {'cards': [{'id': 'c001', 'front': 'old'}], 'questions': [{'id': 'q001'}], 'plan': []}
        store.write('project', p)
        return p

    def test_course_scope_survives_switch(self):
        with store.course_scope(self.cid):
            other = store.create_course('第二门课')
            p = store.read('project')
            self.assertEqual(p['course'], '我的课程')
            p['course'] = '写回第一门'
            store.write('project', p)
        self.assertEqual(store.read('project')['course'], '第二门课')
        store.switch_course(self.cid)
        self.assertEqual(store.read('project')['course'], '写回第一门')
        self.assertNotEqual(other['id'], self.cid)

    def test_lost_pointer_does_not_overwrite_existing_course(self):
        self.pack()
        store.write('progress', {'cards': {'c001': {'seen': 8}}})
        store._write_json_file(store.DATA / 'project.json', {'course': 'obsolete'})
        store.ACTIVE.unlink()
        self.assertEqual(store.active_course_id(), self.cid)
        self.assertEqual(store.read('progress')['cards']['c001']['seen'], 8)

    def test_corrupt_json_is_not_silently_reset(self):
        (store.COURSES / self.cid / 'progress.json').write_text('{broken', encoding='utf-8')
        with self.assertRaises(ValueError):
            store.read('progress')

    def test_invalid_course_path(self):
        for cid in ['../escape', 'C:\\escape', '..', 'x/y']:
            with self.assertRaises(ValueError):
                store.switch_course(cid)

    def test_public_bind_requires_credentials(self):
        with patch.object(sys, 'argv', ['app.py', '--host', '0.0.0.0', '--no-browser']):
            with self.assertRaises(SystemExit) as raised:
                app.main()
        self.assertEqual(raised.exception.code, 2)

    def test_latest_answer_drives_weakness(self):
        p = self.pack()
        progress = {'questions': {'q001': {'attempts': [{'correct': True}] * 20 + [{'correct': False}]}}}
        self.assertEqual(app._build_insights(p, progress)['accuracy'], 0)

    def test_curated_single_choice_has_one_mathematically_true_option(self):
        from tools.seed_content import PRACTICE_RAW
        q = PRACTICE_RAW[0]
        self.assertEqual(q['answer'], 'B')
        self.assertEqual(q['options'][2], 'C. P(A∪B)=P(A)')
        # For arbitrary positive disjoint probabilities, B holds and A/C/D fail.
        for pa, pb in [(0.2, 0.3), (0.4, 0.6), (0.01, 0.02)]:
            truth = [0 == pa * pb, pa - 0 == pa, pa + pb == pa, 0 == pa * pb]
            self.assertEqual(truth, [False, True, False, False])

    def test_concurrent_course_creation_keeps_index(self):
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            rows = list(pool.map(lambda _: store.create_course('重复名称'), range(12)))
        self.assertEqual(len({r['id'] for r in rows}), 12)
        self.assertEqual(len(store.list_courses()), 13)

    def test_auth_health_and_sensitive_routes(self):
        app.ACCESS_TOKEN = 'test-secret'
        self.assertEqual(self.request('/api/health')[0], 200)
        for path in ['/api/state', '/api/export', '/static/app.js']:
            self.assertEqual(self.request(path)[0], 401)
        self.assertEqual(self.request('/api/reset', {})[0], 401)
        auth = 'Basic ' + base64.b64encode(b'user:test-secret').decode()
        status, result = self.request('/api/state', headers={'Authorization': auth})
        self.assertEqual(status, 200)
        self.assertNotIn('api_key', result['settings'])

    def test_origin_and_stale_tab_guards(self):
        self.assertEqual(self.request('/api/state', headers={'Host': 'untrusted.example'})[0], 403)
        self.assertEqual(self.request('/api/reset', {}, {'Origin': 'https://evil.invalid'})[0], 403)
        self.assertEqual(self.request('/api/reset', {}, {'Sec-Fetch-Site': 'cross-site'})[0], 403)
        self.pack()
        self.assertEqual(self.request('/api/progress', {'type': 'card', 'id': 'c001'}, {'X-Analysis-Revision': 'obsolete'})[0], 409)
        other = store.create_course('新课程')
        self.assertEqual(self.request('/api/project', {'course': 'wrong'}, {'X-Course-ID': self.cid})[0], 409)
        self.assertEqual(store.read('project')['course'], '新课程')
        encoded = urllib.parse.quote(other['id'])
        self.assertEqual(self.request('/api/project', {'course': '正确课程'}, {'X-Course-ID': encoded})[0], 200)

    def test_unknown_progress_ids_rejected(self):
        self.pack()
        for body in [{'type': 'question', 'id': 'missing'}, {'type': 'plan', 'id': 'missing'}, {'type': 'card', 'id': 'missing'}]:
            self.assertEqual(self.request('/api/progress', body)[0], 404)

    def test_concurrent_progress_keeps_all_updates(self):
        self.pack()
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            rows = list(pool.map(lambda _: self.request('/api/progress', {'type': 'card', 'id': 'c001', 'rating': 'good'}), range(20)))
        self.assertTrue(all(status == 200 for status, _ in rows))
        self.assertEqual(store.read('progress')['cards']['c001']['seen'], 20)

    def test_upload_keeps_original_filename(self):
        def parse(path, name, kind, doc_id):
            return {'doc_id': doc_id, 'name': name, 'kind': kind, 'pages': [], 'chars': 20}
        with patch.object(app, 'parse_file', parse):
            status, result = self.request('/api/upload', headers={'X-Filename': urllib.parse.quote('期中真题.txt')}, raw='样本文本'.encode())
        self.assertEqual(status, 200)
        self.assertEqual(result['doc']['name'], '期中真题.txt')
        self.assertEqual(result['doc']['kind'], 'exam')

    def test_analysis_archive_and_job_guards(self):
        old = self.pack()
        old['docs'] = [{'doc_id': 'd1', 'name': 'slides', 'kind': 'slides'}]
        store.write('project', old)
        store.write('corpus', {'docs': [{'doc_id': 'd1', 'pages': []}]})
        store.write('progress', {'cards': {'c001': {'seen': 9}}})
        entered, release = threading.Event(), threading.Event()
        def run(_pipeline):
            entered.set()
            release.wait(4)
            return {'cards': [{'id': 'c001', 'front': 'new'}], 'generation': {}}
        with patch.object(app.Pipeline, 'run', run):
            self.assertEqual(self.request('/api/analyze', {'force_offline': True})[0], 202)
            self.assertTrue(entered.wait(2))
            try:
                for path in ['/api/reset', '/api/project', '/api/doc-kind', '/api/delete-doc', '/api/courses/switch']:
                    self.assertEqual(self.request(path, {})[0], 409)
                self.assertEqual(self.request('/api/analyze', {})[0], 409)
            finally:
                release.set()
            app._JOB_THREAD.join(4)
        self.assertFalse(app._JOB_THREAD.is_alive())
        self.assertEqual(store.read('project')['job']['status'], 'done')
        self.assertEqual(store.read('progress')['cards'], {})
        history = list((store.COURSES / self.cid / 'history').glob('*.json'))
        self.assertEqual(len(history), 1)
        archived = json.loads(history[0].read_text(encoding='utf-8'))
        self.assertEqual(archived['progress']['cards']['c001']['seen'], 9)
        self.assertEqual(archived['analysis']['cards'][0]['front'], 'old')

    def test_learning_budget_and_single_day_targets(self):
        for hours in [0.5, 1, 5, 16]:
            for days in [1, 3, 14]:
                plan = offline.build_plan([{'id': 't01'}], days, hours)
                self.assertTrue(all(sum(b['minutes'] for b in d['blocks']) == hours * 60 for d in plan))
                self.assertTrue(all(b['minutes'] > 0 for d in plan for b in d['blocks']))
                self.assertTrue(any('t01' in b['topic_ids'] for d in plan for b in d['blocks']))
        last_day = offline.build_plan([{'id': 't01'}], 3, 0.5)[-1]
        self.assertTrue(any('限时诊断' in b['activity'] for b in last_day['blocks']))

    def test_model_paper_scores_are_normalized(self):
        raw = {'total_score': 100, 'sections': [
            {'score': score, 'questions': [{'stem': '定义是什么？', 'answer': '定义', 'type': 'short'}] * 3}
            for score in [24, 30, 36, 28]
        ]}
        mock = _sanitize_mock(raw, [{'id': 't1', 'name': '定义'}])
        self.assertAlmostEqual(sum(s['score'] for s in mock['sections']), 100)
        self.assertAlmostEqual(sum(q['score'] for s in mock['sections'] for q in s['questions']), 100)

    def test_no_exam_weights_are_explicit_and_missing_not_imputed(self):
        docs = [{'kind': k, 'pages': [{'text': '条件概率'}] * 3} for k in ['slides', 'homework']]
        candidates = [{'name': '条件概率'}, {'name': '完全缺失'}]
        ranked = offline.rank_candidates(docs, candidates, 2)
        self.assertEqual(ranked[0]['_priority'], 80)
        self.assertEqual(ranked[1]['_priority'], 0)
        self.assertIn('低置信度', ranked[0]['_why'])

    def test_full_offline_pipeline_without_exam(self):
        docs = [{'doc_id': 'd1', 'kind': 'slides', 'name': '课程讲义', 'pages': [
            {'locator': f'第{i}页', 'title': f'概念{i}', 'text': f'概念{i}定义：这是一个用于考试的充分条件。注意需要检查适用范围与符号。'} for i in range(1, 5)
        ]}]
        a = Pipeline({'course': '示例课', 'days': 1, 'hours_per_day': 0.5}, docs, {}, force_offline=True).run()
        self.assertTrue(a['topics'] and a['cards'] and a['questions'])
        self.assertEqual(a['plan'][0]['total_minutes'], 30)
        self.assertEqual(a['exam_profile']['confidence'], '低')
        self.assertAlmostEqual(sum(q['score'] for s in a['mock']['sections'] for q in s['questions']), 100)


if __name__ == '__main__':
    unittest.main(verbosity=2)
