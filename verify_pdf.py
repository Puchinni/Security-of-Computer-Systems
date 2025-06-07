import hashlib
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes, serialization
import PyPDF2
from io import BytesIO

def verify_pdf_signature(pdf_path, public_key_bytes):
    reader = PyPDF2.PdfReader(pdf_path)
    metadata = reader.metadata

    if "/Signature" not in metadata:
        print("Signature not found in PDF metadata")
        return False

    signature = bytes.fromhex(metadata["/Signature"])

    # Create a PDF writer to reconstruct the PDF without the signature
    writer = PyPDF2.PdfWriter()
    for page in reader.pages:
        writer.add_page(page)

    metadata_without_signature = dict(metadata)
    metadata_without_signature.pop("/Signature", None)
    writer.add_metadata(metadata_without_signature)

    temp_stream = BytesIO()
    writer.write(temp_stream)
    pdf_data_without_signature = temp_stream.getvalue()

    # Calculate the hash of the PDF data without signature
    hash_digest = hashlib.sha256(pdf_data_without_signature).digest()

    # Add the public key to verify the signature
    public_key = serialization.load_pem_public_key(public_key_bytes)

    try:
        public_key.verify(
            signature,
            hash_digest,
            padding.PKCS1v15(),
            hashes.SHA256()
        )
        print("Signature is valid")
        return True
    except Exception as e:
        print(f"Invalid signature: {e}")
        return False