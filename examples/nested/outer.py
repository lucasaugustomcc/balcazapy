# -*- coding: utf-8 -*-
### Do not edit the lines at the top and bottom of this file.
### Edit the workflow description between START and FINISH comments
from balcaza.t2types import *
from balcaza.t2activity import *
from balcaza.t2flow import *

### START editing your workflow below here
#
# This example creates a simple nested workflow. First, create the main workflow:

rserve = RServer()

flow = Workflow(title='Create Projection Matrix', author="Maria and Jon",
	description="Create a projection matrix from a stage matrix and a list of stages")

# and add the nested workflow (treat the nested workflow just like any other acivity)

flow.task.ProjectionMatrix = NestedWorkflowFile('inner.py')

flow.input.speciesName = flow.task.ProjectionMatrix.input.speciesName


flow.input.stageMatrixFile = TextFile(
	description = """The stage matrix file input port:

Here comes the stage matrix without the stage names (as you see in the example).  It should be provied as a txt-file.  

Example from:
J. Gerard B. Oostermeijer; M.L. Brugman; E.R. de Boer; H.C.M. Den Nijs. 1996. Temporal and Spatial Variation in the Demography of Gentiana pneumonanthe, a Rare Perennial Herb. The Journal of Ecology, Vol. 84(2): 153-166.
""",
	example = """0.0000	0.0000	0.0000	7.6660	0.0000
0.0579	0.0100	0.0000	8.5238	0.0000
0.4637	0.8300	0.9009	0.2857	0.8604
0.0000	0.0400	0.0090	0.6190	0.1162
0.0000	0.0300	0.0180	0.0000	0.0232"""
)

# List types must identify what the list contains

flow.input.stages = List[String]


rshell = rserve.runFile(
	"readMatrix.R",
	inputs = dict(stage_matrix_file=TextFile, stages=Vector[String]),
	outputs = dict(stage_matrix=RExpression)
	)

flow.task.ReadMatrix = rshell

flow.input.stageMatrixFile >> flow.task.ReadMatrix.input.stage_matrix_file
flow.input.stages >> flow.task.ReadMatrix.input.stages

flow.task.ReadMatrix.output.stage_matrix >> flow.task.ProjectionMatrix.input.stageMatrix # not inner.input.stageMatrix !

flow.output.projectionMatrix = PNGImage(description = "A projection matrix")

flow.task.ProjectionMatrix.output.projectionMatrix >> flow.output.projectionMatrix


# Set compressed = True to create a smaller workflow file
# Set compressed = False to create a workflow indented for readability

compressed = True

# FINISH your workflow above here, and do not change the lines below

if __name__ == '__main__':
	import codecs, sys
	import maximal.XMLExport as XMLExport

	UTF8Writer = codecs.getwriter('utf8')
	stdout = UTF8Writer(sys.stdout)

	if compressed:
		flow.exportXML(XMLExport.XMLExporter(XMLExport.XMLCompressor(stdout)))
	else:
		flow.exportXML(XMLExport.XMLExporter(XMLExport.XMLIndenter(stdout)))
