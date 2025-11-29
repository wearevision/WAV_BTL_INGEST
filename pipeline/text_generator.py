"""Structured event content generator for WAV BTL."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


SYSTEM_PROMPT = """[# WAV BTL — AI Content Generation System (Prompt System)

Este documento contiene los **Prompts del Sistema** definitivos para la generación automatizada de contenido de eventos. Estas instrucciones deben inyectarse en el contexto del modelo de lenguaje (LLM) encargado de procesar la información de cada carpeta.

---

## 1. System Persona & Voice

**Role:** Senior Technical Copywriter & SEO Specialist para "We Are Vision" (Agencia BTL de alta gama).
**Tone:** "Cinematic Geometry". Técnico, directo, sofisticado, minimalista.
**Strict Prohibition:** NUNCA usar emojis en títulos, descripciones, summaries o hooks. El uso de emojis está restringido SOLO al cuerpo de Instagram, y debe ser minimalista (máx 3-5).
**Language:** Español de Chile (neutro, profesional).

---

## 2. Field-Specific Prompts (System Instructions)

Utiliza estos prompts para generar cada campo del objeto JSON `WavEvent`.

### A. Identidad del Evento

#### `brand` (Marca)
> **Constraint:** Max 50 chars.
> **Prompt:** "Identifica el nombre oficial de la marca. Usa el nombre exacto, sin descriptores adicionales ni adjetivos (ej: 'Nike', no 'Nike Running Event'). Si es una colaboración, usa 'Marca X x Marca Y'."

#### `title` (Título del Evento)
> **Constraint:** Max 60 chars.
> **Prompt:** "Genera un título descriptivo de máximo 60 caracteres. Debe incluir un verbo de acción implícito o el tipo de evento y un diferenciador clave. Estilo periodístico. NUNCA uses emojis."

#### `slug` (URL Identifier)
> **Constraint:** URL-safe, kebab-case.
> **Prompt:** "Genera un slug SEO siguiendo el formato: `año-marca-nombre-evento`. Todo en minúsculas, sin tildes, sin 'ñ', reemplazando espacios por guiones medios. Ejemplo: `2023-adidas-marathon-santiago`."

---

### B. Contenido Principal (SEO & Web)

#### `summary` (Meta Description)
> **Constraint:** Max 160 chars.
> **Prompt:** "Genera un resumen ejecutivo de máximo 150 caracteres. Enfócate en el valor único y el diferenciador tecnológico o experiencial del evento. Debe funcionar como Meta Description de Google. Sin emojis."

#### `description` (Narrativa Principal)
> **Constraint:** Max 800 chars.
> **Prompt:** "Genera una narrativa técnica de 2 a 3 párrafos (máximo 800 caracteres en total). Estructura:
> 1. **Contexto:** El desafío de la marca.
> 2. **Ejecución:** La solución técnica/creativa (menciona pantallas, luces, estructuras, software).
> 3. **Impacto:** Resultado en la audiencia.
> Tono profesional y sofisticado. Sin lenguaje de ventas barato ('¡Increíble!')."

#### `highlights` (Puntos Clave)
> **Constraint:** Array de strings. Max 100 chars por item.
> **Prompt:** "Extrae 3 a 5 puntos clave (bullet points) que definan el éxito del proyecto. Enfócate en métricas, tecnologías específicas usadas (ej: 'Mapping 4K', '5.000 asistentes') o hitos de producción. Sé concreto."

#### `keywords` (Búsqueda Interna)
> **Constraint:** Array de strings.
> **Prompt:** "Genera 5 a 10 keywords SEO para indexación. Incluye: nombre de la marca, tipo de evento (ej: 'Lanzamiento', 'Fiesta'), industria, tecnologías usadas y ubicación."

---

### C. Social Media Automation (Instagram & LinkedIn)

#### `instagram_hook` (La Primera Línea)
> **Constraint:** Max 100 chars. NO EMOJIS.
> **Prompt:** "Genera un gancho (hook) emocional de 80-100 caracteres para la primera línea de Instagram. Debe detener el scroll. Usa una pregunta retórica o una afirmación potente. ESTRICTAMENTE SIN EMOJIS."

#### `instagram_body` (El Caption)
> **Constraint:** Max 1000 chars.
> **Prompt:** "Redacta el caption para Instagram.
> - **Estilo:** Storytelling inmersivo.
> - **Estructura:** Hook (ya generado) + Desarrollo (anécdota o detalle técnico) + Cierre.
> - **Formato:** Usa saltos de línea cada 2 frases para legibilidad.
> - **Emojis:** Permitidos pero limitados (máximo 3-5 estratégicos).
> - **Hashtags:** NO los incluyas aquí, van en campo separado."

#### `instagram_hashtags` (Etiquetas)
> **Constraint:** String (separados por espacio).
> **Prompt:** "Genera una lista de 10-15 hashtags optimizados. Mezcla:
> - 3 de Alto Volumen (100k+ posts)
> - 5 de Nicho/Industria (Marketing, BTL, Eventos)
> - 2 de Marca (Branded)
> Sepáralos por espacios. Ejemplo: `#MarketingExperiencial #BTLChile #EventProfs`."

#### `linkedin_post` (Profesional)
> **Constraint:** Max 1300 chars.
> **Prompt:** "Redacta un post para LinkedIn (1000-1300 caracteres).
> - **Enfoque:** B2B, Liderazgo de pensamiento (Thought Leadership), Caso de Éxito.
> - **Estructura:**
>   1. Headline profesional.
>   2. El desafío de negocio.
>   3. La solución WAV (técnica/logística).
>   4. Reflexión sobre el futuro de la industria.
> - **Tono:** Experto, analítico. Sin emojis o uso muy minimalista (1-2 bullets)."

---

## 3. Categorization Logic (AI Classifier)

Usa este árbol de decisión para asignar el campo `category`.

1. **¿Hay música en vivo, escenarios masivos o bandas?** -> `festivales-y-musica`
2. **¿Es un evento cerrado, cena, congreso o summit empresarial?** -> `eventos-corporativos`
3. **¿Es una intervención en vía pública, mall o punto de venta (sampling)?** -> `activaciones-de-marca`
4. **¿Involucra mapping, proyecciones, sensores o arte digital puro?** -> `instalaciones-interactivas`
5. **¿Es una tienda pop-up o diseño de vitrina?** -> `retail-experience`
6. **¿Es una exposición de arte, museo o galería?** -> `arte-y-cultura`
7. **¿Usa VR, AR, AI o gadgets tecnológicos como foco principal?** -> `tech-y-innovacion`

*Si no calza en ninguna, usar fallback:* `activaciones-de-marca`
]"""


def _wav_event_schema() -> Dict[str, Any]:
    """JSON schema used for structured outputs in both providers."""
    return {
        "type": "object",
        "properties": {
            "brand": {"type": "string", "maxLength": 50},
            "title": {"type": "string", "maxLength": 60},
            "slug": {"type": "string", "maxLength": 80},
            "summary": {"type": "string", "maxLength": 160},
            "description": {"type": "string", "maxLength": 800},
            "highlights": {
                "type": "array",
                "items": {"type": "string", "maxLength": 100},
                "minItems": 3,
                "maxItems": 5,
            },
            "keywords": {
                "type": "array",
                "items": {"type": "string", "maxLength": 80},
                "minItems": 5,
                "maxItems": 10,
            },
            "hashtags": {
                "type": "array",
                "items": {"type": "string", "maxLength": 80},
                "minItems": 5,
                "maxItems": 15
            },
            "instagram_closing": {"type": "string", "maxLength": 200},
            "alt_instagram": {"type": "string", "maxLength": 1000},
            "linkedin_article": {"type": "string", "maxLength": 3000},
            "alt_title_1": {"type": "string", "maxLength": 60},
            "alt_title_2": {"type": "string", "maxLength": 60},
            "instagram_hook": {"type": "string", "maxLength": 100},
            "instagram_body": {"type": "string", "maxLength": 1000},
            "instagram_hashtags": {"type": "string", "maxLength": 400},
            "linkedin_post": {"type": "string", "maxLength": 1300},
            "category": {
                "type": "string",
                "enum": [
                    "festivales-y-musica",
                    "eventos-corporativos",
                    "activaciones-de-marca",
                    "instalaciones-interactivas",
                    "retail-experience",
                    "arte-y-cultura",
                    "tech-y-innovacion",
                ],
            },
            "needs_review": {"type": "boolean"},
        },
        "required": [
            "brand",
            "title",
            "slug",
            "summary",
            "description",
            "highlights",
            "keywords",
            "hashtags",
            "instagram_closing",
            "alt_instagram",
            "linkedin_article",
            "alt_title_1",
            "alt_title_2",
            "instagram_hook",
            "instagram_body",
            "instagram_hashtags",
            "linkedin_post",
            "category",
            "needs_review",
        ],
        "additionalProperties": False,
    }


@dataclass
class WavEvent:
    brand: str
    title: str
    slug: str
    summary: str
    description: str
    highlights: List[str]
    keywords: List[str]
    hashtags: List[str]
    instagram_closing: str
    alt_instagram: str
    linkedin_article: str
    alt_title_1: str
    alt_title_2: str
    instagram_hook: str
    instagram_body: str
    instagram_hashtags: str
    linkedin_post: str
    category: str
    needs_review: bool = False

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WavEvent":
        return cls(
            brand=data["brand"],
            title=data["title"],
            slug=data["slug"],
            summary=data["summary"],
            description=data["description"],
            highlights=list(data["highlights"]),
            keywords=list(data["keywords"]),
            hashtags=list(data["hashtags"]),
            instagram_closing=data["instagram_closing"],
            alt_instagram=data["alt_instagram"],
            linkedin_article=data["linkedin_article"],
            alt_title_1=data["alt_title_1"],
            alt_title_2=data["alt_title_2"],
            instagram_hook=data["instagram_hook"],
            instagram_body=data["instagram_body"],
            instagram_hashtags=data["instagram_hashtags"],
            linkedin_post=data["linkedin_post"],
            category=data["category"],
            needs_review=data.get("needs_review", False),
        )


def _build_user_prompt(event_data: Dict[str, Any]) -> str:
    formatted = json.dumps(event_data, ensure_ascii=False, indent=2)
    return (
        "Genera todos los campos del objeto WavEvent siguiendo las reglas del system prompt. "
        "Respeta límites de caracteres y formatos de cada campo. "
        "Datos de entrada del evento (JSON):\n"
        f"{formatted}"
    )


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


def _enforce_constraints(data: Dict[str, Any], schema: Dict[str, Any]) -> Tuple[Dict[str, Any], bool]:
    """Trims payload to schema limits and flags needs_review when exceeded."""
    cleaned: Dict[str, Any] = dict(data)
    properties = schema.get("properties", {})
    needs_review = False

    for field, props in properties.items():
        if field not in cleaned:
            continue
        value = cleaned[field]
        typ = props.get("type")

        if typ == "string" and isinstance(value, str):
            max_len = props.get("maxLength")
            if max_len and len(value) > max_len:
                cleaned[field] = value[:max_len]
                needs_review = True

        elif typ == "array" and isinstance(value, list):
            max_items = props.get("maxItems")
            min_items = props.get("minItems")
            item_schema = props.get("items") or {}

            if max_items and len(value) > max_items:
                cleaned[field] = value[:max_items]
                needs_review = True
            if min_items and len(value) < min_items:
                needs_review = True

            if item_schema.get("type") == "string":
                item_max = item_schema.get("maxLength")
                if item_max:
                    new_items: List[str] = []
                    for item in cleaned[field]:
                        if isinstance(item, str) and len(item) > item_max:
                            new_items.append(item[:item_max])
                            needs_review = True
                        else:
                            new_items.append(item)
                    cleaned[field] = new_items

    if needs_review:
        cleaned["needs_review"] = True
    else:
        cleaned.setdefault("needs_review", False)
    return cleaned, needs_review


def _normalize_model_name(model_name: str) -> str:
    return model_name if model_name.startswith("models/") else f"models/{model_name}"


def _call_openai(
    event_data: Dict[str, Any],
    model: Optional[str],
    temperature: float,
    client: Any,
) -> WavEvent:
    schema = _wav_event_schema()
    if client is None:
        try:
            from openai import OpenAI  # type: ignore[import-not-found]
        except ImportError as exc:  # pragma: no cover - dependency guard
            raise RuntimeError("Falta la dependencia openai. Instala `openai` >= 1.2.") from exc
        openai_client = OpenAI()
    else:
        openai_client = client
    completion = openai_client.chat.completions.create(
        model=model or "gpt-4o",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": _build_user_prompt(event_data)},
        ],
        temperature=temperature,
        response_format={
            "type": "json_schema",
            "json_schema": {"name": "wav_event", "schema": schema, "strict": True},
        },
    )
    message = completion.choices[0].message
    parsed = getattr(message, "parsed", None)
    if parsed:
        data = parsed
    else:
        data = _safe_json_loads(message.content)  # type: ignore[arg-type]
    cleaned, needs_review = _enforce_constraints(data, schema)
    if needs_review:
        cleaned["needs_review"] = True
    return WavEvent.from_dict(cleaned)


def _call_gemini(
    event_data: Dict[str, Any],
    model: Optional[str],
    temperature: float,
    client: Any,
) -> WavEvent:
    schema = _wav_event_schema()
    if client is None:
        try:
            import google.generativeai as genai
            from google.api_core.exceptions import NotFound
        except ImportError as exc:  # pragma: no cover - dependency guard
            raise RuntimeError(
                "Falta la dependencia google-generativeai. Instala `google-generativeai` >= 0.5."
            ) from exc

        generation_config = {
            "temperature": temperature,
            "response_schema": schema,
            "response_mime_type": "application/json",
        }
        model_name = _normalize_model_name(model or "gemini-2.0-flash")
        gen_model = genai.GenerativeModel(  # type: ignore[attr-defined]
            model_name=model_name,
            system_instruction=SYSTEM_PROMPT,
            generation_config=generation_config,  # type: ignore[arg-type]
        )
    else:
        gen_model = client
        NotFound = Exception  # type: ignore[misc,assignment-type]

    prompt = _build_user_prompt(event_data)
    try:
        result = gen_model.generate_content(prompt)
    except NotFound as exc:  # type: ignore[misc]
        fallback = "gemini-flash-latest"
        if client is None:
            gen_model = genai.GenerativeModel(  # type: ignore[attr-defined]
                model_name=_normalize_model_name(fallback),
                system_instruction=SYSTEM_PROMPT,
                generation_config=generation_config,  # type: ignore[arg-type]
            )
            result = gen_model.generate_content(prompt)
        else:
            raise RuntimeError(
                "El modelo solicitado no está disponible con la versión de API actual. "
                "Usa un modelo compatible (p.ej. `gemini-pro-vision`)."
            ) from exc

    if getattr(result, "text", None):
        raw = result.text
    elif getattr(result, "candidates", None):
        parts: List[str] = []
        for candidate in result.candidates:
            for part in getattr(candidate.content, "parts", []):
                text_part = getattr(part, "text", "")
                if text_part:
                    parts.append(text_part)
        raw = "\n".join(parts)
    else:
        raw = str(result)
    data = _safe_json_loads(raw)
    cleaned, needs_review = _enforce_constraints(data, schema)
    if needs_review:
        cleaned["needs_review"] = True
    return WavEvent.from_dict(cleaned)


def generate_event_content(
    event_data: Dict[str, Any],
    provider: str = "openai",
    model: Optional[str] = None,
    temperature: float = 0.4,
    client: Any = None,
) -> WavEvent:
    """
    Generate a full WavEvent using Gemini or GPT-4o with structured outputs.

    Args:
        event_data: Dict con los datos base del evento.
        provider: "openai" (GPT-4o) o "gemini".
        model: Nombre del modelo específico (opcional).
        temperature: Creatividad del modelo.
        client: Cliente ya autenticado (opcional).
    """
    provider_key = provider.lower()
    if provider_key in {"openai", "gpt-4o", "gpt4o", "gpt"}:
        return _call_openai(event_data, model, temperature, client)
    if provider_key in {"gemini", "google"}:
        return _call_gemini(event_data, model, temperature, client)
    raise ValueError(f"Proveedor no soportado: {provider}")


__all__ = ["WavEvent", "generate_event_content", "SYSTEM_PROMPT"]
