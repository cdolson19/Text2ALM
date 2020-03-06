# Text2ALM #

My Thesis Project. 

## What is this repository for? ##

**Text2ALM** is written in Python3.

* Text2ALM takes narrative text as input and uses the VerbNet ontology to output an answer set of narrative properties.
* The goal of the system is support Question Answering tasks about a narrative by outputing an answer set of elements that can be queried. 

## Example ##
### System Input ###

Let the input file example.txt be given, containing the following narrative:
```
John traveled to the garage.
John picked up a football.
John went to the kitchen.
```

### System Output ###

The desired output answer set could contain elements such as:
```
location(John, garage, 1), location(John, garage, 2), location(John, kitchen, 3),
held_by(football, John, 2), held_by(football, John, 3),
location(football, garage, 2), location(football, kitchen, 3)
```

## Commands: ##
* To Run Single Narrative:
    * `python3 CommandCenter.py text2alm --input <Narrative_Txt_File_Path>`
    * Ex) `python3 CommandCenter.py text2alm --input \Text2ALM\TestFiles\BABI_Tests\Train\QA1\qa1_single-supporting-fact_train_0.txt`
    
* To Generate BABI Tests:
    * `python3 CommandCenter.py babiparser --input <BABI_File_Path>`
    * Ex) `python3 CommandCenter.py babiparser --input \Text2ALM\TestFiles\BABI_Tests\tasks_1-20_v1-2\en\qa1_single-supporting-fact_train.txt`

* To Create New VerbNet ALM Module
    * `python3 CommandCenter.py verbnetalmgenerator --input <VerbNet_Verb_Class_URL> --names <Theory_Name>.<Module_Name>`
    * Ex) `python3 CommandCenter.py verbnetalmgenerator --input http://verbs.colorado.edu/verb-index/vn/fire-10.10.php --names changing_possession.changing_possession`

* To Run BABI Tests:
    * `python3 CommandCenter.py babitests --input <BABI_QA_#> --size <Num_Tests>`
    * Ex) `python3 CommandCenter.py babitests --input QA1 --size 25`

## Key Components ##
### Text2DRS ###
The Text2DRS subsystem converts a given narrative text file to a discourse representation structure (DRS). 
This system identifies events in the narrative and represents the roles of the narrative's entities in the events. It does this by mapping events to their corresponding VerbNet classes and entities participating in the event to their corresponding VerbNet thematic roles. This system relies on Stanford CoreNLP, LTH, Semlink, and Verbnet.

### DRS2ALM ###
The DRS2ALM subsystem converts a DRS representation to an ALM system description. The ALM system description contains a theory defining the narrative's sorts and dependencies and a structure defining the narrative's event instances.

The following is an example ALM system description:
```
system description example
  theory example
    import run_51_3_2.run_51_3_2 from VN_class_library
    import get_13_5_1.get_13_5_1_1 from VN_class_library
    
    module example
      depends on run_51_3_2.run_51_3_2
    
      sort declarations
        john :: living_entity
        garage :: place
        football :: physical_object
        kitchen :: place
  
  structure example
    instances
      r1 in john
      r2 in garage
      r3 in football
      r4 in kitchen
      
      e1 in run_51_3_2
        vn_theme(r1) = true
        vn_location(r2) = true
        
      e2 in get_13_5_1_1
        vn_agent(r1) = true
        vn_theme(r3) = true
        
      e3 in run_51_3_2
        vn_theme(r1) = true
        vn_location(r4) = true
	
  temporal projection
  max steps 7
  history
    happened(e1, 0).
    happened(e2, 1).
    happened(e3, 2).
```

### CALM ###
Calm is an ALM implementation developed at Texas Tech University. The sytsem uses an ALM system description to produce an answer set of the system states.

### Stanford CoreNLP ###


### LTH SRL ###


## Additional Tool Subsystems ##
### BABI Parser ###
The Facebook bAbI project contains a set of 20 tasks for testing text understanding and reasoning [https://research.fb.com/downloads/babi/]. The 20 QA bAbI tasks are used to train, test, and evaluate this system.

The BABI Parser is a subsystem that can parse an input text file of BABI tests and create text files per narrative that is in a format readable by the Text2ALM system.

### VerbNetALMGenerator ###
The VerbNetALMGenerator is a subsystem that parse a VerbNet class page and output a ALM Module template of the VerbNet class. This is used to expand the system's underlying knowledge base.

## Contact Info ##
Craig Olson (cdolson@unomaha.edu)
