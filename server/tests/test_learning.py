import unittest
from datetime import datetime, timedelta
from engine.learning import build_learning, TZ

class LearningTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026,11,2,10,tzinfo=TZ)
        self.project = {'exam_date':'2026-11-04','hours_per_day':1,'analysis':{
            'topics':[{'id':'t1','name':'高频','priority':95},{'id':'t2','name':'低频','priority':20}],
            'questions':[{'id':'q1','topic_id':'t1','type':'single','rubric':'列条件；列式'},
                         {'id':'q2','topic_id':'t1','type':'single'},
                         {'id':'q3','topic_id':'t2','type':'calculation'}]}}
        self.progress = {'questions':{}}

    def record(self,q,correct=True,assisted=False,age=0,**kw):
        x={'at':(self.now-timedelta(minutes=age)).isoformat(),'correct':correct,
           'assisted':assisted,'evidence_version':1,'elapsed_seconds':60,**kw}
        self.progress['questions'].setdefault(q,{'attempts':[]})['attempts'].append(x)

    def plan(self): return build_learning(self.project,self.progress,self.now)

    def test_diagnosis_is_small_and_prioritized(self):
        p=self.plan()
        self.assertEqual(p['tasks'][0]['question_id'],'q1')
        self.assertEqual(p['tasks'][0]['phase'],'diagnose')
        self.assertLessEqual(sum(t['minutes'] for t in p['tasks']),15)

    def test_assistance_does_not_count_as_independence(self):
        self.record('q1',assisted=True)
        p=self.plan()
        self.assertEqual(p['topics'][0]['state'],'support')
        self.assertEqual(p['tasks'][0]['question_id'],'q2')

    def test_distinct_questions_and_delayed_evidence(self):
        self.record('q1',age=10); self.record('q2')
        self.assertEqual(self.plan()['topics'][0]['state'],'transfer')
        self.record('q1',age=-31)
        self.assertEqual(build_learning(self.project,self.progress,self.now+timedelta(minutes=31))['topics'][0]['state'],'retained')

    def test_legacy_success_is_not_independent(self):
        self.record('q1',evidence_version=0)
        self.assertEqual(self.plan()['topics'][0]['state'],'support')

    def test_partial_steps_drive_repair(self):
        self.record('q1',correct=False,partial=True,completed_steps=[0])
        task=self.plan()['tasks'][0]
        self.assertEqual(task['phase'],'repair')
        self.assertIn('列式',task['reason'])
        self.assertNotIn('列条件',task['reason'])

    def test_two_failures_pause_repetition(self):
        self.record('q1',False,age=1); self.record('q1',False)
        self.assertFalse(any(t['topic_id']=='t1' for t in self.plan()['tasks']))
        self.assertIsNotNone(self.plan()['next_review_at'])

    def test_expired_exam_has_no_tasks(self):
        self.project['exam_date']='2026-11-01'
        self.assertEqual(self.plan()['status'],'expired')
        self.assertEqual(self.plan()['tasks'],[])

    def test_daily_budget_exhaustion(self):
        self.record('q1',elapsed_seconds=3600)
        self.assertEqual(self.plan()['status'],'rest')

    def test_no_unaffordable_task(self):
        self.progress['preferences']={'session_minutes':5}
        self.assertTrue(all(t['minutes']<=5 for t in self.plan()['tasks']))

    def test_repeated_same_question_not_transfer(self):
        self.record('q1',age=1); self.record('q1')
        self.assertEqual(self.plan()['topics'][0]['state'],'independent')

    def test_session_budget_does_not_reset_after_each_answer(self):
        self.record('q1',elapsed_seconds=900)
        self.assertEqual(self.plan()['status'],'session_done')
        self.progress['preferences']={'session_minutes':15,'session_started_at':(self.now+timedelta(seconds=1)).isoformat()}
        p=build_learning(self.project,self.progress,self.now+timedelta(seconds=2))
        self.assertEqual(p['session_remaining'],15)
        self.assertEqual(p['daily_remaining'],45)

if __name__=='__main__': unittest.main()
