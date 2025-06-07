import hashlib
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes, serialization
import PyPDF2
from io import BytesIO


def sign_pdf(pdf_path, private_key_bytes):
    reader = PyPDF2.PdfReader(pdf_path)
    writer = PyPDF2.PdfWriter()

    #Copy all pages from the reader to the writer
    for page in reader.pages:
        writer.add_page(page)

    metadata = reader.metadata or {}
    metadata_without_signature = dict(metadata)
    metadata_without_signature.pop("/Signature", None)  # Just in case there is a signature already

    # Add metadata without signature
    writer.add_metadata(metadata_without_signature)

    # Save the PDF without signature to a temporary stream
    temp_stream = BytesIO()
    writer.write(temp_stream)
    pdf_data_without_signature = temp_stream.getvalue()

    # Calculate the hash of the PDF data without signature
    hash_digest = hashlib.sha256(pdf_data_without_signature).digest()

    private_key = serialization.load_pem_private_key(
        private_key_bytes,
        password=None
    )

    # Sign the hash of the PDF data
    signature = private_key.sign(
        hash_digest,
        padding.PKCS1v15(),
        hashes.SHA256()
    )

    # Add the signature to the metadata
    metadata_with_signature = dict(metadata_without_signature)
    metadata_with_signature["/Signature"] = signature.hex()

    # Create a new PDF writer with the signature in metadata
    writer_with_signature = PyPDF2.PdfWriter()
    for page in reader.pages:
        writer_with_signature.add_page(page)
    writer_with_signature.add_metadata(metadata_with_signature)

    output_pdf_path = pdf_path.replace(".pdf", "_signed.pdf")
    with open(output_pdf_path, "wb") as f_out:
        writer_with_signature.write(f_out)

    return output_pdf_path