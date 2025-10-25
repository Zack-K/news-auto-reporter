import os
import json
from datetime import datetime
from notion_client import Client
from notion_client.errors import APIResponseError

# Notion APIキーとデータベースID
DATABASE_ID = os.environ.get("NOTION_DATABASE_ID")

if not DATABASE_ID:
    raise ValueError(
        "NOTION_DATABASE_ID 環境変数が設定されていません。NotionデータベースIDを設定してください。"
    )

# Notionプロパティ名を環境変数から取得、デフォルトは日本語
PROP_NAME = os.environ.get("NOTION_PROPERTY_NAME", "Name")
PROP_DATE = os.environ.get("NOTION_PROPERTY_DATE", "Date")
PROP_STATUS = os.environ.get("NOTION_PROPERTY_STATUS", "Status")
PROP_ABSTRACT = os.environ.get("NOTION_PROPERTY_ABSTRACT", "Abstract")
PROP_URL = os.environ.get("NOTION_PROPERTY_URL", "URL")

def ensure_notion_database_properties(notion, database_id):
    # Define expected properties with their types and configurations
    expected_properties_config = {
        PROP_NAME: {"type": "title", "config": {"title": {}}},
        PROP_DATE: {"type": "date", "config": {"date": {}}},
        PROP_STATUS: {"type": "status", "config": {"status": {"options": [{"name": "Published", "color": "green"}]}}},
        PROP_ABSTRACT: {"type": "rich_text", "config": {"rich_text": {}}},
        PROP_URL: {"type": "url", "config": {"url": {}}}
    }

    try:
        db_info = notion.databases.retrieve(database_id=database_id)
        existing_properties = db_info["properties"]
        
        properties_to_update = {}
        needs_update_call = False

        for prop_name, expected_prop_details in expected_properties_config.items():
            expected_type = expected_prop_details["type"]
            expected_config = expected_prop_details["config"]

            if prop_name not in existing_properties:
                # Property is missing, add it
                print(f"  - プロパティ '{prop_name}' が見つかりません。作成します。")
                properties_to_update[prop_name] = expected_config
                needs_update_call = True
            else:
                # Property exists, check its type
                existing_prop_type = existing_properties[prop_name]["type"]
                if existing_prop_type != expected_type:
                    print(f"  - 警告: プロパティ '{prop_name}' は存在しますが、タイプが異なります。期待されるタイプ: '{expected_type}', 現在のタイプ: '{existing_prop_type}'。手動で修正してください。")
                    return False # Stop if type mismatch, requires manual intervention

                # Special handling for status property to ensure 'Published' option exists
                if expected_type == "status":
                    existing_status_options = existing_properties[prop_name]["status"]["options"]
                    published_option_exists = any(opt["name"] == "Published" for opt in existing_status_options)
                    
                    if not published_option_exists:
                        print(f"  - プロパティ '{prop_name}' に 'Published' オプションが見つかりません。追加します。")
                        # To add an option, we need to send the full list of options including the new one
                        # This requires a PATCH request with the full properties object for the status property
                        # This is more complex than just adding a new property.
                        # For simplicity, we'll just add the option to the existing list and update the property.
                        # Note: Notion API for updating select/status options can be tricky.
                        # A full update of the property is needed.
                        new_options = existing_status_options + [{"name": "Published", "color": "green"}]
                        properties_to_update[prop_name] = {"status": {"options": new_options}}
                        needs_update_call = True
        
        if needs_update_call:
            print(f"Notionデータベースに不足しているプロパティまたはオプションを更新中...")
            notion.databases.update(
                database_id=database_id,
                properties=properties_to_update
            )
            print("Notionデータベースのプロパティ更新が完了しました。")
        else:
            print("Notionデータベースのプロパティはすべて存在し、タイプも一致しています。")
        
        return True
    except APIResponseError as e:
        error_message = "No message provided"
        if isinstance(e.body, dict):
            error_message = e.body.get("message", error_message)
        elif isinstance(e.body, str):
            try:
                error_json = json.loads(e.body)
                error_message = error_json.get("message", error_message)
            except json.JSONDecodeError:
                error_message = e.body
        print(f"Notionデータベースプロパティの確認/作成中にエラーが発生しました: {e.code} - {error_message}. 詳細: {str(e)}")
        return False
    except Exception as e:
        print(f"予期せぬエラーが発生しました: {e}")
        return False

def create_notion_article_page(article, notion):
    # ページタイトルは記事のタイトル
    page_title = article["title"]
    article_url = article["url"]
    article_summary = article["summary"]
    article_category = article["category"]
    # 取得日はREPORT_DATEを使用
    acquisition_date = os.getenv("REPORT_DATE", datetime.now().strftime("%Y-%m-%d"))

    # Notionのページプロパティを構築
    properties = {
        PROP_NAME: {"title": [{"text": {"content": page_title, "link": {"url": article_url}}}]},
        PROP_DATE: {"date": {"start": acquisition_date}},
        PROP_STATUS: {"status": {"name": "Published"}},
        PROP_ABSTRACT: {"rich_text": [{"text": {"content": article_summary}}]}, # 要約プロパティ
        PROP_URL: {"url": article_url}, # URLプロパティ
        # PROP_CATEGORY: {"select": {"name": article_category}}, # カテゴリプロパティ (必要に応じて追加)
    }

    print(f"Attempting to create Notion page for article: {page_title}")
    print(f"Database ID: {DATABASE_ID}")
    try:
        response = notion.pages.create(
            parent={"database_id": DATABASE_ID},
            properties=properties,
        )
        print(f"Notionページが正常に作成されました: {response['url']}")
        return response["url"]
    except APIResponseError as e:
        error_message = "No message provided"
        if isinstance(e.body, dict):
            error_message = e.body.get("message", error_message)
        elif isinstance(e.body, str):
            try:
                error_json = json.loads(e.body)
                error_message = error_json.get("message", error_message)
            except json.JSONDecodeError:
                error_message = e.body
        print(f"Notion APIエラーが発生しました: {e.code} - {error_message}. 詳細: {str(e)}")
        return None
    except Exception as e:
        print(f"予期せぬエラーが発生しました: {e}")
        return None
