#!/usr/bin/python
import rospy
import smach

import sys

import robot_smach_states
from clean_inspect import CleanInspect

from robocup_knowledge import load_knowledge
challenge_knowledge = load_knowledge('r5cop_demo')


def setup_statemachine(robot):

    sm = smach.StateMachine(outcomes=['Done', 'Aborted'])

    with sm:

        # Start challenge via StartChallengeRobust
        smach.StateMachine.add( "START_CHALLENGE_ROBUST",
                                robot_smach_states.StartChallengeRobust(robot, challenge_knowledge.starting_point,
                                                                        use_entry_points=True),
                                transitions={"Done": "SAY_START_CHALLENGE",
                                             "Aborted": "SAY_START_CHALLENGE",
                                             "Failed": "SAY_START_CHALLENGE"})

        smach.StateMachine.add('SAY_START_CHALLENGE',
                               robot_smach_states.Say(robot, ["Starting R5COP Cooperative cleaning demonstrator",
                                                              "What a mess here, let's clean this room!",
                                                              "Let's see if I can find some garbage here",
                                                              "All I want to do is clean this mess up!"], block=False),
                               transitions={"spoken": "INSPECT_0"})

        for i, e_id in enumerate(challenge_knowledge.inspection_ids):
            next_i = i + 1 if i + 1 < len(challenge_knowledge.inspection_ids) else 0

            smach.StateMachine.add("INSPECT_%d" % i,
                                   CleanInspect(robot, e_id, challenge_knowledge.known_types),
                                   transitions={"done": "INSPECT_%d" % next_i})
    return sm

if __name__ == '__main__':
    rospy.init_node('r5cop_demo_amigo')

    # Check if we have something specified to inspect
    if len(challenge_knowledge.inspection_ids) < 1:
        rospy.logerr("The challenge knowledge inspection_ids list should contain at least one entry!")
        sys.exit(1)

    robot_smach_states.util.startup(setup_statemachine, challenge_name="r5cop_demo_amigo")