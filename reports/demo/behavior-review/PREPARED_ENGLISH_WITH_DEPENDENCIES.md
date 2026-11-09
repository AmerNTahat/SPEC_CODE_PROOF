A.5.1 REGULATE TEMPERATURE FUNCTION.

The Regulate Temperature Function compares the Current Temperature from the Temperature
Sensor with the Desired Temperature Range provided by the Operator Interface and turns the
Heat Source on or off to keep the Current Temperature within the Desired Temperature Range.
It also provides the Display Temperature and the Regulator Status back to the Operator Interface.

The high-level requirements for the Regulate Temperature Function are as follows:

•      REQ-RT-1: The Regulate Temperature Function shall set the value of the Heat Control.
       Rationale: The primary function of the Regulate Temperature Function is to turn the
       Heat Control on and off to maintain the Current Temperature in the Isolette within the
       Desired Temperature Range, as required by SR-1.




                                            A-14
•      REQ-RT-2: The Regulate Temperature Function shall set the value of the Regulator
       Status.
       Rationale: The status of the Regulate Temperature Function is provided to the Operator
       Interface so it can use the status of the Regulate Temperature and Monitor Temperature
       Functions to report the overall status of the Thermostat, as required by SR-1.

•      REQ-RT-3: The Regulate Temperature Function shall set the value of the Display
       Temperature.
       Rationale: The Current Temperature of the Isolette is displayed on the Operator Interface
       to provide the operators with an additional means to confirm that the Isolette is
       maintaining the temperature correctly. This value is provided by the Regulate
       Temperature Function to the Operator Interface as the Display Temperature.

The Regulate Temperature Function is allocated into subfunctions in figure A-3.

                Regulate
              Temperature
                                                           Current
                                                         Temperature


                                                           Manag        Heat
                                                            Heat
                                                                       Control
                                                           Source
                                      Desired
                                      Range
                   Regulator                              Regulator
                    Status                                 Mod


                 Desired       Manag            Mod       Manag        Regulator    Detect
               Temperature     Regulator                  Regulator     Internal   Regulator
                 Range         Interface    Regulator      Mod           Failure    Failure
                                            Interface
                                             Failure       Current
                    Display     Current
                                                         Temperature
                  Temperature Temperature                  (Status)



                   Figure A-3. Regulate Temperature Dependency Diagram

The internal variables for the Regulate Temperature Function are shown in table A-7.




                                                  A-15
                     Table A-7. The Regulate Temperature Internal Variables

          Name                  Type           Range      Units             Physical Interpretation
Desired Range                                                      Desired range of Isolette temperature
    Lower Desired Temp       Integer        [96..101]     °F       Lower value of desired range
    Upper Desired Temp       Integer        [97..102]     °F       Upper value of desired range
Regulator Interface          Boolean        False, True            Indicates an operator interface
Failure
Regulator Internal Failure   Boolean        False, True            Indicates an internal failure
Regulator Mode               Enumerated     Init                   Initializing following power-up
                                            NORMAL                 Normal mode of operation
                                            FAILED                 Internal failure detected

A.5.1.1 Manage Regulator Interface Function.

The Manage Regulator Interface Function defines the interaction with the Operator Interface
external entity. These include obtaining the Desired Range, reporting back the status of the
Regulate Temperature Function, and reporting back the Display Temperature. The constants are
shown in table A-8.

                    Table A-8. Manage Regulator Interface Function Constants

      Name           Type    Value     Units                      Physical Interpretation
 Max Operator        Real     0.5       Sec     The time an operator will tolerate between an operator
 Response Time                                  request or a change in the Thermostat state and the
                                                visible response
 Rationale: A trade study has shown that this lag should be no more than 0.5 second.

The requirements for the Regulator Status controlled variable are as follows:

•        REQ-MRI-1: If the Regulator Mode is INIT, the Regulator Status shall be set to Init.

•        REQ-MRI-2: If the Regulator Mode is NORMAL, the Regulator Status shall be set to
         On.

•        REQ-MRI-3: If the Regulator Mode is FAILED, the Regulator Status shall be set to
         Failed.

         Latency: < Max Operator Response Time
         Tolerance: N/A




                                                A-16
