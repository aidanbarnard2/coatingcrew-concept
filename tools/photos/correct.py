"""Photo pass for the crew's own phone photos: gentle local contrast and a touch of color, no color shifts.
Mean brightness is kept, so bright garages stay bright. No sharpening, to keep files small."""
import cv2
import numpy as np
from PIL import Image


def enhance(path, blend=0.35):
    bgr = cv2.imread(path)
    lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB)
    L = lab[:, :, 0]
    cl = cv2.createCLAHE(clipLimit=1.4, tileGridSize=(8, 8)).apply(L)
    L2 = cv2.addWeighted(L, 1 - blend, cl, blend, 0)
    L2 = np.clip(L2.astype(np.float32) * (L.mean() / max(L2.mean(), 1)), 0, 255).astype(np.uint8)
    lab[:, :, 0] = L2
    ab = lab[:, :, 1:].astype(np.float32) - 128
    lab[:, :, 1:] = np.clip(ab * 1.08 + 128, 0, 255).astype(np.uint8)
    return Image.fromarray(cv2.cvtColor(cv2.cvtColor(lab, cv2.COLOR_LAB2BGR), cv2.COLOR_BGR2RGB))
