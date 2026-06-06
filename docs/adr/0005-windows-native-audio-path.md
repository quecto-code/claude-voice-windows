# 実行環境を WSL2 から Windows ネイティブへ移し、音声経路を waveaudio にする

claude-voice の実行環境を **WSL2（WSLg PulseAudio）から Windows ネイティブ**へ変更する。録音・再生の sox デバイスを `pulseaudio` から **`waveaudio`（Windows Multimedia Audio）** に置き換える。MCP サーバの構成・2 ツール（`voice_listen` / `voice_speak`）・ステートレス方針・2 パイプライン分割・vosk + faster-whisper の二段構成（[ADR-0003](./0003-dual-engine-streaming-listen.md)）・委譲型準並行（[ADR-0004](./0004-delegated-quasi-concurrency.md)）はすべて維持する。

## なぜ

当初 [ADR-0001](./0001-mcp-tool-driven-turn-based.md) 以降の設計は WSL2 上で音声経路（WSLg PulseAudio）を通す前提だった。しかし実運用環境が Windows ネイティブに変わり、WSL を経由しない方が以下の点で素直になった:

- **音声経路が 1 段減る**: WSLg PulseAudio 経由のリサンプリング/underrun（[CH-001](../changes/CHANGELOG.md) で対処した「カリカリ・プツプツ」歪みの原因）が、Windows の音声エンジンに直接出すことで根本的に消える。
- **sox は Windows でも `waveaudio` ドライバを持つ**（SoX 14.4.2 で確認、録音・再生とも可）。`-t waveaudio default` で既定デバイスに繋がる。
- VOICEVOX・vosk・faster-whisper はいずれも Windows 版/Windows 上 CUDA が利用でき、アーキテクチャを変えずに移植できる。

設計の骨格（ツール 2 つ・ステートレス・2 パイプライン）は移植コストが小さいため、プラットフォーム差分（オーディオデバイス指定・プロセス終了・パス・起動コマンド）だけを Windows に合わせる。

## Considered Options

- **WSL2 を維持（不採用）**: WSLg PulseAudio 経由の音声に依存し続ける。CH-001 のバッファ/リサンプリング対策を保守し続ける必要があり、実運用環境（Windows）と乖離する。
- **Windows ネイティブ + waveaudio（採用）**: sox の `waveaudio` を直接使う。音声経路が短くなり歪み要因が減る。プラットフォーム依存はデバイス指定・プロセス終了・パスに限局する。
- **別の Windows 音声ライブラリ（sounddevice 等）へ全面移行（不採用）**: sox サブプロセス方式（[ADR-0003](./0003-dual-engine-streaming-listen.md) 設計判断 2）の利点（無音検出を sox に任せる・raw PCM 正規化）を捨てることになり、変更が過大。

## Consequences

- **録音**: `sox -t waveaudio default -r 16000 -c 1 -t raw -e signed -b 16 - silence ...`。無音による自然停止は sox の silence エフェクトで従来どおり。
- **再生**: `sox -t wav - -t waveaudio default`。VOICEVOX の 24kHz をそのまま Windows 音声エンジンに渡せる。CH-001 の `--buffer` / `rate -v` は **WSLg 由来の歪み対策としては不要**になるが、underrun 耐性の保険として残し、既定で無害に効くよう `config` 化を維持する（Audio Quality NFR 自体は存続）。
- **末尾の取りこぼし対策（実機で判明）**: waveaudio はデバイス close 時に最後の 1 バッファ（≈`SOX_BUFFER_BYTES` 分 ＝ 48kHz/16bit/mono で約 0.34 秒）をドレインせず捨てることがあり、末尾の音声が切れる。sox エフェクト末尾に `pad 0 <PLAYBACK_TAIL_PAD_SEC>`（既定 0.8 秒、バッファ長以上）で無音を足し、捨てられるのが無音になるようにして本来の末尾を守る。
- **プロセス終了（確定ワード）**: Windows には POSIX SIGTERM がない。`proc.terminate()` は `TerminateProcess`（強制終了）になる。sox 終了直前の数チャンク flush は保証されないが、確定済み PCM は読取スレッドが buffer に保持済みのため取りこぼしは最小。設計上は「SIGTERM」を「terminate（停止シグナル）」と読み替える。
- **CUDA**: faster-whisper は `device="cuda"` のまま。前提は WSL の `libcuda.so` ではなく Windows の CUDA/cuDNN ランタイム（`.dll`）。
- **パス・起動**: venv は `.venv\Scripts\python.exe`、`.mcp.json` の `command` も Windows パス。VOICEVOX は Windows 版エンジン（HTTP API `:50021` は同一なので `synthesizer.py` は不変）。
- ADR-0003 / ADR-0004 の決定はプラットフォーム非依存のため不変。本 ADR は音声経路と実行環境だけを更新する。
