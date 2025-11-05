# テスト設計書

#### 1. テスト対象

-   **コードベース**: `src/` ディレクトリ配下の全てのPythonファイル
    *   `rss_single_fetch.py` (RSSフィードからの記事取得)
    *   `llm_processor.py` (LLMによる記事処理)
    *   `write_to_notion.py` (Notionへの書き込み)
    *   `send_slack_message.py` (Slack通知)
    *   `main.py` (全体実行パイプライン)
    *   `utils.py` (共通ユーティリティ)

#### 2. テストレベルと戦略

システム全体の品質を確保するため、以下のテストレベルを定義し、それぞれに適した戦略をとります。

##### 2.1. 単体テスト (Unit Test)

各関数の独立したロジックを検証します。
-   **目的**: 各コンポーネントが仕様通りに動作することを確認する。
-   **範囲**: 各Pythonファイル内の関数。
-   **戦略**:
    *   外部サービス（`requests`, `feedparser`, `BeautifulSoup`, `google.generativeai`, `notion_client`, `slack_sdk`, `unsplash_api`など）への呼び出しは、`unittest.mock` を使用して徹底的にモックします。
    *   環境変数 (`os.environ`) もモックし、テスト間の独立性を確保します。
    *   `time.sleep` もモックし、テスト実行時間を短縮します。
    *   入力値に対する正常系、異常系、境界値のテストを行います。

##### 2.2. 結合テスト (Integration Test)

複数のモジュール間の連携（インターフェース）が正しく機能することを検証します。
-   **目的**: モジュール間のデータ受け渡しや呼び出しシーケンスが正しく行われることを確認する。
-   **範囲**:
    *   `main.py` が `rss_single_fetch.py`, `llm_processor.py`, `write_to_notion.py`, `send_slack_message.py` の各関数を正しい順序と引数で呼び出すかを検証。
    *   `llm_processor.py` 内の各LLM関連関数間の連携（例: 翻訳→カテゴリ分類→選定）。
-   **戦略**:
    *   外部サービス（LLM API、Notion API、Slack API、Unsplash API）はモックし、モジュール間のインタラクション（モックされた関数の呼び出し回数、引数など）を検証します。
    *   `pytest-mock` などのライブラリを使用し、モックを容易にします。

##### 2.3. システムテスト / E2Eテスト (System Test / End-to-End Test) - **オプション**

実際の外部環境を含めたシステム全体の動作を検証します。CI/CDパイプラインでは高コストなため、実施する場合は限定的に。
-   **目的**: ユーザーシナリオに沿った一連の処理が、実際の外部サービスと連携して問題なく動作することを確認する。
-   **範囲**: `main.py` の実行から結果（Notionページ作成、Slack通知）までの一連の流れ。
-   **戦略**:
    *   **専用のテスト環境**: テスト用のGemini APIキー、NotionデータベースID、Slack Webhook URL、Unsplash APIキーを設定し、本番環境とは分離した環境を使用します。これにより、本番データへの影響を防ぎ、APIのレート制限に配慮します。
    *   **限定的な実行頻度**: フルサイクルビルドやデプロイ前など、比較的低頻度で実行します。
    *   **クリーンアップ処理**: テスト実行後にNotionに作成されたページやSlackに送信されたメッセージを自動的にクリーンアップするメカニズムを実装します。
    *   **ユーザーシナリオテスト**: 実際のユーザーがシステムを利用する際の典型的なシナリオ（例: RSSフィードが提供され、ニュースが取得・処理され、Notionにレポートが作成され、Slackに通知される）に沿ってテストします。

#### 3. テスト項目詳細 (QAエンジニア視点強化)

上記テストレベルに基づき、具体的なテスト項目を設計します。

##### 3.1. `rss_single_fetch.py`

*   **正常系**:
    *   有効なRSSフィードURLから記事が正しく取得されること。
        *   タイトル、URL、概要（description/summary）、公開日が正しくパースされること。
        *   `_extract_image_from_html`ヘルパー関数は、Unsplashから画像を取得するため、RSSフィードや記事本文から画像URLを抽出しないこと。
    *   GoogleアラートのリダイレクトURLが正しく最終記事URLに変換され、画像パス解決 (`urljoin`) も正しく行われること。
    *   `time.sleep(0.5)` が記事コンテンツ取得エラー時に一度呼び出されていること。
    *   画像URLはUnsplashから取得されるため、RSSフィードや記事本文からは取得されないこと。
