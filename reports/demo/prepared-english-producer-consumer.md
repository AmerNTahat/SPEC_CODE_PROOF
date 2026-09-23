# KSU Producer/Consumer — Draft Derived Description and Requirements

## System description
The selected material defines the ProdCons_System architecture, comprising a producer process, a consumer process, and a shared processor. Its supported descriptive purpose is to integrate these components and connect the producer's Message output to the consumer's Message input. No broader stakeholder purpose is stated. Each process contains one declared thread. Both threads dispatch periodically and use Rust. The system boundary encloses both processes, their threads, their message connections, and the processor; no external entities or system-level external interfaces are declared. At the component boundary, the producer controls its outgoing Message and the consumer monitors its incoming Message. Each Message contains Integer_32 fields named payload and control_num; no physical meaning or units are specified for either field. The producer guarantees a payload between 0 and 90 inclusive. The consumer assumes incoming payloads between 0 and 100 inclusive and has an Integer_32 state variable, payload_sum, initialized to zero. Subsequent computation is unspecified for both threads. Architecture, deployment, language, scheduling, and generation settings below are source-defined implementation choices, not independently established stakeholder needs. These are draft derived requirements for data preparation, not an independent specification or validation result.

## Requirements
PC-001 [architecture]: The HAMR generation configuration shall select the Microkit platform.
PC-002 [architecture]: The HAMR generation configuration shall specify ../../hamr as the output directory.
PC-003 [architecture]: ProdCons_System shall contain a producer process instance named prod of type Prod_Process.
PC-004 [architecture]: ProdCons_System shall contain a consumer process instance named cons of type Cons_Process.
PC-005 [architecture]: ProdCons_System shall contain a processor instance named proc of type Main_Processor.
PC-006 [interface]: ProdCons_System shall connect the producer process output port to the consumer process input port through the port connection named pc.
PC-007 [architecture]: The producer process shall be deployed on processor proc through the actual processor binding named prod_to_proc.
PC-008 [architecture]: The consumer process shall be deployed on processor proc through the actual processor binding named cons_to_proc.
PC-009 [interface]: Prod_Process shall expose an outgoing event-data port named output carrying Message data.
PC-010 [architecture]: Prod_Process shall use scheduling domain Domain_Prod.
PC-011 [architecture]: Prod_Process shall contain a thread instance named prod of type Prod.
PC-012 [interface]: Prod_Process shall connect its contained producer thread's output port to its process output port through the port connection named prod_output.
PC-013 [interface]: The Prod thread shall expose an outgoing event-data port named output carrying Message data.
PC-014 [timing]: The Prod thread shall use periodic dispatch with a period of 60 milliseconds.
PC-015 [architecture]: The Prod thread shall be implemented in Rust.
PC-016 [functional]: For each Message supplied at the Prod thread's output port, the thread shall ensure that payload is between 0 and 90 inclusive.
PC-017 [interface]: Cons_Process shall expose an incoming event-data port named input carrying Message data.
PC-018 [architecture]: Cons_Process shall use scheduling domain Domain_Cons.
PC-019 [architecture]: Cons_Process shall contain a thread instance named cons of type Cons.
PC-020 [interface]: Cons_Process shall connect its process input port to its contained consumer thread's input port through the port connection named cons_input.
PC-021 [interface]: The Cons thread shall expose an incoming event-data port named input carrying Message data.
PC-022 [timing]: The Cons thread shall use periodic dispatch with a period of 40 milliseconds.
PC-023 [architecture]: The Cons thread shall be implemented in Rust.
PC-024 [state]: The Cons thread shall maintain a state variable named payload_sum of type Base_Types::Integer_32.
PC-025 [architecture]: The consumer's initialization helper Init_Payload_Sum shall return the Integer_32 value zero.
PC-026 [state]: Upon initialization, the Cons thread shall set payload_sum to the value returned by Init_Payload_Sum, namely zero.
PC-027 [interface]: Message shall contain a field named payload of type Base_Types::Integer_32.
PC-028 [interface]: Message shall contain a field named control_num of type Base_Types::Integer_32.
PC-029 [timing]: Main_Processor shall have a frame period of 120 milliseconds.
PC-030 [timing]: Main_Processor shall have a clock period of 2 milliseconds.
PC-031 [architecture]: The scheduling domain identifier Domain_Prod shall have the value 2.
PC-032 [architecture]: The scheduling domain identifier Domain_Cons shall have the value 3.

## Assumptions
Source-defined consumer integration assumption, lines 119–121: each incoming Message payload is between 0 and 100 inclusive. Exact quotation: "(0 [i32] <= input.payload) & (input.payload <= 100 [i32]) ;". This is an assumption on the consumer's input, not a requirement that the consumer validate, reject, or modify input.
No additional environmental assumptions are introduced.

## Unresolved questions
No broader stakeholder goals, operational context, external entities, physical monitored or controlled quantities, or safety goals are supplied.
Producer computation is marked "// TBD" at lines 71–72. Message generation conditions, payload selection, control_num values, and whether any message is emitted on a dispatch are unspecified.
Consumer computation is marked "// TBD" at lines 128–129. State updates, input processing, and any relationship between payload_sum and received payloads are unspecified. Accumulation is only uncertain intent suggested by the state variable name.
The meanings and units of payload, control_num, and payload_sum are unspecified. No control_num constraints beyond its declared type are supplied.
Event-data queue capacity, ordering, overflow handling, delivery guarantees, latency, and behavior when input is absent are unspecified.
The precise evaluation semantics of the integration contracts when no event is present are not supplied. The producer payload requirement does not establish an obligation to emit an event.
The consumer assumes an inclusive upper payload bound of 100, while the producer guarantees 90. These bounds are preserved separately; no behavior for an assumption violation is supplied.
Dispatch phases, first-dispatch timing, scheduling order, domain time allocations, execution-time bounds, and deadlines are unspecified. Periods do not independently establish these values.
The relationship between the processor frame period, clock period, and thread dispatch scheduling is not further defined in the selected material.
Only consumer payload_sum initialization is defined. Producer initialization, message-field initialization, restart behavior, operating modes, and subsequent state-dependent behavior are unspecified.
The imported HAMR and Base_Types definitions and applicable language semantics are not supplied. Detailed integer arithmetic, overflow, serialization, and port semantics cannot be derived from this excerpt.
Line 1 supplies a HAMR generation annotation; its output directory resolution base and whether it is a mandatory project configuration are not independently established.
No rulebook, generated validation output, or independent evidence of implementation correctness is supplied.
