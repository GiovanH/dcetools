import os,json,datetime,mimetypes
import sys
from typing import Any, Generator, Iterable, TypeVar

from dcetools.formatter.base import DiscordWriter
from dcetools.types import DCEExport, Guild, Message, User
from discord_markdown_ast_parser import parse_to_dict,parse
from discord_markdown_ast_parser.parser import Node,NodeType

from jinja2 import Environment, FileSystemLoader
import html
import re
import uuid,requests

THE_WRITER: 'HtmlWriter' = None # type: ignore

env = Environment(loader = FileSystemLoader('dcetools/static'))

reply_like = ['reply','20']

anim_emoji_patt = re.compile(r'<a:(\w+):(\d{17,20})>')
url_pattern = re.compile(r'^https?://(?:discord|discordapp)\.com/channels/.*?/(\d+)/?$')
def replace_anim_emoji_with_uuid(msg):
    matches = anim_emoji_patt.findall(msg)
    new_str = msg
    location_of_anim_emoji = {}
    if len(matches)!=0:
        for match in matches:
            x = str(uuid.uuid4())
            tmp = location_of_anim_emoji.get(f'<a:{match[0]}:{match[1]}>')
            if tmp:
                location_of_anim_emoji[f'<a:{match[0]}:{match[1]}>'].append(x)
            else:
                location_of_anim_emoji[f'<a:{match[0]}:{match[1]}>'] = [x]
                # location_of_anim_emoji[f'<a:{match[0]}:{match[1]}>'].append(x)

            new_str = new_str.replace(f'<a:{match[0]}:{match[1]}>',x,1)
    return new_str,location_of_anim_emoji

markdown_clicky_link_patt = re.compile(r'\[(.*)\]\((.*)\)')

def replace_clicky_with_uuid(msg):
    matches = markdown_clicky_link_patt.findall(msg)
    new_str = msg
    location_of_clicky_link = {}
    if len(matches)!=0:
        for match in matches:
            x = str(uuid.uuid4())
            tmp = location_of_clicky_link.get(f'[{match[0]}]({match[1]})')
            if tmp:
                location_of_clicky_link[f'[{match[0]}]({match[1]})'].append(x)
            else:
                location_of_clicky_link[f'[{match[0]}]({match[1]})'] = [x]

            new_str = new_str.replace(f'[{match[0]}]({match[1]})',x,1)
    return new_str,location_of_clicky_link