*   **異常系/境界値**:
    *   無効なRSSフィードURLが与えられた場合、空のリストが返され、エラーログが出力されること。
    *   RSSフィードが空、または`entries`がない場合、空のリストが返されること。
    *   ネットワークエラー（HTTP 4xx/5xxエラー、タイムアウト、接続拒否など）発生時に、適切にエラーハンドリングされ、空のリストが返されること。
    *   記事内に `title`, `link`, `summary` のいずれかが欠けている場合、デフォルト値（"タイトルなし", "#", "" など）が設定されること。
    *   画像URLがRSSフィード、OGP/Twitter Card、記事本文のいずれからも取得できない場合を含め、画像URLが `None` で適切に扱われること。

##### 3.2. `llm_processor.py`

*   **`initialize_gemini`**:
    *   `GOOGLE_API_KEY`が設定されている場合、正しく`genai.configure`が呼び出されること。
    *   `GOOGLE_API_KEY`が設定されていない場合、`ValueError`が送出されること。
*   **`is_foreign_language`**:
    *   **同値分割**: 日本語のテキスト、英語のテキスト、記号のみのテキスト、短すぎるテキストなど。
    *   **境界値**: 日本語と外国語が混在するテキスト、`langdetect`が検出できない特殊なテキスト。
    *   日本語テキストが与えられた場合`False`、日本語以外のテキストが与えられた場合`True`を返すこと。
    *   言語検出が困難なテキスト（例: ごく短い文字列）が与えられた場合、`True`を返す（フォールバック）。
*   **`translate_and_summarize_with_gemini`**:
    *   **正常系**: 外国語テキストが与えられた場合、JSON形式で日本語の要約(`summary`)と3つの初学者向けポイント(`points`)が返されること。
        *   要約が**約180文字**であること（厳密な文字数ではなく、指定されたプロンプトに沿っているか）。
        *   ポイントが3つ生成されていること。
        *   `comment`キーが空文字列であること。
    *   **異常系**:
        *   LLMからの応答が完全に不正なJSON文字列の場合、フォールバック処理が適切に行われ、`summary`のみが生テキストとなること。
        *   LLMからの応答がJSON形式だが、期待されるキー（`summary`, `points`）が含まれていない場合、欠落したキーが空のリストや文字列となること。
        *   Gemini API呼び出し中にエラー（ネットワーク、APIエラーなど）が発生した場合、適切にエラー情報を含むフォールバックの辞書が返されること。
*   **`categorize_article_with_gemini`**:
    *   **正常系**: 記事のタイトルと要約に基づいて、定義されたカテゴリ (`データサイエンス`, `人工知能` など) のいずれかが正しく返されること。
    *   **異常系**:
        *   LLMが定義外のカテゴリ名を返した場合、「その他」が返されること。
        *   Gemini API呼び出し中にエラーが発生した場合、「その他」が返されること。
*   **`select_and_summarize_articles_with_gemini`**:
    *   **正常系**: 複数の記事とカテゴリが与えられた場合、カテゴリごとに最大3記事が選定され、各記事に初学者向けポイントが生成されたJSON配列が返されること。
        *   選定された記事が元の`articles`リスト内の記事とURLで正しく紐付けられていること。
        *   JSON配列が指定された形式であること。
        *   選定された記事に`comment`キーが含まれていないこと。
    *   **異常系**:
        *   LLMからの応答が不正なJSONの場合、リストが破損せず、適切にエラーハンドリングされること（該当カテゴリの記事が選定されないなど）。
        *   Gemini API呼び出し中にエラーが発生した場合、空のリストが返されること。
        *   選定された記事のタイトルが元記事に存在しない場合、警告が出力されること。
*   **`generate_image_keywords_with_gemini`**:
    *   **正常系**: 記事のタイトル、要約、カテゴリから、英語の画像検索キーワードが3つ（カンマ区切り）生成されること。
    *   **異常系**: Gemini API呼び出し中にエラーが発生した場合、空文字列が返されること。
