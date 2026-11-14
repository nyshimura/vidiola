# Integração Opcional: DaVinci Resolve Studio

Se o usuário pedir para montar a timeline no **DaVinci Resolve Studio** (em vez de renderizar direto via FFmpeg):

1. **Regra "Apenas Adicionar"**:
   - Nunca modifique, sobrescreva ou apague o projeto aberto, a timeline template ou os clipes originais.
   - Sempre duplique a timeline template para `<video> - Transcript cut (v1)`, `(v2)`, etc.
2. **Re-leitura Obrigatória**:
   - Se o usuário fez ajustes manuais no Resolve, re-leia a timeline antes de aplicar B-roll ou legendas para não recolocar trechos que ele apagou.
3. **Sem Chaves no Chat**:
   - Se o usuário configurar transcrição paga externa em `keys.env`, nunca imprima, leia no chat ou faça `cat`/`echo` desse arquivo.