def resolve_node(node:Node,len_ast):
    if node.node_type == NodeType.TEXT:
        assert node.text_content
        temp = html.escape(node.text_content)
        return temp if temp !=None else ''
    elif node.node_type == NodeType.BOLD:
        temp = "".join([resolve_node(child,len_ast) for child in node.children]) # type: ignore
        return f'<strong>{temp}</strong>'
    elif node.node_type == NodeType.UNDERLINE:
        temp = "".join([resolve_node(child,len_ast) for child in node.children]) # type: ignore
        return f'<u>{temp}</u>'
    elif node.node_type == NodeType.ITALIC:
        assert node.children
        temp = "".join([resolve_node(child,len_ast) for child in node.children])
        return f'<em>{temp}</em>'
    elif node.node_type == NodeType.STRIKETHROUGH:
        assert node.children
        temp = "".join([resolve_node(child,len_ast) for child in node.children])
        return f'<s>{temp}</s>'
    elif node.node_type == NodeType.SPOILER:
        assert node.children
        temp = "".join([resolve_node(child,len_ast) for child in node.children])
        return f'<span class="chatlog__markdown-spoiler chatlog__markdown-spoiler--hidden" onclick="showSpoiler(event, this)">{temp}</span>'
    elif node.node_type == NodeType.QUOTE_BLOCK:
        assert node.children
        temp = "".join([resolve_node(child,len_ast) for child in node.children])
        return f'<div class="chatlog__markdown-quote"><div class="chatlog__markdown-quote-border"></div><div class="chatlog__markdown-quote-content">\n{temp}\n</div></div>'
    elif node.node_type == NodeType.CODE_INLINE:
        assert node.children
        temp = "".join([resolve_node(child,len_ast) for child in node.children])
        return f'<code class="chatlog__markdown-pre chatlog__markdown-pre--inline">{temp}</code>'
    elif node.node_type == NodeType.CODE_BLOCK:
        assert node.children
        temp = "".join([resolve_node(child,len_ast) for child in node.children])
        highlight_class = f"language-{node.code_lang}" if node.code_lang else "nohighlight"
        return f'<code class="chatlog__markdown-pre chatlog__markdown-pre--multiline {highlight_class}">{temp}</code>'
    elif node.node_type in [NodeType.URL_WITHOUT_PREVIEW,NodeType.URL_WITH_PREVIEW]:
        url: str = node.url # type: ignore
        matched = url_pattern.match(url)
        if matched:
            msg_id = matched.group(1)
        else:
            msg_id = None
        if msg_id:
            temp = f'<a href="{url}" onclick="scrollToMessage(event, \'{msg_id}\')">{url}'
        else:
            temp = f'<a href="{url}">{url}'

        temp+='</a>'
        return temp
    elif node.node_type  == NodeType.EMOJI_UNICODE_ENCODED:
        return f":{str(node.emoji_name)}:"
    elif node.node_type == NodeType.EMOJI_CUSTOM:
        if len_ast == 1:
            jumbo = True
        else:
            jumbo = False

        return f"""<img loading="lazy" class="chatlog__emoji {'chatlog__emoji--large' if jumbo else ''}" alt="{node.emoji_name}" title=":{node.emoji_name}:" src="https://cdn.discordapp.com/emojis/{node.discord_id}.png">"""
    elif node.node_type == NodeType.USER: #TODO
        discord_id = node.discord_id
        fullname = str(discord_id)
        nickname = str(discord_id)
        return f'<span class="chatlog__markdown-mention" title="{html.escape(fullname)}">@{html.escape(nickname)}</span>'
    elif node.node_type == NodeType.CHANNEL: #TODO
        discord_id = node.discord_id
        symbols = ["🔊" , "#"]
        name = str(discord_id)
        return f'<span class="chatlog__markdown-mention">{symbols[1]}{name}</span>'
    elif node.node_type == NodeType.ROLE: #TODO
        discord_id = node.discord_id
        name = str(discord_id)
        color = [255,0,255]
        style = f'color:rgb({color[0]},{color[1]},{color[2]}); background-color: rgba({color[0]},{color[1]},{color[2]},0.1)'
        return f'<span class="chatlog__markdown-mention" style="{style}">@{html.escape(name)}</span>'

# anim_emoji_patt = re.compile(r'(<a):\w+:(\d{17,20}>)')

# animated_emoji_pattern = re.compile(r'\&lt;a:(\w+):(\d{17,20})\&gt;')
# (<a):\w+:(\d{18}>)
# \&lt;a:(\w+):(\d{18})\&gt;

def anim_emoji_name_to_url(name,jumbo):
    matches = anim_emoji_patt.findall(name)
    if len(matches) == 0:
        return ''
    match = matches[0]
    return f"""<img loading="lazy" class="chatlog__emoji {'chatlog__emoji--large' if jumbo else ''}" alt="{match[0]}" title=":{match[0]}:" src="https://cdn.discordapp.com/emojis/{match[1]}.gif">"""

def fix_animated_emoji(message,anim_location,len_ast):

    if anim_location == {}:
        return message


    if len_ast == 1:
        jumbo = True
    else:
        jumbo = False

    for k,v in anim_location.items():
        for i in v:
            message = message.replace(i,anim_emoji_name_to_url(k,jumbo))

    return message


def clicky_link_to_html(txt):
    matches = markdown_clicky_link_patt.findall(txt)
    if len(matches) == 0:
        return ''
    match = matches[0]
    return f"""<a href="{match[1]}">{match[0]}</a>"""


def fix_clicky_links(message,clicky_location):
    if clicky_location == {}:
        return message

    for k,v in clicky_location.items():
        for i in v:
            message = message.replace(i,clicky_link_to_html(k))

    return message

