# main/plugins/get_videos.py

from pyrogram import Client, filters
from pyrogram.types import Message
import asyncio
import os

# --- Yapılandırma ---
# Botun videoları göndereceği hedef kanal ID'si.
# Bunu bir ENV değişkeni olarak ayarlamak en iyisidir.
# Örneğin, RENDER_TARGET_VIDEO_CHANNEL_ID = -100123456789
TARGET_VIDEO_OUTPUT_CHANNEL_ID = int(os.environ.get("RENDER_TARGET_VIDEO_CHANNEL_ID", YOUR_DEFAULT_OUTPUT_CHANNEL_ID)) # Varsayılan bir değer verin veya hata fırlatın

# --- Komut İşleyici ---
@Client.on_message(filters.command("getvideos") & filters.private)
async def get_all_videos_from_channel(client: Client, message: Message):
    # Komutun doğru formatta olup olmadığını kontrol et
    if len(message.command) < 2:
        await message.reply("Lütfen hangi kanaldan video çekileceğini belirtin. Örnek: `/getvideos @kanal_kullanici_adi`")
        return

    source_channel_identifier = message.command[1].strip() # @kanal_kullanici_adi veya kanal ID'si

    await message.reply(f"'{source_channel_identifier}' kanalındaki tüm videolar taranıyor ve gönderiliyor. Bu biraz zaman alabilir...")

    video_count = 0
    error_count = 0

    try:
        # Kanalı resolution et (ID'ye dönüştür)
        try:
            source_channel = await client.get_chat(source_channel_identifier)
            source_channel_id = source_channel.id
        except Exception as e:
            await message.reply(f"Kanal bulunamadı veya erişilemiyor: {source_channel_identifier}. Hata: {e}")
            return

        # Kanalın tüm mesajlarını dolaş
        # filter=filters.video ile sadece videoları çekiyoruz
        async for msg in client.get_chat_history(source_channel_id):
            if msg.video:
                try:
                    # Medyayı indir
                    file_path = await msg.download(in_memory=False) # Geçici bir dosyaya indir
                    
                    if file_path:
                        # Kendi hedef kanalınıza yeniden gönder
                        await client.send_video(
                            chat_id=TARGET_VIDEO_OUTPUT_CHANNEL_ID,
                            video=file_path,
                            caption=msg.caption or "",
                            parse_mode="html"
                        )
                        video_count += 1
                        
                        # İndirilen geçici dosyayı sil
                        os.remove(file_path)
                        print(f"Video '{file_path}' başarıyla gönderildi ve silindi.")
                        
                        # Aşırı yüklenmeyi önlemek için küçük bir gecikme ekleyebiliriz.
                        await asyncio.sleep(1) # Her video gönderimi sonrası 1 saniye bekle

                except Exception as e:
                    error_count += 1
                    print(f"Video işlenirken hata oluştu (Mesaj ID: {msg.id}): {e}")
                    # Hataları kullanıcıya bildirmek için:
                    # await message.reply(f"Bir video işlenirken hata oluştu (Mesaj ID: {msg.id}): {e}")

    except Exception as e:
        await message.reply(f"Genel bir hata oluştu: {e}")
        print(f"Genel hata: {e}")

    await message.reply(f"İşlem tamamlandı! Toplam {video_count} video gönderildi, {error_count} hata oluştu.")
