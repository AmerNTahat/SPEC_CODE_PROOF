; Proposed initial stored pair97/98 is within the source domains; values are a design choice for review, not mandated initial outputs.
(set-option :timeout 5000)
(set-logic ALL)
(declare-const lo Int) (declare-const hi Int) (declare-const current Int)
(define-fun source_environment ((l Int) (u Int)) Bool
 (and (<= 97 l) (<= l 99) (<= 98 u) (<= u 100) (<= l (- u 1))))
(assert (not (source_environment 97 98)))
(check-sat)
