import base64
import datetime
import pathlib
import time

import numpy as np

import cv2
import yaml
from detectron2.config import get_cfg
from detectron2.data import MetadataCatalog
from detectron2.structures.boxes import Boxes
from project.d2predictor import VisualizationDemo

from project.file_utils import download_file


# MODEL_DOWNLOAD_URL = "https://www.dropbox.com/sh/wgt9skz67usliei/AABPmqM77ERycAd87vubWc4Ua/model_final_trimmed.pth?dl=1"
# MODEL_DOWNLOAD_URL = "https://www.dropbox.com/sh/1098ym6vhad4zi6/AAD8Y-SVN6EbfAWEDYuZHG8xa/model_final_trimmed.pth?dl=1"
MODEL_DOWNLOAD_URL = "https://yangkaichun.s3-ap-northeast-1.amazonaws.com/instances_predictions.pth"
with open(pathlib.Path().parent / "model_config.yaml") as f:
    model_config = yaml.full_load(f)


classes = model_config["categories"]
cfg_file = model_config["cfg_file"]
model_weights = model_config["model_file"]

print(f"Loaded config: {cfg_file}")
print(f"Loaded model: {model_weights}")


def prepare_predictor():
    # create config
    cfg = get_cfg()

    cfg.merge_from_file(cfg_file)
    cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = 0.5
    cfg.MODEL.WEIGHTS = model_weights
    cfg.MODEL.DEVICE = "cpu"

    MetadataCatalog.get("dla_val").thing_classes = classes

    if not pathlib.Path(model_weights).exists():
        print(f"Downloading {model_weights}...")
        download_file(MODEL_DOWNLOAD_URL, model_weights)
        print("Download complete!")
    
    predictor = VisualizationDemo(cfg)
    print("Predictor has been initialized.")

    return predictor


def extract_instances(instances):
    boxes = instances.pred_boxes
    print(f"instances: {len(boxes)}")
    if isinstance(boxes, Boxes):
        boxes = boxes.tensor.numpy()
    else:
        boxes = np.asarray(boxes)

    scores = instances.scores
    pred_classes = instances.pred_classes

    labels = [classes[i] for i in pred_classes]
    labels = ["{} {:.0f}%".format(l, s * 100) for l, s in zip(labels, scores)]
    return boxes, pred_classes, scores, labels


def make_predictions(image, return_json):
    start_time = time.time()

    # image = image[:, :, ::-1]
    predictions, vis_output = predictor.run_on_image(image)

    inference_time = int(time.time() - start_time)
    print(f"inference time: {datetime.timedelta(seconds=inference_time)}")

    boxes, pred_classes, scores, labels = extract_instances(predictions["instances"])

    img = vis_output.get_image()

    if return_json:
        retval, buffer = cv2.imencode(".jpg", img)
        jpg_as_text = base64.b64encode(buffer).decode("utf-8")

        total_time = int(time.time() - start_time)

        json_data = {
            "predictions": {
                "scores": scores.tolist(),
                "pred_classes": pred_classes.tolist(),
                "pred_boxes": boxes.tolist(),
                "classes": classes,
            },
            "instances": len(boxes),
            "img": jpg_as_text,
            "inference_time": f"{inference_time}s",
        }
        return json_data
    else:
        return img


predictor = prepare_predictor()