def fix_everyone_and_here(message):
    return message.replace('@everyone','<span class="chatlog__markdown-mention">@everyone</span>').replace('@here','<span class="chatlog__markdown-mention">@everyone</span>')

def message_markdown(message_content,replace_newlines=False):

    message_semi_content,anim_location = replace_anim_emoji_with_uuid(message_content)
    message_final_content,clicky_location = replace_clicky_with_uuid(message_semi_content)

    message_final_content = message_final_content.replace('___','__').replace('***','**')
    try:
        ast = parse(message_final_content)
    except Exception as e:
        anim_fixed = fix_animated_emoji(message_final_content,anim_location,0)
        clicky_fixed = fix_clicky_links(anim_fixed,clicky_location)
        final = fix_everyone_and_here(clicky_fixed)
        if replace_newlines:
            final = final.replace('\n',' ')
        return final



    text = ''

    for node in ast:

        x = resolve_node(node,len(ast))

        text += x # type: ignore

    anim_fixed = fix_animated_emoji(text,anim_location,len(ast))
    clicky_fixed = fix_clicky_links(anim_fixed,clicky_location)
    final = fix_everyone_and_here(clicky_fixed)
    if replace_newlines:
        final = final.replace('\n',' ')
    return final


    #TODO timestamp fix https://github.com/discordjs/discord-api-types/blob/main/globals.ts#L78-L90



system_message_types = ['recipientadd', 'recipientremove', 'call', 'channelnamechange', 'channeliconchange', 'channelpinnedmessage', 'userjoin', 'threadcreated']
system_message_classes = ["join-icon","leave-icon","call-icon","pencil-icon","pencil-icon","pin-icon","join-icon","thread-icon"]

def timestamp_to_dt_obj(timestamp):
    try:
        date_format = "%Y-%m-%dT%H:%M:%S.%f%z"
        return datetime.datetime.strptime(timestamp, date_format)
    except ValueError:
        date_format = "%Y-%m-%dT%H:%M:%S%z"
        return datetime.datetime.strptime(timestamp, date_format)

def handle_system_notification_content(message):

    if message['type'].lower() == 'recipientadd' and len(message['mentions'])!=0:
        return f"""
                <span>added </span>
                <a class="chatlog__system-notification-link" title="{message['mentions'][0]['name']}">{message['mentions'][0]['nickname']}</a>
                <span> to the group.</span>
"""
    elif message['type'].lower() == 'recipientremove' and len(message['mentions'])!=0:
        if message['mentions'][0]['id'] == message['author']['id']:
            return f"""
                <span>left the group.</span>
"""
        else:
            return f"""
                <span>removed </span>
                <a class="chatlog__system-notification-link" title="{message['mentions'][0]['name']}">{message['mentions'][0]['nickname']}</a>
                <span> from the group.</span>
"""

    elif message['type'].lower() == 'call':
        return f"""
                <span>started a call that lasted {((timestamp_to_dt_obj(message['callEndedTimestamp']) if message['callEndedTimestamp'] is not None else timestamp_to_dt_obj(message['timestamp'])) - timestamp_to_dt_obj(message['timestamp'])).total_seconds() / 60} minutes</span>
"""
    elif message['type'].lower() == 'channelnamechange':
        return f"""
                <span>changed the channel name: </span>
                <span class="chatlog__system-notification-link">{message['content']}</span>
"""
    elif message['type'].lower() == 'channeliconchange':
        return f"""
                <span>changed the channel icon.</span>
"""
    elif message['type'].lower() == 'channelpinnedmessage' and message.get("reference") is not None:
        return f"""
                <span>pinned </span>
                <a class="chatlog__system-notification-link" href="#chatlog__message-container-{message['reference']['messageId']}">a message</a>
                <span> to this channel.</span>
"""
    elif message['type'].lower() == 'userjoin':
        return f"""
                <span>joined the server.</span>
"""
    elif message['type'].lower() == 'threadcreated':
        return f"""
                <span>started a thread.</span>
"""

