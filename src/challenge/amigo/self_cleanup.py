import smach
import robot_smach_states

from robot_smach_states.util.designators import UnoccupiedArmDesignator


class Speak(smach.State):
    def __init__(self, robot, selected_entity_designator):
        smach.State.__init__(self, outcomes=["done"])
        self._robot = robot
        self._selected_entity_designator = selected_entity_designator

    def execute(self, userdata):

	e = self._selected_entity_designator.resolve()

        self._robot.speech.speak("I will clean the %s object which is a %s" % (e.id[0:4], e.type), block=True)

        return "done"


class SelfCleanup(smach.StateMachine):
    def __init__(self, robot, selected_entity_designator):

        smach.StateMachine.__init__(self, outcomes=['done'])

        with self:

            smach.StateMachine.add("SPEAK", Speak(robot, selected_entity_designator),
                                   transitions={"done": "GRAB"})

            smach.StateMachine.add("GRAB", robot_smach_states.grab.SjoerdsGrab(robot, selected_entity_designator, UnoccupiedArmDesignator(robot.arms, robot.leftArm, name="empty_arm_designator")),
		transitions={"done": "done", "failed": "done"})
