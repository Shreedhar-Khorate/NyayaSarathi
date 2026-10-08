import cv2
import numpy as np

class ImagePreprocessor:
    @staticmethod
    def preprocess_image(image_path: str) -> np.ndarray:
        # Load image
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Could not read image: {image_path}")

        # Grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Denoise
        denoised = cv2.fastNlMeansDenoising(gray, h=10)
        
        # Contrast Enhancement using CLAHE
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(denoised)
        
        # Safe Deskew: only correct minor tilt (-15 to +15 deg) using text lines
        # Avoid rotating upright images or 90/180/270 degree orientations (handled by PaddleOCR angle cls)
        try:
            thresh = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 3))
            dilated = cv2.dilate(thresh, kernel, iterations=2)
            contours, _ = cv2.findContours(dilated, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
            angles = []
            for c in contours:
                if cv2.contourArea(c) < 150:
                    continue
                rect = cv2.minAreaRect(c)
                (w, h) = rect[1]
                if w == 0 or h == 0:
                    continue
                angle = rect[-1]
                if w < h:
                    angle = angle - 90 if angle > 0 else angle + 90
                if abs(angle) < 15.0 and (w / max(1, h)) >= 2.0:
                    angles.append(angle)
            if len(angles) >= 3:
                median_angle = float(np.median(angles))
                if 0.5 <= abs(median_angle) <= 15.0:
                    (h_img, w_img) = enhanced.shape[:2]
                    center = (w_img // 2, h_img // 2)
                    M = cv2.getRotationMatrix2D(center, median_angle, 1.0)
                    enhanced = cv2.warpAffine(enhanced, M, (w_img, h_img), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
        except Exception:
            pass
                
        # PaddleOCR expects a 3-channel image, so convert the processed grayscale image back to BGR
        final_img = cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR)
        
        return final_img