The requirements for the Display Temperature controlled variable are as follows:

•      REQ-MRI-4: If the Regulator Mode is NORMAL, the Display Temperature shall be set
       to the value of the Current Temperature rounded to the nearest integer.
       Rationale: Displaying the rounded value of the Current Temperature provides the the
       most accurate display of the Current Temperature possible using an integer display.
       When combined with the accuracy of the Temperature Sensor (EA-TS-2), the Display
       Temperature should be within 0.6°F of the actual value.

•      REQ-MRI-5: If the Regulator Mode is not NORMAL, the value of the Display
       Temperature is UNSPECIFIED.
       Rationale: In modes other than NORMAL, the value of Display Temperature is not
       meaningful and should not be used.
       Latency: < Max Operator Response Time
       Tolerance: ±0.6°F

The requirements for the Regulator Interface Failure internal variable are as follows:

•      REQ-MRI-6: If the Status attribute of the Lower Desired Temperature or the Upper
       Desired Temperature is Invalid, the Regulator Interface Failure shall be set to True.

•      REQ-MRI-7: If the Status attribute of the Lower Desired Temperature and the Upper
       Desired Temperature is Valid, the Regulator Interface Failure shall be set to False.
       Rationale: The Regulator Interface Failure internal variable indicates if any errors have
       occurred in sensing the Operator Interface monitored variables needed by the Regulate
       Temperature Function. Note that its initial value on power-up will always be True since
       the Status of the Lower Desired Temperature and the Upper Desired Temperature are
       initially Invalid.

The requirements for the Desired Range internal variable are as follows:

•      REQ-MRI-8: If the Regulator Interface Failure is False, the Desired Range shall be set to
       the Desired Temperature Range.

•      REQ-MRI-9: If the Regulator Interface Failure is True, the Desired Range is
       UNSPECIFIED.
       Rationale: The Desired Range is only meaningful when there is not a Regulator Interface
       Failure. If there is, its value should not be used, and it can be set to any value.




                                            A-17
A.5.1.2 Manage Regulator Mode Function.

The Manage Regulator Mode Function determines the mode of the Regulate Temperature
Function. The constants and definitions are shown in tables A-9 and A-10, respectively.

                    Table A-9. The Manage Regulator Mode Function Constants

         Name      Type Value Units                       Physical Interpretation
    Regulator      Real      1.0     Sec The time allowed for initialization of the Regulate
    Init Timeout                           Temperature Function before declaring failure
    Rationale: A trade study has shown that users become impatient if the Thermostat requires
    more than one second to initialize.

                 Table A-10. The Manage Regulator Mode Function Definitions


      Name              Type                             Definition
 Regulator Status      Boolean NOT (Regulator Interface Failure OR Regulator Internal Failure)
                               AND Current Temperature.Status = Valid

The requirements for the Regulator Mode internal variable are as follows:

•       The modes and transitions of the Manage Regulator Mode Function are specified in the
        state transition diagram shown in figure A-4. Each transition is a separate requirement
        and is assigned a unique identifier (e.g., Req MRM 1). All transitions are assumed to
        occur in negligible time.


                                                        Req MRM 1


                                                          INIT


                                        Req MRM 4       Req MRM 2
                                                                    Regulator
                                                                    Status = True
              Duration (INMODE) >
                                                       NORMAL
              Regulator Init Timeout

                                                        Req MRM 3
                                                                    Regulator
                                                                    Status = False

                                                        FAILED

              MRM = Manage Regulator Mode

                    Figure A-4. Regulate Temperature Mode Transition Diagram


                                            A-18
       Rationale: (Req MRM 3 and Req MRM 4) Once the regulator has failed, the only way
       for it to re-enter normal operation is for it to be powered off and on. This ensures that the
       operators are made aware of any transient failures that the regulator may be experiencing.

A.5.1.3 Manage Heat Source Function.

The Manage Heat Source Function turns the Heat Source on and off to maintain the Current
Temperature of the Isolette within the Desired Temperature Range. The constants are shown in
table A-11.

                   Table A-11. The Manage Heat Source Function Constants

      Name          Type     Value      Units                 Physical Interpretation
