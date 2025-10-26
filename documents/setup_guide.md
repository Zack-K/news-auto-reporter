# 環境構築ガイド

本プロジェクトの実行には、Pythonの仮想環境ツールである `uv` を使用することを推奨します。`uv` を利用することで、依存関係の管理と仮想環境の構築を高速かつ効率的に行えます。

## 1. uv のインストール

`uv` がシステムにインストールされていない場合は、以下のいずれかの方法でインストールしてください。最新の情報は [uv 公式ドキュメント](https://docs.astral.sh/uv/) を参照してください。

### macOS および Linux

**推奨 (スタンドアロンインストーラー):**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Windows

**推奨 (PowerShell):**
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Python パッケージマネージャーを使用 (pip または pipx)

Pythonが既にインストールされている環境では、`pip` または `pipx` を使用して `uv` をインストールすることも可能です。

**pip を使用したインストール:**
```bash
pip install uv
```

**pipx を使用したインストール (推奨):**
```bash
pipx install uv
```

## 2. 仮想環境の作成とアクティベート

プロジェクトのルートディレクトリで以下のコマンドを実行し、仮想環境を作成してアクティベートします。

```bash
uv venv
source .venv/bin/activate
```

## 3. 依存関係のインストール

仮想環境がアクティベートされた状態で、`requirements.txt` に記載されている依存関係をインストールします。

```bash
uv pip install -r requirements.txt
```