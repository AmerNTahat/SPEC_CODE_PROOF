# Regulate Temperature — draft derived description and requirements

## System description
The selected material defines Regulate_Temperature_i, a system intended to regulate air temperature. Its boundary includes four processes: regulator interface management, heat source management, regulator mode management, and internal failure detection. Each process contains a corresponding thread. The external operator interface supplies lower and upper desired temperatures with validity status and receives regulator status and a temperature value for display. An external temperature sensor supplies current temperature with validity status. The system supplies an on/off command to an external heat source. These input values are the monitored quantities at the modeled boundary; regulator status, displayed temperature, and the heat command are the controlled outputs. The material does not establish a physical temperature-maintenance performance guarantee. Internally, the interface manager supplies desired temperatures and an interface failure flag; the failure detector supplies an internal failure flag; and the mode manager supplies Init, Normal, or Failed mode. The heat manager determines specified heater commands from mode and temperature comparisons. All four threads are periodic with a 1000 ms period. Process/thread decomposition, typed data ports, connections, scheduling domains, and periods are source-defined implementation choices, distinct from the functional behavior expressed in comments and contracts. The requirements below are draft extractions from the selected source, not an independently established specification or a validation result.

## Requirements
REG-A01 [architecture]: The Regulate_Temperature_i system shall contain an mri component of type Manage_Regulator_Interface_Process.
REG-A02 [architecture]: The Regulate_Temperature_i system shall contain an mhs component of type Manage_Heat_Source_Process_i.
REG-A03 [architecture]: The Regulate_Temperature_i system shall contain an mrm component of type Manage_Regulator_Mode_Process_i.
REG-A04 [architecture]: The Regulate_Temperature_i system shall contain a drf component of type Detect_Regulator_Failure_Process_i.
REG-I01 [interface]: The system shall receive the operator interface's lower desired temperature with status through the input DataPort lower_desired_tempWstatus of type Isolette_Data_Model::TempWstatus_i.
REG-I02 [interface]: The system shall receive the operator interface's upper desired temperature with status through the input DataPort upper_desired_tempWstatus of type Isolette_Data_Model::TempWstatus_i.
REG-I03 [interface]: The system shall receive the temperature sensor's current temperature with status through the input DataPort current_tempWstatus of type Isolette_Data_Model::TempWstatus_i.
REG-I04 [interface]: The system shall provide regulator function status to the operator interface through the output DataPort regulator_status of type Isolette_Data_Model::Status.
REG-I05 [interface]: The system shall provide a current-temperature value for operator display through the output DataPort displayed_temp of type Isolette_Data_Model::Temp_i.
REG-I06 [interface]: The system shall provide the heater actuation command through the output DataPort heat_control of type Isolette_Data_Model::On_Off.
REG-C01 [architecture]: The system shall connect upper_desired_tempWstatus to the interface management process's upper_desired_tempWstatus input.
REG-C02 [architecture]: The system shall connect lower_desired_tempWstatus to the interface management process's lower_desired_tempWstatus input.
REG-C03 [architecture]: The system shall connect current_tempWstatus to the interface management process's current_tempWstatus input.
REG-C04 [architecture]: The system shall connect current_tempWstatus to the heat source management process's current_tempWstatus input.
REG-C05 [architecture]: The system shall connect current_tempWstatus to the mode management process's current_tempWstatus input.
REG-C06 [architecture]: The system shall connect the interface management process's displayed_temp output to the system's displayed_temp output.
REG-C07 [architecture]: The system shall connect the interface management process's regulator_status output to the system's regulator_status output.
REG-C08 [architecture]: The system shall connect the heat source management process's heat_control output to the system's heat_control output.
REG-C09 [architecture]: The system shall connect the interface management process's upper_desired_temp output to the heat source management process's upper_desired_temp input.
REG-C10 [architecture]: The system shall connect the interface management process's lower_desired_temp output to the heat source management process's lower_desired_temp input.
REG-C11 [architecture]: The system shall connect the mode management process's regulator_mode output to the interface management process's regulator_mode input.
REG-C12 [architecture]: The system shall connect the mode management process's regulator_mode output to the heat source management process's regulator_mode input.
REG-C13 [architecture]: The system shall connect the interface management process's interface_failure output to the mode management process's interface_failure input.
REG-C14 [architecture]: The system shall connect the failure detection process's internal_failure output to the mode management process's internal_failure input.
MRI-A01 [architecture]: The Manage_Regulator_Interface_Process process shall contain an mri thread of type Manage_Regulator_Interface_i.
MRI-I01 [interface]: The interface management process shall expose input DataPorts lower_desired_tempWstatus, upper_desired_tempWstatus, and current_tempWstatus of type Isolette_Data_Model::TempWstatus_i.
MRI-I02 [interface]: The interface management process shall expose an input DataPort regulator_mode of type Isolette_Data_Model::Regulator_Mode.
MRI-I03 [interface]: The interface management process shall expose output DataPorts lower_desired_temp, upper_desired_temp, and displayed_temp of type Isolette_Data_Model::Temp_i.
MRI-I04 [interface]: The interface management process shall expose an output DataPort regulator_status of type Isolette_Data_Model::Status.
MRI-I05 [interface]: The interface management process shall expose an output DataPort interface_failure of type Isolette_Data_Model::Failure_Flag_i to report improper inputs for mode determination.
MRI-I06 [interface]: The interface management thread shall expose the same nine named DataPorts, with the same directions and types, as its containing process: four inputs for the three temperatures with status and regulator mode, and five outputs for the desired temperatures, displayed temperature, regulator status, and interface failure.
MRI-C01 [architecture]: For each of lower_desired_tempWstatus, upper_desired_tempWstatus, current_tempWstatus, and regulator_mode, the interface management process shall connect its input port to the identically named input port of its contained mri thread.
MRI-C02 [architecture]: For each of lower_desired_temp, upper_desired_temp, displayed_temp, regulator_status, and interface_failure, the interface management process shall connect its contained mri thread's output port to the identically named process output port.
MRI-A02 [architecture]: The interface management process shall have CASE_Scheduling domain 3.
MRI-A03 [architecture]: The interface management thread shall have CASE_Scheduling domain 3.
MRI-T01 [timing]: The interface management thread shall use periodic dispatch with a period of 1000 milliseconds.
MRI-S01 [state]: At initialization, the interface management thread shall set regulator_status to Init_Status.
MRI-F01 [functional]: During computation, when regulator_mode is Init_Regulator_Mode, the interface management thread shall set regulator_status to Init_Status.
MRI-F02 [functional]: During computation, when regulator_mode is Normal_Regulator_Mode, the interface management thread shall set regulator_status to On_Status.
MRI-F03 [functional]: During computation, when regulator_mode is Failed_Regulator_Mode, the interface management thread shall set regulator_status to Failed_Status.
MRI-F04 [functional]: During computation, if either desired-temperature input has status Invalid, the interface management thread shall set interface_failure.flag to true.
MRI-F05 [functional]: During computation, if both desired-temperature inputs have status Valid, the interface management thread shall set interface_failure.flag to false.
MRI-F06 [functional]: During computation, when interface_failure.flag is false, the interface management thread shall set the degrees field of lower_desired_temp equal to the degrees field of lower_desired_tempWstatus.
MRI-F07 [functional]: During computation, when interface_failure.flag is false, the interface management thread shall set the degrees field of upper_desired_temp equal to the degrees field of upper_desired_tempWstatus.
MRM-A01 [architecture]: The Manage_Regulator_Mode_Process_i process shall contain an mrm thread of type Manage_Regulator_Mode_i.
MRM-I01 [interface]: The mode management process shall expose an input DataPort current_tempWstatus of type Isolette_Data_Model::TempWstatus_i.
MRM-I02 [interface]: The mode management process shall expose input DataPorts interface_failure and internal_failure of type Isolette_Data_Model::Failure_Flag_i.
MRM-I03 [interface]: The mode management process shall expose an output DataPort regulator_mode of type Isolette_Data_Model::Regulator_Mode.
MRM-I04 [interface]: The mode management thread shall expose the same four named DataPorts, with the same directions and types, as its containing process: current_tempWstatus, interface_failure, and internal_failure as inputs, and regulator_mode as output.
MRM-C01 [architecture]: For each of current_tempWstatus, interface_failure, and internal_failure, the mode management process shall connect its input port to the identically named input port of its contained mrm thread.
MRM-C02 [architecture]: The mode management process shall connect its contained mrm thread's regulator_mode output to the process's regulator_mode output.
MRM-A02 [architecture]: The mode management process shall have CASE_Scheduling domain 4.
MRM-A03 [architecture]: The mode management thread shall have CASE_Scheduling domain 4.
MRM-T01 [timing]: The mode management thread shall use periodic dispatch with a period of 1000 milliseconds.
MRM-S01 [state]: The mode management thread shall include a state variable lastRegulatorMode of type Isolette_Data_Model::Regulator_Mode.
MRM-S02 [state]: At initialization, the mode management thread shall set regulator_mode to Init_Regulator_Mode.
MRM-S03 [state]: During computation, when lastRegulatorMode is Init_Regulator_Mode, both failure flags are false, and current_tempWstatus.status is Valid, the mode management thread shall set regulator_mode to Normal_Regulator_Mode.
MRM-S04 [state]: During computation, when lastRegulatorMode is Init_Regulator_Mode and at least one of interface_failure.flag being true, internal_failure.flag being true, or current_tempWstatus.status being Invalid holds, the mode management thread shall set regulator_mode to Failed_Regulator_Mode.
MRM-S05 [state]: During computation, when lastRegulatorMode is Normal_Regulator_Mode, both failure flags are false, and current_tempWstatus.status is Valid, the mode management thread shall set regulator_mode to Normal_Regulator_Mode.
MRM-S06 [state]: During computation, when lastRegulatorMode is Normal_Regulator_Mode and at least one of interface_failure.flag being true, internal_failure.flag being true, or current_tempWstatus.status being Invalid holds, the mode management thread shall set regulator_mode to Failed_Regulator_Mode.
MRM-S07 [state]: During computation, when lastRegulatorMode is Failed_Regulator_Mode, the mode management thread shall set regulator_mode to Failed_Regulator_Mode.
MRM-S08 [state]: Once the regulator enters Failed mode, it shall remain in Failed mode until reboot, as stated by the source's descriptive requirement.
MHS-A01 [architecture]: The Manage_Heat_Source_Process_i process shall contain an mhs thread of type Manage_Heat_Source_i.
MHS-I01 [interface]: The heat source management process shall expose an input DataPort current_tempWstatus of type Isolette_Data_Model::TempWstatus_i.
MHS-I02 [interface]: The heat source management process shall expose input DataPorts lower_desired_temp and upper_desired_temp of type Isolette_Data_Model::Temp_i for the desired range bounds.
MHS-I03 [interface]: The heat source management process shall expose an input DataPort regulator_mode of type Isolette_Data_Model::Regulator_Mode.
MHS-I04 [interface]: The heat source management process shall expose an output DataPort heat_control of type Isolette_Data_Model::On_Off.
MHS-I05 [interface]: The heat source management thread shall expose the same five named DataPorts, with the same directions and types, as its containing process: current_tempWstatus, lower_desired_temp, upper_desired_temp, and regulator_mode as inputs, and heat_control as output.
MHS-C01 [architecture]: For each of current_tempWstatus, lower_desired_temp, upper_desired_temp, and regulator_mode, the heat source management process shall connect its input port to the identically named input port of its contained mhs thread.
MHS-C02 [architecture]: The heat source management process shall connect its contained mhs thread's heat_control output to the process's heat_control output.
MHS-A02 [architecture]: The heat source management process shall have CASE_Scheduling domain 5.
MHS-A03 [architecture]: The heat source management thread shall have CASE_Scheduling domain 5.
MHS-T01 [timing]: The heat source management thread shall use periodic dispatch with a period of 1000 milliseconds.
MHS-S01 [state]: At initialization, the heat source management thread shall set heat_control to Off.
MHS-F01 [functional]: During computation, when regulator_mode is Init_Regulator_Mode, the heat source management thread shall set heat_control to Off.
MHS-F02 [functional]: During computation, when regulator_mode is Normal_Regulator_Mode and the current-temperature degrees value is strictly less than the lower desired-temperature degrees value, the heat source management thread shall command heater on using heat_control value Onn.
MHS-F03 [functional]: During computation, when regulator_mode is Normal_Regulator_Mode and the current-temperature degrees value is strictly greater than the upper desired-temperature degrees value, the heat source management thread shall set heat_control to Off.
MHS-F04 [functional]: During computation, when regulator_mode is Failed_Regulator_Mode, the heat source management thread shall set heat_control to Off.
DRF-F01 [functional]: The regulator failure detection function shall identify internal failures in the Regulate Temperature function.
DRF-S01 [state]: The regulator failure detection function shall define a single Boolean-valued Regulator Internal Failure variable.
DRF-F02 [functional]: If an internal failure is detected, the regulator failure detection function shall set Regulator Internal Failure to true.
DRF-A01 [architecture]: The Detect_Regulator_Failure_Process_i process shall contain a drf thread of type Detect_Regulator_Failure_i.
DRF-I01 [interface]: The regulator failure detection process shall expose an output DataPort internal_failure of type Isolette_Data_Model::Failure_Flag_i.
DRF-I02 [interface]: The regulator failure detection thread shall expose an output DataPort internal_failure of type Isolette_Data_Model::Failure_Flag_i.
DRF-C01 [architecture]: The regulator failure detection process shall connect its contained drf thread's internal_failure output to the process's internal_failure output.
DRF-A02 [architecture]: The regulator failure detection process shall have CASE_Scheduling domain 6.
DRF-A03 [architecture]: The regulator failure detection thread shall have CASE_Scheduling domain 6.
DRF-T01 [timing]: The regulator failure detection thread shall use periodic dispatch with a period of 1000 milliseconds.

