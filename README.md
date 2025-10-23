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