def get_formatted_date(timestamp):
    dt_obj = timestamp_to_dt_obj(timestamp)
    return datetime.datetime.strftime(dt_obj,'%d-%b-%y %I:%M %p')

def get_short_timestamp(timestamp):
    dt_obj = timestamp_to_dt_obj(timestamp)
    return datetime.datetime.strftime(dt_obj,'%H:%M')



def handle_system_message(message):
    txt = f"""
        <div class="chatlog__message-aside">
            <svg class="chatlog__system-notification-icon">
                <use href="{system_message_classes[system_message_types.index(message['type'].lower())]}"></use>
            </svg>
        </div>
        <div class="chatlog__message-primary">
            <span class="chatlog__system-notification-author" style="{'' if message['author']['color'] is None else 'color:' + message['author']['color']}" title="{message['author']['name']}" data-user-id="{message['author']['id']}">{message['author']['nickname']}</span>

            <span> </span>

            <span class="chatlog__system-notification-content">

                {handle_system_notification_content(message)}

            </span>

            <span class="chatlog__system-notification-timestamp">
                        <a href="#chatlog__message-container-{message['id']}">{get_formatted_date(message['timestamp'])}</a>
            </span>
        </div>
"""
    return txt

def find_message(message_id):
    return THE_WRITER.messages_by_id.get(message_id)

def handle_reply_primary_1(message):
    if message.get('reference') is not None:
        referred_msg_id = message['reference']['messageId']
        referred_message = find_message(referred_msg_id)

        if referred_message:
            try:
                tmp1 = f"color:{referred_message['author']['color']};"
            except KeyError:
                tmp1 = ''
            txt = f"""
                <img class="chatlog__reference-avatar" src="{referred_message['author']['avatarUrl']}" alt="Avatar" loading="lazy" onerror="this.style.visibility='hidden'" width="16" height="16">
                <div class="chatlog__reference-author" style="{tmp1}" title="{referred_message['author']['name']}">{referred_message['author']['nickname']}</div>
                <div class="chatlog__reference-content">
                    <span class="chatlog__reference-link" onclick="scrollToMessage(event, '{message['reference']['messageId']}')">
                        {'Click to see original message/attachment' if not referred_message else message_markdown(referred_message['content'],replace_newlines=True)}
                    </span>
                    {f'<span class="chatlog__reply-edited-timestamp" title="{get_formatted_date(referred_message["timestampEdited"])}">(edited)</span>' if referred_message['timestampEdited'] is not None else ''}
                </div>
"""
        else:
            txt = f"""
                <div class="chatlog__reference-unknown">
                    Original message was deleted or could not be loaded.
                </div>
"""
    elif message.get('interaction') is not None:
        try:
            tmp1 = f"color:{message['interaction']['user']['color']};"
        except KeyError:
            tmp1 = ''
        txt = f"""
                <img class="chatlog__reference-avatar" src="{message['interaction']['user']['avatarUrl']}" alt="Avatar" loading="lazy">
                <div class="chatlog__reference-author" style="{tmp1}" title="{message['interaction']['user']['name']}">{message['interaction']['user']['nickname']}</div>
                <div class="chatlog__reference-content">
                    used /{message['interaction']['name']}
                </div>
"""

    else:
        txt = f"""
                <div class="chatlog__reply-unknown">
                    Original message was deleted or could not be loaded.
                </div>
"""
    return txt

