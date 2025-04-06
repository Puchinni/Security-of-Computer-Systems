import tkinter as tk
from rsa_generator import KeyGenerator

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

    def generate_keys(self):
        pin = self.pin_entry.get()
        if len(pin) == 0:
            print("Enter PIN")
            return
        
        key_gen = KeyGenerator()
        private_key, public_key = key_gen.generate_keys()
        encrypted_key = key_gen.encode_private_key(private_key, pin)
        key_gen.save_keys(encrypted_key, public_key)
        
        self.pin_entry.delete(0, tk.END) 
        self.pin_label.config(text="Keys generated and saved successfully")
        
        
if __name__ == "__main__":
    window = tk.Tk()
    app = GUI(window)   
    window.mainloop()  