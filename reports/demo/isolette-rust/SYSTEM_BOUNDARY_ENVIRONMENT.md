# Approved system-boundary environmental assumption

EA-OI-6-ORDERING is now explicitly allocated to the external environment:

> The operator/environment supplies desired-temperature settings with Lower Desired Temperature strictly less than Upper Desired Temperature.

This is a condition of the system's acceptance, not a requirement for software to prove that the external world complies. The source is FAA AR-08-32 EA-OI-6 (PDF102 / printedA11), explicitly listed among environmental assumptions. The user approved this boundary allocation. No other FAA assumptions or exact one-degree margin have been silently added.

At the modeled Isolette boundary, operator_commands is abstract and does not expose separate degree fields. The concrete software boundary is the thermostat's lower_desired_tempWstatus and upper_desired_tempWstatus inputs. The workbench boundary contract records these bindings and the heat component's ORDERED_DESIRED_BOUNDS precondition explicitly in ENVIRONMENTAL_ASSUMPTIONS.json next to the repaired model.

The accepted heat repair remains conditional on that premise. Its checked SysML/Rust artifacts are unchanged, so the previously executed11-Verus/5-test results retain their original identity. No new formal system-composition proof was run for this declaration.

The old obligation to prove external establishment of ordering is superseded by this human-approved environmental premise. A separate internal obligation remains: ensure the interface preserves the assumption through initialization and invalid-status handling before the heat component consumes it. REQ_MRI_8 currently constrains copying only when the interface-failure flag is false; input ordering does not by itself prove every internal output pair is ordered. This is an internal propagation check, not a request to reapprove the external assumption.

UI/validation now lists this as an approved environmental assumption, separate from software guarantees and open internal obligations. It neither contributes proof units nor grants whole-system acceptance. The accepted repaired-golden-defect case count remains one.