def handle_single_attachment(attachment):
    mimeType = mimetypes.guess_type(attachment['fileName'])[0]


    if attachment['fileName'].startswith('SPOILER'):
        txt1 = f"""
                    <div class="chatlog__attachment-spoiler-caption">SPOILER</div>
"""
    else:
        txt1 = ''

    if mimeType is not None:
        if 'image' in mimeType:
            txt = f"""
                    <a href="{attachment['url']}">
                        <img class="chatlog__attachment-media" src="{attachment['url']}" alt="Image attachment" title="Image: {attachment['fileName']} ({attachment['fileSizeBytes']} Bytes)" loading="lazy">
                    </a>
"""
        elif 'video' in mimeType:
            txt = f"""
                    <video class="chatlog__attachment-media" controls>
                        <source src="{attachment['url']}" alt="Video attachment" title="Video: {attachment['fileName']} ({attachment['fileSizeBytes']} Bytes)">
                    </video>
"""
        elif 'audio' in mimeType:
            txt = f"""
                    <audio class="chatlog__attachment-media" controls>
                        <source src="{attachment['url']}" alt="Audio attachment" title="Audio: {attachment['fileName']} ({attachment['fileSizeBytes']} Bytes)">
                    </audio>
"""
        else:
            txt = f"""
                    <div class="chatlog__attachment-generic">
                        <svg class="chatlog__attachment-generic-icon">
                            <use href="#attachment-icon"/>
                        </svg>
                        <div class="chatlog__attachment-generic-name">
                            <a href="{attachment['url']}">
                                {attachment['fileName']}
                            </a>
                        </div>
                        <div class="chatlog__attachment-generic-size">
                            {attachment['fileSizeBytes']} Bytes
                        </div>
                    </div>
"""
    else:
        txt = f"""
                    <div class="chatlog__attachment-generic">
                        <svg class="chatlog__attachment-generic-icon">
                            <use href="#attachment-icon"/>
                        </svg>
                        <div class="chatlog__attachment-generic-name">
                            <a href="{attachment['url']}">
                                {attachment['fileName']}
                            </a>
                        </div>
                        <div class="chatlog__attachment-generic-size">
                            {attachment['fileSizeBytes']} Bytes
                        </div>
                    </div>
"""
    return txt1+txt


def handler_for_attachments(message):
    return "\n\n".join([f"""
                <div class="chatlog__attachment {'chatlog__attachment--hidden' if attachment['fileName'].startswith('SPOILER') else ''}" {'onclick="showSpoiler(event, this)"' if attachment['fileName'].startswith('SPOILER') else ''}>
                    {handle_single_attachment(attachment)}
                </div>
""" for attachment in message["attachments"]])


def handle_reply_primary(message):
    txt = f"""
            <div class="chatlog__reference">

                {handle_reply_primary_1(message)}

            </div>
"""
    return txt

def handle_first_primary(message):
    txt = f"""
            {handle_reply_primary(message) if message['type'].lower() in reply_like else ''}

            <div class="chatlog__header">

                <span class="chatlog__author" style="{'' if message['author']['color'] is None else 'color:' + message['author']['color']}" title="{message['author']['name']}" data-user-id="{message['author']['id']}">{message['author']['nickname']}</span>
                {'<span class="chatlog__author-tag">BOT</span>' if message['author']['isBot'] else ''}
                <span class="chatlog__timestamp"><a href="#chatlog__message-container-{message['id']}">{get_formatted_date(message['timestamp'])}</a></span>
            </div>
"""
    return txt

def handle_emb_author_link(embed):
    if not embed['author'].get('url') in [None,'']:
        txt = f"""
                                <a class="chatlog__embed-author-link" href="{embed['author']['url']}">
                                    <div class="chatlog__embed-author">{embed['author']['name']}</div>
                                </a>
"""
    else:
        txt = f"""
                                <div class="chatlog__embed-author">{embed['author']['name']}</div>
"""
    return txt


def handle_emb_author(embed):
    messingup_txt_1 = """onerror="this.style.visibility='hidden'" width="16" height="16">"""
    author_icon_url = f"{embed['author'].get('iconUrl') if embed['author'].get('iconUrl') not in ['',None] else ''}"
    txt = f"""
                            <div class="chatlog__embed-author-container">
                                {f'<img class="chatlog__embed-author-icon" src="{author_icon_url}" alt="Author icon" loading="lazy"' + messingup_txt_1 if embed['author']['url'] is not None else ''}
                                {handle_emb_author_link(embed) if embed['author'].get('name') not in [None,''] else ''}
                            </div>
"""
    return txt

