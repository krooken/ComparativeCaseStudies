#!/usr/bin/env python
"""Autonomous Driving example."""
from __future__ import print_function

import logging
import pickle

import numpy as np
from tulip import spec, synth, hybrid


# The road and vehicles parameters and values
width_road = 1
Safe_Distance = 2
road_length = 30
max_speed = 2


# Specifications

### env_vehicle

env_vars = {

    'lane_env': ["left", "right"],
    'pos_env': (0, road_length),
    'vlc_env': (0, max_speed),
    'ind_env': ["left", "right", "none"]}

env_init = {'pos_env = 10', 'vlc_env = 0', '''lane_env = "right"'''}

env_safe =  {

    ("lane_ego != lane_env" +
     "| (pos_ego > {l}-1 && pos_ego < {L}-{l} && (pos_env - pos_ego > {l} | pos_env - pos_ego < -{l}))" +
     "| (pos_ego < {l} && pos_env > pos_ego+{l} && pos_env < pos_ego+{L}-{l})" +
     "| (pos_ego > {L}-{l}-1 && pos_env > pos_ego-{L}+{l} && pos_env+{l} < pos_ego)")
        .format(l=Safe_Distance, L=road_length),

    ("lane_ego != lane_env' " +
     "| (pos_ego > {l}-1 && pos_ego < {L}-{l} && (pos_env' - pos_ego > {l} | pos_env' - pos_ego < -{l}))" +
     "| (pos_ego < {l} && pos_env' > pos_ego+{l} && pos_env' < pos_ego+{L}-{l})" +
     "| (pos_ego > {L}-{l}-1 && pos_env' > pos_ego-{L}+{l} && pos_env'+{l} < pos_ego)")
        .format(l=Safe_Distance, L=road_length),
    
    ("lane_ego != lane_env  &&" +
     "(-{l} < pos_env - pos_ego | pos_env - pos_ego < {l}) -> lane_env = lane_env'")
        .format(l=Safe_Distance),
    
    ('''(lane_env = "right" && lane_env' = "left")  ->''' +
     '''(ind_env = "left"  && ind_env' = "none" && (vlc_env > 0))'''),
    
    ('''(lane_env = "left" && lane_env' = "right")  ->''' +
     '''(ind_env = "right" && ind_env' = "none" && vlc_env > 0)'''),
    
    ('''lane_env = "left" -> (ind_env = "right"  |  ind_env = "none")'''),
     
    ('''lane_env = "right" -> (ind_env = "left"  |  ind_env= "none")'''),
     
    ('''((pos_env = {L}-1 && (vlc_env = 0 | vlc_env = 1)) | (0 <= pos_env && pos_env<= {L}-2) ) ->''' +
     '''pos_env' = pos_env + vlc_env''')
        .format(L=road_length),
     
    ('''(pos_env = {L}-1 && vlc_env = 2 | pos_env >= {L}) ->''' +
     '''pos_env' = pos_env-{L} + vlc_env''')
        .format(L=road_length),

    # type bounds
    ("(0 <= vlc_env  &&  vlc_env <= {mxs})' ").format(mxs=max_speed)
     
    }

env_prog =  {
             }



### ego_vehicle:


sys_vars = {

    'lane_ego': ["left", "right"],
    'pos_ego': (0, road_length),
    'vlc_ego': (0, max_speed),
    'ind_ego': ["left", "right", "none"]}


sys_init = {'pos_ego = 0', 'vlc_ego = 0', '''lane_ego = "right"'''}


sys_prog = {

     'vlc_ego > 0',
     'pos_ego = 0'

           }

sys_safe = {

    ("lane_ego != lane_env" +
     "| (pos_env > 0 && pos_env < {L}-{l} && (pos_env - pos_ego > {l} | pos_env - pos_ego < -{l}))" +
     "| (pos_env < {l} && pos_ego > pos_env+{l} && pos_ego < pos_env+{L}-{l})" +
     "| (pos_env > {L}-{l}-1 && pos_ego > pos_env-{L}+{l} && pos_ego+{l} < pos_env)")
        .format(l=Safe_Distance, L=road_length),

    ("lane_ego' != lane_env" +
     "| (pos_env > 0 && pos_env < {L}-{l} && (pos_env - pos_ego' > {l} | pos_env - pos_ego' < -{l}))" +
     "| (pos_env < {l} && pos_ego' > pos_env+{l} && pos_ego' < pos_env+{L}-{l})" +
     "| (pos_env > {L}-{l}-1 && pos_ego' > pos_env-{L}+{l} && pos_ego'+{l} < pos_env)")
        .format(l=Safe_Distance, L=road_length),

    ("lane_ego != lane_env  &&" +
     "(-{l} < pos_env - pos_ego | pos_env - pos_ego < {l}) -> lane_ego = lane_ego'")
        .format(l=Safe_Distance),
   
    ('''(lane_ego = "right" && lane_ego' = "left") ->''' +
     '''(ind_ego = "left"  &&  ind_ego' = "none" && vlc_ego > 0)'''),
    
    ('''(lane_ego = "left" && lane_ego' = "right") ->''' +
     '''(ind_ego = "right"  && ind_ego' = "none" && vlc_ego > 0)'''),

    ('''lane_ego = "left" ->  (ind_ego = "right"  |  ind_ego = "none")'''),

    ('''lane_ego = "right" ->  (ind_ego = "left"  |  ind_ego = "none")'''),

    ("((pos_ego = {L}-1 && (vlc_ego = 0 | vlc_ego = 1)) | (0 <= pos_ego && pos_ego <= {L}-2) ) ->" +
     "pos_ego' = pos_ego + vlc_ego")
        .format(L=road_length),
    
    ("(pos_ego = {L}-1 && vlc_ego = 2 | pos_ego >= {L}) ->" +
     "pos_ego' = pos_ego-{L} + vlc_ego")
        .format(L=road_length),

    # type bounds
    ("(0 <= vlc_ego && vlc_ego <= {mxs})' ").format(mxs=max_speed)
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

