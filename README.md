# google-meet-avatar

Envía un avatar de [LemonSlice](https://www.lemonslice.com/) a una llamada de **Google Meet** usando [LiveKit Agents](https://docs.livekit.io/agents/).

El agente entra a la reunión como un participante bot con tu avatar en cámara, escucha el audio de la reunión y responde con voz y animación de baja latencia. Basado en el ejemplo `07-livekit-zoom` de [lemonslice-examples](https://github.com/LemonSlice-ai/lemonslice-examples) (el mismo `join_meeting` también soporta Zoom, Teams y Webex).

## Paso 1 — Clonar el proyecto

```bash
git clone https://github.com/jtmancilla/google-meet-avatar.git
cd google-meet-avatar
```

Todos los comandos siguientes se ejecutan **dentro de esta carpeta**.

## Paso 2 — Instalar dependencias

Necesitas [uv](https://github.com/astral-sh/uv) (gestor de paquetes de Python). Si no lo tienes:

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Luego instala las dependencias del proyecto (crea el entorno virtual solo):

```bash
uv sync
```

## Paso 3 — Configurar las claves

1. Copia la plantilla de variables de entorno:

   ```bash
   cp .env.example .env
   ```

2. Abre el archivo `.env` con cualquier editor y completa cada valor:

   | Variable | Dónde se obtiene |
   |---|---|
   | `LEMONSLICE_API_KEY` | [Portal de LemonSlice](https://lemonslice.com) → API Keys |
   | `LEMONSLICE_IMAGE_URL` | URL **pública** de la imagen del avatar. La del repo funciona: `https://raw.githubusercontent.com/jtmancilla/google-meet-avatar/main/assets/avatar.png` |
   | `LIVEKIT_URL` | [LiveKit Cloud](https://cloud.livekit.io) → tu proyecto → Settings → URL (`wss://...`) |
   | `LIVEKIT_API_KEY` | Mismo lugar → API Keys |
   | `LIVEKIT_API_SECRET` | Mismo lugar → API Keys |
| `TTS_VOICE_ID` | (Opcional) ID de la voz. Debe ser una voz **default** de ElevenLabs (las custom/de comunidad no funcionan vía LiveKit Inference). Default: `cgSgspJ2msm6clMCkdW9` (Sarah). Prueba IDs en la [ElevenLabs Voice Library](https://elevenlabs.io/voice-library). |

   STT, LLM y TTS van por **LiveKit Inference**, así que no necesitas cuentas de Deepgram, OpenAI ni ElevenLabs.

   El archivo debe quedar sin espacios ni comillas, algo así:

   ```env
   LEMONSLICE_API_KEY=sk_abc123
   LEMONSLICE_IMAGE_URL=https://raw.githubusercontent.com/jtmancilla/google-meet-avatar/main/assets/avatar.png
   LIVEKIT_URL=wss://mi-proyecto.livekit.cloud
   LIVEKIT_API_KEY=APIxxxx
   LIVEKIT_API_SECRET=secretxxxx
   ```

## Paso 4 — Encender el agente (terminal 1)

```bash
uv run python agent.py dev
```

Déjalo corriendo. Debes ver un mensaje indicando que el worker se registró como `meet-bot`. **No cierres esta terminal.**

## Paso 5 — Enviar el avatar a la reunión (terminal 2)

Abre una **segunda terminal**, entra a la misma carpeta y ejecuta el dispatch con el link de tu reunión de Google Meet:

```bash
cd google-meet-avatar
uv run python dispatch.py "https://meet.google.com/abc-defg-hij" --bot-name "Mi Avatar"
```

Opciones:

- `--bot-name "Nombre"` — nombre visible del bot en la reunión (default: `Mi Avatar`).
- `--no-chat` — desactiva el reenvío de mensajes del chat de la reunión al agente (por defecto está activo).

## Paso 6 — Admitir al bot

El bot aparecerá en el **lobby** de Google Meet pidiendo entrar. Un participante humano debe **admitirlo** manualmente. Una vez admitido, el avatar se presenta solo y ya puedes hablarle.

## Detener el bot

Para terminar la sesión tienes dos opciones:

- **Desde Meet:** en el panel de participantes, quita al bot de la llamada (como expulsar a cualquier invitado).
- **Desde la terminal:** presiona `Ctrl+C` en la terminal donde corre `agent.py` (terminal 1). Esto detiene el worker por completo; si solo quieres sacar al bot de una reunión, usa la opción anterior.

---

## Problemas comunes

**El avatar entra y se mueve, pero no habla ni responde.**

Revisa la terminal 1 (donde corre `agent.py`): los errores del pipeline aparecen ahí. Las causas más comunes son:

- `LIVEKIT_API_KEY` / `LIVEKIT_API_SECRET` de un proyecto distinto al de `LIVEKIT_URL` → el worker registra pero el dispatch no llega.
- La imagen no es una URL pública → LemonSlice no puede descargarla. Verifica abriéndola en una ventana de incógnito.
- LiveKit Inference no habilitado en tu proyecto → verifica en cloud.livekit.io → tu proyecto → Settings → Inference.

**`command not found: uv`** → cierra y vuelve a abrir la terminal después de instalar uv (o reinicia la sesión para que cargue el PATH).

**El bot se queda en el lobby** → alguien dentro de la reunión debe admitirlo; Meet no lo deja entrar solo.

## Stack del agente

Optimizado para tiempos de respuesta rápidos:

| Componente | Proveedor |
|-----------|-----------|
| STT | Deepgram Nova-2, español (vía LiveKit Inference) |
| LLM | Google Gemma 4 31B IT (`google/gemma-4-31b-it`, vía LiveKit Inference) |
| TTS | ElevenLabs Flash v2.5 (vía LiveKit Inference) |
| Avatar | LemonSlice |

Para inglés, cambia `language="es"` a `"en"` en `agent.py` y ajusta las instrucciones del agente.

## Recursos

- [Guía oficial de LemonSlice para reuniones](https://lemonslice.com/docs/reference/zoom-meetings)
- [Documentación de LiveKit Agents](https://docs.livekit.io/agents/)
- [Integración LemonSlice + LiveKit](https://lemonslice.com/docs/livekit)
