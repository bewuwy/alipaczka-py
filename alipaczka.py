import smtplib
import ssl
import requests
from bs4 import BeautifulSoup
from email.message import EmailMessage
import json
from os.path import exists


def check_tracking(tracking_number):
    print('\n' + '-' * 20)
    print(tracking_number)
    url = f"https://alipaczka.pl/pobierz.php?q={tracking_number}"

    soup = BeautifulSoup(requests.get(url).content, "html.parser")
    print()

    tracking_info = []
    panel = soup.find("div", class_="panel")
    if panel is None:
        print("wrong tracking number!")
        return "Wrong tracking number!"

    table = panel.find("table")
    for i in table:
        if i.find_all("td"):
            print(f'{i.find_all("td")[0].text} {i.find_all("td")[2].text}')
            tracking_info.append(f'{i.find_all("td")[0].text} {i.find_all("td")[2].text}')

    print()
    tracking_info = "\n".join(tracking_info)
    print("loaded tracking info from https://alipaczka.pl!")

    return tracking_info


def check_difference(tracking_number, tracking_info):
    with open("data.json", "r") as fp:
        old_data = json.load(fp)

    old_info = ""
    if tracking_number in old_data:
        old_info = old_data[tracking_number]
    print("loaded old tracking info from data.json")

    changes = tracking_info.split("\n")
    old_info = old_info.split("\n")

    for i in old_info:
        if i in changes:
            changes.remove(i)

    if changes:
        old_data[tracking_number] = tracking_info
        with open("data.json", "w") as fp:
            json.dump(old_data, fp, indent=4)

        changes_str = "\n".join(changes)
        print(f"\nchanges in tracking info: \n{changes_str}")

        return changes_str, "\n".join(old_info)
    else:
        print("no changes")
        return None, "\n".join(old_info)


def send_email(email, pass_, changes, t_info, receiver, old_t_info, p_name, p_number):
    port = 465
    context = ssl.create_default_context()
    if p_name != "":
        p_name = f"({p_name})"

    with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
        try:
            server.login(email, pass_)
        except smtplib.SMTPAuthenticationError:
            print(f"authentication failed! retrying to log into {email} in 60 seconds")
            quit(1)

        msg = EmailMessage()
        msg.set_content(f"Changes in tracking info of package {p_number} {p_name}:\n"
                        f"\n{changes}"
                        f"\n\nNew tracking info: \n\n{t_info}"
                        f"\n\nOld tracking info: \n\n{old_t_info}")
        msg['Subject'] = f'Package Tracking Update! {p_name}'
        msg["To"] = receiver
        msg["From"] = "alipaczka.pl Notifier"

        server.sendmail(email, receiver, msg.as_string())
        print(f"\nemail sent to {receiver}!")

        server.close()


if __name__ == "__main__":
    if not exists("config.json"):
        with open("config.json", "w") as f:
            json.dump({"gmail": "my@gmail.com", "gmail_pass": "myPassword"}, f, indent=4)
    if not exists("check.json"):
        with open("check.json", "w") as f:
            json.dump({"my@email.com": [["PL123456", "my package #1"]]}, f, indent=4)

            print("add some packages to track in check.json file")
            quit(0)
    else:
        with open("check.json") as f:
            check_list = json.load(f)
    if not exists("data.json"):
        with open("data.json", "w") as f:
            json.dump({}, f, indent=4)

    with open("config.json") as f:
        config = json.load(f)

    if not check_list:
        print("add some packages to track in check.json file")
        quit(0)

    for i in check_list:
        print("=" * 30)
        print(i)
        print("=" * 30)

        for z in range(len(check_list[i])):
            # checking tracking info
            number = check_list[i][z][0]
            info = check_tracking(number)
            difference, old = check_difference(number, info)
            name = check_list[i][z][1]

            # sending email
            if difference:
                send_email(config["gmail"], config["gmail_pass"], difference, info, i, old, name, number)
