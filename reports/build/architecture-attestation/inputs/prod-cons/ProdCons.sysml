//@ HAMR: --platform Microkit --output-dir ../../hamr

package ProdCons {

  private import HAMR::*;

  //===============================================================================
  // 
  //  P r o d  C o n s    S y s t e m 
  // 
  //  Top-level architecture definition integrating system subcomponents.
  //
  //===============================================================================

  part def ProdCons_System :> System {
    //-- I n t e r n a l s --
    // ..indicate the processes (partitions) of the system
    part prod: Prod_Process;
    part cons: Cons_Process;
    part proc : Main_Processor;

    // connections (information flows) between partitions
    connection pc : PortConnection connect prod.output to cons.input;
    
    //-- A l l o c a t i o n s  of software/partitions to hardware
    allocation prod_to_proc: Deployment_Properties::Actual_Processor_Binding 
      allocate prod to proc;
    allocation cons_to_proc: Deployment_Properties::Actual_Processor_Binding 
      allocate cons to proc;
  }

  //===============================================================================
  // 
  //  P r o d  
  // 
  //===============================================================================
  
  // ------ P r o c e s s -------

  part def Prod_Process :> Process {
     //-- I n t e r f a c e  --
    port output : EventDataPort {out :>> type : Message; }

    //-- P r o p e r t i e s  --
    attribute :>> Domain = Domain_Prod;

    //-- I n t e r n a l s --
    part prod: Prod; 
    connection prod_output : PortConnection connect prod.output to output;
  }

  // ------ T h r e a d -------

  part def Prod :> Thread {
    //-- I n t e r f a c e  --
    port output : EventDataPort { out :>> type : Message; }

    //-- P r o p e r t i e s  --
    attribute :>> Period = 60 [ms];  
    attribute :>> Dispatch_Protocol = Supported_Dispatch_Protocols::Periodic;
    attribute :>> Implementation_Language = Implementation_Languages::Rust;

    //-- B e h a v i o r    C o n s t r a i n t s --
    language "GUMBO" /*{
          
	  //-- == I n t e g r a t i o n     C o n s t r a i n t s	
	  integration
	    guarantee Payload_Range: 
  	    (0 [i32] <= output.payload) & (output.payload <= 90 [i32]) ;
 
 	  //-- == C o m p u t e 
    // TBD
    }*/

  }


  //===============================================================================
  // 
  //  C o n s   
  // 
  //===============================================================================

  // ------ P r o c e s s -------

  part def Cons_Process :> Process {
    //-- I n t e r f a c e  --
    port input : EventDataPort { in :>> type : Message; }

    //-- P r o p e r t i e s  --
    attribute :>> Domain = Domain_Cons;

    //-- I n t e r n a l s --
    part cons: Cons; 
    connection cons_input : PortConnection connect input to cons.input;
  }

  // ------ T h r e a d -------

  part def Cons :> Thread {
    //-- I n t e r f a c e  --
    port input : EventDataPort { in :>> type : Message; }

    //-- P r o p e r t i e s  --
    attribute :>> Period = 40 [ms];  
    attribute :>> Dispatch_Protocol = Supported_Dispatch_Protocols::Periodic;
    attribute :>> Implementation_Language = Implementation_Languages::Rust;

     //-- B e h a v i o r    C o n s t r a i n t s --
    language "GUMBO" /*{
      state
         payload_sum: Base_Types::Integer_32;
            
      functions
      //  -- constant for initialization value for payload_sum
      def Init_Payload_Sum(): Base_Types::Integer_32 := 0 [i32];
          
	  //-- == I n t e g r a t i o n     C o n s t r a i n t s	
	  integration
	    assume Payload_Range: 
  	    (0 [i32] <= input.payload) & (input.payload <= 100 [i32]) ;

	  //-- == I n i t i a l i z e 
    initialize
      guarantee 
		    initSum: payload_sum == Init_Payload_Sum();   
 
 	  //-- == C o m p u t e 
    // TBD
    }*/

  }

  //===============================================================================
  //
  //  D a t a 
  //
  //===============================================================================

  part def Message :> Data {
    part payload : Base_Types::Integer_32;
    part control_num : Base_Types::Integer_32;
  }

  //===============================================================================
  // 
  //  M a i n    P r o c e s s o r     Processor
  // 
  //===============================================================================
  part def Main_Processor :> Processor {
    attribute :>> Frame_Period = 120 [ms];
    attribute :>> Clock_Period = 2 [ms];
  }

  // scheduling information
  //   ..declaration of scheduling domain identifiers 

  attribute Domain_Prod: CASE_Scheduling::Domain = 2;
  attribute Domain_Cons: CASE_Scheduling::Domain = 3;
}