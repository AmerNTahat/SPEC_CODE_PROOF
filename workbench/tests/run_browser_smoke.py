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
        profile.write_text(json.dumps({'project': str(project), 'input_files': ['Model.sysml'],
            'model_file': 'Model.sysml', 'task_operation': 'verify-only', 'repair_allowed_files': ['Model.sysml'],
            'dataset_task': 'incomplete-saved-selection'}))
        learning_profile = root / 'learning.json'
        learning_profile.write_text(json.dumps({'project':str(project),'input_files':['Model.sysml'],
                                               'model_file':'Model.sysml','task_operation':'verify-only'}))
        (project/'Components.sysml').write_text('package Monitor {}\npackage Regulator {}\n')
        split_profile=root/'components.json'
        split_profile.write_text(json.dumps({'project':str(project),'input_files':['Components.sysml'],'model_file':'Components.sysml'}))
        server, token = make_server(Application(root / 'state', [profile, learning_profile, split_profile], [books]))
        controller = Controller(root / 'state')
        try:
            sources = Sources(controller.store)
            source_root = sources.register_root(project, 'learning')
            source = sources.register(source_root['id'], 'Model.sysml')
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
            click('Inspect generated model, golden comparison and gates')
            until('document.body.textContent.includes("Recorded development evidence · NOT_VALIDATED")')
            assert js('return document.body.textContent.includes("Golden comparison: UNKNOWN")')
            assert js('return document.body.textContent.includes("package Synthetic")')
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
