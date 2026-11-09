"""Actual upgraded engineering checks of existing generated Isolette; no model repair."""
from pathlib import Path
import json,time
from inspecta_scp.controller import Controller

root=Path.cwd();config=json.loads((root/'workbench/profiles/isolette-upgraded.check.json').read_text())
config.update(project=str(root/'.scp-workbench/upgrade-compatibility/fresh_generated'),hamr_platform='Microkit',integration_solver='cvc5',required_gates=['parse_type','architecture_capture','integration_constraints','hamr_codegen'],budget={'wall_seconds':300})
c=Controller(root/'.scp-workbench/app');started=time.monotonic()
try:
 run=c.create(config);run=c.execute(run['id'])
 report={'scope':'Actual upgraded checks of historical generated Isolette source, unchanged. Not new generation, rule transfer or whole-system acceptance.','historical_generated_run_id':'7d406413c64a4219b7674ed71411eaee','model_calls':0,'elapsed_seconds':time.monotonic()-started,'run':run}
 (root/'reports/demo/tool-upgrade/isolette-engineering.json').write_text(json.dumps(report,indent=2)+'\n')
 print(run['id'],run['state']);print([(g['gate'],g['status'],g.get('reason')) for g in run.get('result',{}).get('gates',[])])
finally:c.close()
