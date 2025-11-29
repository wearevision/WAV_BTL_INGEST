# WAV BTL INGEST

Pipeline para automatizar la ingesta de eventos BTL: análisis visual con Gemini, generación textual con GPT-4o, procesamiento de media y entrega final a Supabase.

## Módulos principales
- `pipeline/classifier_gemini.py`: clasificador visual (Gemini Vision) que devuelve metadatos estructurados.
- `pipeline/text_generator.py`: genera todos los campos del objeto `WavEvent` con GPT-4o o Gemini (JSON estricto, `needs_review`).
- `pipeline/supabase_payload.py`: serializa `WavEvent` + media (`cover`, `logo`, `gallery`) en el payload listo para POST `/events`.
- (próximos) `media_processor.py`, `video_processor.py`, `orchestrator.py`: procesado de imágenes/videos y flujo E2E.

## Requisitos
- Python 3.11+ recomendado
- ffmpeg instalado en el sistema (para los módulos de video/media)
- Variables de entorno: `GEMINI_API_KEY`, `OPENAI_API_KEY`, `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE` (o key que uses para `/events` y Storage)

## Instalación
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Configuración
- Copia `.env.sample` (si no existe, crea uno) y define las API keys y URL/keys de Supabase.
- VS Code: el repositorio ya incluye `.vscode/settings.json` apuntando a `.venv` y `pyrightconfig.json`.

## Pruebas locales
```bash
source .venv/bin/activate
python -m unittest discover -s tests
pyright pipeline
```

## Uso rápido
- Clasificador visual de prueba: `python test_classifier.py` (requiere imágenes en `test_images/`).
- Generación de contenido: usa `generate_event_content` pasando los datos base del evento.
- Construir payload Supabase: `build_supabase_event_payload(wav_event, media_dict)`.

## Roadmap inmediato
1. Implementar `pipeline/media_processor.py` (frames, WebP, covers, hooks de upscale/denoise).
2. Implementar `pipeline/video_processor.py` (ffmpeg wrapper 720p, thumbnails, clips).
3. Implementar `pipeline/orchestrator.py` para flujo E2E y subida a Supabase.

## Estilo y calidad
- Sin emojis fuera de donde se permite (Instagram body con límite).
- Respuestas estructuradas en JSON estricto.
- Mantener `needs_review` en los payloads para trazabilidad.

