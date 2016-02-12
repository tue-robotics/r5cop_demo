import smach

import robot_smach_states
from robot_smach_states.util.designators import EdEntityDesignator, VariableDesignator

from handle_detected_entities import HandleDetectedEntities
from robot_skills.classification_result import ClassificationResult

class CleanInspect(smach.StateMachine):
    def __init__(self, robot, entity_id, known_types):

        smach.StateMachine.__init__(self, outcomes=['done'])

        found_entity_classifications_designator = VariableDesignator([], resolve_type=[ClassificationResult])

        with self:
            smach.StateMachine.add("SAY_GOING_TO_INSPECT",
                                   robot_smach_states.Say(robot, ["I'm going to inspect the %s" % entity_id], block=False),
                                   transitions={"spoken": "INSPECT"})

            smach.StateMachine.add("INSPECT",
                                   robot_smach_states.world_model.Inspect(robot, EdEntityDesignator(robot, id=entity_id),
                                                                          objectIDsDes=found_entity_classifications_designator),
                                   transitions={"done": "SAY_INSPECT_DONE",
                                                "failed": "SAY_INSPECT_FAILED"})

            smach.StateMachine.add("SAY_INSPECT_DONE",
                                   robot_smach_states.Say(robot, ["I have inspected the %s" % entity_id], block=False),
                                   transitions={"spoken": "HANDLE_DETECTED_ENTITIES"})

            smach.StateMachine.add("SAY_INSPECT_FAILED",
                                   robot_smach_states.Say(robot, ["I failed to inspect the %s" % entity_id], block=False),
                                   transitions={"spoken": "done"})

            smach.StateMachine.add("HANDLE_DETECTED_ENTITIES",
                                   HandleDetectedEntities(robot, found_entity_classifications_designator, known_types),
                                   transitions={"done":"done"})
