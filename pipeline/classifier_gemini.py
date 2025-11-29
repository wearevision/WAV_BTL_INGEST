"""
Visual classifier module for WAV BTL — powered by Gemini Vision.
Extracts structured metadata from event images/videos.
"""

from __future__ import annotations
import json
import logging
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union


# -----------------------------
# System Prompt (Visual)
# -----------------------------
SYSTEM_VISUAL_PROMPT = """
Eres un analista visual senior especializado en eventos BTL, festivales, activaciones de marca y experiencias interactivas.

Tu misión:
Dado un conjunto de imágenes o frames de video, debes identificar:
- Marca principal visible (si existe)
- Elementos de montaje (DJ, escenario, pantallas LED, mapping, retail, etc.)
- Tipo de evento (categoría WAV)
- Año probable del evento
- Colores dominantes
- Logos presentes
- Conceptos visuales clave
- Objetos relevantes
- Estimación de público
- Elementos técnicos (luces, estructura, displays)

Formato de salida: JSON ESTRICTO.
No inventes información si no aparece visualmente.
No generes texto narrativo; solo metadata estructurada.
"""


# -----------------------------
# Schema de salida del classifier
# -----------------------------
def _visual_schema() -> Dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "brand": {"type": "string"},
            "title_base": {"type": "string"},
            "year": {"type": "integer"},
            "category": {
                "type": "string",
                "enum": [
                    "festivales-y-musica",
                    "eventos-corporativos",
                    "activaciones-de-marca",
                    "instalaciones-interactivas",
                    "retail-experience",
                    "arte-y-cultura",
                    "tech-y-innovacion"
                ]
            },
            "visual_keywords": {
                "type": "array",
                "items": {"type": "string"}
            },
            "logo_detected": {"type": "boolean"},
            "dominant_colors": {
                "type": "array",
                "items": {"type": "string"}
            },
            "main_elements": {
                "type": "array",
                "items": {"type": "string"}
            },
            "confidence_scores": {
                "type": "object",
                "properties": {
                    "brand": {"type": "number"},
                    "category": {"type": "number"},
                    "year": {"type": "number"}
                }
            },
            "needs_review": {"type": "boolean"}
        },
        "required": [
            "brand",
            "title_base",
            "year",
            "category",
            "visual_keywords",
            "logo_detected",
            "dominant_colors",
            "main_elements",
            "confidence_scores",
            "needs_review"
        ]
    }


# -----------------------------
# Dataclass principal
# -----------------------------
@dataclass
class VisualClassification:
    brand: str
    title_base: str
    year: int
    category: str
    visual_keywords: List[str]
    logo_detected: bool
    dominant_colors: List[str]
    main_elements: List[str]
    confidence_scores: Dict[str, float]
    needs_review: bool

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VisualClassification":
        return cls(
            brand=data["brand"],
            title_base=data["title_base"],
            year=data["year"],
            category=data["category"],
            visual_keywords=list(data["visual_keywords"]),
            logo_detected=data["logo_detected"],
            dominant_colors=list(data["dominant_colors"]),
            main_elements=list(data["main_elements"]),
            confidence_scores=dict(data["confidence_scores"]),
            needs_review=data["needs_review"]
        )


# -----------------------------
# Helper
# -----------------------------
def _strip_code_fence(payload: str) -> str:
    cleaned = payload.strip()
    if not cleaned.startswith("```"):
        return cleaned
    sections = cleaned.split("```")
    if len(sections) >= 2:
        body = sections[1]
        if body.lstrip().startswith("json"):
            body = body.lstrip()[4:]
        return body.strip()
    return cleaned


def _safe_json_loads(payload: str) -> Dict[str, Any]:
    return json.loads(_strip_code_fence(payload))


def _normalize_model_name(model_name: str) -> str:
    return model_name if model_name.startswith("models/") else f"models/{model_name}"


# -----------------------------
# Llamada a Gemini
# -----------------------------
def classify_event_visual(
    images: List[Union[str, bytes]],
    model: str = "gemini-2.0-flash",
    temperature: float = 0.0,
    client: Any = None,
    timeout: float = 60.0,
    logger: Optional[logging.Logger] = None,
) -> VisualClassification:
    log = logger or logging.getLogger(__name__)
    try:
        import google.generativeai as genai
        from google.api_core.exceptions import NotFound
    except ImportError as exc:
        raise RuntimeError(
            "Falta la dependencia google-generativeai. Instala `google-generativeai` >= 0.5."
        ) from exc

    if client is None:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise RuntimeError("Falta GEMINI_API_KEY en variables de entorno para usar Gemini Vision.")
        genai.configure(api_key=api_key)  # type: ignore[attr-defined]

    schema = _visual_schema()

    def _build_model(model_name: str):
        normalized = _normalize_model_name(model_name)
        return genai.GenerativeModel(  # type: ignore[attr-defined]
            model_name=normalized,
            system_instruction=SYSTEM_VISUAL_PROMPT,
            generation_config={
                "temperature": temperature,
                "response_schema": schema,
                "response_mime_type": "application/json"
            }
        )

    effective_model = model
    gen_model = client or _build_model(effective_model)

    parts = []
    for img in images:
        if isinstance(img, str):
            with open(img, "rb") as f:
                parts.append({"mime_type": "image/jpeg", "data": f.read()})
        else:
            parts.append({"mime_type": "image/jpeg", "data": img})

    try:
        result = gen_model.generate_content(parts, request_options={"timeout": timeout})
    except NotFound as exc:
        if client is None and effective_model != "gemini-flash-latest":
            effective_model = "gemini-flash-latest"
            log.warning("Modelo %s no disponible, intentando fallback a %s", model, effective_model)
            gen_model = _build_model(effective_model)
            result = gen_model.generate_content(parts, request_options={"timeout": timeout})
        else:
            raise RuntimeError(
                "El modelo solicitado no está disponible con la versión de API actual. "
                "Usa un modelo compatible (p.ej. `gemini-pro-vision`)."
            ) from exc
    except Exception as exc:
        log.error("Error al llamar a Gemini Vision", exc_info=exc)
        raise

    if getattr(result, "text", None):
        raw = result.text
    else:
        raw = "\n".join(
            getattr(part, "text", "")
            for candidate in result.candidates
            for part in getattr(candidate.content, "parts", [])
        )

    data = _safe_json_loads(raw)
    return VisualClassification.from_dict(data)


__all__ = ["VisualClassification", "classify_event_visual"]
