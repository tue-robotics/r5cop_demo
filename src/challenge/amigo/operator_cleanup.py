import smach
import robot_smach_states


class OperatorCleanup(smach.StateMachine):
    def __init__(self, robot, selected_entity_designator, location_id, segment_area):

        smach.StateMachine.__init__(self, outcomes=['done'])

        sentences = ["Operator, please clean this object %s the %s" % (segment_area, location_id),
                     "Operator, can you clean the trash %s the %s?" % (segment_area, location_id),
                     "Can somebody clean the garbage %s the %s?" % (segment_area, location_id)]

        with self:

            smach.StateMachine.add('SAY_OPERATOR_CLEANUP',
                                   robot_smach_states.Say(robot, sentences, block=True),
                                   transitions={"spoken": "done"})