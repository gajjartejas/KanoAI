"""
Sample Gujarati OCR Image Generator
Creates high-fidelity synthetic benchmark images for testing Gujarati OCR:
1. Printed Book / Document
2. Street Photo / Signboard Scene Text
3. Handwritten Student Notebook on Ruled Paper
4. Official State Certificate / Document
5. Difficult Conjuncts & Isolated Numerals
"""

import os
import random
from PIL import Image, ImageDraw, ImageFont, ImageFilter

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FONTS_DIR = os.path.join(REPO_ROOT, "fonts", "Noto_Sans_Gujarati")
OUT_DIR = os.path.join(REPO_ROOT, "docs", "assets", "ocr_samples")
os.makedirs(OUT_DIR, exist_ok=True)

FONT_REGULAR = os.path.join(FONTS_DIR, "NotoSansGujarati-Regular.ttf")
FONT_BOLD = os.path.join(FONTS_DIR, "NotoSansGujarati-Bold.ttf")
FONT_MEDIUM = os.path.join(FONTS_DIR, "NotoSansGujarati-Medium.ttf")


def get_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


def generate_sample_1_printed_book():
    """Sample 1: Printed Book Page with Header, Divider and Paragraphs."""
    width, height = 900, 600
    img = Image.new("RGB", (width, height), color=(252, 250, 245))
    draw = ImageDraw.Draw(img)

    # Subtle paper border
    draw.rectangle([10, 10, width - 11, height - 11], outline=(220, 215, 205), width=2)
    draw.rectangle([20, 20, width - 21, height - 21], outline=(235, 230, 220), width=1)

    f_title = get_font(FONT_BOLD, 36)
    f_sub = get_font(FONT_MEDIUM, 22)
    f_body = get_font(FONT_REGULAR, 26)
    f_quote = get_font(FONT_BOLD, 26)

    # Header
    draw.text((60, 45), "પંચતંત્રની બોધકથાઓ : ચતુર સસલું", font=f_title, fill=(20, 25, 35))
    draw.line([(60, 95), (width - 60, 95)], fill=(180, 175, 165), width=2)

    # Subtitle
    draw.text((60, 115), "પ્રકરણ ૧ : બુદ્ધિ આગળ બળ પાણી ભરે છે", font=f_sub, fill=(100, 105, 120))

    # Paragraph lines
    lines = [
        "એક રમણીય અને ઘટાદાર વનમાં ભાસુરક નામનો એક મહાબળવાન સિંહ રહેતો હતો.",
        "તે વનના તમામ પશુઓ પર અત્યાચાર કરતો અને રોજના અનેક જીવોનો શિકાર કરતો.",
        "આખરે બધા પશુઓએ ભેગા મળીને રોજ એક-એક પશુ સિંહના ખોરાક તરીકે મોકલવાનું નક્કી કર્યું.",
        "એક દિવસ એક નાના પણ ચતુર સસલાનો વારો આવ્યો.",
        "સસલાએ વનમાં એક ઊંડો કૂવો જોયો અને સિંહને કહ્યું: 'વનમાં બીજો સિંહ આવી ગયો છે!'",
        "ક્રોધે ભરાયેલા સિંહે કૂવામાં પોતાનો જ પડછાયો જોયો અને તરાપ મારીને ડૂબી મર્યો.",
    ]

    y = 170
    for line in lines:
        draw.text((60, y), line, font=f_body, fill=(30, 35, 45))
        y += 48

    # Moral Box
    draw.rectangle([60, y + 15, width - 60, y + 80], fill=(245, 240, 230), outline=(210, 200, 185), width=2)
    draw.text((80, y + 32), "બોધ : બળ કરતાં બુદ્ધિ ચડિયાતી છે. (Knowledge is greater than strength.)", font=f_quote, fill=(160, 40, 20))

    out_path = os.path.join(OUT_DIR, "sample_1_printed_book.png")
    img.save(out_path, "PNG", optimize=True)
    print(f"Generated: {out_path}")


