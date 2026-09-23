"""Unit and invariant checks on mathematical fixtures, never model benchmarks."""
import hashlib
import json
import math
from pathlib import Path
import platform
import re
import subprocess
import sys
import unittest
from validation_primitives import (BoxRecord, admit_frame, group_partition,
                                   iou, match_detections, rates, split_manifest)

B = BoxRecord
A = (0, 0, 2, 2)
ROOT = Path(__file__).resolve().parents[2]

class ValidationChecks(unittest.TestCase):
    def test_iou_identical(self):
        self.assertEqual(iou(A,A),1.0)
    def test_iou_partial(self):
        self.assertAlmostEqual(iou(A,(1,1,3,3)),1/7)
    def test_iou_touching(self):
        self.assertEqual(iou(A,(2,0,4,2)),0.0)
    def test_iou_contained(self):
        self.assertEqual(iou(A,(0,0,1,1)),0.25)
    def test_iou_symmetry_translation_scale(self):
        b=(1,1,3,3)
        self.assertEqual(iou(A,b),iou(b,A))
        self.assertAlmostEqual(iou(A,b),iou((10,10,14,14),(12,12,16,16)))
    def test_iou_degenerate(self):
        with self.assertRaises(ValueError): iou((0,0,0,1),A)
    def test_iou_reversed(self):
        with self.assertRaises(ValueError): iou((2,0,1,1),A)
    def test_iou_nan(self):
        with self.assertRaises(ValueError): iou((0,0,math.nan,1),A)
    def test_iou_wrong_dimension(self):
        with self.assertRaises(ValueError): iou((0,0,1),A)
    def test_duplicate_penalty(self):
        self.assertEqual(match_detections([B('a',A)],[B('a',A,.9),B('a',A,.8)]),
                         dict(tp=1,fp=1,fn=0))
    def test_class_mismatch(self):
        self.assertEqual(match_detections([B('a',A)],[B('b',A,.9)]),
                         dict(tp=0,fp=1,fn=1))
    def test_score_boundary_inclusive(self):
        self.assertEqual(match_detections([B('a',A)],[B('a',A,.5)],.5,.5)['tp'],1)
    def test_iou_boundary_inclusive(self):
        self.assertEqual(match_detections([B('a',A)],[B('a',(0,0,1,2),.5)],.5)['tp'],1)
    def test_threshold_filters_predictions(self):
        self.assertEqual(match_detections([B('a',A)],[B('a',A,.49)],.5,.5),
                         dict(tp=0,fp=0,fn=1))
    def test_stable_score_ties(self):
        # First reference wins an exact IoU tie; second box remains unmatched.
        result=match_detections([B('a',A),B('a',A)],[B('a',A,.9)])
        self.assertEqual(result,dict(tp=1,fp=0,fn=1))
    def test_score_sorting_affects_matching(self):
        # Low-score broad prediction overlaps both references. High-score exact
        # prediction must be matched first even if it appears later in input.
        refs=[B('a',(0,0,2,2)),B('a',(1,0,3,2))]
        pred=[B('a',(0,0,3,2),.5),B('a',(0,0,2,2),.9)]
        self.assertEqual(match_detections(refs,pred,.5)['tp'],2)
    def test_invalid_threshold(self):
        for threshold in (0,-1,1.1,math.nan):
            with self.assertRaises(ValueError): match_detections([],[],threshold)
    def test_invalid_score(self):
        with self.assertRaises(ValueError): match_detections([],[B('a',A,math.nan)])
    def test_empty_rates_are_undefined(self):
        self.assertEqual(rates(dict(tp=0,fp=0,fn=0)),
                         dict(precision=None,recall=None,f1=None))
    def test_missed_object_rates(self):
        self.assertEqual(rates(dict(tp=0,fp=0,fn=1)),
                         dict(precision=None,recall=0.0,f1=0.0))
    def test_rates_numeric(self):
        actual=rates(dict(tp=2,fp=1,fn=2))
        self.assertAlmostEqual(actual['precision'],2/3)
        self.assertEqual(actual['recall'],.5)
        self.assertAlmostEqual(actual['f1'],4/7)
    def test_rates_reject_negative_counts(self):
        with self.assertRaises(ValueError): rates(dict(tp=1,fp=-1,fn=0))
    def test_gate_clock_offset_sign(self):
        self.assertTrue(admit_frame(10,10.5,.25,.0625,.3125,True,True))
        self.assertFalse(admit_frame(10,10.5,-.25,.0625,.3125,True,True))
    def test_gate_upper_boundary(self):
        self.assertTrue(admit_frame(10,10.5,.25,.0625,.3125,True,True))
        self.assertFalse(admit_frame(10,10.5,.25,.0625,.30,True,True))
    def test_gate_future_interval(self):
        self.assertFalse(admit_frame(10,10.5,.75,0,1,True,True))
        self.assertFalse(admit_frame(10,10.5,.5,.01,1,True,True))
    def test_gate_unknown_offset(self):
        self.assertFalse(admit_frame(10,10.5,None,.1,1,True,True))
    def test_gate_identity_and_quality(self):
        self.assertFalse(admit_frame(10,10.5,.25,0,1,False,True))
        self.assertFalse(admit_frame(10,10.5,.25,0,1,True,False))
    def test_gate_nonfinite_and_negative_bound(self):
        self.assertFalse(admit_frame(10,math.inf,.25,0,1,True,True))
        self.assertFalse(admit_frame(10,10.5,.25,-.1,1,True,True))
    def test_group_known_sha_fixture(self):
        self.assertEqual(group_partition('site-B'),'calibration')
        self.assertEqual(group_partition('site-A'),'train')
    def test_group_order_and_append_invariance(self):
        original=[dict(frame_id='f1',group_id='site-A'),
                  dict(frame_id='f2',group_id='site-A'),
                  dict(frame_id='f3',group_id='site-B')]
        split=split_manifest(original)
        self.assertEqual(split,split_manifest(list(reversed(original))))
        self.assertEqual(split['f1'],split['f2'])
        extended=split_manifest(original+[dict(frame_id='f4',group_id='site-new')])
        self.assertEqual(split,{k:extended[k] for k in split})
    def test_repeated_frame_rejected(self):
        records=[dict(frame_id='f',group_id='g')]*2
        with self.assertRaises(ValueError): split_manifest(records)
    def test_blank_group_rejected(self):
        with self.assertRaises(ValueError): group_partition('  ')
    def test_listings_match_and_execute(self):
        blocks=re.findall(r'```python\n(.*?)```',
             (ROOT/'research/ml_methods_revision.md').read_text(encoding='utf-8'),re.S)
        self.assertEqual(len(blocks),2)
        for name,block in zip(('listing1_freshness.py','listing2_matching.py'),blocks):
            source=Path(__file__).with_name(name)
            self.assertEqual(source.read_text(encoding='utf-8'),block)
            self.assertLessEqual(max(map(len,block.splitlines())),81)
            subprocess.run([sys.executable,str(source)],check=True,capture_output=True)

class RecordingResult(unittest.TextTestResult):
    def startTest(self,test):
        super().startTest(test)
        self.outcomes.append({'name':test.id(),'status':'RUNNING'})
    def addSuccess(self,test):
        super().addSuccess(test);self.outcomes[-1]['status']='PASS'
    def addFailure(self,test,err):
        super().addFailure(test,err);self.outcomes[-1]['status']='FAIL'
    def addError(self,test,err):
        super().addError(test,err);self.outcomes[-1]['status']='ERROR'
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs);self.outcomes=[]

if __name__=='__main__':
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(ValidationChecks)
    result=unittest.TextTestRunner(verbosity=1,resultclass=RecordingResult).run(suite)
    files=list(Path(__file__).parent.glob('*.py'))
    report={'status':'PASS' if result.wasSuccessful() else 'FAIL',
            'scope':'Deterministic software fixtures; no training, model inference, acquired sensor data or rover performance measurements.',
            'test_count':result.testsRun,'failures':len(result.failures),
            'errors':len(result.errors),'python':platform.python_version(),
            'tests':result.outcomes,
            'code_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}}
    out=ROOT/'build/reports/ml_code_checks.json';out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,indent=2),encoding='utf-8')
    sys.exit(0 if result.wasSuccessful() else 1)
