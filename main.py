import os
import requests
import pygame
import re
import traceback
import base64
from datetime import datetime

# Ruta base del script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Rutas de las carpetas
config_dir = os.path.join(script_dir, "config")
temp_dir = os.path.join(script_dir, "temp")
logs_dir = os.path.join(script_dir, "logs")
sound_library_path = os.path.join(script_dir, "sounds")

# Crear las carpetas necesarias
os.makedirs(temp_dir, exist_ok=True)
os.makedirs(logs_dir, exist_ok=True)

# Rutas de los archivos dentro de la carpeta `config`
apis_file_path = os.path.join(config_dir, "apis.txt")
endpoint_file_path = os.path.join(config_dir, "endpoint.txt")
text_file_path = os.path.join(config_dir, "msg.txt")
volume_file_path = os.path.join(config_dir, "volume.txt")
error_log_path = os.path.join(config_dir, "errores.txt")

# Inicializa el archivo de errores limpio
with open(error_log_path, "w", encoding="utf-8") as error_file:
    error_file.write("")

def clean_old_logs(logs_dir, max_logs=10):
    """Mantener solo los más recientes max_logs archivos en la carpeta logs."""
    log_files = [os.path.join(logs_dir, f) for f in os.listdir(logs_dir) if f.startswith("log_") and f.endswith(".txt")]
    log_files.sort(key=os.path.getmtime, reverse=True)
    if len(log_files) > max_logs:
        old_logs = log_files[max_logs:]
        for old_log in old_logs:
            os.remove(old_log)

# Crear un archivo de log diario
today = datetime.now().strftime("%Y-%m-%d")
log_file_path = os.path.join(logs_dir, f"log_{today}.txt")

