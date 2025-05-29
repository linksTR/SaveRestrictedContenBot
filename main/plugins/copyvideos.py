import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, Chat
from pyrogram.errors import UsernameNotOccupied, PeerIdInvalid, ChannelInvalid, UserNotParticipant

# --- Yeni Komut İşleyici ---
@Client.on_message(filters.command("copyvideos") & filters.private)
async def copy_videos_between_channels(client: Client, message: Message):
    """
    Kullanıcının belirttiği kaynaktan, belirttiği hedefe videoları kopyalar.
    Kullanım: /copyvideos <kaynak_kanal_kullanici_adi_veya_id> <hedef_kanal_kullanici_adi_veya_id>
    """
    
    # Komutun doğru formatta olup olmadığını kontrol et
    if len(message.command) < 3:
        await message.reply(
            "Lütfen hem **kaynak** hem de **hedef** kanalı belirtin.\n"
            "Örnek: `/copyvideos @kaynak_kanal_adi @hedef_kanal_adi` veya "
            "`/copyvideos -100123456789 -100987654321`"
        )
        return

    source_identifier = message.command[1].strip()
    target_identifier = message.command[2].strip()

    await message.reply(
        f"'{source_identifier}' kanalındaki tüm videolar '{target_identifier}' kanalına kopyalanıyor. "
        "Bu biraz zaman alabilir ve büyük kanallar için uzun sürebilir..."
    )

    video_count = 0
    error_count = 0

    try:
        # Kaynak kanalı çözümle (ID'ye dönüştür)
        source_chat: Chat = None
        try:
            source_chat = await client.get_chat(source_identifier)
        except (UsernameNotOccupied, PeerIdInvalid, ChannelInvalid) as e:
            await message.reply(f"**Hata:** Kaynak kanal '{source_identifier}' bulunamadı veya geçersiz. Lütfen doğru bir kullanıcı adı veya ID girin. ({e})")
            return
        except UserNotParticipant:
            await message.reply(f"**Hata:** Kaynak kanal '{source_identifier}' bir gizli kanal olabilir ve botunuz üyesi değil. Lütfen botu kanala ekleyin.")
            return
        
        # Hedef kanalı çözümle (ID'ye dönüştür)
        target_chat: Chat = None
        try:
            target_chat = await client.get_chat(target_identifier)
        except (UsernameNotOccupied, PeerIdInvalid, ChannelInvalid) as e:
            await message.reply(f"**Hata:** Hedef kanal '{target_identifier}' bulunamadı veya geçersiz. Lütfen doğru bir kullanıcı adı veya ID girin. ({e})")
            return
        except UserNotParticipant:
            await message.reply(f"**Hata:** Hedef kanal '{target_identifier}' bir gizli kanal olabilir ve botunuz üyesi değil. Lütfen botu kanala ekleyin.")
            return

        # Botun hedef kanala mesaj gönderme yetkisi var mı kontrol edin (isteğe bağlı ama önerilir)
        # Eğer botunuz yönetici değilse veya mesaj gönderme izni yoksa hata alırsınız.
        # Daha sağlam bir kontrol için get_chat_member veya try-except send_message kullanabilirsiniz.

        # Kanalın tüm mesajlarını dolaş ve sadece videoları işle
        async for msg in client.get_chat_history(source_chat.id):
            if msg.video:
                try:
                    # Medyayı indir
                    # in_memory=False: dosyayı diske indirir (daha büyük dosyalar için iyi)
                    file_path = await msg.download(in_memory=False) 
                    
                    if file_path:
                        # Kendi hedef kanalınıza yeniden gönder
                        await client.send_video(
                            chat_id=target_chat.id,
                            video=file_path,
                            caption=msg.caption or "",
                            parse_mode="html" # veya "markdown", orijinal formata göre ayarlayın
                        )
                        video_count += 1
                        
                        # İndirilen geçici dosyayı sil
                        os.remove(file_path)
                        # print(f"Video '{file_path}' başarıyla gönderildi ve silindi.")
                        
                        # Aşırı yüklenmeyi önlemek için küçük bir gecikme ekleyebiliriz.
                        await asyncio.sleep(1) # Her video gönderimi sonrası 1 saniye bekle

                except Exception as e:
                    error_count += 1
                    print(f"Video işlenirken hata oluştu (Kaynak Mesaj ID: {msg.id}, Hata: {e})")
                    # Hataları kullanıcıya bildirmek için:
                    # await message.reply(f"Bir video işlenirken hata oluştu (Mesaj ID: {msg.id}): {e}")

    except Exception as e:
        await message.reply(f"**Hata:** İşlem sırasında genel bir sorun oluştu: {e}")
        print(f"Genel hata: {e}")

    await message.reply(
        f"İşlem tamamlandı! '{source_identifier}' kanalından '{target_identifier}' kanalına "
        f"toplam **{video_count}** video gönderildi, **{error_count}** hata oluştu."
    )
