; Source-backed bounds and ordering rule out simultaneous below-lower and above-upper guards.
(set-option :timeout 5000)
(set-logic ALL)
(declare-const lo Int) (declare-const hi Int) (declare-const current Int)
(define-fun source_environment ((l Int) (u Int)) Bool
 (and (<= 97 l) (<= l 99) (<= 98 u) (<= u 100) (<= l (- u 1))))
(assert (source_environment lo hi)) (assert (< current lo)) (assert (> current hi))
(check-sat)
