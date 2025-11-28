"""Encrypted Notes Vault with Tkinter GUI.

A secure notes application that encrypts notes using Fernet symmetric
encryption with a password-derived key (PBKDF2). Notes are stored
encrypted in a JSON file and can only be accessed with the master password.

Features:
- Master password protection
- AES encryption via Fernet
- PBKDF2 key derivation with SHA256
- Simple Tkinter-based GUI
"""
import tkinter as tk
from tkinter import messagebox, simpledialog, scrolledtext
import json
import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

DATA_FILE = "vault.json"


class Security:
    """Utility class for encryption/decryption operations."""

    @staticmethod
    def derive_key(password: str, salt: bytes) -> bytes:
        """Derive an encryption key from a password using PBKDF2.

        Args:
            password: The master password.
            salt: Random salt bytes.

        Returns:
            bytes: URL-safe base64-encoded Fernet key.
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        return base64.urlsafe_b64encode(kdf.derive(password.encode()))

    @staticmethod
    def encrypt(data: dict, password: str) -> dict:
        """Encrypt data using Fernet symmetric encryption.

        Args:
            data: Dictionary to encrypt.
            password: Master password for key derivation.

        Returns:
            dict: Contains base64-encoded salt and encrypted data.
        """
        salt = os.urandom(16)
        key = Security.derive_key(password, salt)
        f = Fernet(key)
        json_data = json.dumps(data).encode()
        token = f.encrypt(json_data)
        return {
            "salt": base64.b64encode(salt).decode(),
            "data": base64.b64encode(token).decode()
        }

    @staticmethod
    def decrypt(encrypted_store: dict, password: str) -> dict:
        """Decrypt data encrypted by the encrypt method.

        Args:
            encrypted_store: Dictionary with salt and encrypted data.
            password: Master password for key derivation.

        Returns:
            dict: Decrypted data, or None if decryption fails.
        """
        salt = base64.b64decode(encrypted_store["salt"])
        token = base64.b64decode(encrypted_store["data"])
        key = Security.derive_key(password, salt)
        f = Fernet(key)
        try:
            decrypted_data = f.decrypt(token)
            return json.loads(decrypted_data.decode())
        except Exception:
            return None

class VaultApp:
    """Main application class for the encrypted notes vault GUI."""

    def __init__(self, root):
        """Initialize the vault application.

        Args:
            root: Tkinter root window.
        """
        self.root = root
        self.root.title("Encrypted Notes Vault")
        self.root.geometry("600x400")
        
        self.notes = []
        self.password = None
        
        self.check_vault()

    def check_vault(self):
        """
        Docstring for check_vault.
        """
        if os.path.exists(DATA_FILE):
            self.login_screen()
        else:
            self.setup_screen()

    def setup_screen(self):
        """
        Docstring for setup_screen.
        """
        self.clear_screen()
        tk.Label(self.root, text="Create Master Password", font=("Arial", 16)).pack(pady=20)
        
        self.pwd_entry = tk.Entry(self.root, show="*", width=30)
        self.pwd_entry.pack(pady=10)
        
        tk.Button(self.root, text="Create Vault", command=self.create_vault).pack(pady=10)

    def create_vault(self):
        """
        Docstring for create_vault.
        """
        pwd = self.pwd_entry.get()
        if not pwd:
            messagebox.showerror("Error", "Password cannot be empty")
            return
        
        self.password = pwd
        self.notes = []
        self.save_vault()
        self.main_screen()

    def login_screen(self):
        """
        Docstring for login_screen.
        """
        self.clear_screen()
        tk.Label(self.root, text="Enter Master Password", font=("Arial", 16)).pack(pady=20)
        
        self.pwd_entry = tk.Entry(self.root, show="*", width=30)
        self.pwd_entry.pack(pady=10)
        self.pwd_entry.bind('<Return>', lambda e: self.login())
        
        tk.Button(self.root, text="Unlock", command=self.login).pack(pady=10)

    def login(self):
        """
        Docstring for login.
        """
        pwd = self.pwd_entry.get()
        try:
            with open(DATA_FILE, 'r') as f:
                encrypted_store = json.load(f)
            
            decrypted_notes = Security.decrypt(encrypted_store, pwd)
            
            if decrypted_notes is not None:
                self.password = pwd
                self.notes = decrypted_notes
                self.main_screen()
            else:
                messagebox.showerror("Error", "Invalid Password")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load vault: {e}")

    def save_vault(self):
        """
        Docstring for save_vault.
        """
        if self.password:
            encrypted_store = Security.encrypt(self.notes, self.password)
            with open(DATA_FILE, 'w') as f:
                json.dump(encrypted_store, f)

    def main_screen(self):
        """
        Docstring for main_screen.
        """
        self.clear_screen()
        
        frame = tk.Frame(self.root)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.listbox = tk.Listbox(frame)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = tk.Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.listbox.yview)
        
        self.listbox.bind('<Double-1>', self.view_note)
        
        self.refresh_list()
        
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Button(btn_frame, text="New Note", command=self.new_note).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Delete Note", command=self.delete_note).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Lock Vault", command=self.login_screen).pack(side=tk.RIGHT, padx=5)

    def refresh_list(self):
        """
        Docstring for refresh_list.
        """
        self.listbox.delete(0, tk.END)
        for note in self.notes:
            self.listbox.insert(tk.END, note['title'])

    def new_note(self):
        """
        Docstring for new_note.
        """
        self.note_editor(None)

    def view_note(self, event):
        """
        Docstring for view_note.
        """
        selection = self.listbox.curselection()
        if selection:
            index = selection[0]
            self.note_editor(index)

    def delete_note(self):
        """
        Docstring for delete_note.
        """
        selection = self.listbox.curselection()
        if selection:
            index = selection[0]
            del self.notes[index]
            self.save_vault()
            self.refresh_list()

    def note_editor(self, index):
        """
        Docstring for note_editor.
        """
        editor = tk.Toplevel(self.root)
        editor.title("Edit Note" if index is not None else "New Note")
        editor.geometry("400x300")
        
        tk.Label(editor, text="Title:").pack(pady=5)
        title_entry = tk.Entry(editor, width=40)
        title_entry.pack(pady=5)
        
        tk.Label(editor, text="Content:").pack(pady=5)
        content_text = scrolledtext.ScrolledText(editor, width=40, height=10)
        content_text.pack(pady=5)
        
        if index is not None:
            note = self.notes[index]
            title_entry.insert(0, note['title'])
            content_text.insert(tk.END, note['content'])
            
        def save():
            """
            Docstring for save.
            """
            title = title_entry.get()
            content = content_text.get("1.0", tk.END).strip()
            
            if not title:
                messagebox.showwarning("Warning", "Title is required")
                return
                
            note_data = {'title': title, 'content': content}
            
            if index is not None:
                self.notes[index] = note_data
            else:
                self.notes.append(note_data)
                
            self.save_vault()
            self.refresh_list()
            editor.destroy()
            
        tk.Button(editor, text="Save", command=save).pack(pady=10)

    def clear_screen(self):
        """
        Docstring for clear_screen.
        """
        for widget in self.root.winfo_children():
            widget.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = VaultApp(root)
    root.mainloop()
