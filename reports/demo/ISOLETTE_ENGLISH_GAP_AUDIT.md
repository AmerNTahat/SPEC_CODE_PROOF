# Isolette: English, reference and generated-model gap audit

The generated model has not satisfied all English requirements. This audit separates structural design decisions from missing behavioral evidence. The golden reference is also incomplete and is not the authority for weakening FAA requirements.

## Regulator category and wrappers

English: A.5.1 allocates four subfunctions; it does not say System -> four Process wrappers -> one Thread each.

Reference: Regulate_Temperature_i is a System with four Process children, each with one Thread.

Generated: Regulate_Temperature_i is one Process directly containing the four Threads.

Assessment: Underspecified reconstruction input; not evidence of a missing functional requirement.

## Nineteen wrapper ports and forwarding connections

English: Figure A-3 and A.5.1.1–4 describe role-to-role data flow, not the additional wrapper layer.

Reference: Process wrappers have9+4+5+1=19 ports and19 forwarding connections.

Generated: Direct Threads retain the functional paths without this layer.

Assessment: Same architectural input gap; connectivity/type checks still required.

## Periodic1000ms and domains3/4/5/6

English: English gives end-to-end response <0.5s and heat response <6s, not these deployment values.

Reference: Four periodic threads,1000ms; domains3,4,5,6 on owning processes and threads.

Generated: No declared dispatch/period/domain; explicit unresolved deployment note.

Assessment: Reference design decisions absent from English.1000ms periodic sampling may conflict with <0.5s response; do not silently treat reference as requirement authority.

## Display rounding and accuracy

English: REQ-MRI-4 and Display Temperature latency/tolerance require nearest integer and physical accuracy±0.6°F.

Reference: No REQ_MRI_4 executable contract in this reference.

Generated: REQ_MRI_4 copies the shared Integer_32 degrees value and explicitly leaves physical reconstruction/rounding unresolved.

Assessment: Partial representation/integration gap, not a missing English requirement; no proof of physical fidelity.

## Heat command retention

English: REQ-MHS-4: retain Heat Control between inclusive bounds.

Reference: No REQ_MHS_4 contract in the reference.

Generated: REQ_MHS_4 plus Previous_Heat_Control initialization and commit are present.

Assessment: Generated contract covers a clause missing from the reference contract set; behavioral correctness still needs proof/tests.

## Init timeout and elapsed-time progress

English: Table A-9 and Figure A-4 define1.0s regulator initialization timeout.

Reference: Fails immediately on unhealthy INIT; no elapsed-time state, and lastRegulatorMode lifecycle is incomplete.

Generated: Contains REQ_MRM_4 and clock constraints, but admits a frozen clock and lacks actual time acquisition.

Assessment: Partial formalization/implementation gap; generated text acknowledges missing progress. Healthy INIT plus expired timeout also needs guard-overlap review.

## Response latency and implementation

English: Operator-visible response<0.5s; heat-source response<6s.

Reference: Periodic1000ms declarations do not establish these end-to-end bounds.

Generated: Requirements are retained as prose obligations; no scheduling/implementation/runtime evidence discharges them.

Assessment: Known unmet validation obligations, not absence of English.

## Failure detection criteria

English: A.5.1.4 says detailed requirements cannot be specified until an implementation platform is chosen.

Reference: Failure output Thread has no detection behavior.

Generated: Implication from an internal-detection predicate; predicate updates/coverage remain open.

Assessment: Source intentionally leaves design work; do not invent diagnostic behavior or claim complete implementation.

## Why the earlier attempt failed

Reconstruction demanded unstated deployment structure while only a local behavior rule was selected. This is an input/specification and rule-selection mismatch, not just renaming. Intentional deferral of unsupported scheduling is visible in the generated source; the agent internal cause cannot be proven.

The FAA Figure A-3 text extraction is visibly fragmented. The revised English states the independently reviewed role/flow interpretation explicitly rather than treating OCR layout as a reliable architecture prescription.
