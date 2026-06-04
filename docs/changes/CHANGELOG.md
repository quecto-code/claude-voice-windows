# 変更ログ

> SDD 成果物（requirements / design / tasks）への全変更を時系列で残す append-only な履歴。
> 本体ドキュメントは常に最新。このログは「どう変えてきたか」を一望するためのもの。
> 1 変更 = 1 エントリ。過去エントリは書き換えず、誤りは取り消しエントリで訂正する。

| ID | 日付 | 起点 | 種別 | 対象 | 要約 | 影響範囲 | 状況 |
|---|---|---|---|---|---|---|---|
| CH-001 | 2026-05-30 | req | fix | Audio Quality NFR / player.py | 24kHz のまま WSLg PulseAudio に渡すことで生じていた再生音声の歪み（カリカリ・プツプツ）を、`sox --buffer 32768 + rate -v 48000`（バッファ拡大＋高品質リサンプリング）で解消。併せて「音声出力が歪みなく明瞭に再生される」Audio Quality NFR を新設 | **tasks 起点（player バグ修正）→ design（player/config 記述）→ requirements（音質 NFR）に遡上**。requirements §NFR / design §構成（player・config）/ 新タスク追加 `02-voice-output-speak/01-synthesize-and-play/03-improve-playback-quality`（実装済み `[x]`、既存 player タスクは不変）/ config.py・player.py・test_player.py | applied |
| CH-002 | 2026-05-31 | tasks→**ADR-0001 へ遡上**→req | add/modify | 対話モデル / ADR-0001 / ADR-0002・A-2 / CONTEXT / `/voice-chat` | 重い作業中の沈黙を、フォアグラウンド会話ループからバックグラウンド・サブエージェントへの作業委譲で解消する「委譲型準並行」を採用。会話を続けつつ重い作業を裏で進め、進捗・完了をターンの切れ目で音声報告。同時 1 ジョブ・単一スピーカー・破壊的操作はフォアグラウンド限定で A-2 を維持。読み上げを 3→4 役割（進捗報告を追加） | **「サブエージェントで速く」という tasks 起点の要求が、ターン制という不可逆判断（ADR-0001）に反するため ADR へ遡上**。ADR-0004 新設（0001 を supersede）／ADR-0002 に準並行下の安全ノート追記／CONTEXT のターン再定義・委譲/準並行/単一スピーカー追加・3→4 役割。下流（requirements 対話モデル＋進捗 FR → design 相互作用 → `/voice-chat` → 新タスク → 実装）まで適用済み。1 往復レイテンシ(#3) は対象外・別計測トラック | applied（ADR/req/design/tasks→実装まで main 着地。epic merge `a75d14e`、STATUS 21/21。#3=1往復レイテンシは別トラックで未着手） |
