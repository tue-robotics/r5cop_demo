import smach

import robot_smach_states
from robot_smach_states.util.designators import EdEntityDesignator, VariableDesignator

from handle_detected_entities import HandleDetectedEntities
from robot_skills.classification_result import ClassificationResult


class CleanInspect(smach.StateMachine):
    def __init__(self, robot, entity_id, room_id, navigate_area, segment_areas, known_types):

        smach.StateMachine.__init__(self, outcomes=['done'])

        # Set up the designators for this machine
        e_classifications_des = VariableDesignator([], resolve_type=[ClassificationResult])
        e_des = EdEntityDesignator(robot, id=entity_id)
        room_des = EdEntityDesignator(robot, id=room_id)

        with self:

            smach.StateMachine.add("RESET_ED", robot_smach_states.ResetED(robot),
                                   transitions={'done': 'NAVIGATE'})

            smach.StateMachine.add("NAVIGATE",
                                   robot_smach_states.NavigateToSymbolic(robot, {e_des: navigate_area, room_des: "in"},
                                                                         e_des),
                                   transitions={'arrived': 'SEGMENT_SAY_0',
                                                'unreachable': 'SAY_UNREACHABLE',
                                                'goal_not_defined': 'SAY_UNREACHABLE'})

            for i, segment_area in enumerate(segment_areas):

                smach.StateMachine.add("SEGMENT_SAY_%d" % i,
                                       robot_smach_states.Say(robot, ["Looking %s the %s"
                                                                      % (segment_area, entity_id)], block=False),
                                       transitions={"spoken": "SEGMENT_%d" % i})

                next_state = "SEGMENT_SAY_%d" % (i + 1) if i + 1 < len(segment_areas) else "HANDLE_DETECTED_ENTITIES"
                smach.StateMachine.add('SEGMENT_%d' % i, robot_smach_states.SegmentObjects(robot,
                                                                                           e_classifications_des.writeable,
                                                                                           e_des,
                                                                                           segment_area),
                                       transitions={'done': next_state})

            smach.StateMachine.add("SAY_UNREACHABLE",
                                   robot_smach_states.Say(robot, ["I failed to inspect the %s" % entity_id], block=False),
                                   transitions={"spoken": "done"})

            smach.StateMachine.add("HANDLE_DETECTED_ENTITIES",
                                   HandleDetectedEntities(robot, e_classifications_des, known_types),
                                   transitions={"done": "done"})
