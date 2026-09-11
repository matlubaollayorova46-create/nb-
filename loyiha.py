import os

# Tizimga kirish paroli
KIRISH_PAROLI = "python2026"
# Shifrlash kaliti (harflarni nechta gachaga surish)
SHIFR_KALITI = 4

def sezar_shifrlash(matn, kalit):
    """Matnni Sezar usulida shifrlash"""
    shifrlangan = ""
    for belgi in matn:
        if belgi.isalpha():
            # Katta va kichik harflarni hisobga olamiz
            kod = ord(belgi) + kalit
            if belgi.isupper():
                if kod > ord('Z'): kod -= 26
            else:
                if kod > ord('z'): kod -= 26
            shifrlangan += chr(kod)
        else:
            shifrlangan += belgi
    return shifrlangan

def sezar_deshifrlash(matn, kalit):
    """Shifrlangan matnni asl holiga qaytarish"""
    return sezar_shifrlash(matn, -kalit)

def qayd_yozish():
    """Yangi qayd qo'shish va uni shifrlab saqlash"""
    sana = input("\nSanani kiriting (masalan, 12.05.2026): ")
    matn = input("Bugungi kun qanday o'tdi? Qaydni yozing:\n> ")
    
    toliq_matn = f"Sana: {sana}\nQayd: {matn}\n" + "-"*30 + "\n"
    shifrlangan_matn = sezar_shifrlash(toliq_matn, SHIFR_KALITI)
    
    with open("kundalik_baza.txt", "a", encoding="utf-8") as fayl:
        fayl.write(shifrlangan_matn + "===BLOK===\n")
    print("\n✅ Qayd shifrlangan holda muvaffaqiyatli saqlandi!")

def kundalikni_o_qish():
    """Shifrlangan faylni o'qib, deshifrlab ko'rsatish"""
    if not os.path.exists("kundalik_baza.txt"):
        print("\n📭 Kundalik hali bo'sh. Biror narsa yozing.")
        return
        
    print("\n📖 --- SIZNING SHAXSIY QAYDLARINGIZ ---")
    with open("kundalik_baza.txt", "r", encoding="utf-8") as fayl:
        kontent = fayl.read()
        
    bloklar = kontent.split("===BLOK===\n")
    for blok in bloklar:
        if blok.strip():
            asl_holat = sezar_deshifrlash(blok, SHIFR_KALITI)
            print(asl_holat)

def dastur():
    """Asosiy boshqaruv menyusi"""
    print("🔒 Shaxsiy shifrlangan kundalikka xush kelibsiz!")
    parol = input("Tizimga kirish parolini kiriting: ")
    
    if parol != KIRISH_PAROLI:
        print("❌ Parol noto'g'ri! Dastur yopildi.")
        return

    print("\n🔓 Kirish muvaffaqiyatli bajarildi!")
    
    while True:
        print("\n--- MENYU ---")
        print("1. Yangi qayd yozish")
        print("2. Kundalikni o'qish")
        print("3. Chiqish")
        
        tanlov = input("Tanlang (1/2/3): ")
        
        if tanlov == '1':
            qayd_yozish()
        elif tanlov == '2':
            kundalikni_o_qish()
        elif tanlov == '3':
            print("Xayr! Kundalik qulflandi. 🔒")
            break
        else:
            print("Noto'g'ri buyruq!")

# Dasturni ishga tushirish
if __name__ == "__main__":
    dastur()