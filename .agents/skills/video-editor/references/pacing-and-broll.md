# Pacing, Corte por Índice de Palavra & B-Roll

## Regra de Ouro: Decisão por Índice, Tempo por Script
- O agente decide **quais palavras ficam** usando os índices `[0000]` de `transcript.txt` (ou `manifest.json`).
- Nunca invente timestamps manualmente; use os tempos exatos de `manifest.json` + `silences` para preencher `edl.json`.

## Seleção de Takes & Cortes
- **Retakes**: Quando o criador repete uma frase até acertar, mantenha o **último take completo e limpo** (a menos que o usuário indique outro trecho).
- **Margens de corte**:
  - Início do segmento: `0.05s – 0.07s` antes da primeira palavra.
  - Fim do segmento: no início do silêncio após a última palavra (confirme com `silences` para não cortar consoantes finais).
- **Punch-in (4K → 1080p)**: Dois segmentos consecutivos no mesmo ângulo pedem alteração de escala (`zoom: 1.3` a `1.8`, `cx: 0.5`, `cy: 0.45` focado no peito/rosto).
- **Notas faladas ao editor**: Frases como *"editor, coloca um B-roll aqui"* ou *"corta isso"* devem ser removidas do corte final e convertidas em anotações/marcadores no resumo.

## B-Roll
- Clipes em `inbox/` sem fala (ou marcados como B-roll pelo usuário) entram como cobertura visual sobre o A-roll, mantendo o áudio da voz principal contínuo.
- Nunca baixe vídeos/músicas da internet sem direito de uso ou confirmação do usuário.

