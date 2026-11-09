; The proposed hold-last-valid refinement preserves ordered bounds even during invalid-input propagation, assuming a valid initial stored pair and source-backed valid inputs.
(set-option :timeout 5000)
(set-logic ALL)
(declare-const lo Int) (declare-const hi Int) (declare-const current Int)
(define-fun source_environment ((l Int) (u Int)) Bool
 (and (<= 97 l) (<= l 99) (<= 98 u) (<= u 100) (<= l (- u 1))))
(declare-const old_lo Int) (declare-const old_hi Int) (declare-const valid Bool)
(assert (source_environment old_lo old_hi))
(assert (=> valid (source_environment lo hi)))
(define-fun next_lo () Int (ite valid lo old_lo))
(define-fun next_hi () Int (ite valid hi old_hi))
(assert (not (source_environment next_lo next_hi)))
(check-sat)
