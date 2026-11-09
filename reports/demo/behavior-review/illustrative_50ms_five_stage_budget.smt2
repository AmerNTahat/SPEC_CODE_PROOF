; Conditional arithmetic only: five<=50ms waits plus<=200ms other cost gives<=450ms. Actual path count, WCET, jitter, transport and rendering bounds are not measured or established.
(set-option :timeout 5000)
(set-logic ALL)
(declare-const w1 Real) (declare-const w2 Real) (declare-const w3 Real) (declare-const w4 Real) (declare-const w5 Real) (declare-const other_cost_ms Real)
(assert (and (<= 0 w1) (<= w1 50) (<= 0 w2) (<= w2 50) (<= 0 w3) (<= w3 50) (<= 0 w4) (<= w4 50) (<= 0 w5) (<= w5 50) (<= 0 other_cost_ms) (<= other_cost_ms 200)))
(assert (>= (+ w1 w2 w3 w4 w5 other_cost_ms) 500))
(check-sat)
