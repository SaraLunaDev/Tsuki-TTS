# Tsuki TTS

Sistema de text-to-speech con voces múltiples y efectos de audio.

## Instalación

```bash
git clone https://github.com/SaraLunaDev/Tsuki-TTS-.git
cd Tsuki-TTS-
pip install requests pygame
```

## Configuración

Crear archivos en `config/`:

**`apis.txt`** - API keys de ElevenLabs (una por línea):
```
tu_api_key_aqui
```

**`endpoint.txt`** - Voces disponibles:
```
2=Alba=voice_id_elevenlabs
13=Maria=google_es-ES-Standard-A
```

**`msg.txt`** - Mensaje a procesar:
```
(2:)Hola mundo(4)(13:)Esto es genial
```

**`volume.txt`** - Volumen (0.0 a 1.0):
```
0.5
```

## Uso

```bash
python main.py
```

**Formato de mensajes:**
- `(2:)texto` - Usar voz ID 2
- `(4)` - Reproducir sonido 4

## Requisitos

- Python 3.7+
- API keys de ElevenLabs y/o Google TTS