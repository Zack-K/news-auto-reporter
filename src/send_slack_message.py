import requests
import json
import os


def send_slack_message(
    webhook_url, channel, notion_report_url, news_articles, report_date, closing_comment
):
    message_blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"AIニュースレポート - {report_date}",
                "emoji": True,
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "データサイエンス、データエンジニアリング、データ分析の学習者の皆さん、最新のAIニュースで知識をアップデートし、日々の学習に活かしましょう！今日のニュースが、皆さんの次のステップへのヒントになることを願っています。",
            },
        },
        {"type": "divider"},
    ]

    # カテゴリごとにニュースを整理
    categories = {}
    for article in news_articles:
        category = article.get("category", "その他")
        if category not in categories:
            categories[category] = []
        categories[category].append(article)

    for category, articles in categories.items():
        message_blocks.append(
            {"type": "section", "text": {"type": "mrkdwn", "text": f"*【{category}】*"}}
        )
        for article in articles:
            message_blocks.append(
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*<{article['url']}|{article['title']}>*\n{article['summary']}",
                    },
                }
            )
            if article.get("points"):
                points_list_formatted = [f"- {p}" for p in article["points"]]
                points_text_block = "*初学者向けポイント:*\n" + "\n".join(
                    points_list_formatted
                )
                message_blocks.append(
                    {
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": points_text_block},
                    }
                )
            # 個別の記事に対する「会話を促すコメント」のブロックは削除

            message_blocks.append({"type": "divider"})

    if notion_report_url:
        message_blocks.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"Notionで詳細を見る: <{notion_report_url}|AIニュースレポート - {report_date}>",
                },
            }
        )
    
    # クロージングコメントを追加
    if closing_comment:
        message_blocks.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": closing_comment,
                },
            }
        )

    slack_data = {"channel": channel, "blocks": message_blocks}

    try:
        response = requests.post(
            webhook_url,
            data=json.dumps(slack_data),
            headers={"Content-Type": "application/json"},
        )
        response.raise_for_status()
        print("Slack通知が正常に送信されました。")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Slack通知の送信中にエラーが発生しました: {e}")
        print(f"レスポンス: {response.text if response else 'N/A'}")
        return False


if __name__ == "__main__":
    # 仮のデータ。実際には前のフェーズで収集したニュースデータとNotion URLを使用。
    news_articles = [
        {
            "title": "Solving virtual machine puzzles: How AI is optimizing cloud computing",
            "url": "https://research.google/blog/solving-virtual-machine-puzzles-how-ai-is-optimizing-cloud-computing/",
            "category": "データエンジニアリング",
            "summary": "Google AIは、AIを活用してクラウドコンピューティングにおける仮想マシンの最適化を行う方法について発表しました。AIが複雑なリソース割り当ての問題を解決し、効率を向上させる可能性を探ります。",
        },
        {
            "title": "Using AI to identify genetic variants in tumors with DeepSomatic",
            "url": "https://research.google/blog/using-ai-to-identify-genetic-variants-in-tumors-with-deepsomatic/",
            "category": "データ分析",
            "summary": "Google AIは、DeepSomaticというAIモデルを使用して腫瘍内の遺伝子変異を特定する研究を発表しました。これにより、がん研究と診断の精度向上に貢献することが期待されます。",
        },
        {
            "title": "Coral NPU: A full-stack platform for Edge AI",
            "url": "https://google.com/blog/coral-npu-a-full-stack-platform-for-edge-ai/",
            "category": "データエンジニアリング",
            "summary": "Googleは、エッジAI向けのフルスタックプラットフォームであるCoral NPUを発表しました。デバイス上でのAI処理を高速化し、リアルタイムアプリケーションの可能性を広げます。",
        },
        {
            "title": "Sora 2 is here",
            "url": "https://openai.com/news/sora-2-is-here",
            "category": "人工知能",
            "summary": "OpenAIは、テキストから動画を生成するAIモデルSoraの次世代バージョンSora 2を発表しました。より高品質で長尺な動画生成が可能になり、クリエイティブな表現の幅を広げます。",
        },
        {
            "title": "Introducing gpt-realtime and Realtime API updates for production voice agents",
            "url": "https://openai.com/news/introducing-gpt-realtime-and-realtime-api-updates",
            "category": "人工知能",
            "summary": "OpenAIは、リアルタイム音声エージェント向けのgpt-realtimeモデルとAPIアップデートを発表しました。これにより、より自然で応答性の高い会話型AIの構築が可能になります。",
        },
        {
            "title": "Introducing GPT-5",
            "url": "https://openai.com/news/introducing-gpt-5",
            "category": "人工知能",
            "summary": "OpenAIは、次世代の基盤モデルGPT-5を発表しました。GPT-4を上回る性能と機能を持つとされ、様々な応用分野でのさらなる進化が期待されます。",
        },
        {
            "title": "How the NPU is paving the way toward a more intelligent Windows",
            "url": "https://news.microsoft.com/source/features/ai/how-the-npu-is-paving-the-way-toward-a-more-intelligent-windows/",
            "category": "データエンジニアリング",
            "summary": "Microsoftは、NPU（Neural Processing Unit）がWindowsのインテリジェンス向上にどのように貢献しているかを紹介しています。NPUにより、AI機能がデバイス上で効率的に実行され、ユーザー体験が向上します。",
        },
        {
            "title": "6 surprising ways a new AI agent can help you crush it at work",
            "url": "https://news.microsoft.com/source/features/ai/6-surprising-ways-a-new-ai-agent-can-help-you-crush-it-at-work/",
            "category": "データ分析",
            "summary": "Microsoftは、新しいAIエージェントが仕事の生産性を向上させる6つの方法を提案しています。AIを活用したアシスタントが、情報収集、分析、レポート作成などを効率化します。",
        },
        {
            "title": "Can We Save the AI Economy?",
            "url": "https://towardsdatascience.com/can-we-save-the-ai-economy/",
            "category": "人工知能",
            "summary": "Towards Data Scienceの記事では、AIエコノミーの現状と課題について考察しています。AIの過剰な期待と実用性とのギャップ、そしてその経済的影響について議論しています。",
        },
        {
            "title": "Python 3.14 and the End of the GIL",
            "url": "https://towardsdatascience.com/python-3-14-and-the-end-of-the-gil/",
            "category": "データエンジニアリング",
            "summary": "Towards Data Scienceの記事では、Python 3.14で導入されるGIL（Global Interpreter Lock）の変更点と、それがPythonの並列処理性能に与える影響について解説しています。",
        },
    ]

    # Notion URLは仮のプレースホルダー
    notion_url_placeholder = "[NotionレポートURLは現在利用できません]"

    # Slack Webhook URLとチャンネル名は環境変数または直接指定
    SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL")
    SLACK_CHANNEL = os.environ.get("SLACK_CHANNEL", "#general")  # デフォルトは #general

    if SLACK_WEBHOOK_URL is None:
        print("エラー: SLACK_WEBHOOK_URL 環境変数が設定されていません。")
    else:
        send_slack_message(
            SLACK_WEBHOOK_URL, SLACK_CHANNEL, notion_url_placeholder, news_articles
        )
