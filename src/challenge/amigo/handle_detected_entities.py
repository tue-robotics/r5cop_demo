import smach
import rospy
import robot_smach_states
from robot_smach_states.util.designators import EdEntityDesignator, VariableDesignator, EntityByIdDesignator
import robot_skills.util.msg_constructors as msgs

from operator_cleanup import OperatorCleanup
from self_cleanup import SelfCleanup
from other_robot_cleanup import OtherRobotCleanup


class SelectEntity(smach.State):
    def __init__(self, robot, entitity_classifications_designator, selected_entity_designator):
        smach.State.__init__(self, outcomes=["entity_selected", "no_entities_left"])
        self._robot = robot
        self._entity_classifications_designator = entitity_classifications_designator
        self._selected_entity_designator = selected_entity_designator

    def execute(self, userdata):

        # Try to pop item from entities_ids_designator
        try:
            entity_classification = self._entity_classifications_designator.resolve().pop()
        except:
            return "no_entities_left"

        rospy.loginfo("We have selected the entity with id %s" % entity_classification.id)
        self._selected_entity_designator.id_ = entity_classification.id

        print self._selected_entity_designator.resolve()

        return "entity_selected"


class DetermineAction(smach.State):
    def __init__(self, robot, selected_entity_designator, known_types):
        smach.State.__init__(self, outcomes=["self", "operator", "other_robot"])
        self._robot = robot
        self._known_types = known_types
        self._selected_entity_designator = selected_entity_designator

    def execute(self, userdata):

        selected_entity = self._selected_entity_designator.resolve()

        rospy.loginfo("The type of the entity is '%s'" % selected_entity.type)

        # If we don't know the entity type, try to classify again
        if selected_entity.type == "" or selected_entity.type == "unknown":
            # Make sure the head looks at the entity
            pos = selected_entity.pose.position
            self._robot.head.look_at_point(msgs.PointStamped(pos.x, pos.y, 0.8, "/map"), timeout=10)

            # This is needed because the head is not entirely still when the look_at_point function finishes
            rospy.sleep(1)

            # Inspect the entity again
            self._robot.ed.update_kinect(selected_entity.id)

            # Classify the entity again
            try:
                selected_entity.type = self._robot.ed.classify(ids=[selected_entity.id])[0].type
                rospy.loginfo("We classified the entity again; type = %s" % selected_entity.type)
            except Exception as e:
                rospy.logerr(e)

        if selected_entity.type not in self._known_types:
            return "operator"

        # Ground
        if selected_entity.pose.position.z < 0.4:
            return "other_robot"

        return "self"


class HandleDetectedEntities(smach.StateMachine):
    def __init__(self, robot, found_entity_classifications_designator, known_types, location_id, segment_area):

        smach.StateMachine.__init__(self, outcomes=['done'])

        selected_entity_designator = EntityByIdDesignator(robot, "TBD")

        with self:

            smach.StateMachine.add("SELECT_ENTITY",
                                   SelectEntity(robot, found_entity_classifications_designator,
                                                selected_entity_designator),
                                   transitions={"entity_selected": "NAVIGATE_TO_ENTITY",
                                                "no_entities_left": "done"})

            smach.StateMachine.add("NAVIGATE_TO_ENTITY",
                                   robot_smach_states.NavigateToSymbolic(robot, {selected_entity_designator: "near"},
                                                                         selected_entity_designator),
                                   transitions={'arrived': 'DETERMINE_ACTION',
                                                'unreachable': 'DETERMINE_ACTION',
                                                'goal_not_defined': 'DETERMINE_ACTION'})

            smach.StateMachine.add("DETERMINE_ACTION",
                                   DetermineAction(robot, selected_entity_designator, known_types),
                                   transitions={"self": "SELF_CLEANUP",
                                                "operator": "OPERATOR_CLEANUP",
                                                "other_robot": "OTHER_ROBOT_CLEANUP"})

            smach.StateMachine.add("SELF_CLEANUP", SelfCleanup(robot, selected_entity_designator, location_id, segment_area),
                                   transitions={"done": "SELECT_ENTITY"})

            smach.StateMachine.add("OPERATOR_CLEANUP", OperatorCleanup(robot, selected_entity_designator, location_id, segment_area),
                                   transitions={"done": "SELECT_ENTITY"})

            smach.StateMachine.add("OTHER_ROBOT_CLEANUP", OtherRobotCleanup(robot, selected_entity_designator, location_id, segment_area),
                                   transitions={"done": "SELECT_ENTITY"})
