#!/usr/bin/env python
"""Stick picking game."""
from __future__ import print_function

import logging
import pickle

from tulip import spec, synth

import utils

sticks = 7
max_moves = 3


# Specifications
# Environment variables and assumptions

env_vars = {
    'player_2_picks': (0, max_moves)
    }

env_init = {
    'player_2_picks = 0'
    }

env_safe = {
    '(sticks > 0 && player_turn=2) -> (player_2_picks = 1 || player_2_picks = 2 || player_2_picks = 3)',
    '(sticks = 0 || player_turn!=2) -> player_2_picks=0',
    'player_2_picks <= sticks'
    }

sys_vars = {
    'sticks': (0, sticks),
    'player_1_picks': (0, max_moves),
    'player_turn': (1,2)
    }

sys_init = {
    'player_turn=1',
    'sticks = {sticks}'.format(sticks=sticks),
    'player_1_picks = 1 || player_1_picks = 2 || player_1_picks = 3'
    }

sys_safe = {
    "sticks>0 -> (player_turn' != player_turn)",
    "sticks=0 -> (player_turn' = player_turn)",
    '(sticks>0 && player_turn=1) -> (player_1_picks = 1 || player_1_picks = 2 || player_1_picks = 3)',
    '(sticks=0 || player_turn!=1) -> player_1_picks=0',
    'player_1_picks <= sticks',
    "(sticks>0 && player_turn=1) -> sticks'=sticks-player_1_picks",
    "(sticks>0 && player_turn=2) -> sticks'=sticks-player_2_picks",
    "sticks=0 -> sticks'=0",
    '(sticks>0 && player_turn=1) -> player_1_picks<sticks'
    }


logging.basicConfig(level=logging.WARNING)

# Create the specification
specs = spec.GRSpec(env_vars, sys_vars, env_init, sys_init,
                    env_safe, sys_safe)
specs.qinit = '\E \A'
specs.moore = True
specs.plus_one = False

# Synthesize the built in TuLiP way.
print(synth.is_realizable(specs, ignore_sys_init=False, ignore_env_init=False))
ctrl = synth.synthesize(specs, ignore_sys_init=False, ignore_env_init=False)
assert ctrl is not None, 'unrealizable'


with open('two_players_controller.pickle', 'wb') as f:
    pickle.dump(ctrl, f)

# Save the controller as a picture. The initial transitions will cover more
# than specified.
if not ctrl.save('two_players.eps'):
    print(ctrl)



# Synthesize manually by copying from TuLiP source code.
# Also force to use cudd.
ignore_env_init = False
ignore_sys_init = False
specs = synth._spec_plus_sys(
        specs, None, None,
        ignore_env_init,
        ignore_sys_init)
realizable = synth.omega_int.is_realizable(specs, use_cudd=False)
print(realizable)

strategy = synth.omega_int.synthesize_enumerated_streett(specs, use_cudd=False)

# This is the shorthand way to create a Mealy machine of the strategy, but
# this way creates falsifiable initial transitions.
ctrl = synth._trim_strategy(strategy, specs, rm_deadends=True)
assert ctrl is not None, 'unrealizable'

full_mealy = synth.strategy2mealy(strategy, specs)
full_mealy.save('two_players_all_transitions.eps')

# Use custom code to create Mealy machine. The initial transitions will only be
# created to states that fullfill both env_init and sys_init.
mealy = utils.strategy2mealy(strategy, specs)
mealy.remove_deadends()
mealy.save('two_players_strict_init.eps')


# Showing how to construct a valid strategy by falsifying assumptions.
# Add a specification which puts player two in an impossible situation.
# Player one will force player two into a situation where one stick is left.
# However, player two cannot do anything. (S)he has to select sticks, but this
# conflicts with this new specification.
env_safe |= {'(sticks>0 && player_turn=2) -> player_2_picks<sticks'}

# Create the specification
specs = spec.GRSpec(env_vars, sys_vars, env_init, sys_init,
                    env_safe, sys_safe)
specs.qinit = '\E \A'
specs.moore = True
specs.plus_one = False

# Now, TuLiP will report that it is realizable, but the synthesis will fail
# when it tries to produce a automaton without deadends.
print(synth.is_realizable(specs, ignore_sys_init=False, ignore_env_init=False))

# Synthesizing with internal methods works fine.
strategy = synth.omega_int.synthesize_enumerated_streett(specs, use_cudd=False)

# And here is the automaton before any triming has taken place.
full_mealy = synth.strategy2mealy(strategy, specs)
full_mealy.save('two_players_falsified_all_transitions.eps')

# Here TuLiP fails when it tries to trim the strategy
ctrl = synth.synthesize(specs, ignore_sys_init=False, ignore_env_init=False)
