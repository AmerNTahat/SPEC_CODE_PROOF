; Even zero execution/transport cost cannot ensure <500ms arbitrary-phase response for a1000ms polling stage.
(set-option :timeout 5000)
(set-logic ALL)
(declare-const arrival_phase_ms Real)
(assert (> arrival_phase_ms 0)) (assert (< arrival_phase_ms 1000))
(define-fun polling_wait_ms () Real (- 1000 arrival_phase_ms))
(assert (>= polling_wait_ms 500))
(check-sat)
(get-model)
