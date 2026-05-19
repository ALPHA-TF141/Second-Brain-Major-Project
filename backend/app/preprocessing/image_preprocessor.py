import cv2


class ImagePreprocessor:
    def prepare_for_ocr(self, image_path: str):
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError("Image could not be read")

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        denoised = cv2.fastNlMeansDenoising(gray, h=10)

        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        contrast = clahe.apply(denoised)

        blurred = cv2.GaussianBlur(contrast, (0, 0), sigmaX=1.0)
        sharpened = cv2.addWeighted(contrast, 1.5, blurred, -0.5, 0)

        binary = cv2.adaptiveThreshold(
            sharpened,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            31,
            11,
        )
        return binary
