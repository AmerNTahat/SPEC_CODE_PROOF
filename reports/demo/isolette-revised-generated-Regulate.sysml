// Regulate.sysml
package Regulate {
    private import AADL::*;
    private import Isolette_Data_Model::*;
    private import HAMR_Time_Units::*;

    doc /* Proposed reconstruction for review. ARCH-R-1..4 establish the
     * System/Process/Thread architecture and reference deployment properties.
     * FAA behavior remains authoritative. No verification result is asserted.
     * Contracts constrain thread implementations; they are not thread bodies.
     * All enabled guarantees apply simultaneously, without textual priority. */

    part def Manage_Regulator_Interface_i :> AADL::Thread {
        attribute :>> Dispatch_Protocol = AADL_Project::Supported_Dispatch_Protocols::Periodic;
        attribute :>> Period = 1000 [ms];
        attribute Domain : CASE_Scheduling::Domain = 3;

        port Current_Temperature : AADL::DataPort { in :>> type : Isolette_Data_Model::TempWstatus_i; }
        port Lower_Desired_Temperature : AADL::DataPort { in :>> type : Isolette_Data_Model::TempWstatus_i; }
        port Upper_Desired_Temperature : AADL::DataPort { in :>> type : Isolette_Data_Model::TempWstatus_i; }
        port Regulator_Mode : AADL::DataPort { in :>> type : Isolette_Data_Model::Regulator_Mode; }
        port Regulator_Status : AADL::DataPort { out :>> type : Isolette_Data_Model::Status; }
        port Display_Temperature : AADL::DataPort { out :>> type : Isolette_Data_Model::Temp_i; }
        port Lower_Desired_Temp : AADL::DataPort { out :>> type : Isolette_Data_Model::Temp_i; }
        port Upper_Desired_Temp : AADL::DataPort { out :>> type : Isolette_Data_Model::Temp_i; }
        port Regulator_Interface_Failure : AADL::DataPort { out :>> type : Isolette_Data_Model::Failure_Flag_i; }

        attribute Max_Operator_Response_Time : ScalarValues::Real = 0.5;

        language "GUMBO" /*{
            initialize
                guarantee MRI_INITIAL_STATUS:
                    Regulator_Status == Isolette_Data_Model::Status::Init_Status;
                guarantee MRI_INITIAL_FAILURE:
                    Regulator_Interface_Failure.flag;
                guarantee MRI_INITIAL_LOWER_DOMAIN:
                    96 [s32] <= Lower_Desired_Temp.degrees and Lower_Desired_Temp.degrees <= 101 [s32];
                guarantee MRI_INITIAL_UPPER_DOMAIN:
                    97 [s32] <= Upper_Desired_Temp.degrees and Upper_Desired_Temp.degrees <= 102 [s32];
                guarantee MRI_INITIAL_DISPLAY_DOMAIN:
                    -128 [s32] <= Display_Temperature.degrees and Display_Temperature.degrees <= 134 [s32];
            compute
                guarantee REQ_MRI_1:
                    (Regulator_Mode == Isolette_Data_Model::Regulator_Mode::Init_Regulator_Mode) implies
                    (Regulator_Status == Isolette_Data_Model::Status::Init_Status);
                guarantee REQ_MRI_2:
                    (Regulator_Mode == Isolette_Data_Model::Regulator_Mode::Normal_Regulator_Mode) implies
                    (Regulator_Status == Isolette_Data_Model::Status::On_Status);
                guarantee REQ_MRI_3:
                    (Regulator_Mode == Isolette_Data_Model::Regulator_Mode::Failed_Regulator_Mode) implies
                    (Regulator_Status == Isolette_Data_Model::Status::Failed_Status);
                guarantee REQ_MRI_4:
                    (Regulator_Mode == Isolette_Data_Model::Regulator_Mode::Normal_Regulator_Mode) implies
                    (Display_Temperature.degrees == Current_Temperature.degrees);
                guarantee REQ_MRI_6:
                    (Lower_Desired_Temperature.status == Isolette_Data_Model::ValueStatus::Invalid or
                     Upper_Desired_Temperature.status == Isolette_Data_Model::ValueStatus::Invalid) implies
                    Regulator_Interface_Failure.flag;
                guarantee REQ_MRI_7:
                    (Lower_Desired_Temperature.status == Isolette_Data_Model::ValueStatus::Valid and
                     Upper_Desired_Temperature.status == Isolette_Data_Model::ValueStatus::Valid) implies
                    (not Regulator_Interface_Failure.flag);
                guarantee REQ_MRI_8:
                    (not Regulator_Interface_Failure.flag) implies
                    (Lower_Desired_Temp.degrees == Lower_Desired_Temperature.degrees and
                     Upper_Desired_Temp.degrees == Upper_Desired_Temperature.degrees);
                guarantee TABLE_A7_LOWER_DOMAIN:
                    96 [s32] <= Lower_Desired_Temp.degrees and Lower_Desired_Temp.degrees <= 101 [s32];
                guarantee TABLE_A7_UPPER_DOMAIN:
                    97 [s32] <= Upper_Desired_Temp.degrees and Upper_Desired_Temp.degrees <= 102 [s32];
        }*/

        requirement 'REQ-MRI-5' {
            doc /* Outside NORMAL, Display Temperature is UNSPECIFIED within
             * its payload domain. The compute contract deliberately imposes
             * no value or retention relation there. Initialize must publish
             * a representable value, without reading any input port. */
        }
        requirement 'REQ-MRI-9' {
            doc /* On interface failure, Desired Range is UNSPECIFIED within
             * Table A-7 domains. REQ_MRI_8 imposes no copying relation then.
             * Consumers must not rely on failed-interface ranges. Establish
             * this across failure propagation, mode feedback and sampling;
             * the heat thread has no direct interface-failure input. */
        }
        requirement Interface_Initialization {
            doc /* External producers must initially supply Invalid statuses
             * on both desired-temperature inputs. The initial failure output
             * is true and initial status is Init without reading inputs.
             * Every output DataPort must be published during initialization;
             * unconstrained values are not permission to omit publication. */
        }
        requirement Display_Physical_Mapping {
            doc /* REQ-MRI-4 requires nearest-integer Fahrenheit rounding.
             * Equality in REQ_MRI_4 implements rounding only on the supplied
             * integer-valued abstraction. It does not establish a mapping
             * from fractional sensor measurements. Resolve representation,
             * rounding ties and EA-TS-2 before claiming physical refinement.
             * Preserve display accuracy +/-0.6 degrees F and sensor accuracy
             * and resolution 0.1 degrees F; do not silently rescale degrees. */
        }
        requirement Interface_Response {
            doc /* Table A-8 Max Operator Response Time is 0.5 seconds.
             * REQ-MRI-1..5 retain strictly less than 0.5 seconds visible
             * response. Status tolerance is N/A; display tolerance is
             * +/-0.6 degrees F. Include acquisition, computation, transport
             * and Operator Interface rendering. The 1000 ms reference period
             * is incompatible with guaranteeing this bound for arbitrary
             * arrival phases under ordinary periodic sampling. This remains
             * an unresolved deployment conflict, not a relaxed deadline. */
        }
        requirement Desired_Range_Compatibility {
            doc /* Table A-7 lower [96..101] and upper [97..102] guarantees
             * coexist with conditional copying. Valid monitored values
             * outside those domains make these guarantees incompatible.
             * Establish a justified external domain or resolve requirements;
             * no global Valid-status or range-order assumption is introduced. */
        }
    }

    part def Manage_Regulator_Mode_i :> AADL::Thread {
        attribute :>> Dispatch_Protocol = AADL_Project::Supported_Dispatch_Protocols::Periodic;
        attribute :>> Period = 1000 [ms];
        attribute Domain : CASE_Scheduling::Domain = 4;

        port Current_Temperature : AADL::DataPort { in :>> type : Isolette_Data_Model::TempWstatus_i; }
        port Regulator_Interface_Failure : AADL::DataPort { in :>> type : Isolette_Data_Model::Failure_Flag_i; }
        port Regulator_Internal_Failure : AADL::DataPort { in :>> type : Isolette_Data_Model::Failure_Flag_i; }
        port Regulator_Mode : AADL::DataPort { out :>> type : Isolette_Data_Model::Regulator_Mode; }

        attribute Regulator_Init_Timeout : ScalarValues::Real = 1.0;

        language "GUMBO" /*{
            state
                Previous_Regulator_Mode : Isolette_Data_Model::Regulator_Mode;
                Regulator_Status : Base_Types::Boolean;
                Duration_INMODE : Base_Types::Float_64;
            initialize
                guarantee REQ_MRM_1:
                    Regulator_Mode == Isolette_Data_Model::Regulator_Mode::Init_Regulator_Mode;
                guarantee MODE_INITIAL_HISTORY:
                    Previous_Regulator_Mode == Isolette_Data_Model::Regulator_Mode::Init_Regulator_Mode;
                guarantee MODE_INITIAL_CLOCK:
                    Duration_INMODE == 0.0;
                guarantee MODE_INITIAL_HEALTH:
                    not Regulator_Status;
            compute
                guarantee TABLE_A10_REGULATOR_STATUS:
                    Regulator_Status ==
                    (not (Regulator_Interface_Failure.flag or Regulator_Internal_Failure.flag) and
                     Current_Temperature.status == Isolette_Data_Model::ValueStatus::Valid);
                guarantee REQ_MRM_2:
                    (In(Previous_Regulator_Mode) == Isolette_Data_Model::Regulator_Mode::Init_Regulator_Mode and
                     Regulator_Status) implies
                    (Regulator_Mode == Isolette_Data_Model::Regulator_Mode::Normal_Regulator_Mode);
                guarantee REQ_MRM_3:
                    (In(Previous_Regulator_Mode) == Isolette_Data_Model::Regulator_Mode::Normal_Regulator_Mode and
                     not Regulator_Status) implies
                    (Regulator_Mode == Isolette_Data_Model::Regulator_Mode::Failed_Regulator_Mode);
                guarantee REQ_MRM_4:
                    (In(Previous_Regulator_Mode) == Isolette_Data_Model::Regulator_Mode::Init_Regulator_Mode and
                     In(Duration_INMODE) > 1.0) implies
                    (Regulator_Mode == Isolette_Data_Model::Regulator_Mode::Failed_Regulator_Mode);
                guarantee INIT_PERSISTENCE:
                    (In(Previous_Regulator_Mode) == Isolette_Data_Model::Regulator_Mode::Init_Regulator_Mode and
                     not Regulator_Status and In(Duration_INMODE) <= 1.0) implies
                    (Regulator_Mode == Isolette_Data_Model::Regulator_Mode::Init_Regulator_Mode);
                guarantee NORMAL_PERSISTENCE:
                    (In(Previous_Regulator_Mode) == Isolette_Data_Model::Regulator_Mode::Normal_Regulator_Mode and
                     Regulator_Status) implies
                    (Regulator_Mode == Isolette_Data_Model::Regulator_Mode::Normal_Regulator_Mode);
                guarantee FAILED_LATCH:
                    (In(Previous_Regulator_Mode) == Isolette_Data_Model::Regulator_Mode::Failed_Regulator_Mode) implies
                    (Regulator_Mode == Isolette_Data_Model::Regulator_Mode::Failed_Regulator_Mode);
                guarantee MODE_HISTORY_COMMIT:
                    Previous_Regulator_Mode == Regulator_Mode;
                guarantee CLOCK_NONNEGATIVE:
                    Duration_INMODE >= 0.0;
                guarantee CLOCK_ENTRY_RESET:
                    (Regulator_Mode != In(Previous_Regulator_Mode)) implies
                    (Duration_INMODE == 0.0);
                guarantee CLOCK_NONDECREASING_WITHIN_MODE:
                    (Regulator_Mode == In(Previous_Regulator_Mode)) implies
                    (Duration_INMODE >= In(Duration_INMODE));
        }*/

        requirement Mode_Clock_Integration {
            doc /* Duration_INMODE denotes elapsed residence time in seconds.
             * The executable reset and monotonicity predicates do not supply
             * a clock or exclude frozen time. Integrate actual elapsed time
             * at guard evaluation, with coherent pre-state snapshots and
             * finite numeric values. Do not substitute the dispatch count
             * for elapsed time. The >1.0 second timeout and negligible-time
             * transition abstraction remain physical implementation/proof
             * obligations under the 1000 ms sampled execution. */
        }
        requirement Mode_Compatibility {
            doc /* Healthy INIT with elapsed duration >1.0 simultaneously
             * enables Req MRM 2 and Req MRM 4, demanding NORMAL and FAILED.
             * Resolve transition priority or prove this overlap unreachable
             * from justified execution semantics. No priority or assumption
             * is invented. FAILED persists until power-cycle initialization.
             * The Table A-10 Boolean health variable is distinct from the
             * enumerated Regulator Status produced by the interface thread.
             * Initial health is false because initial interface failure is
             * true; initialization reads no input ports. */
        }
    }

    part def Manage_Heat_Source_i :> AADL::Thread {
        attribute :>> Dispatch_Protocol = AADL_Project::Supported_Dispatch_Protocols::Periodic;
        attribute :>> Period = 1000 [ms];
        attribute Domain : CASE_Scheduling::Domain = 5;

        port Current_Temperature : AADL::DataPort { in :>> type : Isolette_Data_Model::TempWstatus_i; }
        port Lower_Desired_Temp : AADL::DataPort { in :>> type : Isolette_Data_Model::Temp_i; }
        port Upper_Desired_Temp : AADL::DataPort { in :>> type : Isolette_Data_Model::Temp_i; }
        port Regulator_Mode : AADL::DataPort { in :>> type : Isolette_Data_Model::Regulator_Mode; }
        port Heat_Control : AADL::DataPort { out :>> type : Isolette_Data_Model::On_Off; }

        attribute Allowed_Heat_Source_Latency : ScalarValues::Real = 6.0;

        language "GUMBO" /*{
            state
                Previous_Heat_Control : Isolette_Data_Model::On_Off;
            initialize
                guarantee INITIAL_HEAT_OFF:
                    Heat_Control == Isolette_Data_Model::On_Off::Off;
                guarantee INITIAL_HEAT_HISTORY:
                    Previous_Heat_Control == Isolette_Data_Model::On_Off::Off;
            compute
                guarantee REQ_MHS_1:
                    (Regulator_Mode == Isolette_Data_Model::Regulator_Mode::Init_Regulator_Mode) implies
                    (Heat_Control == Isolette_Data_Model::On_Off::Off);
                guarantee REQ_MHS_2:
                    (Regulator_Mode == Isolette_Data_Model::Regulator_Mode::Normal_Regulator_Mode and
                     Current_Temperature.degrees < Lower_Desired_Temp.degrees) implies
                    (Heat_Control == Isolette_Data_Model::On_Off::Onn);
                guarantee REQ_MHS_3:
                    (Regulator_Mode == Isolette_Data_Model::Regulator_Mode::Normal_Regulator_Mode and
                     Current_Temperature.degrees > Upper_Desired_Temp.degrees) implies
                    (Heat_Control == Isolette_Data_Model::On_Off::Off);
                guarantee REQ_MHS_4:
                    (Regulator_Mode == Isolette_Data_Model::Regulator_Mode::Normal_Regulator_Mode and
                     Current_Temperature.degrees >= Lower_Desired_Temp.degrees and
                     Current_Temperature.degrees <= Upper_Desired_Temp.degrees) implies
                    (Heat_Control == In(Previous_Heat_Control));
                guarantee REQ_MHS_5:
                    (Regulator_Mode == Isolette_Data_Model::Regulator_Mode::Failed_Regulator_Mode) implies
                    (Heat_Control == Isolette_Data_Model::On_Off::Off);
                guarantee HEAT_HISTORY_COMMIT:
                    Previous_Heat_Control == Heat_Control;
        }*/

        requirement Heat_History_Implementation {
            doc /* Initialize output and history to Off. Read frozen inputs
             * and preceding history, compute, then publish output and commit
             * matching history. Both exact bounds retain the previous heat
             * command. No sensor-validity guard excludes required behavior.
             * FAA endpoint inequalities govern despite the informal rationale
             * referring to reaching a threshold. */
        }
        requirement Heat_Compatibility {
            doc /* If upper < current < lower in NORMAL, REQ-MHS-2 and
             * REQ-MHS-3 demand contradictory commands. Table A-7 alone does
             * not establish ordering. Resolve the domain/composition gap;
             * do not silently sort bounds, add priority or assume it away. */
        }
        requirement Heat_Response {
            doc /* REQ-MHS-1..5 retain response strictly less than 6.0 seconds,
             * tolerance N/A, including sampling, transport and actuation.
             * EA-IS1 and EA-IS2 bound temperature change by 1 degree F/minute;
             * six seconds corresponds to 0.1 degree F, as referenced by EA-TS2.
             * The reference period alone establishes no end-to-end bound. */
        }
    }

    part def Detect_Regulator_Failure_i :> AADL::Thread {
        attribute :>> Dispatch_Protocol = AADL_Project::Supported_Dispatch_Protocols::Periodic;
        attribute :>> Period = 1000 [ms];
        attribute Domain : CASE_Scheduling::Domain = 6;

        port Regulator_Internal_Failure : AADL::DataPort { out :>> type : Isolette_Data_Model::Failure_Flag_i; }

        language "GUMBO" /*{
            state
                Internal_Failure_Detected : Base_Types::Boolean;
            initialize
                guarantee INITIAL_DETECTED_INTERNAL_FAILURE:
                    Internal_Failure_Detected implies Regulator_Internal_Failure.flag;
            compute
                guarantee DETECTED_INTERNAL_FAILURE:
                    Internal_Failure_Detected implies Regulator_Internal_Failure.flag;
        }*/

        requirement Internal_Failure_Detection {
            doc /* A.5.1.4 requires true when an internal failure is detected.
             * Platform diagnostics must establish Internal_Failure_Detected,
             * including its initialization and subsequent updates. Publish
             * the output DataPort at initialization without reading inputs.
             * No particular initial Boolean or false-output behavior is
             * prescribed by the FAA excerpt. Diagnostic criteria, memory
             * checks, coverage and detection time remain platform-specific.
             * The implication does not implement that detection mechanism. */
        }
    }

    // ARCH-R-2: nine wrapper ports and nine transparent forwarding edges.
    part def Manage_Regulator_Interface_Process_i :> AADL::Process {
        attribute Domain : CASE_Scheduling::Domain = 3;
        port Current_Temperature : AADL::DataPort { in :>> type : Isolette_Data_Model::TempWstatus_i; }
        port Lower_Desired_Temperature : AADL::DataPort { in :>> type : Isolette_Data_Model::TempWstatus_i; }
        port Upper_Desired_Temperature : AADL::DataPort { in :>> type : Isolette_Data_Model::TempWstatus_i; }
        port Regulator_Mode : AADL::DataPort { in :>> type : Isolette_Data_Model::Regulator_Mode; }
        port Regulator_Status : AADL::DataPort { out :>> type : Isolette_Data_Model::Status; }
        port Display_Temperature : AADL::DataPort { out :>> type : Isolette_Data_Model::Temp_i; }
        port Lower_Desired_Temp : AADL::DataPort { out :>> type : Isolette_Data_Model::Temp_i; }
        port Upper_Desired_Temp : AADL::DataPort { out :>> type : Isolette_Data_Model::Temp_i; }
        port Regulator_Interface_Failure : AADL::DataPort { out :>> type : Isolette_Data_Model::Failure_Flag_i; }
        part implementation : Manage_Regulator_Interface_i;
        connection forward_current : AADL::FeatureConnection connect Current_Temperature to implementation.Current_Temperature;
        connection forward_lower_input : AADL::FeatureConnection connect Lower_Desired_Temperature to implementation.Lower_Desired_Temperature;
        connection forward_upper_input : AADL::FeatureConnection connect Upper_Desired_Temperature to implementation.Upper_Desired_Temperature;
        connection forward_mode : AADL::FeatureConnection connect Regulator_Mode to implementation.Regulator_Mode;
        connection forward_status : AADL::FeatureConnection connect implementation.Regulator_Status to Regulator_Status;
        connection forward_display : AADL::FeatureConnection connect implementation.Display_Temperature to Display_Temperature;
        connection forward_lower_output : AADL::FeatureConnection connect implementation.Lower_Desired_Temp to Lower_Desired_Temp;
        connection forward_upper_output : AADL::FeatureConnection connect implementation.Upper_Desired_Temp to Upper_Desired_Temp;
        connection forward_failure : AADL::FeatureConnection connect implementation.Regulator_Interface_Failure to Regulator_Interface_Failure;
    }

    // ARCH-R-2: four wrapper ports and four forwarding edges.
    part def Manage_Regulator_Mode_Process_i :> AADL::Process {
        attribute Domain : CASE_Scheduling::Domain = 4;
        port Current_Temperature : AADL::DataPort { in :>> type : Isolette_Data_Model::TempWstatus_i; }
        port Regulator_Interface_Failure : AADL::DataPort { in :>> type : Isolette_Data_Model::Failure_Flag_i; }
        port Regulator_Internal_Failure : AADL::DataPort { in :>> type : Isolette_Data_Model::Failure_Flag_i; }
        port Regulator_Mode : AADL::DataPort { out :>> type : Isolette_Data_Model::Regulator_Mode; }
        part implementation : Manage_Regulator_Mode_i;
        connection forward_current : AADL::FeatureConnection connect Current_Temperature to implementation.Current_Temperature;
        connection forward_interface_failure : AADL::FeatureConnection connect Regulator_Interface_Failure to implementation.Regulator_Interface_Failure;
        connection forward_internal_failure : AADL::FeatureConnection connect Regulator_Internal_Failure to implementation.Regulator_Internal_Failure;
        connection forward_mode : AADL::FeatureConnection connect implementation.Regulator_Mode to Regulator_Mode;
    }

    // ARCH-R-2: five wrapper ports and five forwarding edges.
    part def Manage_Heat_Source_Process_i :> AADL::Process {
        attribute Domain : CASE_Scheduling::Domain = 5;
        port Current_Temperature : AADL::DataPort { in :>> type : Isolette_Data_Model::TempWstatus_i; }
        port Lower_Desired_Temp : AADL::DataPort { in :>> type : Isolette_Data_Model::Temp_i; }
        port Upper_Desired_Temp : AADL::DataPort { in :>> type : Isolette_Data_Model::Temp_i; }
        port Regulator_Mode : AADL::DataPort { in :>> type : Isolette_Data_Model::Regulator_Mode; }
        port Heat_Control : AADL::DataPort { out :>> type : Isolette_Data_Model::On_Off; }
        part implementation : Manage_Heat_Source_i;
        connection forward_current : AADL::FeatureConnection connect Current_Temperature to implementation.Current_Temperature;
        connection forward_lower : AADL::FeatureConnection connect Lower_Desired_Temp to implementation.Lower_Desired_Temp;
        connection forward_upper : AADL::FeatureConnection connect Upper_Desired_Temp to implementation.Upper_Desired_Temp;
        connection forward_mode : AADL::FeatureConnection connect Regulator_Mode to implementation.Regulator_Mode;
        connection forward_heat : AADL::FeatureConnection connect implementation.Heat_Control to Heat_Control;
    }

    // ARCH-R-2: one wrapper port and one forwarding edge.
    part def Detect_Regulator_Failure_Process_i :> AADL::Process {
        attribute Domain : CASE_Scheduling::Domain = 6;
        port Regulator_Internal_Failure : AADL::DataPort { out :>> type : Isolette_Data_Model::Failure_Flag_i; }
        part implementation : Detect_Regulator_Failure_i;
        connection forward_failure : AADL::FeatureConnection connect implementation.Regulator_Internal_Failure to Regulator_Internal_Failure;
    }

    part def Regulate_Temperature_i :> AADL::System {
        port current_tempWstatus : AADL::DataPort { in :>> type : Isolette_Data_Model::TempWstatus_i; }
        port lower_desired_tempWstatus : AADL::DataPort { in :>> type : Isolette_Data_Model::TempWstatus_i; }
        port upper_desired_tempWstatus : AADL::DataPort { in :>> type : Isolette_Data_Model::TempWstatus_i; }
        port heat_control : AADL::DataPort { out :>> type : Isolette_Data_Model::On_Off; }
        port regulator_status : AADL::DataPort { out :>> type : Isolette_Data_Model::Status; }
        port displayed_temp : AADL::DataPort { out :>> type : Isolette_Data_Model::Temp_i; }

        part manage_regulator_interface : Manage_Regulator_Interface_Process_i;
        part manage_regulator_mode : Manage_Regulator_Mode_Process_i;
        part manage_heat_source : Manage_Heat_Source_Process_i;
        part detect_regulator_failure : Detect_Regulator_Failure_Process_i;

        // ARCH-R-3: fourteen parent edges, preserving prior endpoint names.
        connection temperature_to_interface : AADL::FeatureConnection connect current_tempWstatus to manage_regulator_interface.Current_Temperature;
        connection temperature_to_mode : AADL::FeatureConnection connect current_tempWstatus to manage_regulator_mode.Current_Temperature;
        connection temperature_to_heat : AADL::FeatureConnection connect current_tempWstatus to manage_heat_source.Current_Temperature;
        connection lower_input : AADL::FeatureConnection connect lower_desired_tempWstatus to manage_regulator_interface.Lower_Desired_Temperature;
        connection upper_input : AADL::FeatureConnection connect upper_desired_tempWstatus to manage_regulator_interface.Upper_Desired_Temperature;
        connection lower_range : AADL::FeatureConnection connect manage_regulator_interface.Lower_Desired_Temp to manage_heat_source.Lower_Desired_Temp;
        connection upper_range : AADL::FeatureConnection connect manage_regulator_interface.Upper_Desired_Temp to manage_heat_source.Upper_Desired_Temp;
        connection interface_failure : AADL::FeatureConnection connect manage_regulator_interface.Regulator_Interface_Failure to manage_regulator_mode.Regulator_Interface_Failure;
        connection internal_failure : AADL::FeatureConnection connect detect_regulator_failure.Regulator_Internal_Failure to manage_regulator_mode.Regulator_Internal_Failure;
        connection mode_to_interface : AADL::FeatureConnection connect manage_regulator_mode.Regulator_Mode to manage_regulator_interface.Regulator_Mode;
        connection mode_to_heat : AADL::FeatureConnection connect manage_regulator_mode.Regulator_Mode to manage_heat_source.Regulator_Mode;
        connection heat_output : AADL::FeatureConnection connect manage_heat_source.Heat_Control to heat_control;
        connection status_output : AADL::FeatureConnection connect manage_regulator_interface.Regulator_Status to regulator_status;
        connection display_output : AADL::FeatureConnection connect manage_regulator_interface.Display_Temperature to displayed_temp;

        requirement Allocation_Ledger {
            doc /* REQ-RT-1 -> Manage_Heat_Source_i REQ_MHS_1..5 ->
             * manage_heat_source.implementation.Heat_Control -> forward_heat
             * -> manage_heat_source.Heat_Control -> heat_output -> heat_control.
             * REQ-RT-2 -> Manage_Regulator_Interface_i REQ_MRI_1..3 ->
             * forward_status -> status_output -> regulator_status.
             * REQ-RT-3 -> Manage_Regulator_Interface_i REQ_MRI_4/5 ->
             * forward_display -> display_output -> displayed_temp.
             * REQ-MRI-6/7 -> interface validity -> forward_failure ->
             * interface_failure -> Mode.forward_interface_failure.
             * REQ-MRI-8/9 -> lower/upper outputs -> forwarding ->
             * lower_range/upper_range -> Heat.forward_lower/forward_upper.
             * Req MRM 1..4 and persistence -> Manage_Regulator_Mode_i ->
             * forward_mode -> mode_to_interface/mode_to_heat -> consumers.
             * A.5.1.4 -> Detect_Regulator_Failure_i -> forward_failure ->
             * internal_failure -> Mode.forward_internal_failure.
             * Current temperature fans out through three process input
             * forwarders; desired status-bearing bounds enter Interface only.
             * Table A-7 domains remain with Interface; Table A-10 health,
             * mode history and elapsed time remain with Mode; command history
             * remains with Heat. The System owns composition and deadlines.
             * Each trace requires implementation, proof and independent tests;
             * named clauses and connections alone supply no such evidence. */
        }
        requirement Composition_Obligations {
            doc /* Preserve SR-1, EA-TS-2, EA-TS2, EA-IS1 and EA-IS2.
             * Temperature Sensor supplies current_tempWstatus; Operator
             * Interface supplies desired bounds and receives status/display;
             * Heat Source receives heat_control. Establish producer guarantees,
             * startup values, actual sampling ages and transport semantics at
             * each consumer. In particular, prove Heat never uses an
             * unspecified failed-interface range while a stale NORMAL mode
             * is still visible. No local assumption hides invalid statuses.
             * Equal periods and matching domains do not prove simultaneous
             * observations, negligible transitions or response deadlines.
             * Preserve both <0.5 second visible response and <6.0 second heat
             * response. The former conflicts with the reference 1000 ms period
             * under ordinary periodic sampling; retain as an open obligation. */
        }
        requirement Deployment_Integration {
            doc /* ARCH-R-4 assigns Interface/Mode/Heat/Failure domains 3/4/5/6
             * to both Processes and Threads, and Periodic 1000 ms to Threads.
             * These are reference-derived choices, not FAA requirements.
             * No processor is introduced. No binding declaration or enclosing
             * hardware instance is supplied in this target context. Existing
             * enclosing allocations must continue to bind these Processes and
             * their Threads to the existing isolette_processor. Review changed
             * containment paths in the enclosing allocation owner; any repair
             * must use Deployment_Properties::Actual_Processor_Binding.
             * Do not fabricate a local hardware endpoint or duplicate binding.
             * The supplied resolved-architecture capture omits all components;
             * it cannot establish current allocation resolution. */
        }
        requirement Verification_And_Repair_Ledger {
            doc /* Trigger: previous source flattened four Threads into one
             * Process; ARCH-R-1/2 instead require four one-thread Processes
             * inside the public Regulate_Temperature_i System. Previous tool
             * diagnostics also reported missing Dispatch Protocol and fallback
             * to Sporadic for all four Threads. This revision supplies the
             * wrappers, nineteen forwarding edges, fourteen parent edges,
             * explicit reference periods, dispatch protocols and domains.
             *
             * Next workflow gates, not executed here: HAMR parse/type checking
             * and complete architecture capture with compatible libraries and
             * full sourcepaths. Inspect diagnostics independently of exit code.
             * Compare resolved categories, all six boundary ports, all nineteen
             * wrapper ports, ownership, all thirty-three connections, domains,
             * periods and enclosing processor bindings. If nested-System
             * support is a tool-version blocker, record it rather than undoing
             * the explicitly required System abstraction.
             *
             * Resolve numeric representation, range compatibility, overlapping
             * transitions, clock progress and platform diagnostics before
             * claiming behavioral completeness. Run Logika integration and
             * satisfiability checks; then regenerate HAMR infrastructure and
             * implement application entry points outside managed markers.
             * Publish every DataPort during initialization without reading
             * inputs, and implement explicit history updates after computation.
             * Verify Rust refinement with Verus; do not use external_body to
             * bypass application proofs.
             *
             * Derive manual assertions independently from FAA requirements;
             * supplement with state-aware GUMBOX and serialized PropTest tests.
             * Cover all modes, all validity combinations, both retained heat
             * commands, exact bounds and adjacent values, startup, power cycle,
             * FAILED persistence, elapsed time below/equal/above 1.0 seconds,
             * healthy expired INIT, reversed bounds, valid out-of-domain bounds,
             * numeric extremes and physical rounding after representation is
             * resolved. Test delayed failure/mode/range propagation and mutate
             * connections to expose omissions, wrong fan-out and swapped bounds.
             * Rejected preconditions are not evidence of required behavior.
             *
             * Analyze the actual cyclic schedule, transport and device delays;
             * generated unit tests do not establish deployed deadlines. No
             * whole-system acceptance or successful check is claimed. */
        }
    }

    alias Regulate_i for Regulate_Temperature_i;
}
