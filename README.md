# Verification-System

![out](https://github.com/viam-labs/verification-system/assets/8298653/7af85327-8d6f-4691-ade8-bb8e651c57c8)


https://app.viam.com/module/viam-labs/verification-system

A vision service module that sets up a system to detect, verify, and alarm based on specified detections.

Configure this vision service as a [modular resource](https://docs.viam.com/modular-resources/) on your robot to access and perform inference.

## Introduction 

The module sets up a state machine with 5 states:
1. `TRIGGER_1`: The module begins in this state. It is meant to be a coarse, fast detector, like a simple motion detector. If the detector triggers, then the state moves to `TRIGGER_2`. If no `TRIGGER_1` detector was specified in the config, the module moves immediately to state `TRIGGER_2`.
2. `TRIGGER_2`: This state runs the `trigger_2_detector` on every frame, looking for detections with any label from `trigger_2_labels` with at least `trigger_2_confidence`. If the detector triggers, then the state moves to `COUNTDOWN`. If it doesn't trigger in 10 frames, it returns to state `TRIGGER_1`.
3. `COUNTDOWN`: This state runs the `verification_detector` on every frame, looking for detections with any label from `verification_labels` with at least `verification_confidence`. If the detector triggers, then the state moves to `DISARMED`. If it doesn't trigger in the time specified by `countdown_time_s`, it moves to state `ALARM`.
4. `ALARM`: The alarm state. The module will emit the `ALARM` classification for the amount of time specified in `alarm_time_s`. After that amount of time elapses, the module will return to state `TRIGGER_1`.
5. `DISARMED`: The disarmed state. The module will emit the `DISARMED` classification for the amount of time specified in `disarmed_time_s`. After that amount of time elapses, the module will return to state `TRIGGER_1`.

If you do not want the `ALARM` capabilities, and would like to just use it as a notification system when a detector gets triggered, you can set `disable_alarm: true` in the config, which will prevent `TRIGGER_2` from entering into the `COUNTDOWN` state, meaning the system will eventually return to `TRIGGER_1`.

If you want to save images to the Viam cloud when the system enters into specific states, you can use the [filtered-camera module](https://app.viam.com/module/erh/filtered-camera) in tandem with this module.

## Config

```
{
  "name": "security",
  "type": "vision",
  "namespace": "rdk",
  "model": "viam-labs:classifier:verification-system",
  "attributes": {
    "camera_name": "color-cam",
    "trigger_1_detector": "motion_detection",
    "trigger_1_labels": [
     "motion"
    ],
    "trigger_1_confidence": 0.2,
    "trigger_2_detector": "people",
    "trigger_2_labels": [
     "Person"
    ],
    "trigger_2_confidence": 0.5,
    "verification_detector": "face-verify",
    "verification_labels": [
      "myName"
    ],
    "verification_confidence": 0.5,
    "countdown_time_s": 30,
    "disarmed_time_s": 600,
    "alarm_time_s": 10,
    "disable_alarm": false
  }
}

```
### Attributes


| Name | Type | Inclusion | Description |
| ---- | ---- | --------- | ----------- |
| `camera_name` | string | **Required** | The name of the camera component to use for source images. |
| `trigger_1_detector` | string | Optional | The name of the vision service detector that will be used as the first stage to trigger the system to enter verification mode. If left blank, the system will immediately transition to state `TRIGGER_2`. |
| `trigger_1_labels` | array | Optional | The class names from `trigger_1_detector` that count as valid. Required if `trigger_1_detector` is specified. |
| `trigger_1_confidence` | float | Optional | The detection confidence needed in order to move into the `TRIGGER_2` state. Default value is 0.2. |
| `trigger_2_detector` | string | **Required** | The name of the vision service detector that will detect the thing that needs to be verified. |
| `trigger_2_labels` | array | **Required** | The class names from `trigger_2_detector` that count as valid. |
| `trigger_2_confidence` | float | Optional | The detection confidence needed in order to move into the `COUNTDOWN` state. Default value is 0.5. |
| `verification_detector` | string | **Required** | The name of the vision service detector that will be used to verify the object. |
| `verification_labels` | array | **Required** | The class names from `verification_detector` that count as valid. |
| `verification_confidence` | float | Optional | The detection confidence needed in order to move into the `DISARMED` state. Default value is 0.8 |
| `countdown_time_s` | int | Optional | The time in seconds the system will remain in state `COUNTDOWN` before transitioning to state `ALARM`. Default value is 20. |
| `alarm_time_s` | int | Optional | The time in seconds the system will remain in  state `ALARM` before transitioning to state `TRIGGER_1`. Default value is 10. |
| `disarmed_time_s` | int | Optional | The time in seconds the system will remain in  state `DISARMED` before transitioning to state `TRIGGER_1`. Default value is 10. |
| `disable_alarm` | bool | Optional | Disables the `COUNTDOWN` and `ALARM` states. The system will always remain the `TRIGGER_1` and `TRIGGER_2` states. Default value is False. |

