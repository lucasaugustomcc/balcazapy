# -*- coding: utf-8 -*-
#
# Copyright (c) 2013 Cardiff University
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from balcaza.t2types import *
from balcaza.t2activity import *
from balcaza.t2flow import Workflow

flow = Workflow(title='Place Effect', author=u'Maria Paula Balcázar-Vargas, Jonathan Giddy and Gerard Oostermeijer')

flow.input.places = List[String](
	description="Site names",
	example="[Dwingeloo 1, Dwingeloo 2, Dwingeloo 3, Lochem, Terschelling]"
	)

flow.input.stages = List[String](
	description='''Growth stages of the species populations

The names of the stages or categories of the input matrix.

In the following example, the matrix has 5 stages or categories:

	S	J	V	G	D
S	0.0000	0.0000	0.0000	7.6660	0.0000
J	0.0579	0.0100	0.0000	8.5238	0.0000
V	0.4637	0.8300	0.9009	0.2857	0.8604
G	0.0000	0.0400	0.0090	0.6190	0.1162
D	0.0000	0.0300	0.0180	0.0000	0.0232

The stages of this matrix are: 
1) Seedlings		S 
2) Juveniles		J
3) Vegetative		V
4) Reproductive individuals	G
5) Dormant plants	D
''',
	example='[S, J, V, G, D]'
	)

flow.input.pooled_matrix_file = TextFile

RequestStageMatrices = flow.task.RequestStageMatrices << InteractionPage(
	'http://biovel.googlecode.com/svn/tags/mpm-20131215/select_matrices.html',
	inputs = dict(
		title=String(description="Message displayed at top of page"),
		values=List[String](description="Values for which user will select input files"),
		field=String(description="Name of field in input port values"),
		multiple=String['true','false'](description="""true = select multiple input files per value
false = select a single input file per value"""),
		),
	outputs = dict(
		matrices=List[List[String]](description="""Contents of the files per value

Each element of the top-level list is related to each element of the input port values. For each value there is a list containing the contents of each file selected for a value. If the input port multiple is false, there will only be one string in each of these inner lists""")
		)
	)

RequestStageMatrices.input.title = "Select multiple stage matrices from different years for each location"
RequestStageMatrices.input.field = "Location"
RequestStageMatrices.input.multiple = "true"
flow.input.places | RequestStageMatrices.input.values

rserve = RServer()

import sys
sys.path.append('')
from util.r.file import ReadMatrixFromFile

ReadStageMatrix = flow.task.ReadStageMatrix << ReadMatrixFromFile(rserve)

RequestStageMatrices.output.matrices |++ ReadStageMatrix.input.matrix_file
matrices_LLRn2 = ReadStageMatrix.output.matrix
flow.input.stages | ReadStageMatrix.input.xlabels
flow.input.stages | ReadStageMatrix.input.ylabels

ReadPooledMatrix = flow.task.ReadPooledMatrix << ReadMatrixFromFile(rserve)
flow.input.pooled_matrix_file | ReadPooledMatrix.input.matrix_file
flow.input.stages | ReadPooledMatrix.input.xlabels
flow.input.stages | ReadPooledMatrix.input.ylabels

from balcaza.activity.rstats.list import ListRtoRList

MeanMatrix = flow.task.MeanMatrix << rserve.code('''
# mean(matrix) usually returns the mean of all values in the matrix
# mean(list of matrices) isn't present in base R, but the logical return value
# would be a list (or vector) of the mean of each matrix in the list.  However,
# package "popbio" overides mean for lists to return a matrix containing the
# mean of values at each coordinate in all the matrices.  To emphasise that we
# are calling this function, we call it with the function's full name, including
# type.
library(popbio)
mean_matrix <- mean.list(matrices)
''',
	inputs = dict(matrices = RExpression),
	outputs = dict(mean_matrix = RExpression),
	defaultInput = 'matrices',
	defaultOutput = 'mean_matrix'
	)

mean_matrices_LRn2 = matrices_LLRn2 |- ListRtoRList | MeanMatrix

AddNames = flow.task.AddNames << rserve.code(
	'names(expr) <- labels',
	inputs=dict(labels=Vector[String]),
	defaultInput='expr',
	defaultOutput='expr'
	)

flow.input.places | AddNames.input.labels

CalculatePlaceEffect = flow.task.CalculatePlaceEffect << NestedZapyFile('LTRE.py',
    inputs = dict(
        matrices = RExpression,
        pooled_matrix = RExpression,
        xticks = List[String],
        xlabel = String,
        plot_colour = String,
        plot_title = String,
        ylabel = String
        ),
    outputs = dict(
        LTRE_Analysis = RExpression,
        graph = PNG_Image,
        LTRE_Results = List[Number],
        LTRE_Results_RLn = RExpression
        )
)

mean_matrices_LRn2 |- ListRtoRList | AddNames | CalculatePlaceEffect.input.matrices

ReadPooledMatrix.output.matrix | CalculatePlaceEffect.input.pooled_matrix
CalculatePlaceEffect.input.xlabel = 'Places'
flow.input.places | CalculatePlaceEffect.input.xticks
CalculatePlaceEffect.input.ylabel = 'Place Effect'
CalculatePlaceEffect.input.plot_colour = 'lightgreen'
CalculatePlaceEffect.extendUnusedInputs()

from balcaza.activity.rstats.format import RExpressionToString

PrintAnalysis = flow.task.PrintAnalysis << RExpressionToString(rserve)
CalculatePlaceEffect.output.LTRE_Analysis | PrintAnalysis | flow.output.LTRE_Analysis

PrintResults = flow.task.PrintResults << RExpressionToString(rserve)
CalculatePlaceEffect.output.LTRE_Results_RLn | PrintResults | flow.output.LTRE_Results

CalculatePlaceEffect.output.graph | flow.output.LTRE_Graph


