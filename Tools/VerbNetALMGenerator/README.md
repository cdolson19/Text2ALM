# VerbNetALMGenerator
Script to create a ALM representation of a VerbNet class by using a VerbNet URL the name of a Knowledge Representation theory, module, and sort.

## Running
To run, use the command:

`python3 VerbNetALMGenerator.py <VerbNet URL> <TheoryName.ModuleName.SortName>`

where VerbNet URL is the URL to a VerbNet class and TheoryName.ModuleName.SortName is a string listing the ALM theory, module, and sort that the verb inherits from.

For example, the command:

`python3 VerbNetALMGenerator.py http://verbs.colorado.edu/verb-index/vn/put-9.1.php theory.module.sort Hold.Grab.Grabs`

will create a .ALM file containing modules for Put 9.1, Put 9.1.1, and Put 9.1.2 that map to the sort Grabs in module Grab in theory hold.
