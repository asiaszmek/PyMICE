#!/usr/bin/env python
# encoding: utf-8
###############################################################################
#                                                                             #
#    PyMICE library                                                           #
#                                                                             #
#    Copyright (C) 2017 Jakub M. Dzik a.k.a. Kowalski (Laboratory of          #
#    Neuroinformatics; Nencki Institute of Experimental Biology of Polish     #
#    Academy of Sciences)                                                     #
#                                                                             #
#    This software is free software: you can redistribute it and/or modify    #
#    it under the terms of the GNU General Public License as published by     #
#    the Free Software Foundation, either version 3 of the License, or        #
#    (at your option) any later version.                                      #
#                                                                             #
#    This software is distributed in the hope that it will be useful,         #
#    but WITHOUT ANY WARRANTY; without even the implied warranty of           #
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the            #
#    GNU General Public License for more details.                             #
#                                                                             #
#    You should have received a copy of the GNU General Public License        #
#    along with this software.  If not, see http://www.gnu.org/licenses/.     #
#                                                                             #
###############################################################################
import os

# dependence tracking
from . import _dependencies
import types
__dependencies__ = _dependencies.moduleDependencies(*[x for x in globals().values()
                                                      if isinstance(x, types.ModuleType)])


__NeuroLexID__ = 'nlx_158570'
__RRID__ = 'RRID:' + __NeuroLexID__
__version__ = open(os.path.join(os.path.dirname(__file__),
                                'data/__version__.txt'),
                   'r').read()
__ID__ = __RRID__ + ' ' + __version__
