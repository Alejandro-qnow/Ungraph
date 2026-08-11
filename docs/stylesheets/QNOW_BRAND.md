# Paleta y estilo Qnow (docs MkDocs)

**Fuente de verdad visual:** tokens en [`qnow-tokens.css`](qnow-tokens.css), muestreados de los colores publicados en [qnow.tech](https://qnow.tech/) (2026-08).  
**Aplicación:** [`extra.css`](extra.css) + `theme.palette` `primary/accent: custom` en `mkdocs.yml`.

## Tokens principales

| Rol | Token | Hex | Uso |
|-----|-------|-----|-----|
| Ink | `--qnow-ink` | `#0d131a` | Texto principal (contraste sobre surface) |
| Surface | `--qnow-surface` | `#faf9fa` | Fondos unificados: página, header, tabs, nav, footer |
| Primary | `--qnow-primary` | `#5025d1` | Marca / hover de enlaces (no chrome) |
| Primary deep | `--qnow-primary-deep` | `#2f1c6a` | Títulos H1, contraste |
| Accent | `--qnow-accent` | `#00b090` | Enlaces, énfasis técnico |
| Accent deep | `--qnow-accent-deep` | `#008361` | Links hover/base claro |
| Wash primary | `--qnow-primary-wash` | `#ebe4ff` | Soft / slate text |
| Wash accent | `--qnow-accent-wash` | `#def4f0` | Soft tip / success |

Secundarios (uso escaso): azul `#357df9`, ámbar `#fea419`, rosa `#fc5185`.

## Reglas de uso en docs

1. No hardcodear hex nuevos en páginas markdown; si hace falta color, extender `qnow-tokens.css`.
2. Surface = fondos del chrome; primary = identidad Qnow en tipografía/hover; accent = señal “ahora / medible / técnico”.
3. Logo canónico (README / qnow.tech): wordmark negro sobre claro. Para el header MkDocs, guardar como `docs/assets/qnow-logo.png` y descomentar `theme.logo` / `favicon` en `mkdocs.yml`.
4. El curado científico (`CURATION_CHECKLIST`) no define color; este archivo sí.

## Preview

```bash
uv sync --extra docs
uv run mkdocs serve -a 127.0.0.1:8000
```
