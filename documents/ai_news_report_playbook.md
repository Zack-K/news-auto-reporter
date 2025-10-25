# 📰 AIニュースレポート自動生成プレイブック

## 🎯 目的
データサイエンス、データエンジニアリング、データ分析の学習者向けに、AIの最新ニュースを毎朝自動で収集し、  
**Notionにレポートを作成 → Slackに通知**することで、最新情報の共有を効率化します。

---

## ⏰ 実行スケジュール
- **毎日 08:00（日本標準時）** に定期実行（cronまたはワークフロー管理ツールを使用）
- 実行対象スクリプト：`main.py`

---

## 🪜 実行ステップ

### ① AIニュースの収集
GoogleアラートのRSSフィードからAI関連の最新記事を全て収集します。

**抽出項目**
- 記事タイトル
- URL
- 公開日
- 概要（descriptionまたはsummary）

※外国語の記事は自動翻訳・要約（※翻訳APIまたは自前モデル）を実行。

---

### ② 記事の翻訳・カテゴリ分類
収集したニュース記事を以下のカテゴリに分類します：

- データサイエンス  
- データエンジニアリング  
- データ分析  
- 人工知能  
- プログラミング  
- パフォーマンス最適化

**分類基準**
- 記事タイトル・概要のキーワード  
- 固有名詞（モデル名、技術名）  
- 記事発行元（例：OpenAI → 人工知能）

---

### ③ Notionデータベースへの書き込み
`notion-sdk-py` を使用して、指定のデータベースに新規ページを作成します。

**ページ構造**
- ページタイトル：  
  `AIニュースレポート - YYYY年MM月DD日`
- 導入文：  
  `データサイエンス、データエンジニアリング、データ分析の学習者向けに、AIの最新ニュースを毎日お届けします。`
- 各カテゴリごとに見出し（`heading_2`）
- 各記事タイトル（URLリンク付き、`heading_3`）
- 記事の要約（`paragraph`）
- 記事間には `divider` を挿入

**処理フロー**
1. `fetch_latest_entry()` → RSS取得
2. `create_notion_page()` → Notionページ生成
3. Notion URLを返却

---

### ④ Slack通知メッセージの作成と送信
Slack Incoming Webhookを使い、指定チャンネルにレポート内容を送信します。

**メッセージ内容**
- レポートタイトル（`header`）
- 導入文（`section`）
- カテゴリごとの記事タイトル・URL・要約（`section`）
- 収集した全てのニュース記事（タイトル、URL、要約）
- Dividerで区切り
- 最後に Notion レポートURLへのリンクを添付

**処理フロー**
1. Notion URLとニュースデータを受け取る  
2. `send_slack_message()` 関数で整形  
3. Webhook経由で送信

---

## ⚙️ 必要な環境変数

| 変数名                | 説明                                | 例                                                |
|-----------------------|-------------------------------------|--------------------------------------------------|
| `NOTION_API_KEY`       | NotionのAPIキー                     | `secret_xxxxxxxxxxxxxxxxx`                       |
| `NOTION_DATABASE_ID`   | 書き込み先NotionデータベースのID    | `291axxxxxxxxxxxxx`|
| `SLACK_WEBHOOK_URL`    | Slack Incoming WebhookのURL         | `https://hooks.slack.com/services/...`          |
| `SLACK_CHANNEL`        | 通知するSlackチャンネル名           | `#ai-news`                                      |
| `REPORT_DATE`          | レポートの日付                      | `2025-10-21`                                    |

---

## 📝 注意事項

- Notionの統合に対象データベースへの「**編集権限**」が付与されていることを確認してください。
- Slack Webhook URLには、対象チャンネルへの**投稿権限**が必要です。
- 翻訳・要約機能を追加する場合は、翻訳APIキーの管理にも注意してください。
- RSS元サイトのレート制限に留意し、アクセス間隔を調整してください。

---

## 🧰 使用スクリプト構成

```
project/
├── rss_single_fetch.py        # RSSフィードから記事取得
├── write_to_notion.py         # Notionへの書き込み
├── send_slack_message.py      # Slack通知
├── main.py                    # 全体実行パイプライン
└── .env                       # 環境変数定義
```

---

## 🏃 実行例

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
