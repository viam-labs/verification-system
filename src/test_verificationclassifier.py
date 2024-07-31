import time
import pytest
from google.protobuf.struct_pb2 import Struct
from unittest.mock import AsyncMock, MagicMock
from viam.proto.app.robot import ComponentConfig
from viam.services.vision import Vision
from viam.components.camera import Camera
from src.verificationclassifier import VerificationSystem, AlarmState


def make_component_config(dictionary):
    struct = Struct()
    struct.update(dictionary)
    return ComponentConfig(attributes=struct)


class TestVerificationSystem:
    @pytest.fixture
    def mock_dependencies(self):
        mock_camera = MagicMock(spec=Camera)
        mock_vision = MagicMock(spec=Vision)

        mock_config = MagicMock(spec=ComponentConfig)

        mock_attributes = MagicMock()
        mock_attributes.fields = {
            "camera_name": MagicMock(string_value="mock_camera"),
            "trigger_1_detector": MagicMock(string_value="mock_trigger1"),
            "trigger_1_labels": MagicMock(list_value=["label1"]),
            "trigger_1_confidence": MagicMock(number_value=0.8),
            "trigger_2_detector": MagicMock(string_value="mock_trigger2"),
            "trigger_2_labels": MagicMock(list_value=["label2"]),
            "trigger_2_confidence": MagicMock(number_value=0.6),
            "verification_detector": MagicMock(string_value="mock_verification"),
            "verification_labels": MagicMock(list_value=["verify_label"]),
            "verification_confidence": MagicMock(number_value=0.9),
            "countdown_time_s": MagicMock(number_value=15),
            "disarmed_time_s": MagicMock(number_value=20),
            "alarm_time_s": MagicMock(number_value=25),
            "disable_alarm": MagicMock(bool_value=True),
        }
        mock_config.attributes = mock_attributes

        mock_dependencies = {
            Camera.get_resource_name("mock_camera"): mock_camera,
            Vision.get_resource_name("mock_trigger1"): mock_vision,
            Vision.get_resource_name("mock_trigger2"): mock_vision,
            Vision.get_resource_name("mock_verification"): mock_vision,
        }
        return mock_config, mock_dependencies

    @pytest.fixture
    def model(self, mock_dependencies):
        mock_config, dependencies = mock_dependencies
        return VerificationSystem.new(mock_config, dependencies)

    @pytest.mark.asyncio
    async def test_validate_empty_config(self):
        empty_config = make_component_config({})
        with pytest.raises(Exception) as excinfo:
            VerificationSystem.validate(config=empty_config)

        assert str(excinfo.value) in [
            "attribute 'camera_name' is required and cannot be blank",
            "attribute 'trigger_1_confidence' must be between 0.0 and 1.0",
            "attribute 'trigger_2_confidence' must be between 0.0 and 1.0",
            "attribute 'trigger_2_labels' cannot be empty",
            "attribute 'trigger_2_detector' is required and cannot be blank",
            "attribute 'verification_confidence' must be between 0.0 and 1.0",
            "attribute 'verification_labels' cannot be empty",
            "attribute 'verification_detector' is required and cannot be blank",
        ]

    @pytest.mark.asyncio
    async def test_validate(self, mock_dependencies):
        valid_config, _ = mock_dependencies
        response = VerificationSystem.validate(config=valid_config)
        assert response == [
            "mock_trigger1",
            "mock_trigger2",
            "mock_camera",
            "mock_verification",
        ]

    @pytest.mark.asyncio
    async def test_validation_with_invalid_camera_name(self, mock_dependencies):
        invalid_config, _ = mock_dependencies
        invalid_config.attributes.fields["camera_name"].string_value = ""
        with pytest.raises(Exception) as excinfo:
            VerificationSystem.validate(config=invalid_config)
        assert (
            str(excinfo.value)
            == "attribute 'camera_name' is required and cannot be blank"
        )

    @pytest.mark.asyncio
    async def test_validation_with_invalid_confidence(self, mock_dependencies):
        invalid_config, _ = mock_dependencies
        invalid_config.attributes.fields["trigger_1_confidence"].number_value = 1.1
        with pytest.raises(Exception) as excinfo:
            VerificationSystem.validate(config=invalid_config)
        assert (
            str(excinfo.value)
            == "attribute 'trigger_1_confidence' must be between 0.0 and 1.0"
        )

    def test_verification_system_initialization(self, model):
        system = model

        assert system.camera_name == "mock_camera"
        assert system.trigger_1_confidence == 0.8
        assert system.trigger_2_confidence == 0.6
        assert system.verification_confidence == 0.9
        assert system.countdown_time_s == 15
        assert system.disarmed_time_s == 20
        assert system.alarm_time_s == 25
        assert system.disable_alarm is True

    def test_reconfigure(self, model, mock_dependencies):
        system = model
        config, dependencies = mock_dependencies
        system.reconfigure(config, dependencies)

        assert system.alarm_state == AlarmState.TRIGGER_1
        assert system.camera_name == "mock_camera"
        assert system.camera == dependencies[Camera.get_resource_name("mock_camera")]
        assert (
            system.trigger_1_detector
            == dependencies[Vision.get_resource_name("mock_trigger1")]
        )
        assert system.trigger_1_labels == ["label1"]
        assert system.trigger_1_confidence == 0.8
        assert (
            system.trigger_2_detector
            == dependencies[Vision.get_resource_name("mock_trigger2")]
        )
        assert system.trigger_2_labels == ["label2"]
        assert system.trigger_2_confidence == 0.6
        assert (
            system.verification_detector
            == dependencies[Vision.get_resource_name("mock_verification")]
        )
        assert system.verification_labels == ["verify_label"]
        assert system.verification_confidence == 0.9
        assert system.countdown_time_s == 15
        assert system.disarmed_time_s == 20
        assert system.alarm_time_s == 25
        assert system.disable_alarm is True

        assert system.start_time is not None
        assert system.last_disarmed_by == ""
        assert system.detect_count == 0
        assert system.detect_limit == 10

    def test_reconfigure_with_empty(self, mock_dependencies):
        config, dependencies = mock_dependencies

        # make them empty
        config.attributes.fields["trigger_1_confidence"].number_value = None
        config.attributes.fields["trigger_2_confidence"].number_value = None
        config.attributes.fields["verification_confidence"].number_value = None
        config.attributes.fields["countdown_time_s"].number_value = None
        config.attributes.fields["disarmed_time_s"].number_value = None
        config.attributes.fields["alarm_time_s"].number_value = None
        config.attributes.fields["disable_alarm"].bool_value = None
        config.attributes.fields["trigger_1_detector"].string_value = ""
        config.attributes.fields["trigger_1_labels"].list_value = []
        config.attributes.fields["trigger_2_detector"].string_value = ""
        config.attributes.fields["trigger_2_labels"].list_value = []
        config.attributes.fields["verification_detector"].string_value = ""
        config.attributes.fields["verification_labels"].list_value = []

        dependencies[Vision.get_resource_name("")] = None

        system = VerificationSystem.new(config, dependencies)
        system.reconfigure(config, dependencies)

        # check if defaults are set correctly
        assert system.alarm_state == AlarmState.TRIGGER_1
        assert system.camera_name == "mock_camera"
        assert system.camera == dependencies[Camera.get_resource_name("mock_camera")]
        assert system.trigger_1_detector is None
        assert system.trigger_1_labels == []
        assert system.trigger_1_confidence == 0.2
        assert system.trigger_2_detector is None
        assert system.trigger_2_labels == []
        assert system.trigger_2_confidence == 0.5
        assert system.verification_detector is None
        assert system.verification_labels == []
        assert system.verification_confidence == 0.8
        assert system.countdown_time_s == 20
        assert system.disarmed_time_s == 10
        assert system.alarm_time_s == 10
        assert system.disable_alarm is False

        assert system.start_time is not None
        assert system.last_disarmed_by == ""
        assert system.detect_count == 0
        assert system.detect_limit == 10

    @pytest.mark.asyncio
    async def test_get_properties(self, model):
        system = model

        properties = await system.get_properties()

        assert properties.classifications_supported is True
        assert properties.detections_supported is False
        assert properties.object_point_clouds_supported is False

    @pytest.mark.asyncio
    async def test_capture_all_from_camera(self, model):
        system = model

        mock_camera = system.camera
        mock_camera.get_image = AsyncMock(return_value=b"mock_image_data")
        system.get_classifications = AsyncMock(return_value=["class1", "class2"])

        result = await system.capture_all_from_camera(
            camera_name="mock_camera",
            return_image=True,
            return_classifications=True,
            return_detections=True,
            return_object_point_clouds=True,
        )

        assert result.image == b"mock_image_data" 
        assert result.classifications == ["class1", "class2"]
        assert result.detections == []
        assert result.objects == []

    @pytest.mark.asyncio
    async def test_get_classifications_countdown(self, model):
        system = model

        system.process_image = AsyncMock(return_value="")

        system.alarm_state = AlarmState.COUNTDOWN
        system.start_time = time.time() - 5
        system.countdown_time_s = 20

        result = await system.get_classifications(b"mock_image_data", 1)

        assert result == [{"class_name": "COUNTDOWN: 15 s remain", "confidence": 1.0}]

    @pytest.mark.asyncio
    async def test_get_classifications_disarmed(self, model):
        system = model

        system.process_image = AsyncMock(return_value="user1")

        system.alarm_state = AlarmState.DISARMED
        system.start_time = time.time() - 10
        system.disarmed_time_s = 20

        result = await system.get_classifications(b"mock_image_data", 1)

        assert result == [
            {"class_name": "DISARMED by user1: 10 s remain", "confidence": 1.0}
        ]

    @pytest.mark.asyncio
    async def test_get_classifications_no_last_disarmed_by(self, model):
        system = model

        system.process_image = AsyncMock(return_value="")

        system.alarm_state = AlarmState.TRIGGER_1

        result = await system.get_classifications(b"mock_image_data", 1)

        assert result == [{"class_name": "TRIGGER_1", "confidence": 1.0}]

    @pytest.mark.asyncio
    async def test_process_image_trigger_1_transitions(self, model):
        system = model

        # case 1: with detector
        mock_detector = system.trigger_1_detector
        mock_detector.get_detections = AsyncMock(
            return_value=[MagicMock(class_name="label1", confidence=0.9)]
        )

        system.alarm_state = AlarmState.TRIGGER_1
        system.trigger_1_labels = ["label1"]
        system.trigger_1_confidence = 0.8

        result = await system.process_image(b"mock_image_data")

        assert system.alarm_state == AlarmState.TRIGGER_2
        assert result == ""

        # case 2: without detector
        system.alarm_state = AlarmState.TRIGGER_1
        system.trigger_1_detector = None

        result = await system.process_image(b"mock_image_data")

        assert system.alarm_state == AlarmState.TRIGGER_2
        assert result == ""

    @pytest.mark.asyncio
    async def test_process_image_trigger_2_transitions(self, model):

        # case 1: TRIGGER_2 to COUNTDOWN
        system = model

        mock_detector = system.trigger_2_detector
        mock_detector.get_detections = AsyncMock(
            return_value=[MagicMock(class_name="label2", confidence=0.7)]
        )

        system.alarm_state = AlarmState.TRIGGER_2
        system.trigger_2_labels = ["label2"]
        system.trigger_2_confidence = 0.6
        system.disable_alarm = False

        result = await system.process_image(b"mock_image_data")

        assert system.alarm_state == AlarmState.COUNTDOWN
        assert system.detect_count == 0
        assert result == ""

        # case 2: TRIGGER_2 to TRIGGER_1
        system = model

        mock_detector.get_detections = AsyncMock(
            return_value=[MagicMock(class_name="other_label", confidence=0.7)]
        )

        system.alarm_state = AlarmState.TRIGGER_2
        system.trigger_2_labels = ["label2"]
        system.trigger_2_confidence = 0.6
        system.detect_count = 10
        system.detect_limit = 10
        system.disable_alarm = False

        result = await system.process_image(b"mock_image_data")

        assert system.alarm_state == AlarmState.TRIGGER_1
        assert system.detect_count == 0
        assert result == ""

    @pytest.mark.asyncio
    async def test_process_image_countdown_transitions(self, model):
        system = model

        # case 1: COUNTDOWN to ALARM
        system.alarm_state = AlarmState.COUNTDOWN
        system.start_time = time.time() - 16  # elapsed time
        system.countdown_time_s = 15

        result = await system.process_image(b"mock_image_data")

        assert system.alarm_state == AlarmState.ALARM
        assert result == ""

        # reset
        system.alarm_state = AlarmState.COUNTDOWN
        system.start_time = time.time() - 5  # elapsed time

        # Scenario 2: COUNTDOWN to DISARMED
        mock_verification_detector = system.verification_detector
        mock_verification_detector.get_detections = AsyncMock(
            return_value=[MagicMock(class_name="verify_label", confidence=1.0)]
        )

        system.verification_labels = ["verify_label"]
        system.verification_confidence = 0.9

        result = await system.process_image(b"mock_image_data")

        assert system.alarm_state == AlarmState.DISARMED
        assert result == "verify_label"

    @pytest.mark.asyncio
    async def test_process_image_alarm_to_trigger_1(self, model):
        system = model

        system.alarm_state = AlarmState.ALARM
        system.start_time = time.time() - 26  # elapsed time
        system.alarm_time_s = 25

        result = await system.process_image(b"mock_image_data")

        assert system.alarm_state == AlarmState.TRIGGER_1
        assert result == ""

    @pytest.mark.asyncio
    async def test_process_image_disarmed_to_trigger_1(self, model):
        system = model

        system.alarm_state = AlarmState.DISARMED
        system.start_time = time.time() - 21  # elapsed time
        system.disarmed_time_s = 20

        result = await system.process_image(b"mock_image_data")

        assert system.alarm_state == AlarmState.TRIGGER_1
        assert result == ""
