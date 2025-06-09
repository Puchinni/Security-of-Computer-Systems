"""!
@file pdf.py
@brief PDF signing module
@details This module provides a function to sign PDF files using a private RSA key
and embed the signature into the PDF metadata.
"""

import hashlib
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import hashes, serialization
import PyPDF2
from io import BytesIO

def sign_pdf(pdf_path, private_key_bytes):
    """!
    Sign a PDF file with a private RSA key.

    This function creates a SHA-256 hash of the PDF content (excluding any existing signature),
    signs the hash using the provided private RSA key, and embeds the hexadecimal signature
    into the PDF's metadata under the key `/Signature`.

    @param pdf_path: Path to the input PDF file.
    @type pdf_path: str
    @param private_key_bytes: Private RSA key in PEM format as bytes.
    @type private_key_bytes: bytes
    @return: Path to the newly signed PDF file.
    @rtype: str
    """
    reader = PyPDF2.PdfReader(pdf_path)
    writer = PyPDF2.PdfWriter()

    # Copy all pages from the reader to the writer
    for page in reader.pages:
        writer.add_page(page)

    metadata = reader.metadata or {}
    metadata_without_signature = dict(metadata)
    metadata_without_signature.pop("/Signature", None)  # Remove existing signature if present

    # Add metadata without signature
    writer.add_metadata(metadata_without_signature)

    # Save the PDF without signature to a temporary stream
    temp_stream = BytesIO()
    writer.write(temp_stream)
    pdf_data_without_signature = temp_stream.getvalue()

    # Calculate the SHA-256 hash of the PDF data
    hash_digest = hashlib.sha256(pdf_data_without_signature).digest()

    # Load the private RSA key
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

    # Embed the signature in the metadata
    metadata_with_signature = dict(metadata_without_signature)
    metadata_with_signature["/Signature"] = signature.hex()

    # Write the final PDF with the signature
    writer_with_signature = PyPDF2.PdfWriter()
    for page in reader.pages:
        writer_with_signature.add_page(page)
    writer_with_signature.add_metadata(metadata_with_signature)

    output_pdf_path = pdf_path.replace(".pdf", "_signed.pdf")
    with open(output_pdf_path, "wb") as f_out:
        writer_with_signature.write(f_out)

    return output_pdf_path
