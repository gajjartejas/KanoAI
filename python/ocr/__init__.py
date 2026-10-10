"""
KanoAI Gujarati Optical Character Recognition (OCR) Package
"""

from .ocr_service import OCRService
from .indic_photo_ocr import IndicPhotoOCR
from .trocr_service import GujaratiTrOCR
from .handwriting_hcr import GujaratiHCR

__all__ = ["OCRService", "IndicPhotoOCR", "GujaratiTrOCR", "GujaratiHCR"]
