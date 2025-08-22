from notion_client import Client # install using from notion_client import Client


# Seting Notion Integration Token here
NOTION_TOKEN = "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" # from https://www.notion.so/profile/integrations
NOTION_DATABASE_ID = "254e42734388808badc4f5bc4297b4ad" # from the link name of database

# Initializing Notion client
notion = Client(auth=NOTION_TOKEN)