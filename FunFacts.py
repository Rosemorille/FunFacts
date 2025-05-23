# -*- coding: utf-8 -*-
"""
Created on Fri May 23 15:15:31 2025

@author: rosem
"""
import socket
import threading
import json
import tkinter as tk
from tkinter import messagebox

# === Base de données JSON ===

DB_FILE = "users.json"  # Nom du fichier de stockage des utilisateurs


def load_users():
    """
    Charge les utilisateurs depuis le fichier JSON.
    Retourne un dictionnaire {username: password}.
    """
    try:
        with open(DB_FILE, "r") as f:
            return json.load(f)
    except:
        return {}  # Si le fichier n'existe pas ou est vide


def save_users(users):
    """
    saves the users in the JSON file.
    """
    with open(DB_FILE, "w") as f:
        json.dump(users, f)


# === Serveur (exécuté en arrière-plan) ===

def start_server():
    """
    launches the server which listens to client connexions (ready to recieve)
    and manages the connexion requests (login) and inscription (signup).
    """
    users = load_users()  # Chargement initial des utilisateurs

    def handle_client(conn):
        """
        Gère une connexion cliente : attend un message, le traite et renvoie une réponse.
        Format attendu : "commande:nom_utilisateur:mot_de_passe"
        """
        nonlocal users
        while True:
            try:
                data = conn.recv(1024).decode() #big message size 1024 in unicode in case we have a big message
                if not data:
                    break  # Déconnexion
                cmd, username, password = data.split(":")
                
                if cmd == "signup":
                    # Traitement de l'inscription
                    if username in users:
                        conn.send("Username already exists".encode())
                    else:
                        users[username] = password
                        save_users(users)
                        conn.send("Signup successful".encode())
                elif cmd == "login":
                    # Traitement de la connexion
                    if users.get(username) == password:
                        conn.send("Login successful".encode())
                    else:
                        conn.send("Invalid credentials".encode())
            except:
                break  # Erreur de communication ou client déconnecté
        conn.close()

    def run():
        """
        Lance le serveur TCP sur localhost:12345.
        Accepte plusieurs clients en parallèle via des threads.
        """
        s = socket.socket()
        s.bind(("localhost", 12345))  # Lien sur le port local 12345
        s.listen(5)  # Jusqu'à 5 connexions simultanées
        print("Server listening on port 12345...")
        while True:
            client, _ = s.accept()
            threading.Thread(target=handle_client, args=(client,)).start()

    threading.Thread(target=run, daemon=True).start()  # Lancer en tâche de fond


# === Interface Client (Tkinter) ===

class App:
    """
    Interface utilisateur avec Tkinter pour permettre la connexion ou l'inscription.
    """

    def __init__(self, root):
        self.root = root
        self.root.title("Login / Signup")
        
        self.root.attributes('-fullscreen', True) #pour avoir directement une fenêtre en full screen
        self.root.bind("<Escape>", lambda event: root.attributes('-fullscreen', False))

        # Connexion au serveur dès le démarrage
        self.sock = socket.socket()
        self.sock.connect(("localhost", 12345))

        # Création de l'interface graphique
        self.frame = tk.Frame(root)
        self.frame.pack(padx=10, pady=10)

        # Zone de texte pour le nom d'utilisateur
        tk.Label(self.frame, text="Username").grid(row=0, column=0)
        self.username = tk.Entry(self.frame)
        self.username.grid(row=0, column=1)

        # Zone de texte pour le mot de passe
        tk.Label(self.frame, text="Password").grid(row=1, column=0)
        self.password = tk.Entry(self.frame, show="*")
        self.password.grid(row=1, column=1)

        # Bouton de connexion
        self.login_btn = tk.Button(self.frame, text="Login", command=self.login)
        self.login_btn.grid(row=2, column=0)

        # Bouton d'inscription
        self.signup_btn = tk.Button(self.frame, text="Signup", command=self.signup)
        self.signup_btn.grid(row=2, column=1)

    def send_data(self, command):
        """
        Envoie une commande ('login' ou 'signup') au serveur avec le nom d'utilisateur et le mot de passe.
        Affiche ensuite la réponse reçue dans une popup.
        """
        user = self.username.get()
        pwd = self.password.get()
        msg = f"{command}:{user}:{pwd}"  # Format : "login:utilisateur:motdepasse"
        self.sock.send(msg.encode())
        response = self.sock.recv(1024).decode()
        messagebox.showinfo("Response", response)

    def login(self):
        """Lance une requête de connexion."""
        self.send_data("login")

    def signup(self):
        """Lance une requête d'inscription."""
        self.send_data("signup")


# === Lancement du programme principal ===

if __name__ == "__main__":
    start_server()  # Lancer le serveur en tâche de fond
    root = tk.Tk()  # Fenêtre principale Tkinter
    app = App(root)  # Lancer l'interface client
    root.mainloop()  # Démarrer la boucle Tkinter
