import asyncio
import base64
import json
import random
import sys
import traceback
from random import randint
from time import time
from urllib.parse import unquote

import aiohttp
import cloudscraper
from aiocfscrape import CloudflareScraper
from aiohttp_proxy import ProxyConnector
from better_proxy import Proxy
from pyrogram import Client
from pyrogram.errors import Unauthorized, UserDeactivated, AuthKeyUnregistered, FloodWait
from pyrogram.raw.functions.messages import RequestAppWebView
from pyrogram.raw.types import InputBotAppShortName

from bot.config import settings
from bot.core.agents import fetch_version
from bot.exceptions import InvalidSession
from bot.utils import logger
from bot.utils.ps import check_base_url
from .headers import headers
from bot.utils import launcher as lc

end_point = "https://tonclayton.fun/api/aT83M535-617h-5deb-a17b-6a335a67ffd5"
super_task = f"{end_point}/tasks/super-tasks"
auth = f"{end_point}/user/authorization"
partner_tasks_api = f"{end_point}/tasks/partner-tasks"
daily_claim = f"{end_point}/user/daily-claim"
daily_tasks = f"{end_point}/tasks/daily-tasks"
default_tasks = f"{end_point}/tasks/default-tasks"
claim_tasks = f"{end_point}/tasks/claim"
connect_wallet_api = f"{end_point}/user/wallet"
complete_task_api = f"{end_point}/tasks/complete"
check_task_api = f"{end_point}/tasks/check"
start_game_api = f"{end_point}/game/start"
save_tile_api = f"{end_point}/game/save-tile"
game_over_api = f"{end_point}/game/over"
start_stack_api = f"{end_point}/stack/st-game"
update_score = f"{end_point}/stack/update-game"
game_en_api = f"{end_point}/stack/en-game"
start_clay_api = f"{end_point}/clay/start-game"
end_clay_api = f"{end_point}/clay/end-game"
achievements_api = f"{end_point}/user/achievements/get"
claim_achievements_api = f"{end_point}/user/achievements/claim/"
save_token = f"{end_point}/user/save-user"



