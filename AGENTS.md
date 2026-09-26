# editor-videos — guía para agentes

**La fuente de verdad es `CLAUDE.md`** (y la skill `.claude/skills/video-tech-premium/`).
Este archivo solo resume; si algo de aquí choca con `CLAUDE.md`, manda `CLAUDE.md`.

- `editar-pieza`: la misma edición sin preguntas, para piezas que pide el dashboard (ver CLAUDE.md §2).

Resumen del sistema actual:

- **Layout `triband`** por defecto en todo REEL (animación arriba · subtítulo en medio ·
  hablante abajo, a la mitad del lienzo); la banda de arriba nunca queda vacía y nada entra
  antes de su palabra.
- **Dos paletas de la marca**, `claro` (crema, tinta casi negra) y `oscuro` (casi negro
  cálido, texto crema), con acento terracota. Cada pieza declara `"palette"` en
  `plan.json`/`edl.json` (obligatorio); todos los colores salen de `scripts/tokens.py`.
- **Tipografía**: Inter (todo el texto, 900 en titulares y subtítulos) + JetBrains Mono
  (etiquetas y datos). Subtítulos en karaoke con pastilla `accent_pill`.
- **Pipeline**: detectar formato → AssemblyAI → `refine-timings` → `plan-cuts --audio` →
  preguntar las animaciones (paso 3b, o brief de `plan-edicion`) → corte bruto →
  `audit-breaths` → cara → plan/EDL → `build-composition` → `hyperframes check` → render
  `--sdr`, y verificación sobre el MP4.
- **Reglas duras**: medir en vez de estimar (formato, cara, contraste, audio por canal),
  ningún color a mano en un componente, no tapar la cara, no adelantar el guion, no
  estilizar el metraje. Lista completa en `CLAUDE.md` §13.
