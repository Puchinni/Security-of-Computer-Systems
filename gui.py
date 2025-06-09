## @file gui.py
#  @brief GUI for the application in tkinter
#  @details This application provides a user interface for generating and saving RSA keys,
#  signing PDF files, and verifying digital signatures.

import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox
from rsa_generator import KeyGenerator
from usb_watch import *
from pdf import *
from verify_pdf import *
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os
import uuid

class GUI:
    """
    Main graphical user interface class.

    Handles RSA key generation, PDF signing, and signature verification using a USB drive.
    """

    def __init__(self, window):
        """
        Initialize the GUI and set up widgets.

        :param window: The main tkinter window.
        """
        self.window = window
        window.title("Qualified Electronic Signature - PAdES")
        window.geometry("600x600")

        self.pin_label = tk.Label(window, text="Enter your PIN")
        self.pin_label.pack()

        self.pin_entry = tk.Entry(window, show="*")
        self.pin_entry.pack()

        self.generate_button = tk.Button(window, text="Generate RSA keys", command=self.generate_keys)
        self.generate_button.pack(pady=5)

        self.drives_label = tk.Label(window, text="Detected USB drives:")
        self.drives_label.pack()

        self.drives_frame = tk.Frame(window)
        self.drives_frame.pack(pady=10)

        self.polling_delay = 2000
        self.known_drives = []
        self.selected_mountpoint = tk.StringVar()

        self.poll_usb_drives()
        self.update_drive_buttons()

        self.sign_button = tk.Button(window, text="Sign PDF", command=self.sign_pdf)
        self.sign_button.pack(pady=5)

        self.verify_button = tk.Button(window, text="Verify Signature", command=self.verify_signature)
        self.verify_button.pack(pady=5)

    def poll_usb_drives(self):
        """
        Periodically poll for USB drives and update the UI.
        """
        self.known_drives, updated, _ = get_usb_update(self.known_drives)
        if updated:
            self.update_drive_buttons()
        self.window.after(self.polling_delay, self.poll_usb_drives)

    def update_drive_buttons(self):
        """
        Update radio buttons for detected USB drives.
        """
        for widget in self.drives_frame.winfo_children():
            widget.destroy()

        if self.known_drives:
            if not self.selected_mountpoint.get() or self.selected_mountpoint.get() not in [d.mountpoint for d in self.known_drives]:
                self.selected_mountpoint.set(self.known_drives[0].mountpoint)

            for drive in self.known_drives:
                rb = tk.Radiobutton(self.drives_frame, text=drive.device,
                                    variable=self.selected_mountpoint,
                                    value=drive.mountpoint)
                rb.pack(anchor="w")
        else:
            tk.Label(self.drives_frame, text="No USB drives detected").pack()
            self.selected_mountpoint.set("")

    def generate_keys(self):
        """
        Generate RSA key pair and save them to the selected USB drive.

        Encrypts the private key using the user's PIN.
        """
        pin = self.pin_entry.get()
        if not pin:
            messagebox.showwarning("Missing PIN", "Please enter your PIN")
            return

        key_gen = KeyGenerator()
        private_key, public_key = key_gen.generate_keys()
        encrypted_key = key_gen.encode_private_key(private_key, pin)
        self.save_keys(encrypted_key, public_key)

        self.pin_entry.delete(0, tk.END)
        self.pin_label.config(text="Keys generated and saved successfully")

    def save_keys(self, private_key, public_key):
        """
        Prompt user to select paths and save the private and public keys.

        :param private_key: The encrypted private key in bytes.
        :param public_key: The public key in PEM format.
        """
        if not self.selected_mountpoint.get():
            messagebox.showerror("No USB", "No USB selected")
            return
        
        usb_path = self.selected_mountpoint.get()
        
        try:
            unique_id = str(uuid.uuid4())
            private_key_filename = f"private_{unique_id}.key"
            private_key_path = os.path.join(usb_path, private_key_filename)

            with open(private_key_path, "wb") as f:
                f.write(private_key)
                
            key_list_path = os.path.join(usb_path, "key_list.txt")
            with open(key_list_path, "a") as f:
                f.write(f"{private_key_filename}\n")

            public_key_path = filedialog.asksaveasfilename(title="Public key path",
                                                        defaultextension=".pem",
                                                        filetypes=[("PEM files", "*.pem")])
            if public_key_path:
                with open(public_key_path, "wb") as f:
                    f.write(public_key)
                    
        except Exception as e:
            messagebox.showerror("Save Error", str(e))

    def decrypt_private_key(self, encrypted_data, pin):
        """
        Decrypt the private key using the provided PIN.

        :param encrypted_data: Encrypted key data read from file.
        :param pin: User's PIN as a string.
        :return: Decrypted private key in bytes.
        """
        salt = encrypted_data[:16]
        nonce = encrypted_data[16:28]
        ciphertext = encrypted_data[28:]

        kdf = Scrypt(salt=salt, length=32, n=2**14, r=8, p=1)
        key = kdf.derive(pin.encode())
        aesgcm = AESGCM(key)
        return aesgcm.decrypt(nonce, ciphertext, None)
    
    def sign_pdf(self):
        """
        Sign a selected PDF file using the private key stored on USB.

        Prompts the user for a PIN and file paths, then saves the signed PDF.
        """
        if not self.selected_mountpoint.get():
            messagebox.showerror("USB", "No USB drive selected.")
            return

        pin = simpledialog.askstring("PIN", "Enter your PIN:", show="*")
        if not pin:
            return

        pdf_path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if not pdf_path:
            return

        usb_path = self.selected_mountpoint.get()
        key_list_path = os.path.join(usb_path, "key_list.txt")

        if not os.path.exists(key_list_path):
            messagebox.showerror("Missing Keys", "No key_list.txt found on USB.")
            return

        try:
            with open(key_list_path, "r") as f:
                all_keys = [line.strip() for line in f if line.strip()]

            if not all_keys:
                raise FileNotFoundError("No private keys listed in key_list.txt")

            latest_key_filename = all_keys[-1] 
            key_path = os.path.join(usb_path, latest_key_filename)

            if not os.path.exists(key_path):
                raise FileNotFoundError(f"Private key file not found: {latest_key_filename}")

            with open(key_path, "rb") as f:
                encrypted_data = f.read()

            private_key_bytes = self.decrypt_private_key(encrypted_data, pin)

        except Exception as e:
            messagebox.showerror("Decryption Error", str(e))
            return

        output_path = sign_pdf(pdf_path, private_key_bytes)
        messagebox.showinfo("Success", f"PDF signed and saved to:\n{output_path}")

    def verify_signature(self):
        """
        Verify the digital signature of a selected PDF file.

        Uses a public key in PEM format.
        """
        pdf_path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if not pdf_path:
            return

        public_key_path = filedialog.askopenfilename(filetypes=[("PEM files", "*.pem")])
        if not public_key_path:
            return

        with open(public_key_path, "rb") as f:
            public_key_bytes = f.read()

        valid = verify_pdf_signature(pdf_path, public_key_bytes)
        if valid:
            messagebox.showinfo("Signature", "Signature is VALID")
        else:
            messagebox.showerror("Signature", "Signature is INVALID")


if __name__ == "__main__":
    window = tk.Tk()
    app = GUI(window)
    window.mainloop()
