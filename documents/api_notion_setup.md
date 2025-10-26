# API・Notion設定ガイド

本プロジェクトを実行するためには、Google Gemini API、Slack Incoming Webhook、Notion APIのキーおよび関連設定が必要です。

## 1. Google Gemini APIキーの取得

1.  [Google AI Studio](https://aistudio.google.com/) にアクセスし、Googleアカウントでサインインします。
2.  左サイドバーの「Get API Key」または「APIキーを作成」をクリックします。
3.  新しいAPIキーを作成し、コピーします。

**重要**: このAPIキーは秘密として扱ってください。

## 2. GoogleアラートのRSSフィードURLの取得

1.  [Googleアラート](https://www.google.com/alerts) にアクセスし、Googleアカウントでサインインします。
2.  監視したいキーワード（例: "AI"）でアラートを作成します。
3.  アラート作成後、アラートリストの右側にある歯車アイコン（設定）をクリックし、「RSSフィード」のアイコンをクリックします。
4.  表示されたRSSフィードのURLをコピーします。複数のキーワードでアラートを作成し、それぞれのRSSフィードURLをカンマ区切りで環境変数に設定できます。

## 3. Slack Incoming Webhook URLの取得

Slackにメッセージを送信するために、Incoming Webhook URLを設定します。

1.  **Slackアプリの作成**: [Slack APIサイト](https://api.slack.com/apps) にアクセスし、Slackアカウントでサインインします。「Create New App」をクリックし、「From scratch」を選択します。
2.  **アプリ名の設定とワークスペースの選択**: アプリケーションの名前を入力し、インストール先のSlackワークスペースを選択して「Create App」をクリックします。
3.  **Incoming Webhooksの有効化**: アプリ作成後、設定ページにリダイレクトされます。左サイドバーで「Incoming Webhooks」を見つけてクリックし、「Activate Incoming Webhooks」を「On」に切り替えます。
4.  **ワークスペースへの新しいWebhookの追加**: 設定ページが更新されたら、「Webhook URLs for Your Workspace」セクションまでスクロールし、「Add New Webhook to Workspace」ボタンをクリックします。
5.  **チャンネルの選択**: メッセージの送信先となる特定のチャンネルを選択し、「Allow」または「Authorize」をクリックします。プライベートチャンネルに追加する場合は、事前にそのチャンネルのメンバーである必要があります。
6.  **Webhook URLのコピー**: 承認後、Incoming Webhooks設定ページに戻ります。「Webhook URLs for Your Workspace」の下に生成された一意のIncoming Webhook URLが表示されますので、これをコピーします。このURLが、外部アプリケーションからSlackにメッセージを送信するために使用されます。

**重要**: このURLは秘密として扱ってください。このURLを知っている人は誰でも、追加の認証なしに定義されたSlackチャンネルにメッセージを送信できます。

## 4. Notion APIキー (内部インテグレーションシークレット) の取得

Notionデータベースと連携するために、内部インテグレーションシークレットを取得します。

1.  **インテグレーションダッシュボードへのアクセス**: [Notionのインテグレーションダッシュボード](https://www.notion.com/my-integrations) にアクセスします。
2.  **新しいインテグレーションの作成**: 「+ New integration」ボタンをクリックします。
3.  **インテグレーションの設定**: インテグレーションの名前を入力し、必要に応じてロゴをアップロードし、関連するNotionワークスペースを選択します。
4.  **機能の設定**: 「Capabilities」タブに移動し、必要な権限（例: コンテンツの読み取り、コンテンツの更新、コンテンツの挿入、メールアドレスなしのユーザー情報）を選択します。変更を保存することを忘れないでください。
5.  **シークレットの取得**: インテグレーション作成後、インテグレーション設定内の「Secrets」または「Configuration」タブに移動します。ここに「Internal Integration Token」（APIシークレットとも呼ばれます）が表示されますので、これをコピーします。
6.  **ページ権限の付与**: インテグレーションがNotionワークスペース内の特定のページやデータベースとやり取りできるようにするには、それらのページをインテグレーションと明示的に共有する必要があります。対象のNotionページにアクセスし、「...」（その他）メニューをクリックし、「+ Add Connections」までスクロールして、作成したインテグレーションを選択します。

**注意**: 2024年9月25日以降、Notionの公開APIトークン形式が更新され、`secret_`の代わりに`ntn_`プレフィックスを使用するようになりましたが、内部インテグレーションのシークレット取得プロセスは変更されていません。既存の`secret_`トークン（内部インテグレーションシークレットを含む）は引き続き機能します。

## 5. NotionデータベースIDの取得

プロジェクトが連携するNotionデータベースのIDを取得します。

1.  Notionで対象のデータベースページを開きます。
2.  ブラウザのアドレスバーに表示されるURLを確認します。URLは通常 `https://www.notion.so/{workspace_name}/{database_id}?v={view_id}` のような形式です。
例: `https://www.notion.so/291a8159567e800f8e3fc699f35eefdd?v=291a8159567e808fb0e8000c5ba3b102&source=copy_link`
3.  `{database_id}` の部分がデータベースIDです。これをコピーします。

## 6. Notionデータベースの設定

プロジェクトが正しく動作するためには、Notionデータベースに以下のプロパティが設定されている必要があります。もし存在しない場合は、データベースに手動で追加してください。

*   **Name**: タイプは「Title」
*   **Date**: タイプは「Date」
*   **Status**: タイプは「Status」。少なくとも「Published」という名前のオプションが含まれている必要があります。
*   **Abstract**: タイプは「Rich text」
*   **URL**: タイプは「URL」

これらのプロパティ名は、`src/write_to_notion.py` 内で環境変数 `NOTION_PROPERTY_NAME`, `NOTION_PROPERTY_DATE`, `NOTION_PROPERTY_STATUS`, `NOTION_PROPERTY_ABSTRACT`, `NOTION_PROPERTY_URL` を設定することでカスタマイズ可能です。