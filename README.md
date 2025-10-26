# AIニュースレポート自動生成システム

## 目的
データサイエンス、データエンジニアリング、データ分析の学習者向けに、AIの最新ニュースを毎日Notionにまとめ、Slackに通知するレポートを自動生成します。

## 機能概要
本システムは、以下の主要な機能を提供します。
- **AIニュースの収集:** GoogleアラートのRSSフィードから、AI関連の最新記事を全て自動収集します。
- **LLMによる記事処理:** 収集した記事は、LLM（Gemini-2.5-flash）によって以下の処理が行われます。
    - 外国語記事の日本語への翻訳と要約。
    - 記事のカテゴリ分類（データサイエンス、データエンジニアリング、データ分析、人工知能、プログラミング、パフォーマンス最適化）。
    - 各カテゴリから、学習者にとって最も有用で会話のきっかけになりそうな記事を最大3つ選定し、初学者向けのポイント（3行）と会話を促すコメントを生成します。
- **Notionレポートの作成:** 選定された記事を基に、Notionに「AIニュースレポート - YYYY年MM月DD日」という単一のレポートページを作成します。このページには、導入文、カテゴリごとの見出し、各記事のタイトル（URLリンク付き）、要約、初学者向けポイント、会話を促すコメントが含まれます。
- **Slack通知の送信:** Notionに作成されたレポートの内容を基に、Slackの指定されたチャンネルに通知メッセージを送信します。メッセージは学習者を鼓舞する導入文を含み、選定された記事の要約、初学者向けポイント、会話を促すコメント、Notionレポートへのリンクが含まれます。

## 実行スケジュール
毎日午前8時00分（日本標準時）に定期実行されます。

## 環境構築
本プロジェクトの環境構築については、[環境構築ガイド](documents/setup_guide.md) を参照してください。

## APIキーとNotionデータベースの設定
本プロジェクトの実行に必要なAPIキーの取得方法やNotionデータベースの設定については、[API・Notion設定ガイド](documents/api_notion_setup.md) を参照してください。

## 必要な環境変数
本プロジェクトの実行には、以下の環境変数が設定されている必要があります。詳細は[API・Notion設定ガイド](documents/api_notion_setup.md) を参照してください。

| 変数名                      | 説明                                |
|-----------------------------|-----------------------------------------|
| `GOOGLE_API_KEY`            | Google Gemini APIキー                   |
| `GOOGLE_ALERTS_RSS_URLS`    | GoogleアラートのRSSフィードURL（カンマ区切りで複数指定可能） |
| `NOTION_API_KEY`            | Notion APIキー                          |
| `NOTION_DATABASE_ID`        | NotionデータベースID                    |
| `SLACK_WEBHOOK_URL`         | Slack Incoming Webhook URL              |
| `SLACK_CHANNEL`             | Slack通知チャンネル名                   |

## 実行例

```bash
# 1. 環境変数を設定 (詳細はAPI・Notion設定ガイドを参照)
export GOOGLE_API_KEY="your_gemini_api_key"
export GOOGLE_ALERTS_RSS_URLS="https://alerts.google.com/alerts/feeds/..."
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

## 使用スクリプト構成
```
project/
├── rss_single_fetch.py        # RSSフィードから記事取得
├── write_to_notion.py         # Notionへの書き込み
├── send_slack_message.py      # Slack通知
├── main.py                    # 全体実行パイプライン
├── llm_processor.py           # LLMによる記事処理（翻訳、要約、カテゴリ分類、選定）
└── .env                       # 環境変数定義
```

## 注意事項
*   Notion APIキーには、対象データベースへの「編集」権限が付与されている必要があります。
*   Slack Webhook URLは、指定されたチャンネルへの投稿権限が必要です。
*   LLMのAPI呼び出しにはレート制限があるため、大量の記事を処理する場合は注意が必要です。