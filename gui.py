import tkinter as tk
from tkinter import filedialog
from rsa_generator import KeyGenerator
from usb_watch import *

class GUI:
    def __init__(self, window):
        self.window = window
        window.title("RSA generator")
        window.geometry("600x500")
        self.pin_label = tk.Label(self.window, text="Enter your PIN")
        self.pin_label.pack()
        
        self.pin_entry = tk.Entry(window, show="*")
        self.pin_entry.pack()

        self.generate_button = tk.Button(window, text="Generate RSA keys", command=self.generate_keys)
        self.generate_button.pack()

        self.drives_label = tk.Label(self.window, text="Detected USB drives:")
        self.drives_label.pack()

        self.drives_frame = tk.Frame(self.window)
        self.drives_frame.pack(pady=10)

        self.polling_delay = 2000
        self.known_drives = []
        self.selected_mountpoint = tk.StringVar()

        self.poll_usb_drives()
        self.update_drive_buttons()

    def poll_usb_drives(self):
        self.known_drives, updated, _ = get_usb_update(self.known_drives)
        if updated:
            self.update_drive_buttons()
        self.window.after(self.polling_delay, self.poll_usb_drives)

    def update_drive_buttons(self):
        # Clear existing radiobuttons
        for widget in self.drives_frame.winfo_children():
            widget.destroy()

        # Create new radiobuttons for each drive
        for drive in self.known_drives:
            rb = tk.Radiobutton(
                self.drives_frame,
                text=drive.device,
                variable=self.selected_mountpoint,
                value=drive.mountpoint,

            )
            rb.pack(anchor="w")

        # If no drives, show a message
        if not self.known_drives:
            tk.Label(self.drives_frame, text="No USB drives detected").pack()


    def save_keys(self, private_key, public_key):
        print(self.selected_mountpoint.get())
        private_key_path = filedialog.asksaveasfilename(title="Private key path", defaultextension=".key",
                                                        filetypes=[("KEY files", "*.key")],
                                                        initialdir=self.selected_mountpoint.get(),)

        with open(private_key_path, "wb") as f:
            f.write(private_key)

        public_key_path = filedialog.asksaveasfilename(title="Public key path", defaultextension=".pem",
                                                       filetypes=[("PEM files", "*.pem")])
        with open(public_key_path, "wb") as f:
            f.write(public_key)


    def generate_keys(self):
        pin = self.pin_entry.get()
        if len(pin) == 0:
            print("Enter PIN")
            return
        
        key_gen = KeyGenerator()
        private_key, public_key = key_gen.generate_keys()
        encrypted_key = key_gen.encode_private_key(private_key, pin)
        self.save_keys(encrypted_key, public_key)
        
        self.pin_entry.delete(0, tk.END) 
        self.pin_label.config(text="Keys generated and saved successfully")
        
        
if __name__ == "__main__":
    window = tk.Tk()
    app = GUI(window)   
    window.mainloop()  