Allowed Heat        Real      6.0        Sec     The maximum time by which the Heat Source
Source Latency                                   must be turned on or off to ensure acceptable
                                                 operation of the Isolette system
Rationale: Since a closed Isolette will warm or cool at a maximum rate of 1°F per minute
(EA-IS1 and EA-IS2), turning the Heat Source on or off within 6 seconds ensures that the
Current Temperature will not have changed by more than 0.1°F, the required accuracy and
resolution of the Temperature Sensor (EA-TS2).

The requirements for the Heat Control controlled variable are as follows:

•      REQ-MHS-1: If the Regulator Mode is INIT, the Heat Control shall be set to Off.
       Rationale: A regulator that is initializing cannot regulate the Current Temperature of the
       Isolette and the Heat Control should be turned off.

•      REQ-MHS-2: If the Regulator Mode is NORMAL and the Current Temperature is less
       than the Lower Desired Temperature, the Heat Control shall be set to On.

•      REQ-MHS-3: If the Regulator Mode is NORMAL and the Current Temperature is
       greater than the Upper Desired Temperature, the Heat Control shall be set to Off.

•      REQ-MHS-4: If the Regulator Mode is NORMAL and the Current Temperature is
       greater than or equal to the Lower Desired Temperature and less than or equal to the
       Upper Desired Temperature, the value of the Heat Control shall not be changed.
       Rationale: When the Isolette is warming towards the Upper Desired Temperature, the
       Heat Source should be left on until the Upper Desired Temperature is reached. In a
       similar fashion, if the Isolette is cooling towards the Lower Desired Temperature, the
       Heat Source should be left off until the Lower Desired Temperature is reached.




                                             A-19
•      REQ-MHS-5: If the Regulator Mode is FAILED, the Heat Control shall be set to Off.
       Rationale: In failed mode, the regulator cannot regulate the Current Temperature of the
       Isolette and the Heat Control should be turned off.
       Latency: < Allowed Heat Source Latency
       Tolerance: N/A

A.5.1.4 Detect Regulator Failure Function.

The Detect Regulator Failure Function identifies internal failures, (e.g., a memory check failure)
in the Regulate Temperature Function. It defines a single Boolean-valued internal variable,
Regulator Internal Failure, which is set to True if an internal failure is detected.

The requirements for Regulator Internal Failure variable are implementation-specific and cannot
be specified until an implementation platform is chosen.



# Proposed architecture supplement — explicit reference-derived design choices

DRAFT FOR HUMAN REVIEW. These clauses are reconstructed from the approved isolated
Regulate.sysml reference for this development reconstruction test. They are not
new FAA stakeholder requirements and are not independent transfer evidence.
FAA English above remains authoritative for behavior, timing and unspecified regions.

ARCH-R-1: Represent Regulate Temperature as an AADL System containing four distinct
AADL Processes: Manage Regulator Interface, Manage Regulator Mode, Manage Heat Source,
and Detect Regulator Failure. Each Process shall contain exactly one corresponding
AADL Thread. Preserve the existing public Regulate_Temperature_i classifier.

ARCH-R-2: Each Process shall expose the ports required by its Thread and forward
inputs inward and outputs outward without changing direction, payload type or
functional ownership. Interface has9 ports, Mode4, Heat5, and Failure1. These19
wrapper ports require19 forwarding connections. Do not flatten away this layer.

ARCH-R-3: At the regulator boundary, accept current temperature with status and
lower/upper desired temperature with status. Emit regulator status, displayed
temperature and heat command. Route current temperature to Interface, Mode and
Heat; desired inputs to Interface; validated desired bounds from Interface to Heat;
Interface failure and internal Failure to Mode; Mode to Interface and Heat;
Interface display/status and Heat command to the boundary. Preserve all14 parent
connections and the shared payload definitions. No extra processor is introduced.

ARCH-R-4: The reference allocates domains3,4,5,6 to Interface, Mode, Heat, Failure
respectively, on both Process and Thread; it sets Periodic and1000ms on each Thread.
These are reference-derived deployment choices, not FAA requirements. For a scoped
architecture reconstruction test, reproduce them explicitly and report their
unresolved compatibility with the FAA <0.5s visible-response requirement. Do not
claim whole-system acceptance or change the FAA timing requirement to match them.

