#!/usr/bin/env python3
"""
Categorize events based on keywords, title, description, and metadata.
Maps to the correct Spanish categories used in Figma/Make.
"""

import re
from typing import Dict, List, Optional

# Category definitions with keywords
CATEGORIES = {
    "Activaciones de Marca": [
        "activacion", "activación", "brand activation", "lanzamiento", "launch",
        "experiencia de marca", "street marketing", "sampling", "degustacion",
        "promocion", "promoción", "pop-up", "flash mob"
    ],
    "Eventos Corporativos": [
        "evento corporativo", "corporate event", "convencion", "convención",
        "conference", "summit", "congreso", "reunion", "reunión", "meeting",
        "celebracion", "celebración", "aniversario", "anniversary", "premiacion",
        "premiación", "gala", "cena", "dinner", "cocktail"
    ],
    "Brand Experience": [
        "brand experience", "experiencia de marca", "inmersivo", "immersive",
        "interactivo", "interactive", "museo", "museum", "exhibition",
        "exposicion", "exposición", "instalacion", "instalación", "art",
        "arte", "sensorial", "journey", "recorrido"
    ],
    "Trade Marketing & Retail": [
        "trade marketing", "retail", "punto de venta", "pdv", "pos",
        "merchandising", "shopper marketing", "in-store", "tienda",
        "retail activation", "dealer", "distribuidor", "channel"
    ],
    "Stands & Ferias": [
        "stand", "feria", "expo", "exhibition", "trade show", "booth",
        "pabellon", "pabellón", "showroom", "salon", "salón", "muestra",
        "exhibicion", "exhibición", "display"
    ],
    "Experiencia Digital & Híbrida": [
        "digital", "hibrido", "híbrido", "hybrid", "virtual", "online",
        "streaming", "webinar", "zoom", "metaverso", "metaverse", "ar", "vr",
        "realidad aumentada", "realidad virtual", "app", "mobile", "web",
        "plataforma", "platform", "tecnologia", "tecnología", "tech"
    ],
    "Ambient Marketing": [
        "ambient", "ooh", "out of home", "publicidad exterior", "outdoor",
        "valla", "billboard", "mupis", "street furniture", "mobiliario urbano",
        "guerrilla", "unconventional", "no convencional"
    ],
    "Roadshows": [
        "roadshow", "road show", "gira", "tour", "itinerante", "mobile",
        "movil", "móvil", "truck", "camion", "camión", "caravan", "caravana",
        "ruta", "route", "multiciudad", "multi-ciudad"
    ],
    "Producción Audiovisual": [
        "video", "audiovisual", "produccion", "producción", "filmacion",
        "filmación", "spot", "comercial", "motion", "animacion", "animación",
        "reel", "contenido", "content", "fotografia", "fotografía", "photo",
        "filming", "recording", "grabacion", "grabación", "edit", "edicion",
        "edición", "postproduccion", "postproducción"
    ],
    "Logística & Operaciones": [
        "logistica", "logística", "logistics", "operaciones", "operations",
        "montaje", "setup", "produccion", "producción", "coordinacion",
        "coordinación", "gestion", "gestión", "management", "implementacion",
        "implementación", "ejecucion", "ejecución"
    ]
}


def categorize_event(
    title: str = "",
    description: str = "",
    summary: str = "",
    keywords: List[str] = None,
    event_name: str = "",
    slug: str = ""
) -> str:
    """
    Categorize an event based on its content.
    Returns the best matching category in Spanish.
    """
    keywords = keywords or []
    
    # Combine all text for analysis
    combined_text = " ".join([
        title.lower(),
        description.lower(),
        summary.lower(),
        event_name.lower(),
        slug.lower(),
        " ".join(keywords).lower()
    ])
    
    # Score each category
    scores: Dict[str, int] = {cat: 0 for cat in CATEGORIES.keys()}
    
    for category, category_keywords in CATEGORIES.items():
        for keyword in category_keywords:
            # Count occurrences (case insensitive, whole words preferred)
            keyword_lower = keyword.lower()
            
            # Whole word match (higher score)
            whole_word_pattern = r'\b' + re.escape(keyword_lower) + r'\b'
            whole_word_matches = len(re.findall(whole_word_pattern, combined_text))
            scores[category] += whole_word_matches * 3
            
            # Partial match (lower score)
            if keyword_lower in combined_text and whole_word_matches == 0:
                scores[category] += 1
    
    # Get category with highest score
    best_category = max(scores.items(), key=lambda x: x[1])
    
    # If no strong match, default to "Activaciones de Marca"
    if best_category[1] == 0:
        return "Activaciones de Marca"
    
    return best_category[0]


def categorize_event_from_dict(event: Dict) -> str:
    """
    Categorize an event from a dictionary structure.
    Handles both old and new metadata formats.
    """
    # Extract fields
    title = event.get("title", "")
    description = event.get("description", "")
    summary = event.get("summary", "")
    slug = event.get("slug", "")
    
    # Try to get from metadata.content if exists
    metadata = event.get("metadata", {})
    content = metadata.get("content", {})
    
    if content:
        title = title or content.get("title", "")
        description = description or content.get("description", "")
        summary = summary or content.get("summary", "")
        keywords = content.get("keywords", [])
    else:
        keywords = event.get("keywords", [])
    
    event_name = metadata.get("event_name", "")
    
    return categorize_event(
        title=title,
        description=description,
        summary=summary,
        keywords=keywords,
        event_name=event_name,
        slug=slug
    )


# Example usage
if __name__ == "__main__":
    # Test cases
    test_events = [
        {
            "title": "Lanzamiento Nike Air Max 2024",
            "description": "Evento de lanzamiento con instalación interactiva y DJ set",
            "keywords": ["lanzamiento", "brand activation", "experiencia"]
        },
        {
            "title": "Convención Anual de Ventas",
            "description": "Reunión corporativa con premiación de vendedores destacados",
            "keywords": ["convencion", "corporate", "premiacion"]
        },
        {
            "title": "Stand Feria Laboral",
            "description": "Diseño e implementación de stand para feria de empleos",
            "keywords": ["stand", "feria", "booth"]
        },
        {
            "title": "Video Promocional Coca-Cola",
            "description": "Producción audiovisual de spot publicitario",
            "keywords": ["video", "produccion", "spot"]
        },
        {
            "title": "Roadshow Regional Chile",
            "description": "Gira por 5 ciudades con camión móvil",
            "keywords": ["roadshow", "gira", "movil"]
        }
    ]
    
    print("🎯 Category Mapping Test:\n")
    for event in test_events:
        category = categorize_event(
            title=event["title"],
            description=event["description"],
            keywords=event["keywords"]
        )
        print(f"Event: {event['title']}")
        print(f"  → Category: {category}\n")