def handle_emb_title_link(embed):
    txt = f"""
                                <a class="chatlog__embed-title-link" href="{embed['url']}">
                                    <div class="chatlog__markdown chatlog__markdown-preserve">{embed['title']}</div>
                                </a>
"""
    return txt

def handle_emb_title(embed):
    txt = f"""
                            <div class="chatlog__embed-title">
                                {handle_emb_title_link(embed) if embed.get('url') not in [None,''] else f'<div class="chatlog__markdown chatlog__markdown-preserve">{embed["title"]}</div>'}
                            </div>
"""
    return txt


def handle_emb_description(embed):
    txt = f"""
                            <div class="chatlog__embed-description">
                                <div class="chatlog__markdown chatlog__markdown-preserve">{message_markdown(embed['description'])}</div>
                            </div>
"""
    return txt

def handle_emb_field(field):
    txt = f"""
                                <div class="chatlog__embed-field {"chatlog__embed-field--inline" if field['isInline'] else ''}">
                                    <div class="chatlog__embed-field-name">
                                        <div class="chatlog__markdown chatlog__markdown-preserve">{field['name']}</div>
                                    </div>
                                    <div class="chatlog__embed-field-value">
                                        <div class="chatlog__markdown chatlog__markdown-preserve">{message_markdown(field['value'])}</div>
                                    </div>
                                </div>

"""
    return txt


def handler_for_embed_fields(embed):
    return '\n\n'.join(
        [handle_emb_field(field) for field in embed['fields']]
    )

def handle_embed_thumbnail(embed):
    txt = f"""
                        <div class="chatlog__embed-thumbnail-container">
                            <a class="chatlog__embed-thumbnail-link" href="{embed['thumbnail']['url']}">
                                <img class="chatlog__embed-thumbnail" src="{embed['thumbnail']['url']}" alt="Thumbnail" loading="lazy">
                            </a>
                        </div>
"""
    return txt


def handle_embed_image(image):
    txt = f"""
                        <div class="chatlog__embed-image-container">
                            <a class="chatlog__embed-image-link" href="{image['url']}">
                                <img class="chatlog__embed-image" src="{image['url']}" alt="Image" loading="lazy">
                            </a>
                        </div>
"""
    return txt


def handler_for_images(embed):
    return '\n\n'.join(
        [handle_embed_image(img) for img in embed['images'] if img.get('url') not in [None,''] ]
    )

def handle_emb_timestamp_and_footer(embed):
    if embed.get('footer') in ['',None]:
        return ''
    if embed.get('timestamp') in ['',None]:
        return ''
    if embed['footer'].get('iconUrl') not in [None,'']:
        footer_icon_url = f"{embed['footer'].get('iconUrl')}"
    else:
        footer_icon_url = ''
    txt = f"""
                    <div class="chatlog__embed-footer">
                        {f'<img class="chatlog__embed-footer-icon" src="{footer_icon_url}" alt="Footer icon" loading="lazy">' if embed['footer'].get('iconUrl') not in [None,''] else ''}

                        <span class="chatlog__embed-footer-text">

                            {embed['footer'].get('text') if embed['footer'].get('text') not in [None,''] else ''}
                            {" • " if embed['footer'].get('text') not in [None,''] and embed['timestamp'] not in [None,''] else ''}
                            {datetime.datetime.strftime(timestamp_to_dt_obj(embed['timestamp']),'%d/%m/%Y %I:%M %p') if embed['timestamp'] not in [None,''] else ''}
                        </span>

                    </div>
"""
    return txt


