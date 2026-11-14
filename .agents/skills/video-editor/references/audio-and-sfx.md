# Áudio, Normalização & SFX Locais

## Correções Automáticas (`assemble.py`)
- **Microfone sem fio em modo mono/1 canal**: Se `audio_channels == 1`, duplica automaticamente para estéreo (`pan=stereo|c0=c0|c1=c0`) para a voz não sair só de um lado.
- **Normalização de Loudness**: Aplica `loudnorm=I=-14:TP=-1.5:LRA=11` (padrão YouTube/Reels).

## Efeitos Sonoros (SFX) & Trilha
- Use arquivos fornecidos pelo usuário em `my-sounds/`.
- Se `my-sounds/` estiver vazio, rode `sfx_synth.py` para gerar `whoosh-short.wav`, `pop.wav`, `click.wav` e `impact-bass.wav` localmente via FFmpeg (zero downloads externos).
- **Volume de SFX**: Sutil (máximo `0.75` do ganho base, nunca acima da voz).
- **Trilha musical**: Use ducking (`sidechaincompress` ou redução de `-18 dB` a `-22 dB`) sempre que houver voz.

