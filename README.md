# Vidiola — Edição de Vídeo Local Segura (Antigravity & Claude Code)

**Vidiola** é uma skill local-first e endurecida em segurança para **Antigravity** e **Claude Code**, projetada para transformar vídeos brutos em Reels, Shorts, TikToks (`9:16`) ou vídeos de YouTube (`16:9`) diretamente na sua máquina — sem enviar seus vídeos para a nuvem e sem tocar nos arquivos originais.

---

## 1. Instalação (Antigravity ou Claude Code)

### No Antigravity
**Global (usar em qualquer pasta dizendo `vidiola`):**
- **Windows (PowerShell):**
  ```powershell
  git clone https://github.com/nyshimura/vidiola.git "$env:TEMP\vidiola-repo"
  New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.gemini\config\skills\vidiola" | Out-Null
  Copy-Item -Recurse -Force "$env:TEMP\vidiola-repo\.agents\skills\video-editor\*" "$env:USERPROFILE\.gemini\config\skills\vidiola\"
  Remove-Item -Recurse -Force "$env:TEMP\vidiola-repo"
  ```
- **macOS / Linux:**
  ```bash
  git clone https://github.com/nyshimura/vidiola.git /tmp/vidiola-repo
  mkdir -p ~/.gemini/config/skills/vidiola
  cp -R /tmp/vidiola-repo/.agents/skills/video-editor/* ~/.gemini/config/skills/vidiola/
  rm -rf /tmp/vidiola-repo
  ```

### No Claude Code
**Global (usar com `/vidiola` em qualquer projeto):**
- **Windows (PowerShell):**
  ```powershell
  git clone https://github.com/nyshimura/vidiola.git "$env:TEMP\vidiola-repo"
  New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.claude\skills\vidiola" | Out-Null
  Copy-Item -Recurse -Force "$env:TEMP\vidiola-repo\.agents\skills\video-editor\*" "$env:USERPROFILE\.claude\skills\vidiola\"
  Remove-Item -Recurse -Force "$env:TEMP\vidiola-repo"
  ```
- **macOS / Linux:**
  ```bash
  git clone https://github.com/nyshimura/vidiola.git /tmp/vidiola-repo
  mkdir -p ~/.claude/skills/vidiola
  cp -R /tmp/vidiola-repo/.agents/skills/video-editor/* ~/.claude/skills/vidiola/
  rm -rf /tmp/vidiola-repo
  ```

*(Ou, para usar apenas em um projeto específico, copie a pasta `.agents/skills/video-editor` para `.agents/skills/vidiola` ou `.claude/skills/vidiola` dentro do projeto.)*

---

## 2. Dependências Automáticas (Pré-voo)

Assim que você baixar a skill e disser **`vidiola`** (ou **`/vidiola`**) pela primeira vez, o **Passo 0 (`doctor.py`)** roda automaticamente antes de qualquer edição:
1. Verifica `ffmpeg`, `ffprobe`, `faster-whisper==1.2.1`, `av>=11,<19` (com teste real de decodificação de áudio) e `pillow`.
2. Se faltar qualquer biblioteca ou houver versão incompatível (ex.: `PyAV 19+`), a skill **pede sua permissão** e instala/atualiza tudo automaticamente com:
   ```powershell
   python "<caminho_da_skill>/scripts/doctor.py" --install --yes
   ```
3. *(Opcional)* Se quiser usar também o efeito de **texto atrás da cabeça (`bold`)**, instale:
   ```powershell
   pip install rembg onnxruntime
   ```

---

## 3. Como Usar (em qualquer pasta)

Basta mencionar **`vidiola`** ou **`/vidiola`** no chat e informar onde estão seus vídeos brutos:

> *"vidiola, edite os vídeos que estão em `D:\Gravacoes\Aula01` para Reels."*

### O que acontece automaticamente
1. **Pré-voo (`doctor.py`)**: garante que todas as bibliotecas estão instaladas e compatíveis (`READY`).
2. **Estilo (`my-style.md`)**: na primeira vez, faz perguntas rápidas (formato, estilo de legenda, ritmo e áudio) e salva suas preferências.
3. **Pasta de Resultados (`vidiola-edits/`)**: cria automaticamente a subpasta `vidiola-edits/` dentro da sua pasta de vídeos (ou em outro local que você escolher), mantendo os **arquivos originais 100% intactos**.
4. **Rascunho & QA**: gera `<slug>-v1.mp4`, valida resolução/áudio/frames com `qa_check.py` e apresenta o resumo dos cortes.

