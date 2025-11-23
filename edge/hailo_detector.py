#!/usr/bin/env python3
"""
Flying GEM Brain - Hailo AI Detector
YOLOv8n object detection on Hailo AI HAT+ (26 TOPS)
"""

import logging
from typing import List, Tuple, Optional
from dataclasses import dataclass

# Note: hailo-platform SDK required on actual hardware
# Install from: https://hailo.ai/developer-zone/
try:
    from hailo_platform import (
        HEF,
        ConfigureParams,
        InferVStreams,
        InputVStreamParams,
        OutputVStreamParams,
        FormatType
    )
    HAILO_AVAILABLE = True
except ImportError:
    HAILO_AVAILABLE = False
    print("Warning: Hailo SDK not installed. Running in simulation mode.")

import numpy as np
try:
    import cv2
except ImportError:
    print("Warning: OpenCV not installed. Install with: pip install opencv-python")
    cv2 = None


@dataclass
class Detection:
    """Object detection result"""
    class_name: str
    confidence: float
    bbox: Tuple[int, int, int, int]  # (x, y, width, height)


class HailoDetector:
    """
    YOLOv8n object detection using Hailo AI HAT+

    Hardware Specs:
    - Hailo-8L NPU: 26 TOPS
    - YOLOv8n: ~30 FPS at 640x640
    - Power: ~2.5W during inference
    """

    def __init__(
        self,
        model_path: str = "models/yolov8n.hef",
        confidence_threshold: float = 0.5,
        nms_threshold: float = 0.45,
        input_size: Tuple[int, int] = (640, 640)
    ):
        """
        Initialize Hailo detector

        Args:
            model_path: Path to compiled Hailo HEF file
            confidence_threshold: Minimum detection confidence
            nms_threshold: Non-max suppression threshold
            input_size: Model input resolution (width, height)
        """
        self.model_path = model_path
        self.confidence_threshold = confidence_threshold
        self.nms_threshold = nms_threshold
        self.input_size = input_size

        self.logger = logging.getLogger("HailoDetector")

        # COCO class names (YOLOv8n default)
        self.class_names = [
            "person", "bicycle", "car", "motorcycle", "airplane", "bus", "train",
            "truck", "boat", "traffic light", "fire hydrant", "stop sign",
            "parking meter", "bench", "bird", "cat", "dog", "horse", "sheep",
            "cow", "elephant", "bear", "zebra", "giraffe", "backpack", "umbrella",
            "handbag", "tie", "suitcase", "frisbee", "skis", "snowboard",
            "sports ball", "kite", "baseball bat", "baseball glove", "skateboard",
            "surfboard", "tennis racket", "bottle", "wine glass", "cup", "fork",
            "knife", "spoon", "bowl", "banana", "apple", "sandwich", "orange",
            "broccoli", "carrot", "hot dog", "pizza", "donut", "cake", "chair",
            "couch", "potted plant", "bed", "dining table", "toilet", "tv",
            "laptop", "mouse", "remote", "keyboard", "cell phone", "microwave",
            "oven", "toaster", "sink", "refrigerator", "book", "clock", "vase",
            "scissors", "teddy bear", "hair drier", "toothbrush"
        ]

        # Initialize Hailo device
        self.device = None
        self.network_group = None
        self.input_vstreams = None
        self.output_vstreams = None

        if HAILO_AVAILABLE:
            self._init_hailo()
        else:
            self.logger.warning("Hailo SDK not available - running in simulation mode")

    def _init_hailo(self):
        """Initialize Hailo AI HAT+ device"""
        try:
            # Load compiled model
            self.hef = HEF(self.model_path)

            # Configure device
            self.device = self.hef.create_configure_params()

            # Create network group
            network_group_params = self.hef.create_network_group()
            self.network_group = self.device.configure(network_group_params)[0]

            # Setup input/output streams
            input_vstream_params = InputVStreamParams.make_from_network_group(
                self.network_group,
                quantized=False,
                format_type=FormatType.FLOAT32
            )

            output_vstream_params = OutputVStreamParams.make_from_network_group(
                self.network_group,
                quantized=False,
                format_type=FormatType.FLOAT32
            )

            self.input_vstreams = InferVStreams(self.network_group, input_vstream_params)
            self.output_vstreams = InferVStreams(self.network_group, output_vstream_params)

            self.logger.info(f"Hailo device initialized with model: {self.model_path}")
            self.logger.info(f"Input size: {self.input_size}, Confidence: {self.confidence_threshold}")

        except Exception as e:
            self.logger.error(f"Failed to initialize Hailo device: {e}")
            self.logger.warning("Falling back to simulation mode")
            self.device = None

    def preprocess(self, frame: np.ndarray) -> np.ndarray:
        """
        Preprocess frame for YOLOv8n inference

        Args:
            frame: Input frame (BGR format from OpenCV)

        Returns:
            Preprocessed frame ready for inference
        """
        # Resize to model input size
        resized = cv2.resize(frame, self.input_size)

        # Convert BGR to RGB
        rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)

        # Normalize to [0, 1]
        normalized = rgb.astype(np.float32) / 255.0

        # Add batch dimension
        batched = np.expand_dims(normalized, axis=0)

        return batched

    def postprocess(self, outputs: List[np.ndarray], frame_shape: Tuple[int, int]) -> List[Detection]:
        """
        Postprocess YOLOv8n outputs to detections

        Args:
            outputs: Raw model outputs
            frame_shape: Original frame shape (height, width)

        Returns:
            List of Detection objects
        """
        detections = []

        # YOLOv8n output format: [batch, 84, 8400]
        # 84 = 4 bbox coords + 80 class scores
        output = outputs[0][0]  # Remove batch dimension

        # Transpose to [8400, 84]
        output = output.transpose()

        # Extract bounding boxes and scores
        boxes = output[:, :4]  # [x_center, y_center, width, height]
        scores = output[:, 4:]  # [80 class scores]

        # Get class with highest score for each detection
        class_ids = np.argmax(scores, axis=1)
        confidences = np.max(scores, axis=1)

        # Filter by confidence threshold
        mask = confidences > self.confidence_threshold
        boxes = boxes[mask]
        class_ids = class_ids[mask]
        confidences = confidences[mask]

        # Convert from center format to corner format
        # Scale to original frame size
        h, w = frame_shape
        scale_x = w / self.input_size[0]
        scale_y = h / self.input_size[1]

        for box, class_id, confidence in zip(boxes, class_ids, confidences):
            x_center, y_center, width, height = box

            # Convert to corner format
            x1 = int((x_center - width / 2) * scale_x)
            y1 = int((y_center - height / 2) * scale_y)
            x2 = int((x_center + width / 2) * scale_x)
            y2 = int((y_center + height / 2) * scale_y)

            # Clip to frame bounds
            x1 = max(0, min(x1, w))
            y1 = max(0, min(y1, h))
            x2 = max(0, min(x2, w))
            y2 = max(0, min(y2, h))

            detections.append(Detection(
                class_name=self.class_names[class_id],
                confidence=float(confidence),
                bbox=(x1, y1, x2 - x1, y2 - y1)
            ))

        # Apply NMS (non-max suppression)
        detections = self._apply_nms(detections)

        return detections

    def _apply_nms(self, detections: List[Detection]) -> List[Detection]:
        """Apply non-maximum suppression to remove duplicate detections"""
        if not detections:
            return []

        # Convert to format for cv2.dnn.NMSBoxes
        boxes = [d.bbox for d in detections]
        confidences = [d.confidence for d in detections]

        indices = cv2.dnn.NMSBoxes(
            boxes,
            confidences,
            self.confidence_threshold,
            self.nms_threshold
        )

        if len(indices) > 0:
            return [detections[i] for i in indices.flatten()]
        return []

    def detect(self, frame: np.ndarray) -> List[Detection]:
        """
        Run object detection on frame

        Args:
            frame: Input frame (BGR format from OpenCV)

        Returns:
            List of Detection objects
        """
        if self.device is None:
            # Simulation mode - return dummy detections
            return self._simulate_detection(frame)

        try:
            # Preprocess
            input_data = self.preprocess(frame)

            # Run inference on Hailo
            outputs = self.input_vstreams.infer(input_data)

            # Postprocess
            detections = self.postprocess(outputs, frame.shape[:2])

            return detections

        except Exception as e:
            self.logger.error(f"Detection failed: {e}")
            return []

    def _simulate_detection(self, frame: np.ndarray) -> List[Detection]:
        """Simulate detections when Hailo hardware not available"""
        import random

        # 20% chance of detecting something
        if random.random() < 0.2:
            h, w = frame.shape[:2]
            return [Detection(
                class_name=random.choice(["person", "car", "truck"]),
                confidence=random.uniform(0.6, 0.95),
                bbox=(
                    random.randint(0, w // 2),
                    random.randint(0, h // 2),
                    random.randint(50, 200),
                    random.randint(50, 200)
                )
            )]
        return []

    def cleanup(self):
        """Release Hailo resources"""
        if self.input_vstreams:
            self.input_vstreams.release()
        if self.output_vstreams:
            self.output_vstreams.release()
        if self.network_group:
            self.network_group.release()

        self.logger.info("Hailo detector cleanup complete")


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    detector = HailoDetector()

    if cv2 is not None:
        # Example: Process video stream
        cap = cv2.VideoCapture(0)  # Camera 0

        print("Press 'q' to quit")

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # Detect objects
            detections = detector.detect(frame)

            # Draw detections
            for det in detections:
                x, y, w, h = det.bbox
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                label = f"{det.class_name}: {det.confidence:.2f}"
                cv2.putText(frame, label, (x, y - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

            cv2.imshow("Hailo Detection", frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()

    detector.cleanup()
