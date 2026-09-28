"""One durable allowance across live trials, retries, forecasts and repairs."""
import time
import uuid
import json
from .config import PolicyError


class Campaign:
    def __init__(self, store):self.store=store

    def control_state(self,campaign_id):
        row=self.store.db.execute("SELECT payload FROM events WHERE run_id=? AND kind='campaign_control' ORDER BY id DESC LIMIT 1",('campaign:'+campaign_id,)).fetchone()
        return json.loads(row['payload'])['state'] if row else 'ACTIVE'

    def control(self,campaign_id,action):
        if action not in {'pause','resume'}:raise PolicyError('Choose pause or resume')
        self.store.db.execute('BEGIN IMMEDIATE')
        try:
            state=self.status(campaign_id)
            if action=='resume' and state['reserved_tokens']:raise PolicyError('Wait for the interrupted call to settle before resuming')
            desired='PAUSED' if action=='pause' else 'ACTIVE'
            if state['control_state']!=desired:
                self.store.event('campaign:'+campaign_id,'campaign_control',{'state':desired,'clock_and_usage_reset':False})
            self.store.db.execute('COMMIT')
        except BaseException:self.store.db.execute('ROLLBACK');raise
        return self.status(campaign_id)

    def authorize(self, tokens, wall_seconds, consent):
        if type(tokens) is not int or tokens <= 0 or type(wall_seconds) is not int or wall_seconds <= 0:
            raise PolicyError('Positive aggregate token and wall-clock limits required')
        if not isinstance(consent,str) or not consent.strip():raise PolicyError('Explicit best-effort authorization record required')
        record=self.store.record('campaign_authorization',{'aggregate_tokens':tokens,'wall_seconds':wall_seconds,
            'enforcement':'best_effort','consent':consent,'hard_token_cap_validated':False,
            'clock_starts':'first paid reservation','concurrency':1,'automatic_extension':False})
        self.store.db.execute('INSERT OR IGNORE INTO campaigns(id) VALUES(?)',(record['id'],))
        return self.status(record['id'])

    def status(self, campaign_id):
        authorization=self.store.read_record('campaign_authorization',campaign_id)
        row=self.store.db.execute('SELECT * FROM campaigns WHERE id=?',(campaign_id,)).fetchone()
        if row is None:raise PolicyError('Unknown campaign ledger')
        estimated=self.store.db.execute('SELECT COALESCE(SUM(a.debit),0) FROM campaign_adjustments a JOIN campaign_calls c ON a.call_id=c.id WHERE c.campaign_id=?',(campaign_id,)).fetchone()[0]
        extensions=[x for x in self.store.records('campaign_time_extension') if x['campaign_id']==campaign_id]
        token_extensions=[x for x in self.store.records('campaign_token_extension') if x['campaign_id']==campaign_id]
        ceiling=authorization['aggregate_tokens']+sum(x['tokens'] for x in token_extensions)
        wall_seconds=authorization['wall_seconds']+sum(x['seconds'] for x in extensions)
        result=dict(row);result['estimated_debit_tokens']=estimated;deadline=row['started']+wall_seconds+sum(x.get('expired_wait_seconds',0) for x in extensions) if row['started'] is not None else None
        policies=[p for p in self.store.records('campaign_failure_policy') if p['campaign_id']==campaign_id]
        continuations=[p for p in self.store.records('campaign_continuation_allowance') if p['campaign_id']==campaign_id]
        continuation_extensions=[p for p in self.store.records('campaign_continuation_extension') if p['campaign_id']==campaign_id]
        extra=sum(p['tokens'] for p in continuation_extensions)
        continuation_remaining=min((max(0,p['baseline_charged_tokens']+p['additional_charged_tokens']+extra-row['used_tokens']-estimated-row['reserved_tokens']) for p in continuations),default=None)
        return {**result,'control_state':self.control_state(campaign_id),'failure_policy':policies[-1] if policies else None,'authorization':authorization,'deadline':deadline,
            'continuation_remaining_tokens':continuation_remaining,'continuation_extensions':continuation_extensions,
            'time_extensions':extensions,'token_extensions':token_extensions,'token_ceiling':ceiling,'authorized_wall_seconds':wall_seconds,
            'remaining_seconds':max(0,deadline-time.time()) if deadline else wall_seconds,
            'remaining_tokens':None if row['usage_unknown'] else max(0,ceiling-row['used_tokens']-estimated-row['reserved_tokens']),
            'scope':'Best-effort aggregate accounting; termination may leave uncertain in-flight usage'}

    def extend_continuation(self,campaign_id,tokens,expected_remaining,consent):
        """Increase only the explicit continuation sublimit, never the aggregate cap."""
        if type(tokens) is not int or tokens<=0 or not isinstance(consent,str) or not consent.strip():
            raise PolicyError('Positive continuation extension and explicit authorization required')
        self.store.db.execute('BEGIN IMMEDIATE')
        try:
            state=self.status(campaign_id)
            if state['reserved_tokens']:raise PolicyError('Wait for the active call to settle')
            if state['continuation_remaining_tokens'] is None or state['continuation_remaining_tokens']!=expected_remaining:
                raise PolicyError('Continuation extension must bind the exact remaining allowance')
            extension=self.store.record('campaign_continuation_extension',{'campaign_id':campaign_id,'tokens':tokens,
                'previous_remaining':expected_remaining,'consent':consent,'deadline_unchanged':state['deadline'],
                'aggregate_ceiling_unchanged':state['token_ceiling'],'charged_tokens_unchanged':state['used_tokens']+state['estimated_debit_tokens']})
            self.store.event('campaign:'+campaign_id,'continuation_extension_authorized',extension)
            self.store.db.execute('COMMIT')
        except BaseException:self.store.db.execute('ROLLBACK');raise
        return self.status(campaign_id)

    def extend_tokens(self,campaign_id,tokens,expected_ceiling,consent):
        if type(tokens) is not int or tokens<=0 or not isinstance(consent,str) or not consent.strip():
            raise PolicyError('Positive token extension and explicit authorization required')
        self.store.db.execute('BEGIN IMMEDIATE')
        try:
            state=self.status(campaign_id)
            if state['token_ceiling']!=expected_ceiling:raise PolicyError('Token extension must bind the exact previous ceiling')
            if state['reserved_tokens']:raise PolicyError('Wait for the active call to settle')
            extension=self.store.record('campaign_token_extension',{'campaign_id':campaign_id,'tokens':tokens,
                'previous_ceiling':expected_ceiling,'consent':consent,'deadline_unchanged':state['deadline']})
            self.store.event('campaign:'+campaign_id,'token_extension_authorized',extension)
            self.store.db.execute('COMMIT')
        except BaseException:self.store.db.execute('ROLLBACK');raise
        return self.status(campaign_id)

    def extend_time(self,campaign_id,seconds,expected_deadline,consent,resume_after_expiry=False):
        """Explicit additional time, retaining the original token ledger and start."""
        if type(resume_after_expiry) is not bool:raise PolicyError('Explicit resume policy required')
        if type(seconds) is not int or seconds<=0 or not isinstance(consent,str) or not consent.strip():
            raise PolicyError('Positive extension and explicit authorization required')
        self.store.db.execute('BEGIN IMMEDIATE')
        try:
            state=self.status(campaign_id)
            if state['deadline'] is None or state['deadline']!=expected_deadline:
                raise PolicyError('Extension must bind the exact existing campaign deadline')
            if state['reserved_tokens']:raise PolicyError('Stop the active call before extending time')
            extension=self.store.record('campaign_time_extension',{'campaign_id':campaign_id,'seconds':seconds,
                'previous_deadline':expected_deadline,'consent':consent,'token_ceiling_unchanged':state['token_ceiling'],
                'expired_wait_seconds':max(0,time.time()-expected_deadline) if resume_after_expiry else 0,
                'resume_after_expiry':resume_after_expiry})
            self.store.event('campaign:'+campaign_id,'time_extension_authorized',extension)
            self.store.db.execute('COMMIT')
        except BaseException:self.store.db.execute('ROLLBACK');raise
        return self.status(campaign_id)

    def reserve(self,campaign_id,tokens):
        if type(tokens) is not int or tokens <= 0:raise PolicyError('Positive call reservation required')
        self.store.db.execute('BEGIN IMMEDIATE')
        try:
            state=self.status(campaign_id)
            estimate_headroom=state['failure_policy']['debit_per_failure'] if state.get('failure_policy') else 0
            if state['continuation_remaining_tokens'] is not None and tokens+estimate_headroom>state['continuation_remaining_tokens']:
                raise PolicyError('Authorized continuation token allowance exhausted; aggregate cap is unchanged')
            if state['control_state']!='ACTIVE' or state['remaining_tokens'] is None or tokens + estimate_headroom > state['remaining_tokens'] or state['remaining_seconds']<=0:
                raise PolicyError('Campaign allowance exhausted or uncertain; explicit extension/reconciliation required')
            if state['reserved_tokens']:raise PolicyError('Only one paid call may be in flight')
            call_id=uuid.uuid4().hex
            self.store.db.execute('UPDATE campaigns SET started=COALESCE(started,?),reserved_tokens=reserved_tokens+? WHERE id=?',
                                  (time.time(),tokens,campaign_id))
            self.store.db.execute('INSERT INTO campaign_calls VALUES(?,?,?,0)',(call_id,campaign_id,tokens))
            self.store.event('campaign:'+campaign_id,'reserved',{'call_id':call_id,'tokens':tokens})
            self.store.db.execute('COMMIT');return call_id
        except BaseException:self.store.db.execute('ROLLBACK');raise

    def settle(self,call_id,usage,complete):
        if type(complete) is not bool:raise PolicyError('Usage completeness required')
        if not isinstance(usage,dict) or any(type(usage.get(k)) is not int or usage[k]<0 for k in ('input_tokens','cached_input_tokens','output_tokens')):
            raise PolicyError('Known usage must be nonnegative integer counts')
        if usage['cached_input_tokens']>usage['input_tokens']:raise PolicyError('Cached input is a subset')
        total=usage['input_tokens']+usage['output_tokens']
        self.store.db.execute('BEGIN IMMEDIATE')
        try:
            row=self.store.db.execute('SELECT * FROM campaign_calls WHERE id=?',(call_id,)).fetchone()
            if row is None or row['settled']:raise PolicyError('Unknown or already settled call')
            self.store.db.execute('UPDATE campaigns SET used_tokens=used_tokens+?,reserved_tokens=reserved_tokens-?,usage_unknown=MAX(usage_unknown,?) WHERE id=?',
                                  (total,row['reserved'],int(not complete),row['campaign_id']))
            self.store.db.execute('UPDATE campaign_calls SET settled=1 WHERE id=?',(call_id,))
            self.store.db.execute('INSERT INTO campaign_usage VALUES(?,?,?)',(call_id,int(complete),total))
            self.store.event('campaign:'+row['campaign_id'],'usage',{'call_id':call_id,'usage':usage,'usage_complete':complete,
                                                                  'reservation_overshoot':max(0,total-row['reserved'])})
            self.store.db.execute('COMMIT')
        except BaseException:self.store.db.execute('ROLLBACK');raise
        return self.status(row['campaign_id'])

    def reconcile_estimate(self,call_id,debit,consent):
        """Human-approved extra debit; preserves unknown actual usage in immutable evidence."""
        if type(debit) is not int or debit <= 0 or not isinstance(consent,str) or not consent.strip():
            raise PolicyError('Positive conservative debit and explicit consent required')
        self.store.db.execute('BEGIN IMMEDIATE')
        try:
            call=self.store.db.execute('SELECT * FROM campaign_calls WHERE id=?',(call_id,)).fetchone()
            if call is None or not call['settled']:raise PolicyError('Settle the stopped call first')
            usage=self.store.db.execute('SELECT * FROM campaign_usage WHERE call_id=?',(call_id,)).fetchone()
            if usage is None:
                # Upgrade a pre-migration ledger only from its immutable completed call record.
                evidence=[r for r in self.store.records('model_call') if r['call_id']==call_id]
                if len(evidence)!=1:raise PolicyError('Missing exact call evidence')
                r=evidence[0]['result'];known=r['usage']['input_tokens']+r['usage']['output_tokens']
                self.store.db.execute('INSERT INTO campaign_usage VALUES(?,?,?)',(call_id,int(r['usage_complete']),known))
                usage=self.store.db.execute('SELECT * FROM campaign_usage WHERE call_id=?',(call_id,)).fetchone()
            if usage['complete']:raise PolicyError('Measured usage cannot be replaced with an estimate')
            if self.store.db.execute('SELECT 1 FROM campaign_adjustments WHERE call_id=?',(call_id,)).fetchone():
                raise PolicyError('Call already reconciled; no repeat debit or reset')
            if debit<call['reserved']:raise PolicyError('Conservative debit must cover the original reservation')
            self.store.db.execute('INSERT INTO campaign_adjustments VALUES(?,?,?)',(call_id,debit,consent))
            unresolved=self.store.db.execute("SELECT COUNT(*) FROM campaign_calls c LEFT JOIN campaign_usage u ON c.id=u.call_id LEFT JOIN campaign_adjustments a ON a.call_id=c.id WHERE c.campaign_id=? AND c.settled=1 AND (u.call_id IS NULL OR (u.complete=0 AND a.call_id IS NULL))",(call['campaign_id'],)).fetchone()[0]
            self.store.db.execute('UPDATE campaigns SET usage_unknown=? WHERE id=?',(int(bool(unresolved)),call['campaign_id']))
            self.store.event('campaign:'+call['campaign_id'],'estimated_usage_authorized',{'call_id':call_id,'extra_debit_tokens':debit,'actual_usage':'UNKNOWN','consent':consent,'hard_bound':False})
            self.store.db.execute('COMMIT')
        except BaseException:self.store.db.execute('ROLLBACK');raise
        return self.status(call['campaign_id'])
