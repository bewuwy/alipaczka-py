from os import environ
from simplenote import Simplenote


def save_simplenote(number, t_info, client):
    found = None
    for n in client.get_note_list(data=True)[0]:
        if number in n["tags"]:
            print("updating existing note!")
            found = n

    if found is None:
        print("creating a new note!")
        found = client.add_note(t_info)[0]

    found["tags"] = [number]
    found["content"] = t_info

    client.update_note(found)


def load_simplenote(number, client):
    for n in client.get_note_list(data=True)[0]:
        if number in n["tags"]:
            return n["content"]
    return None


sn = Simplenote(environ.get("SN_USER"), environ.get("SN_PASS"))
print("logged into simplenote using username and password")

for i in sn.get_note_list(data=True)[0]:
    print(i)
    if i["deleted"] or not i["tags"]:
        sn.delete_note(i["key"])

print()

for i in sn.get_note_list(data=True)[0]:
    print(i)