def handle_embeds(embed):
    emb_url = embed['url']

    if not emb_url:
        _type = 'rich'
    elif 'open.spotify.com' in emb_url:
        _type = 'spotify'
    elif 'youtube.com' in emb_url and not ('youtube.com/channel' in emb_url or 'youtube.com/@' in emb_url):
        _type = 'youtube'
    else:
        _type = 'rich'

    if _type == 'spotify':
        txt = f"""
            <div class="chatlog__embed">
                <div class="chatlog__embed-spotify-container">
                    <iframe class="chatlog__embed-spotify" src="{embed['url']}" width="400" height="80" allowtransparency="true" allow="encrypted-media"></iframe>
                </div>
            </div>
"""
    elif _type == 'youtube':
        txt = f"""
            <div class="chatlog__embed">
                <div class="chatlog__embed-color-pill chatlog__embed-color-pill--default"></div>
                <div class="chatlog__embed-content-container">
                    <div class="chatlog__embed-content">
                        <div class="chatlog__embed-text">
                            {handle_emb_author(embed) if embed.get('author') not in [None,''] else ''}
                            {handle_emb_title(embed) if embed.get('title') not in [None,''] else ''}
                            <div class="chatlog__embed-youtube-container">
                                <iframe class="chatlog__embed-youtube" src="{embed['url'].replace('https://www.youtube.com/watch?v=','https://www.youtube.com/embed/')}" width="400" height="225"></iframe>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
"""
    else: # rich embed
        txt = f"""
            <div class="chatlog__embed">
                {f'<div class="chatlog__embed-color-pill" style="background-color: {embed["color"]}"></div>' if embed.get('color') not in [None,''] else '<div class="chatlog__embed-color-pill chatlog__embed-color-pill--default"></div>'}
                <div class="chatlog__embed-content-container">
                    <div class="chatlog__embed-content">
                        <div class="chatlog__embed-text">
                            {handle_emb_author(embed) if embed.get('author') not in [None,''] else ''}
                            {handle_emb_title(embed) if embed.get('title') not in [None,''] else ''}
                            {handle_emb_description(embed)if embed.get('description') not in [None,''] else ''}
                            <div class="chatlog__embed-fields">
                                {handler_for_embed_fields(embed) if len(embed['fields']) !=0 else ''}
                            </div>
                        </div>
                        {handle_embed_thumbnail(embed) if embed.get('thumbnail') not in [None,''] and embed.get('thumbnail').get('url') not in [None,''] else ''}
                    </div>
                    <div class="chatlog__embed-images {"chatlog__embed-images--single" if len(embed['images']) == 1 else ''}">
                        {handler_for_images(embed) if len(embed['images']) !=0 else ''}
                    </div>

                    {handle_emb_timestamp_and_footer(embed) if embed.get('footer') not in [None,''] or embed.get('timestamp') not in [None,''] else ''}

                </div>
            </div>
"""


    return txt

def handler_for_embeds(message):
    if len(message['embeds']) == 0:return ''
    return '\n\n'.join([
        handle_embeds(embed) for embed in message['embeds']
    ])


def handle_sticker(sticker):
    txt = f"""
            <div class="chatlog__sticker" title="{sticker['name']}">
                <img class="chatlog__sticker--media" src="{sticker['sourceUrl']}" alt="Sticker">
            </div>

"""
    return txt


def handler_for_stickers(message):
    return '\n\n'.join([
        handle_sticker(sticker) for sticker in message['stickers']
    ])


def handle_reaction(reaction):
    txt = f"""
                <div class="chatlog__reaction" title="{reaction['emoji']['name']}">
                    <img class="chatlog__emoji chatlog__emoji--small" alt="{reaction['emoji']['name']}" src="{reaction['emoji']['imageUrl']}" loading="lazy">
                    <span class="chatlog__reaction-count">{reaction['count']}</span>
                </div>
"""
    return txt


def handler_for_reactions(message):
    return '\n\n'.join([
        handle_reaction(reaction) for reaction in message['reactions']
    ])


def handle_first_aside(message):
    txt = f"""
            {'<div class="chatlog__reference-symbol"></div>' if message['type'].lower() in reply_like else ''}
            <img class="chatlog__avatar" src="{message['author']['avatarUrl']}" alt="Avatar" loading="lazy">
"""
    return txt


pattern_ggsans = re.compile(r'(ggsans)-(italic|normal)-(400|500|600|700|800)')
pattern_whitney = re.compile(r'(whitney)-(300|400|500|600|700)')

# style_css_temp = style_css

