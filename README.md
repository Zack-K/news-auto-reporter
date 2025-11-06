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
    - 選定された記事のタイトル、要約、カテゴリから画像検索用のキーワードを生成し、Unsplashから関連画像を検索します。
- **Notionレポートの作成:** 選定された記事を基に、Notionに「AIニュースレポート - YYYY年MM月DD日」という単一のレポートページを作成します。このページには、導入文、カテゴリごとの見出し、各記事のタイトル（URLリンク付き）、要約、初学者向けポイント、会話を促すコメント、そしてレポートのカバー画像（Unsplashから検索された画像）が含まれます。

## 実行スケジュール
毎日午前8時00分（日本標準時）に定期実行されます。このスケジュールは、GitHub Actionsのワークフローによって自動化されています。

**GitHub Actionsによる自動実行:**
*   **ワークフローファイル:** `.github/workflows/daily_report.yml`
*   **トリガー:**
    *   `schedule`: 毎日午前8時00分（日本標準時）に実行されるように設定されています。
    *   `workflow_dispatch`: GitHub UIから手動でワークフローを実行することも可能です。
*   **ジョブの構成:**
    *   `build_and_test`: コードのチェックアウト、Python環境のセットアップ、依存関係のインストール、Ruffによる静的解析、Pytestによる単体テストを実行します。
    *   `run_report`: `build_and_test` ジョブが成功した場合にのみ実行されます。AIニュースレポートの生成と通知のメイン処理を実行します。
*   **環境変数:** 必要なAPIキーや設定値は、GitHubリポジトリのSecretsとして安全に管理されています。
*   **失敗時の通知:** ワークフローの実行が失敗した場合、Slackに通知が送信されます。

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
| `UNSPLASH_ACCESS_KEY`       | Unsplash APIキー                    |
| `REPORT_DATE`               | レポートの日付（GitHub Actionsで自動設定） |

## 実行例

```bash
# 1. 環境変数を設定 (詳細はAPI・Notion設定ガイドを参照)
export GOOGLE_API_KEY="your_gemini_api_key"
export GOOGLE_ALERTS_RSS_URLS="https://alerts.google.com/alerts/feeds/..."
export NOTION_API_KEY="your_notion_key"
export NOTION_DATABASE_ID="your_db_id"
export SLACK_WEBHOOK_URL="your_webhook_url"
export SLACK_CHANNEL="#ai-news"
export UNSPLASH_ACCESS_KEY="your_unsplash_key"

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
├── llm_processor.py           # LLMによる記事処理（翻訳、要約、カテゴリ分類、選定、画像キーワード生成、クロージングコメント生成）
├── utils.py                   # 共通ユーティリティ（HTMLタグ除去など）
└── .env                       # 環境変数定義
```

## 注意事項
*   Notion APIキーには、対象データベースへの「編集」権限が付与されている必要があります。
*   Slack Webhook URLは、指定されたチャンネルへの投稿権限が必要です。
*   LLMのAPI呼び出しにはレート制限があるため、大量の記事を処理する場合は注意が必要です。
*   LLMによる要約、ポイント、クロージングコメントは、指定された文字数に制限される場合があります。
*   **Unsplash APIの利用について**: Unsplash APIの利用には、利用規約とレート制限があります。これらを遵守し、適切な利用を心がけてください。
*   **画像検索の関連性**: Unsplashからの画像検索は、LLMが生成するキーワードの精度に依存します。必ずしも記事内容に完全に合致する画像が取得できるとは限りません。