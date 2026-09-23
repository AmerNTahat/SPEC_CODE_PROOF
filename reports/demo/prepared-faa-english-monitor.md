A.5.2 Monitor Temperature Function.

The Monitor Temperature Function compares the Current Temperature from the Temperature
Sensor with the Alarm Temperature Range provided by the Operator Interface and turns the
Alarm Control on or off to Alert The Nurse if the Current Temperature falls below or rises above
the safe range. It also provides the Monitor Status back to the Operator Interface.

The high-level requirements for the Monitor Temperature Function are as follows:

•      REQ-MT-1:      The Monitor Temperature Function shall set the value of the Alarm
       Control.
       Rationale: The primary function of the Monitor Temperature Function is to raise an
       alarm if the Isolette is unable to maintain the Current Temperature within the Alarm
       Temperature Range, as required by safety requirement SR-2.

•      REQ-MT-2: The Monitor Temperature Function shall set the value of the Monitor
       Status.
       Rationale: Safety requirement SR-2 requires the Thermostat to provide an independent
       monitor function. The status of this function must be provided to the Operator Interface,
       which will use it and the status of the Regulate Temperature Function to report the
       overall status of the Thermostat, as required by safety requirement SR-2.

The Monitor Temperature Function is allocated into subfunctions as shown in figure A-5.




                                             A-20
                   Figure A-5. Monitor Temperature Dependency Diagram

The Monitor Temperature internal variables are shown in table A-12.

                     Table A-12. Monitor Temperature Internal Variables

         Name              Type          Range       Units          Physical Interpretation
Alarm Range                                                  Safe range of Isolette temperature
 Lower Alarm Temp      Integer        [96..101]       °F     Lower value of alarm range
 Upper Alarm Temp      Integer        [97..102]       °F     Upper value of alarm range
Monitor Interface      Boolean        False, True            Indicates an operator
Failure                                                      interface failure
Monitor Internal       Boolean        False, True
                                                             Indicates an internal failure
Failure
Monitor Mode           Enumerated     INIT                   Initializing following power-up
                                      NORMAL                 Normal mode of operation
                                      FAILED                 Internal failure detected

A.5.2.1 Manage Monitor Interface Function.

The Manage Monitor Interface function defines the interaction with the Operator Interface
external entity. These include obtaining the Alarm Range and reporting back the status of the
Monitor Temperature Function. The constants are shown in table A-13.




                                          A-21
                Table A-13. The Manage Monitor Interface Function Constants

     Name           Type    Value Units                    Physical Interpretation
Max Operator        Real     0.5   Sec The time an operator will tolerate between an
Response Time                             operator request or a change in the Thermostat state
                                          and the visible response
Rationale: A trade study has shown that this lag should be no more than 0.5 second.

The requirements for the Monitor Status controlled variable are as follows:

•      REQ-MMI-1: If the Manage Monitor Interface mode is INIT, the Monitor Status shall be
       set to Init.

•      REQ-MMI-2: If the Manage Monitor Interface mode is NORMAL, the Monitor Status
       shall be set to On.

•      REQ-MMI-3: If the Manage Monitor Interface mode is FAILED, the Monitor Status
       shall be set to Failed.

       Latency: < Max Operator Response Time
       Tolerance: N/A

The requirements for Monitor Interface Failure internal variable are as follows:

•      REQ-MMI-4: If the Status attribute of the Lower Alarm Temperature or the Upper
       Alarm Temperature is Invalid, the Monitor Interface Failure shall be set to True.

•      REQ-MMI-5: If the Status attribute of the Lower Alarm Temperature and the Upper
       Alarm Temperature is Valid, the Monitor Interface Failure shall be set to False.
       Rationale: The Monitor Interface Failure internal variable indicates if any errors have
       occurred in sensing the Operator Interface monitored variables needed by the Manage
       Temperature Function. Note that its initial value on power-up will always be True since
       the Status attribute of the Lower Alarm Temperature and the Upper Alarm Temperature
       will initially be Invalid.

The requirements for Alarm Range Internal variable are as follows:

•      REQ-MMI-6: If the Monitor Interface Failure is False, the Alarm Range variable shall
       be set to the Desired Temperature Range.

•      REQ-MMI-7: If the Monitor Interface Failure is True, the Alarm Range variable is
       UNSPECIFIED.
       Rationale: The Alarm Range variable is only meaningful when there is not a Monitor
       Interface Failure. If there is, its value should not used and it can be set to any value.



                                            A-22