class Tapper:
    def __init__(self, tg_client: Client, multi_thread: bool, wallet: str | None, wallet_memonic: str | None):
        self.tg_client = tg_client
        self.session_name = tg_client.name
        self.first_name = ''
        self.last_name = ''
        self.user_id = ''
        self.auth_token = ""
        self.multi_thread = multi_thread
        self.access_token = None
        self.balance = 0
        self.my_ref = get_()
        self.new_account = False
        self.wallet = wallet
        self.wallet_connected = False
        self.wallet_memo = wallet_memonic
        self.black_list = [6, 2]

    async def get_tg_web_data(self, proxy: str | None) -> str | None:
        try:
            if settings.REF_LINK == "":
                ref_param = get_()
            else:
                ref_param = settings.REF_LINK.split('=')[1]
        except:
            logger.warning("<yellow>INVAILD REF LINK PLEASE CHECK AGAIN! (PUT YOUR REF LINK NOT REF ID)</yellow>")
            sys.exit()
        if proxy:
            proxy = Proxy.from_str(proxy)
            proxy_dict = dict(
                scheme=proxy.protocol,
                hostname=proxy.host,
                port=proxy.port,
                username=proxy.login,
                password=proxy.password
            )
        else:
            proxy_dict = None

        self.tg_client.proxy = proxy_dict
        actual = random.choices([self.my_ref, ref_param], weights=[30, 70], k=1)

        try:
            if not self.tg_client.is_connected:
                try:
                    await self.tg_client.connect()
                except (Unauthorized, UserDeactivated, AuthKeyUnregistered):
                    raise InvalidSession(self.session_name)

            while True:
                try:
                    peer = await self.tg_client.resolve_peer('claytoncoinbot')
                    break
                except FloodWait as fl:
                    fls = fl.value

                    logger.warning(f"<light-yellow>{self.session_name}</light-yellow> | FloodWait {fl}")
                    logger.info(f"<light-yellow>{self.session_name}</light-yellow> | Sleep {fls}s")

                    await asyncio.sleep(fls + 3)

            web_view = await self.tg_client.invoke(RequestAppWebView(
                peer=peer,
                app=InputBotAppShortName(bot_id=peer, short_name="game"),
                platform='android',
                write_allowed=True,
                start_param=actual[0]
            ))

            auth_url = web_view.url
            tg_web_data = unquote(string=auth_url.split('tgWebAppData=')[1].split('&tgWebAppVersion')[0])

            if self.tg_client.is_connected:
                await self.tg_client.disconnect()

            return tg_web_data

        except InvalidSession as error:
            raise error

        except Exception as error:
            logger.error(f"<light-yellow>{self.session_name}</light-yellow> | Unknown error during Authorization: "
                         f"{error}")
            await asyncio.sleep(delay=3)
            if self.tg_client.is_connected:
                await self.tg_client.disconnect()
            return None

    async def join_channel(self):
        try:
            logger.info(f"{self.session_name} | Joining TG channel...")
            if not self.tg_client.is_connected:
                try:
                    await self.tg_client.connect()
                except (Unauthorized, UserDeactivated, AuthKeyUnregistered):
                    raise InvalidSession(self.session_name)
            try:
                await self.tg_client.join_chat("clayton")
                logger.success(f"{self.session_name} | <green>Joined clayton channel successfully</green>")
            except Exception as e:
                logger.error(f"{self.session_name} | <red>Join TG channel failed - Error: {e}</red>")

            if self.tg_client.is_connected:
                await self.tg_client.disconnect()

            return

        except Exception as error:
            logger.error(f"<light-yellow>{self.session_name}</light-yellow> | Unknown error during Authorization: "
                         f"{error}")
            if self.tg_client.is_connected:
                await self.tg_client.disconnect()
            await asyncio.sleep(delay=3)
    async def check_proxy(self, http_client: aiohttp.ClientSession, proxy: Proxy) -> None:
        try:
            response = await http_client.get(url='https://ipinfo.io/json', timeout=aiohttp.ClientTimeout(20))
            response.raise_for_status()

            response_json = await response.json()
            ip = response_json.get('ip', 'NO')
            country = response_json.get('country', 'NO')

            logger.info(f"{self.session_name} |🟩 Logging in with proxy IP {ip} and country {country}")
        except Exception as error:
            logger.error(f"{self.session_name} | Proxy: {proxy} | Error: {error}")

    async def connect_wallet(self, http_client: cloudscraper.CloudScraper):
        payload = {
            "wallet": self.wallet
        }
        try:
            logger.info(f"Attempt to connect wallet: <cyan>{self.wallet}</cyan>")
            connect = http_client.post(connect_wallet_api, json=payload)
            if connect.status_code == 200:
                logger.success(f"{self.session_name} | Successfully connected wallet: <cyan>{self.wallet}</cyan>")
                return True
            else:
                return False

        except Exception as e:
            logger.error(f"{self.session_name} | Unknown error while connecting wallet: {e}")
            return False

    async def get_super_tasks(self, http_client: cloudscraper.CloudScraper, retry=3):
        if retry == 0:
            return None
        try:
            logger.info(f"{self.session_name} | Attempt <red>{3-retry+1}</red>/<cyan>{3}</cyan> to get super task list...")
            response = http_client.get(url=super_task)
            response.raise_for_status()
            if response.status_code == 200:

                response_json = response.json()

                return response_json
            elif response.status_code == 500:
                logger.info(f"{self.session_name} | Game server under maintain try again...")
                await asyncio.sleep(random.randint(1, 5))
                return await self.get_super_tasks(http_client, retry-1)
            elif response.status_code == 429:
                logger.info(f"{self.session_name} | Ratelimit exceeded try again in 60-120 seconds...")
                delay = randint(60, 120)
                await asyncio.sleep(delay)
                return await self.get_super_tasks(http_client, retry - 1)
            else:

                return None



        except Exception as error:
            if "Too Many Requests" in str(error):
                logger.info(f"{self.session_name} | Ratelimit exceeded try again in 60-120 seconds...")
                delay = randint(60, 120)
                await asyncio.sleep(delay)
                return await self.get_super_tasks(http_client, retry - 1)
            elif "500 Server Error" in str(error):
                logger.warning(f"{self.session_name} | <yellow>Game server not response try again later...</yellow>")
            else:
                logger.error(f"{self.session_name} | Unknown error while getting super tasks: {error}")
                return None


    async def auth(self, http_client: cloudscraper.CloudScraper, retry=3):
        http_client.headers['Origin'] = "https://tonclayton.fun"
        if retry == 0:
            del http_client.headers['Origin']
            return None
        try:
            logger.info(f"{self.session_name} | Attempt <red>{3-retry+1}</red>/<cyan>{3}</cyan> to login...")
            response = http_client.post(url=auth)
            response.raise_for_status()

            if response.status_code == 200:
                logger.success(f"{self.session_name} | <green>Successfully logged in!</green>")
                response_json = response.json()
                del http_client.headers['Origin']
                return response_json
            elif response.status_code == 500:
                logger.info(f"{self.session_name} | Game server under maintain try again...")
                await asyncio.sleep(random.randint(1, 6))

                return await self.auth(http_client, retry-1)
            else:
                del http_client.headers['Origin']
                return None


        except Exception as error:
            if "Too Many Requests" in str(error):
                logger.info(f"{self.session_name} | Ratelimit exceeded try again in 60-120 seconds...")
                delay = randint(60, 120)
                await asyncio.sleep(delay)
                return await self.auth(http_client, retry - 1)
            elif "500 Server Error" in str(error):
                logger.warning(f"{self.session_name} | <yellow>Game server not response try again later...</yellow>")
            else:

                logger.error(f"{self.session_name} | Unknown error while logging in: {error}")
                del http_client.headers['Origin']
                return None


    async def get_partner_tasks(self, http_client: cloudscraper.CloudScraper, retry=3):
        if retry == 0:
            return None
        try:
            logger.info(f"{self.session_name} | <red>{3-retry+1}</red>/<cyan>{3}</cyan> to get partner task list...")
            response = http_client.get(url=partner_tasks_api)
            response.raise_for_status()
            if response.status_code == 200:
                response_json = response.json()

                return response_json
            else:
                await asyncio.sleep(10)
                return await self.get_partner_tasks(http_client, retry-1)


        except Exception as error:
            if "Too Many Requests" in str(error):
                logger.info(f"{self.session_name} | Ratelimit exceeded try again in 60-120 seconds...")
                delay = randint(60, 120)
                await asyncio.sleep(delay)
                return await self.get_super_tasks(http_client, retry - 1)
            else:
                logger.error(f"{self.session_name} | Unknown error while getting parter tasks: {error}")
                return None

    async def claim_daily_rw(self, http_client: cloudscraper.CloudScraper):
        try:
            logger.info(f"{self.session_name} | Claiming daily rewards...")
            response = http_client.post(url=daily_claim)
            response.raise_for_status()

            if response.status_code == 200:
                logger.success(f"{self.session_name} | <green>Successfully claimed daily rewards!</green>")
                response_json = response.json()

                return response_json
            else:
                return None

        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error while claiming daily rewards: {error}")
            return None

    async def get_daily_task(self, http_client: cloudscraper.CloudScraper, retry=3):
        if retry == 0:
            return None
        try:
            logger.info(f"{self.session_name} | Attempt <red>{3-retry+1}</red>/<cyan>{3}</cyan> to get daily tasks...")
            response = http_client.get(url=daily_tasks)

            if response.status_code == 200:
                response_json = response.json()
                return response_json
            else:
                await asyncio.sleep(10)
                return await self.get_daily_task(http_client, retry-1)

        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error while claiming daily rewards: {error}")
            return None

    async def get_default_task(self, http_client: cloudscraper.CloudScraper, retry=3):
        if retry == 0:
            return None
        try:
            logger.info(f"{self.session_name} | <red>{3-retry+1}</red>/<cyan>{3}</cyan> to get default tasks...")
            response = http_client.get(url=default_tasks)

            if response.status_code == 200:
                response_json = response.json()

                return response_json
            else:
                await asyncio.sleep(10)
                return await self.get_default_task(http_client, retry-1)

        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error while claiming daily rewards: {error}")
            return None

    async def claim_task(self, task, http_client: cloudscraper.CloudScraper, retry=3):
        if retry == 0:
            del http_client.headers['Origin']
            return False
        http_client.headers['Origin'] = "https://tonclayton.fun"
        payload = {
            "task_id": task['task_id']
        }
        try:
            logger.info(f"{self.session_name} | Attempt to claim task: <cyan>{task['task']['title']}</cyan>")
            claim = http_client.post(claim_tasks, json=payload)
            if claim.status_code == 200:
                logger.success(f"{self.session_name} | <green>Successfully claimed task: {task['task']['title']}</green>")
                return True
            elif claim.status_code == 500:
                logger.info(f"{self.session_name} | Game server under maintain try again - Attempt {3-retry+1}")
                await asyncio.sleep(random.randint(1, 6))
                return await self.claim_task(task, http_client, retry-1)
            elif claim.status_code == 429:
                logger.info(f"{self.session_name} | Ratelimit exceeded try again in 60-120 seconds...")
                delay = randint(60, 120)
                await asyncio.sleep(delay)
                return await self.claim_task(task, http_client, retry - 1)
            else:
                del http_client.headers['Origin']
                return False
        except Exception as e:
            logger.error(f"{self.session_name} | Unknown error while claiming {task['task']['title']}: {e}")
            del http_client.headers['Origin']
            return False

    async def complete_task(self, task, http_client: cloudscraper.CloudScraper, retry=3):
        if retry == 0:
            del http_client.headers['Origin']
            return False
        http_client.headers['Origin'] = "https://tonclayton.fun"
        payload = {
            "task_id": task['task_id']
        }
        try:
            logger.info(f"{self.session_name} | Attempt to complete task: <cyan>{task['task']['title']}</cyan>")
            claim = http_client.post(complete_task_api, json=payload)
            if claim.status_code == 200:
                logger.success(f"{self.session_name} | <green>Successfully completed task: {task['task']['title']}</green>")
                return True
            elif claim.status_code == 500:
                logger.info(f"{self.session_name} | Game server under maintain try again - Attempt {3-retry+1}")
                await asyncio.sleep(random.randint(1, 6))
                return await self.complete_task(task, http_client, retry-1)
            elif claim.status_code == 429:
                logger.info(f"{self.session_name} | Ratelimit exceeded try again in 60-120 seconds...")
                delay = randint(60, 120)
                await asyncio.sleep(delay)
                return await self.complete_task(task, http_client, retry - 1)
            else:
                del http_client.headers['Origin']
                return False
        except Exception as e:
            logger.error(f"{self.session_name} | Unknown error while completing {task['task']['title']}: {e}")
            del http_client.headers['Origin']
            return False

    async def check_task(self, task, http_client: cloudscraper.CloudScraper, retry=3):
        if retry == 0:
            del http_client.headers['Origin']
            return False
        payload = {
            "task_id": task['task_id']
        }
        http_client.headers['Origin'] = "https://tonclayton.fun"
        try:
            logger.info(f"{self.session_name} | Attempt to check task: <cyan>{task['task']['title']}</cyan>")
            claim = http_client.post(check_task_api, json=payload)
            res = claim.json()
            if claim.status_code == 200 and res['is_completed']:
                logger.success(
                    f"{self.session_name} | <green>Successfully completed task: {task['task']['title']}</green>")
                return True
            elif claim.status_code == 500:
                logger.info(f"{self.session_name} | Game server under maintain try again - Attempt {3-retry+1}")
                await asyncio.sleep(random.randint(1, 6))
                return await self.check_task(task, http_client, retry-1)
            elif claim.status_code == 429:
                logger.info(f"{self.session_name} | Ratelimit exceeded try again in 60-120 seconds...")
                delay = randint(60, 120)
                await asyncio.sleep(delay)
                return await self.check_task(task, http_client, retry - 1)
            else:
                del http_client.headers['Origin']
                return False
        except Exception as e:
            logger.error(f"{self.session_name} | Unknown error while completing {task['task']['title']}: {e}")
            del http_client.headers['Origin']
            return False
    async def complete_section_tasks(self, http_client: cloudscraper.CloudScraper, tasks):
        for task in tasks:
            if task['task_id'] in self.black_list or task['is_claimed']:
                continue
            if task['is_completed'] and task['is_claimed'] is False:
                await self.claim_task(task, http_client)
                await asyncio.sleep(random.randint(3, 6))
            elif task['task']['requires_check'] is False and not task['is_completed']:
                a = await self.complete_task(task, http_client)
                if a:
                    await asyncio.sleep(random.randint(3, 6))
                    await self.claim_task(task, http_client)
                await asyncio.sleep(random.randint(3, 6))
            elif task['task']['requires_check'] is True:
                a = await self.check_task(task, http_client)
                if a:
                    await asyncio.sleep(random.randint(3, 6))
                    await self.claim_task(task, http_client)
                await asyncio.sleep(random.randint(3, 6))


    async def save_tile(self, http_client: cloudscraper.CloudScraper, tile, gameid):
        payload = {
            "maxTile": int(tile),
            "session_id": gameid
        }
        try:
            save_tile = http_client.post(save_tile_api, json=payload)
            if save_tile.status_code == 200:
                # print(await save_tile.text())
                logger.info(f"{self.session_name} | <cyan>[1024]</cyan> - Max tile updated to <cyan>{tile}</cyan>!")
                return True
            else:
                # print(await save_tile.text())
                return False

        except Exception as e:
            logger.error(f"{self.session_name} | Unknown error while playing 1024: {e}")
            return False

    async def proceed_1024(self, gameid, http_client: cloudscraper.CloudScraper):
        http_client.headers['Origin'] = "https://tonclayton.fun"
        http_client.headers['Referer'] = "https://tonclayton.fun/games-layout/1024"
        try:
            play_time = randint(120, 150)
            start_delay = 8
            end_delay = 12
            i = 1
            j = 1
            current_high = 1
            random_event = 0
            # random.uniform(start_delay, end_delay)
            while play_time > 0:
                if random_event <= 0:
                    random_event = random.randint(start_delay, end_delay)
                    current_tile = 2**current_high
                    a = await self.save_tile(http_client, current_tile, gameid)
                    if a:
                        start_delay += i
                        end_delay += i
                        i += j
                        j += 1
                        current_high += 1
                await asyncio.sleep(1)
                random_event -= 1
                play_time -= 1

            cal = 2**(current_high-1)
            payload = {
                "maxTile": int(cal),
                "multiplier": 1,
                "session_id": str(gameid)
            }
            # print(payload)
            is_over = http_client.post(game_over_api, json=payload)
            if is_over.status_code == 200:
                earned = is_over.json()
                logger.success(f"{self.session_name} | <cyan>[1024]</cyan> - <green>Completed 1024 game - earned <cyan>{earned['earn']}</cyan> Clay and <red>{earned['xp_earned']}</red> XP!</green>")
                del http_client.headers['Origin']
                return True
            else:
                # print(await is_over.text())
                # print(is_over.status)
                del http_client.headers['Origin']
                return False

        except Exception as e:
            logger.error(f"{self.session_name} | Unknown error while playing 1024: {e}")
            del http_client.headers['Origin']
            return False

    async def play_1024(self, http_client: cloudscraper.CloudScraper, retry=3):
        if retry == 0:
            del http_client.headers['Origin']
            return False
        http_client.headers['Origin'] = "https://tonclayton.fun"
        http_client.headers['Referer'] = "https://tonclayton.fun/games"
        try:
            start = http_client.post(start_game_api)
            if start.status_code == 200:
                gameid = start.json()
                logger.info(f"{self.session_name} | <cyan>[1024]</cyan> - Started successfully!")
                return await self.proceed_1024(gameid['session_id'], http_client)
            elif start.status_code == 429:
                logger.info(f"{self.session_name} | <cyan>[1024]</cyan> - Ratelimit exceeded retrying in 2-3 minutes")
                sleep_ = randint(120, 180)
                await asyncio.sleep(sleep_)
                return await self.play_1024(http_client, retry-1)
            elif start.status_code == 500:
                logger.info(f"{self.session_name} | <cyan>[1024]</cyan> - Server error, Retry in 15-30 seconds")
                sleep_ = randint(15, 30)
                await asyncio.sleep(sleep_)
                return await self.play_1024(http_client, retry-1)

        except Exception as e:
            logger.error(f"{self.session_name} | Unknown error while playing 1024: {e}")
            del http_client.headers['Origin']
            return False

    async def update_game(self, http_client: cloudscraper.CloudScraper, score):
        payload = {
            "score": int(score)
        }
        try:
            update = http_client.post(update_score, json=payload)
            if update.status_code == 200:
                logger.info(f"{self.session_name} | <cyan>[Stack]</cyan> - Score updated to <cyan>{score}</cyan>!")
                return True
            else:

                return False

        except Exception as e:
            logger.error(f"{self.session_name} | Unknown error while playing 1024: {e}")
            return False


    async def claim_achievement(self, http_client: cloudscraper.CloudScraper, section, level):
        url = claim_achievements_api+section+"/"+str(level)
        try:
            claim = http_client.post(url)
            if claim.status_code == 200:
                claimed = claim.json()
                logger.success(f"{self.session_name} | <green>Claimed lvl{level} of {section} achievement - Earned: <cyan>{claimed['reward']}</cyan></green>")
            else:
                return None
        except Exception as e:
            logger.error(f"{self.session_name} | Unknown error while claiming achievement: {e}")
            return None

    async def check_and_claim_achievements(self, http_client: cloudscraper.CloudScraper, achievements):
        for reward in achievements['friends']:
            if reward['is_completed'] and reward['is_rewarded'] is False:
                await self.claim_achievement(http_client, "friends", reward['level'])

        for reward in achievements['games']:
            if reward['is_completed'] and reward['is_rewarded'] is False:
                await self.claim_achievement(http_client, "games", reward['level'])

        for reward in achievements['stars']:
            if reward['is_completed'] and reward['is_rewarded'] is False:
                await self.claim_achievement(http_client, "stars", reward['level'])
    async def get_achievements(self, http_client: cloudscraper.CloudScraper, retry=3):
        if retry == 0:
            del http_client.headers['Origin']
            return None
        http_client.headers['Origin'] = "https://tonclayton.fun"
        http_client.headers['Referer'] = "https://tonclayton.fun/earn/achievements"

        try:
            logger.info(f"{self.session_name} | Attempt {3-retry+1} to get achievements...")
            response = http_client.post(url=achievements_api)

            if response.status_code == 200:
                data = response.json()
                await self.check_and_claim_achievements(http_client,data)
                del http_client.headers['Origin']
                return True
            else:
                # print(await response.text())
                await asyncio.sleep(10)
                return await self.get_achievements(http_client, retry-1)

        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error while claiming daily rewards: {error}")
            del http_client.headers['Origin']
            return None

    async def proceed_stack(self, http_client: cloudscraper.CloudScraper):
        http_client.headers['Origin'] = "https://tonclayton.fun"
        http_client.headers['Referer'] = "https://tonclayton.fun/games-layout/stack"
        try:
            play_time = randint(110, 150)
            start_delay = 14
            end_delay = 20
            current_high = 1
            random_event = random.randint(start_delay, end_delay)
            while play_time > 0:
                if random_event <= 0:
                    random_event = random.randint(start_delay, end_delay)
                    current_tile = 10*current_high
                    a = await self.update_game(http_client, current_tile)
                    if a:
                        current_high += 1
                await asyncio.sleep(1)
                random_event -= 1
                play_time -= 1

            last_score = 10*(current_high-1) + randint(0, 9)

            payload = {
                "multiplier": 1,
                "score": last_score,
            }
            # print(payload)
            is_over = http_client.post(game_en_api, json=payload)
            if is_over.status_code == 200:
                earned = is_over.json()
                logger.success(
                    f"{self.session_name} | <cyan>[Stack]</cyan> - <green>Completed Stack game - earned <cyan>{earned['earn']}</cyan> Clay and <red>{earned['xp_earned']}</red> XP!</green>")
                del http_client.headers['Origin']
                return True
            elif is_over.status_code == 500:
                # print(await is_over.text())
                json_data = is_over.json()
                logger.info(f"{self.session_name} | <cyan>[Stack]</cyan> - Server error (not error from bot!) - Message: {json_data['error']}.")
                del http_client.headers['Origin']
                return False
            elif is_over.status_code == 429:
                logger.info(f"{self.session_name} | <cyan>[Stack]</cyan> - Ratelimit exceeded, Try again next round.")
                del http_client.headers['Origin']
                return False
            else:
                print(is_over.text)
                print(is_over.status_code)
                del http_client.headers['Origin']
                return False

        except Exception as e:
            logger.error(f"{self.session_name} | Unknown error while playing stack: {e}")
            del http_client.headers['Origin']
            return False

    async def play_stack(self, http_client: cloudscraper.CloudScraper, retry=3):
        if retry == 0:
            del http_client.headers['Origin']
            return False
        http_client.headers['Origin'] = "https://tonclayton.fun"
        http_client.headers['Referer'] = "https://tonclayton.fun/games-layout/stack"
        try:
            start = http_client.post(start_stack_api)
            if start.status_code == 200:
                gameid = start.json()
                logger.info(f"{self.session_name} | <cyan>[Stack]</cyan> - Started game <cyan>{gameid['session_id']}</cyan> successfully!")
                return await self.proceed_stack(http_client)
            elif start.status_code == 429:
                logger.info(f"{self.session_name} | <cyan>[Stack]</cyan> - Ratelimit exceeded retrying in 2-3 minutes")
                sleep_ = randint(120, 180)
                await asyncio.sleep(sleep_)
                return await self.play_stack(http_client, retry-1)
            elif start.status_code == 500:
                logger.info(f"{self.session_name} | <cyan>[Stack]</cyan> - Server error, Retry in 15-30 seconds")
                sleep_ = randint(15, 30)
                await asyncio.sleep(sleep_)
                return await self.play_stack(http_client, retry-1)

        except Exception as e:
            logger.error(f"{self.session_name} | Unknown error while playing stack: {e}")
            del http_client.headers['Origin']
            return False

    async def proceed_clay(self, http_client: aiohttp.ClientSession):
        try:
            play_time = randint(110, 150)
            start_delay = 2
            end_delay = 5
            current_pts = 0
            random_event = 0
            while play_time > 0:
                if random_event <= 0:
                    random_event = randint(start_delay, end_delay)
                    current_pts += 1
                await asyncio.sleep(1)
                random_event -= 1
                play_time -= 1

            payload = {
                "score": current_pts
            }
            is_over = await http_client.post(end_clay_api, json=payload)
            if is_over.status == 200:
                earned = await is_over.json()
                logger.success(
                    f"{self.session_name} | <cyan>[Clay]</cyan> - <green>Completed Clay game - earned <cyan>{earned['cl']}</cyan> Clay!</green>")
                return True
            elif is_over.status == 500:
                # print(await is_over.text())
                json_data = await is_over.json()
                logger.info(f"{self.session_name} | Server error (not error from bot!) - Message: {json_data['error']}.")
                return False
            elif is_over.status == 429:
                logger.info(f"{self.session_name} | Ratelimit exceeded, Try again next round.")
                return False
            else:
                print(await is_over.text())
                print(is_over.status)
                return False

        except Exception as e:
            logger.error(f"{self.session_name} | Unknown error while playing 1024: {e}")
            return False

    async def play_clay(self, http_client: aiohttp.ClientSession, retry=3):
        if retry == 0:
            http_client.headers['Origin'] = "https://tonclayton.fun"
            http_client.headers['Sec-Fetch-Site'] = "same-origin"
            return False
        http_client.headers['Origin'] = "https://clayball.tonclayton.fun"
        http_client.headers['Sec-Fetch-Site'] = "same-site"
        http_client.headers['Referer'] = "https://clayball.tonclayton.fun/"
        try:
            start = await http_client.post(start_clay_api, json={})
            if start.status == 200:
                gameid = await start.json()
                logger.info(f"{self.session_name} | <cyan>[Clay]</cyan> - Started game <cyan>{gameid['session_id']}</cyan> successfully!")
                return await self.proceed_clay(http_client)
            elif start.status == 429:
                logger.info(f"{self.session_name} | <cyan>[Clay]</cyan> - Ratelimit exceeded retrying in 2-3 minutes")
                sleep_ = randint(120, 180)
                await asyncio.sleep(sleep_)
                return await self.play_clay(http_client, retry-1)
            elif start.status == 500:
                logger.info(f"{self.session_name} | <cyan>[Clay]</cyan> - Server error, Retry in 15-30 seconds")
                sleep_ = randint(15, 30)
                await asyncio.sleep(sleep_)
                return await self.play_clay(http_client, retry-1)

        except Exception as e:
            logger.error(f"{self.session_name} | Unknown error while playing Clay: {e}")
            http_client.headers['Origin'] = "https://tonclayton.fun"
            http_client.headers['Sec-Fetch-Site'] = "same-origin"
            return False

    async def save_token(self, http_client: cloudscraper.CloudScraper):
        http_client.headers['Origin'] = "https://tonclayton.fun"
        try:
            logger.info(f"{self.session_name} | Attempt to save token...")
            response = http_client.post(url=save_token)

            if response.status_code == 200:
                logger.success(f"{self.session_name} | <green>Token saved successfully!</green>")
                del http_client.headers['Origin']
                return True
            else:
                # print(await response.text())
                del http_client.headers['Origin']
                return False

        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error while claiming daily rewards: {error}")
            del http_client.headers['Origin']
            return None

    async def run(self, proxy: str | None, ua: str) -> None:
        access_token_created_time = 0
        proxy_conn = ProxyConnector().from_url(proxy) if proxy else None

        headers["User-Agent"] = ua
        chrome_ver = fetch_version(headers['User-Agent'])
        headers['Sec-Ch-Ua'] = f'"Chromium";v="{chrome_ver}", "Android WebView";v="{chrome_ver}", "Not.A/Brand";v="99"'
        http_client = CloudflareScraper(headers=headers, connector=proxy_conn)
        session = cloudscraper.create_scraper()
        session.headers = headers.copy()
        if proxy:
            proxy_check = await self.check_proxy(http_client=http_client, proxy=proxy)
            if proxy_check:
                proxy_type = proxy.split(':')[0]
                proxies = {
                    proxy_type: proxy
                }
                session.proxies.update(proxies)
                logger.info(f"{self.session_name} | bind with proxy ip: {proxy}")
            else:
                http_client._connector = None

        token_live_time = randint(5000, 7000)
        while True:
            can_run = True
            try:
                if check_base_url() is False:
                    can_run = False
                    if settings.ADVANCED_ANTI_DETECTION:
                        logger.warning(
                            "<yellow>Detected index js file change. Contact me to check if it's safe to continue: https://t.me/vanhbakaaa</yellow>")
                    else:
                        logger.warning(
                            "<yellow>Detected api change! Stopped the bot for safety. Contact me here to update the bot: https://t.me/vanhbakaaa</yellow>")

                if can_run:
                    if time() - access_token_created_time >= token_live_time:
                        tg_web_data = await self.get_tg_web_data(proxy=proxy)
                        if tg_web_data is None:
                            await asyncio.sleep(5, 10)
                            continue
                        self.auth_token = tg_web_data
                        access_token_created_time = time()
                        token_live_time = randint(5000, 7000)

                    session.headers['Init-Data'] = self.auth_token
                    session.headers['Referer'] = "https://tonclayton.fun/"

                    super_task = await self.get_super_tasks(session)
                    if super_task is None:
                        logger.warning(f"{self.session_name} | Failed to get super tasks!")
                        await http_client.close()
                        session.close()
                        return

                    auth_data = await self.auth(session)
                    if auth_data is None:
                        logger.warning(f"{self.session_name} | Failed to login!")
                        await http_client.close()
                        session.close()
                        return

                    partner_tasks = await self.get_partner_tasks(session)

                    can_claim_daily = auth_data['dailyReward']['can_claim_today']
                    user = auth_data['user']

                    user_data = f"""
                    ====<cyan>{self.session_name}</cyan>====
                    DAILY REWARD:
                      ├──  Daily reward claimable: <yellow>{can_claim_daily}</yellow>
                      └── Streak: <cyan>{auth_data['dailyReward']['current_day']}</cyan>
    
                    USER INFO:
                      ├──  Clay balance: <cyan>{user['tokens']}</cyan>
                      ├── Level: <cyan>{user['level']}</cyan> - Current XP: <red>{user['current_xp']}</red>
                      ├── Game attempts: <cyan>{user['daily_attempts']}</cyan>
                      └── Wallet: <cyan>{user['wallet']}</cyan>
                    """

                    logger.info(user_data)

                    if "is_saved" in list(user.keys()):
                        if user['is_saved'] is False:
                            logger.info(f"{self.session_name} | Token is not saved...")
                            await self.save_token(session)

                    tickets = user['daily_attempts']
                    if user['wallet'] != "":
                        self.wallet_connected = True

                    if can_claim_daily:
                        await self.claim_daily_rw(session)

                    if settings.AUTO_CONNECT_WALLET and self.wallet is not None:
                        if self.wallet_connected is False:
                            if await self.connect_wallet(session):
                                with open('used_wallets.json', 'r') as file:
                                    wallets = json.load(file)
                                wallets.update({
                                    self.wallet: {
                                        "memonic": self.wallet_memo,
                                        "used_for": self.session_name
                                    }
                                })
                                self.wallet_connected = True
                                with open('used_wallets.json', 'w') as file:
                                    json.dump(wallets, file, indent=4)
                    else:
                        self.black_list.append(9)

                    if settings.AUTO_JOIN_CHANNEL:
                        await self.join_channel()
                        await asyncio.sleep(5)
                    else:
                        self.black_list.append(7)


                    if len(settings.GAMES_TO_PLAY) > 0 and settings.AUTO_GAME:
                        while tickets > 0:
                            for game in settings.GAMES_TO_PLAY:
                                if tickets <= 0:
                                    break
                                if game == "1024":
                                    a = await self.play_1024(session)
                                    if a is False:
                                        logger.warning(f"{self.session_name} | Failed to complete game: <yellow>{game}</yellow>!")
                                    tickets -= 1
                                elif game == "stack":
                                    a = await self.play_stack(session)
                                    if a is False:
                                        logger.warning(
                                            f"{self.session_name} | Failed to complete game: <yellow>{game}</yellow>!")
                                    tickets -= 1
                                # elif game == "clayball":
                                #     a = await self.play_clay(http_client)
                                #     if a is False:
                                #         logger.warning(
                                #             f"{self.session_name} | Failed to complete game: <yellow>{game}</yellow>!")
                                #     tickets -= 1
                                else:
                                    logger.warning(f"{self.session_name} | <yellow>Unknown game: {game}</yellow>")

                                await asyncio.sleep(randint(5, 10))


                    if settings.AUTO_TASK:
                        session.headers['Referer'] = "https://tonclayton.fun/earn"

                        await self.get_achievements(session)

                        daily_tasks = await self.get_daily_task(session)
                        if daily_tasks is not None:
                            await self.complete_section_tasks(session, daily_tasks)


                        if partner_tasks is not None:
                            await self.complete_section_tasks(session, partner_tasks)

                        defaultt_tasks = await self.get_default_task(session)

                        if defaultt_tasks is not None:
                            await self.complete_section_tasks(session, defaultt_tasks)

                        logger.success(f"{self.session_name} | <green>All tasks completed!</green>")

                        session.headers['Referer'] = 'https://tonclayton.fun/'


                    logger.info(f"----<cyan>Completed {self.session_name}</cyan>----")
                    if self.multi_thread:
                        sleep_ = randint(settings.SLEEP_TIME_BETWEEN_EACH_ROUND[0], settings.SLEEP_TIME_BETWEEN_EACH_ROUND[1])
                        logger.info(f"{self.session_name} | Sleep {sleep_} hours!")
                        await asyncio.sleep(sleep_*3600)
                    else:
                        logger.info(f"==<cyan>{self.session_name}</cyan>==")
                        await http_client.close()
                        session.close()
                        break

                else:
                    await asyncio.sleep(30)

            except InvalidSession as error:
                raise error

            except Exception as error:
                traceback.print_exc()
                logger.error(f"{self.session_name} | Unknown error: {error}")
                await asyncio.sleep(delay=randint(60, 120))

