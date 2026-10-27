import io
import email.message
import docx
from docx.opc.constants import RELATIONSHIP_TYPE as RT
import fitz
from PIL import Image
import httpx

API_URL = "http://127.0.0.1:8000/api/analyze"

def make_png():
    img = Image.new("RGB", (300, 200), (200, 100, 50))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return ("sample.png", buf.getvalue(), "image/png")

def make_jpg():
    img = Image.new("RGB", (300, 200), (50, 100, 200))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return ("sample.jpg", buf.getvalue(), "image/jpeg")

def make_webp():
    img = Image.new("RGB", (300, 200), (50, 200, 100))
    buf = io.BytesIO()
    img.save(buf, format="WEBP")
    return ("sample.webp", buf.getvalue(), "image/webp")

def make_text_pdf():
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 72), "Congratulations! Selected for Virtual Internship. Pay Rs 1500 refundable deposit.")
    rect = fitz.Rect(50, 72, 350, 90)
    page.insert_link({"kind": fitz.LINK_URI, "from": rect, "uri": "https://fake-internship-portal.org/pay"})
    buf = doc.tobytes()
    doc.close()
    return ("offer.pdf", buf, "application/pdf")

def make_scanned_pdf():
    img = Image.new("RGB", (400, 300), (240, 240, 240))
    img_io = io.BytesIO()
    img.save(img_io, format="JPEG")
    doc = fitz.open()
    page = doc.new_page(width=400, height=300)
    page.insert_image(fitz.Rect(0, 0, 400, 300), stream=img_io.getvalue())
    buf = doc.tobytes()
    doc.close()
    return ("scan.pdf", buf, "application/pdf")

def make_docx():
    doc = docx.Document()
    doc.add_paragraph("Dear Applicant, Your loan has been approved. Click here:")
    doc.part.relate_to("https://fake-loan-subsidy.com/claim", RT.HYPERLINK, is_external=True)
    buf = io.BytesIO()
    doc.save(buf)
    return ("loan_approval.docx", buf.getvalue(), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")

def make_txt():
    content = "URGENT: Electricity power will be disconnected tonight at 9:30 PM due to unpaid bill. Call officer at 9876543210 immediately."
    return ("power_notice.txt", content.encode("utf-8"), "text/plain")

def make_eml():
    msg = email.message.EmailMessage()
    msg["From"] = "security-update@sbi-online-alerts.top"
    msg["To"] = "customer@example.com"
    msg["Subject"] = "URGENT: Your SBI netbanking account is suspended"
    msg.set_content("Please click https://sbi-kyc-verify.top/login to update your KYC immediately.")
    return ("phishing_email.eml", msg.as_bytes(), "message/rfc822")

def make_doc():
    # Legacy OLE2 compound document header without Word streams
    ole_header = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1" + b"\x00" * 504
    return ("legacy_notice.doc", ole_header, "application/msword")

def make_corrupt_png():
    return ("broken.png", b"\x89PNG\r\n\x1a\ncorruptcontent", "image/png")

def make_mislabelled():
    return ("sneaky.png", b"This is plain text disguised with a .png extension", "image/png")

formats_to_test = [
    ("PNG", make_png),
    ("JPG", make_jpg),
    ("WEBP", make_webp),
    ("PDF (text)", make_text_pdf),
    ("PDF (scanned)", make_scanned_pdf),
    ("DOCX", make_docx),
    ("TXT", make_txt),
    ("EML", make_eml),
    ("DOC (legacy Word)", make_doc),
    ("Corrupt file", make_corrupt_png),
    ("Mislabelled file", make_mislabelled),
]

with httpx.Client(timeout=30.0) as client:
    print("=" * 60)
    print("MANUAL UPLOAD TEST MATRIX (http://127.0.0.1:8000/api/analyze)")
    print("=" * 60)
    for name, maker in formats_to_test:
        filename, data_bytes, mime = maker()
        try:
            resp = client.post(
                API_URL,
                files={"file": (filename, data_bytes, mime)},
                data={"language": "en", "mode": "mock"},
            )
            print(f"[{name}] status={resp.status_code}")
            if resp.status_code == 200:
                res = resp.json()
                print(f"   -> band={res.get('band')}, score={res.get('score')}, doc_type={res.get('extracted', {}).get('document_type')}")
            else:
                err = resp.json().get("detail", resp.text)
                print(f"   -> rejected with error: {err}")
        except Exception as e:
            print(f"[{name}] EXCEPTION: {e}")
    print("=" * 60)
