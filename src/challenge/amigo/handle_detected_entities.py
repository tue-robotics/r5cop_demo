import smach, rospy
from robot_smach_states.util.designators import EdEntityDesignator, VariableDesignator, EntityByIdDesignator

from operator_cleanup import OperatorCleanup
from self_cleanup import SelfCleanup
from other_robot_cleanup import OtherRobotCleanup


class SelectEntityAndDetermineAction(smach.State):
    def __init__(self, robot, entitity_classifications_designator, known_types, selected_entity_designator):
        smach.State.__init__(self, outcomes=["self", "operator", "other_robot", "no_entities_left"])
        self._robot = robot
        self._entity_classifications_designator = entitity_classifications_designator
        self._known_types = known_types
        self._selected_entity_designator = selected_entity_designator

    def execute(self, userdata):

        # Try to pop item from entities_ids_designator
        try:
            entity_classification = self._entity_classifications_designator.resolve().pop()
        except:
            return "no_entities_left"

        rospy.loginfo("We have selected the entity with id %s" % entity_classification.id)
        self._selected_entity_designator.id_ = entity_classification.id

        if entity_classification.type not in self._known_types:
            return "operator"

        # Resolve the entity and determine the action based on the height
        e_resolved = self._selected_entity_designator.resolve()

        # Ground
        if e_resolved.pose.position.z < 0.4:
            return "other_robot"

        return "self"


class HandleDetectedEntities(smach.StateMachine):
    def __init__(self, robot, found_entity_classifications_designator, known_types):

        smach.StateMachine.__init__(self, outcomes=['done'])

        selected_entity_designator = EntityByIdDesignator(robot, "TBD")

        with self:

            smach.StateMachine.add("SELECT_ENTITY_AND_DETERMINE_ACTION",
                                   SelectEntityAndDetermineAction(robot, found_entity_classifications_designator,
                                                                  known_types, selected_entity_designator),
                                   transitions={"self": "SELF_CLEANUP",
                                                "operator": "OPERATOR_CLEANUP",
                                                "other_robot": "OTHER_ROBOT_CLEANUP",
                                                "no_entities_left": "done"})

            smach.StateMachine.add("SELF_CLEANUP", SelfCleanup(robot, selected_entity_designator),
                                   transitions={"done": "SELECT_ENTITY_AND_DETERMINE_ACTION"})

            smach.StateMachine.add("OPERATOR_CLEANUP", OperatorCleanup(robot, selected_entity_designator),
                                   transitions={"done": "SELECT_ENTITY_AND_DETERMINE_ACTION"})

            smach.StateMachine.add("OTHER_ROBOT_CLEANUP", OtherRobotCleanup(robot, selected_entity_designator),
                                   transitions={"done": "SELECT_ENTITY_AND_DETERMINE_ACTION"})
