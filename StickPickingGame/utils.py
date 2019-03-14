#!/usr/bin/env python

# Copyright (c) 2010-2018 by California Institute of Technology
# Copyright (c) 2014-2018 by The Regents of the University of Michigan
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder(s) nor the names of its
#    contributors may be used to endorse or promote products derived
#    from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL THE
# COPYRIGHT HOLDERS OR THE CONTRIBUTORS BE LIABLE FOR ANY DIRECT,
# INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
# HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
# STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED
# OF THE POSSIBILITY OF SUCH DAMAGE.

"""Utilities to help with synthesis."""
from __future__ import print_function

import logging
import pprint

from tulip import transys
from tulip.spec import translation as ts

logger = logging.getLogger(__name__)

def _conj(iterable, unary='', op='&&'):
    return ' {op} '.format(op=op).join(
        ['{u}({s})'.format(u=unary, s=s) for s in iterable])

def isinit_test(self, no_str):
    self.str_to_int()
    init = {'env': self.env_init, 'sys': self.sys_init}
    pyinit = dict()
    for side, clauses in init.items():
        if no_str:
            clauses = [self._bool_int[x] for x in clauses]
        logger.info('clauses to compile: ' + str(clauses))
        c = [ts.translate_ast(self.ast(x), 'python').flatten()
             for x in clauses]
        logger.info('after translation to python: ' + str(c))
        s = _conj(c, op='and')
        if not s:
            s = 'True'
        pyinit[side] = s
    # Do the conjunction of assumptions (env_init) and assertions (sys_init)
    s = '({assumption}) and ({assertion})'.format(
        assumption=pyinit['env'],
        assertion=pyinit['sys'])
    # The original code looked like this. Every state was considered a valid
    # initial state if not (env_init) or (sys_init)
#    s = 'not ({assumption}) or ({assertion})'.format(
#        assumption=pyinit['env'],
#        assertion=pyinit['sys'])
    logger.info('should be valid in initial states: {formula}'.format(formula=s))
    return compile(s, '<string>', 'eval')

def strategy2mealy(A, spec):
    """Convert strategy to Mealy transducer.

    Note that the strategy is a deterministic game graph,
    but the input C{A} is given as the contraction of
    this game graph.

    @param A: strategy
    @type A: C{networkx.DiGraph}

    @type spec: L{GRSpec}

    @rtype: L{MealyMachine}
    """
    assert len(A) > 0
    logger.info('converting strategy (compact) to Mealy machine')
    env_vars = spec.env_vars
    sys_vars = spec.sys_vars
    mach = transys.MealyMachine()
    inputs = transys.machines.create_machine_ports(env_vars)
    mach.add_inputs(inputs)
    outputs = transys.machines.create_machine_ports(sys_vars)
    mach.add_outputs(outputs)
    str_vars = {
        k: v for k, v in env_vars.items()
        if isinstance(v, list)}
    str_vars.update({
        k: v for k, v in sys_vars.items()
        if isinstance(v, list)})
    mach.states.add_from(A)
    # transitions labeled with I/O
    for u in A:
        for v in A.successors_iter(u):
            d = A.node[v]['state']
            d = _int2str(d, str_vars)
            mach.transitions.add(u, v, **d)

            logger.info('node: {v}, state: {d}'.format(v=v, d=d))
    # special initial state, for first reaction
    initial_state = 'Sinit'
    mach.states.add(initial_state)
    mach.states.initial.add(initial_state)
    # fix an ordering for keys
    # because tuple(dict.items()) is not safe:
    # https://docs.python.org/2/library/stdtypes.html#dict.items
    try:
        u = next(iter(A))
        keys = A.node[u]['state'].keys()
    except Exception:
        logger.warning('strategy has no states.')
    # to store tuples of dict values for fast search
    # isinit = spec.compile_init(no_str=True)
    # Previous line is the original. Use this module's isinit_test() to create
    # transitions to only specified initial conditions.
    isinit = isinit_test(spec, True)
    # Mealy reaction to initial env input
    init_valuations = set()
    tmp = dict()

    for u, d in A.nodes_iter(data=True):
        var_values = d['state']
        vals = tuple(var_values[k] for k in keys)
        # already an initial valuation ?
        if vals in init_valuations:
            continue
        # add edge: Sinit -> u ?
        tmp.update(var_values)
        if eval(isinit, tmp):
            label = _int2str(var_values, str_vars)
            mach.transitions.add(initial_state, u, **label)
            # remember variable values to avoid
            # spurious non-determinism wrt the machine's memory
            #
            # in other words,
            # "state" omits the strategy's memory
            # hidden (existentially quantified)
            # so multiple nodes can be labeled with the same state
            #
            # non-uniqueness here would be equivalent to
            # multiple choices for initializing the hidden memory.
            init_valuations.add(vals)
            logger.debug('found initial state: {u}'.format(u=u))
        logger.debug('machine vertex: {u}, has var values: {v}'.format(
                     u=u, v=var_values))
    n = len(A)
    m = len(mach)
    assert m == n + 1, (n, m)
    if not mach.successors('Sinit'):
        raise Exception(
            'The machine obtained from the strategy '
            'does not have any initial states !\n'
            'The strategy is:\n'
            'vertices:' + pprint.pformat(A.nodes(data=True)) + 2 * '\n' +
            'edges:\n' + str(A.edges()) + 2 * '\n' +
            'and the machine:\n' + str(mach) + 2 * '\n' +
            'and the specification is:\n' + str(spec.pretty()) + 2 * '\n')
    return mach


def _int2str(label, str_vars):
    """Replace integers with string values for string variables.

    @param label: mapping from variable names, to integer (as strings)
    @type label: C{dict}

    @param str_vars: mapping that defines those variables that
        should be converted from integer to string variables.
        Each variable is mapped to a list of strings that
        comprise its range. This list defines how integer values
        correspond to string literals for that variable.
    @type str_vars: C{dict}

    @rtype: C{dict}
    """
    label = dict(label)
    label.update({k: str_vars[k][int(v)]
                 for k, v in label.items()
                 if k in str_vars})
    return label
