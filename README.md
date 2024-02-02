# Verification System

This module implements Viam's machine learning (ML) model service and vision service to provide a tool for facial verification and object detection.

Viam-powered machines configured with this module can enter an alarm state for unapproved individuals and disarm for approved visitors. You can enhance recognition capabilities by training the ML model by classifying images with labeled visitors. 

This module utilizes two ML model detectors: 

- [`people-detect`](#configure-an-mlmodel-person-detector) to identify the presence of visitors in the camera feed.
- [`face-detect`](#configure-a-facial-detector), which leverages the DeepFace library to recognize specific visitors.

This module has the following 5 states available:

| State | Description | Trigger Conditions | Next State  |
| ------------- | ------------- | ------------- | ------------- |
| `TRIGGER_1` | Coarse, fast detection state. | Detector: `trigger_1_detector`<br/>Labels: `trigger_1_labels`<br/>Confidence: `trigger_1_confidence` | `TRIGGER_2` |
| `TRIGGER_2` | The secondary detection state. | Detector: `trigger_2_detector`<br/>Labels: `trigger_2_labels`<br/>Confidence: `trigger_2_confidence` | `COUNTDOWN` (on trigger) / `TRIGGER_1`   |
| `COUNTDOWN` | The current state of verification. | Detector: `verification_detector`<br/>Labels: `verification_labels`<br/>Confidence: `verification_confidence` | `DISARMED` (on trigger) / `ALARM` (on timeout) |
| `ALARM`    | The alarm state. | - | TRIGGER_1 (after `alarm_time_s`) |
| `DISARMED` | The disarmed state.| - | TRIGGER_1 (after `disarmed_time_s`) |

## Build and Run

To use this module, configure your machine with the resources outlined in this readme.

Before configuring the resources for this module, [Create a new machine](https://docs.viam.com/fleet/machines/#add-a-new-machine) in the Viam app. Then [Install `viam-server`](https://docs.viam.com/get-started/installation/) on your new machine.

Configure the [camera](https://docs.viam.com/components/camera/) component, such as a [webcam](https://docs.viam.com/components/camera/webcam/), for your security system in the [**Config** tab](https://docs.viam.com/build/configure/#the-config-tab) on your machine's page in the Viam app.
Then, configure a [transform camera](https://docs.viam.com/components/camera/transform/) and enter the following configuration into the **Attributes** field:

```json
{
  "pipeline": [
    {
      "attributes": {
        "classifier_name": "security",
        "confidence_threshold": 0.5
      },
      "type": "classification"
    }
  ],
  "source": "my-webcam"
}
```

### Configure an `mlmodel` person detector

1. Follow instructions to [add the data management service to your machine and enable data capture](https://docs.viam.com/data/capture/#add-the-data-management-service) on your camera component.<br/>If you’re using a webcam, set the data capture method **Type** to **ReadImage** and set the **Frequency** to `0.333`.

For more information, see [Configure data capture for individual components](https://docs.viam.com/data/capture/#configure-data-capture-for-individual-components).

2. [Create a dataset and add the images you captured](https://docs.viam.com/data/dataset/#create-a-dataset-and-add-data).<br/>Provide at least 10 images that include people, taken from a variety of angles and under different lighting conditions.
> [!TIP]
> Your dataset should predominately contain labeled images, with unlabeled images making up no more than 20%.
> For example, if your dataset includes 25 images, at least 20 of them should be labeled.

3. [Add the label `"person"`](https://docs.viam.com/data/dataset/#label-data) to the images containing individuals by incorporating bounding boxes.
4. [Train a model on your dataset](https://docs.viam.com/ml/train-model/). Give it the name `"persondetect"`, and select **Object Detection** as the **Model Type**.
5. [Deploy the model](https://docs.viam.com/ml/deploy/) to your machine.
6. Follow the instructions to [configure an ML model detector](https://docs.viam.com/ml/vision/mlmodel/) and name your model `people-detect`.


Copy and paste the following configuration into the **Attributes** field:

```json
{
  "mlmodel_name": "persondetect"
}
```

### Configure a facial detector

After you copy clear pictures of the faces you want your detector to identify to your machine's file system, follow the instructions to [Add the `facial-detector` module to your machine](https://docs.viam.com/registry/configure/#add-a-modular-service-from-the-viam-registry).<br/>Search for `detector:facial-detector` and name the resulting modular vision service `"face-detect"`.

Copy and paste the following configuration into the **Attributes** field:

```json
{
  "face_labels": {
    "my_name": "/home/me/my-photo.jpg"
  },
  "recognition_model": "ArcFace",
  "detection_framework": "ssd"
}
```

#### Attributes

| Name  | Type | Inclusion | Description |
| ------------- | ------------- | ------------- | ------------- |
| `recognition_model` | string | **Required** | The model to use for facial recognition.<br/>`ArcFace` is set as the default. |
| `detection_framework`  | string | **Required** | The detection framework to use for facial detection.<br/>`ssd` is set as the default. |
| `face_labels` | dictionary[string,string] | Optional | The dictionary representing labels for photos of individuals faces paired with the image path on your machine running `viam-server`. |
| `verify_threshold` | float64 | Optional | The confidence threshold for face verification. <br/>Only applicable if `disable_verify` is `false` and `face_labels` are set. Faces below this threshold will be labeled as normal detected `"face"`. <br/>Defaults to `0.8`. |
| `disable_detect` | bool | Optional | If set to `true`, facial detection will be disabled.<br/>Only applicable if `disable_verify` is `false` and `face_labels` are set. Any faces detected without being verified as matching a label will be labeled as `"face"`.<br/>Defaults to `false`. |
| `disable_verify` | bool | Optional | If set to `true`, facial verification will be disabled. <br/>Defaults to `false`. <br/>Only applicable if `face_labels` are set. If you only want verified faces to be labeled and skip labeling unverified visitors as `"face"`, set this to `false` and `disable_detect` to `true`. |

> [!NOTE]
> For more information on the available attributes, see the [`facial-detector` module documentation](https://github.com/viam-labs/facial-detection).

### Configure the verification system

Add the alarm logic by following the instructions to [Add the `verification-system` module to your machine](https://docs.viam.com/registry/configure/#add-a-modular-service-from-the-viam-registry).<br/>Search for `classifier:verification-system` and name the resulting modular vision service `"security"`.

Copy and paste the following configuration into the **Attributes** field:

```json
{
  "trigger_1_confidence": 0.35,
  "verification_detector": "face-detect",
  "camera_name": "my-webcam",
  "trigger_2_confidence": 0.5,
  "trigger_1_labels": ["Person"],
  "trigger_2_labels": ["Person"],
  "disable_alarm": false,
  "trigger_2_detector": "people-detect",
  "verification_labels": ["my_name"],
  "trigger_1_detector": "people-detect",
  "disarmed_time_s": 10,
  "countdown_time_s": 10
}
```

#### Attributes

| Name  | Type | Inclusion | Description |
| ------------- | ------------- | ------------- | ------------- |
| `camera_name` | string | **Required** | The name of the camera component to use for source images.  |
| `trigger_1_detector` | string | Optional | The name of the vision service detector used to trigger the system to enter to verification mode. |
| `trigger_2_detector` | string | **Required** | The name of the vision service detector that will be used to detect the object. If left blank, the system will transition to `TRIGGER_2` state. |
| `trigger_1_labels` | array | Optional| The valid labels from `trigger_1_detector` for the 1st trigger.<br/> Required if `trigger_1_detector` is specified.  |
| `trigger_2_labels` | array | **Required** | The valid labels from `trigger_2_detector` for the 2nd trigger. |
| `trigger_1_confidence` | float | Optional | The detection confidence required to trigger the `TRIGGER_2` state.<br/>Default: `0.2`|
| `trigger_2_confidence` | float | **Required** | The detection confidence required to trigger the `TRIGGER_2` state.<br/>Default: `0.5`|
| `verification_detector` | string | **Required** | The name of the vision service detector that will be used to verify the object.|
| `verification_labels` | array | **Required** | The labels from `verification_detector` that count as valid. |
| `verification_confidence` | float | Optional | The detection confidence required to move into the `DISARMED` state.<br/>Default: `0.8`|
| `countdown_time_s` | int | Optional | The time in seconds the system will remain in the `COUNTDOWN` state before transitioning to the `ALARM`state.<br/>Default: `20` |
| `alarm_time_s` | int | Optional | The time in seconds the system will remain in the `ALARM` state before transitioning to the `TRIGGER_1` state.<br/>Default: `10` |
| `disarmed_time_s` | int | Optional | The time in seconds the system will remain in the `DISARMED` state before transitioning to the `TRIGGER_1` state.<br/>Default: `10` |
| `disable_alarm` | bool | Optional | Disables the `COUNTDOWN` and `ALARM` states. The system will always remain in the `TRIGGER_1` and `TRIGGER_2` states. Default value is False.|

## Next Steps

- See [Create a Facial Verification System](https://docs.viam.com/tutorials/projects/verification-system/#configure-a-verification-system) for a complete tutorial.
- Use the [filtered-camera module](https://app.viam.com/module/erh/filtered-camera) in tandem with this module if you want to save images to the Viam cloud when the system enters into specific states.
- If you don’t want the `ALARM` capabilities, and would like to just use it as a notification system when a detector gets triggered, set `disable_alarm` to `"true"`, which prevents `TRIGGER_2` from entering into the `COUNTDOWN` state and the system will only cycle between the `TRIGGER_1` and `TRIGGER_2` states.
- Use entering into the state `TRIGGER_2` as a way to send notifications.


