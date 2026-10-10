"""
Unified Gujarati OCR Service
Coordinates IndicPhotoOCR (Bhashini-IITJ), Gujarati TrOCR (umangchaudhari),
and GujaratiHCR handwritten recognition.
"""

import os
import json
import base64
from typing import Dict, Any, List

from .indic_photo_ocr import IndicPhotoOCR
from .trocr_service import GujaratiTrOCR
from .handwriting_hcr import GujaratiHCR

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SAMPLES_DIR = os.path.join(REPO_ROOT, "docs", "assets", "ocr_samples")


class OCRService:
    def __init__(self):
        self.indic_photo = IndicPhotoOCR()
        self.trocr = GujaratiTrOCR()
        self.hcr = GujaratiHCR()

    def get_sample_catalogs(self) -> List[Dict[str, Any]]:
        """Returns metadata for built-in benchmark sample images."""
        return [
            {
                "id": "sample_1_printed_book",
                "title": "📖 Printed Book Page (પંચતંત્ર બોધકથા)",
                "category": "printed",
                "recommended_engine": "indic_photo_ocr",
                "image_url": "assets/ocr_samples/sample_1_printed_book.png",
                "description": "Scanned Gujarati story page with title, subtitle, paragraph lines, and moral callout box.",
                "ground_truth": "પંચતંત્રની બોધકથાઓ : ચતુર સસલું\nપ્રકરણ ૧ : બુદ્ધિ આગળ બળ પાણી ભરે છે\nએક રમણીય અને ઘટાદાર વનમાં ભાસુરક નામનો એક મહાબળવાન સિંહ રહેતો હતો.\nતે વનના તમામ પશુઓ પર અત્યાચાર કરતો અને રોજના અનેક જીવોનો શિકાર કરતો.\nઆખરે બધા પશુઓએ ભેગા મળીને રોજ એક-એક પશુ સિંહના ખોરાક તરીકે મોકલવાનું નક્કી કર્યું.\nએક દિવસ એક નાના પણ ચતુર સસલાનો વારો આવ્યો.\nસસલાએ વનમાં એક ઊંડો કૂવો જોયો અને સિંહને કહ્યું: 'વનમાં બીજો સિંહ આવી ગયો છે!'\nક્રોધે ભરાયેલા સિંહે કૂવામાં પોતાનો જ પડછાયો જોયો અને તરાપ મારીને ડૂબી મર્યો.\nબોધ : બળ કરતાં બુદ્ધિ ચડિયાતી છે."
            },
            {
                "id": "sample_2_photo_signboard",
                "title": "🚏 Street Signboard / Scene Text (અમદાવાદ જંકશન)",
                "category": "scene",
                "recommended_engine": "indic_photo_ocr",
                "image_url": "assets/ocr_samples/sample_2_photo_signboard.png",
                "description": "Multi-colored railway & tourism station sign with bilingual text, direction arrows, and badges.",
                "ground_truth": "ગુજરાત પ્રવાસન નિગમ • GUJARAT TOURISM\nઅમદાવાદ જંકશન\nAHMEDABAD JUNCTION\nઆપનું હાર્દિક સ્વાગત છે • WELCOME\nપ્લેટફોર્મ નં. ૧ થી ૧૨  |  ટિકિટ બારી અને પૂછપરછ\nમુખ્ય પ્રવેશદ્વાર ➔  |  સ્વચ્છ ભારત અભિયાન"
            },
            {
                "id": "sample_3_handwritten_note",
                "title": "✍️ Handwritten Notebook (ગાંધીજીના સુવિચારો)",
                "category": "handwritten",
                "recommended_engine": "gujarati_hcr",
                "image_url": "assets/ocr_samples/sample_3_handwritten_note.png",
                "description": "Cursive student handwriting on ruled lined notepad with red margin and date header.",
                "ground_truth": "તારીખ: ૦૮/૧૦/૨૦૨૬\nગાંધીજીના અણમોલ સુવિચારો :\n૧. સત્ય એ જ મારો ઈશ્વર છે અને પ્રેમ એ જ મારો માર્ગ.\n૨. અહિંસા એ માત્ર કાયરતા નથી, પણ શક્તિશાળીનું સાચું હથિયાર છે.\n૩. તમારો આજનો વિચાર તમારા આવતીકાલનું નિર્માણ કરે છે.\n૪. શિક્ષણ એટલે બાળક અને માણસના શરીર, મન અને આત્માનો વિકાસ.\n૫. મારું જીવન એ જ મારો સંદેશ છે. - મહાત્મા ગાંધી\n૬. કસ્તુરબા આશ્રમ, સાબરમતી નદી કાંઠે, અમદાવાદ.\n૭. ગુજરાતી ભાષા આપણી અસ્મિતા અને ગૌરવ છે.\n૮. જય હિન્દ! જય જય ગરવી ગુજરાત!"
            },
            {
                "id": "sample_4_official_doc",
                "title": "🏛️ Official Certificate (શિક્ષણ બોર્ડ પ્રમાણપત્ર)",
                "category": "document",
                "recommended_engine": "indic_photo_ocr",
                "image_url": "assets/ocr_samples/sample_4_official_doc.png",
                "description": "Government state certificate layout with decorative emblem, bordered fields, roll number, and signature.",
                "ground_truth": "ગુજરાત માધ્યમિક શિક્ષણ બોર્ડ, ગાંધીનગર\nપ્રમાણપત્ર : ગુજરાતી ભાષા પ્રાવીણ્ય\nપ્રમાણિત કરવામાં આવે છે કે : કુમાર આલોકભાઈ મહેતા\nપરીક્ષા કેન્દ્ર : સુરત | રોલ નંબર : GJ-૨૦૨૬-૪૫૮૯\nમેળવેલ ગુણ : ૯૫ / ૧૦૦ | શ્રેણી : વિશિષ્ટ યોગ્યતા (Distinction)\nતેમણે ગુજરાતી વાંચન, લેખન અને વ્યાકરણમાં શ્રેષ્ઠતા સિદ્ધ કરી છે.\nનિયામકશ્રી (પરીક્ષા)"
            },
            {
                "id": "sample_5_conjuncts",
                "title": "🔤 Isolated Conjuncts & Numerals (જોડાક્ષરો અને અંકો)",
                "category": "isolated",
                "recommended_engine": "gujarati_trocr",
                "image_url": "assets/ocr_samples/sample_5_conjuncts.png",
                "description": "Complex compound ligatures (ક્ષ, જ્ઞ, ત્ર, શ્ર, દ્વ), matra conjuncts (વિદ્યા, સૂર્ય, કૃષ્ણ), and Gujarati digits ૦–૧૦.",
                "ground_truth": "ગુજરાતી જોડાક્ષરો (Conjuncts) અને સંખ્યાઓ (Numerals)\nક્ષ   જ્ઞ   ત્ર   શ્ર   દ્વ   દ્ભ   હ્મ   ઙ\nશબ્દો: વિદ્યા   સૂર્ય   કૃષ્ણ   બુદ્ધિ   જ્ઞાન   સત્ય\nગુજરાતી અંકો: ૦  ૧  ૨  ૩  ૪  ૫  ૬  ૭  ૮  ૯  ૧૦\nગણતરી: ૧૨૫ + ૩૭૫ = ૫૦૦  |  તારીખ: ૨૦૨૬"
            }
        ]

    def recognize(
        self,
        image_input,
        engine: str = "indic_photo_ocr",
        lang: str = "gujarati",
        api_url: str = None,
        hf_token: str = None,
        mode: str = "offline",
        options: dict = None,
        sample_id: str = None
    ) -> Dict[str, Any]:
        """
        Processes image with the chosen OCR engine.
        """
        engine = engine.lower().strip()

        if engine in ["indic_photo_ocr", "bhashini", "scene"]:
            res = self.indic_photo.recognize(
                image_input,
                lang=lang,
                hf_token=hf_token,
                mode=mode,
                api_url=api_url
            )
            # If Bhashini cloud is unreachable or errored, seamlessly fallback to Local TrOCR
            if not res.get("success"):
                print(f"[OCR Service] IndicPhotoOCR unreachable ({res.get('error')}). Auto-routing to Local Gujarati TrOCR...")
                trocr_res = self.trocr.recognize(image_input, api_url=api_url, mode=mode)
                if trocr_res.get("success") and trocr_res.get("text"):
                    trocr_res["note"] = "Bhashini Space unreachable; auto-transcribed via Local TrOCR Engine."
                    return trocr_res
                # Otherwise fallback to GujaratiHCR
                hcr_res = self.hcr.recognize(image_input)
                hcr_res["note"] = "Processed via GujaratiHCR Document Pipeline."
                return hcr_res

            # If photo OCR returned empty text but succeeded (e.g. custom upload in offline mode),
            # automatically transcribe via online Bhashini space (TextBPN++ & PARSeq) or local TrOCR:
            if res.get("success") and not res.get("text"):
                print("[OCR Service] Offline IndicPhotoOCR produced no text for custom upload. Auto-transcribing via Bhashini neural pipeline...")
                try:
                    online_res = self.indic_photo.recognize(
                        image_input,
                        lang=lang,
                        hf_token=hf_token,
                        mode="online"
                    )
                    if online_res.get("success") and online_res.get("text"):
                        # Keep high-resolution local boxes/annotations if online did not provide them
                        if res.get("boxes") and not online_res.get("boxes"):
                            online_res["boxes"] = res["boxes"]
                            online_res["box_count"] = len(res["boxes"])
                        if res.get("processed_image_base64") and not online_res.get("processed_image_base64"):
                            online_res["processed_image_base64"] = res["processed_image_base64"]
                        return online_res
                except Exception as online_err:
                    print(f"[OCR Service] Online Bhashini auto-transcription warning: {online_err}")

                # If online not reachable, attempt local TrOCR recognition
                trocr_res = self.trocr.recognize(image_input, api_url=api_url, mode=mode)
                if trocr_res.get("success") and trocr_res.get("text"):
                    res["text"] = trocr_res["text"]
                    res["lines"] = trocr_res.get("lines", [l for l in trocr_res["text"].splitlines() if l.strip()])
                    res["model_name"] = "IndicPhotoOCR + Local TrOCR Hybrid"
                    return res

                # Augment with HCR fallback segmentation
                hcr_res = self.hcr.recognize(image_input)
                if hcr_res.get("success") and hcr_res.get("boxes"):
                    res["boxes"] = hcr_res["boxes"]
                    res["box_count"] = len(hcr_res["boxes"])
            return res

        elif engine in ["gujarati_trocr", "trocr", "printed"]:
            return self.trocr.recognize(image_input, api_url=api_url, hf_token=hf_token, mode=mode)

        elif engine in ["gujarati_hcr", "hcr", "handwriting"]:
            return self.hcr.recognize(image_input)

        else:
            # Default to IndicPhotoOCR
            return self.indic_photo.recognize(image_input, lang=lang, hf_token=hf_token, mode=mode)

    def compare(
        self,
        image_input,
        lang: str = "gujarati",
        hf_token: str = None,
        api_url: str = None
    ) -> Dict[str, Any]:
        """
        Executes Dual Engine comparison (IndicPhotoOCR vs GujaratiTrOCR / GujaratiHCR).
        """
        res_photo = self.indic_photo.recognize(image_input, lang=lang, hf_token=hf_token)
        res_hcr = self.hcr.recognize(image_input)

        return {
            "success": True,
            "mode": "comparison",
            "results": {
                "indic_photo_ocr": res_photo,
                "gujarati_hcr": res_hcr
            }
        }