BEHAVIOR-R-1: Preserve every FAA requirement above, including heat retention,
display rounding, initialization/history and timeout semantics, even where the
reference's contracts omit them. Record physical representation and clock-progress
gaps as outstanding implementation/proof obligations. Never copy a missing or
incorrect golden contract as the behavioral acceptance criterion.


## Additional source context — Steve_Miller_FAA_docAR-08-32.pdf (lines 4579–4722)

A.3.2 TEMPERATURE SENSOR.

The Temperature Sensor provides the Current Temperature of the Air in the Isolette to the
Thermostat. The monitored variables are shown in table A-3.

                 Table A-3. Thermostat Monitored Variables for Temperature Sensor

            Name              Type        Range          Units            Physical Interpretation
    Current Temperature      Real       [68.0..105.0]     °F     Current air temperature inside Isolette
                             Status    ●Invalid, Valid

● denotes initial value

The following environmental assumptions are made:

•         EA-TS-1: The Current Temperature will be provided to the Thermostat in degrees
          Fahrenheit
          Rationale: Consistency with environmental-assumption Operator Interface EA-OI-1

•         EA-TS-2: The Current Temperature will be sensed to an accuracy of ±0.1°F.
          Rationale: An accuracy of 0.1°F is necessary to ensure the Thermostat can turn the Heat
          Source on and off quickly enough to maintain the Desired Temperature Range.

•         EA-TS-3: The Current Temperature will cover the range of at least 68.0° to 105.0°F.
          Rationale: This is the specified range of operation of the Isolette. The lower end of this
          range is useful for monitoring an Isolette that is warming to the Desired Temperature
          Range. The upper end is greater than the Upper Alarm Temperature to ensure that the
          Current Temperature will be sensed across the entire Alarm Temperature Range.

A.3.3 HEAT SOURCE.

The Heat Source heats the Air in the Isolette. It is turned on and off by changing the value of the
Heat Control controlled variable. The controlled variables are shown in table A-4. No
environmental assumptions are made.

                      Table A-4. Thermostat Controlled Variables for Heat Source

        Name                Type         Range      Units          Physical Interpretation
    Heat Control          Enumerated     Off, On            Command to turn Heat Source on and off




                                                   A-9
A.3.4 OPERATOR INTERFACE.

The Operator Interface provides the Operator Settings for the Thermostat and receives Operator
Feedback from the Thermostat. The environmental assumptions associated with the Operator
Interface are quite strong, which simplifies the manage Operator Interface Function. If these
assumptions were not satisfied by the Operator Interface external entity, the Manage Operator
Interface Function would need to be strengthened to ensure consistent inputs to the Thermostat.
The monitored and controlled variables are shown in tables A-5 and A-6, respectively.

                  Table A-5. Thermostat Monitored Variables for Operator Interface

        Name          Type               Range           Units                 Physical Interpretation
Operator Settings                                                   Thermostat settings provided by operator
 Desired Temperature Range                                          Desired range of Isolette temperature
     Lower Desired        Integer        [97..99]            °F     Lower value of Desired Temperature
     Temperature          Status      ●Invalid, Valid               Range
     Upper Desired        Integer        [98..100]           °F     Upper value of Desired Temperature
     Temperature          Status      ●Invalid, Valid               Range
  Alarm Temperature Range                                           Activate Alarm when outside of this range
     Lower Alarm          Integer        [93..98]            °F     Lower value of Alarm Temperature Range
     Temperature          Status      ●Invalid, Valid
     Upper Alarm          Integer        [99..103]           °F     Upper value of Alarm Temperature Range
     Temperature          Status      ●Invalid, Valid

● denotes initial value

                  Table A-6. Thermostat Controlled Variables for Operator Interface

           Name                      Type            Range        Units         Physical Interpretation
  Operator Feedback                                                       Information provided back to the
                                                                          operator
    Regulator Status               Enumerated       Init, On,             Status of the Thermostat
                                                     Failed               Regulator Function
    Monitor Status                 Enumerated       Init, On,             Status of the Thermostat Monitor
                                                     Failed               Function
    Display Temperature              Integer        [68..105]      °F     Displayed temperature of Isolette
    Alarm                          Enumerated        Off, On              Command to turn Alarm on or
                                                                          off




                                                     A-10
