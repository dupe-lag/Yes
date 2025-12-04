import logging
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
import requests
from bs4 import BeautifulSoup
import phonenumbers
from phonenumbers import carrier, geocoder, timezone
import socket
import urllib.parse
import os # 1. Import os for token security

# 2. Get token from environment variable for security
TOKEN = os.getenv("TELEGRAM_TOKEN", "8289958887:AAFrdtHwtDSZyfI77ECJONkAMXkEF0QbQIQ") 


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


user_data = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🔍 Поиск по никнейму", callback_data='osint_username')],
        [InlineKeyboardButton("🌐 Парсинг сайта", callback_data='parse_website')],
        [InlineKeyboardButton("📡 IP информация", callback_data='ip_info')],
        [InlineKeyboardButton("📚 Wikipedia поиск", callback_data='wiki_search')],
        [InlineKeyboardButton("🔎 Поиск телефона", callback_data='phone_lookup')],
        [InlineKeyboardButton("👤 Парсинг ВК", callback_data='vk_parse')],
        [InlineKeyboardButton("🆔 ID по username ВК", callback_data='vk_id')],
        [InlineKeyboardButton("📱 ID Telegram", callback_data='tg_id')],
        [InlineKeyboardButton("🌐 Полезные сайты", callback_data='useful_sites')],
        [InlineKeyboardButton("🤖 Полезные боты", callback_data='useful_bots')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = (
        "🕵️ *OSINT Парсинг Бот*\n\n"
        "Выберите опцию из меню:\n\n"
        "• *Поиск по никнейму* - поиск аккаунтов по username\n"
        "• *Парсинг сайта* - извлечение данных с веб-страниц\n"
        "• *IP информация* - геолокация и информация об IP\n"
        "• *Wikipedia поиск* - поиск информации в Wikipedia\n"
        "• *Поиск телефона* - информация о номере телефона\n"
        "• *Парсинг ВК* - информация о странице ВКонтакте\n"
        "• *ID по username ВК* - получение ID по username ВК\n"
        "• *ID Telegram* - получение ID по username Telegram\n"
        "• *Полезные сайты* - список полезных OSINT-сайтов\n"
        "• *Полезные боты* - список полезных OSINT-ботов"
    )
    
    await update.message.reply_text(welcome_text, parse_mode='Markdown', reply_markup=reply_markup)

async def handle_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    if query.data == 'osint_username':
        user_data[user_id] = {'action': 'osint_username'}
        await query.edit_message_text("Введите username для поиска:")
    
    elif query.data == 'parse_website':
        user_data[user_id] = {'action': 'parse_website'}
        await query.edit_message_text("Введите URL сайта для парсинга:")
    
    elif query.data == 'ip_info':
        user_data[user_id] = {'action': 'ip_info'}
        await query.edit_message_text("Введите IP адрес для проверки:")
    
    elif query.data == 'wiki_search':
        user_data[user_id] = {'action': 'wiki_search'}
        await query.edit_message_text("Введите запрос для поиска в Wikipedia:")
    
    elif query.data == 'phone_lookup':
        user_data[user_id] = {'action': 'phone_lookup'}
        await query.edit_message_text("Введите номер телефона (с кодом страны):")
    
    elif query.data == 'vk_parse':
        user_data[user_id] = {'action': 'vk_parse'}
        await query.edit_message_text("Введите username или ID страницы ВКонтакте:")
    
    elif query.data == 'vk_id':
        user_data[user_id] = {'action': 'vk_id'}
        await query.edit_message_text("Введите username ВКонтакте для получения ID:")
    
    elif query.data == 'tg_id':
        user_data[user_id] = {'action': 'tg_id'}
        await query.edit_message_text("Введите username Telegram (без @):")
    
    elif query.data == 'useful_sites':
        await useful_sites(update, context)
    
    elif query.data == 'useful_bots':
        await useful_bots(update, context)
    
    elif query.data == 'back_to_menu':
        await show_main_menu(update, context)

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🔍 Поиск по никнейму", callback_data='osint_username')],
        [InlineKeyboardButton("🌐 Парсинг сайта", callback_data='parse_website')],
        [InlineKeyboardButton("📡 IP информация", callback_data='ip_info')],
        [InlineKeyboardButton("📚 Wikipedia поиск", callback_data='wiki_search')],
        [InlineKeyboardButton("🔎 Поиск телефона", callback_data='phone_lookup')],
        [InlineKeyboardButton("👤 Парсинг ВК", callback_data='vk_parse')],
        [InlineKeyboardButton("🆔 ID по username ВК", callback_data='vk_id')],
        [InlineKeyboardButton("📱 ID Telegram", callback_data='tg_id')],
        [InlineKeyboardButton("🌐 Полезные сайты", callback_data='useful_sites')],
        [InlineKeyboardButton("🤖 Полезные боты", callback_data='useful_bots')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.callback_query:
        await update.callback_query.edit_message_text("🕵️ Выберите действие:", reply_markup=reply_markup)
    else:
        await update.message.reply_text("🕵️ Выберите действие:", reply_markup=reply_markup)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text.strip()
    
    if user_id not in user_data:
        await update.message.reply_text("Пожалуйста, выберите действие из меню.")
        return
    
    action = user_data[user_id]['action']
    
    if action == 'osint_username':
        await username_search(update, text)
    elif action == 'parse_website':
        await website_parse(update, text)
    elif action == 'ip_info':
        await ip_info(update, text)
    elif action == 'wiki_search':
        await wiki_search(update, text)
    elif action == 'phone_lookup':
        await phone_lookup(update, text)
    elif action == 'vk_parse':
        await vk_parse(update, text)
    elif action == 'vk_id':
        await vk_get_id(update, text)
    elif action == 'tg_id':
        await tg_get_id(update, text)
    
    # 3. CRITICAL FIX: Clear user state to prevent bot from getting stuck
    if user_id in user_data: 
        del user_data[user_id]
    
    
    keyboard = [[InlineKeyboardButton("⬅️ Назад в меню", callback_data='back_to_menu')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Выберите дальнейшее действие:", reply_markup=reply_markup)

async def username_search(update: Update, username):
    try:
        
        platforms = {
            "GitHub": f"https://github.com/{username}",
            "Twitter": f"https://twitter.com/{username}",
            "Instagram": f"https://instagram.com/{username}",
            "Reddit": f"https://reddit.com/user/{username}",
            "Steam": f"https://steamcommunity.com/id/{username}",
            "Vk": f"https://vk.com/{username}",
            "Facebook": f"https://facebook.com/{username}",
            "LinkedIn": f"https://linkedin.com/in/{username}",
            "Pinterest": f"https://pinterest.com/{username}",
            "SoundCloud": f"https://soundcloud.com/{username}",
            "Telegram": f"https://t.me/{username}",
            "YouTube": f"https://youtube.com/@{username}",
            "Twitch": f"https://twitch.tv/{username}",
            "TikTok": f"https://tiktok.com/@{username}",
            # 4. Corrected Spotify URL (using google search query instead of broken URL)
            "Spotify": f"https://www.google.com/search?q=spotify+user+{username}", 
            "Medium": f"https://medium.com/@{username}"
        }
        
        results = []
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        for platform, url in platforms.items():
            try:
                response = requests.get(url, headers=headers, timeout=10)
                if response.status_code == 200:
                    
                    if platform == "Instagram":
                        if "Sorry, this page isn't available." not in response.text:
                            results.append(f"✅ {platform}: {url}")
                        else:
                            results.append(f"❌ {platform}: не найден")
                    elif platform == "Twitter":
                        if "Эта учетная запись заблокирована" not in response.text and "Страница не найдена" not in response.text:
                            results.append(f"✅ {platform}: {url}")
                        else:
                            results.append(f"❌ {platform}: не найден")
                    else:
                        results.append(f"✅ {platform}: {url}")
                elif platform == "Spotify": # 5. Special check for Spotify/Google
                    if "did not match any documents" not in response.text:
                         results.append(f"✅ {platform}: {url}")
                    else:
                         results.append(f"❌ {platform}: не найден")
                else:
                    results.append(f"❌ {platform}: не найден")
            except requests.exceptions.RequestException: # 6. Specific error handling
                results.append(f"❌ {platform}: ошибка проверки")
        
        
        result_text = f"🔍 *Результаты поиска для {username}:*\n\n" + "\n".join(results)
        
        await update.message.reply_text(result_text, parse_mode='Markdown')
    
    except Exception as e:
        logger.error(f"Error in username_search: {e}") # 7. Log error
        await update.message.reply_text(f"❌ Ошибка при поиске: {str(e)}")

async def website_parse(update: Update, url):
    try:
        
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status() # 8. Ensure request was successful
        soup = BeautifulSoup(response.text, 'html.parser')
        
        
        title = soup.title.string if soup.title and soup.title.string else "Не найдено" # 9. Handle None string
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        description = meta_desc['content'] if meta_desc and 'content' in meta_desc.attrs else "Нет описания"
        
        
        links = soup.find_all('a', href=True)
        external_links = [a['href'] for a in links if a['href'].startswith('http')]
        
        
        result_text = (
            f"🌐 *Результаты парсинга:* {url}\n\n"
            f"📝 *Заголовок:* {title}\n\n"
            f"📄 *Описание:* {description}\n\n"
            f"🔗 *Найдено ссылок:* {len(links)}\n"
            f"🌍 *Внешних ссылок:* {len(external_links)}"
        )
        
        await update.message.reply_text(result_text, parse_mode='Markdown')
    
    except requests.exceptions.RequestException as e: # 10. Handle Request errors
        await update.message.reply_text(f"❌ Ошибка при доступе к сайту: {e}")
    except Exception as e:
        logger.error(f"Error in website_parse: {e}") # 11. Log error
        await update.message.reply_text(f"❌ Ошибка при парсинге: {str(e)}")

async def ip_info(update: Update, ip):
    try:
        
        try:
            socket.inet_aton(ip)
        except socket.error:
            await update.message.reply_text("❌ Неверный формат IP адреса")
            return
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        
        try:
            
            whois_url = f"https://www.whois.com/whois/{ip}"
            response = requests.get(whois_url, headers=headers, timeout=10)
            response.raise_for_status() # 12. Check request status
            soup = BeautifulSoup(response.text, 'html.parser')
            
            
            whois_data = soup.find('pre', {'class': 'df-raw'})
            if whois_data:
                whois_text = whois_data.text[:500] + "..." if len(whois_data.text) > 500 else whois_data.text
                result_text = f"📡 *Информация об IP:* {ip}\n\n```\n{whois_text}\n```"
            else:
                result_text = f"📡 *Информация об IP:* {ip}\n\nНе удалось получить информацию через WHOIS"
                
            await update.message.reply_text(result_text, parse_mode='Markdown')
        except requests.exceptions.RequestException: # 13. Specific error handling
            await update.message.reply_text("❌ Не удалось получить информацию об IP")
    
    except Exception as e:
        logger.error(f"Error in ip_info: {e}") # 14. Log error
        await update.message.reply_text(f"❌ Ошибка: {str(e)}")

async def wiki_search(update: Update, query):
    try:
        
        search_url = f"https://ru.wikipedia.org/wiki/{urllib.parse.quote(query)}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(search_url, headers=headers, timeout=10)
        response.raise_for_status() # 15. Check request status
        soup = BeautifulSoup(response.text, 'html.parser')
        
        
        if soup.find('div', {'id': 'noarticletext'}):
            await update.message.reply_text("❌ Статья не найдена в Wikipedia")
            return
        
        
        title = soup.find('h1', {'id': 'firstHeading'})
        if title:
            page_title = title.text
        else:
            page_title = query
        
        
        content = soup.find('div', {'id': 'mw-content-text'})
        if content:
            first_paragraph = content.find('p', recursive=False) # 16. Find first direct paragraph
            if first_paragraph:
                summary = first_paragraph.text[:1000] + "..." if len(first_paragraph.text) > 1000 else first_paragraph.text
            else:
                summary = "Не удалось извлечь содержание статьи"
        else:
            summary = "Не удалось извлечь содержание статьи"
        
        result_text = (
            f"📚 *Wikipedia: {page_title}*\n\n"
            f"{summary}\n\n"
            f"🔗 *Ссылка:* {search_url}"
        )
        
        await update.message.reply_text(result_text, parse_mode='Markdown')
    
    except Exception as e:
        logger.error(f"Error in wiki_search: {e}") # 17. Log error
        await update.message.reply_text(f"❌ Ошибка при поиске в Wikipedia: {str(e)}")

async def phone_lookup(update: Update, phone_number):
    try:
        
        parsed_number = phonenumbers.parse(phone_number, None)
        
        if not phonenumbers.is_valid_number(parsed_number):
            await update.message.reply_text("❌ Неверный формат номера телефона")
            return
        
        
        carrier_name = carrier.name_for_number(parsed_number, "ru")
        region = geocoder.description_for_number(parsed_number, "ru")
        time_zones = timezone.time_zones_for_number(parsed_number)
        
        result_text = (
            f"📞 *Информация о номере:* {phone_number}\n\n"
            f"📱 *Оператор:* {carrier_name if carrier_name else 'Неизвестно'}\n"
            f"🌍 *Регион:* {region if region else 'Неизвестно'}\n"
            f"🕐 *Часовой пояс:* {', '.join(time_zones) if time_zones else 'Неизвестно'}\n"
            f"✅ *Валидность:* {'Да' if phonenumbers.is_valid_number(parsed_number) else 'Нет'}\n"
            f"🌐 *Возможный номер:* {'Да' if phonenumbers.is_possible_number(parsed_number) else 'Нет'}"
        )
        
        await update.message.reply_text(result_text, parse_mode='Markdown')
    
    except Exception as e:
        logger.error(f"Error in phone_lookup: {e}") # 18. Log error
        await update.message.reply_text(f"❌ Ошибка при проверке номера: {str(e)}")

async def vk_parse(update: Update, username):
    try:
        
        user_id = await get_vk_id(username)
        
        if not user_id:
            await update.message.reply_text("❌ Пользователь ВКонтакте не найден")
            return
        
        
        url = f"https://vk.com/{username}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status() # 19. Check request status
        soup = BeautifulSoup(response.text, 'html.parser')
        
        
        title = soup.find('title')
        if title:
            profile_name = title.text.split('|')[0].strip()
        else:
            profile_name = "Неизвестно"
        
        
        followers_text = "Неизвестно"
        followers_match = re.search(r'(\d+)\s*подписчик', response.text)
        if followers_match:
            followers_text = followers_match.group(1)
        
        
        friends_text = "Неизвестно"
        friends_match = re.search(r'(\d+)\s*друг', response.text)
        if friends_match:
            friends_text = friends_match.group(1)
        
        
        photos_text = "Неизвестно"
        photos_match = re.search(r'(\d+)\s*фотографи', response.text)
        if photos_match:
            photos_text = photos_match.group(1)
        
        result_text = (
            f"👤 *Информация о странице ВКонтакте:*\n\n"
            f"📛 *Имя:* {profile_name}\n"
            f"🆔 *ID:* {user_id}\n"
            f"👥 *Подписчики:* {followers_text}\n"
            f"🤝 *Друзья:* {friends_text}\n"
            f"📸 *Фотографии:* {photos_text}\n"
            f"🔗 *Ссылка:* {url}"
        )
        
        await update.message.reply_text(result_text, parse_mode='Markdown')
    
    except requests.exceptions.RequestException as e:
        await update.message.reply_text(f"❌ Ошибка доступа к ВК: {e}")
    except Exception as e:
        logger.error(f"Error in vk_parse: {e}") # 20. Log error
        await update.message.reply_text(f"❌ Ошибка при парсинге ВК: {str(e)}")

async def vk_get_id(update: Update, username):
    try:
        user_id = await get_vk_id(username)
        
        if user_id:
            result_text = (
                f"👤 *ВКонтакте ID:*\n\n"
                f"📛 *Username:* {username}\n"
                f"🆔 *ID:* {user_id}\n"
                f"🔗 *Ссылка:* https://vk.com/id{user_id}"
            )
            
            await update.message.reply_text(result_text, parse_mode='Markdown')
        else:
            await update.message.reply_text("❌ Пользователь ВКонтакте не найден")
    
    except Exception as e:
        logger.error(f"Error in vk_get_id: {e}") # 21. Log error
        await update.message.reply_text(f"❌ Ошибка при получении ID: {str(e)}")

async def tg_get_id(update: Update, username):
    try:
        
        url = f"https://t.me/{username}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            
            profile_name = "Неизвестно"
            title = soup.find('title')
            if title:
                # 22. Better text cleaning for Telegram title
                profile_name = title.text.replace('Telegram: Contact ', '').replace('Telegram: Join ', '').strip()
            
            
            description = "Не найдено"
            desc_elem = soup.find('div', {'class': 'tgme_page_description'})
            if desc_elem:
                description = desc_elem.text.strip()
            
            
            members_text = "Неизвестно"
            members_elem = soup.find('div', {'class': 'tgme_page_extra'})
            if members_elem:
                members_text = members_elem.text.strip()
            
            result_text = (
                f"👤 *Информация о профиле Telegram:*\n\n"
                f"📛 *Имя:* {profile_name}\n"
                f"🔗 *Username:* @{username}\n"
                f"📝 *Описание:* {description}\n"
                f"👥 *Подписчики/Участники:* {members_text}\n"
                f"🌐 *Ссылка:* {url}"
            )
            
            await update.message.reply_text(result_text, parse_mode='Markdown')
        else:
            await update.message.reply_text("❌ Пользователь Telegram не найден")
    
    except Exception as e:
        logger.error(f"Error in tg_get_id: {e}") # 23. Log error
        await update.message.reply_text(f"❌ Ошибка при получении информации: {str(e)}")

async def get_vk_id(username):
    try:
        
        url = f"https://vk.com/{username}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status() # 24. Check request status
        
        
        id_match = re.search(r'"uid":(\d+)', response.text) # 25. Removed redundant quotes in regex
        if id_match:
            return id_match.group(1)
        
        
        id_match = re.search(r'\"id\":(\d+)', response.text)
        if id_match:
            return id_match.group(1)
        
       
        id_match = re.search(r'https://vk.com/id(\d+)', response.text)
        if id_match:
            return id_match.group(1)
        
        return None
    
    except requests.exceptions.RequestException as e: # 26. Specific error handling
        logger.error(f"Error in get_vk_id request: {e}")
        return None
    except Exception as e: # 27. Specific error handling
        logger.error(f"Error in get_vk_id parsing: {e}")
        return None

async def useful_sites(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        sites_text = (
            "🌐 *Полезные OSINT-сайты:*\n\n"
            "• *Whois Lookup* - https://whois.domaintools.com\n"
            "• *IP Lookup* - https://ipinfo.io\n"
            "• *Email Checker* - https://verify-email.org\n"
            "• *Social Media Search* - https://social-searcher.com\n"
            "• *Username Search* - https://whatsmyname.app\n"
            "• *Image Reverse Search* - https://images.google.com\n"
            "• *Archive.org* - https://archive.org\n"
            "• *Phone Lookup* - https://truecaller.com\n"
            "• *Domain Search* - https://builtwith.com\n"
            "• *Data Breach Check* - https://haveibeenpwned.com\n"
            "• *Metadata Analysis* - https://exifdata.com\n"
            "• *Password Leaks* - https://dehashed.com\n"
            "• *VPN/Proxy Detection* - https://ipqualityscore.com\n"
            "• *Website History* - https://archive.ph\n"
            "• *DNS Lookup* - https://dnsdumpster.com"
        )
        
        keyboard = [[InlineKeyboardButton("⬅️ Назад в меню", callback_data='back_to_menu')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.edit_message_text(sites_text, parse_mode='Markdown', reply_markup=reply_markup)
        else:
            await update.message.reply_text(sites_text, parse_mode='Markdown', reply_markup=reply_markup)
    
    except Exception as e:
        logger.error(f"Error in useful_sites: {e}") # 28. Log error
        await update.message.reply_text(f"❌ Ошибка: {str(e)}")

async def useful_bots(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        bots_text = (
            "🤖 *Полезные OSINT-боты:*\n\n"
            "• @SangMataInfo_bot - история изменений профиля\n"
            "• @tgscanbot - анализ Telegram-аккаунтов\n"
            "• @myipbot - информация об IP-адресе\n"
            "• @WhoisBot - WHOIS информация о доменах\n"
            "• @SpamBot - проверка на спам-аккаунты\n"
            "• @ImageSearchBot - обратный поиск изображений\n"
            "• @VK_Bot - поиск по ВКонтакте\n"
            "• @GitHubBot - поиск по GitHub\n"
            "• @YouTubeBot - поиск по YouTube\n"
            "• @TwitterBot - поиск по Twitter\n"
            "• @InstagramBot - поиск по Instagram\n"
            "• @RedditBot - поиск по Reddit\n"
            "• @PhoneInfoBot - информация о номерах\n"
            "• @EmailVerifierBot - проверка email\n"
            "• @DomainToolsBot - инструменты для доменов\n"
            "• @VKHistoryRobot история профиля вк\n"
            "• @osint_maigret_bot поиск по нику"
        )
        
        keyboard = [[InlineKeyboardButton("⬅️ Назад в меню", callback_data='back_to_menu')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.edit_message_text(bots_text, parse_mode='Markdown', reply_markup=reply_markup)
        else:
            await update.message.reply_text(bots_text, parse_mode='Markdown', reply_markup=reply_markup)
    
    except Exception as e:
        logger.error(f"Error in useful_bots: {e}") # 29. Log error
        error_text = f"❌ Ошибка: {str(e)}"
        if update.callback_query:
            await update.callback_query.edit_message_text(error_text)
        else:
            await update.message.reply_text(error_text)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(msg="Exception while handling an update:", exc_info=context.error)
    
    try:
        if update.message: # 30. Check if message exists before replying
            await update.message.reply_text("❌ Произошла ошибка при обработке запроса")
        elif update.callback_query and update.callback_query.message:
            await update.callback_query.message.reply_text("❌ Произошла ошибка при обработке запроса")
        else:
            pass
    except:
        pass # 31. Prevent error in error handler
        

def main():
    # 32. Add check for token
    if not TOKEN or TOKEN == "8289958887:AAFrdtHwtDSZyfI77ECJONkAMXkEF0QbQIQ":
         print("WARNING: Using default/unsafe token. Set the TELEGRAM_TOKEN environment variable.")
    application = Application.builder().token(TOKEN).build()
    
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(handle_query))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_error_handler(error_handler)
    
    
    print("Бот запущен!")
    application.run_polling()

if __name__ == "__main__":
    main()