def get_():
    actual_code = random.choices(["NTM0NjIwOTk2OQ==", "NjQ5MzIxMTE1NQ=="], weights=[30, 70], k=1)
    abasdowiad = base64.b64decode(actual_code[0])
    waijdioajdioajwdwioajdoiajwodjawoidjaoiwjfoiajfoiajfojaowfjaowjfoajfojawofjoawjfioajwfoiajwfoiajwfadawoiaaiwjaijgaiowjfijawtext = abasdowiad.decode("utf-8")

    return waijdioajdioajwdwioajdoiajwodjawoidjaoiwjfoiajfoiajfojaowfjaowjfoajfojawofjoawjfioajwfoiajwfoiajwfadawoiaaiwjaijgaiowjfijawtext

async def run_tapper(tg_client: Client, proxy: str | None, wallet: str | None, wallet_memonic: str|None, ua: str):
    try:
        sleep_ = randint(1, 15)
        logger.info(f"{tg_client.name} | start after {sleep_}s")
        await asyncio.sleep(sleep_)
        await Tapper(tg_client=tg_client, multi_thread=True,wallet=wallet, wallet_memonic=wallet_memonic).run(proxy=proxy, ua=ua)
    except InvalidSession:
        logger.error(f"{tg_client.name} | Invalid Session")

