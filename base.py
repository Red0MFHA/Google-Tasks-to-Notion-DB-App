from TasksAPI import create_service
from NotionAPI import notion, NOTION_DATABASE_ID
import time
service = create_service()

# --- Helper functions for Notion ---

def fetch_existing_notion_tasks():
    """Fetch all tasks currently in Notion DB and return dict keyed by Name + List."""
    existing = {}
    has_more = True
    cursor = None

    while has_more:
        response = notion.databases.query(
            database_id=NOTION_DATABASE_ID,
            start_cursor=cursor
        )
        for row in response["results"]:
            props = row["properties"]
            name = props["Name"]["title"][0]["text"]["content"] if props["Name"]["title"] else None
            tasklist = props["List"]["rich_text"][0]["text"]["content"] if props["List"]["rich_text"] else None

            if name and tasklist:
                existing[(name, tasklist)] = {
                    "id": row["id"],
                    "Status": props["Status"]["select"]["name"] if props["Status"]["select"] else None,
                    "Description": props["Description"]["rich_text"][0]["text"]["content"] if props["Description"]["rich_text"] else None,
                    "Start Date": props["Start Date"]["date"]["start"] if props["Start Date"]["date"] else None,
                    "Due Date": props["Due Date"]["date"]["start"] if props["Due Date"]["date"] else None,
                    "Completed At": props["Completed At"]["date"]["start"] if props["Completed At"]["date"] else None,
                    "Updated At": props["Updated At"]["date"]["start"] if props["Updated At"]["date"] else None,
                }

        has_more = response.get("has_more", False)
        cursor = response.get("next_cursor", None)

    return existing


def task_to_properties(task, tasklist_name):
    """Convert Google Task object to Notion DB properties format."""
    return {
        "Name": {"title": [{"text": {"content": task.get("title", "Untitled")}}]},
        "List": {"rich_text": [{"text": {"content": tasklist_name}}]},
        "Status": {"select": {"name": task.get("status")}},
        "Description": {"rich_text": [{"text": {"content": task.get("notes", "")}}]} if task.get("notes") else None,
        "Start Date": {"date": {"start": task.get("start")}} if task.get("start") else None,
        "Due Date": {"date": {"start": task.get("due")}} if task.get("due") else None,
        "Completed At": {"date": {"start": task.get("completed")}} if task.get("completed") else None,
        "Updated At": {"date": {"start": task.get("updated")}} if task.get("updated") else None,
    }


def update_notion_task(page_id, properties):
    """Update a Notion task by page_id."""
    notion.pages.update(page_id=page_id, properties={k: v for k, v in properties.items() if v})


def insert_notion_task(properties):
    """Insert a new task into Notion DB."""
    notion.pages.create(parent={"database_id": NOTION_DATABASE_ID},
                        properties={k: v for k, v in properties.items() if v})


# --- Main logic ---
def Main_Tasks_to_Notion():
    # Gets existing Notion tasks
    notion_tasks = fetch_existing_notion_tasks()

    # Fetches Google tasklists
    tasklists = []
    page_token = None
    while True:
        response = service.tasklists().list(maxResults=10, pageToken=page_token).execute()
        tasklists.extend(response.get("items", []))
        page_token = response.get("nextPageToken")
        if not page_token:
            break

    for t in tasklists:
        tasks = service.tasks().list(tasklist=t["id"], showCompleted=True, showHidden=True).execute()
        items = tasks.get("items", [])

        for task in items:
            key = (task["title"], t["title"])  # Identifies uniqueness by (task name + list)

            properties = task_to_properties(task, t["title"])

            if key in notion_tasks:
                # Checks if anything changed
                notion_record = notion_tasks[key]
                has_changes = False
                for field in ["Status", "Description", "Start Date", "Due Date", "Completed At", "Updated At"]:
                    val = None
                    prop = properties.get(field)

                    if not prop:
                        new_val = None
                    elif field.endswith("Date"):
                        new_val = prop.get("date", {}).get("start")
                    elif field == "Status":
                        new_val = prop.get("select", {}).get("name")
                    elif field in ["Description"]:
                        new_val = prop.get("rich_text", [{}])[0].get("text", {}).get("content")
                    else:
                        new_val = None

                    if notion_record.get(field) != new_val:
                        has_changes = True
                        break

                if has_changes:
                    print(f"Updating task: {task['title']} in list {t['title']}")
                    update_notion_task(notion_record["id"], properties)
                else:
                    print(f"No change for task: {task['title']} in list {t['title']}")
            else:
                print(f"Inserting new task: {task['title']} in list {t['title']}")
                insert_notion_task(properties)


#now the loop for 10 minutes


if __name__ == "__main__":
    while True:
        sleep_Time = 600
        try:
            print("\nStarting sync at", time.ctime())
            Main_Tasks_to_Notion()
            print("Sync complete. Waiting 10 minutes...\n")
        except Exception as e:
            print("Error during sync:", e)

        time.sleep(sleep_Time) # 600 s means 10 minutes; the task transfer and updation runs every 10 minutes