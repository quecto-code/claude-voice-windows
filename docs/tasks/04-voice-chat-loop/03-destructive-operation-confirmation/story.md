---
type: story
title: 破壊的操作を音声で確認する
label: must-have
depends_on:
  - 04-voice-chat-loop/01-voice-chat-command-and-loop
---

## 背景・目的

音声モードは `--dangerously-skip-permissions` 前提でハーネスのキーボード承認を出さない。その代償として、Claude が破壊的・不可逆な操作の前に音声で許可を求め、「はい」でのみ実行する安全弁を設ける（[ADR-0002](../../../adr/0002-skip-permissions-with-voice-confirmation.md)、requirement A-2、[design.md 設計判断 6](../../../design/design.md#主要な設計判断とその理由)）。

サーバ側にはパーミッション機構を一切置かない（[design.md 設計判断 6]）。安全弁は `/voice-chat` プロンプト側の振る舞いとして実装する。

## ユーザーストーリー

**As a** 手が離れた状態で Claude に作業させる開発者
**I want to** 破壊的な操作の前に音声で確認してほしい
**So that** 誤った不可逆操作を音声で止められる

## 受入条件

- [ ] `.claude/commands/voice-chat.md` に「破壊的・不可逆な操作の前に、許可要求(`voice_speak`) → `voice_listen` で返事を待つ（ブロッキング）」手順がある
- [ ] 返事が肯定（「はい」等）のときのみ実行し、否定なら実行しない手順がある
- [ ] **ブロッキングで待つのは許可要求のみ**（宣言・報告は待たない）と整合している
- [ ] 「破壊的操作」の例示（削除・上書き・force push・リセット等）と、線引きは使いながら調整する旨が書かれている

## 仕様詳細

### UI / 画面

なし

### API / Server Action

- `voice_speak`（許可要求）＋ `voice_listen`（はい/いいえ）

### データモデル

なし

### バリデーション

- 返事が不明瞭（unintelligible）なら再度確認する

### エラーハンドリング

- 確認が取れない場合は実行しない（安全側に倒す）

### エッジケース

- 「はい」以外の曖昧な肯定/否定の扱い（迷ったら実行しない）

## 依存関係

- 前提（着手前に完了が必要）: `04-voice-chat-loop/01-voice-chat-command-and-loop`
- ブロックする: なし

理由: ループの核ができてから安全確認の振る舞いを足す。

## スコープ外

- ハーネス側パーミッション機構の利用（バイパス前提のため使わない）
- サーバ側コード追加（設計判断 6 によりサーバには置かない）

## 補足

- [ADR-0002](../../../adr/0002-skip-permissions-with-voice-confirmation.md)
- 関連設計: [design.md 設計判断 6（パーミッション機構をサーバに置かない）](../../../design/design.md#主要な設計判断とその理由)