def generate_sample_2_photo_signboard():
    """Sample 2: Outdoor Street / Transport Signboard Scene Text."""
    width, height = 900, 520
    img = Image.new("RGB", (width, height), color=(15, 23, 42))
    draw = ImageDraw.Draw(img)

    # Metallic signboard styling
    draw.rectangle([25, 25, width - 26, height - 26], fill=(16, 75, 145), outline=(220, 225, 230), width=6)
    draw.rectangle([35, 35, width - 36, height - 36], outline=(255, 255, 255), width=2)

    f_top = get_font(FONT_MEDIUM, 22)
    f_main = get_font(FONT_BOLD, 46)
    f_eng = get_font(FONT_BOLD, 28)
    f_sub = get_font(FONT_BOLD, 30)
    f_pill = get_font(FONT_BOLD, 22)

    # Header banner
    draw.rectangle([37, 37, width - 37, 95], fill=(255, 165, 0))
    draw.text((60, 50), "ગુજરાત પ્રવાસન નિગમ • GUJARAT TOURISM", font=f_top, fill=(10, 20, 30))

    # Main station title
    draw.text((60, 130), "અમદાવાદ જંકશન", font=f_main, fill=(255, 255, 255))
    draw.text((60, 195), "AHMEDABAD JUNCTION", font=f_eng, fill=(255, 235, 100))

    draw.line([(60, 250), (width - 60, 250)], fill=(255, 255, 255, 160), width=3)

    # Direction and Facilities
    draw.text((60, 280), "આપનું હાર્દિક સ્વાગત છે • WELCOME", font=f_sub, fill=(240, 245, 255))
    draw.text((60, 335), "પ્લેટફોર્મ નં. ૧ થી ૧૨  |  ટિકિટ બારી અને પૂછપરછ", font=f_sub, fill=(255, 255, 255))

    # Badges / Pills
    draw.rectangle([60, 400, 280, 450], fill=(46, 125, 50), outline=(255, 255, 255), width=2)
    draw.text((80, 412), "મુખ્ય પ્રવેશદ્વાર ➔", font=f_pill, fill=(255, 255, 255))

    draw.rectangle([310, 400, 560, 450], fill=(211, 47, 47), outline=(255, 255, 255), width=2)
    draw.text((330, 412), "સ્વચ્છ ભારત અભિયાન", font=f_pill, fill=(255, 255, 255))

    out_path = os.path.join(OUT_DIR, "sample_2_photo_signboard.png")
    img.save(out_path, "PNG", optimize=True)
    print(f"Generated: {out_path}")


def generate_sample_3_handwritten_note():
    """Sample 3: Handwritten Student Notebook on Ruled Paper."""
    width, height = 850, 580
    img = Image.new("RGB", (width, height), color=(253, 252, 248))
    draw = ImageDraw.Draw(img)

    # Red vertical margin line
    margin_x = 110
    draw.line([(margin_x, 0), (margin_x, height)], fill=(235, 100, 100), width=2)

    # Blue ruled horizontal lines
    start_y = 70
    line_spacing = 52
    y_lines = []
    y = start_y
    while y < height:
        draw.line([(0, y), (width, y)], fill=(185, 215, 245), width=1)
        y_lines.append(y)
        y += line_spacing

    f_title = get_font(FONT_BOLD, 30)
    f_hand = get_font(FONT_MEDIUM, 26)

    # Date header in top right
    draw.text((width - 240, 25), "તારીખ: ૦૮/૧૦/૨૦૨૬", font=f_hand, fill=(40, 60, 120))

    # Notebook Title
    draw.text((margin_x + 25, 22), "ગાંધીજીના અણમોલ સુવિચારો :", font=f_title, fill=(20, 30, 80))

    # Handwritten notes with subtle baseline variations simulating natural handwriting
    notes = [
        "૧. સત્ય એ જ મારો ઈશ્વર છે અને પ્રેમ એ જ મારો માર્ગ.",
        "૨. અહિંસા એ માત્ર કાયરતા નથી, પણ શક્તિશાળીનું સાચું હથિયાર છે.",
        "૩. તમારો આજનો વિચાર તમારા આવતીકાલનું નિર્માણ કરે છે.",
        "૪. શિક્ષણ એટલે બાળક અને માણસના શરીર, મન અને આત્માનો વિકાસ.",
        "૫. મારું જીવન એ જ મારો સંદેશ છે. - મહાત્મા ગાંધી",
        "૬. કસ્તુરબા આશ્રમ, સાબરમતી નદી કાંઠે, અમદાવાદ.",
        "૭. ગુજરાતી ભાષા આપણી અસ્મિતા અને ગૌરવ છે.",
        "૮. જય હિન્દ! જય જય ગરવી ગુજરાત!",
    ]

    for idx, text in enumerate(notes):
        if idx < len(y_lines) - 1:
            line_y = y_lines[idx] + 12
            draw.text((margin_x + 25, line_y), text, font=f_hand, fill=(15, 30, 75))

    out_path = os.path.join(OUT_DIR, "sample_3_handwritten_note.png")
    img.save(out_path, "PNG", optimize=True)
    print(f"Generated: {out_path}")


