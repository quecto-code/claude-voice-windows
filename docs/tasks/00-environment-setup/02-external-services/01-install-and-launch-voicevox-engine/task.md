---
type: task
title: VOICEVOX エンジンをインストールし起動する
label: must-have
depends_on: []
---

## 背景

親 Story `00-environment-setup/02-external-services` の一部として、VOICEVOX **Windows 版**エンジンを DL し、ローカルで起動して `/version` が叩ける状態にする（[ADR-0005](../../../../adr/0005-windows-native-audio-path.md)。旧 Linux 版前提を更新）。

親 Story: 00-environment-setup/02-external-services

## 受入条件

- [ ] VOICEVOX **Windows 版**エンジン（または VOICEVOX アプリ同梱エンジン）が DL され、合意した配置先に展開されている（例: `%LOCALAPPDATA%\Programs\VOICEVOX\` もしくは `voicevox-engine` 単体配布）
- [ ] エンジン起動コマンド（`run.exe --host 127.0.0.1 --port 50021 --use_gpu`、または VOICEVOX アプリ起動）が実行可能で、起動するとポート 50021 を listen する → PowerShell `Get-NetTCPConnection -LocalPort 50021` で確認
- [ ] 起動状態で `Invoke-RestMethod http://127.0.0.1:50021/version` が版番号を返す（HTTP 200）
- [x] 起動コマンドと配置先パスがメモされている（後続 Story 03 の README に転記する）→ 下の「変更ファイル」に記載

## 仕様詳細

### 変更ファイル

リポジトリ内ファイルへの変更はなし（環境作業）。配置先と起動コマンドを以下に記録（Story 03 で README へ転記）:

- **配置先（例）**: `%LOCALAPPDATA%\Programs\VOICEVOX\`（VOICEVOX アプリ）または `voicevox-engine`（エンジン単体配布）
- **起動コマンド（PowerShell, バックグラウンド）**:
  ```powershell
  Start-Process -FilePath "<engine>\run.exe" `
      -ArgumentList "--host","127.0.0.1","--port","50021","--use_gpu" `
      -WindowStyle Hidden
  ```
  （VOICEVOX アプリを GUI 起動しても 50021 で同エンジンが立ち上がる）
- **疎通確認**: `Invoke-RestMethod http://127.0.0.1:50021/version`
- **停止**: `Get-Process run | Stop-Process`（または VOICEVOX アプリを終了）
- **DL 元（再現用）**: VOICEVOX 公式リリースの **Windows 版**（`voicevox-windows-nvidia-*` または インストーラ）。CPU 版を使う場合は `--use_gpu` を外す
- **GPU 確認**: 起動ログに `CUDA ... を利用します` が出ること、`nvidia-smi` で VRAM 使用が現れること

### 関数 / API シグネチャ

該当なし

### バリデーション・エラー処理

- 起動失敗時はエンジンのログを確認する手順を README に残す
- ポート 50021 が他で使用中の場合は別ポートにする選択肢を README で示す

### エッジケース

- CPU / GPU の選択（CUDA 版エンジンと CPU 版があれば、GPU 版を選び `nvidia-smi` の VRAM に収まることを確認）
- 本タスクは Windows ネイティブで VOICEVOX Windows 版を直接起動する（[ADR-0005](../../../../adr/0005-windows-native-audio-path.md)）

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
