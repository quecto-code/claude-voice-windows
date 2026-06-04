---
type: task
title: VOICEVOX エンジンをインストールし起動する
label: must-have
depends_on: []
---

## 背景

親 Story `00-environment-setup/02-external-services` の一部として、VOICEVOX Linux 版エンジンを DL し、ローカルで起動して `/version` が叩ける状態にする。

親 Story: 00-environment-setup/02-external-services

## 受入条件

- [x] VOICEVOX Linux 版エンジンのアーカイブが DL され、プロジェクト外（例: `~/voicevox-engine/`）または合意した配置先に展開されている → `~/voicevox-engine/linux-nvidia/`（GPU 版 0.25.2）
- [x] エンジン起動コマンド（例: `~/voicevox-engine/run`）が実行可能で、起動するとポート 50021 を listen する → `~/voicevox-engine/linux-nvidia/run --host 127.0.0.1 --port 50021 --use_gpu`、`ss -lnt | grep 50021` で確認
- [x] 起動状態で `curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:50021/version` が `200` を返す → `200` / body `"0.25.2"`
- [x] 起動コマンドと配置先パスがメモされている（後続 Story 03 の README に転記する）→ 下の「変更ファイル」に記載

## 仕様詳細

### 変更ファイル

リポジトリ内ファイルへの変更はなし（環境作業）。配置先と起動コマンドを以下に記録（Story 03 で README へ転記）:

- **配置先**: `~/voicevox-engine/linux-nvidia/`（GPU 版 / linux-nvidia-0.25.2）
- **起動コマンド（バックグラウンド）**:
  ```bash
  nohup ~/voicevox-engine/linux-nvidia/run --host 127.0.0.1 --port 50021 --use_gpu \
        > ~/voicevox-engine/engine.log 2>&1 &
  ```
- **疎通確認**: `curl -s http://127.0.0.1:50021/version`
- **停止**: `pkill -f voicevox-engine/linux-nvidia/run`
- **DL 元（再現用）**: `https://github.com/VOICEVOX/voicevox_engine/releases/download/0.25.2/voicevox_engine-linux-nvidia-0.25.2.7z.{001,002}` を 7z で展開
- **GPU 確認**: 起動ログに `CUDA (device_id=0)を利用します` が出ること、`nvidia-smi` で VRAM 使用が現れること（~580MiB）

### 関数 / API シグネチャ

該当なし

### バリデーション・エラー処理

- 起動失敗時はエンジンのログを確認する手順を README に残す
- ポート 50021 が他で使用中の場合は別ポートにする選択肢を README で示す

### エッジケース

- CPU / GPU の選択（CUDA 版エンジンと CPU 版があれば、GPU 版を選び `nvidia-smi` の VRAM に収まることを確認）
- WSL2 から Windows 側の VOICEVOX を叩く代替案も将来取りうるが、本タスクでは Linux 版を直接起動する

## 依存関係

- 前提: なし
- ブロックする: 02-voice-output-speak の全タスク

理由: speak の受入確認に必要。

## スコープ外

- 自動起動（systemd / supervisor）の整備
- speaker id の選定（Epic 02 で調整）

## 補足

- 配布元 URL は VOICEVOX 公式リリースを参照（README に記載）
- **手動検証**: 実際の音質確認は Epic 02 の speak タスクで人耳判定
