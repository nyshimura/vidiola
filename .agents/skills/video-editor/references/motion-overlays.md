# Motion Overlays & Sub-Agentes (Opcional)

O fluxo padrão usa **FFmpeg puro** (rápido e sem dependências externas). Quando o usuário pedir inserts animados complexos (cards de UI, notificações, animações HTML/CSS ou React):

1. **HyperFrames / Remotion (Opcional)**:
   - Só instale ou execute pacotes Node (`hyperframes` ou `remotion`) após confirmação explícita do usuário.
   - Prefira dependências fixadas em `package.json` local, evitando `npx --yes` em pacotes não auditados.
2. **Brief para Sub-Agentes de Overlay**:
   - Tamanho fixo (`1080x1920` ou caixa exata dentro da safe zone).
   - Duração fixa sincronizada com os timestamps das palavras em `manifest.json`.
   - Saída em WebM transparente (VP9 com alpha) para composição via FFmpeg sobre o `aroll.mp4`.
   - Sem dados fabricados de terceiros (use apenas dados reais do usuário ou placeholders genéricos claramente fictícios).

