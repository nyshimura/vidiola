# Safe Zones & Layout

## Vertical 9:16 (1080 × 1920 — Reels, TikTok, Shorts)
Mantenha todo texto, legenda e card dentro da área segura:
- **Topo livre**: `220 px` (status bar + título do app).
- **Base livre**: `450 px` (nada abaixo de `y = 1470` — barra de legenda/descrição).
- **Laterais**: mínimo `35 px` à esquerda; `100 px` à direita a partir de `y = 1155` (ícones de curtir/comentar/compartilhar).
- **Rosto protegido**: nunca cubra olhos/boca com legendas ou cards.
- **Texto atrás da cabeça (`bold`)**: cada letra deve manter pelo menos ~70% de visibilidade.

## Horizontal 16:9 (1920 × 1080 — YouTube)
- Ao gerar versão horizontal a partir de um projeto vertical, **recompõe** o enquadramento e a posição das legendas (`MarginV = 60`), nunca apenas recorte cego.
- Margens seguras: `96 px` laterais, `54 px` topo/base.

