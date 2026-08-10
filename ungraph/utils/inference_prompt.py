"""
Ensamblado de texto auxiliar para prompts de extracción (GraphTransformer, etc.).
"""

from __future__ import annotations

from ungraph.domain.value_objects.document_context import DocumentContext


def build_graph_transformer_context_addon(
    document_context: DocumentContext,
    domain_questions: tuple[str, ...],
    *,
    max_chars: int = 6000,
) -> str:
    """
    Concatena resumen de documento y preguntas de dominio para inyectar en prompts.

    El llamador decide si añadirlo al system prompt, user o plantilla del transformer.
    """
    parts: list[str] = [document_context.to_prompt_snippet()]
    if domain_questions:
        parts.append(
            "Domain questions — use them to decide which entities and relations matter:\n"
            + "\n".join(f"- {q}" for q in domain_questions)
        )
    out = "\n\n".join(parts)
    if len(out) > max_chars:
        return out[: max_chars - 1] + "…"
    return out


def build_spacy_lexical_hints_addon(
    entity_name_types: list[tuple[str, str]],
    *,
    max_chars: int = 4500,
    max_items: int = 120,
) -> str:
    """
    Formatea candidatos NER (spaCy) para inyectarlos antes del texto fuente en extracción LLM.

    El modelo puede anclar nodos a estos spans cuando aparecen en el texto y completar el grafo
    con relaciones y tipos permitidos por el esquema.
    """
    if not entity_name_types:
        return ""
    seen: set[tuple[str, str]] = set()
    lines: list[str] = []
    for name, typ in entity_name_types:
        n = (name or "").strip()
        if not n:
            continue
        t = (typ or "UNKNOWN").strip() or "UNKNOWN"
        key = (n.lower(), t)
        if key in seen:
            continue
        seen.add(key)
        lines.append(f"- {n} ({t})")
        if len(lines) >= max_items:
            break
    if not lines:
        return ""
    header = (
        "Lexical entity candidates (spaCy NER) — prefer resolving these spans when they "
        "appear verbatim or clearly refer to the same referent in the source; you may add "
        "other entities and relationships allowed by the schema.\n"
    )
    body = "\n".join(lines)
    out = header + body
    if len(out) > max_chars:
        return out[: max_chars - 1] + "…"
    return out