*   **`search_image_from_unsplash`**:
    *   **正常系**: 有効なキーワードが与えられた場合、Unsplashから画像URLが返されること。
    *   **異常系**:
        *   `UNSPLASH_ACCESS_KEY`が設定されていない場合、`None`が返され、警告が出力されること。
        *   キーワードが空の場合、`None`が返されること。
        *   Unsplash API呼び出し中にエラーが発生した場合、`None`が返されること。
        *   キーワードに一致する画像が見つからない場合、`None`が返されること。
*   **`generate_closing_comment_with_gemini`**:
    *   **正常系**: 選定された記事のリストに基づいて、コミュニケーションを促進する**100文字程度**のクロージングコメントが生成されること。
    *   **異常系**:
        *   Gemini API呼び出し中にエラーが発生した場合、デフォルトのフォールバックコメントが返されること。

##### 3.3. `write_to_notion.py`

*   **`ensure_notion_database_properties`**:
    *   **正常系**:
        *   必要なプロパティがすべて存在し、タイプも一致している場合、`True`を返すこと。
        *   不足しているプロパティがある場合、それが追加され、`True`を返すこと。（Notion APIモックで検証）
        *   `Status`プロパティに`Published`オプションがない場合、それが追加され、`True`を返すこと。（Notion APIモックで検証）
    *   **異常系**:
        *   Notion APIがエラーを返した場合（例: 権限不足、DB ID誤り）、`False`を返し、適切なエラーメッセージが出力されること。
        *   プロパティのタイプが既存のものと一致しない場合、`False`を返し、警告メッセージが出力されること。
*   **`create_notion_report_page`**:
    *   **正常系**:
        *   Notionのページが正しく作成され、そのURLが返されること。
        *   ページタイトル、導入文、カテゴリごとの見出し、記事タイトル（URLリンク付き）、記事の要約、`divider`が正しい構成で設定されていること。
        *   `REPORT_DATE`環境変数がページタイトルと日付プロパティに正しく反映されること。
        *   `processed_articles`に`image_url`がある場合、最初の記事の画像がカバー画像として設定されること。
    *   **異常系**:
        *   Notion APIがエラーを返した場合、`None`を返し、適切なエラーメッセージが出力されること。
        *   `processed_articles`が空の場合でも、エラーなくページ作成処理が完了すること（タイトルや導入文のみのページ）。

##### 3.4. `send_slack_message.py`

*   **`send_slack_message`**:
    *   **正常系**:
        *   有効なWebhook URLとデータが与えられた場合、Slackメッセージが正常に送信され(`requests.post`の成功をモック)、`True`を返すこと。
        *   メッセージブロックが期待される形式で構築されていること（ヘッダー、導入文、カテゴリごとの記事、初学者向けポイント、クロージングコメント、Notion URLリンク）。
        *   `report_date`と`closing_comment`がメッセージ内に正しく表示されること。
    *   **異常系**:
        *   `requests.post`がHTTPエラー（例: 4xx, 5xx）を返した場合、`False`を返し、エラーメッセージが出力されること。
        *   ネットワークエラー（接続拒否、タイムアウトなど）が発生した場合、`False`を返し、エラーメッセージが出力されること。
        *   `slack_webhook_url`が`None`または空の場合、メッセージ送信がスキップされ、警告が出力されること（`main.py`側で制御）。
        *   `news_articles`が空の場合でも、エラーなくメッセージが構築・送信されること（ヘッダーと導入文のみ）。

##### 3.5. `main.py`