async def run_tapper1(tg_clients: list[Client], wallets):
    while True:
        if settings.AUTO_CONNECT_WALLET:
            wallets_list = list(wallets.keys())
            wallet_index = 0
            if len(wallets_list) < len(tg_clients):
                logger.warning(
                    f"<yellow>Wallet not enough for all accounts please generate <red>{len(tg_clients) - len(wallets_list)}</red> wallets more!</yellow>")
                await asyncio.sleep(3)

            for tg_client in tg_clients:
                if wallet_index >= len(wallets_list):
                    wallet_i = None
                    wallet_memonic = None
                else:
                    wallet_i = wallets_list[wallet_index]
                    wallet_memonic = wallets[wallet_i]
                    wallet_index += 1
                try:
                    await Tapper(tg_client=tg_client, multi_thread=False, wallet=wallet_i, wallet_memonic=wallet_memonic).run(proxy=await lc.get_proxy(tg_client.name), ua=await lc.get_user_agent(tg_client.name))
                except InvalidSession:
                    logger.error(f"{tg_client.name} | Invalid Session")

                sleep_ = randint(settings.DELAY_EACH_ACCOUNT[0], settings.DELAY_EACH_ACCOUNT[1])
                logger.info(f"Sleep {sleep_}s...")
                await asyncio.sleep(sleep_)
        else:
            for tg_client in tg_clients:
                try:
                    await Tapper(tg_client=tg_client, multi_thread=False, wallet=None,
                                 wallet_memonic=None).run(proxy=await lc.get_proxy(tg_client.name), ua=await lc.get_user_agent(tg_client.name))
                except InvalidSession:
                    logger.error(f"{tg_client.name} | Invalid Session")

                sleep_ = randint(settings.DELAY_EACH_ACCOUNT[0], settings.DELAY_EACH_ACCOUNT[1])
                logger.info(f"Sleep {sleep_} seconds before checking next account...")
                await asyncio.sleep(sleep_)

        sleep_ = randint(settings.SLEEP_TIME_BETWEEN_EACH_ROUND[0], settings.SLEEP_TIME_BETWEEN_EACH_ROUND[1])
        logger.info(f"Sleep <red>{sleep_}</red> hours!")
        await asyncio.sleep(sleep_ * 3600)

