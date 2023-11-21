from typing import Union, ClassVar, Mapping, Any, Dict, Optional, List
from typing_extensions import Self

from enum import Enum

from PIL import Image

from viam.media.video import RawImage

from viam.module.types import Reconfigurable
from viam.proto.app.robot import ComponentConfig
from viam.proto.service.vision import Classification
from viam.proto.common import ResourceName
from viam.resource.base import ResourceBase
from viam.resource.types import Model, ModelFamily

from viam.services.vision import Vision

from viam.components.camera import Camera

from viam.logging import getLogger

import time

LOGGER = getLogger(__name__)


class AlarmState(Enum):
    TRIGGER_1 = 1
    TRIGGER_2 = 2
    DISARMED = 3
    ALARM = 4
    COUNTDOWN = 5


class VerificationSystem(Vision, Reconfigurable):

    MODEL: ClassVar[Model] = Model(ModelFamily(
        "viam-labs", "classifier"), "verification-system")
    camera_name: str
    camera: Camera
    trigger_1_detector: str  #
    trigger_1_labels: List[str]
    trigger_1_confidence: float
    trigger_2_detector: str
    trigger_2_labels: List[str]
    trigger_2_confidence: float
    verification_detector: str
    verification_labels: List[str]
    verification_confidence: float
    countdown_time_s: int
    disarmed_time_s: int
    alarm_time_s: int
    last_disarmed_by: str
    detect_count: int
    detect_limit: int
    disable_alarm: bool

    # Constructor
    @classmethod
    def new(cls, config: ComponentConfig, dependencies: Mapping[ResourceName, ResourceBase]) -> Self:
        my_class = cls(config.name)
        my_class.reconfigure(config, dependencies)
        return my_class

    # Validates JSON Configuration
    @classmethod
    def validate(cls, config: ComponentConfig):
        # verify camera
        camera_name = config.attributes.fields["camera_name"].string_value.strip(
        )
        if camera_name == "":
            raise Exception(
                "attribute 'camera_name' is required and cannot be blank")
        # verify trigger 1 detector
        if config.attributes.fields["trigger_1_confidence"].number_value > 1.0:
            raise Exception(
                "attribute 'trigger_1_confidence' must be between 0.0 and 1.0")
        # verify trigger 2 detector
        if config.attributes.fields["trigger_2_confidence"].number_value > 1.0:
            raise Exception(
                "attribute 'trigger_2_confidence' must be between 0.0 and 1.0")
        if len(config.attributes.fields["trigger_2_labels"].list_value) == 0:
            raise Exception("attribute 'trigger_2_labels' cannot be empty")
        trigger_2_name = config.attributes.fields["trigger_2_detector"].string_value.strip(
        )
        if trigger_2_name == "":
            raise Exception(
                "attribute 'trigger_2_detector' is required and cannot be blank")
        # verify verification module
        if config.attributes.fields["verification_confidence"].number_value > 1.0:
            raise Exception(
                "attribute 'verification_confidence' must be between 0.0 and 1.0")
        if len(config.attributes.fields["verification_labels"].list_value) == 0:
            raise Exception("attribute 'verification_labels' cannot be empty")
        verification_name = config.attributes.fields["verification_detector"].string_value.strip(
        )
        if verification_name == "":
            raise Exception(
                "attribute 'verification_detector' is required and cannot be blank")
        # return dependencies
        trigger_1_name = config.attributes.fields["trigger_1_detector"].string_value.strip(
        )
        if trigger_1_name == "":
            return [trigger_2_name, camera_name, verification_name]
        else:
            if len(config.attributes.fields["trigger_1_labels"].list_value) == 0:
                raise Exception("attribute 'trigger_1_labels' cannot be empty")
            return [trigger_1_name, trigger_2_name, camera_name, verification_name]

    # Handles attribute reconfiguration
    def reconfigure(self, config: ComponentConfig, dependencies: Mapping[ResourceName, ResourceBase]):
        self.alarm_state = AlarmState.TRIGGER_1
        self.camera_name = config.attributes.fields["camera_name"].string_value.strip(
        )
        self.camera = dependencies[Camera.get_resource_name(self.camera_name)]
        # the 1st trigger
        self.trigger_1_detector = None
        trigger_1_name = config.attributes.fields["trigger_1_detector"].string_value.strip(
        )
        if trigger_1_name != "":
            self.trigger_1_detector = dependencies[Vision.get_resource_name(
                trigger_1_name)]
        self.trigger_1_labels = config.attributes.fields["trigger_1_labels"].list_value
        self.trigger_1_confidence = config.attributes.fields["trigger_1_confidence"].number_value or 0.2
        # the 2nd trigger
        trigger_2_name = config.attributes.fields["trigger_2_detector"].string_value.strip(
        )
        self.trigger_2_detector = dependencies[Vision.get_resource_name(trigger_2_name)]
        self.trigger_2_labels = config.attributes.fields["trigger_2_labels"].list_value
        self.trigger_2_confidence = config.attributes.fields[
            "trigger_2_confidence"].number_value or 0.5
        # the verification module
        verification_name = config.attributes.fields["verification_detector"].string_value.strip(
        )
        self.verification_detector = dependencies[Vision.get_resource_name(
            verification_name)]
        self.verification_labels = config.attributes.fields["verification_labels"].list_value
        self.verification_confidence = config.attributes.fields[
            "verification_confidence"].number_value or 0.8
        # the timing
        self.countdown_time_s = config.attributes.fields["countdown_time_s"].number_value or 20
        self.disarmed_time_s = config.attributes.fields["disarmed_time_s"].number_value or 10
        self.alarm_time_s = config.attributes.fields["alarm_time_s"].number_value or 10
        self.disable_alarm = config.attributes.fields["disable_alarm"].bool_value or False
        self.start_time = time.time()
        self.last_disarmed_by = ""
        self.detect_count = 0
        self.detect_limit = 10

        return

    async def get_detections_from_camera(self):
        return

    async def get_detections(self):
        return

    async def do_command(self):
        return

    async def get_object_point_clouds(self):
        return

    async def get_classifications_from_camera(self,
                                              camera_name: str,
                                              count: int,
                                              *,
                                              extra: Optional[Dict[str,
                                                                   Any]] = None,
                                              timeout: Optional[float] = None,
                                              **kwargs) -> List[Classification]:
        if camera_name != self.camera_name:
            raise Exception(
                f"camera {camera_name} was not declared in the camera_name dependency")
        cam_image = await self.camera.get_image(mime_type="image/jpeg")
        return await self.get_classifications(cam_image, 1)

    async def get_classifications(self,
                                  image: Union[Image.Image, RawImage],
                                  count: int,
                                  *,
                                  extra: Optional[Dict[str, Any]] = None,
                                  timeout: Optional[float] = None,
                                  **kwargs) -> List[Classification]:
        last_disarmed_by = await self.process_image(image)
        if last_disarmed_by != "":
            self.last_disarmed_by = last_disarmed_by
        class_name = self.alarm_state.name
        if self.alarm_state is AlarmState.COUNTDOWN:
            elapsed_time = time.time() - self.start_time
            time_remaining = self.countdown_time_s - elapsed_time
            class_name = class_name + \
                f": {time_remaining:.0f} s remain, Look at the camera!"
        if self.alarm_state is AlarmState.DISARMED:
            elapsed_time = time.time() - self.start_time
            time_remaining = self.disarmed_time_s - elapsed_time
            class_name = class_name + f" by {self.last_disarmed_by}: {time_remaining:.0f} s remain"
        classifications = [{"class_name": class_name, "confidence": 1.0}]
        return classifications

    async def process_image(self, image: Union[Image.Image, RawImage]):
        if self.alarm_state is AlarmState.TRIGGER_1:
            if self.trigger_1_detector is None:
                self.alarm_state = AlarmState.TRIGGER_2  # go straight to trigger 2
            else:
                detections = await self.trigger_1_detector.get_detections(
                    image)
                for detection in detections:
                    if detection.class_name in self.trigger_1_labels and detection.confidence > self.trigger_1_confidence:
                        self.alarm_state = AlarmState.TRIGGER_2
        if self.alarm_state is AlarmState.TRIGGER_2:
            detections = await self.trigger_2_detector.get_detections(image)
            for detection in detections:
                if detection.class_name in self.trigger_2_labels and detection.confidence > self.trigger_2_confidence and not self.disable_alarm:
                    self.start_time = time.time()
                    self.alarm_state = AlarmState.COUNTDOWN
                    self.detect_count = 0
                    return ""
            self.detect_count += 1
            if self.detect_count > self.detect_limit:
                self.detect_count = 0
                self.alarm_state = AlarmState.TRIGGER_1  # go back to trigger 1
        if self.alarm_state is AlarmState.COUNTDOWN:
            elapsed_time = time.time() - self.start_time
            if elapsed_time > self.countdown_time_s:
                self.start_time = time.time()
                self.alarm_state = AlarmState.ALARM
                return ""
            detections = await self.verification_detector.get_detections(image)
            for detection in detections:
                if detection.class_name in self.verification_labels and detection.confidence > self.verification_confidence:
                    self.start_time = time.time()
                    self.alarm_state = AlarmState.DISARMED
                    return detection.class_name
        if self.alarm_state is AlarmState.ALARM:
            elapsed_time = time.time() - self.start_time
            if elapsed_time > self.alarm_time_s:
                self.alarm_state = AlarmState.TRIGGER_1
        if self.alarm_state is AlarmState.DISARMED:
            elapsed_time = time.time() - self.start_time
            if elapsed_time > self.disarmed_time_s:
                self.alarm_state = AlarmState.TRIGGER_1
        return ""
