# google-meet-avatar

Envía un avatar de [LemonSlice](https://www.lemonslice.com/) a una llamada de **Google Meet** usando [LiveKit Agents](https://docs.livekit.io/agents/).

El agente entra a la reunión como un participante bot con tu avatar en cámara, escucha el audio de la reunión y responde con voz y animación de baja latencia. Basado en el ejemplo `07-livekit-zoom` de [lemonslice-examples](https://github.com/LemonSlice-ai/lemonslice-examples) (el mismo `join_meeting` también soporta Zoom, Teams y Webex).

## Prerequisitos

- Python 3.10 a 3.12
- [uv](https://github.com/astral-sh/uv)
- [LiveKit CLI](https://docs.livekit.io/home/cli/) (`lk`) para despachar trabajos
- Claves de API de:
  - LiveKit (URL, API key y API secret)
  - LemonSlice
  - ElevenLabs

## Instalación

```bash
cd 11-google-meet-avatar
uv sync
```

## Configuración

1. Copia las variables de entorno:

   ```bash
   cp .env.example .env
   ```

2. Completa `.env`:

   ```env
   LEMONSLICE_API_KEY=tu_lemonslice_api_key
   LEMONSLICE_IMAGE_URL=https://ejemplo.com/tu-avatar.png
   LIVEKIT_API_KEY=tu_livekit_api_key
   LIVEKIT_API_SECRET=tu_livekit_api_secret
   LIVEKIT_URL=wss://tu-proyecto.livekit.cloud
   ELEVENLABS_VOICE_ID=tu_elevenlabs_voice_id
   ELEVEN_API_KEY=tu_elevenlabs_api_key
   ```

   `LEMONSLICE_IMAGE_URL` debe ser una URL pública de la imagen del avatar.

## Ejecutar el worker

Inicia el worker localmente (se registra con el nombre de agente `meet-bot`):

```bash
uv run python agent.py dev
```

## Unir el avatar a un Google Meet

Con el worker corriendo, crea un dispatch con el link de la reunión en el metadata:

```bash
lk dispatch create \
  --new-room \
  --agent-name meet-bot \
  --metadata '{"meeting_url":"https://meet.google.com/abc-defg-hij", "bot_name": "Mi Avatar", "listen_to_meeting_chat": true}'
```

- `meeting_url`: el link estándar del evento de calendario de Google Meet.
- `bot_name` (opcional): nombre visible del bot en la reunión.
- `listen_to_meeting_chat` (opcional, default `true`): reenvía los mensajes del chat de la reunión al agente.

**Nota:** el bot entra al lobby de Meet y un participante humano debe **admitirlo** manualmente.

## Stack del agente

Optimizado para tiempos de respuesta rápidos:

| Componente | Proveedor |
|-----------|-----------|
| STT | Deepgram Nova-2, español (vía LiveKit Inference) |
| LLM | Google Gemma 4 31B IT (`google/gemma-4-31b-it`, vía LiveKit Inference) |
| TTS | ElevenLabs `eleven_flash_v2_5` |
| Avatar | LemonSlice |

Para inglés, cambia `language="es"` a `"en"` en `agent.py` y ajusta las instrucciones del agente.

## Recursos

- [Guía oficial de LemonSlice para reuniones](https://lemonslice.com/docs/reference/zoom-meetings)
- [Documentación de LiveKit Agents](https://docs.livekit.io/agents/)
- [Integración LemonSlice + LiveKit](https://lemonslice.com/docs/livekit)
- [LiveKit agent dispatch](https://docs.livekit.io/agents/build/dispatch/)
