import difflib
import smtplib
import ssl
from email.message import EmailMessage
from os import environ
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
import json
import gkeepapi
from simplenote import Simplenote
import time


def load_info_keep(keep, p_number):
    gnotes = keep.find(query=p_number)

    for g in gnotes:
        if g.title == p_number:
            return g.text

    return None


def save_info_keep(keep, p_number, p_info):
    gnotes = keep.find(query=p_number)

    for n in gnotes:
        if n.title == p_number:
            n.delete()

    keep.createNote(p_number, p_info)
    keep.sync()


def login_keep(gmail_address, google_pass):
    gkeep = gkeepapi.Keep()
    try:
        gkeep.login(gmail_address, google_pass)
        print("logged to keep using email and password")
    except gkeepapi.exception.LoginException:
        print("GOOGLE KEEP: BAD AUTHENTICATION")
        print("APP WON'T WORK PROPERLY")
        print("TRY USING SIMPLENOTE")
        gkeep = None

    return gkeep


def login_simplenote(user, pass_):
    print("logged into simplenotes using email and password!")
    return Simplenote(user, pass_)


def load_simplenote(number, client):
    for n in client.get_note_list(data=True)[0]:
        if number in n["tags"]:
            return n["content"]
    return ""


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


def check_tracking(tracking_number):
    options = Options()
    options.headless = True
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.binary_location = environ.get("GOOGLE_CHROME_BIN")
    chrome_driver = webdriver.Chrome(options=options)  # , executable_path=environ.get("CHROMEDRIVER"))

    print('\n' + '-' * 20)
    print(tracking_number)
    url = "https://alipaczka.pl/?track="

    chrome_driver.get(url + tracking_number)

    try:
        elem = WebDriverWait(chrome_driver, 3).until(ec.presence_of_element_located((By.CLASS_NAME, 'panel')))
    except TimeoutException:
        print("Error while trying to read tracking info!")
        chrome_driver.save_screenshot("test\\error.png")
        return None

    tracking_info = elem.text
    print("loaded tracking info from https://alipaczka.pl!")

    chrome_driver.quit()
    return tracking_info


def difference(new_t, old_t):
    added = []
    removed = []
    for i in difflib.ndiff(old_t, new_t):
        if i[0] == "":
            continue
        elif i[0] == "+":
            added.append(i[-1])
        elif i[0] == "-":
            removed.append(i[-1])
    added = "".join(added)
    removed = "".join(removed)
    return added, removed


def check_difference_keep(keep, tracking_number, tracking_info):
    old_tracking_info = load_info_keep(keep, tracking_number)
    print("loaded old tracking info from keep!")

    added, removed = difference(tracking_info, old_tracking_info)
    change = "+ " + added + "\n- " + removed

    if added or removed:
        save_info_keep(keep, tracking_number, tracking_info)
        print(f"changes in tracking info: \n{change}")

    return change, old_tracking_info


def check_difference_simplenote(sn, tracking_number, tracking_info):
    old_info = load_simplenote(tracking_number, sn)
    print("loaded old tracking info from simplenotes!")

    added, removed = difference(tracking_info, old_info)
    change = "+ " + added + "\n- " + removed

    if added or removed:
        save_simplenote(tracking_number, tracking_info, sn)
        print(f"\nchanges in tracking info: \n{change}")

    return change, old_info


def send_email(email, pass_, changes, t_info, receiver, old_t_info, p_name, p_number):
    port = 465
    context = ssl.create_default_context()
    if p_name != "":
        p_name = f"({p_name})"

    with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
        while True:
            try:
                server.login(email, pass_)
                break
            except smtplib.SMTPAuthenticationError:
                print(f"authentication failed! retrying to log into {email} in 60 seconds")
                time.sleep(60)

        msg = EmailMessage()
        msg.set_content(f"Changes in tracking info of package {p_number} {p_name}:"
                        f"\n{changes}"
                        f"\n\nNew tracking info: \n\n{t_info}"
                        f"\n\nOld tracking info: \n\n{old_t_info}")
        msg['Subject'] = f'Package Tracking Update! {p_name}'
        msg["To"] = receiver
        msg["From"] = "alipaczka.pl Notifier"

        server.sendmail(email, receiver, msg.as_string())
        print(f"\nemail sent to {receiver}!")

        server.close()


def check_keep(check_list, gmail_address, google_pass):
    gkeep = login_keep(gmail_address, google_pass)

    for i in check_list:
        print("=" * 30)
        print(i)
        print("=" * 30)

        for z in range(len(check_list[i])):
            # checking tracking info
            number = check_list[i][z][0]
            info = check_tracking(number)
            diff, old = check_difference_keep(gkeep, number, info)

            name = ""
            if len(check_list[i][z]) > 1:
                name = check_list[i][z][1]

            # sending email
            if diff:
                send_email(gmail_address, google_pass, diff, info, i, old, name, number)
            else:
                print("\nno differences!")


def check_simplenote(check_list, gmail_address, google_pass, sn_user, sn_pass):
    client = login_simplenote(sn_user, sn_pass)

    for i in check_list:
        print("=" * 30)
        print(i)
        print("=" * 30)

        for z in range(len(check_list[i])):
            # checking tracking info
            number = check_list[i][z][0]
            info = check_tracking(number)
            diff, old = check_difference_simplenote(client, number, info)

            name = ""
            if len(check_list[i][z]) > 1:
                name = check_list[i][z][1]

            # sending email
            if diff != "+ \n- ":
                send_email(gmail_address, google_pass, diff, info, i, old, name, number)
            else:
                print("\nno differences!")


if __name__ == "__main__":
    with open("check.json") as f:
        c_list = json.load(f)

    while True:
        # keep version (not working on vps :c)
        # check_keep(c_list, environ.get("MAIL"), environ.get("GOOGLE_PASS"))

        check_simplenote(c_list, environ.get("MAIL"), environ.get("GOOGLE_PASS"),
                         environ.get("SN_USER"), environ.get("SN_PASS"))

        print("\n")
        print('-' * 30)
        print("next check in 60 minutes!")
        print('-' * 30)

        time.sleep(60 * 60)