def generate_sample_4_official_doc():
    """Sample 4: Official Certificate / Government Document."""
    width, height = 900, 560
    img = Image.new("RGB", (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    # Certificate border
    draw.rectangle([15, 15, width - 16, height - 16], outline=(180, 130, 50), width=4)
    draw.rectangle([25, 25, width - 26, height - 26], outline=(220, 180, 100), width=1)

    f_top = get_font(FONT_BOLD, 22)
    f_cert = get_font(FONT_BOLD, 38)
    f_body = get_font(FONT_MEDIUM, 24)
    f_val = get_font(FONT_BOLD, 26)

    # Emblem placeholder
    draw.ellipse([(width // 2 - 30, 40), (width // 2 + 30, 100)], fill=(245, 235, 210), outline=(180, 130, 50), width=2)
    draw.text((width // 2 - 14, 55), "🏛️", font=f_top)

    draw.text((width // 2 - 160, 115), "ગુજરાત માધ્યમિક શિક્ષણ બોર્ડ, ગાંધીનગર", font=f_top, fill=(60, 40, 20))
    draw.text((width // 2 - 170, 150), "પ્રમાણપત્ર : ગુજરાતી ભાષા પ્રાવીણ્ય", font=f_cert, fill=(140, 30, 20))

    draw.line([(100, 205), (width - 100, 205)], fill=(180, 130, 50), width=2)

    # Details
    draw.text((80, 230), "પ્રમાણિત કરવામાં આવે છે કે :", font=f_body, fill=(50, 50, 50))
    draw.text((360, 228), "કુમાર આલોકભાઈ મહેતા", font=f_val, fill=(20, 30, 80))

    draw.text((80, 280), "પરીક્ષા કેન્દ્ર : સુરત", font=f_body, fill=(50, 50, 50))
    draw.text((450, 280), "રોલ નંબર : GJ-૨૦૨૬-૪૫૮૯", font=f_val, fill=(20, 30, 80))

    draw.text((80, 330), "મેળવેલ ગુણ : ૯૫ / ૧૦૦", font=f_val, fill=(30, 120, 40))
    draw.text((450, 330), "શ્રેણી : વિશિષ્ટ યોગ્યતા (Distinction)", font=f_val, fill=(160, 30, 20))

    draw.text((80, 385), "તેમણે ગુજરાતી વાંચન, લેખન અને વ્યાકરણમાં શ્રેષ્ઠતા સિદ્ધ કરી છે.", font=f_body, fill=(60, 60, 60))

    # Signature line
    draw.line([(width - 280, 480), (width - 80, 480)], fill=(100, 100, 100), width=1)
    draw.text((width - 250, 490), "નિયામકશ્રી (પરીક્ષા)", font=f_top, fill=(70, 70, 70))

    out_path = os.path.join(OUT_DIR, "sample_4_official_doc.png")
    img.save(out_path, "PNG", optimize=True)
    print(f"Generated: {out_path}")


def generate_sample_5_conjuncts():
    """Sample 5: Difficult Isolated Characters, Conjuncts (જોડાક્ષરો) and Numerals."""
    width, height = 800, 480
    img = Image.new("RGB", (width, height), color=(248, 250, 252))
    draw = ImageDraw.Draw(img)

    f_title = get_font(FONT_BOLD, 28)
    f_large = get_font(FONT_BOLD, 42)
    f_words = get_font(FONT_MEDIUM, 30)

    draw.text((40, 30), "ગુજરાતી જોડાક્ષરો (Conjuncts) અને સંખ્યાઓ (Numerals)", font=f_title, fill=(15, 23, 42))
    draw.line([(40, 75), (width - 40, 75)], fill=(203, 213, 225), width=2)

    # Conjunct Glyphs
    draw.text((40, 100), "ક્ષ   જ્ઞ   ત્ર   શ્ર   દ્વ   દ્ભ   હ્મ   ઙ", font=f_large, fill=(225, 29, 72))
    draw.text((40, 175), "શબ્દો: વિદ્યા   સૂર્ય   કૃષ્ણ   બુદ્ધિ   જ્ઞાન   સત્ય", font=f_words, fill=(30, 41, 59))

    draw.line([(40, 240), (width - 40, 240)], fill=(203, 213, 225), width=1)

    # Numerals
    draw.text((40, 265), "ગુજરાતી અંકો: ૦  ૧  ૨  ૩  ૪  ૫  ૬  ૭  ૮  ૯  ૧૦", font=f_large, fill=(14, 116, 144))
    draw.text((40, 345), "ગણતરી: ૧૨૫ + ૩૭૫ = ૫૦૦  |  તારીખ: ૨૦૨૬", font=f_words, fill=(71, 85, 105))

    out_path = os.path.join(OUT_DIR, "sample_5_conjuncts.png")
    img.save(out_path, "PNG", optimize=True)
    print(f"Generated: {out_path}")


if __name__ == "__main__":
    generate_sample_1_printed_book()
    generate_sample_2_photo_signboard()
    generate_sample_3_handwritten_note()
    generate_sample_4_official_doc()
    generate_sample_5_conjuncts()
    print("All 5 benchmark sample images generated successfully!")
