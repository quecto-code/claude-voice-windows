# 設計

> 実装の設計（データモデル・インターフェース・相互作用・エラー方針・構成）と、その理由。
> 入力: [docs/requirements/requirements.md](../requirements/requirements.md), [CONTEXT.md](../CONTEXT.md), [docs/adr/](../adr/)
> 実装はこの設計に従う。

- 最終更新: 2026-05-28
- 対象スタック: Python 3.10/3.11 / MCP Python SDK / faster-whisper / vosk / VOICEVOX HTTP / sox（サブプロセス）
- 構成スタイル: フィーチャー分割（listen / speak の 2 サブパッケージ）

## ドキュメント索引

本プロジェクトは小規模なため、設計を本ファイル 1 本に統合する（構造・データモデル・インターフェース・相互作用を以下のセクションに畳む）。肥大化したら `structure.md` / `data-model.md` / `interfaces.md` / `interactions.md` に分割する。

- [#構成](#構成)
- [#データモデル](#データモデル)
- [#インターフェース](#インターフェース)
- [#相互作用・状態・エラー方針](#相互作用状態エラー方針)

## 設計方針

1. **サーバはステートレス。** 1 回のツール呼び出し中のみ状態を持つ。音声モード／ターン／silent 連続回数／終了コマンド判定／**進行中バックグラウンドジョブのハンドル 1 個**などの会話状態は、すべて `/voice-chat` の指示プロンプト（= Claude）側に住む（由来: [ADR-0004](../adr/0004-delegated-quasi-concurrency.md)。当初の [ADR-0001](../adr/0001-mcp-tool-driven-turn-based.md) を更新。委譲型準並行でもサーバはステートレスのまま堅持）。
2. **listen と speak は独立した 2 パイプライン。** 互いに参照しない。実装着手も独立に進められる（由来: [ADR-0003](../adr/0003-dual-engine-streaming-listen.md) と CONTEXT の語彙分離「listen 状態」と「読み上げの 4 役割」）。
3. **失敗は例外でなく status / error フィールドで表現する。** MCP ツール境界で例外を投げず、ループ全体は壊れない（由来: requirements の Reliability NFR）。
4. **CONTEXT の語彙は「サーバに住むもの」と「`/voice-chat` 側に住むもの」に意図的に振り分ける。** サーバはパイプライン成果物（録音・確定理由・文字起こし・合成音声）だけをモデル化し、対話レベルの語彙（音声モード／ターン／4 役割／終了コマンド）はコードに対応物を持たせない（[CONTEXT.md](../CONTEXT.md) と本設計のトレーサビリティ節を参照）。

## 全体像

claude-voice は Claude Code が stdio で起動する MCP サーバ。提供するのは **2 つの純粋関数ツール**だけ:

- `voice_listen()` — マイクから 1 つの発話を録音し、文字起こしして返す
- `voice_speak(text)` — テキストを VOICEVOX で合成して再生する

サーバの中身は 2 つの独立したパイプライン:

```
voice_listen()  ── listen.listen()  ── recorder ─→ (raw PCM bytes) ─→ transcriber  ─→ ListenResult
                                       │
                                       └─ sox 子プロセス + 単一読取スレッド + vosk(確定ワード検出)
                                          └─ 停止条件: silence / word / timeout

voice_speak(s)  ── speak.speak(s)   ── synthesizer ─→ (WAV bytes) ─→ player  ─→ SpeakResult
                                       └─ VOICEVOX /audio_query → /synthesis    └─ sox で pulse 再生
```

ループ・4 役割の使い分け・破壊的操作の許可要求などの「対話の振る舞い」は、すべて `/voice-chat` プロンプトが Claude に指示する形で実現される（サーバの責務外）。

対話モデルは**委譲型準並行**（[ADR-0004](../adr/0004-delegated-quasi-concurrency.md)）。フォアグラウンドの `/voice-chat` 会話ループが、重い作業を 1 つのバックグラウンド・サブエージェントに委譲して即 `voice_listen` に戻り、会話を続ける。ただし**これはすべて既存の 2 ツール（`voice_listen` / `voice_speak`）の呼び出しパターンとサブエージェント機構で実現され、サーバの API・構成・データモデルは一切変えない**。委譲・進捗・完了・破壊的操作の差し戻しのオーケストレーションは下記「相互作用」のオーケストレーション節（サーバ外）で扱う。

---

## 構成

### ツリー

```
claude-voice/
  pyproject.toml
  src/claude_voice/
    __init__.py
    __main__.py          # python -m claude_voice → server.run()
    server.py            # MCP ツール登録: voice_listen / voice_speak
    config.py            # しきい値・モデル名・VOICEVOX URL・speaker id
    types.py             # ListenResult / SpeakResult / FinalizeReason
    listen/
      __init__.py        # 公開: listen() パイプライン
      recorder.py        # sox 子プロセス + 読取スレッド + vosk + SIGTERM
      transcriber.py     # faster-whisper ラッパ
    speak/
      __init__.py        # 公開: speak(text) パイプライン
      synthesizer.py     # VOICEVOX HTTP クライアント
      player.py          # sox による pulse 再生
  tests/
    listen/
    speak/
```

### 各ディレクトリの責務

| パス | 責務 | 由来 |
|---|---|---|
| `server.py` | MCP ツール登録のみ。listen.listen / speak.speak を呼んで結果を返すだけの薄いラッパ | ADR-0001（ツール駆動） |
| `config.py` | しきい値（silence 1.2s・onset timeout 30s）、faster-whisper モデルサイズ、vosk モデルパス、確定ワード、VOICEVOX URL、speaker id、再生サンプルレート（既定 48000）・sox 再生バッファサイズを定数 + env 上書き | 「使いながら調整」運用 |
| `types.py` | `FinalizeReason` / `ListenResult` / `SpeakResult` の値オブジェクトのみ。葉 | パイプラインの境界用 |
| `listen/__init__.py` | `listen() -> ListenResult` を公開。recorder と transcriber を順に呼ぶオーケストレータ | CONTEXT「listen 状態 / 確定」 |
| `listen/recorder.py` | sox 子プロセス起動・読取スレッド・vosk 供給・確定ワード検出による SIGTERM・onset timeout | ADR-0003 + 質問2の決定 |
| `listen/transcriber.py` | faster-whisper（small/CUDA）に PCM を渡して文字起こし。確定ワード「以上」の末尾除去も担う | ADR-0003 |
| `speak/__init__.py` | `speak(text) -> SpeakResult` を公開。synthesizer と player を順に呼ぶ | CONTEXT「読み上げの 4 役割」（中身の判別はプロンプト側、再生はここ） |
| `speak/synthesizer.py` | VOICEVOX に POST `/audio_query` → `/synthesis`。WAV bytes を返す | TTS 選定 |
| `speak/player.py` | WAV bytes を `sox --buffer <SOX_BUFFER_BYTES> -t wav - -t pulseaudio default rate -v <PLAYBACK_SAMPLE_RATE>` で同期再生。24kHz のまま渡すと WSLg PulseAudio の内部リサンプリング/underrun で歪む（カリカリ・プツプツ）ため、バッファ拡大＋高品質リサンプリングで整える（Audio Quality NFR） | 音声経路（WSLg PulseAudio + sox） |
| `tests/listen/`, `tests/speak/` | pytest（独立ツリー、Python 慣習） | stack-patterns |

### 配置ルール（新しいコードの置き場所を即断するため）

- 新しい録音/STT 関連の関数は `listen/`、それ以外で TTS/再生は `speak/`。両方に跨るなら設計を見直す（基本は跨らない）。
- 入出力の境界をまたぐ型は `types.py` に置く。1 モジュール内で閉じる型はそのモジュール内に置く。
- 設定値（パラメータ）は **必ず `config.py`** に集約。各モジュールにマジックナンバーを置かない。
- 横断ユーティリティ用の `shared/` や `utils/` は**作らない**。listen と speak は sox の使い方が違う（入力＝raw PCM + silence エフェクト + パイプ読取、出力＝WAV を流し込んで再生）ので、共通化はかえって読みにくくなる。各モジュールが直接 `subprocess.Popen` する。

### 依存方向

```
server.py ──→ listen, speak, types, config
listen/__init__.py ──→ recorder, transcriber, types, config
speak/__init__.py  ──→ synthesizer, player, types, config
recorder, transcriber ──→ types, config
synthesizer, player   ──→ types, config
types, config         ──→ なし（葉）
```

- listen と speak は互いに参照しない（独立した 2 パイプライン）。
- 循環なし。`types` と `config` は誰にも依存しない葉。
- `server.py` は薄いラッパに留め、ロジックを書かない。

### スタック慣習との折り合い

- Python 慣習の `src/<package>/` レイアウトに従う（[stack-patterns.md] の Python 節）。
- `__init__.py` で公開 API を絞る（`listen/__init__.py` が `listen` 関数だけを公開、`speak/__init__.py` も同様）。recorder/transcriber 等の内部実装は外から触らせない。
- `claude_voice/__init__.py` は実行モジュールなので空でよい（ライブラリ用途を想定しない）。

---

## データモデル

このサーバはエンティティ（同一性を持つ概念）を持たない。流れるのは**パイプラインの中間値（値オブジェクト）**のみ。

### 値オブジェクト

#### `FinalizeReason`（enum）
録音停止の理由。
- `silence` — sox の silence エフェクトが自然停止した（無音 1.2 秒検出）
- `word` — vosk が確定ワード「以上」を検出し SIGTERM で停止
- `timeout` — 発話開始（onset）が onset_timeout（既定 30 秒）以内に観測されず kill

#### `ListenResult`
`voice_listen()` の戻り値。
- `transcript: str` — 文字起こし結果。`status != "ok"` のときは空文字
- `status: Literal["ok", "silent", "unintelligible"]`
  - `ok` — 文字起こしに成功（reason=silence or word、transcribe 結果が非空）
  - `silent` — reason=timeout（Edge Case 1/2 の起点）
  - `unintelligible` — 音は拾ったが transcribe が空・極端に短い・失敗（Requirement 6 の起点）

#### `SpeakResult`
`voice_speak(text)` の戻り値。
- `ok: bool`
- `error: str | None` — 失敗時の理由（VOICEVOX 接続不可、合成失敗、再生失敗 等）

### 関数間を流れる生データ

- 録音 PCM: `bytes`（16kHz / mono / s16le / ヘッダなし raw）。recorder 内部で蓄積し、transcriber に渡す
- 合成 WAV: `bytes`（VOICEVOX 既定の形式そのまま）。synthesizer から player に渡す

### CONTEXT.md 用語との対応

| CONTEXT 用語 | コードでの表現 |
|---|---|
| 確定 | `FinalizeReason` enum と recorder の停止条件 |
| 確定ワード | `config.FINALIZE_WORD`（既定「以上」）。recorder の vosk スポッティングが参照 |
| listen 状態 | recorder の「sox 起動中・PCM を読みながら vosk に供給している間」。コード上の型としては持たず関数の実行中スコープで表現 |
| 読み上げの 4 役割 | **サーバには対応物を置かない**（意図）。4 役割の使い分けは `/voice-chat` プロンプト側で Claude が判断 |
| 音声モード / ターン / 終了コマンド | **同上**。`/voice-chat` プロンプト側のループ指示と意味解釈 |

### 不変条件

- `ListenResult.status == "ok"` ⇒ `transcript` は非空
- `ListenResult.status != "ok"` ⇒ `transcript == ""`
- `SpeakResult.ok == True` ⇒ `error is None`
- `SpeakResult.ok == False` ⇒ `error` は非空文字列

---

## インターフェース

### MCP ツール（外部公開）

```python
def voice_listen() -> ListenResult: ...
def voice_speak(text: str) -> SpeakResult: ...
```

requirements の対応:
- `voice_listen` ← FR-2（発話を指示として受け取る）
- `voice_speak` ← FR-3（伝えるべき応答を音声で読み上げる）／FR-4（処理完了通知）／A-2（許可要求の発声）

### サブパッケージの公開 API（内部）

```python
# claude_voice/listen/__init__.py
def listen() -> ListenResult: ...

# claude_voice/speak/__init__.py
def speak(text: str) -> SpeakResult: ...
```

`server.py` はこれらを 1 行で呼ぶだけ。

### 各モジュールの責務 IF（内部実装、外には見せない）

```python
# listen/recorder.py
def record(finalize_word: str,
           silence_sec: float,
           onset_timeout_sec: float) -> tuple[bytes, FinalizeReason]:
    """sox + vosk を回し、確定 PCM と理由を返す。例外は投げない（失敗時は (b"", FinalizeReason.timeout) など）"""

# listen/transcriber.py
def transcribe(pcm: bytes) -> str | None:
    """16kHz/mono/s16le の生 PCM を faster-whisper に渡す。失敗・空入力で None"""

# speak/synthesizer.py
def synthesize(text: str, speaker: int) -> bytes | None:
    """VOICEVOX で WAV bytes を生成。失敗で None"""

# speak/player.py
def play(wav: bytes) -> bool:
    """sox で同期再生。成功 True / 失敗 False（例外は投げない）"""
```

### 公開境界の線引き

- 外（MCP/Claude）が触ってよいのは `voice_listen` と `voice_speak` だけ
- プロジェクト内（テストや他モジュール）が触ってよいのは `listen.listen` と `speak.speak` だけ
- recorder / transcriber / synthesizer / player は実装詳細。直接は呼ばない（テストはこれらも単体で叩く）

### 外部 API（VOICEVOX）

- `POST {VOICEVOX_URL}/audio_query?text=...&speaker={id}` → audio_query JSON
- `POST {VOICEVOX_URL}/synthesis?speaker={id}` body: audio_query JSON → WAV bytes
- 既定 `VOICEVOX_URL = http://127.0.0.1:50021`（`config.py` で env 上書き可）

### ドメインイベント

なし（ステートレス・同期呼び出し）。

---

## 相互作用・状態・エラー方針

### 主要フロー: listen（← FR-2 / FR-6 / FR-8 / FR-9 / Edge1 / Edge2）

```
voice_listen()
└─ listen.listen():
    pcm, reason = recorder.record(finalize_word=config.FINALIZE_WORD,
                                   silence_sec=config.SILENCE_SEC,
                                   onset_timeout_sec=config.ONSET_TIMEOUT_SEC)
    if reason == FinalizeReason.timeout:
        return ListenResult("", "silent")
    text = transcriber.transcribe(pcm)
    if not text:
        return ListenResult("", "unintelligible")
    text = strip_finalize_word(text, config.FINALIZE_WORD)
    return ListenResult(text, "ok")
```

recorder.record の内部:
1. `sox -t pulseaudio default -r 16000 -c 1 -t raw -e signed -b 16 - silence 1 0.05 1% 1 {silence_sec} 1%` を起動（stdout=PIPE）。
2. 単一の読取スレッドが sox.stdout から 4KB チャンクで読む。
3. 各チャンクを (a) 全 PCM バッファに `append`、(b) vosk Recognizer に `AcceptWaveform`。
4. vosk の partial に `finalize_word` を検出 → sox に SIGTERM、`reason=word`。
5. sox が自然終了（無音検出） → `reason=silence`。
6. onset timer：最初のチャンクに「音声」と見なせる振幅が見つかる前に `onset_timeout_sec` が経過 → sox を kill、`reason=timeout`、空 bytes を返す。
7. 読取スレッド合流後、`(bytes, reason)` を返す。

### 主要フロー: speak（← FR-3 / FR-4 / A-2）

```
voice_speak(text)
└─ speak.speak(text):
    if not text:
        return SpeakResult(ok=True, error=None)
    wav = synthesizer.synthesize(text, speaker=config.SPEAKER_ID)
    if wav is None:
        return SpeakResult(ok=False, error="voicevox synthesis failed")
    ok = player.play(wav)
    return SpeakResult(ok=ok, error=None if ok else "playback failed")
```

連続呼び出しの再生重なりは、Python レベルのモジュールロック（`speak/_lock.Lock()`）で直列化する（player.play の入口で取得）。

### オーケストレーション: 委譲型準並行（← FR-10 / FR-11 / A-2 / Edge2、[ADR-0004](../adr/0004-delegated-quasi-concurrency.md)）

これは `/voice-chat` プロンプト側（= Claude）の振る舞いであり、**サーバの責務外**。ただし全体の相互作用を 1 箇所で読めるよう設計として記す。**新しいサーバ API は要らない** — 既存の `voice_listen` / `voice_speak` と Claude Code のバックグラウンド・サブエージェント機構だけで成立する。

```
フォアグラウンド /voice-chat 会話ループ（ターンを回す）
└─ voice_listen() の transcript を解釈し分岐:
    ├─ 軽い作業／会話        → その場で処理し voice_speak（事前宣言・事後報告）
    └─ 重い作業             → バックグラウンド・サブエージェントに委譲（同時 1 ジョブまで）
                              → 即 voice_listen に戻る（FR-10: 完了を待たず会話継続）

ジョブ走行中の各ターン:
  - voice_listen が "ok"      → 新しい発話として会話継続（走行中ジョブに新指示が来たら
                                「終わってから／止めて差し替え」を確認。暗黙の並列起動はしない）
  - voice_listen が "silent"  → 進捗報告を voice_speak（FR-11。既存 onset timeout タイマを転用）。
                                ★ジョブ走行中は Edge2 の silent 自動終了を抑止する
  - 子ジョブ完了の通知        → 次のターンの切れ目で事後報告を voice_speak
```

要点:
- **単一スピーカー**: `voice_speak` / `voice_listen` を呼ぶのは**フォアグラウンドのみ**。バックグラウンドジョブは voice ツールを呼ばず、結果・進捗を**テキストで親に返す**。音声の混線とターンの濁りを防ぐ。
- **完了・進捗はターンの切れ目で**（瞬時割り込みではない＝「準」並行）。進捗の粒度は `config.ONSET_TIMEOUT_SEC`（既存）に従い ~数十秒。粗さは運用で調整する既知のトレードオフ（[ADR-0004](../adr/0004-delegated-quasi-concurrency.md)）。
- **破壊的操作の差し戻し**: バックグラウンドジョブは破壊的・不可逆な操作を**実行しない**。到達したら親に差し戻し、親が A-2 のブロッキング確認（`voice_speak` 許可要求 → 直後の `voice_listen` で「はい」待ち）を経て、肯定なら親が実行（または許可付きで再委譲）。これにより [ADR-0002](../adr/0002-skip-permissions-with-voice-confirmation.md) の安全不変条件を緩めずに保つ。

### 状態遷移

- recorder の内部実行ステートは `waiting_onset → recording → finalized(silence|word|timeout)` の 3 状態（コードでは局所変数で表現）。
- それ以外にステートを持つエンティティはない（ステートレス方針）。
- requirements の WHEN/WHILE は **`/voice-chat` プロンプト側**で状態遷移として扱う（サーバの範囲外）。

### 失敗パスとエラーハンドリング方針

| 失敗モード | 発生箇所 | サーバの扱い |
|---|---|---|
| マイクデバイスを開けない | recorder（sox 起動失敗） | `(b"", FinalizeReason.timeout)` を返す ⇒ ListenResult `silent` 相当（Claude は継続通知へ） |
| vosk モデル未配置 | recorder | 同上（`silent` 相当）＋ stderr にログ |
| 発話なし | recorder | `FinalizeReason.timeout` ⇒ ListenResult `silent`（Edge1/2） |
| 雑音のみ・極短発話 | transcriber | `transcribe → None` ⇒ ListenResult `unintelligible`（FR-6） |
| faster-whisper 推論失敗 | transcriber | 同上 `unintelligible` ＋ stderr ログ |
| VOICEVOX 接続不可 / 5xx | synthesizer | `wav=None` ⇒ SpeakResult `{ok:false, error:"voicevox synthesis failed"}` |
| 再生失敗（sox エラー） | player | `False` ⇒ SpeakResult `{ok:false, error:"playback failed"}` |

原則:
- **どの境界でも例外を MCP に返さない**。捕捉して status / error に変換する（Reliability NFR）。
- stderr へのロギングは積極的に行う（Claude Code の MCP ログで読める）。voice モードでは画面を見られないので、後追い調査の唯一の手段。
- リトライは行わない（呼び出し側＝Claude がループで再 listen / 再 speak する設計）。冪等性も問題にならない（録音・再生は副作用が音響だけ）。

---

## 主要な設計判断とその理由

### 1. サーバはステートレスにする
- **採用**: 1 ツール呼び出し内のみ状態を持つ。会話状態は `/voice-chat` プロンプトに住む
- **検討した別案**: (a) セッションオブジェクトを `voice_session_start/end` で持つ、(b) silent カウントをサーバが管理
- **理由**: ADR-0001 で「Claude がループを回す」を選んだ時点で状態の持ち主は Claude。サーバが状態を持つと二重管理になり乖離リスク。MCP ツールの自然な形（純粋関数）に揃う
- **関連 ADR**: [ADR-0001](../adr/0001-mcp-tool-driven-turn-based.md)

### 2. listen の並行性: sox + 単一読取スレッド + vosk + SIGTERM
- **採用**: sox サブプロセスで raw PCM 16kHz/mono/s16le に正規化し、単一スレッドが stdout を読みながら vosk に逐次供給。確定ワードで SIGTERM、無音は sox の silence エフェクトで自然停止、onset timeout はタイマで kill
- **検討した別案**: (a) asyncio + asyncio.subprocess、(b) sounddevice/PortAudio で Python 直叩き、(c) tempfile に書き出してから vosk
- **理由**:
  - sox 自身が無音検出を持つので Python 側の実装が最小
  - PCM raw に揃えれば WAV ヘッダのストリーミング解析が不要
  - 単一スレッドで競合・ロック不要
  - tempfile 経由は録音中の確定ワード検出ができず ADR-0003 の意義が消える
- **関連 ADR**: [ADR-0003](../adr/0003-dual-engine-streaming-listen.md)

### 3. listen / speak を完全独立な 2 サブパッケージにする（共有 sox ヘルパは作らない）
- **採用**: `src/claude_voice/listen/` と `src/claude_voice/speak/` を兄弟配置し、互いに参照しない。`shared/audio/` 等の共有モジュールも作らない
- **検討した別案**: (a) フラット 1 ディレクトリ（境界が消える）、(b) `domain/application/infrastructure` 3 層レイヤー（過剰）、(c) `shared/audio/sox.py` で sox サブプロセス起動を共通化
- **理由**:
  - listen と speak は sox の使い方が違う（入力＝raw PCM + silence + パイプ読取、出力＝WAV を流し込んで再生）。共通化は抽象を増やすだけ
  - 独立配置は speak の先行開発（Epic 02 先行）を自然に支える
  - ドメインを「叫ぶ」配置（CONTEXT「listen 状態」「読み上げの 4 役割」が物理ツリーに現れる）

### 4. 失敗を例外でなく status / error で表現する
- **採用**: MCP ツール境界では例外を投げない。ListenResult.status と SpeakResult.error で表現
- **検討した別案**: 例外を MCP 越しに送る／途中で raise する
- **理由**: requirements の Reliability NFR「単発失敗でループ全体がクラッシュしない」を境界で確実に守るため。Claude が status を見て分岐する設計と整合
- **関連 FR**: Reliability NFR / FR-6（unintelligible 分岐）

### 5. 読み上げの 4 役割／音声モード／ターン／終了コマンドをサーバに置かない
- **採用**: 対話レベルの語彙はすべて `/voice-chat` プロンプトに住ませる。サーバには対応するクラス・関数・状態を作らない。読み上げの役割は **4 つ**（事前宣言・進捗報告・事後報告・許可要求）で、`voice_speak` を呼ぶのはフォアグラウンドのみ（**単一スピーカー**）
- **検討した別案**: サーバに `SpeakRole` enum を作り `voice_speak(text, role=...)` のように渡させる／バックグラウンドジョブにも `voice_speak` を許す
- **理由**: 役割の判断は「Claude が何を言うか決める」プロンプト工学の領域で、サーバ側のロジックではない。サーバはどの役割の音声でも同じく合成・再生するだけ。型に出すと Claude にとっての意味づけと二重管理になる。バックグラウンドジョブにも喋らせると音声が混線しターンが濁るため、音声出力はフォアグラウンドに一本化する。意図的に対応物を作らない方が「叫ぶ」設計になる
- **関連 ADR**: [ADR-0004](../adr/0004-delegated-quasi-concurrency.md)（進捗報告の追加・単一スピーカー）／[ADR-0001](../adr/0001-mcp-tool-driven-turn-based.md)

### 6. パーミッション機構をサーバ側に置かない（破壊的操作の許可は `/voice-chat` 側）
- **採用**: サーバには破壊的操作の判定や許可フローを実装しない。`voice_listen` / `voice_speak` を素直に使うだけ。委譲型準並行では**破壊的操作はフォアグラウンドでのみ実行**し、バックグラウンドジョブは破壊的操作を実行せず親に差し戻す
- **検討した別案**: サーバに「許可要求モード」のツールを追加する／バックグラウンドジョブ自身に音声確認させる／委譲前に一括事前承認する
- **理由**: ADR-0002 の通り Claude Code は `--dangerously-skip-permissions` 前提で、許可判断・確認フローは Claude の `/voice-chat` プロンプト側に住む。サーバを汚染しない。準並行では走行中ジョブを音声で即時 kill できないため「割り込めるから事前確認は任意」というモデル B の論理は採らず、A-2 のブロッキング確認を破壊的操作に対して維持する（差し戻し→親が確認）
- **関連 ADR**: [ADR-0002](../adr/0002-skip-permissions-with-voice-confirmation.md) / [ADR-0004](../adr/0004-delegated-quasi-concurrency.md)

### 7. 委譲型準並行のオーケストレーションはプロンプトに住み、サーバ API は変えない
- **採用**: 重い作業をバックグラウンド・サブエージェント（同時 1 ジョブ）に委譲し会話を継続する委譲型準並行を、既存の `voice_listen` / `voice_speak` と Claude Code のサブエージェント機構だけで実現する。サーバの API・構成・データモデルは不変
- **検討した別案**: (a) ターン制維持（沈黙の待ちが残る）、(b) 外部プロセス駆動の完全モデル B（実装が重くリスク高）、(c) サーバに「ジョブ管理ツール」を足してサーバが進行中ジョブを保持する
- **理由**: 会話状態はフォアグラウンドが唯一持つ（設計判断 1 の堅持）。サーバにジョブ状態を持たせると二重管理になり、ステートレス方針が崩れる。完了・進捗はターンの切れ目で届く（瞬時割り込みではない）ため「準」並行に留め、実装と安全モデルの複雑化を避ける
- **関連 ADR**: [ADR-0004](../adr/0004-delegated-quasi-concurrency.md)

---

## トレーサビリティ

### CONTEXT 用語 → モデル・配置先

| CONTEXT 用語 | コード上の対応 | 配置 |
|---|---|---|
| 音声モード | — | `/voice-chat` プロンプト側（サーバ外） |
| ターン | — | 同上 |
| listen 状態 | `recorder.record` の実行スコープ | `src/claude_voice/listen/recorder.py` |
| 確定 | `FinalizeReason` enum と recorder の停止条件 | `types.py` + `recorder.py` |
| 確定ワード | `config.FINALIZE_WORD`（既定「以上」） | `config.py`（参照は recorder） |
| 終了コマンド | — | `/voice-chat` プロンプト側で意味解釈 |
| 読み上げの 4 役割（進捗報告を追加） | — | `/voice-chat` プロンプト側（単一スピーカー） |
| 委譲 / バックグラウンドジョブ | — （Claude Code のサブエージェント機構。サーバに対応物なし） | `/voice-chat` プロンプト側 |
| 委譲型準並行 | — | `/voice-chat` プロンプト側（オーケストレーション） |
| 単一スピーカー | `speak/_lock` による再生直列化が下支え。呼び出し主体の限定はプロンプト側 | `/voice-chat` プロンプト側 + `speak/__init__.py` |

### 主要 FR → ユースケース・配置先

| FR / Edge | 対応 | サーバ内の配置 |
|---|---|---|
| FR-1（モード開始） | `/voice-chat` 実行 | サーバ外 |
| FR-2（発話を指示として受け取る） | `voice_listen()` | `server.py` → `listen/__init__.py` |
| FR-3（応答を音声で読み上げ） | `voice_speak(text)` | `server.py` → `speak/__init__.py` |
| FR-4（完了通知） | 事後報告として `voice_speak` を呼ぶ（プロンプト） | サーバ外（呼び方の指示） |
| FR-5（伝えるべき内容のみ） | プロンプト側で Claude が要約を選ぶ | サーバ外 |
| FR-6（聞き取れない） | ListenResult `unintelligible` → プロンプトが再 listen | 判定: `transcriber.py`／分岐: サーバ外 |
| FR-7（モード終了） | プロンプト側で意味解釈 → ループ離脱 | サーバ外 |
| FR-8（沈黙確定） | sox `silence` エフェクト | `recorder.py` |
| FR-9（確定ワード） | vosk + SIGTERM | `recorder.py` |
| Edge1（継続通知） | ListenResult `silent` → プロンプト | 判定: `recorder.py`／分岐: サーバ外 |
| Edge2（自動終了） | 同上 + プロンプト | 同上 |
| A-2（破壊的操作の事前確認） | `voice_speak`（許可要求）+ `voice_listen` で「はい」待ち。委譲型準並行では破壊的操作はフォアグラウンド限定、子は親に差し戻し | プロンプト側（[ADR-0002](../adr/0002-skip-permissions-with-voice-confirmation.md) / [ADR-0004](../adr/0004-delegated-quasi-concurrency.md)） |
| FR-10（作業進行中も新発話を受付・会話継続） | 重い作業を委譲して即 `voice_listen` に戻る | プロンプト側（オーケストレーション節） |
| FR-11（作業進行中の沈黙時に進捗を音声通知） | ジョブ走行中の `silent`（onset timeout）ごとに `voice_speak`（進捗報告）。Edge2 自動終了は抑止 | 判定: `recorder.py`（silent）／分岐・進捗: プロンプト側（[ADR-0004](../adr/0004-delegated-quasi-concurrency.md)） |
| Reliability NFR | 例外を投げず status / error で表現 | 全モジュール共通方針 |
| Performance NFR P95<3s | faster-whisper small + CUDA / sox silence 1.2s | `config.py`（しきい値）+ `transcriber.py` |
| Performance NFR < 2s | VOICEVOX + GPU / sox 即時再生 | `synthesizer.py` + `player.py` |

### ADR → 設計への反映

| ADR | 設計への反映 |
|---|---|
| [ADR-0004](../adr/0004-delegated-quasi-concurrency.md) | 委譲型準並行のオーケストレーション（設計判断 7）・進捗報告で読み上げ 4 役割（判断 5）・破壊的操作はフォアグラウンド限定で差し戻し（判断 6）・会話状態に進行中ジョブのハンドルを追加（判断 1）。サーバ API/構成/データモデルは不変 |
| [ADR-0001](../adr/0001-mcp-tool-driven-turn-based.md)（ADR-0004 が supersede） | ツール 2 つ（voice_listen / voice_speak）のみ・サーバステートレス・ループは `/voice-chat` 側（この骨格は ADR-0004 でも有効。ターン制の排他性のみ ADR-0004 で更新） |
| [ADR-0002](../adr/0002-skip-permissions-with-voice-confirmation.md) | サーバには許可機構を置かない（プロンプト側）。設計判断 6 で明記 |
| [ADR-0003](../adr/0003-dual-engine-streaming-listen.md) | listen 内で `recorder.py`（vosk ストリーミング）と `transcriber.py`（faster-whisper 確定）を分離 |

---

## TBD / 保留

特になし。設計を左右する未確定 ADR 級判断はなし。

実装段階で詰める運用パラメータ（しきい値・話者 id・モデルサイズ）はすべて `config.py` に集約してあるので、設計には影響しない。
