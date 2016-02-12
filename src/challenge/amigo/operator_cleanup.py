import smach


class Test(smach.State):
    def __init__(self, robot, selected_entity_designator):
        smach.State.__init__(self, outcomes=["done"])
        self._robot = robot
        self._selected_entity_designator = selected_entity_designator

    def execute(self, userdata):

        id_str = self._selected_entity_designator.resolve().id[0:4]

        self._robot.speech.speak("Hi operator, please clean the %s object" % id_str, block=True)

        return "done"


class OperatorCleanup(smach.StateMachine):
    def __init__(self, robot, selected_entity_designator):

        smach.StateMachine.__init__(self, outcomes=['done'])

        with self:

            smach.StateMachine.add("TEST", Test(robot, selected_entity_designator),
                                   transitions={"done": "done"})