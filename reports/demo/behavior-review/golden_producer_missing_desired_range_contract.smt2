; Golden Operator_Interface GUMBO supplies no desired-range guarantees. With no such premise, composition cannot discharge the restored consumer assumptions.
(set-option :timeout 5000)
(set-logic ALL)
(declare-const lo Int) (declare-const hi Int) (declare-const current Int)
(define-fun source_environment ((l Int) (u Int)) Bool
 (and (<= 97 l) (<= l 99) (<= 98 u) (<= u 100) (<= l (- u 1))))
(assert (not (source_environment lo hi)))
(check-sat)
(get-model)
