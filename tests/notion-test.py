from os import environ
from notion.client import NotionClient
from notion.block import TextBlock


client = NotionClient(token_v2=environ.get("TOKEN_V2"))

page = client.get_top_level_pages()[0]
print(page)

page.children.add_new(TextBlock, title="PL12345")