def log_message(message):
    """Registrar un mensaje en el archivo de log diario con la hora exacta."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file_path, "a", encoding="utf-8") as log_file:
        log_file.write(f"[{timestamp}] {message}\n")

def clean_temp_folder(temp_dir):
    """Elimina todos los archivos de la carpeta temporal."""
    if os.path.exists(temp_dir):
        for file in os.listdir(temp_dir):
            file_path = os.path.join(temp_dir, file)
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    log_message(f"Archivo temporal eliminado: {file_path}")
            except Exception as e:
                log_message(f"Error al eliminar archivo temporal '{file_path}': {str(e)}")

# Limpieza inicial
clean_temp_folder(temp_dir)
clean_old_logs(logs_dir)



try:
    log_message("Inicio de ejecución del programa.")

    # Cargar las claves de API
    if os.path.exists(apis_file_path):
        with open(apis_file_path, "r", encoding="utf-8") as file:
            api_keys = [line.strip() for line in file if line.strip()]
        log_message(f"Se cargaron {len(api_keys)} claves API.")
    else:
        raise FileNotFoundError(f"No se encontró '{apis_file_path}'.")

    # Cargar las voces desde el archivo de endpoints
    voices_by_id = {}
    voices_by_name = {}

    if os.path.exists(endpoint_file_path):
        with open(endpoint_file_path, "r", encoding="utf-8") as file:
            for line in file:
                line = line.strip()
                if "=" in line:
                    parts = line.split("=")
                    if len(parts) == 3:
                        voice_id, voice_name, voice_identifiers = parts
                        identifiers_list = voice_identifiers.split(",")  # Separar los identificadores por comas
                        voices_by_id[voice_id] = {"name": voice_name, "identifiers": identifiers_list}
                        voices_by_name[voice_name] = {"id": voice_id, "identifiers": identifiers_list}
                    else:
                        log_message(f"Línea malformada en '{endpoint_file_path}': {line}")
    else:
        raise FileNotFoundError(f"No se encontró '{endpoint_file_path}'.")
    log_message(f"Se cargaron {len(voices_by_id)} voces desde '{endpoint_file_path}'.")

    # Verificar que haya al menos una voz cargada
    if not voices_by_id:
        raise ValueError("No se encontró ninguna voz en el archivo 'endpoint.txt'.")

    # Cargar sonidos
    sounds = {}
    for file_name in os.listdir(sound_library_path):
        if file_name.endswith(".mp3"):
            parts = file_name.split("_", 1)
            if len(parts) == 2 and parts[0].isdigit():
                sound_id = parts[0]
                sound_name = parts[1].replace(".mp3", "")
                sounds[sound_id] = {"id": sound_id, "name": sound_name, "file": os.path.join(sound_library_path, file_name)}
                sounds[sound_name] = {"id": sound_id, "name": sound_name, "file": os.path.join(sound_library_path, file_name)}
    log_message(f"Se cargaron {len(sounds)} sonidos desde la carpeta de sonidos.")

    # Cargar el volumen
    if os.path.exists(volume_file_path):
        with open(volume_file_path, "r", encoding="utf-8") as file:
            volume = float(file.read().strip())
            volume = max(0.0, min(1.0, volume))
        log_message(f"Volumen configurado a {volume:.2f}.")
    else:
        volume = 0.5
        log_message("No se encontró el archivo de volumen. Usando volumen predeterminado (0.5).")

    def procesar_mensaje(texto, voz_predeterminada="(2:)"):
        """
        Procesa el mensaje para añadir:
        - Una voz predeterminada al inicio si no existe.
        - Una voz después de cada sonido si no hay texto que ya tenga una voz explícita.
        """
        # Añadir voz predeterminada al inicio si no existe
        if not re.match(r"^\(\d+:\)", texto):
            texto = f"{voz_predeterminada} {texto}"

        # Procesar segmentos del texto
        segments = re.findall(r"(\([^:()\n]+:\))|(\(\d+\))|([^\(\)]+)", texto)
        procesado = ""
        ultima_voz = voz_predeterminada

        for segment in segments:
            if segment[0]:  # Identificador de voz
                ultima_voz = segment[0]
                procesado += ultima_voz
            elif segment[1]:  # Sonido
                procesado += segment[1]
                if ultima_voz:  # Añadir la última voz después del sonido
                    procesado += ultima_voz
            elif segment[2]:  # Texto simple
                procesado += segment[2]

        return procesado


    if os.path.exists(text_file_path):
        with open(text_file_path, "r", encoding="utf-8") as file:
            texto_original = file.read().strip()
        log_message("Se cargó el mensaje de texto.")

        # Procesar el mensaje con voz predeterminada
        texto_procesado = procesar_mensaje(texto_original, voz_predeterminada="(2:)")
        with open(text_file_path, "w", encoding="utf-8") as file:
            file.write(texto_procesado)
        log_message("Se procesó el mensaje de texto para añadir voz predeterminada donde no había.")
    else:
        raise FileNotFoundError(f"No se encontró '{text_file_path}'.")
        
    segments = re.findall(r"\((\d+):\)([^(\n]+)|\(([^:()\n]+):\)([^(\n]+)|\((\d+)\)|\(([^:()\n]+)\)", texto_procesado)

    def buscar_voz(voice_identifier):
        return voices_by_id.get(voice_identifier) or voices_by_name.get(voice_identifier)

    def buscar_sonido(sound_identifier):
        return sounds.get(sound_identifier, {}).get("file")

    def generar_audio_mixto(api_keys, voice_identifiers, text, file_name, google_api_key):
        """
        Intenta generar audio usando múltiples identificadores, mezclando ElevenLabs y Google.
        """
        elevenlabs_identifiers = [vid for vid in voice_identifiers if not vid.startswith("google_")]
        google_identifiers = [vid for vid in voice_identifiers if vid.startswith("google_")]

        # Intentar con ElevenLabs
        for voice_id in elevenlabs_identifiers:
            for i, api_key in enumerate(api_keys):
                headers = {"xi-api-key": api_key, "Content-Type": "application/json"}
                payload = {"text": text.strip(), "model_id": "eleven_multilingual_v2", "voice_settings": {"stability": 0.5, "similarity_boost": 0.75, "style": 0.1, "use_speaker_boost": True}}
                url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
                response = requests.post(url, json=payload, headers=headers)
                if response.status_code == 200:
                    with open(file_name, "wb") as audio_file:
                        audio_file.write(response.content)
                    log_message(f"Audio generado con ElevenLabs usando identificador '{voice_id}'.")
                    return True
                elif response.status_code == 429:  # Límite alcanzado
                    log_message(f"Límite alcanzado para la API key {api_key[:10]}****. Moviendo al final de la lista.")
                    api_keys.append(api_keys.pop(i))  # Mover la clave al final
                else:
                    log_message(f"Error al usar identificador '{voice_id}': {response.status_code} - {response.text}")

        # Intentar con Google TTS
        for voice_id in google_identifiers:
            google_voice_name = voice_id.replace("google_", "")
            url = f"https://texttospeech.googleapis.com/v1/text:synthesize?key={google_api_key}"
            headers = {"Content-Type": "application/json"}
            payload = {
                "input": {"text": text.strip()},
                "voice": {"languageCode": "es-ES", "name": google_voice_name},
                "audioConfig": {"audioEncoding": "MP3"}
            }
            response = requests.post(url, json=payload, headers=headers)
            if response.status_code == 200:
                audio_content = response.json().get("audioContent")
                if audio_content:
                    with open(file_name, "wb") as audio_file:
                        audio_file.write(base64.b64decode(audio_content))
                    log_message(f"Audio generado con Google TTS usando identificador '{google_voice_name}'.")
                    return True
            else:
                log_message(f"Error al usar Google TTS '{google_voice_name}': {response.status_code} - {response.text}")

        log_message(f"No se pudo generar audio usando los identificadores: {voice_identifiers}")
        return False

    audio_files = []

    if not segments:  # Si no hay segmentos encontrados, usar voz predeterminada
        log_message("No se encontraron voces en el mensaje. Usando la voz predeterminada (ID 2 - Alba).")
        default_voice_id = "2"
        default_voice_data = voices_by_id.get(default_voice_id)
        if not default_voice_data:
            raise ValueError("La voz predeterminada (ID 2 - Alba) no está definida en el archivo 'endpoint.txt'.")
        default_voice_identifier = default_voice_data["identifier"]
        file_name = os.path.join(temp_dir, "default_audio.mp3")
        if default_voice_identifier.startswith("google_"):
            google_voice_name = default_voice_identifier.replace("google_", "")
            if not generar_audio_google("AIzaSyBwtrjL4pxiNAxqP0ebe8wd4f1pXr6Sido", google_voice_name, texto, file_name):
                raise RuntimeError("No se pudo generar audio con la voz predeterminada (Google TTS).")
        else:
            if not generar_audio(api_keys, default_voice_identifier, texto, file_name):
                raise RuntimeError("No se pudo generar audio con la voz predeterminada (ElevenLabs).")
        audio_files.append(file_name)

    else:  # Procesar segmentos normalmente
        for i, segment in enumerate(segments):
            if segment[4] or segment[5]:  # Sonido por ID o nombre
                sound_identifier = segment[4] or segment[5]
                sound_file = buscar_sonido(sound_identifier)
                if sound_file:
                    audio_files.append(sound_file)
            elif segment[0] or segment[2]:  # Voz por ID o por nombre
                voice_identifier = segment[0] or segment[2]
                text = segment[1] or segment[3]
                voice_data = buscar_voz(voice_identifier)
                if not voice_data:
                    raise ValueError(f"Voz '{voice_identifier}' no encontrada.")
                voice_identifiers = voice_data["identifiers"]
                file_name = os.path.join(temp_dir, f"audio_{i}.mp3")
                if generar_audio_mixto(api_keys, voice_identifiers, text, file_name, "AIzaSyBwtrjL4pxiNAxqP0ebe8wd4f1pXr6Sido"):
                    audio_files.append(file_name)

    # Reproducción de audios
    pygame.mixer.init()
    for file in audio_files:
        pygame.mixer.music.load(file)
        pygame.mixer.music.set_volume(volume)
        pygame.mixer.music.play()
        log_message(f"Reproduciendo archivo de audio: {file}")
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)

    log_message("Ejecución completada exitosamente.")

except Exception as e:
    error_message = traceback.format_exc()
    with open(error_log_path, "w", encoding="utf-8") as error_file:
        error_file.write("Ha ocurrido un error:\n")
        error_file.write(error_message)
    log_message(f"Error ocurrido: {error_message}")
    print(f"Error. Consulta '{error_log_path}' para más detalles.")
