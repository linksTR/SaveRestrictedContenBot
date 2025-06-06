#Github.com-Vasusen-code

import asyncio, time, os

from .. import bot as Drone
from main.plugins.progress import progress_for_pyrogram
from main.plugins.helpers import screenshot

from pyrogram import Client, filters
from pyrogram.errors import ChannelBanned, ChannelInvalid, ChannelPrivate, ChatIdInvalid, ChatInvalid, PeerIdInvalid
from pyrogram.enums import MessageMediaType
from pyrogram.types import InputMediaPhoto, InputMediaVideo, InputMediaDocument, InputMediaAudio, InputMediaAnimation, InputMessageContent
from ethon.pyfunc import video_metadata
from ethon.telefunc import fast_upload
from telethon.tl.types import DocumentAttributeVideo
from telethon import events

def thumbnail(sender):
    if os.path.exists(f'{sender}.jpg'):
        return f'{sender}.jpg'
    else:
         return None
      
def remove_file(file_paths):
    for file_name in file_paths :
        try:
            os.remove(file_name)
            if os.path.isfile(file_name) == True:
                os.remove(file_name)
        except Exception:
            pass

async def get_msg(userbot, client, bot, sender, edit_id, msg_link, i):
    
    """ userbot: PyrogramUserBot
    client: PyrogramBotClient
    bot: TelethonBotClient """
    
    edit = ""
    chat = ""
    round_message = False
    params = {}
    if "?" in msg_link:
        msg_link_split = msg_link.split("?")
        msg_link = msg_link_split[0]
        params_split = msg_link_split[1].split("&")
        for params_str in params_split:
            if "=" in params_str:
                params_key_value = params_str.split("=")
                params[params_key_value[0]] = params_key_value[1]
    msg_id = int(msg_link.split("/")[-1]) + int(i)
    height, width, duration, thumb_path = 90, 90, 0, None
    if 't.me/c/' in msg_link or 't.me/b/' in msg_link:
        if 't.me/b/' in msg_link:
            chat = str(msg_link.split("/")[-2])
        else:
            chat = int('-100' + str(msg_link.split("/")[-2]))
        file = ""
        try:
            # single or group
            single_msg = await userbot.get_messages(chat, msg_id)
            msg_group = [single_msg]
            if single_msg.media_group_id :
                msg_group = await userbot.get_media_group(chat, msg_id)
            
            # download all
            file_names = []
            input_file = []
            edit = await client.edit_message_text(sender, edit_id, "Trying to Download.")
            for msg in msg_group:
                if msg.media:
                    if msg.media==MessageMediaType.WEB_PAGE:
                        edit = await client.edit_message_text(sender, edit_id, "Cloning.")
                        await client.send_message(sender, msg.text.markdown)
                        await edit.delete()
                        return
                if not msg.media:
                    if msg.text:
                        edit = await client.edit_message_text(sender, edit_id, "Cloning.")
                        await client.send_message(sender, msg.text.markdown)
                        await edit.delete()
                        return
                file = await userbot.download_media(
                    msg,
                    progress=progress_for_pyrogram,
                    progress_args=(
                        client,
                        "**DOWNLOADING:**\n",
                        edit,
                        time.time()
                    )
                )
                print(file)
                file_names.append(file)
                if msg.media==MessageMediaType.VIDEO :
                    input_file.append(InputMediaVideo(file))
                elif msg.media==MessageMediaType.PHOTO :
                    input_file.append(InputMediaPhoto(file))
                elif msg.media==MessageMediaType.DOCUMENT :
                    input_file.append(InputMediaDocument(file))
                elif msg.media==MessageMediaType.AUDIO :
                    input_file.append(InputMediaAudio(file))
                elif msg.media==MessageMediaType.ANIMATION :
                    input_file.append(InputMediaAnimation(file))
                elif msg.media==MessageMediaType.CONTACT :
                    input_file.append(InputMessageContent(file))
                

            await edit.edit('Preparing to Upload!')
            if len(file_names) >= 2 and len(input_file) >= 2 :
                await client.send_media_group(sender, input_file)
                remove_file(file_names)
                return await edit.delete()
            
            file = file_names[0]
            msg = msg_group[0]
            caption = None
            if msg.caption is not None:
                caption = msg.caption
            if msg.media==MessageMediaType.VIDEO_NOTE:
                round_message = True
                print("Trying to get metadata")
                data = video_metadata(file)
                height, width, duration = data["height"], data["width"], data["duration"]
                print(f'd: {duration}, w: {width}, h:{height}')
                try:
                    thumb_path = await screenshot(file, duration, sender)
                except Exception:
                    thumb_path = None
                await client.send_video_note(
                    chat_id=sender,
                    video_note=file,
                    length=height, duration=duration, 
                    thumb=thumb_path,
                    progress=progress_for_pyrogram,
                    progress_args=(
                        client,
                        '**UPLOADING:**\n',
                        edit,
                        time.time()
                    )
                )
            elif msg.media==MessageMediaType.VIDEO and msg.video.mime_type in ["video/mp4", "video/x-matroska"]:
                print("Trying to get metadata")
                data = video_metadata(file)
                height, width, duration = data["height"], data["width"], data["duration"]
                print(f'd: {duration}, w: {width}, h:{height}')
                try:
                    thumb_path = await screenshot(file, duration, sender)
                except Exception:
                    thumb_path = None
                await client.send_video(
                    chat_id=sender,
                    video=file,
                    caption=caption,
                    supports_streaming=True,
                    height=height, width=width, duration=duration, 
                    thumb=thumb_path,
                    progress=progress_for_pyrogram,
                    progress_args=(
                        client,
                        '**UPLOADING:**\n',
                        edit,
                        time.time()
                    )
                )
            
            elif msg.media==MessageMediaType.PHOTO:
                await edit.edit("Uploading photo.")
                await bot.send_file(sender, file, caption=caption)
            else:
                thumb_path=thumbnail(sender)
                await client.send_document(
                    sender,
                    file, 
                    caption=caption,
                    thumb=thumb_path,
                    progress=progress_for_pyrogram,
                    progress_args=(
                        client,
                        '**UPLOADING:**\n',
                        edit,
                        time.time()
                    )
                )
            remove_file(file_names)
            await edit.delete()
        except (ChannelBanned, ChannelInvalid, ChannelPrivate, ChatIdInvalid, ChatInvalid):
            await client.edit_message_text(sender, edit_id, "Have you joined the channel?")
            return
        except PeerIdInvalid:
            chat = msg_link.split("/")[-3]
            try:
                int(chat)
                new_link = f"t.me/c/{chat}/{msg_id}"
            except:
                new_link = f"t.me/b/{chat}/{msg_id}"
            return await get_msg(userbot, client, bot, sender, edit_id, msg_link, i)
        except Exception as e:
            print(e)
            if "messages.SendMedia" in str(e) \
            or "SaveBigFilePartRequest" in str(e) \
            or "SendMediaRequest" in str(e) \
            or str(e) == "File size equals to 0 B":
                try: 
                    if msg.media==MessageMediaType.VIDEO and msg.video.mime_type in ["video/mp4", "video/x-matroska"]:
                        UT = time.time()
                        uploader = await fast_upload(f'{file}', f'{file}', UT, bot, edit, '**UPLOADING:**')
                        attributes = [DocumentAttributeVideo(duration=duration, w=width, h=height, round_message=round_message, supports_streaming=True)] 
                        await bot.send_file(sender, uploader, caption=caption, thumb=thumb_path, attributes=attributes, force_document=False)
                    elif msg.media==MessageMediaType.VIDEO_NOTE:
                        uploader = await fast_upload(f'{file}', f'{file}', UT, bot, edit, '**UPLOADING:**')
                        attributes = [DocumentAttributeVideo(duration=duration, w=width, h=height, round_message=round_message, supports_streaming=True)] 
                        await bot.send_file(sender, uploader, caption=caption, thumb=thumb_path, attributes=attributes, force_document=False)
                    else:
                        UT = time.time()
                        uploader = await fast_upload(f'{file}', f'{file}', UT, bot, edit, '**UPLOADING:**')
                        await bot.send_file(sender, uploader, caption=caption, thumb=thumb_path, force_document=True)
                    if os.path.isfile(file) == True:
                        os.remove(file)
                except Exception as e:
                    print(e)
                    await client.edit_message_text(sender, edit_id, f'Failed to save: `{msg_link}`\n\nError: {str(e)}')
                    try:
                        os.remove(file)
                    except Exception:
                        return
                    return 
            else:
                await client.edit_message_text(sender, edit_id, f'Failed to save: `{msg_link}`\n\nError: {str(e)}')
                try:
                    os.remove(file)
                except Exception:
                    return
                return
        try:
            os.remove(file)
            if os.path.isfile(file) == True:
                os.remove(file)
        except Exception:
            pass
        await edit.delete()
    elif 'comment' in params :
        chat =  msg_link.split("t.me")[1].split("/")[1]
        discussion_chat = await userbot.get_discussion_message(chat, msg_id)
        comment = await userbot.get_messages(discussion_chat.chat.id, int(params['comment']))
        if comment.link :
            return await get_msg(userbot, client, bot, sender, edit_id, comment.link, i)
    else:
        edit = await client.edit_message_text(sender, edit_id, "Cloning.")
        chat =  msg_link.split("t.me")[1].split("/")[1]
        try:
            msg = await client.get_messages(chat, msg_id)
            if msg.empty:
                new_link = f't.me/b/{chat}/{int(msg_id)}'
                #recurrsion 
                return await get_msg(userbot, client, bot, sender, edit_id, new_link, i)
            if msg.media_group_id :
                await edit.delete()
                return await client.copy_media_group(sender, chat, msg_id)
            await client.copy_message(sender, chat, msg_id)
        except Exception as e:
            print(e)
            return await client.edit_message_text(sender, edit_id, f'Failed to save: `{msg_link}`\n\nError: {str(e)}')
        await edit.delete()
        
async def get_bulk_msg(userbot, client, sender, msg_link, i):
    x = await client.send_message(sender, "Processing!")
    await get_msg(userbot, client, Drone, sender, x.id, msg_link, i)

print(f"main has Imported  {os.path.basename(__file__)}")