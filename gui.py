import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox
from rsa_generator import KeyGenerator
from usb_watch import *
from pdf import *
from verify_pdf import *
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

class GUI:
    def __init__(self, window):
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
        self.known_drives, updated, _ = get_usb_update(self.known_drives)
        if updated:
            self.update_drive_buttons()
        self.window.after(self.polling_delay, self.poll_usb_drives)

    def update_drive_buttons(self):
        for widget in self.drives_frame.winfo_children():
            widget.destroy()

        if self.known_drives:
            # Selecting the first mountpoint if none is selected
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
        if not self.selected_mountpoint.get():
            messagebox.showerror("No USB", "No USB selected")
            return

        private_key_path = filedialog.asksaveasfilename(title="Private key path",
                                                        defaultextension=".key",
                                                        filetypes=[("KEY files", "*.key")],
                                                        initialdir=self.selected_mountpoint.get())

        if private_key_path:
            with open(private_key_path, "wb") as f:
                f.write(private_key)

        public_key_path = filedialog.asksaveasfilename(title="Public key path",
                                                       defaultextension=".pem",
                                                       filetypes=[("PEM files", "*.pem")])
        if public_key_path:
            with open(public_key_path, "wb") as f:
                f.write(public_key)

    def decrypt_private_key(self, encrypted_data, pin):
        salt = encrypted_data[:16]
        nonce = encrypted_data[16:28]
        ciphertext = encrypted_data[28:]

        kdf = Scrypt(salt=salt, length=32, n=2**14, r=8, p=1)
        key = kdf.derive(pin.encode())
        aesgcm = AESGCM(key)
        return aesgcm.decrypt(nonce, ciphertext, None)

    def sign_pdf(self):
        if not self.selected_mountpoint.get():
            messagebox.showerror("USB", "No USB drive selected.")
            return

        pin = simpledialog.askstring("PIN", "Enter your PIN:", show="*")
        if not pin:
            return

        pdf_path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if not pdf_path:
            return

        key_path = filedialog.askopenfilename(title="Select Encrypted Private Key",
                                              initialdir=self.selected_mountpoint.get(),
                                              filetypes=[("KEY files", "*.key")])
        if not key_path:
            return

        try:
            with open(key_path, "rb") as f:
                encrypted_data = f.read()

            private_key_bytes = self.decrypt_private_key(encrypted_data, pin)
        except Exception as e:
            messagebox.showerror("Decryption Error", str(e))
            return

        output_path = sign_pdf(pdf_path, private_key_bytes)
        messagebox.showinfo("Success", f"PDF signed and saved to:\n{output_path}")

    def verify_signature(self):
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