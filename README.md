# AIニュースレポート自動生成システム

## 目的
データサイエンス、データエンジニアリング、データ分析の学習者向けに、AIの最新ニュースを毎日Notionにまとめ、Slackに通知するレポートを自動生成します。

## 実行スケジュール
毎日午前8時00分（日本標準時）に定期実行されます。

## 実行ステップ

### 1. AIニュースの収集と選定
以下の技術ブログおよび業界ニュースサイトから、AI関連の最新記事をRSS経由で収集します。
- Google AI Blog
- OpenAI Blog
- Microsoft AI Blog
- Towards Data Science

各記事から、タイトル、URL、公開日、概要を抽出します。外国語の記事については、日本語に翻訳し、要約を作成します。

### 2. ニュースの翻訳と要約、カテゴリ分類
収集した各ニュース記事を以下のカテゴリに分類します。
- データサイエンス
- データエンジニアリング
- データ分析
- 人工知能
- プログラミング
- パフォーマンス最適化

分類基準:
- 記事タイトル・概要のキーワード
- 固有名詞（モデル名、技術名）
- 記事発行元（例：OpenAI → 人工知能）

### 3. Notionデータベースへの書き込み
Notion API (`notion-sdk-py`を使用) を使用して、指定されたNotionデータベースに新しいページを作成します。

ページ構造:
- ページタイトル: `AIニュースレポート - YYYY年MM月DD日`
- 導入文: `データサイエンス、データエンジニアリング、データ分析の学習者向けに、AIの最新ニュースを毎日お届けします。`
- 各カテゴリの見出し（例: 「【人工知能】」）
- 各記事のタイトル（URLリンク付き）
- 各記事の要約
- 記事間には区切り線（divider）を挿入

### 4. Slack通知メッセージの作成と送信
Notionに書き込まれた内容を基に、Slackの指定されたチャンネルに通知メッセージを送信します。Slack Incoming Webhookを使用します。

メッセージ内容:
- レポートのタイトル
- 導入文
- カテゴリごとのニュース記事（タイトル、URL、要約）
- Notionレポートへのリンク

## 環境構築 (Environment Setup)

本プロジェクトの実行には、Pythonの仮想環境ツールである `uv` を使用することを推奨します。`uv` を利用することで、依存関係の管理と仮想環境の構築を高速かつ効率的に行えます。

### 1. uv のインストール

