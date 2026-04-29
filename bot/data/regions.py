REGIONS = {
    "Toshkent shahri": [
        "Bektemir", "Chilonzor", "Mirobod", "Mirzo Ulug'bek", "Olmazor",
        "Sergeli", "Shayxontohur", "Uchtepa", "Yakkasaroy", "Yashnobod",
        "Yunusobod", "Yangihayot",
    ],
    "Toshkent viloyati": [
        "Bekobod", "Bo'ka", "Bo'stonliq", "Chinoz", "Qibray",
        "Ohangaron", "Oqqo'rg'on", "Olmaliq", "Parkent", "Piskent",
        "O'rtachirchiq", "Yangiyo'l", "Yuqorichirchiq", "Zangiota", "Quyichirchiq",
        "Nurafshon", "Angren",
    ],
    "Andijon viloyati": [
        "Andijon shahri", "Asaka", "Baliqchi", "Bo'z", "Buloqboshi",
        "Izboskan", "Jalaquduq", "Xo'jaobod", "Qo'rg'ontepa", "Marhamat",
        "Oltinko'l", "Paxtaobod", "Shahrixon", "Ulug'nor",
    ],
    "Buxoro viloyati": [
        "Buxoro shahri", "Olot", "G'ijduvon", "Jondor", "Kogon",
        "Qorako'l", "Qorovulbozor", "Peshku", "Romitan", "Shofirkon",
        "Vobkent",
    ],
    "Farg'ona viloyati": [
        "Farg'ona shahri", "Marg'ilon", "Quva", "Quvasoy", "Qo'qon",
        "Bag'dod", "Beshariq", "Buvayda", "Dang'ara", "Furqat",
        "Oltiariq", "Rishton", "So'x", "Toshloq", "Uchko'prik",
        "O'zbekiston tumani", "Yozyovon",
    ],
    "Jizzax viloyati": [
        "Jizzax shahri", "Arnasoy", "Baxmal", "Do'stlik", "Forish",
        "G'allaorol", "Mirzacho'l", "Paxtakor", "Yangiobod", "Zafarobod",
        "Zarbdor", "Zomin",
    ],
    "Xorazm viloyati": [
        "Urganch", "Xiva", "Bog'ot", "Gurlan", "Hazorasp",
        "Xonqa", "Qo'shko'pir", "Shovot", "Yangiariq", "Yangibozor",
    ],
    "Namangan viloyati": [
        "Namangan shahri", "Chortoq", "Chust", "Kosonsoy", "Mingbuloq",
        "Namangan tumani", "Norin", "Pop", "To'raqo'rg'on", "Uchqo'rg'on",
        "Uychi", "Yangiqo'rg'on",
    ],
    "Navoiy viloyati": [
        "Navoiy shahri", "Karmana", "Konimex", "Navbahor", "Nurota",
        "Qiziltepa", "Tomdi", "Uchquduq", "Xatirchi",
    ],
    "Qashqadaryo viloyati": [
        "Qarshi", "Shahrisabz", "Chiroqchi", "Dehqonobod", "G'uzor",
        "Kasbi", "Kitob", "Koson", "Mirishkor", "Muborak",
        "Nishon", "Qamashi", "Yakkabog'",
    ],
    "Qoraqalpog'iston Respublikasi": [
        "Nukus", "Amudaryo", "Beruniy", "Chimboy", "Ellikqal'a",
        "Kegeyli", "Mo'ynoq", "Nukus tumani", "Qanliko'l", "Qo'ng'irot",
        "Qorao'zak", "Shumanay", "Taxiatosh", "Taxtako'pir", "To'rtko'l",
        "Xo'jayli",
    ],
    "Samarqand viloyati": [
        "Samarqand shahri", "Bulung'ur", "Ishtixon", "Jomboy", "Kattaqo'rg'on",
        "Narpay", "Nurobod", "Oqdaryo", "Paxtachi", "Payariq",
        "Pastdarg'om", "Qo'shrabot", "Samarqand tumani", "Toyloq", "Urgut",
    ],
    "Sirdaryo viloyati": [
        "Guliston", "Shirin", "Yangiyer", "Boyovut", "Mirzaobod",
        "Oqoltin", "Sayxunobod", "Sardoba", "Sirdaryo tumani", "Xovos",
    ],
    "Surxondaryo viloyati": [
        "Termiz", "Angor", "Bandixon", "Boysun", "Denov",
        "Jarqo'rg'on", "Muzrabot", "Oltinsoy", "Qiziriq", "Qumqo'rg'on",
        "Sariosiyo", "Sherobod", "Sho'rchi", "Termiz tumani", "Uzun",
    ],
}


def list_regions() -> list[str]:
    return list(REGIONS.keys())


def list_districts(region: str) -> list[str]:
    return REGIONS.get(region, [])
