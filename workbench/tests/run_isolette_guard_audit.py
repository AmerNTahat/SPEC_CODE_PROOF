"""Bounded checks of explicitly transcribed guards; not a GUMBO proof or reachability result."""
from pathlib import Path
import json,hashlib,itertools
root=Path.cwd();source=root/'reports/demo/isolette-revised-generated-Regulate.sysml';text=source.read_text()
assert 'guarantee REQ_MRM_2:' in text and 'guarantee REQ_MRM_4:' in text
assert 'In(Duration_INMODE) > 1.0' in text
cases=[]
for healthy,duration in [(True,0.5),(False,1.1),(True,1.1)]:
    # Explicit transcription of REQ_MRM_2 and REQ_MRM_4 for Previous_Mode=INIT.
    normal_guard=healthy;failed_guard=duration>1.0
    allowed=[mode for mode in ['INIT','NORMAL','FAILED'] if (not normal_guard or mode=='NORMAL') and (not failed_guard or mode=='FAILED')]
    cases.append({'previous_mode':'INIT','regulator_healthy':healthy,'previous_duration_seconds':duration,'REQ_MRM_2_guard':normal_guard,'REQ_MRM_4_guard':failed_guard,'allowed_outputs_for_these_two_guarantees':allowed})
assert cases[0]['allowed_outputs_for_these_two_guarantees']==['NORMAL']
assert cases[1]['allowed_outputs_for_these_two_guarantees']==['FAILED']
assert cases[2]['allowed_outputs_for_these_two_guarantees']==[]
report={'source':source.relative_to(root).as_posix(),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'method':'Exhaustive enumeration of3 output modes for3 explicit input witnesses using manually transcribed two-guard semantics','scope':'Local guard consistency only; not automatically extracted GUMBO semantics, reachable-state proof, complete contract satisfiability or whole-system acceptance','cases':cases,'result':'Healthy expired INIT admits no output satisfying both guarantees','next_step':'Review transition priority or justify/prove this pre-state unreachable using actual timing and execution semantics. Do not silently add an assumption.','model_calls':0,'whole_system_acceptance':False}
(root/'reports/demo/ISOLETTE_GUARD_AUDIT.json').write_text(json.dumps(report,indent=2)+'\n');print(report['result'])