`uv` がシステムにインストールされていない場合は、以下のいずれかの方法でインストールしてください。最新の情報は [uv 公式ドキュメント](https://docs.astral.sh/uv/) を参照してください。

#### macOS および Linux

**推奨 (スタンドアロンインストーラー):**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

#### Windows

**推奨 (PowerShell):**
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

#### Python パッケージマネージャーを使用 (pip または pipx)

Pythonが既にインストールされている環境では、`pip` または `pipx` を使用して `uv` をインストールすることも可能です。

**pip を使用したインストール:**
```bash
pip install uv
```

**pipx を使用したインストール (推奨):**
```bash
pipx install uv
```

### 2. 仮想環境の作成とアクティベート

プロジェクトのルートディレクトリで以下のコマンドを実行し、仮想環境を作成してアクティベートします。

```bash
uv venv
source .venv/bin/activate
```

### 3. 依存関係のインストール

仮想環境がアクティベートされた状態で、`requirements.txt` に記載されている依存関係をインストールします。

```bash
uv pip install -r requirements.txt
```

## APIキーとNotionデータベースの設定

本プロジェクトを実行するためには、SlackとNotionのAPIキーおよび関連設定が必要です。

### Slack Incoming Webhook URLの取得

Slackにメッセージを送信するために、Incoming Webhook URLを設定します。

1.  **Slackアプリの作成**: [Slack APIサイト](https://api.slack.com/apps) にアクセスし、Slackアカウントでサインインします。「Create New App」をクリックし、「From scratch」を選択します。
2.  **アプリ名の設定とワークスペースの選択**: アプリケーションの名前を入力し、インストール先のSlackワークスペースを選択して「Create App」をクリックします。
3.  **Incoming Webhooksの有効化**: アプリ作成後、設定ページにリダイレクトされます。左サイドバーで「Incoming Webhooks」を見つけてクリックし、「Activate Incoming Webhooks」を「On」に切り替えます。
4.  **ワークスペースへの新しいWebhookの追加**: 設定ページが更新されたら、「Webhook URLs for Your Workspace」セクションまでスクロールし、「Add New Webhook to Workspace」ボタンをクリックします。
5.  **チャンネルの選択**: メッセージの送信先となる特定のチャンネルを選択し、「Allow」または「Authorize」をクリックします。プライベートチャンネルに追加する場合は、事前にそのチャンネルのメンバーである必要があります。
6.  **Webhook URLのコピー**: 承認後、Incoming Webhooks設定ページに戻ります。「Webhook URLs for Your Workspace」の下に生成された一意のIncoming Webhook URLが表示されますので、これをコピーします。このURLが、外部アプリケーションからSlackにメッセージを送信するために使用されます。

**重要**: このURLは秘密として扱ってください。このURLを知っている人は誰でも、追加の認証なしに定義されたSlackチャンネルにメッセージを送信できます。

### Notion APIキー (内部インテグレーションシークレット) の取得

Notionデータベースと連携するために、内部インテグレーションシークレットを取得します。

1.  **インテグレーションダッシュボードへのアクセス**: [Notionのインテグレーションダッシュボード](https://www.notion.com/my-integrations) にアクセスします。
2.  **新しいインテグレーションの作成**: 「+ New integration」ボタンをクリックします。
3.  **インテグレーションの設定**: インテグレーションの名前を入力し、必要に応じてロゴをアップロードし、関連するNotionワークスペースを選択します。
4.  **機能の設定**: 「Capabilities」タブに移動し、必要な権限（例: コンテンツの読み取り、コンテンツの更新、コンテンツの挿入、メールアドレスなしのユーザー情報）を選択します。変更を保存することを忘れないでください。
5.  **シークレットの取得**: インテグレーション作成後、インテグレーション設定内の「Secrets」または「Configuration」タブに移動します。ここに「Internal Integration Token」（APIシークレットとも呼ばれます）が表示されますので、これをコピーします。
6.  **ページ権限の付与**: インテグレーションがNotionワークスペース内の特定のページやデータベースとやり取りできるようにするには、それらのページをインテグレーションと明示的に共有する必要があります。対象のNotionページにアクセスし、「...」（その他）メニューをクリックし、「+ Add Connections」までスクロールして、作成したインテグレーションを選択します。

**注意**: 2024年9月25日以降、Notionの公開APIトークン形式が更新され、`secret_`の代わりに`ntn_`プレフィックスを使用するようになりましたが、内部インテグレーションのシークレット取得プロセスは変更されていません。既存の`secret_`トークン（内部インテグレーションシークレットを含む）は引き続き機能します。

### NotionデータベースIDの取得

プロジェクトが連携するNotionデータベースのIDを取得します。

1.  Notionで対象のデータベースページを開きます。
2.  ブラウザのアドレスバーに表示されるURLを確認します。URLは通常 `https://www.notion.so/{workspace_name}/{database_id}?v={view_id}` のような形式です。
例: `https://www.notion.so/291a8159567e800f8e3fc699f35eefdd?v=291a8159567e808fb0e8000c5ba3b102&source=copy_link`
3.  `{database_id}` の部分がデータベースIDです。これをコピーします。

### Notionデータベースの設定

プロジェクトが正しく動作するためには、Notionデータベースに以下のプロパティが設定されている必要があります。もし存在しない場合は、データベースに手動で追加してください。

*   **Name**: タイプは「Title」
*   **日付**: タイプは「Date」
*   **ステータス**: タイプは「Status」。少なくとも「Published」という名前のオプションが含まれている必要があります。
*   **要約**: タイプは「Rich text」
*   **URL**: タイプは「URL」

これらのプロパティ名は、`src/write_to_notion.py` 内で環境変数 `NOTION_PROPERTY_NAME`, `NOTION_PROPERTY_DATE`, `NOTION_PROPERTY_STATUS`, `NOTION_PROPERTY_ABSTRACT`, `NOTION_PROPERTY_URL` を設定することでカスタマイズ可能です。

## 必要な環境変数

以下の環境変数が設定されている必要があります。

| 変数名                | 説明                                | 例                                                |
|-----------------------|-------------------------------------|--------------------------------------------------|
| `NOTION_API_KEY`       | NotionのAPIキー                     | `secret_xxxxxxxxxxxxxxxxx`                       |
| `NOTION_DATABASE_ID`   | 書き込み先NotionデータベースのID    | `291axxxxxxxxxxxxx`                              |
| `SLACK_WEBHOOK_URL`    | Slack Incoming WebhookのURL         | `https://hooks.slack.com/services/...`          |
| `SLACK_CHANNEL`        | 通知するSlackチャンネル名           | `#ai-news`                                      |
| `REPORT_DATE`          | レポートの日付 (YYYY-MM-DD形式)     | `2025-10-21`                                    |

## 注意事項

*   Notion APIキーには、対象データベースへの「編集」権限が付与されている必要があります。
*   Slack Webhook URLは、指定されたチャンネルへの投稿権限が必要です。
*   翻訳・要約機能を追加する場合は、翻訳APIキーの管理にも注意してください。
*   RSS元サイトのレート制限に留意し、アクセス間隔を調整してください。

## 使用スクリプト構成

```
project/
├── rss_single_fetch.py        # RSSフィードから記事取得
├── write_to_notion.py         # Notionへの書き込み
├── send_slack_message.py      # Slack通知
├── main.py                    # 全体実行パイプライン
└── .env                       # 環境変数定義
```

## 実行例

```bash
# 1. 環境変数を設定
export NOTION_API_KEY="your_notion_key"
export NOTION_DATABASE_ID="your_db_id"
export SLACK_WEBHOOK_URL="your_webhook_url"
export SLACK_CHANNEL="#ai-news"

# 2. パイプラインを実行
python main.py
```

実行後、
✅ Notionに新規レポートページが作成され、
✅ Slackチャンネルにニュース要約とリンクが通知されます 🚀