The following environmental assumptions are made:

•     EA-OI-1: All temperatures will be entered and displayed in degrees Fahrenheit.
      Rationale: Minimize the complexity of this example. An actual system would probably
      support Celsius or perhaps both Fahrenheit and Celsius

•     EA4-OI-2: All temperatures will be set and displayed by the operators in increments of
      1°F.
      Rationale: Marketing studies have shown that customers prefer to set temperatures in
      1 degree increments. A resolution 1°F is sufficient to be consistent with the functional
      and performance requirements specified in the rest of the document.

•     EA-OI-3: The Lower Alarm Temperature will always be ≥93°F.
      Rationale: Exposure to temperatures less than 93°F will result in hypothermia, which can
      lead to death within a few minutes for severely ill preterm infants.

•     EA-OI-4: The Lower Alarm Temperature will always be less than or equal to the Lower
      Desired Temperature of -1°F.
      Rationale: If the Lower Alarm Temperature is greater than or equal to the Lower Desired
      Temperature, the Alarm could be activated while the Current Temperature is still in the
      Desired Temperature Range.

•     EA-OI-5: The Lower Desired Temperature will always be ≥97°F.
      Rationale: Exposing the Infant to temperatures lower than 97°F may result in excessive
      heat loss and drop in heart rate secondary to metabolic acidosis.

•     EA-OI-6: The Lower Desired Temperature will always be less than or equal to the Upper
      Desired Temperature of -1°F.
      Rationale: If the Lower Desired Temperature is greater than or equal to the Upper
      Desired Temperature, it is unclear if the Heat Source should be on or off. This may result
      in excessive cycling of the Heat Source.

•     EA-OI-7: The Upper Desired Temperature will always be ≤100°F.
      Rationale: Exposing the Infant to temperatures greater than 100°F may result in an
      incorrect diagnosis of fever resulting in aggressive evaluation (blood culture and lumbar
      puncture) and treatment for infection.

•     EA-OI-8: The Upper Alarm Temperature will always be greater than or equal to the
      Upper Desired Temperature of 1°F.
      Rationale: If the Upper Alarm Temperature is less than or equal to the Upper Desired
      Temperature, the Alarm could be activated while the Current Temperature is still in the
      Desired Temperature Range.
•     EA-OI-9: The Upper Alarm Temperature will always be ≤103°F.


                                          A-11
       Rationale: Exposure to temperatures greater than 103°F will result in hyperthermia,
       which can lead to cardiac arrhythmias and febrile seizures within a few minutes.

•      EA-OI-9: The Display Temperature will cover the range of at least 68.0° to 105.0°F.
       Rationale: This is the specified range of operation of the Isolette. The lower end of this
       range is useful for monitoring an Isolette that is warming to the Desired Temperature
       Range. The upper end is set to be greater than the maximum Upper Alarm Temperature.



## English transcription of Figure A-4 — requires visual/source review

Source: Steve_Miller_FAA_docAR-08-32.pdf, PDF page 109 (printed A-18), Figure A-4, Regulator Mode State Machine. This is a transcription of the diagram, not a new timing interpretation.

- REQ-MRM-1: The initial transition enters INIT.
- REQ-MRM-2: The transition from INIT to NORMAL is labeled Regulator Status = True.
- REQ-MRM-3: The transition from NORMAL to FAILED is labeled Regulator Status = False.
- REQ-MRM-4: The transition from INIT to FAILED is labeled Duration(INMODE) > 1.0s.
- The accompanying note says transition time is negligible.
- The diagram does not give explicit priority when the INIT-to-NORMAL and INIT-to-FAILED guards overlap. A discrete implementation needs a reviewed priority or a justified proof that the overlap is unreachable. No priority is silently added here.

Source fidelity note: EA-OI-6 uses the awkward wording “Upper Desired Temperature of -1°F.” The proposed mathematical reading lower <= upper - 1°F must be reviewed against the PDF; do not silently repair source wording. Source identifiers also contain typographical anomalies, which the exact excerpt retains.

