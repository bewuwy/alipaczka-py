import difflib


new = """Tracking przewoźnika
Data Lokalizacja Opis
2020-11-26 05:28:35 Nadejście do sortowni
2020-11-26 05:28:35 Opuszczenie magazynu łączenia przesyłek
2020-11-26 06:04:37 Opuszczenie sortowni
Sprawdź naszą stronę promocyjną ze wszystkimi niezbędnymi informacjami, kodami i kuponami aliexpress! Dostępna tutaj -> alipaczka.pl/alipromocje"""


old = """Tracking przewoźnika
Data Lokalizacja Opis
2020-11-26 05:28:35 Nadejście do sortowni
Black Friday na aliexpress! Sprawdź naszą stronę promocyjną ze wszystkimi niezbędnymi informacjami, kodami i kuponami aliexpress! Dostępna tutaj -> alipaczka.pl/alipromocje"""


added = []
removed = []
for i in difflib.ndiff(old, new):
    if i[0] == "":
        continue
    elif i[0] == "+":
        added.append(i[-1])
    elif i[0] == "-":
        removed.append(i[-1])

print("+")
print("".join(added))

print("-")
print("".join(removed))
