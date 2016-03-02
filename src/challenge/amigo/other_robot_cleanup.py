import smach
import robot_smach_states


class OtherRobotCleanup(smach.StateMachine):
    def __init__(self, robot, selected_entity_designator, location_id, segment_area):

        smach.StateMachine.__init__(self, outcomes=['done'])

        sentences = ["Jaguar, please clean this object %s the %s" % (segment_area, location_id),
                     "Jaguar, can you clean the trash %s the %s?" % (segment_area, location_id),
                     "Can another robot clean the garbage %s the %s?" % (segment_area, location_id)]
        with self:

            smach.StateMachine.add('SAY_OTHER_ROBOT_CLEANUP',
                                   robot_smach_states.Say(robot, sentences, block=True),
                                   transitions={"spoken": "done"})