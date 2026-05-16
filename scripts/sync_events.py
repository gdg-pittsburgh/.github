import json, os, requests, sys

noco_url   = os.environ["NOCO_URL"]
table_id   = os.environ["NOCO_TABLE_ID"]
noco_token = os.environ["NOCO_TOKEN"]

headers = {
    "xc-token": noco_token,
    "Content-Type": "application/json"
}

endpoint = f"{noco_url}/api/v2/tables/{table_id}/records"

SKIP_FIELDS = {"Status", "Title"}  # Title already mapped from content, Status mismatches NocoDB options

with open("project_items.json") as f:
    data = json.load(f)

items = data["data"]["organization"]["projectV2"]["items"]["nodes"]
print(f"Found {len(items)} project items")

success, failed = 0, 0

for item in items:
    content = item.get("content")
    if not content:
        print("Skipping item with no content")
        continue

    field_values = {}
    for fv in item.get("fieldValues", {}).get("nodes", []):
        field = fv.get("field", {}).get("name", "")
        value = fv.get("text") or fv.get("name") or fv.get("date")
        if field and value and field not in SKIP_FIELDS:
            field_values[field] = value

    record = {
        "Title":       content.get("title", ""),
        "Description": content.get("body", ""),
        "URL":         content.get("url", ""),
        "Created":     content.get("createdAt", ""),
        "Labels":      ", ".join(l["name"] for l in content.get("labels", {}).get("nodes", [])),
    }

    record.update(field_values)

    resp = requests.post(endpoint, headers=headers, json=record)
    if resp.status_code in (200, 201):
        print(f"  Created: {record['Title']}")
        success += 1
    else:
        print(f"  FAILED: {record['Title']} — {resp.status_code} {resp.text}")
        failed += 1

print(f"\nDone. {success} created, {failed} failed.")
sys.exit(1 if failed > 0 else 0)
