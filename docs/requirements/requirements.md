# Claude Code 音声入出力インターフェース（claude-voice）

**優先度:** Medium
**対象ユーザー:** Claude Code を日常的に使う開発者（主に作者自身）
**対象モジュール:** 新規 MCP サーバ（claude-voice）

## Problem

### 現在起きていること

Claude Code はキーボードでの入出力が前提のため、以下の場面で使えない/使いづらい:

- **ハンズフリーで使えない**: 料理中・歩行中・別作業中など、キーボードに向かえない場面で指示を出せない
- **長文入力が面倒**: 仕様説明やアイデア出しなど、口で説明したほうが速い指示をタイプするのが億劫
- **タイピングが負担**: 入力そのものが負担になる場面がある
- **処理完了が分からない**: Claude Code の出力を待つ間に別作業をしたいが、いつ出力が完了したか分からない。通知設定でもラグがあり、音声で即座に知りたい

### なぜ問題なのか

キーボード前提であるために、Claude Code を使える場面が物理的に席に着いている時間に限定され、活用機会を取りこぼしている。

**Why Now:** 仕事の効率化欲求。また Claude Code Pro プランの使用上限まで活用できておらず、利用機会を増やしたい。

**Expected Impact:**
- キーボードに触れずに Claude Code への指示〜応答受領まで完結できる
- 別作業中でも Claude Code の処理完了を音声で即座に把握できる（通知ラグの解消）
- Claude Code の日常的な使用を促進する

## Functional Requirements

### User Story

**As a** Claude Code を日常的に使う開発者（キーボードに向かえない/向かいたくない場面がある）
**I want** 音声で Claude Code に指示を出し、その応答や処理完了を音声で受け取りたい
**So that** ハンズフリーかつ長文タイプの手間なく、別作業をしながらでも Claude Code を使えるようにする

### Requirements

#### Requirement 1
WHEN ユーザが音声モードを開始する
THE SYSTEM SHALL ユーザの音声指示の受け付けを開始する

#### Requirement 2
WHEN ユーザが音声で指示を話し終える
THE SYSTEM SHALL その発話内容を指示として受け取り、処理を開始する

#### Requirement 3
WHEN Claude Code がユーザに伝えるべき応答を生成する
THE SYSTEM SHALL その内容を音声で読み上げる

#### Requirement 4
WHEN Claude Code が一連の処理を完了する
THE SYSTEM SHALL 処理が完了したことを音声でユーザに通知する

#### Requirement 5
THE SYSTEM SHALL ユーザに伝える必要があると Claude が判断した内容のみを音声で読み上げる

#### Requirement 6
IF ユーザの音声を聞き取れない、または指示として認識できない
THEN THE SYSTEM SHALL 聞き取れなかった旨を音声で伝え、再度の発話を促す

#### Requirement 7
WHEN ユーザが音声モードの終了を指示する
THE SYSTEM SHALL 音声指示の受け付けを停止し、ターン制ループを終了する

#### Requirement 8
WHEN ユーザの発話が一定時間途切れる（無音になる）
THE SYSTEM SHALL その時点までの発話を 1 つの指示として確定する

#### Requirement 9
WHEN ユーザが特定の終了ワードを発話する
THE SYSTEM SHALL その時点までの発話を 1 つの指示として確定し、処理を開始する

> Requirement 1〜9 は対話モデルに依存しない共通要件。採用した対話モデル（委譲型準並行）固有の要件は後述「対話モデル」節に示す。

### Edge Cases

#### Edge Case 1
WHILE 音声入力待ち WHEN 一定時間ユーザの発話がない
THE SYSTEM SHALL 音声モードが継続中であることを音声で通知する

#### Edge Case 2
WHILE 音声入力待ち WHEN 継続通知後さらに一定時間発話がない
THE SYSTEM SHALL 音声モードを自動的に終了する

> ただし時間のかかる作業が進行中の場合、ユーザは結果を待って黙っているだけなので**自動終了しない**（[ADR-0004](../adr/0004-delegated-quasi-concurrency.md)）。この抑止は下記 Requirement 11（進捗通知）と対になる。

### 対話モデル（委譲型準並行に確定 — [ADR-0004](../adr/0004-delegated-quasi-concurrency.md)）

ユーザが**処理中・読み上げ中に割り込めるか**で対話モデルが分かれる。当初はモデル A（ターン制）/ モデル B（割り込み可能）を両論併記し design に委ねていたが、**[ADR-0004](../adr/0004-delegated-quasi-concurrency.md) で第 3 の「委譲型準並行」を採用**した。

委譲型準並行では、時間のかかる作業はユーザを待たせず裏で進み、**その間もユーザは会話や新しい指示を続けられる**。一方、**進行中の処理を音声で即座に中断（barge-in＝割り込んで止める）ことはできない**（モデル B の B-1 / B-2 は採らない）。割り込んで止めたい場合は作業の完了を待つ。

