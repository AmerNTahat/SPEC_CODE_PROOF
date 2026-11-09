; At exactly1.0s an unhealthy INIT does not time out: retain source strict greater-than.
(set-option :timeout 5000)
(set-logic ALL)
(declare-datatypes () ((Mode INIT NORMAL FAILED)))
(declare-const previous Mode) (declare-const healthy Bool) (declare-const elapsed Real)
(assert (>= elapsed 0))
(define-fun allowed ((next Mode)) Bool
 (and
  (=> (and (= previous INIT) (> elapsed 1)) (= next FAILED))
  (=> (and (= previous INIT) (<= elapsed 1) healthy) (= next NORMAL))
  (=> (and (= previous INIT) (<= elapsed 1) (not healthy)) (= next INIT))
  (=> (and (= previous NORMAL) healthy) (= next NORMAL))
  (=> (and (= previous NORMAL) (not healthy)) (= next FAILED))
  (=> (= previous FAILED) (= next FAILED))))
(assert (= previous INIT)) (assert (= elapsed 1)) (assert (not healthy)) (assert (allowed FAILED))
(check-sat)
