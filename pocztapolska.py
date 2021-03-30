from zeep import Client
from zeep.wsse.username import UsernameToken


def get_pp_info(p_nr):
    client = Client('https://tt.poczta-polska.pl/Sledzenie/services/Sledzenie?wsdl',
                    wsse=UsernameToken("sledzeniepp", "PPSA"))
    result = client.service.sprawdzPrzesylke(p_nr)
    track_info = []

    for i in result["danePrzesylki"]["zdarzenia"]["zdarzenie"]:
        track_info.append(f"{i['czas']} - {i['nazwa']} ({i['jednostka']['nazwa']})")
        print(f"{i['czas']} - {i['nazwa']} ({i['jednostka']['nazwa']})")

    if result["danePrzesylki"]["zakonczonoObsluge"]:
        print("Skończona dostawa")
        track_info.append("Skończona dostawa")

    return track_info
