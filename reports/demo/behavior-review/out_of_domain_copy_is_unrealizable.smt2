; A hypothetical Valid input200 cannot satisfy both unconditional copying and TableA7. TableA5 excludes this environmental witness.
(set-option :timeout 5000)
(set-logic ALL)
(declare-const lo Int) (declare-const hi Int) (declare-const current Int)
(define-fun source_environment ((l Int) (u Int)) Bool
 (and (<= 97 l) (<= l 99) (<= 98 u) (<= u 100) (<= l (- u 1))))
(declare-const copied Int) (assert (= lo 200)) (assert (= copied lo)) (assert (and (<= 96 copied) (<= copied 101)))
(check-sat)
