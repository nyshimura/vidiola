# Vidiola — Guia de Uso & Melhores Práticas

**Vidiola** é uma skill local-first e endurecida em segurança para o **Antigravity**, projetada para transformar vídeos brutos em Reels, Shorts, TikToks (`9:16`) ou vídeos de YouTube (`16:9`) diretamente na sua máquina — sem enviar seus vídeos para a nuvem e sem tocar nos arquivos originais.

---

## 1. Como Começar (em qualquer pasta)

Para usar em qualquer projeto ou pasta do Antigravity ou Claud, basta mencionar **`vidiola`** ou **`/vidiola`** no chat e informar onde estão seus vídeos:

> *"vidiola, edite os vídeos que estão em `D:\Gravacoes\Aula01` para Reels."*

### O que acontece automaticamente
1. **Diagnóstico (`doctor.py`)**: verifica `ffmpeg`, `ffprobe`, `faster-whisper` e `pillow`. Se algo faltar em outro computador, a skill lista o que precisa e **pede sua permissão** antes de instalar.
2. **Estilo (`my-style.md`)**: na primeira vez, faz perguntas rápidas (formato, estilo de legenda, ritmo e áudio) e salva suas preferências.
3. **Pasta de Resultados (`vidiola-edits/`)**: cria automaticamente a subpasta `vidiola-edits/` dentro da sua pasta de vídeos (ou em outro local que você escolher), mantendo os **arquivos originais 100% intactos**.
4. **Rascunho & QA**: gera `<slug>-v1.mp4`, valida resolução/áudio/frames com `qa_check.py` e apresenta o resumo dos cortes.

---

## 2. Melhores Práticas ao Gravar

Seguir estes hábitos simples melhora drasticamente o resultado automático da Vidiola:

- **Grave em 4K quando possível**: permite aplicar *punch-in* (zoom de `1.3x–1.8x` entre cortes do mesmo ângulo) mantendo nitidez total em `1080p`.
- **Errou? Repita a frase inteira**: a skill seleciona automaticamente o **último take completo e limpo**, cortando tentativas anteriores, pausas longas e silêncios.
- **Fale notas para o editor durante a gravação**: frases como *"editor, coloca um B-roll de tela aqui"* são detectadas na transcrição, removidas do corte final e transformadas em marcações.
- **Microfone sem fio em 1 canal (mono)**: não se preocupe se a voz saiu só no lado esquerdo — o `assemble.py` detecta `audio_channels == 1` e converte para estéreo centralizado automaticamente.
- **B-Roll**: deixe clipes extras sem fala na mesma pasta (ou indique os arquivos) para que entrem cobrindo o A-roll sem cortar sua voz.

---

## 3. Melhores Práticas no Chat (Prompts Eficientes)

### Primeira edição
- *"vidiola, corta os vídeos de `C:\Users\nyshi\Videos\ProjetoX` em formato 9:16 com look bold e legendas."*
- *"vidiola, pega só o arquivo `D:\Clips\take_final.mp4` e salva o resultado em `D:\Editados`."*

### Pedindo ajustes (gera `-v2`, `-v3`...)
Fale em linguagem natural, sem precisar saber termos técnicos:
- *"Deixa o ritmo mais apertado, sem respiros."*
- *"Tira o trecho em que eu falo sobre X e volta a frase anterior."*
- *"Faz uma versão horizontal 16:9 para o YouTube."* *(A skill recompõe o enquadramento e as legendas para 1920×1080, não apenas recorta).*
- *"Aprovado, gera o final."* → gera `<slug>-final.mp4`.

### Ensinando seu gosto (`my-rules.md`)
Sempre que você disser algo como *"sempre corte respiros"*, *"nunca use legenda amarela"* ou *"sempre normalize o áudio bem alto"*, a Vidiola salva isso como uma regra datada em `my-rules.md`. Nas próximas edições, **as suas regras têm prioridade sobre o estilo padrão**.

---

## 4. Looks & Safe Zones

| Look | Visual & Indicação |
| :--- | :--- |
| **`bold`** | Tipografia cinética forte, caixa alta em destaques, ideal para Reels/Shorts de retenção alta. |
| **`cool-girl`** | Paleta quente, serifada itálica suave, ritmo mais fluido e natural. |
| **`cool-dude`** | Alto contraste editorial escuro, títulos espaçados + corpo serifado limpo. |

**Safe Zones respeitadas automaticamente (9:16 — 1080×1920):**
- `220 px` livres no topo (barra de status / título).
- `450 px` livres na base (legenda e botões do app).
- `100 px` livres à direita abaixo de `y = 1155` (ícones de curtir/comentar/compartilhar).
- Nunca cobre rosto, olhos ou boca com texto.

---

## 5. Segurança & Privacidade Local

A Vidiola foi construída para uso local seguro:
- **100% Offline por padrão**: transcrição via `faster-whisper` local e SFX sintetizados localmente via FFmpeg (`sfx_synth.py`) — nenhum vídeo ou áudio é enviado para servidores externos.
- **Originais intocados**: a pasta de origem é tratada como **somente leitura**.
- **Confinamento de caminhos (`security.py`)**: bloqueia *path traversal* (`../`) e impede leitura/escrita em diretórios de sistema (`Windows`, `Program Files`, `/usr`, `/etc`, etc.).
- **Zero *shell injection***: todos os comandos rodam via `subprocess.run(..., shell=False)` com escape de texto para legendas/filtros FFmpeg.
- **Segredos protegidos**: caso você opte por configurar chaves em `.env` no futuro, a skill nunca lê nem imprime chaves no chat.

---

## 6. Referências & Créditos

A arquitetura e metodologia da Vidiola consolidam aprendizados de:
- [`tenfoldmarc/video-edit-skill`](https://github.com/tenfoldmarc/video-edit-skill) — pipeline 9:16, seleção de takes, *safe zones* e QA por frames.
- [`riecodes/free247editor`](https://github.com/riecodes/free247editor) — onboarding de estilo (`my-style.md`), aprendizado contínuo (`my-rules.md`) e versionamento simples.
- [`appariciojunior/video-editor-skills`](https://github.com/appariciojunior/video-editor-skills) — edição modular por índice de palavra, *vlog pacing*, B-roll e tratamento de áudio *(CC BY-NC 4.0 — uso pessoal/não-comercial)*.
- [`zhuyansen/awesome-claude-video-skills`](https://github.com/zhuyansen/awesome-claude-video-skills) — critérios objetivos de QA e diretrizes de segurança para skills de vídeo.

