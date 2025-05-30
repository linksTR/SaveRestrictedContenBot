# restricted_content_handler.py

import os
import json
import time
import threading
import re
from pyrogram.errors import UserAlreadyParticipant, InviteHashExpired, UsernameNotOccupied
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, User # Message ve User tiplerini import edin

# --- Yardimci Fonksiyonlar ---
# Bu fonksiyonlar, ana isleyici fonksiyon tarafindan kullanilacaktir.
# Baslarindaki '_' isareti, onlarin bu module ozel oldugunu gosterir.

def _get_config_value(key: str):
    """
    config.json dosyasindan veya ortam degiskenlerinden bir anahtar degerini alir.
    """
    # Bu fonksiyon sadece bir kez calistirilacagi varsayilarak
    # config.json'i her cagirimda okumak yerine daha verimli bir yapi kurulabilir.
    # Ancak basitlik icin bu sekilde birakilmistir.
    try:
        with open('config.json', 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        # print("Uyari: config.json dosyasi bulunamadi. Ortam degiskenleri kontrol ediliyor.")
        data = {}
    return os.environ.get(key) or data.get(key, None)

def _downstatus_thread(bot_client: Client, statusfile: str, message_obj: Message):
    """
    Indirme durumunu izler ve Telegram'da mesaji gunceller.
    Ayri bir thread'de calismalidir.
    """
    while not os.path.exists(statusfile):
        time.sleep(1) # Dosyanin olusmasini bekle
    time.sleep(3) # Dosyanin yazilmasina izin vermek icin kisa bir gecikme
    while os.path.exists(statusfile):
        try:
            with open(statusfile, "r") as f:
                txt = f.read()
            bot_client.edit_message_text(message_obj.chat.id, message_obj.id, f"__Indiriliyor__ : **{txt}**")
            time.sleep(10) # Guncellemeler arasinda daha uzun bekleme
        except Exception:
            time.sleep(5) # Hata durumunda kisa bekleme

def _upstatus_thread(bot_client: Client, statusfile: str, message_obj: Message):
    """
    Yukleme durumunu izler ve Telegram'da mesaji gunceller.
    Ayri bir thread'de calismalidir.
    """
    while not os.path.exists(statusfile):
        time.sleep(1) # Dosyanin olusmasini bekle
    time.sleep(3) # Dosyanin yazilmasina izin vermek icin kisa bir gecikme
    while os.path.exists(statusfile):
        try:
            with open(statusfile, "r") as f:
                txt = f.read()
            bot_client.edit_message_text(message_obj.chat.id, message_obj.id, f"__Yukleniyor__ : **{txt}**")
            time.sleep(10) # Guncellemeler arasinda daha uzun bekleme
        except Exception:
            time.sleep(5) # Hata durumunda kisa bekleme

def _progress_callback(current: int, total: int, message_obj: Message, file_type: str):
    """
    Pyrogram indirme/yukleme ilerlemesi icin dosya yazar.
    """
    try:
        with open(f'{message_obj.id}{file_type}status.txt', "w") as f:
            f.write(f"{current * 100 / total:.1f}%")
    except Exception as e:
        print(f"Ilerleme dosyasina yazma hatasi: {e}")

def _get_message_content_type(msg: Message):
    """Bir Pyrogram mesajinin icerik turunu dondurur."""
    if msg.document: return "Document"
    if msg.video: return "Video"
    if msg.animation: return "Animation"
    if msg.sticker: return "Sticker"
    if msg.voice: return "Voice"
    if msg.audio: return "Audio"
    if msg.photo: return "Photo"
    if msg.text: return "Text"
    return "Unknown"

# --- Ana Isleyici Fonksiyon ---

async def handle_telegram_content(bot_client: Client, message: Message, userbot_client: Client = None):
    """
    Kisitli veya genel Telegram icerik linklerini isler ve kullaniciya gonderir.

    Parametreler:
        bot_client (Client): Ana bot istemcisi.
        message (Message): Gelen Telegram mesaji objesi.
        userbot_client (Client, istege bagli): Ozel kanallardan/botlardan cekmek icin userbot istemcisi.
    """
    if not message.text:
        return # Sadece metin mesajlariyla ilgileniyoruz

