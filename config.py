import os
import sys
import requests
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

# Determinar la ruta base del ejecutable o script
if getattr(sys, 'frozen', False):  # Si está empaquetado como .exe
    base_path = os.path.dirname(sys.executable)
else:  # Si se ejecuta como script .py
    base_path = os.path.dirname(os.path.abspath(__file__))

# Rutas del proyecto
config_dir = os.path.join(base_path, "config")
sound_library_dir = os.path.join(base_path, "sounds")
os.makedirs(config_dir, exist_ok=True)
os.makedirs(sound_library_dir, exist_ok=True)

apis_file_path = os.path.join(config_dir, "apis.txt")
endpoint_file_path = os.path.join(config_dir, "endpoint.txt")

# Funciones de archivo
def read_file(file_path):
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as file:
            return [line.strip() for line in file if line.strip()]
    return []

def write_file(file_path, lines):
    with open(file_path, "w", encoding="utf-8") as file:
        file.write("\n".join(lines))

# Obtener créditos de una API key
def get_api_credits(api_key):
    url = "https://api.elevenlabs.io/v1/user/subscription"
    headers = {"xi-api-key": api_key}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        return data.get("character_count", 0)
    except requests.RequestException:
        return 0

 # Función para enmascarar claves API
def mask_api_key(api_key):
    if len(api_key) > 10:
        return api_key[:10] + '-' * (len(api_key) - 10)
    return api_key