採用モデルは上記 Requirement 1〜9 / Edge Case 1〜2（Edge Case 2 は作業進行中は抑止）を満たし、加えて以下を満たす。

#### 採用モデルが引き継ぐ要件（旧モデル A 由来）

##### Requirement A-1
WHEN システムがユーザの音声入力を受け付ける状態（listen）に入る
THE SYSTEM SHALL その状態に入ったことを音声でユーザに伝える

##### Requirement A-2
IF Claude Code が破壊的操作を実行しようとする
THEN THE SYSTEM SHALL 実行前にその操作内容を音声でユーザに伝え、実行してよいかを音声で確認する

> A-2 は安全策。委譲型準並行でも進行中の処理を音声でとっさに止められないため、破壊的操作の事前確認は引き続き**必須**（[ADR-0002](../adr/0002-skip-permissions-with-voice-confirmation.md) / [ADR-0004](../adr/0004-delegated-quasi-concurrency.md)）。

#### 委譲型準並行に固有の要件

##### Requirement 10
WHILE 時間のかかる作業が進行中 WHEN ユーザが新たに発話する
THE SYSTEM SHALL その発話を受け付け、作業の完了を待たずに応答・会話を継続する

##### Requirement 11
WHILE 時間のかかる作業が進行中 WHEN 一定時間ユーザの発話がない
THE SYSTEM SHALL その作業が進行中であることを音声でユーザに伝える

> Requirement 11 は「重い作業中の沈黙をなくし、進捗を音声で知らせてほしい」というユーザ要望を満たす。進捗通知の間隔（粒度）は実装で調整する運用パラメータ（[ADR-0004](../adr/0004-delegated-quasi-concurrency.md)）。

#### モデル B（不採用 — 記録として保持）

> [ADR-0001](../adr/0001-mcp-tool-driven-turn-based.md) / [ADR-0004](../adr/0004-delegated-quasi-concurrency.md) により、処理中の真の割り込み（barge-in）を行うモデル B は**不採用**。以下は検討記録として ID を保持したまま残す。委譲型準並行は「処理中も入力を受け付ける」体験の一部を、進行中処理の即時停止（B-1 / B-2 の中断）なしに Requirement 10 で実現する。

##### Requirement B-1（不採用）
WHILE システムが音声を読み上げている WHEN ユーザが話し始める
THE SYSTEM SHALL 読み上げを中断し、ユーザの発話を新しい指示として受け付ける

##### Requirement B-2（不採用）
WHILE Claude Code が処理を実行している WHEN ユーザが音声で入力を始める
THE SYSTEM SHALL 実行中の処理を停止する

##### Requirement B-3（不採用）
WHEN ユーザの新しい音声入力が完了する
THE SYSTEM SHALL 停止した処理を再開すべきか判断する

##### Requirement B-4（不採用）
IF 停止した処理を再開すべきか曖昧である
THEN THE SYSTEM SHALL ユーザに音声で確認する

## Non-Functional Requirements

### Performance

- [ ] 発話確定から復唱または処理開始までの待ち時間が P95 < 3 秒
- [ ] Claude の応答生成完了から読み上げ開始までの遅延が < 2 秒

### Reliability

- [ ] 音声認識/合成が単発で失敗しても、その指示のみ失敗として扱い、音声モードのループは継続する（ループ全体がクラッシュしない）

### Audio Quality

- [ ] 読み上げ音声が歪み・ノイズなく明瞭に再生される（再生環境のサンプルレート変換やバッファ不足で音割れ・プツプツが乗らない）

### その他

- Security / Scalability / Accessibility / Internationalization: 該当なし（個人・ローカル・認証なしのため）

## Success Metrics

### Technical

- [ ] 音声入力がテキスト化され Claude Code への指示として伝達される
- [ ] Claude Code の応答テキストが音声で再生される
- [ ] 処理完了が音声で通知される

### Business

- [ ] 作者自身が音声経由で Claude Code を日常的に利用する（週 N 回以上）

## Dependencies

- MCP サーバ連携に対応した Claude Code（Opus 4.7 利用前提）
- マイク入力・音声出力が利用できる実行環境（**Windows ネイティブ**。sox の `waveaudio` 経由。当初の WSL2 前提は [ADR-0005](../adr/0005-windows-native-audio-path.md) で更新）
- 無料の STT / TTS 手段（具体的な選定は design 段階）
- 既存 ADR: なし（新規プロジェクト）

## Out of Scope

- ホットワードによる常時バックグラウンド待ち受け起動（開始は手動で行う）
- 複数ユーザ・マルチセッション対応
- 認証・認可
- 日本語以外の多言語対応（日本語前提）
- GUI / モバイルアプリ
- Slack・メール等への外部通知連携
