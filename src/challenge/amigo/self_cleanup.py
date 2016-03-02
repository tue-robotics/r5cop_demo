import smach
import robot_smach_states

from robot_smach_states.util.designators import UnoccupiedArmDesignator, OccupiedArmDesignator, Designator

from geometry_msgs.msg import PoseStamped


class dropPoseDesignator(Designator):
    def __init__(self, robot, drop_height, name):
        super(dropPoseDesignator, self).__init__(resolve_type=PoseStamped, name=name)

        self._robot = robot
        self._drop_height = drop_height

    def _resolve(self):
        ps = PoseStamped()

        # Query ed
        try:
            p = self._robot.ed.get_entity(id="trashbin").pose
        except:
            return None

        p.position.z = self._drop_height

        ps.header.frame_id = "/map"
        ps.pose = p

        return ps


class Speak(smach.State):
    def __init__(self, robot, selected_entity_designator):
        smach.State.__init__(self, outcomes=["done"])
        self._robot = robot
        self._selected_entity_designator = selected_entity_designator

    def execute(self, userdata):
        e = self._selected_entity_designator.resolve()

        self._robot.speech.speak("I will clean the %s object which is a %s" % (e.id[0:4], e.type), block=False)

        return "done"


class SelfCleanup(smach.StateMachine):
    def __init__(self, robot, selected_entity_designator, location_id, segment_area):

        smach.StateMachine.__init__(self, outcomes=['done'])

        place_pose = dropPoseDesignator(robot, 0.6, "drop_pose")

        with self:

            smach.StateMachine.add("SPEAK", Speak(robot, selected_entity_designator),
                                   transitions={"done": "GRAB"})

            smach.StateMachine.add("GRAB",
                                   robot_smach_states.Grab(robot, selected_entity_designator,
                                                           UnoccupiedArmDesignator(robot.arms,
                                                                                   robot.rightArm,
                                                                                   name="empty_arm_designator")),
                                   transitions={"done": "SAY_GRAB_SUCCESS", "failed": "SAY_GRAB_FAILED"})

            smach.StateMachine.add('SAY_GRAB_SUCCESS',
                                   robot_smach_states.Say(robot, ["Now I am going to toss the item in the trashbin",
                                                                  "Let's clean up this object",
                                                                  "Away with this garbage",
                                                                  "Everything will be cleaned"], block=False),
                                   transitions={"spoken": "PLACE"})

            smach.StateMachine.add('SAY_GRAB_FAILED',
                                   robot_smach_states.Say(robot, ["I could not grab the item.",
                                                                  "I failed to grasp the item",
                                                                  "I cannot reach the item",
                                                                  "Item grab failed"], block=False),
                                   transitions={"spoken": "done"})

            smach.StateMachine.add('PLACE',
                                   robot_smach_states.Place(robot, 
                                                            selected_entity_designator, 
                                                            place_pose, 
                                                            OccupiedArmDesignator(robot.arms,
                                                                                  robot.rightArm,
                                                                                  name="occupied_arm_designator")),
                                   transitions={"done": "SAY_PLACE_SUCCESS", "failed": "SAY_PLACE_FAILED"})

            smach.StateMachine.add('SAY_PLACE_SUCCESS',
                                   robot_smach_states.Say(robot, ["Bye bye!",
                                                                  "Yeah!",
                                                                  "Successfully disposed the item",
                                                                  "Another score for AMIGO"], block=False),
                                   transitions={"spoken": "done"})

            smach.StateMachine.add('SAY_PLACE_FAILED',
                                   robot_smach_states.Say(robot, ["I could not cleanup the item.",
                                                                  "I cannot put the item in the trashbin",
                                                                  "Item cleanup failed"], block=False),
                                   transitions={"spoken": "done"})
