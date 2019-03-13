#!/usr/bin/env python
"""Autonomous Driving example."""
from __future__ import print_function

import logging
import pickle

from tulip import spec, synth


# The road and vehicles parameters and values
safe_distance = 2
road_length = 30
max_speed = 2


# Specifications

### env_vehicle

env_vars = {

    'lane_env': ["left", "right"],
    'pos_env': (0, road_length),
    'vlc_env': (0, max_speed),
    'ind_env': ["left", "right", "none"]}

env_init = {'pos_env = 10', 'vlc_env = 0', 'lane_env = "right"'}

env_safe =  {

    # If the two vehicles are in different lanes, no safety distance is required.
    # If the vehicles are in the same lane, three cases is taken care of:
        # 1. The other vehicle is farther from the road ends than the safety distance.
        #    In this case this vehicle needs to be positioned before or after the safety distance.
        # 2. The other vehicle is close to the road start.
        #    In this case the rear safety distance wraps around and some positions at the road end cannot be
        #    occupied by this vehicle.
        # 3. The other vehicle is close to the road end.
        #    In this case the front safety distance wraps around and some positions at the road start cannot
        #    be occupied by this vehicle.
    ("lane_ego != lane_env" +
     "| (pos_ego > {l}-1 && pos_ego < {L}-{l} && (pos_env - pos_ego > {l} | pos_env - pos_ego < -{l}))" +
     "| (pos_ego < {l} && pos_env > pos_ego+{l} && pos_env < pos_ego+{L}-{l})" +
     "| (pos_ego > {L}-{l}-1 && pos_env > pos_ego-{L}+{l} && pos_env+{l} < pos_ego)")
        .format(l=safe_distance, L=road_length),

    # Similar to previous comment, but this time it is made sure that the next position does not violate
    # the safety distance.
    ("lane_ego != lane_env' " +
     "| (pos_ego > {l}-1 && pos_ego < {L}-{l} && (pos_env' - pos_ego > {l} | pos_env' - pos_ego < -{l}))" +
     "| (pos_ego < {l} && pos_env' > pos_ego+{l} && pos_env' < pos_ego+{L}-{l})" +
     "| (pos_ego > {L}-{l}-1 && pos_env' > pos_ego-{L}+{l} && pos_env'+{l} < pos_ego)")
        .format(l=safe_distance, L=road_length),
    
    # If the vehicle changes lanes, from right to left, then the left indicator should be active.
    # Lane changes can only be performed if the vehicle is moving.
    ('''(lane_env = "right" && lane_env' = "left")  ->''' +
     '''(ind_env = "left"  && ind_env' = "none" && vlc_env > 0)'''),
    
    # Same as previous, but left to right.
    ('''(lane_env = "left" && lane_env' = "right")  ->''' +
     '''(ind_env = "right" && ind_env' = "none" && vlc_env > 0)'''),
    
    # When driving in the left lane it is not allowed to have the left indicator active.
    ('''lane_env = "left" -> (ind_env = "right"  |  ind_env = "none")'''),
    
    # Same as previous, but right lane and right indicator.
    ('''lane_env = "right" -> (ind_env = "left"  |  ind_env= "none")'''),
    
    # Modulus 30 implementation.
    # If the current position plus the current velocity is less than 30, the speed can be added to
    # the current position to get the next position.
    ('''((pos_env = {L}-2 && (vlc_env = 0 | vlc_env = 1)) | (0 <= pos_env && pos_env<= {L}-3) | (pos_env = {L}-1 && vlc_env = 0) ) ->''' +
     '''pos_env' = pos_env + vlc_env''')
        .format(L=road_length),
    
    # Modulus 30 implementation.
    # If the current position plus the current velocity is 30 or more, then the road length
    # is subtracted from the position, and then the velocity is added.
    ('''(pos_env = {L}-2 && vlc_env = 2 | pos_env >= {L}-1 && vlc_env > 0) ->''' +
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


sys_init = {'pos_ego = 0', 'vlc_ego = 0', 'lane_ego = "right"'}


sys_prog = {

     # An autonomous vehicle needs to be able to drive.
     # Force it to run infinitely many laps.
     'vlc_ego > 0',
     'pos_ego = 0'

           }

sys_safe = {

    # See specification for env_vehicle for explanations.
    ("lane_ego != lane_env" +
     "| (pos_env > 0 && pos_env < {L}-{l} && (pos_env - pos_ego > {l} | pos_env - pos_ego < -{l}))" +
     "| (pos_env < {l} && pos_ego > pos_env+{l} && pos_ego < pos_env+{L}-{l})" +
     "| (pos_env > {L}-{l}-1 && pos_ego > pos_env-{L}+{l} && pos_ego+{l} < pos_env)")
        .format(l=safe_distance, L=road_length),

    ("lane_ego' != lane_env" +
     "| (pos_env > 0 && pos_env < {L}-{l} && (pos_env - pos_ego' > {l} | pos_env - pos_ego' < -{l}))" +
     "| (pos_env < {l} && pos_ego' > pos_env+{l} && pos_ego' < pos_env+{L}-{l})" +
     "| (pos_env > {L}-{l}-1 && pos_ego' > pos_env-{L}+{l} && pos_ego'+{l} < pos_env)")
        .format(l=safe_distance, L=road_length),
   
    ('''(lane_ego = "right" && lane_ego' = "left") ->''' +
     '''(ind_ego = "left"  &&  ind_ego' = "none" && vlc_ego > 0)'''),
    
    ('''(lane_ego = "left" && lane_ego' = "right") ->''' +
     '''(ind_ego = "right"  && ind_ego' = "none" && vlc_ego > 0)'''),

    ('''lane_ego = "left" ->  (ind_ego = "right"  |  ind_ego = "none")'''),

    ('''lane_ego = "right" ->  (ind_ego = "left"  |  ind_ego = "none")'''),

    ("((pos_ego = {L}-2 && (vlc_ego = 0 | vlc_ego = 1)) | (0 <= pos_ego && pos_ego <= {L}-3) | (pos_ego = {L}-1 && vlc_ego = 0) ) ->" +
     "pos_ego' = pos_ego + vlc_ego")
        .format(L=road_length),
    
    ("(pos_ego = {L}-2 && vlc_ego = 2 | pos_ego >= {L}-1 && vlc_ego > 0) ->" +
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
specs.moore = False
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

