import json
from industrialops.evaluation.v07.judge_runner import load_judge_case_results
def test_loads_completed_metrics(tmp_path):
    p=tmp_path/'r.json';p.write_text(json.dumps({'metrics':[{'scenario_id':'s','status':'answered','ragas_faithfulness':1.0,'deepeval_faithfulness':0.9}]}),encoding='utf8')
    assert load_judge_case_results(p)[0]['hard_gate_passed'] is True