# matches_ggsans = pattern_ggsans.findall(style_css)
# for match in matches_ggsans:
#     style_css_temp = style_css.replace(f'{match[0]}-{match[1]}-{match[2]}',f'https://raw.githubusercontent.com/jsmsj/DCE-JSONtoHTML/master/fonts/{match[0]}-{match[1]}-{match[2]}.woff2')

# matches_whitney = pattern_whitney.findall(style_css)
# for match in matches_whitney:
#     style_css_temp = style_css_temp.replace(f'{match[0]}-{match[1]}',f'https://raw.githubusercontent.com/jsmsj/DCE-JSONtoHTML/master/fonts/{match[0]}-{match[1]}.woff')


# style_css = style_css_temp

class HtmlWriter(DiscordWriter):
    def __init__(self, *args, **kwargs):
        global THE_WRITER
        THE_WRITER = self
        super().__init__(*args, **kwargs)

    # Entrypoint

    def format(self) -> Iterable[str]:
        template = env.get_template('html_prefix.html.j2')
        yield template.render({**locals(), **globals()})

        for frag in self.formatDocuments():
            yield str(frag)

        template = env.get_template('html_postfix.html.j2')
        yield template.render({**locals(), **globals()})

    # Division, channel

    def formatChannelWrapStart(
        self,
        message_list: list[Message],
    ) -> Iterable[str]:
        this_channel = message_list[0]['channel']

        guild_name = self.guild_by_channel[this_channel].get("name")
        guild_iconurl = self.guild_by_channel[this_channel].get("iconUrl")
        channel_category = self.channels[this_channel].get('category')
        channel_name = self.channels[this_channel].get('name')

        yield f"""<div class=preamble>
            <div class=preamble__guild-icon-container><img class=preamble__guild-icon
                    src="{guild_iconurl}"
                    alt="Guild icon" loading=lazy
                    height="200px"
                    width="200px">
                </img></div>
            <div class=preamble__entries-container>
                <div class=preamble__entry>{guild_name}</div>
                <div class=preamble__entry>{channel_category} / {channel_name}</div>
                <div class="preamble__entry preamble__entry--small">{channel_name}</div>
            </div>
        </div>
        <div class="chatlog">"""

    def formatChannelWrapEnd(
        self,
        message_list: list[Message],
    ) -> Iterable[str]:
        yield "</div>"

    # Division, message group

    def formatMessageGroupTime(
        self,
        msg_group_time: list[Message],
        maybe_guild: Guild | None,
        channel: str
    ) -> Iterable[str]:
        message0 = msg_group_time[0]

        yield f'<div id="chatlog__message-container-{message0["id"]}" class="chatlog__message-container {"chatlog__message-container--pinned" if message0["isPinned"] else ""}" data-message-id="{message0["id"]}">'

        for i, message in enumerate(msg_group_time):
            yield f"""
            <div class="chatlog__message">
                <div class="chatlog__message-aside">
                    {handle_first_aside(message) + f'<div class="chatlog__short-timestamp" title="{get_short_timestamp(message["timestamp"])}">{get_short_timestamp(message["timestamp"])}</div>'}
                </div>"""

            if message['type'].lower() in system_message_types:
                yield handle_system_message(message)
            else:
                yield from self.formatMessage(message)
            yield """
            </div>
            """

    # Individual message

    def formatMessage(self, message: Message) -> Iterable[str]:
        yield f"""<div class="chatlog__message-primary">"""

        yield handle_first_primary(message)

        if (not message['content'] == '') or (message['timestampEdited'] is not None):
            yield f"""
            <div class="chatlog__content chatlog__markdown">
                {f'<span class="chatlog__markdown-preserve">{message_markdown(message["content"])}</span>' if not message['content'] == '' else ''}
                {f'<span class="chatlog__edited-timestamp" title="{get_formatted_date(message["timestampEdited"])}">(edited)</span>' if message['timestampEdited'] is not None else ''}
            </div>"""

        yield handler_for_attachments(message)

        yield handler_for_embeds(message)

        yield handler_for_stickers(message)

        yield f"""
               <div class="chatlog__reactions">
                    {handler_for_reactions(message)}
                </div>
            </div>
        """