*   **結合テスト視点（モック利用）**:
    *   **正常フロー**:
        *   すべての外部依存関数（`fetch_all_entries`, `initialize_gemini`, `translate_and_summarize_with_gemini`, `categorize_article_with_gemini`, `select_and_summarize_articles_with_gemini`, `generate_image_keywords_with_gemini`, `search_image_from_unsplash`, `generate_closing_comment_with_gemini`, `ensure_notion_database_properties`, `create_notion_report_page`, `send_slack_message`）が正しい順序で、適切な引数とともに呼び出されていること。
        *   `os.environ["REPORT_DATE"]` が正しく設定されていること。
        *   `final_articles_for_report`内の各記事タイトルからHTMLタグが除去されていること。
        *   `llm_processor.py`から返された要約に対して`remove_html_tags`が適用されていること。
    *   **異常フロー**:
        *   `GOOGLE_API_KEY`、`GOOGLE_ALERTS_RSS_URLS`、`NOTION_API_KEY`、**`UNSPLASH_ACCESS_KEY`**が設定されていない場合、処理が早期終了し、適切なエラーメッセージが出力されること。
        *   `fetch_all_entries`が空のリストを返した場合、処理が早期終了すること。
        *   `select_and_summarize_articles_with_gemini`が空のリストを返した場合、処理が早期終了すること。
        *   Notionデータベースのプロパティ準備(`ensure_notion_database_properties`)に失敗した場合、Notionページ作成(`create_notion_report_page`)がスキップされること。
        *   `slack_webhook_url`または`notion_report_url`が利用できない場合、Slack通知がスキップされ、適切なメッセージが出力されること。

##### 3.6. `utils.py`

*   **`remove_html_tags`**:
    *   HTMLタグを含む文字列が完璧に除去されること（例: `"<p>Hello <b>World</b>!</p>"` -> `"Hello World!"`）。
    *   **HTMLエンティティ（例: `&nbsp;`）が適切にデコードされ、除去されること。**
    *   HTMLタグを含まない文字列が変更されないこと。
    *   空文字列が与えられた場合、空文字列が返されること。
    *   壊れたHTMLタグ（例: `"Hello <b World!"`）でもエラーなく処理され、可能な限りタグを除去すること。

#### 4. テストデータの準備

*   **RSSフィード**:
    *   正常なRSS XMLデータ（複数記事、単一記事、画像URLあり/なし）。
    *   空のRSS XMLデータ。
    *   不正な形式のRSS XMLデータ。
*   **記事データ**:
    *   完全な記事情報（タイトル、URL、概要、画像URL）。
    *   一部情報が欠落した記事情報。
    *   日本語、英語など複数の言語の概要。
    *   HTMLタグを含む記事タイトル。
    *   **HTMLエンティティを含む記事概要。**
*   **LLM応答データ**:
    *   `llm_processor` の各関数が期待するJSON形式の応答データ。
    *   不正なJSON形式、部分的に欠落したJSON形式の応答データ。
    *   LLMのエラー応答（APIエラー、レート制限エラーなど）。
*   **Notionデータ**:
    *   Notion APIクライアントで使用するモックデータ（データベース情報、ページ作成応答など）。
    *   Notionデータベースのプロパティ情報（不足しているプロパティ、タイプが異なるプロパティなど）。
*   **Unsplashデータ**:
    *   Unsplash APIからの正常な画像検索応答データ。
    *   Unsplash APIからの画像なし応答データ。
    *   Unsplash APIからのエラー応答。
*   **Slackデータ**:
    *   Slack Webhookへの正常なペイロードデータ。
    *   Slack Webhookからのエラー応答。

#### 5. テスト実行環境と自動化 (CI/CDエンジニア視点)

*   **テストフレームワーク**: `pytest` を使用し、テストの発見と実行を効率化します。
*   **テストレポート**: `pytest-html` や `pytest-cov` などのプラグインを使用し、テスト結果（成功/失敗、カバレッジ）をHTMLレポートやカバレッジレポートとして生成します。これはCI/CDツール（GitHub Actionsなど）で視覚的に確認できるようにします。
*   **CI/CDパイプラインへの統合**:
    *   `requirements-dev.txt` または `requirements.txt` にテストに必要な依存関係を明記します。
    *   GitHub Actionsのワークフローにテスト実行ステップを含めます。
    *   単体テストおよび結合テストは、Pull Requestごとに実行し、高速なフィードバックを提供します。
    *   E2Eテストは、上記懸念事項（コスト、実行時間、安定性）を考慮し、毎週など限定された頻度、または本番デプロイ前などに、隔離された環境で実行することを検討します。
*   **環境変数管理**: CI/CD環境ではAPIキーなどの機密情報は、GitHub Actions Secretsなどのセキュアな方法で管理されます。テストコードはこれらのSecretsを正しく参照するようにします。