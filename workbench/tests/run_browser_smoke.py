"""Opt-in real Firefox UI test, synthetic project only; no model/tool demonstration.
Uses Firefox's local Marionette protocol and standard-library sockets.
"""
import base64
import http.client
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import tempfile
import threading
import time
from inspecta_scp.api import Application, make_server
from inspecta_scp.controller import Controller
from inspecta_scp.sources import Sources


def main():
    evidence = {'scope': 'Actual Firefox application UI smoke; synthetic input; no live engineering demo', 'model_calls': 0, 'checks': []}
    output = Path('reports/build')
    with tempfile.TemporaryDirectory(prefix='inspecta-browser-') as temp:
        root = Path(temp)
        project = root / 'project'
        project.mkdir()
        (project / 'Model.sysml').write_text('package Synthetic {}')
        books = root / 'books'
        books.mkdir()
        (books / 'rules.md').write_text('# MR-BROWSER\n<script>window.inspectaInjected=true</script>\n')
        profile = root / 'browser.json'
        profile.write_text(json.dumps({'sireum':None,'sireum_sha256':None,'project': str(project), 'input_files': ['Model.sysml'],
            'model_file': 'Model.sysml', 'task_operation': 'verify-only', 'repair_allowed_files': ['Model.sysml'],
            'dataset_task': 'incomplete-saved-selection'}))
        learning_profile = root / 'learning.json'
        learning_profile.write_text(json.dumps({'sireum':None,'sireum_sha256':None,'project':str(project),'input_files':['Model.sysml'],
                                               'model_file':'Model.sysml','task_operation':'verify-only'}))
        (project/'Components.sysml').write_text('package Monitor {}\npackage Regulator {}\n')
        split_profile=root/'components.json'
        split_profile.write_text(json.dumps({'sireum':None,'sireum_sha256':None,'project':str(project),'input_files':['Components.sysml'],'model_file':'Components.sysml'}))
        server, token = make_server(Application(root / 'state', [profile, learning_profile, split_profile], [books]))
        controller = Controller(root / 'state')
        try:
            from inspecta_scp.validation_repair import ValidationRepair
            ValidationRepair(controller).set_human_limit(6,3,'Synthetic user authorization')
            controller.store.record('repair_failure_lesson',{'title':'Synthetic failed guard lesson','observation':'Synthetic conflict','cause':'Missing dependency','next_check':'Check assumption owner','rule_id':'SYNTHETIC','disposition':'Draft only','evidence':[]})
            controller.store.record('golden_defect_review',{'title':'Synthetic boundary declaration','target':'Synthetic target','comment':'Synthetic environment condition','human_consent':'Synthetic consent','citations':['Synthetic only'],'artifacts':[], 'model_report':str(project/'absent-proof.json'),'contradiction_report':str(project/'absent-diagnosis.json'),'verification_report':str(project/'absent-proof.json'),'component':'synthetic','scope':'Synthetic UI fixture, not proof','open_obligations':['Internal preservation remains open'],'environmental_assumptions':[{'id':'EA-SYNTHETIC','boundary':'Synthetic system input','predicate':'lower < upper','source_citation':'Synthetic guidebook','allocation':'Trace to component','mapping_status':'DECLARED_NOT_PROVED'}]})
            sources = Sources(controller.store)
            source_root = sources.register_root(project, 'learning')
            source = sources.register(source_root['id'], 'Model.sysml')
            controller.store.record('proof_execution_note',{'tool':'Synthetic Verus','target':'Synthetic target only','result':'TEST FIXTURE','obligations':'Synthetic proof scope disclosure','limitations':'Not live proof evidence','report_path':str(project/'Model.sysml'),'report_sha256':hashlib.sha256((project/'Model.sysml').read_bytes()).hexdigest()})
            controller.store.record('golden_coverage_note',{'feature':'Synthetic golden coverage gap','english_requirement':'Synthetic requirement, not live evidence','golden_observation':'No matching synthetic contract','reference_role':'Synthetic test fixture','qualification_effect':'No automatic acceptance','revisit_condition':'On reference change','reference_files':[{'path':str(project/'Model.sysml'),'sha256':hashlib.sha256((project/'Model.sysml').read_bytes()).hexdigest()}]})
            task_inventory = [{'id': 'browser-task', 'family_id': 'browser-family', 'lineage_id': 'browser-lineage',
                               'role': 'learning', 'source_ids': [source['id']], 'reference_ids': []}]
        finally:
            controller.close()
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        host = '127.0.0.1:' + str(server.server_port)
        def request_http(method, path, headers=None, body=None):
            conn = http.client.HTTPConnection('127.0.0.1', server.server_port, timeout=5)
            conn.request(method, path, body=body, headers=headers or {})
            response = conn.getresponse()
            data = response.read()
            status = response.status
            conn.close()
            return status, data
        assert request_http('GET', '/api/overview')[0] == 401
        auth = {'Authorization': 'Bearer ' + token}
        assert request_http('GET', '/api/overview', {**auth, 'Origin': 'http://evil.invalid'})[0] == 403
        assert request_http('GET', '/api/overview', {**auth, 'Host': 'evil.invalid'})[0] == 403
        assert request_http('POST', '/api/runs', {**auth, 'Content-Type': 'application/json'}, '{}')[0] == 403
        assert request_http('GET', '/../../etc/passwd', auth)[0] == 400
        evidence['checks'].append('HTTP authentication, Host, Origin, traversal rejection')
        with socket.socket() as probe:
            probe.bind(('127.0.0.1', 0))
            marionette_port = probe.getsockname()[1]
        firefox_profile = root / 'firefox'
        firefox_profile.mkdir()
        (firefox_profile / 'user.js').write_text('\n'.join([
            'user_pref("marionette.port", %d);' % marionette_port,
            'user_pref("browser.shell.checkDefaultBrowser", false);',
            'user_pref("browser.startup.homepage_override.mstone", "ignore");',
            'user_pref("datareporting.policy.dataSubmissionEnabled", false);',
            'user_pref("toolkit.telemetry.enabled", false);']))
        log = (output / 'browser-process.log').open('w')
        process = subprocess.Popen(['firefox', '--headless', '--new-instance', '--profile', str(firefox_profile), '--marionette', 'about:blank'], stdout=log, stderr=log)
        sock = None
        try:
            deadline = time.monotonic() + 25
            while time.monotonic() < deadline:
                try:
                    sock = socket.create_connection(('127.0.0.1', marionette_port), timeout=2)
                    break
                except OSError:
                    if process.poll() is not None:
                        raise RuntimeError('Firefox exited; inspect browser-process.log')
                    time.sleep(.2)
            if sock is None:
                raise RuntimeError('Firefox Marionette startup timed out')
            sock.settimeout(20)
            def receive():
                size = b''
                while not size.endswith(b':'):
                    size += sock.recv(1)
                count = int(size[:-1])
                data = b''
                while len(data) < count:
                    block = sock.recv(count - len(data))
                    if not block:
                        raise RuntimeError('Firefox protocol closed')
                    data += block
                return json.loads(data)
            receive()
            sequence = 0
            def command(name, args=None):
                nonlocal sequence
                sequence += 1
                payload = json.dumps([0, sequence, name, args or {}]).encode()
                sock.sendall(str(len(payload)).encode() + b':' + payload)
                response = receive()
                if response[2]:
                    raise RuntimeError(str(response[2]))
                return response[3]
            def js(script):
                result = command('WebDriver:ExecuteScript', {'script': script, 'args': [], 'newSandbox': False, 'sandbox': None})
                return result.get('value') if isinstance(result, dict) else result
            def until(script):
                deadline = time.monotonic() + 10
                while time.monotonic() < deadline:
                    if js('return !!(' + script + ')'):
                        return
                    time.sleep(.1)
                raise AssertionError('UI timeout: ' + script + '\n' + str(js('return document.body.textContent')).replace(token, '[REDACTED]'))
            def click(label):
                script = 'Array.from(document.querySelectorAll("button")).find(b => b.textContent === ' + json.dumps(label) + ')'
                until(script + ' && !(' + script + ').disabled')
                js(script + '.click();')
            session = command('WebDriver:NewSession', {'capabilities': {'alwaysMatch': {'acceptInsecureCerts': False}}})
            evidence['browser'] = session
            command('WebDriver:Navigate', {'url': 'http://' + host + '/#token=' + token})
            until('document.body.textContent.includes("No runs yet")')
            assert js('return location.hash') == ''
            click('Apply & check a project')
            until('document.body.textContent.includes("The saved task has no dataset assignment")')
            assert js('return Array.from(document.querySelectorAll("button")).find(b => b.textContent === "Next").disabled')
            assert not js('return !!document.querySelector(\'input[type="password"]\')')
            click('Use project without dataset')
            evidence['checks'].append('Incomplete dataset selection is blocked at Materials and can be cleared atomically')
            for _ in range(3):
                click('Next')
                time.sleep(.15)
            click('Resolve configuration')
            click('Prepare run')
            until('document.body.textContent.includes("READY")')
            click('pause')
            until('document.body.textContent.includes("PAUSED")')
            click('resume')
            until('document.body.textContent.includes("READY")')
            evidence['checks'].append('Real React workflow resolve, snapshot, pause and resume')
            click('Trace requirements and inputs')
            until('document.body.textContent.includes("No reviewed unit registry")')
            click('Model.sysml')
            until('document.querySelector(".source-text")')
            assert js('return document.querySelector(".source-text").textContent') == 'package Synthetic {}'
            evidence['checks'].append('Run trace opens exact allowlisted snapshot and reports missing requirement/unit links')
            def fill(label, value):
                js('const label = Array.from(document.querySelectorAll("label")).find(l => l.textContent === ' + json.dumps(label) + '); const input = label.querySelector("input"); Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,"value").set.call(input,' + json.dumps(value) + '); input.dispatchEvent(new Event("input",{bubbles:true}));')
                time.sleep(.1)
            js('Array.from(document.querySelectorAll("summary")).find(s => s.textContent === "Request a budget extension").parentElement.open = true;')
            fill('Total tokens', '1000100')
            fill('Total wall-clock seconds', '1300')
            click('Request review')
            until('document.body.textContent.includes("increase_budget")')
            fill('Reviewer name or review record', 'synthetic-browser-test-reviewer')
            click('APPROVED')
            click('Apply approved extension')
            until('document.body.textContent.includes("Approved caps applied")')
            status, body = request_http('GET', '/api/overview', auth)
            recorded = json.loads(body)['runs'][0]
            assert recorded['config']['budget']['wall_seconds'] == 1300
            assert recorded['deadline'] == recorded['created'] + 1300
            assert recorded['used_tokens'] == 0
            click('resume')
            until('document.body.textContent.includes("READY")')
            evidence['checks'].append('Budget request, exact-subject review and approved amendment through UI')
            command('WebDriver:Refresh')
            until('document.body.textContent.includes("READY")')
            evidence['checks'].append('Session reconnect and durable run after reload')
            click('Engineering policies')
            until('document.body.textContent.includes("No architecture captures yet")')
            evidence['checks'].append('Engineering UI reads actual backend records without inventing captures')
            click('Data assignments')
            until('document.querySelector(\'textarea[aria-label="Task inventory JSON"]\')')
            fill('Task name','browser-task')
            fill('Reviewed family','browser-family')
            fill('Reviewed lineage','browser-lineage')
            click('Add project to inventory')
            until('document.querySelector("textarea").value.includes("browser-task")')
            assert json.loads(js('return document.querySelector("textarea").value')) == task_inventory
            click('Save assignment proposal')
            until('document.body.textContent.includes("user_assigned")')
            click('Request assignment review')
            until('document.body.textContent.includes("approve_dataset")')
            status, body = request_http('GET', '/api/datasets', auth)
            assert status == 200 and json.loads(body)['datasets'][0]['proposal']['tasks'][0]['role'] == 'learning'
            evidence['checks'].append('Guided dataset UI registers a saved project, preserves manual membership and requests exact review without moving sources')
            click('Data assignments')
            until('document.querySelector(\'textarea[aria-label="Task inventory JSON"]\')')
            js('const input = document.querySelector("textarea"); Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype,"value").set.call(input,"[]"); input.dispatchEvent(new Event("input",{bubbles:true}));')
            click('Save assignment proposal')
            until('document.body.textContent.includes("Task registry is empty")')
            assert not js('return !!document.querySelector(\'input[type="password"]\')')
            evidence['checks'].append('Configuration errors show their cause without a misleading session-token prompt')
            click('Repair memory')
            until('document.querySelector(\'textarea[aria-label="Exact patch request JSON"]\')')
            patch = {'run_id': recorded['id'], 'issue': 'browser-test', 'patch': {'Model.sysml': {
                'expected_sha256': hashlib.sha256(b'package Synthetic {}').hexdigest(), 'text': 'package Proposed {}'}}}
            js('const input = document.querySelector("textarea"); Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype,"value").set.call(input,' + json.dumps(json.dumps(patch)) + '); input.dispatchEvent(new Event("input",{bubbles:true}));')
            time.sleep(.15)
            click('Stage provisional patch')
            until('document.body.textContent.includes("browser-test")')
            click('Inspect exact diff')
            until('document.body.textContent.includes("+package Proposed")')
            click('Validate revision')
            until('document.body.textContent.includes("BLOCKED — provisional validation")')
            assert (project / 'Model.sysml').read_text() == 'package Synthetic {}'
            evidence['checks'].append('UI stages exact provisional patch, shows diff, blocks missing tool and preserves source')
            click('Rulebooks')
            click('Import books')
            until('document.body.textContent.includes("MR-BROWSER")')
            js('document.querySelector("section.card details").open = true;')
            click('rules.md')
            until('document.querySelector(".source-text")')
            assert '<script>' in js('return document.querySelector(".source-text").textContent')
            assert js('return window.inspectaInjected === undefined')
            evidence['checks'].append('Real source navigation; imported HTML displayed as text without executing')
            js('sessionStorage.setItem("inspecta-token", "invalid-test-token");')
            click('Data assignments')
            until('document.querySelector(\'input[type="password"]\')')
            js('document.querySelector(".error details").open = true;')
            fill('Session token', token)
            click('Connect')
            until('!document.querySelector(\'input[type="password"]\')')
            evidence['checks'].append('Actual authentication rejection offers reconnection and a valid token restores access')
            picture = command('WebDriver:TakeScreenshot', {'id': None, 'full': True})
            if isinstance(picture, dict):
                picture = picture['value']
            (output / 'workbench-browser.png').write_bytes(base64.b64decode(picture))
            click('Apply & check a project')
            until('document.body.textContent.includes("The saved task has no dataset assignment")')
            click('Use project without dataset')
            for _ in range(3):
                click('Next'); time.sleep(.15)
            click('Resolve configuration')
            until('Array.from(document.querySelectorAll("button")).some(b => b.textContent === "Prepare run")')
            assert not js('return !!document.querySelector(".error")')
            fixed_picture = command('WebDriver:TakeScreenshot', {'id': None, 'full': True})
            if isinstance(fixed_picture, dict):fixed_picture = fixed_picture['value']
            (output / 'workbench-workflow-fixed.png').write_bytes(base64.b64decode(fixed_picture))
            click('Home')
            until('document.body.textContent.includes("The self-evolution cycle")')
            click('Set up learning')
            until('document.querySelector("#golden-coverage")?.textContent.includes("Synthetic golden coverage gap")')
            assert js('return document.querySelector("#golden-coverage").textContent.includes("Not supported in golden yet")')
            assert js('return document.querySelector("#golden-coverage").textContent.includes("Coverage notes do not accept rules automatically")')
            evidence['checks'].append('Dedicated golden-coverage section lists uncovered features without declaring tool incapability or accepting candidates; synthetic fixture')
            assert js('return document.querySelector("#golden-defects").textContent.includes("Golden contradictions repaired with human approval")')
            assert js('return document.querySelector("#golden-defects").textContent.includes("0 accepted repair cases")')
            assert js('return document.querySelector("#golden-defects").textContent.includes("EA-SYNTHETIC")')
            assert js('return document.querySelector("#golden-defects").textContent.includes("Assumed from the environment, not a software guarantee")')
            assert js('return document.querySelector("#golden-defects").textContent.includes("DECLARED_NOT_PROVED")')
            evidence['checks'].append('Golden-defect criterion and approved environmental premise display separately from software proof and internal propagation; no invented pass')
            assert js('return document.querySelector("#behavior-acceptance").textContent.includes("Rule transfer is not required")')
            evidence['checks'].append('Scoped behavior acceptance has a separate human review panel and does not require reusable-rule transfer validation')
            assert js('return document.querySelector("#transfer-progress").textContent.includes("Synthetic target only")')
            assert js('return document.querySelector("#transfer-progress").textContent.includes("Accepted and transferred")')
            evidence['checks'].append('Transfer progress and proof target/obligation disclosures are distinct from model acceptance; synthetic fixture')
            assert js('return document.body.textContent.includes("repair up to 6 times")')
            assert js('return document.body.textContent.includes("Synthetic failed guard lesson")')
            evidence['checks'].append('Six-attempt policy and retained failure lessons appear in validation UI; synthetic fixture')
            until('document.body.textContent.includes("Set up Learning Mode")')
            js('const select = Array.from(document.querySelectorAll("label")).find(l => l.textContent.startsWith("Example / project profile")).querySelector("select"); select.value="learning"; select.dispatchEvent(new Event("change",{bubbles:true}));')
            click('Inspect learning materials')
            until('document.body.textContent.includes("Inspection complete")')
            status, body = request_http('GET','/api/learning',auth)
            learning_record=json.loads(body)
            assert status==200 and len(learning_record['sessions'])==1
            assert learning_record['sessions'][0]['model_calls']==0
            assert learning_record['stages'][1]['available']
            assert (books/'rules.md').read_text()=='# MR-BROWSER\n<script>window.inspectaInjected=true</script>\n'
            evidence['checks'].append('Learning home and setup inspect actual materials, preserve books, and disclose unfinished model stages')
            def input_value(label, value):
                js('const el=Array.from(document.querySelectorAll("label")).find(l=>l.textContent.startsWith('+json.dumps(label)+')).querySelector("input,select,textarea"); const setter=Object.getOwnPropertyDescriptor(el.tagName==="SELECT"?HTMLSelectElement.prototype:el.tagName==="TEXTAREA"?HTMLTextAreaElement.prototype:HTMLInputElement.prototype,"value").set; setter.call(el,'+json.dumps(str(value))+'); el.dispatchEvent(new Event(el.tagName==="SELECT"?"change":"input",{bubbles:true}));')
            input_value('Local context repository or folder',str(books))
            click('Inspect context folder')
            until('document.body.textContent.includes("documents found")')
            js('document.querySelector(".file-list input[type=checkbox]").click()')
            click('Import selected context')
            until('document.body.textContent.includes("rules.md · learning context")')
            input_value('Example project','components')
            click('Inspect example files')
            until('document.body.textContent.includes("Components.sysml · 2 lines")')
            source_key=js('return Array.from(document.querySelectorAll("label")).find(l=>l.textContent.startsWith("Source file")).querySelector("select").options[1].value')
            input_value('Source file',source_key)
            input_value('Component label','Monitor')
            input_value('Last line',1)
            click('Add selected component')
            input_value('Component label','Regulator')
            input_value('Use in','validation')
            input_value('First line',2)
            input_value('Last line',2)
            click('Add selected component')
            input_value('Cosine distance threshold',0.1)
            click('Review this learning split')
            until('document.body.textContent.includes("Train on Monitor. Validate on Regulator.")')
            input_value('Reviewer name','Browser synthetic reviewer')
            click('Approve displayed split')
            until('document.body.textContent.includes("Review selected split · APPROVED")')
            status,body=request_http('GET','/api/learning',auth)
            records=json.loads(body)
            assert len(records['plans'])==1 and records['plans'][0]['retrieval']['epsilon']==0.1
            assert records['plans'][0]['training'][0]['end']==1 and records['plans'][0]['validation'][0]['start']==2
            assert not js('return window.inspectaInjected===true')
            evidence['checks'].append('Context repository selection, disjoint component ranges, cosine-distance epsilon and exact split approval through Firefox')
            input_value('Materials for preparation',records['plans'][0]['id'])
            input_value('English availability','existing')
            input_value('Existing system description and requirements','Synthetic training description. REQ-1: Preserve the Monitor package.')
            click('Prepare English for review')
            until('document.querySelector("#learning-preparation").textContent.includes("Source trace, preparation usage and provenance")')
            input_value('Prepared data reviewer','Synthetic preparation reviewer')
            click('Approve prepared English')
            until('document.body.textContent.includes("Reviewed training English is ready.")')
            status,prepared_body=request_http('GET','/api/learning',auth)
            prepared_records=json.loads(prepared_body)['prepared_requirements']
            assert len(prepared_records)==1 and prepared_records[0]['role']=='training'
            assert prepared_records[0]['approval']['status']=='APPROVED'
            input_value('Review and edit prepared English','Unsaved modified description.')
            assert js('return Array.from(document.querySelectorAll("button")).find(b=>b.textContent==="Approve prepared English").disabled')
            input_value('Review and edit prepared English',prepared_records[0]['english'])
            evidence['checks'].append('Data preparation saves existing English with source/role provenance; exact review unlocks learning; unsaved edits cannot be approved; zero model calls')
            input_value('System or component to describe','validation:0')
            input_value('English availability','source')
            input_value('Existing English source',records['context_documents'][0]['id'])
            input_value('English passage last line',2)
            click('Prepare English for review')
            until('document.querySelector("#learning-preparation h3")?.textContent.includes("Regulator")')
            status,prepared_body=request_http('GET','/api/learning',auth)
            source_prepared=[r for r in json.loads(prepared_body)['prepared_requirements'] if r['role']=='validation'][0]
            assert source_prepared['approval']['status']=='APPROVED' and source_prepared['english_source']['start']==1
            assert 'source reuse only' in source_prepared['approval']['reviewer']
            assert not js('return window.inspectaInjected===true')
            evidence['checks'].append('Existing approved English passage is reused with exact range and inherited source authorization, separate from semantic validation; source markup remains inert')
            js('document.querySelector("#learning-preparation details").open=true')
            input_value('Supporting approved document',records['context_documents'][0]['id'])
            click('Read supporting source with line numbers')
            until('document.querySelector("#learning-preparation pre")!==null')
            input_value('Dependency last line',2)
            input_value('Why this context is required','Restore a referenced definition for synthetic validation.')
            click('Create supplemented English for review')
            until('Array.from(document.querySelectorAll("#learning-preparation option")).some(x=>x.selected && x.textContent.includes("supplemented English"))')
            status,supplement_body=request_http('GET','/api/learning',auth)
            supplemented=[r for r in json.loads(supplement_body)['prepared_requirements'] if r.get('context_supplements')][0]
            assert supplemented['approval']['status']=='PENDING'
            assert supplemented['previous_preparation_id']==source_prepared['id']
            assert supplemented['english'].startswith(source_prepared['english'])
            assert not js('return window.inspectaInjected===true')
            evidence['checks'].append('Supporting context can be read and appended through the UI; exact source provenance retained, original approval unchanged, supplemented English needs review, no model calls')
            # Synthetic capability fixture: tests UI policy, never engineering support.
            synthetic_tool=root/'tool/bin/sireum';synthetic_tool.parent.mkdir(parents=True);synthetic_tool.write_text('synthetic version one');synthetic_tool.chmod(0o700)
            fixture_controller=Controller(root/'state')
            try:
                tool_hash=hashlib.sha256(synthetic_tool.read_bytes()).hexdigest()
                probe=fixture_controller.create({'sireum':None,'sireum_sha256':None,'project':str(project),'input_files':['Model.sysml'],'model_file':'Model.sysml','task_operation':'verify-only','required_gates':['parse_type'],'sireum':str(synthetic_tool),'sireum_sha256':tool_hash})
                ref=fixture_controller.store.object({'tool_identity':{'launcher_sha256':tool_hash,'runtime_files':{}},'scope':'Synthetic browser fixture; no executed capability claim'})
                fixture_controller._parse_type=lambda *args:({'gate':'parse_type','status':'FAIL','reason':'Synthetic unsupported fixture','evidence':ref},None)
                fixture_controller.execute(probe['id'])
            finally:fixture_controller.close()
            js('document.querySelector("#learning-capabilities details").open=true')
            input_value('English revision for capability review',prepared_records[0]['id'])
            click('Refresh capability evidence')
            until('Array.from(document.querySelectorAll("#learning-capabilities option")).some(x=>x.value==='+json.dumps(probe['id'])+')')
            input_value('Executed capability check',probe['id'])
            input_value('Requirement identifier','REQ-1')
            input_value('Exact English excerpt','REQ-1: Preserve the Monitor package.')
            input_value('Capability classification','NOT_SUPPORTED_TOOL_VERSION')
            input_value('Capability evidence and reason','Synthetic feature absence; UI test only.')
            input_value('Alternative encoding review','Synthetic review, not an actual limitation.')
            input_value('When to revisit','After a tool upgrade.')
            click('Add target for review');click('Save capability scope for review')
            until('document.querySelector("#learning-capabilities").textContent.includes("1 mandatory in this scope")')
            input_value('Capability scope reviewer','Synthetic capability reviewer')
            click('Approve displayed version-specific scope')
            until('document.querySelector("#learning-capabilities").textContent.includes("1 tool-unsupported")')
            status,scope_body=request_http('GET','/api/learning',auth);scope=json.loads(scope_body)['capability_scopes'][0]
            assert scope['deferred_targets']==1 and scope['total_targets']==1 and scope['verified_targets']==0
            assert not scope['whole_system_acceptance']
            synthetic_tool.write_text('synthetic upgraded tool')
            status,scope_body=request_http('GET','/api/learning',auth);scope=json.loads(scope_body)['capability_scopes'][0]
            assert not scope['current'] and scope['mandatory_targets']==1 and scope['deferred_targets']==0
            evidence['checks'].append('Version-specific scope review defers only approved unsupported targets without proof credit, preserves English and invalidates exclusions on tool upgrade; synthetic capability fixture')
            from inspecta_scp.unit_definitions import UnitDefinitions,FIELDS,ARRAYS
            definition={**{k:'Synthetic browser '+k for k in FIELDS},**{k:['Synthetic browser '+k] for k in ARRAYS},'granularity':'sysml_gumbo_obligation'}
            fixture_controller=Controller(root/'state')
            try:
                from inspecta_scp.campaign import Campaign
                campaign=Campaign(fixture_controller.store).authorize(200000,60,'Synthetic browser fixture; no model calls')
                task=fixture_controller.store.record('development_task',{'baseline_run_id':recorded['id'],
                    'target_file':'Model.sysml','candidate_ids':[]})
                comparison=fixture_controller.store.record('development_golden_comparison',{
                    'architecture_status':'UNKNOWN','architecture_differences':None})
                fixture_controller.store.record('development_result',{'task_id':task['id'],
                    'generated_run_id':recorded['id'],'reference_run_id':recorded['id'],
                    'comparison_id':comparison['id'],'status':'NOT_VALIDATED',
                    'whole_system_acceptance':False,'scope':'Synthetic browser display fixture, not generation evidence'})
                for attempt in range(6):
                    fixture_controller.store.record('development_generation_context',{'task_id':task['id'],'development_retry':{'synthetic_attempt':attempt}})
                proposal=fixture_controller.store.record('unit_definition_proposal',{'plan_id':records['plans'][0]['id'],'model_call_id':'synthetic-not-live','definition':definition})
                UnitDefinitions(fixture_controller.store).revise(proposal['id'],definition)
            finally:fixture_controller.close()
            click('Home');click('Set up learning')
            until('document.body.textContent.includes("Review selected split · APPROVED")')
            assert js('return document.body.textContent.includes("Train on Monitor. Validate on Regulator.")')
            click('Pause model work')
            until('document.body.textContent.includes("Model work: PAUSED")')
            assert js('return Array.from(document.querySelectorAll("button")).find(b=>b.textContent==="Extract all remaining context batches").disabled')
            click('Resume model work')
            until('document.body.textContent.includes("Model work: ACTIVE")')
            assert not js('return Array.from(document.querySelectorAll("button")).find(b=>b.textContent==="Extract all remaining context batches").disabled')
            evidence['checks'].append('Approved split restored after navigation; campaign pause/resume disables/enables extraction without any model call')
            input_value('Rule extraction focus','system_architecture')
            assert js('return document.body.textContent.includes("Whole-system architecture and interfaces")')
            input_value('Rule extraction focus','full_stack')
            click('Export versioned learned rulebook')
            until('document.body.textContent.includes("DRAFT_NOT_PUBLISHED")')
            status,body=request_http('GET','/api/learning',auth)
            assert json.loads(body)['learned_books'][0]['candidate_count']==0
            js('Array.from(document.querySelectorAll("details")).find(d=>d.querySelector("summary")?.textContent.includes("0 learned candidates")).open=true;')
            click('Read learned book')
            until('document.body.textContent.includes("Learned book · DRAFT")')
            assert js('return document.querySelector("#learning-rules .source-text").textContent.includes("not a validated or published User release")')
            click('Close learned book')
            evidence['checks'].append('System-level extraction focus is selectable; readable book export preserves draft status without model calls')
            input_value('Learning operation','specialize')
            assert js('return Array.from(document.querySelectorAll("button")).find(b=>b.textContent==="Ask Astra to learn from this failure").disabled')
            assert js('return document.querySelector("#learning-workflows").textContent.includes("Golden models and graph differences are excluded")')
            input_value('Learning operation','generalize')
            evidence['checks'].append('Workflow generalization/specialization is selectable and blocked without exact context, provenance and prior-rule selections; no model call')
            assert js('return document.querySelector("#learning-validation input[type=file]").accept.includes(".txt")')
            assert js('return document.querySelector("#learning-validation").textContent.includes("repair up to 6 times")')
            click('Inspect generated model, golden comparison and gates')
            until('document.body.textContent.includes("Recorded development evidence · NOT_VALIDATED")')
            assert js('return document.body.textContent.includes("Historical exact syntax comparison: UNKNOWN")')
            assert js('return document.body.textContent.includes("package Synthetic")')
            assert js('return Array.from(document.querySelectorAll("button")).some(b=>b.textContent==="Compare directed architecture graphs ignoring names")')
            assert js('return document.body.textContent.includes("Rules consulted and proposed repairs")')
            until('document.body.textContent.includes("6 repair attempts have been made")')
            input_value('Your repair suggestion','Check the port direction; preserve requirements')
            input_value('Guidance reviewer','Synthetic browser reviewer')
            click('Save suggestion and authorize up to 6 more repairs')
            until('document.body.textContent.includes("6 total repair attempts; 0 since human guidance")')
            evidence['checks'].append('Validation English upload, six-attempt human checkpoint and explicit continuation preserve total repair count; no model call')
            assert js('return document.body.textContent.includes("Structural meta-rule review")')
            js('const panel=document.createElement("div");panel.id="structural-browser-fixture";document.body.appendChild(panel);ReactDOM.createRoot(panel).render(React.createElement(StructuralPatternPanel,{patterns:{generated:{evidence_current:true,roots:[{root:"Fixture",component_counts:{System:1,Process:1,Thread:4},one_thread_per_process:{status:"FAIL",violations:[{direct_threads:4}]},gumbo_owner_categories:{Thread:3}}]}}}));')
            until('document.querySelector("#structural-browser-fixture")?.textContent.includes("FAIL")')
            assert js('return document.querySelector("#structural-browser-fixture table").textContent.includes("No capture")')
            assert js('return document.querySelector("#structural-browser-fixture").textContent.includes("style observation")')
            js('document.querySelector("#structural-browser-fixture").remove()')
            evidence['checks'].append('Structural profile panel distinguishes four-Thread Process failure, missing reference capture, GUMBO owners and advisory source order; synthetic display fixture')
            click('Close evidence inspection')
            evidence['checks'].append('Development evidence inspection renders actual backend snapshot text and unknown comparison without claiming validation')
            until('Array.from(document.querySelectorAll("label")).some(l=>l.textContent.startsWith("Saved unit definitions"))')
            unit_key=js('return Array.from(document.querySelectorAll("label")).find(l=>l.textContent.startsWith("Saved unit definitions")).querySelector("select").options[1].value')
            input_value('Saved unit definitions',unit_key)
            until('document.body.textContent.includes("What one unit means")')
            input_value('What one unit means','Edited synthetic unit meaning')
            assert js('return Array.from(document.querySelectorAll("button")).find(b=>b.textContent==="Approve displayed unit definition").disabled')
            click('Save edited definition for review')
            until('document.body.textContent.includes("Review status: PENDING")')
            input_value('Unit-definition reviewer','Synthetic browser reviewer')
            click('Approve displayed unit definition')
            until('document.body.textContent.includes("Review status: APPROVED")')
            status,body=request_http('GET','/api/learning',auth)
            definitions=json.loads(body)['unit_definitions']
            assert any(x['human_modified'] and x['definition']['definition']=='Edited synthetic unit meaning' for x in definitions)
            assert all(x['verified_count']==0 for x in definitions)
            evidence['checks'].append('Unit-definition editing creates a new revision; unsaved edits cannot be approved and approval creates no verified units')

            # Exact scoped bulk approval with synthetic evidence; no engineering claim.
            fixture_controller=Controller(root/'state')
            try:
                from inspecta_scp.scoped_rulebooks import ScopedRulebooks
                rule=json.loads((Path(__file__).parent/'fixtures/synthetic-rule.json').read_text());rule['dependencies']=[]
                rule['validation_gate_ids']=['parse_type','configured_formal_verification']
                candidate=fixture_controller.store.record('candidate_rule',{'record':rule})
                scoped_run=fixture_controller.create({'sireum':None,'sireum_sha256':None,'project':str(project),'input_files':['Model.sysml'],'model_file':'Model.sysml','task_operation':'verify-only','required_gates':['parse_type']})
                ref=fixture_controller.store.object({'scope':'Synthetic browser policy fixture; not actual proof'})
                fixture_controller._parse_type=lambda *args:({'gate':'parse_type','status':'PASS','reason':'Synthetic scoped browser fixture','evidence':ref},None)
                scoped_run=fixture_controller.execute(scoped_run['id'])
                scoped_task=fixture_controller.store.record('development_task',{'baseline_run_id':scoped_run['id'],'target_file':'Model.sysml','candidate_ids':[candidate['id']]})
                scoped_result=fixture_controller.store.record('development_result',{'task_id':scoped_task['id'],'generated_run_id':scoped_run['id'],'status':'NOT_VALIDATED'})
                service=ScopedRulebooks(fixture_controller)
                scope_a=service.create(scoped_result['id'],'Synthetic scope A',['parse_type'])
                scope_b=service.create(scoped_result['id'],'Synthetic scope B',['parse_type'])
                scope_partial=service.create(scoped_result['id'],'Synthetic partial scope',['parse_type','configured_formal_verification'])
            finally:fixture_controller.close()
            click('Home');click('Set up learning')
            until('document.querySelector("#scoped-rulebooks")?.textContent.includes("Synthetic partial scope")')
            assert js('return document.querySelector("#scoped-rulebooks").textContent.includes("1/2 passed (50%)")')
            assert js('return document.querySelector("#scoped-rulebooks").textContent.includes("coverage unknown")')
            assert js('return document.querySelector("#scoped-rulebooks").textContent.includes("ISOLETTE-INVALID-RANGE-CONSUMPTION")')
            assert js('return Array.from(document.querySelectorAll("#scoped-rulebooks article > label")).find(l=>l.textContent.includes("Synthetic partial scope")).querySelector("input").disabled')
            js('Array.from(document.querySelectorAll("#scoped-rulebooks article > label")).find(l=>l.textContent.includes("Synthetic scope A")).querySelector("input").click()')
            input_value('Scoped approval comment','Synthetic review: parser scope only; behavior remains open')
            click('Review approval of selected eligible rulebooks')
            until('document.body.textContent.includes("Confirm exact scoped selection")')
            input_value('Scoped approval reviewer','Synthetic scope reviewer')
            click('Approve all displayed rulebooks for current scopes')
            until('document.querySelector("#scoped-rulebooks").textContent.includes("1 accepted scopes")')
            status,body=request_http('GET','/api/learning/rulebook-scopes',auth)
            scoped_rows={r['id']:r for r in json.loads(body)['scopes']}
            assert scoped_rows[scope_b['id']]['status']=='ACCEPTED_CURRENT_SCOPE'
            assert scoped_rows[scope_a['id']]['status']=='AWAITING_HUMAN_REVIEW'
            assert scoped_rows[scope_partial['id']]['status']=='PARTIAL_SUCCESS'
            assert all(not r['publishes_rules'] and not r['whole_system_acceptance'] for r in scoped_rows.values())
            click('Select all eligible scopes')
            click('Review approval of selected eligible rulebooks')
            until('document.body.textContent.includes("Confirm exact scoped selection")')
            click('Approve all displayed rulebooks for current scopes')
            until('document.querySelector("#scoped-rulebooks").textContent.includes("2 accepted scopes")')
            evidence['checks'].append('Scoped bulk approval defaults to eligible scopes, preserves deselection, blocks incomplete scope, displays50%check score/unknown requirement coverage, saves exact human reviews and never publishes; synthetic fixture')

            # Synthetic mapped formal evidence exercises per-obligation decisions, not actual proofs.
            fixture_controller=Controller(root/'state')
            try:
                from inspecta_scp.evidence_review import EvidenceReview
                formal_run=fixture_controller.create({'sireum':None,'sireum_sha256':None,'project':str(project),'input_files':['Model.sysml'],'model_file':'Model.sysml','task_operation':'verify-only','required_gates':['parse_type','configured_formal_verification']})
                formal_ref=fixture_controller.store.object({'mapped_obligations':[
                    {'id':'verified','requirement':'SYNTHETIC-REQ-A','contract':'a','status':'PASS'},
                    {'id':'open','requirement':'SYNTHETIC-REQ-B','contract':'b','status':'FAIL'}]})
                fixture_controller.store.change(formal_run['id'],{'READY'},'CHECKING',worker=os.getpid())
                fixture_controller.store.finish(formal_run['id'],{'task_status':'FAILED','gates':[
                    {'gate':'parse_type','status':'PASS','reason':'Synthetic parser','evidence':ref},
                    {'gate':'configured_formal_verification','status':'FAIL','reason':'Synthetic mapped failure','evidence':formal_ref}]})
                formal_task=fixture_controller.store.record('development_task',{'baseline_run_id':formal_run['id'],'target_file':'Model.sysml','candidate_ids':[candidate['id']]})
                formal_result=fixture_controller.store.record('development_result',{'task_id':formal_task['id'],'generated_run_id':formal_run['id'],'status':'NOT_VALIDATED'})
                review=EvidenceReview(fixture_controller).propose(formal_result['id'],require_semantic=False)
            finally:fixture_controller.close()
            click('Home');click('Set up learning')
            until('document.querySelector("#evidence-decisions")?.textContent.includes("SYNTHETIC-REQ-B")')
            input_value('Evidence decision reviewer','Synthetic evidence reviewer')
            assert js('return document.querySelector("#evidence-decisions").textContent.includes("1/2 mapped obligations")')
            assert js('return Array.from(document.querySelectorAll("#evidence-decisions button")).find(b=>b.textContent==="Accept reviewed scope").disabled')
            click('Propose exclusion / edit')
            input_value('Exclusion reason and supporting evidence','Synthetic human deferral for policy testing')
            input_value('Revisit condition','After synthetic follow-up')
            click('Save proposed exclusion')
            until('document.querySelector("#evidence-decisions").textContent.includes("Approve exclusion")')
            assert js('return !!document.querySelector(".pending-scope-proposal") && document.querySelector(".pending-scope-proposal").getBoundingClientRect().height>0')
            click('Edit and approve')
            input_value('Exclusion reason and supporting evidence','Edited synthetic deferral')
            click('Approve displayed exclusion')
            until('document.querySelector("#evidence-decisions").textContent.includes("HUMAN_APPROVED_DEFERRAL")')
            click('Accept reviewed scope')
            until('document.querySelector("#evidence-decisions").textContent.includes("ACCEPTED HUMAN REVIEWED PARTIAL SCOPE")')
            assert js('return document.querySelector("#evidence-decisions").textContent.includes("SYNTHETIC-REQ-B: FAIL")')
            click('Revoke exclusion')
            until('Array.from(document.querySelectorAll("#evidence-decisions button")).find(b=>b.textContent==="Accept reviewed scope").disabled')
            until('document.querySelector("#evidence-decisions").textContent.includes("PARTIAL PROGRESS NOT ACCEPTED")')
            evidence['checks'].append('Per-obligation exclusion editing/approval and scoped acceptance preserve original formal failure and scores; revocation reopens required work; synthetic evidence')

            # The simple flow requires no reason typing: tick, defer, tick, approve.
            js("document.querySelector('input[aria-label=\"Select configured_formal_verification:open\"]').click()")
            click('Defer selected')
            until('document.querySelector(".simple-review").textContent.includes("Decision deferred")')
            js("document.querySelector('input[aria-label=\"Select configured_formal_verification:open\"]').click()")
            click('Exclude selected & accept partial')
            until('document.querySelector(".simple-review").textContent.includes("Accepted for reviewed scope")')
            click('Undo this exclusion')
            until('document.querySelector(".simple-review").textContent.includes("Validation in progress")')
            evidence['checks'].append('Simplified verification flow: checkbox selection, defer without exclusion, one-click exclusion plus partial acceptance, and undo; synthetic evidence')

            fixture_controller=Controller(root/'state')
            try:
                from inspecta_scp.approvals import Approvals
                engineering_approval=Approvals(fixture_controller.store).request('approve_requirements',{'kind':'engineering_proposal','title':'Synthetic engineering proposal','summary':'Synthetic exact patch decision, no proof credit.','proposal':'synthetic patch'})
            finally:fixture_controller.close()
            click('Home');click('Set up learning')
            click('Refresh proof progress')
            until('document.querySelector("#evidence-decisions")?.textContent.includes("Synthetic engineering proposal")')
            assert js('return Array.from(document.querySelectorAll("button")).find(b=>b.textContent==="Approve this proposal").disabled')
            input_value('Evidence decision reviewer','Synthetic proposal reviewer')
            click('Approve this proposal')
            until('document.querySelector("#evidence-decisions").textContent.includes("Synthetic engineering proposal · APPROVED")')
            click('Revoke this proposal approval')
            until('document.querySelector("#evidence-decisions").textContent.includes("Synthetic engineering proposal · REVOKED")')
            evidence['checks'].append('Engineering proposal is visible beside gates; approval requires reviewer, records exact subject and can be revoked without granting proof credit; synthetic fixture')

            fixture_controller=Controller(root/'state')
            try:
                review_service=EvidenceReview(fixture_controller)
                exclusion=review_service.exclude(review['id'],'configured_formal_verification:open','GOLDEN_COVERAGE','Synthetic golden physical interaction gap','On synthetic reference extension')
                approval=exclusion['approval']
                Approvals(fixture_controller.store).decide(approval['id'],approval['subject_digest'],'APPROVED','Synthetic Results reviewer',controller=fixture_controller)
            finally:fixture_controller.close()
            click('Runs & results')
            until('document.querySelector("#current-results")?.textContent.includes("HUMAN-APPROVED EXCLUSION")')
            assert js('return document.querySelector("#current-results").textContent.includes("Synthetic golden physical interaction gap")')
            assert js('return document.querySelector("#current-results").textContent.includes("Recorded application checks")')
            click('Refresh proof progress')
            until('!!document.querySelector("#current-results") && document.querySelector("nav[aria-label=Workspace] button[aria-current=page]").textContent==="Runs & results"')
            evidence['checks'].append('Results tab loads current gate scores and approved exclusions; refresh stays on Results and support checks remain separate; synthetic evidence')

            learning_picture=command('WebDriver:TakeScreenshot', {'id':None,'full':True})
            if isinstance(learning_picture,dict):learning_picture=learning_picture['value']
            (output/'workbench-learning.png').write_bytes(base64.b64decode(learning_picture))
            evidence['status'] = 'PASS'
            command('WebDriver:DeleteSession')
        finally:
            if sock:
                sock.close()
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
            log.close()
            server.shutdown()
            server.server_close()
    (output / 'browser-smoke.json').write_text(json.dumps(evidence, indent=2) + '\n')
    print(json.dumps({'status': evidence['status'], 'checks': evidence['checks'], 'model_calls': 0}, indent=2))


if __name__ == '__main__':
    main()
