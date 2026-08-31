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
   | `LEMONSLICE_IMAGE_URL` | URL **pública** de la imagen del avatar. La del repo funciona: `https://raw.githubusercontent.com/jtmancilla/google-meet-avatar/main/assets/avatar_2.png` |
   | `LIVEKIT_URL` | [LiveKit Cloud](https://cloud.livekit.io) → tu proyecto → Settings → URL (`wss://...`) |
   | `LIVEKIT_API_KEY` | Mismo lugar → API Keys |
   | `LIVEKIT_API_SECRET` | Mismo lugar → API Keys |
   | `TTS_VOICE_ID` | (Opcional) ID de la voz (UUID). Explora voces en la [Cartesia Voice Library](https://cartesia.ai/voices) (deben ser voces *default*, no clonadas). Default: `9626c31c-bec5-4cca-baa8-f8ba9e84c8bc`. |

   Variables de comportamiento (opcionales, tienen defaults):

   | Variable | Qué hace |
   |---|---|
   | `AGENT_INSTRUCTIONS` | System prompt del agente. Si se define, reemplaza el default por completo. |
   | `AVATAR_NAME` | Nombre del avatar (la "wake-word"). Default: `Tony`. |
   | `AVATAR_GATE_ENABLED` | `true`/`false`. Activa el modo wake-word. Default: `true`. |
   | `AVATAR_ACTIVATION_WINDOW_S` | Segundos que sigue atento tras hablarle. Default: `30`. |
   | `AVATAR_CLOSING_PHRASES` | Frases de cierre separadas por comas (vuelve a silencio). |
   | `AVATAR_AMBIENT_MAX_TURNS` | Máximo de mensajes ambientales guardados como contexto. Default: `10`. |
   | `AVATAR_AMBIENT_LABEL` | Etiqueta de los mensajes ambientales. |

   STT, LLM y TTS van por **LiveKit Inference**, así que no necesitas cuentas de Deepgram, OpenAI ni Cartesia.

   El archivo debe quedar sin espacios ni comillas, algo así:

   ```env
   LEMONSLICE_API_KEY=sk_abc123
   LEMONSLICE_IMAGE_URL=https://raw.githubusercontent.com/jtmancilla/google-meet-avatar/main/assets/avatar_2.png
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
uv run python dispatch.py "https://meet.google.com/abc-defg-hij" --bot-name "Tony"
```

Opciones:

- `--bot-name "Nombre"` — nombre visible del bot en la reunión (default: `Mi Avatar`). Usa el mismo valor de `AVATAR_NAME` para que los participantes sepan cómo llamarlo.
- `--no-chat` — desactiva el reenvío de mensajes del chat de la reunión al agente (por defecto está activo).

## Paso 6 — Admitir al bot

El bot aparecerá en el **lobby** de Google Meet pidiendo entrar. Un participante humano debe **admitirlo** manualmente. Una vez admitido, el avatar **entra en silencio**: escucha la conversación y solo habla cuando alguien le dirige la palabra por su nombre (ver "Modo wake-word" más abajo).

## Detener el bot

Para terminar la sesión tienes dos opciones:

- **Desde Meet:** en el panel de participantes, quita al bot de la llamada (como expulsar a cualquier invitado).
- **Desde la terminal:** presiona `Ctrl+C` en la terminal donde corre `agent.py` (terminal 1). Esto detiene el worker por completo; si solo quieres sacar al bot de una reunión, usa la opción anterior.

## Modo wake-word (estilo Alexa)

Por defecto el bot **escucha todo pero solo habla cuando se le dirige la palabra**, usando su nombre como activador:

- **Activar:** dile algo como *"Oye Tony, ¿puedes ayudarnos?"* o *"Tony, ¿qué opinas?"*.
- **Ventana de atención:** después de hablarle, sigue atento `AVATAR_ACTIVATION_WINDOW_S` segundos (default 30) sin necesidad de repetir el nombre. Cada turno renueva la ventana.
- **Cerrar:** frases como *"gracias, eso era todo"* o *"ya puedes irte"* lo regresan a silencio de inmediato.
- **Contexto ambiental:** aunque esté en silencio, guarda lo que se dice en la reunión (etiquetado, máximo los últimos `AVATAR_AMBIENT_MAX_TURNS` turnos) para tener contexto cuando sí le hablen.

Para que responda a todo (comportamiento anterior), pon `AVATAR_GATE_ENABLED=false` en el `.env`.

## Personalizar el comportamiento (system prompt)

Las instrucciones del agente son 100% configurables por `AGENT_INSTRUCTIONS` en el `.env`, sin tocar código. El default es un asistente genérico en español consciente del modo wake-word.

Ejemplo de un rol con contexto propio:

```env
AGENT_INSTRUCTIONS=Eres Tony, asistente de voz en el cierre de un taller. Responde en español, máximo 2 oraciones. Si te piden palabras finales, agradece a los participantes...
```

---

## Problemas comunes

**El avatar entra y se mueve, pero no habla ni responde.**

Primero descarta lo esperado: en modo wake-word el bot **entra en silencio por diseño** — dile algo por su nombre (ej. *"Oye Tony, ¿me escuchas?"*). Si aun así no responde, revisa la terminal 1 (donde corre `agent.py`): los errores del pipeline aparecen ahí. Las causas más comunes son:

- `LIVEKIT_API_KEY` / `LIVEKIT_API_SECRET` de un proyecto distinto al de `LIVEKIT_URL` → el worker registra pero el dispatch no llega.
- La imagen no es una URL pública → LemonSlice no puede descargarla. Verifica abriéndola en una ventana de incógnito.
- `TTS_VOICE_ID` con un ID que no existe en Cartesia (los IDs de ElevenLabs no sirven) → error `voice does not exist` en los logs.
- LiveKit Inference no habilitado en tu proyecto → verifica en cloud.livekit.io → tu proyecto → Settings → Inference.

**`command not found: uv`** → cierra y vuelve a abrir la terminal después de instalar uv (o reinicia la sesión para que cargue el PATH).

**El bot se queda en el lobby** → alguien dentro de la reunión debe admitirlo; Meet no lo deja entrar solo.

## Tests

La lógica del wake-word tiene suite de tests (sin red ni servicios externos):

```bash
uv run pytest
```

## Stack del agente

Optimizado para tiempos de respuesta rápidos:

| Componente | Proveedor |
|-----------|-----------|
| STT | Deepgram Nova-2, español (vía LiveKit Inference) |
| LLM | Google Gemma 4 31B IT (`google/gemma-4-31b-it`, vía LiveKit Inference) |
| TTS | Cartesia Sonic 3 (vía LiveKit Inference) |
| Avatar | LemonSlice |

Para inglés, cambia `language="es"` a `"en"` en `agent.py` y ajusta las instrucciones del agente.

## Recursos

- [Guía oficial de LemonSlice para reuniones](https://lemonslice.com/docs/reference/zoom-meetings)
- [Documentación de LiveKit Agents](https://docs.livekit.io/agents/)
- [Integración LemonSlice + LiveKit](https://lemonslice.com/docs/livekit)