## Assumptions
No additional environmental assumptions are introduced. Contract case assumptions are translated as conditions on required behavior, not as promises that the environment always satisfies them.
The selected GUMBO contract text and descriptive comments are treated as sources of draft obligations; their presence does not establish implementation or validation.
The source's Onn enumeration value is described as heater on because its accompanying case description explicitly says On; the source spelling is preserved.
Repeated port and connection requirements use universal wording for the explicitly listed ports; no additional ports or connections are inferred.

## Unresolved questions
Lines 5–8 import external models whose definitions are absent. Temperature scale, numeric representation, resolution, admissible ranges, complete status and mode enumerations, failure-flag structure, and detailed DataPort semantics cannot be established.
The source calls the overall element a process in comments but declares it as a System at line 20. Components described as threads at lines 22–29 are declared process instances containing threads. The extracted architecture follows the declarations.
The source does not state temperature units beyond the field name degrees. Celsius, Fahrenheit, absolute limits, and safe desired ranges must not be inferred.
Lines 275–310 declare lastRegulatorMode and use it in transition conditions, but do not initialize it or specify how it is updated from regulator_mode. The intended previous-mode relationship is suggested by the case descriptions but is not fully defined.
Line 308 states that Failed mode persists until reboot, but no reboot input, reboot conditions, reset procedure, or explicit relationship between reboot and initialization is supplied.
Lines 169–215 declare displayed_temp but provide no computation rule for it. Copying current temperature, rounding, status handling, and display behavior in each mode are unspecified.
Lines 200–214 define interface failure for Invalid desired-temperature statuses and for two Valid statuses. Behavior for any other status values, if the imported type permits them, is unspecified.
Lines 210–214 do not constrain desired-temperature outputs when interface_failure.flag is true. Retention, replacement values, and output suppression are not specified.
No rule checks that the lower desired temperature is less than or equal to the upper desired temperature. Inverted bounds could make the heater-on and heater-off conditions simultaneously true; no conflict resolution or input restriction is given.
Lines 384–392 do not define the Normal-mode heater command when current temperature equals either bound or lies between the bounds. No hold-last-command or hysteresis behavior is supplied.
The Normal-mode heat-control conditions do not test current_tempWstatus.status. No direct heat-manager rule for Invalid current temperature is supplied; failure-dependent behavior relies on the received regulator mode, with propagation timing unspecified.
Initialization is specified only for regulator_status, regulator_mode, and heat_control. Initial displayed temperature, desired-temperature outputs, interface failure, internal failure, and lastRegulatorMode are unspecified.
Lines 408–410 give failure detection intent but no complete failure set, detection method, detection coverage, or detection deadline. The memory check failure is an example, not a specified mandatory test procedure.
The intended correspondence between the descriptive Boolean Regulator Internal Failure and internal_failure.flag is suggested by naming and use, but is not explicitly defined in the detector. The detector has no behavioral contract, no rule requiring false when no failure is detected, and no clearing or latching rule.
The 1000 ms periods do not specify execution-time bounds, deadlines, startup phase, jitter, thread ordering, synchronization, communication latency, or end-to-end reaction time. Scheduling domain numbers alone do not establish execution order.
Port connections identify endpoints but do not establish transport protocols, buffering, sampling, freshness, physical interfaces, sensor accuracy, heater response, or operator-interface presentation.
The material supplies no quantitative air-temperature regulation performance, environmental operating conditions, or explicit safety goal. Such facts cannot be imported from the style-guide example.
Applied-rule comments and AR-08-32 trace labels occur in the source, but no rulebook, generated validation output, or referenced requirement bodies are supplied. Completeness, port compatibility, and conformance to those external references remain unverified.