A.5.2.2 Manage Monitor Mode Function.

The Manage Monitor Mode Function determines the mode of the Monitor Temperature
Function. The constants and definitions are shown in tables A-14 and A-15, respectively.

                  Table A-14. The Manage Monitor Mode Function Constants

        Name      Type Value Units                       Physical Interpretation
 Monitor           Real      1.0     Sec The time allowed for initialization of the Monitor
 Initialization                            Temperature Function before declaring failure.
 Timeout
 Rationale: A trade study has shown that users become impatient if the Thermostat requires
 more than one second to initialize.

                  Table A-15. The Manage Monitor Mode Function Definitions

      Name             Type                           Definition
 Monitor Status       Boolean NOT (Monitor Interface Failure OR Monitor Internal Failure)
                              AND Current Temperature.Status = Valid

The modes and transitions of the Manage Monitor Mode Function are specified in the state
transition diagram shown in figure A-6. Each transition is a separate requirement and is assigned
a unique identifier (e.g., Req MMM 1). All transitions are assumed to occur in negligible time.


                                                        Req MMM 1


                                                         INIT


                                                       Req MMM 2
                                                                    Monitor
                                                                    Status = Valid

                                                       NORMAL
           Duration (INMODE) > Req MMM
         Monitor Initialization Timeout
                                                       Req MMM 3
                                                                    Monitor
                                                                    Status ≠ Valid

                                                        FAILED

        MMM = Manage Monitor Mode

                  Figure A-6. Monitor Temperature Mode Transition Diagram




                                            A-23
Rationale: (Req MMM 3 and Req MMM 4) Once the monitor has failed, the only way for it to
re-enter normal operation is for it to be powered off and on. This ensures that the operators are
made aware of any transient failures that the monitor may be experiencing.

A.5.2.3 Manage Alarm Function.

The Manage Alarm Function turns the Alarm Control on when the Current Temperature of the
Isolette falls below or rises above the Alarm Temperature Range.

The requirements for the Alarm Control controlled variable are as follows:

•      REQ-MA-1: If the Monitor Mode is INIT, the Alarm Control shall be set to Off.
       Rationale: A monitor that is initializing should not activate the alarm unless it enters the
       FAILED mode.

•      REQ-MA-2: If the Monitor Mode is NORMAL and the Current Temperature is less than
       the Lower Alarm Temperature or greater than the Upper Alarm Temperature, the Alarm
       Control shall be set to On.

•      REQ-MA-3: If the Monitor Mode is NORMAL and the Current Temperature is greater
       than or equal to the Lower Alarm Temperature and less than the Lower Alarm
       Temperature +0.5°, or the Current Temperature is greater than the Upper Alarm
       Temperature -0.5° and less than or equal to the Upper Alarm Temperature, the value of
       the Alarm Control shall not be changed.
       Rationale: This provides a hysteresis that prevents transient alarms, see figure A-7.


               Alarm On                                                    Alarm On

                                              Alarm Off



                   Lower Alarm Temp                           Upper Alarm Temp


                            Figure A-7. Transient Alarm Hysteresis

•      REQ-MA-4: If the Monitor Mode is NORMAL and the value of the Current
       Temperature is greater than or equal to the Lower Alarm Temperature +0.5° and less than
       or equal to the Upper Alarm Temperature -0.5°, the Alarm Control shall be set to Off.
       Rationale: This turns the alarm off at the same moment that the Displayed Temperature
       shows a value greater than the Lower Alarm Temperature and less than the Upper Alarm
       Temperature.



                                            A-24
•      REQ-MA-5: If the Monitor Mode is FAILED, the Alarm Control shall be set to On.
       Rationale: A failed monitor cannot monitor the Current Temperature of the Isolette and
       the Alarm should be turned on.

       Latency: <5 seconds
       Tolerance: N/A

       Rationale: Required by SR-2.

A.5.2.4 Detect Monitor Failure Function.

The Detect Monitor Failure Function identifies internal failures, (e.g., a memory check failure)
in the Monitor Temperature Function. It defines a single Boolean-valued internal variable,
Monitor Internal Failure, which is set to True if an internal failure is detected.

The requirements for Monitor Internal Failure variable are implementation-specific and cannot
be specified until an implementation platform is chosen.




                                        A-25/A-26
