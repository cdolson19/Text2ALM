# Text2ALM #

A Thesis Project developed at the University of Nebraska Omaha by Craig Olson and Dr. Yuliya Lierler.

## Publications Related to this Work ##
* Processing Narratives by Means of Action Languages. [2019 Thesis Report](https://digitalcommons.unomaha.edu/compscistudent/1/)
* Information Extraction Tool Text2ALM: From Narratives to Action Language System Descriptions. [ICLP 2019 Report](https://works.bepress.com/yuliya_lierler/86/)
* An Architecture of Semantic Information Extraction Tool Text2ALM. [OSTIS 2020 Report](https://works.bepress.com/yuliya_lierler/91/)

## What is this repository for? ##

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

## Setup ##
Go to this repository's [wiki](https://github.com/cdolson19/Text2ALM/wiki) to see how to prepare and run the system. 

## Contact Info ##
Craig Olson (cdolson@unomaha.edu)
