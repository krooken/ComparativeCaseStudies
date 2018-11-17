#!/usr/bin/env python
"""Autonomous cars example."""
from __future__ import print_function

import logging
import pickle

import numpy as np
from tulip import spec, synth, hybrid
from polytope import box2poly
from tulip.abstract import prop2part, discretize
from tulip.abstract.plot import plot_partition


# The road and vehicles parameters and values
width_road = 1
Safe_Distance = 2
road_length = 100
max_speed = 2


# Specifications

### env_vehicle

env_vars = {

    'lane_env': ["left", "right"],

    'pos_env': (0, road_length),

    'vlc_env': (0, max_speed),

    'ind_env': ["left", "right", "none"]}

env_init = {'''(lane_env = "right")''', 'pos_env = 10', 'vlc_env = 0'}

env_safe =  {

    " (lane_adv = lane_env) | ((pos_env - pos_adv)>= -{l}) | ((pos_env - pos_adv)<= -{l}) ".format(
        l=Safe_Distance),

    " (lane_adv = lane_env') | ((pos_env' - pos_adv)>= -{l}) | ((pos_env' - pos_adv)<= -{l}) ".format(
        l=Safe_Distance),

    '''
    (lane_adv != lane_env  &&  (-{l} < pos_env - pos_adv | pos_env - pos_adv < {l}) -> (lane_env = lane_env'))
    '''.format(l=Safe_Distance),

    '''
    ((lane_env' = "left" && lane_env = "right")  ->  (ind_env = "left"  && ind_env' = "none"))
    ''',

    '''
    ((lane_env' = "right" && lane_env = "left")  ->  (ind_env = "right" && ind_env' = "none"))
    ''',

    '''
    ((lane_env = "left") ->  (ind_env = "right"  |  ind_env= "none"))
    ''',

    '''
    ((lane_env = "right") ->  (ind_env = "left"  |  ind_env= "none"))
    ''',

    "((pos_env = 99 && (vlc_env = 0 || vlc_env = 1)) || ((0 <= pos_env) && (pos_env<= 98)) )-> (pos_env' = pos_env + vlc_env)",
   
    "((pos_env = 99 && vlc_env = 2) || (pos_env >= 100))-> (pos_env' = (pos_env-100) + vlc_env)",


    # type bounds
    " (0 <= vlc_env  &&  vlc_env <= {mxs})' ".format(mxs=max_speed)
    }

env_prog =  {

    '(vlc_env > 0)',

    'pos_env = 0'}



### adv_vehicle:


sys_vars = {

    'lane_adv': ["left", "right"],

    'pos_adv': (0, road_length),

    'vlc_adv': (0, max_speed),

    'ind_adv': ["left", "right", "none"]}


sys_init = {'''(lane_adv = "right")''', 'pos_adv = 0', 'vlc_adv = 0'}


sys_prog = {

    'ind_adv = "none" ',

    'pos_adv = {end}'.format(end=road_length)}

sys_safe = {

    " (lane_adv = lane_env) | ((pos_env - pos_adv)>= -{l}) | ((pos_env - pos_adv)<=-{l}) ".format(
        l=Safe_Distance),

    " (lane_adv' = lane_env) | ((pos_env - pos_adv')>= -{l}) | ((pos_env - pos_adv')<=-{l}) ".format(
        l=Safe_Distance),

    '''
    (lane_adv != lane_env  &&  (-{l} < pos_env - pos_adv | pos_env - pos_adv < {l}) -> (lane_adv = lane_adv'))
    '''.format(l=Safe_Distance),
   
    '''
    ((lane_adv' = "left" && lane_adv = "right")  ->  (ind_adv = "left"  &&  ind_adv' = "none"))
    ''',
    
    '''
    ((lane_adv' = "right" && lane_adv = "left")  ->  (ind_adv = "right"  && ind_adv' = "none"))
    ''',

    '''
    ((lane_adv = "left") ->  (ind_adv = "right"  |  ind_adv= "none"))
    ''',

    '''
    ((lane_adv = "right") ->  (ind_adv = "left"  |  ind_adv= "none"))
    ''',

    "((pos_adv = 99 && (vlc_adv = 0 || vlc_adv = 1)) || ((0 <= pos_adv) && (pos_adv <= 98)) )-> (pos_adv' = pos_adv + vlc_adv)",
    
    "((pos_adv = 99 && vlc_adv = 2) || (pos_adv >= 100))-> (pos_adv' = (pos_adv-100) + vlc_adv)",


    # type bounds
    " (0 <= vlc_adv  &&  vlc_adv <= {mxs})' ".format(mxs=max_speed)
     }


logging.basicConfig(level=logging.WARNING)
show = False

# Create the specification
specs = spec.GRSpec(env_vars, sys_vars, env_init, sys_init,
                    env_safe, sys_safe, env_prog, sys_prog)
specs.qinit = '\E \A'
specs.moore = True
specs.plus_one = True

# @synthesize_section@
# Synthesize
realizable = synth.omega_int.is_realizable(specs, use_cudd=True)
print(realizable)

strategy = synth.omega_int.synthesize_enumerated_streett(specs, use_cudd=True)
ctrl = synth._trim_strategy(strategy, specs, rm_deadends=True)
assert ctrl is not None, 'unrealizable'

with open('synthesized_controller.pickle', 'wb') as f:
    pickle.dump(ctrl, f)