# Aplicación principal
class ConfigApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Gestor de Configuración")
        self.geometry("500x400")
        self.resizable(False, False)

        # Inicializar pestañas
        self.tab_control = ttk.Notebook(self)
        self.api_tab = ttk.Frame(self.tab_control)
        self.voice_tab = ttk.Frame(self.tab_control)
        self.audio_tab = ttk.Frame(self.tab_control)

        self.tab_control.add(self.api_tab, text="APIs")
        self.tab_control.add(self.voice_tab, text="Voces")
        self.tab_control.add(self.audio_tab, text="Audios")
        self.tab_control.pack(expand=1, fill="both")

        # Crear interfaces
        self.create_api_tab()
        self.create_voice_tab()
        self.create_audio_tab()
        
    # --- API Management ---
    def create_api_tab(self):
        self.api_label = tk.Label(self.api_tab, text="Gestión de APIs", font=("Arial", 12))
        self.api_label.pack(pady=10)

        self.api_list = read_file(apis_file_path)
        self.api_status_label = tk.Label(self.api_tab, text="Total de APIs: 0 || Créditos Disponibles: Calculando...", font=("Arial", 10))
        self.api_status_label.pack()

        self.api_tree = ttk.Treeview(self.api_tab, columns=("API Key",), show="headings")
        self.api_tree.heading("API Key", text="Clave API")
        self.api_tree.pack(fill="both", expand=True, padx=20, pady=10)

        # Frame inferior para botones y textfield
        api_bottom_frame = tk.Frame(self.api_tab)
        api_bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=20, pady=10)

        # Crear textfield y añadir al frame
        self.api_entry = tk.Entry(api_bottom_frame, width=52)
        self.api_entry.pack(side=tk.LEFT, padx=5, pady=5)

        # Crear botones
        self.api_add_button = tk.Button(api_bottom_frame, text="Añadir", command=self.add_api)
        self.api_add_button.pack(side=tk.RIGHT, padx=5, pady=5)

        self.api_delete_button = tk.Button(api_bottom_frame, text="Eliminar", command=self.delete_selected_api)
        self.api_delete_button.pack(side=tk.RIGHT, padx=5, pady=5)

        self.update_idletasks()  # Asegurar que los widgets se rendericen

        self.update_api_tree()
        self.update_total_credits()

    def update_api_tree(self):
        for row in self.api_tree.get_children():
            self.api_tree.delete(row)
        for api in self.api_list:
            # Enmascarar clave API antes de mostrarla
            masked_key = mask_api_key(api)
            self.api_tree.insert("", "end", values=(masked_key,))
        self.update_total_credits()

        self.api_tree.column("API Key", anchor="center")
        self.update_total_credits()

    def add_api(self):
        api_key = self.api_entry.get().strip()
        if api_key and api_key not in self.api_list:
            self.api_list.append(api_key)
            write_file(apis_file_path, self.api_list)
            self.update_api_tree()
            self.api_entry.delete(0, tk.END)

    def delete_selected_api(self):
        selected_items = self.api_tree.selection()
        for item in selected_items:
            api_key = self.api_tree.item(item, "values")[0]
            self.api_list.remove(api_key)
        write_file(apis_file_path, self.api_list)
        self.update_api_tree()

    def update_total_credits(self):
        total_character_count = 0
        total_character_limit = 0

        for api_key in self.api_list:
            url = "https://api.elevenlabs.io/v1/user/subscription"
            headers = {"xi-api-key": api_key}
            try:
                response = requests.get(url, headers=headers)
                response.raise_for_status()
                data = response.json()
                total_character_count += data.get("character_count", 0)
                total_character_limit += data.get("character_limit", 0)
            except requests.RequestException:
                continue

        # Calcular el porcentaje de créditos usados
        if total_character_limit > 0:
            used_percentage = (total_character_count / total_character_limit) * 100
            available_percentage = 100 - used_percentage
        else:
            available_percentage = 0

        self.api_status_label.config(
            text=f"Total de APIs: {len(self.api_list)} || Créditos Disponibles: {available_percentage:.2f}%"
        )

    # --- Voice Management ---
    def create_voice_tab(self):
        self.voice_label = tk.Label(self.voice_tab, text="Gestión de Voces", font=("Arial", 12))
        self.voice_label.pack(pady=10)

        self.voice_list = {line.split("=")[0]: line.split("=")[1] for line in read_file(endpoint_file_path)}
        self.voice_total_label = tk.Label(self.voice_tab, text=f"Total de Voces: {len(self.voice_list)}", font=("Arial", 10))
        self.voice_total_label.pack()

        self.voice_tree = ttk.Treeview(self.voice_tab, columns=("Nombre", "ID"), show="headings")
        self.voice_tree.heading("Nombre", text="Nombre")
        self.voice_tree.heading("ID", text="ID")
        self.voice_tree.pack(fill="both", expand=True, padx=20, pady=10)

        # Frame inferior para botones y textfields
        voice_bottom_frame = tk.Frame(self.voice_tab)
        voice_bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=20, pady=10)

        # Crear textfields primero
        self.voice_name_entry = tk.Entry(voice_bottom_frame, width=15)
        self.voice_name_entry.pack(side=tk.LEFT, padx=5, pady=5)

        self.voice_id_entry = tk.Entry(voice_bottom_frame, width=35)
        self.voice_id_entry.pack(side=tk.LEFT, padx=5, pady=5)

        # Crear botones
        self.voice_add_button = tk.Button(voice_bottom_frame, text="Añadir", command=self.add_voice)
        self.voice_add_button.pack(side=tk.RIGHT, padx=5, pady=5)

        self.voice_delete_button = tk.Button(voice_bottom_frame, text="Eliminar", command=self.delete_selected_voice)
        self.voice_delete_button.pack(side=tk.RIGHT, padx=5, pady=5)

        # Alinear botones con textfields
        self.update_idletasks()
        entry_height = self.voice_name_entry.winfo_height()
        self.voice_add_button.config(height=1, pady=(entry_height - self.voice_add_button.winfo_reqheight()) // 2)
        self.voice_delete_button.config(height=1, pady=(entry_height - self.voice_delete_button.winfo_reqheight()) // 2)

        self.update_voice_tree()
    
    def update_voice_tree(self):
        for row in self.voice_tree.get_children():
            self.voice_tree.delete(row)
        for name, voice_id in self.voice_list.items():
            self.voice_tree.insert("", "end", values=(name, voice_id))
        self.voice_total_label.config(text=f"Total de Voces: {len(self.voice_list)}")

    def add_voice(self):
        name = self.voice_name_entry.get().strip()
        voice_id = self.voice_id_entry.get().strip()
        if name and voice_id and name not in self.voice_list:
            self.voice_list[name] = voice_id
            write_file(endpoint_file_path, [f"{k}={v}" for k, v in self.voice_list.items()])
            self.update_voice_tree()
            self.voice_name_entry.delete(0, tk.END)
            self.voice_id_entry.delete(0, tk.END)

    def delete_selected_voice(self):
        selected_items = self.voice_tree.selection()
        for item in selected_items:
            name = self.voice_tree.item(item, "values")[0]
            del self.voice_list[name]
        write_file(endpoint_file_path, [f"{k}={v}" for k, v in self.voice_list.items()])
        self.update_voice_tree()

    # --- Audio Management ---
    def create_audio_tab(self):
        self.audio_label = tk.Label(self.audio_tab, text="Gestión de Audios", font=("Arial", 12))
        self.audio_label.pack(pady=10)

        self.audio_files = [f for f in os.listdir(sound_library_dir) if f.endswith(".mp3")]
        self.audio_total_label = tk.Label(self.audio_tab, text=f"Total de Audios: {len(self.audio_files)}", font=("Arial", 10))
        self.audio_total_label.pack()

        self.audio_tree = ttk.Treeview(self.audio_tab, columns=("Archivo",), show="headings")
        self.audio_tree.heading("Archivo", text="Archivo")
        self.audio_tree.pack(fill="both", expand=True, padx=20, pady=10)

        # Frame inferior para botones
        audio_bottom_frame = tk.Frame(self.audio_tab)
        audio_bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=20, pady=10)

        # Crear botones
        self.audio_add_button = tk.Button(audio_bottom_frame, text="Añadir", command=self.add_audio)
        self.audio_add_button.pack(side=tk.RIGHT, padx=5, pady=5)

        self.audio_delete_button = tk.Button(audio_bottom_frame, text="Eliminar", command=self.delete_selected_audio)
        self.audio_delete_button.pack(side=tk.RIGHT, padx=5, pady=5)

        self.update_audio_tree()

    def update_audio_tree(self):
        for row in self.audio_tree.get_children():
            self.audio_tree.delete(row)
        for audio in self.audio_files:
            self.audio_tree.insert("", "end", values=(audio,))
        self.audio_total_label.config(text=f"Total de Audios: {len(self.audio_files)}")

    def add_audio(self):
        file_path = filedialog.askopenfilename(filetypes=[("Audio Files", "*.mp3")])
        if file_path:
            file_name = os.path.basename(file_path)
            dest_path = os.path.join(sound_library_dir, file_name)
            if not os.path.exists(dest_path):
                os.rename(file_path, dest_path)
                self.audio_files.append(file_name)
                self.update_audio_tree()

    def delete_selected_audio(self):
        selected_items = self.audio_tree.selection()
        for item in selected_items:
            file_name = self.audio_tree.item(item, "values")[0]
            file_path = os.path.join(sound_library_dir, file_name)
            if os.path.exists(file_path):
                os.remove(file_path)
                self.audio_files.remove(file_name)
        self.update_audio_tree()


# Ejecutar la aplicación
if __name__ == "__main__":
    app = ConfigApp()
    app.mainloop()
