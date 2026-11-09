; Nonnegative monotonicity alone admits a frozen clock; an actual clock/progress obligation is necessary.
(set-option :timeout 5000)
(set-logic ALL)
(declare-const before Real) (declare-const after Real) (assert (>= before 0)) (assert (>= after before)) (assert (= before after))
(check-sat)
(get-model)
