(set-logic QF_LIA)
(declare-const external_lower Int)
(declare-const external_upper Int)
(declare-const internal_lower Int)
(declare-const internal_upper Int)
(declare-const interface_failure Bool)
; Approved environmental ordering, assumed, not proved.
(assert (< external_lower external_upper))
; MRI8: a healthy interface forwards the same quantities.
(assert (=> (not interface_failure)
  (and (= internal_lower external_lower) (= internal_upper external_upper))))
; Internal TableA7 domains. MRI9 otherwise leaves the range unspecified.
(assert (and (<= 96 internal_lower) (<= internal_lower 101)))
(assert (and (<= 97 internal_upper) (<= internal_upper 102)))
(assert (not interface_failure))
(assert (not (< internal_lower internal_upper)))
(check-sat)