---

## 4. Melhores Práticas ao Gravar

- **Grave em 4K quando possível**: permite aplicar *punch-in* (zoom de `1.3x–1.8x` entre cortes do mesmo ângulo) mantendo nitidez total em `1080p`.
- **Errou? Repita a frase inteira**: a skill seleciona automaticamente o **último take completo e limpo**, cortando tentativas anteriores, pausas longas e silêncios.
- **Fale notas para o editor durante a gravação**: frases como *"editor, coloca um B-roll de tela aqui"* são detectadas na transcrição, removidas do corte final e transformadas em marcações.
- **Microfone sem fio em 1 canal (mono)**: não se preocupe se a voz saiu só no lado esquerdo — o `assemble.py` detecta `audio_channels == 1` e converte para estéreo centralizado automaticamente.
- **B-Roll**: deixe clipes extras sem fala na mesma pasta (ou indique os arquivos) para que entrem cobrindo o A-roll sem cortar sua voz.

---

## 5. Melhores Práticas no Chat (Prompts Eficientes)

### Primeira edição
- *"vidiola, corta os vídeos de `C:\Users\seu_usuario\Videos\ProjetoX` em formato 9:16 com look bold e legendas."*
- *"vidiola, pega só o arquivo `D:\Clips\take_final.mp4` e salva o resultado em `D:\Editados`."*

### Pedindo ajustes (gera `-v2`, `-v3`...)
Fale em linguagem natural:
- *"Deixa o ritmo mais apertado, sem respiros."*
- *"Tira o trecho em que eu falo sobre X e volta a frase anterior."*
- *"Faz uma versão horizontal 16:9 para o YouTube."* *(A skill recompõe o enquadramento e as legendas para 1920×1080, não apenas recorta).*
- *"Aprovado, gera o final."* → gera `<slug>-final.mp4`.

### Ensinando seu gosto (`my-rules.md`)
Sempre que você disser algo como *"sempre corte respiros"*, *"nunca use legenda amarela"* ou *"sempre normalize o áudio bem alto"*, a Vidiola salva isso como uma regra datada em `my-rules.md`. Nas próximas edições, **as suas regras têm prioridade sobre o estilo padrão**.

---

## 6. Looks & Safe Zones

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

## 7. Segurança & Privacidade Local

- **100% Offline por padrão**: transcrição via `faster-whisper` local e SFX sintetizados localmente via FFmpeg (`sfx_synth.py`) — nenhum vídeo ou áudio é enviado para servidores externos.
- **Originais intocados**: a pasta de origem é tratada como **somente leitura**.
- **Confinamento de caminhos (`security.py`)**: bloqueia *path traversal* (`../`) e impede leitura/escrita em diretórios de sistema (`Windows`, `Program Files`, `/usr`, `/etc`, etc.).
- **Zero *shell injection***: todos os comandos rodam via `subprocess.run(..., shell=False)` com escape de texto para legendas/filtros FFmpeg.
- **Segredos protegidos**: caso você opte por configurar chaves em `.env` no futuro, a skill nunca lê nem imprime chaves no chat.

---

## 8. Referências & Créditos

A arquitetura e metodologia da Vidiola consolidam aprendizados de:
- [`tenfoldmarc/video-edit-skill`](https://github.com/tenfoldmarc/video-edit-skill) — pipeline 9:16, seleção de takes, *safe zones* e QA por frames.
- [`riecodes/free247editor`](https://github.com/riecodes/free247editor) — onboarding de estilo (`my-style.md`), aprendizado contínuo (`my-rules.md`) e versionamento simples.
- [`appariciojunior/video-editor-skills`](https://github.com/appariciojunior/video-editor-skills) — edição modular por índice de palavra, *vlog pacing*, B-roll e tratamento de áudio *(CC BY-NC 4.0 — uso pessoal/não-comercial)*.
- [`zhuyansen/awesome-claude-video-skills`](https://github.com/zhuyansen/awesome-claude-video-skills) — critérios objetivos de QA e diretrizes de segurança para skills de vídeo.
