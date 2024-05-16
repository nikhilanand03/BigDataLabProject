import torch
import albumentations as A
from albumentations.pytorch import ToTensorV2
import cv2

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
LEARNING_RATE = 8e-6
WEIGHT_DECAY = 1e-3
BATCH_SIZE = 64
NUM_EPOCHS = 100
NUM_WORKERS = 4
CHECKPOINT_FILE = "b0.pth.tar"
PIN_MEMORY = True
SAVE_MODEL = True
LOAD_MODEL = True

train_transforms = A.Compose(
    [
        A.Resize(width=96, height=96),
        A.Rotate(limit=15, border_mode=cv2.BORDER_CONSTANT, p=0.8),
        A.HorizontalFlip(p=0.4),
        A.RandomBrightnessContrast(contrast_limit=0.5, brightness_limit=0.5, p=0.2),
        A.OneOf([
            A.GaussNoise(p=0.8),
            A.CLAHE(p=0.8),
            A.ImageCompression(p=0.8),
            A.RandomGamma(p=0.8),
            A.Posterize(p=0.8),
            A.Blur(p=0.8),
        ], p=1.0),
        A.OneOf([
            A.GaussNoise(p=0.8),
            A.CLAHE(p=0.8),
            A.ImageCompression(p=0.8),
            A.RandomGamma(p=0.8),
            A.Posterize(p=0.8),
            A.Blur(p=0.8),
        ], p=1.0),
        A.ShiftScaleRotate(shift_limit=0.1, scale_limit=0.1, rotate_limit=0, p=0.2, border_mode=cv2.BORDER_CONSTANT),
        A.Normalize(mean=[0.4897, 0.4897, 0.4897], std=[0.2330, 0.2330, 0.2330], max_pixel_value=255.0,
        ),
        ToTensorV2(),
    ], keypoint_params=A.KeypointParams(format="xy", remove_invisible=False),
)


val_transforms = A.Compose(
    [
        A.Resize(height=96, width=96),
        A.Normalize(mean=[0.4897, 0.4897, 0.4897], std=[0.2330, 0.2330, 0.2330], max_pixel_value=255.0),
        ToTensorV2(),
    ], keypoint_params=A.KeypointParams(format="xy", remove_invisible=False),
)