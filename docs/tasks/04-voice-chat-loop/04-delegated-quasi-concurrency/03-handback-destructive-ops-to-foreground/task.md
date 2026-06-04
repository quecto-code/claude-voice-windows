---
type: task
title: 破壊的操作のフォアグラウンド差し戻しを組み込む
label: must-have
depends_on:
  - 04-voice-chat-loop/04-delegated-quasi-concurrency/01-delegate-heavy-work-and-continue-loop
---

## 背景

親 Story `04-voice-chat-loop/04-delegated-quasi-concurrency` の一部。委譲型準並行では走行中ジョブを音声で即時に止められないため、破壊的操作はフォアグラウンドに閉じ込めて A-2 のブロッキング確認を維持する。バックグラウンドジョブが破壊的・不可逆な操作に到達したら実行せず親に差し戻し、親が既存の許可要求フローを経て実行する（[ADR-0004](../../../../adr/0004-delegated-quasi-concurrency.md) / [ADR-0002](../../../../adr/0002-skip-permissions-with-voice-confirmation.md)、[design.md 設計判断 6](../../../../design/design.md#主要な設計判断とその理由)）。

親 Story: 04-voice-chat-loop/04-delegated-quasi-concurrency

## 受入条件

- [x] `.claude/commands/voice-chat.md` に、バックグラウンドジョブは破壊的・不可逆な操作を**実行せず親（フォアグラウンド）に差し戻す**手順が明記されている
- [x] 差し戻しを受けた親が、既存の A-2 ブロッキング確認（許可要求 `voice_speak` → `voice_listen` で「はい」待ち）を経て、肯定でのみ実行する（または許可付きで再委譲する）手順がある
- [x] 「割り込めるから事前確認は任意」というモデル B の論理は採らず、破壊的操作の事前確認は引き続き必須と整合している
- [x] 既存「破壊的操作の音声確認 (許可要求 / A-2)」節は保全したまま、委譲型準並行での差し戻しを追記している（既存の受入を壊さない）

## 仕様詳細

### 変更ファイル

- `.claude/commands/voice-chat.md` — 「破壊的操作の音声確認 (許可要求 / A-2)」節に「委譲型準並行での扱い」を追記（バックグラウンドジョブは破壊的操作を実行せず親に差し戻す → 親が A-2 確認 → 肯定なら親が実行 or 許可付き再委譲。破壊的操作はフォアグラウンド限定）
- `tests/test_voice_chat_command.py` — 04/04/03 用の grep テストを追加（差し戻し手順・親が A-2 確認・破壊的操作はフォアグラウンド限定・事前確認は必須維持の各文言）

### 関数 / API シグネチャ

該当なし（プロンプト記述）

### バリデーション・エラー処理

- 確認が取れない／曖昧なら実行しない（既存の安全側に倒す方針を踏襲）

### エッジケース

- ジョブの大半は非破壊（編集・検索・テスト・ビルド）なので差し戻しは点的。差し戻し中はそのジョブを中断扱いにし、確認後に再開／中止を決める

## 依存関係

- 前提: 04-voice-chat-loop/04-delegated-quasi-concurrency/01-delegate-heavy-work-and-continue-loop
- ブロックする: なし

理由: 委譲＝バックグラウンドジョブの概念ができてから、そのジョブの破壊的操作の扱いを足す。

## スコープ外

- 既存の A-2 確認フロー自体の再実装（04/03/01 で完了済み。本タスクは差し戻し経路の追記のみ）
- サーバ側のパーミッション機構（バイパス前提・設計判断 6）

## 補足

- [ADR-0004](../../../../adr/0004-delegated-quasi-concurrency.md) / [ADR-0002](../../../../adr/0002-skip-permissions-with-voice-confirmation.md) / requirement A-2
- 関連設計: [design.md#相互作用状態エラー方針（オーケストレーション: 委譲型準並行 / 破壊的操作の差し戻し）](../../../../design/design.md#相互作用状態エラー方針) / [design.md 設計判断 6](../../../../design/design.md#主要な設計判断とその理由)
- 変更履歴: docs/changes/CHANGELOG.md CH-002
