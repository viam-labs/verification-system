# `verification-system` modular resource

This module implements the `rdk:vision` API in the  `verification-system` model.

Machines configured with this module can enter an alarm state for unapproved individuals and disarm for approved visitors. You can enhance recognition capabilities by training an ML classification model using images of labeled visitors. 

This module has the following 5 states available:

| State | Description | Trigger Conditions | Next State  |
| ------------- | ------------- | ------------- | ------------- |
| `TRIGGER_1` | The initial state. A coarse, fast detector, similar to a simple motion detector. | Detector:<br/> `trigger_1_detector`<br/><br/> Labels:<br/> `trigger_1_labels`<br/><br/> Confidence:<br/> `trigger_1_confidence` | `TRIGGER_2` |
| `TRIGGER_2` | The secondary detection state.| Detector:<br/> `trigger_2_detector`<br/><br/> Labels:<br/> `trigger_2_labels`<br/><br/> Confidence:<br/> `trigger_2_confidence` | `TRIGGER_1` or `COUNTDOWN`|
| `COUNTDOWN` | The verification state before triggering the alarm. Enters `DISARMED` state if verification is successful, otherwise, transitions to `ALARM` after the duration set in `countdown_time_s`.| Detector:<br/> `verification_detector`<br/><br/> Labels:<br/> `verification_labels`<br/><br/> Confidence:<br/> `verification_confidence` | `DISARMED` or `ARMED`   |
| `ALARM` | The alarm state. Signals the `ALARM` classification which lasts for specified duration before returning to `TRIGGER_1`.| Timeout:<br/> `alarm_time_s`| `TRIGGER_1`|
| `DISARMED` | The disarmed state. Signals the `DISARMED` classification for the specified duration before returning to `TRIGGER_1`| Timeout:<br/> `disarmed_time_s`| `TRIGGER_1`|

## Requirements

- [camera](https://docs.viam.com/components/camera/) (such as a [webcam](https://docs.viam.com/components/camera/webcam/))
- 2-3 [detectors](https://docs.viam.com/ml/vision/mlmodel/)
- [transform camera](https://docs.viam.com/components/camera/transform/) (to see detections)

## Build and run

To use this module, follow the instructions to [add a module from the Viam Registry](https://docs.viam.com/registry/configure/#add-a-modular-resource-from-the-viam-registry) and select the `classifier:verification-system` model from the [`verification-system` module](https://app.viam.com/module/viam-labs/verification-system).

## Configure your verification system

> [!NOTE]
> Before configuring your verification system, you must [create a machine](https://docs.viam.com/fleet/machines/#add-a-new-machine).

Navigate to the **Config** tab of your machine's page in [the Viam app](https://app.viam.com).
Click on the **Services** subtab and click **Create service**.
Select the `vision` type, then select the `classifier:verification-system` model.
Enter a name for your vision service and click **Create**.

On the new service panel, copy and paste the following attribute template into your vision service’s **Attributes** box. 

```json
{
  "trigger_1_confidence": 0.35,
  "verification_detector": <your-verification-detector>,
  "camera_name": <your-camera-name>,
  "trigger_2_confidence": 0.5,
  "trigger_1_labels": ["Person"],
  "trigger_2_labels": ["Person"],
  "disable_alarm": false,
  "trigger_2_detector": <detector-name>,
  "verification_labels": ["my_name"],
  "trigger_1_detector":  <detector-name>,
  "disarmed_time_s": 10,
  "countdown_time_s": 10
}
```

> [!NOTE]
> For more information, see [Configure a Robot](https://docs.viam.com/manage/configuration/).

#### Attributes

The following attributes are available for `classifier:verification-system`:

| Name  | Type | Inclusion | Description |
| ------------- | ------------- | ------------- | ------------- |
| `verification_detector` | string | **Required** | The name of the vision service detector that will be used to verify the object.|
| `camera_name` | string | **Required** | The name of the camera component to use for source images.  |
| `trigger_1_confidence` | float | Optional | The detection confidence required to trigger the `TRIGGER_2` state.<br/> Default: `0.2`|
| `trigger_1_labels` | array | Optional| The valid labels from `trigger_1_detector` for the 1st trigger.<br/> Required if `trigger_1_detector` is specified.  |
| `verification_labels` | array | **Required** | The labels from `verification_detector` that count as valid. |
| `trigger_1_detector` | string | Optional | The name of the vision service detector used to trigger the system to enter to verification mode. |
| `countdown_time_s` | int | Optional | The time in seconds the system will remain in the `COUNTDOWN` state before transitioning to the `ALARM`state.<br/> Default: `20` |

> [!NOTE]
> If you don’t want the `ALARM` capabilities, and would like to just use it as a notification system when a detector gets triggered, set `disable_alarm` to `"true"`, which prevents `TRIGGER_2` from entering into the `COUNTDOWN` state. 
> Then the system will only cycle between the `TRIGGER_1` and `TRIGGER_2` states.
> You can use the `TRIGGER_2` state as a way to send notifications.

#### Example configuration

```json
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
      "my_name"
    ],
    "verification_confidence": 0.5,
    "countdown_time_s": 30,
    "disarmed_time_s": 600,
    "alarm_time_s": 10,
    "disable_alarm": false
  }
}
```

## Next steps

- For a complete tutorial, see [Create a Facial Verification System](https://docs.viam.com/tutorials/projects/verification-system/#configure-a-verification-system).
- To save images to the Viam cloud when the system enters into different states, use the [filtered-camera module](https://app.viam.com/module/erh/filtered-camera) in tandem with this module.