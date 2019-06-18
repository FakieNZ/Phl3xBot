import os
import irc.bot
import requests
import sqlite3
import time
import datetime
import random
from time import sleep
from threading import Thread
import json
from mock import mock
import math
from case_data import cases, stattrak, knives, knife_skins, wear
from csgo_stats import csgo_stats_kd, csgo_stats_wl, csgo_stats_lastmatch, csgo_stats_rifle, csgo_stats_pistol, csgo_stats_smg, csgo_stats_shotgun 
from csgo_stats import csgo_stats_maps, csgo_stats_knife, csgo_stats_1337boi, csgo_stats_nades, csgo_stats_brassandlead, csgo_stats_bomb
from settings import username, clientid, channel, spotify_username

twitch_tokens_db = os.path.join(os.path.dirname(__file__), 'twitch_tokens.sqlite')
chat_db = os.path.join(os.path.dirname(__file__), 'chat_commands.db')
token_db = os.path.join(os.path.dirname(__file__), 'spotify_tokens.db')
chat_log_db = os.path.join(os.path.dirname(__file__), 'chat_log.db')
csgo_case_db = os.path.join(os.path.dirname(__file__), 'csgo_cases.db')

class ListenerBot(irc.bot.SingleServerIRCBot):
    def __init__(self, username, client_id, channel):
        global chat_db
        global token_db
        global chat_log_db
        global twitch_tokens_db

        self.client_id = client_id
        self.token = self.get_twitch_token(username)
        self.channel = '#' + channel
        
        url = 'https://api.twitch.tv/kraken/users?login=' + channel 
        headers = {'Client-ID': client_id, 'Accept': 'application/vnd.twitchtv.v5+json'}
        r = requests.get(url, headers=headers).json()
        self.channel_id = r['users'][0]['_id']
        
        server = 'irc.chat.twitch.tv'
        port = 6667
        print ('Connecting to ' + server + ' on port ' + str(port) + '...')
        irc.bot.SingleServerIRCBot.__init__(self, [(server, port, 'oauth:'+ self.token)], username, username)

    def __call__(self):
        self.start()

    def log_message(self, e):
        #Commit an entry to the chat log db
        timestamp = datetime.datetime.now()
        username = e.source.split('@')[1]
        user_id = e.tags[12]['value']
        user_type = e.tags[13]['value']
        display_name = e.tags[3]['value']
        message = e.arguments[0]
        
        #Chat Logs Database Connection + Cursor + SQL Execution
        chat_log_con = sqlite3.connect(chat_log_db)
        chat_log_cursor = chat_log_con.cursor()
        sql ="""
            INSERT INTO chat_log (timestamp, username, user_id, user_type, display_name, message) 
            VALUES (?, ?, ?, ?, ?, ?)"""
        
        chat_log_cursor.execute(sql, (timestamp, username, user_id, user_type, display_name, message))
        chat_log_con.commit()
        chat_log_con.close()
    
    def is_channel_live(self, channel_id):
        #returns "live" or "" for channel_id ARG
        url = 'https://api.twitch.tv/helix/streams?user_id=' + channel_id
        headers = {'Client-ID': self.client_id}
        r = requests.get(url, headers=headers).json()
        if len(r['data']) > 0: #r['data'][0]['type'] == 'live'
            s = 'live'
        else:
            s = 'offline'
        return s

    def get_channel_stats(self, channel_id):
        #viewers
        url = 'https://api.twitch.tv/helix/streams?user_id=' + channel_id
        headers = {'Client-ID': self.client_id}
        r = requests.get(url, headers=headers).json()
        viewers = r['data'][0]['viewer_count']
        #subcount
        subcount = self.get_channel_subcount()
        #views 
        url = 'https://api.twitch.tv/helix/users?id=' + channel_id
        r = requests.get(url, headers=headers).json()
        views = r['data'][0]['view_count']
        #followers
        to_id = self.get_channel_id(channel)
        headers = headers = {'Client-ID': self.client_id}
        url = 'https://api.twitch.tv/helix/users/follows?to_id=' + to_id
        r = requests.get(url, headers=headers).json()
        followers = r['total']

        return viewers, subcount, views, followers

    def get_twitch_token(self, username):
        con = sqlite3.connect(twitch_tokens_db)
        c = con.cursor()
        c.execute("SELECT access_token FROM tokens WHERE username = ?", [username])
        access_token = c.fetchone()
        con.close()
        return access_token[0]

    def bot_log_message(self, message):
        #Commit an entry to the chat log db
        timestamp = datetime.datetime.now()
        username = 'phl3xbot.tmi.twitch.tv'
        user_id = '*#66767#'
        user_type = 'Bot'
        display_name = 'Phl3xBot'
        message = message
        
        #Chat Logs Database Connection + Cursor + SQL Execution
        chat_log_con = sqlite3.connect(chat_log_db)
        chat_log_cursor = chat_log_con.cursor()
        sql ="""
            INSERT INTO chat_log (timestamp, username, user_id, user_type, display_name, message) 
            VALUES (?, ?, ?, ?, ?, ?)"""
        
        chat_log_cursor.execute(sql, (timestamp, username, user_id, user_type, display_name, message))
        chat_log_con.commit()
        chat_log_con.close()
    
    def post_message(self, message):
        c = self.connection
        self.bot_log_message(message)
        c.privmsg(self.channel, message)
    
    def get_channel_id(self, username):
        url = 'https://api.twitch.tv/kraken/users?login=' + username 
        headers = {'Client-ID': self.client_id, 'Accept': 'application/vnd.twitchtv.v5+json'}
        r = requests.get(url, headers=headers).json()
        print (r['users'])
        if r['users'] == []:
            raise Exception('get_channel_id failed')
        channel_id = r['users'][0]['_id']
        return channel_id

    def on_welcome(self, c, e):
        print ('Joining ' + self.channel)
        print (datetime.datetime.now())
        c.cap('REQ', ':twitch.tv/membership')
        c.cap('REQ', ':twitch.tv/tags')
        c.cap('REQ', ':twitch.tv/commands')
        c.join(self.channel)
        time.sleep(2)
        self.post_message('/color Green')            

    def on_pubmsg(self, c, e):
        global chat_db
        self.log_message(e)
        print (e.source + ' - ' + e.arguments[0])

        #message = e.arguments[0]
        usr = e.tags[3]['value']
        cmd = e.arguments[0].lower().split(' ')[0][1:]
        cmdargs = e.arguments[0].split(' ')[1:]

        if e.tags[3]['value'] in ['Nightbot','jnzl']:
            msg = 'hi im ' + e.tags[3]['value'] + ' and ' + e.arguments[0].lower()
            mocked_msg = mock(msg)
            self.post_message(mocked_msg)
        
        elif e.arguments[0][:1] == '!':
            print ('Received command: ' + cmd)
            self.do_user_command(e, cmd, cmdargs, usr)

        elif e.arguments[0][:1] == '#':
            if e.tags[7]['value'] == 1 or e.tags[13]['value'] == 'mod' :
                print ('Received Mod command: ' + cmd)
                self.do_mod_command(e, cmd, cmdargs, usr)    
            else:
                print ('Ignored Mod command from a user')
                self.post_message('/me #Locals Only, Bro. No Kooks!') 
                sleep(2)
                self.post_message("Commands with '#' are for Mods, Have a siick vid instead - https://www.youtube.com/watch?v=PK28Kaj-X-4")
                
        elif e.arguments[0].lower().split(' ')[0] in ['rephl3xwhut','kappa','kappapride','gachibass']:
            cmd = e.arguments[0].lower().split(' ')[0]
            print ('Received "other" command: ' + cmd)
            self.do_user_command(e, cmd, cmdargs, usr)

        else:
            pass   

    def do_user_command(self, e, cmd, cmdargs, usr):
        global chat_db
        con = sqlite3.connect(chat_db)
        cursor = con.cursor()
        cursor.execute("SELECT command_result FROM chat_commands WHERE command = ?", [cmd])
        sqlcmd = cursor.fetchall()
        cursor.close()
        
        if sqlcmd:
            self.post_message(sqlcmd[0][0])

        ### Advanced/Logic Chat Commands ###
        elif cmd in ['bot','phl3xbot', 'nightbot']:
            self.post_message("I was forced to read 10,000 of Rephl3x's tweets and now i'm much better than nightbot - https://www.youtube.com/watch?v=OWwOJlOI1nU")
            self.post_message('/me Wiki: https://bit.ly/2uP3lrB')
            self.post_message('/me Commands: https://bit.ly/2U0mh0P')
            self.post_message('/me Support: Send a whisper to FakieNZ')

        elif cmd == "bestfollower":
            if usr == "FakieNZ":
                self.post_message(usr)
            else:
                self.post_message('not ' + usr)

        elif cmd == 'penis':
            penis_size = random.randint(1, 30)
            self.post_message('@' + str(usr) + ', Your penis is ' + str(penis_size) + ' Centimeters')
        
        elif cmd == 'rr':
            self.post_message('How many cowboys?')
            sleep(3)
            self.post_message('18')
        
        elif cmd == 'lmgtfy':
            if cmdargs != None:
                g_prefix = 'https://www.google.com/search?q='
                g_suffix = " ".join(map(str, cmdargs))
                g_suffix = g_suffix.replace(' ','+')
                self.post_message(g_prefix + g_suffix)
            else:
                pass

        #TWITCH-API-GAME
        elif cmd == "game":
            url = 'https://api.twitch.tv/kraken/channels/' + self.channel_id
            headers = {'Client-ID': self.client_id, 'Accept': 'application/vnd.twitchtv.v5+json'}
            r = requests.get(url, headers=headers).json()
            self.post_message('Ya boi ' + r['display_name'] + ' is currently playing ' + r['game'])

        #TWITCH-API-TITLE
        elif cmd == "title":
            url = 'https://api.twitch.tv/kraken/channels/' + self.channel_id
            headers = {'Client-ID': self.client_id, 'Accept': 'application/vnd.twitchtv.v5+json'}
            r = requests.get(url, headers=headers).json()
            self.post_message(r['status'])

        #TWITCH-API-UPTIME
        elif cmd == "uptime":
            url = 'https://api.twitch.tv/kraken/streams/' + self.channel_id
            headers = {'Client-ID': self.client_id, 'Accept': 'application/vnd.twitchtv.v5+json'}
            r = requests.get(url, headers=headers).json()
            print (r['stream'])
            if r['stream'] == None:
                self.post_message('Ya boi is busy doing other shit')
            else:
                raw_stream_started_at = r['stream']['created_at'] #Twitch Time (UTC) Format 2019-04-07T03:42:54Z 
                UTC_stream_started_at = datetime.datetime.strptime(raw_stream_started_at, '%Y-%m-%dT%H:%M:%SZ')
                Local_stream_started_at = UTC_stream_started_at + datetime.timedelta(hours=12)  
                Local_stream_started_at_timeobject = Local_stream_started_at.time()

                Local_datetime_now = datetime.datetime.now()
                
                stream_uptime = Local_datetime_now - Local_stream_started_at
                stream_uptime_str = str(stream_uptime)
                stream_uptime_hours = stream_uptime_str.split(':')[0]
                stream_uptime_minutes = stream_uptime_str.split(':')[1]             
            
                self.post_message('Streaming since ' + str(Local_stream_started_at_timeobject) + ' NZ Time')
                self.post_message('Ya boi has been live for ' + stream_uptime_hours + ' hours ' + stream_uptime_minutes + ' minutes (or at least time since the last internet flap LUL )')

        #TWITCH-API-SUBCOUNT
        elif cmd == "subcount":
            count = self.get_channel_subcount()
            self.post_message(str(count) + ' worms have been hooked and baited!')
            sleep (2)
            self.post_message('Join the Phl3x Crew: https://www.twitch.tv/subs/Rephl3x')

        #Twitch-API-FOLLOWAGE
        elif cmd == "followage":
            #https://dev.twitch.tv/docs/api/reference/#get-users-follows
            try:
                if cmdargs != []:
                    from_id = self.get_channel_id(cmdargs[0])
                    s_usr = cmdargs[0]
                else:    
                    from_id = self.get_channel_id(usr)
                    s_usr = usr
                
                to_id = self.get_channel_id(channel)

                headers = headers = {'Client-ID': self.client_id}
                url = 'https://api.twitch.tv/helix/users/follows?from_id=' + from_id + '&to_id=' + to_id
                r = requests.get(url, headers=headers)

                if r.status_code == 200:
                    r = r.json()
                    if r["total"] == 0:
                        self.post_message('The name you provided didnt match a valid twitch account or they are not currently following Rephl3x (Error: FA1)')    
                    
                    else:
                        followed_at = r["data"][0]["followed_at"] #Twitch Time (UTC) Format 2019-04-07T03:42:54Z 
                        utc_followed_at = datetime.datetime.strptime(followed_at, '%Y-%m-%dT%H:%M:%SZ')
                        local_followed_at = utc_followed_at + datetime.timedelta(hours=12)
                        now = datetime.datetime.now()
                        followed_time = now - local_followed_at

                        #FakieNZ has been following Rephl3x for 2 weeks, 6 days
                        print (str(followed_time.days))
                        self.post_message(s_usr + ' has been following for ' + str(followed_time.days) + ' days.')
                else:
                    self.post_message('Error: User not found: ' + s_usr)

            except Exception:
                print(Exception)
                self.post_message('The name you provided didnt match a valid twitch account or they are not currently following Rephl3x (Error: FA2)') 

        #SpotifyAPI-CurrentSong
        elif cmd == "song":
            conection = sqlite3.connect(token_db)
            cursor = conection.cursor()
            load_sql = "SELECT access_token,refresh_token FROM spotify_token WHERE username = ?"
            cursor.execute(load_sql, [spotify_username])
            token_data = cursor.fetchone()
            conection.close()
            access_token = token_data[0]
            access_token = str('Bearer ' + access_token)             
            
            url = 'https://api.spotify.com/v1/me/player/currently-playing'          
            headers = {'Accept': 'application/json', 'Content-Type': 'application/json', 'Authorization': access_token}
            
            try:
                song = requests.get(url, headers=headers)
                print (f'HTTP Code {song.status_code}')
                #check the HTTP Codes in the API response
                if song.status_code == 204:
                    self.post_message('Ya boi aint got nothing playing on Spotify')
                
                else:        
                    song = song.json()
                    
                    if 'error' in song:
                        self.post_message('Spotify API Error: ' + str(song['error']['status']) + ' - ' + song['error']['message'])
                    elif song['is_playing'] != True:
                        self.post_message('Ya boi aint got nothing playing on Spotify')
                    elif song['item']:    
                        self.post_message('Ya boi is currently playing ' + song['item']['name'] + ' by ' + song['item']['artists'][0]['name'] + ' from the album ' + song['item']['album']['name'])
                        self.post_message('Check it out here: ' + song['item']['external_urls']['spotify'])
                    else:
                        pass

            except Exception:
                print(Exception)
                self.post_message('@FakieNZ can\'t figure out how to log proper error codes, Ask him why !song isnt working')

        #from JPARKZ
        elif cmd == "rl":
            if cmdargs == []:
                self.post_message(usr + ', Does your carer know you are on the internet right now?')
            else:
                self.post_message(cmdargs[0] + ', Does your carer know you are on the internet right now?')

        elif cmd == 'case':
            self.open_csgo_case(usr)
        
        elif cmd == 'csgostats':
            steam_id = None

            if cmdargs == []:
                self.post_message("!csgostats <category> - Categories are KD, WL, LastMatch, Rifle, Pistol, SMG, Shotgun, Maps, Knife, 1337Boi, Nades, BrassandLead, Bomb")

            else: 
                stats_category = cmdargs[0].lower()
            
                if stats_category == 'kd':
                    try:
                        kills, deaths, timeplayed, kdratio = csgo_stats_kd(steam_id)
                        
                        self.post_message ('Total Kills: ' + kills)
                        self.post_message ('Total Deaths: ' + deaths)
                        self.post_message ('KDR: ' + kdratio)
                        self.post_message ('Time Played: ' + timeplayed + ' hours')

                    except ValueError:
                        self.post_message('API Error - Try changing your steam privacy settings')    

                elif stats_category == 'wl':
                    try:
                        total_matches_won, total_matches_played, total_wins_pistolround, total_rounds_played = csgo_stats_wl(steam_id)

                        self.post_message ('Win/Loss Stats:')
                        self.post_message ('Matches won: ' + total_matches_won)
                        self.post_message ('Matches played: ' + total_matches_played)
                        self.post_message ('Pistol round wins: ' + total_wins_pistolround)
                        self.post_message ('Total rounds played: ' + total_rounds_played)

                    except ValueError:
                        self.post_message('API Error - Try changing your steam privacy settings')
                
                elif stats_category == 'lastmatch':
                    try:
                        lm_kills, lm_deaths, lm_damge, lm_money_spent = csgo_stats_lastmatch(steam_id)

                        self.post_message ('Stats from the last match:')
                        self.post_message ('Kills: ' + lm_kills)
                        self.post_message ('Deaths: ' + lm_deaths)
                        self.post_message ('Damage Dealt: ' + lm_damge)
                        self.post_message ('Money Spent: $' + lm_money_spent)

                    except ValueError:
                        self.post_message('API Error - Try changing your steam privacy settings')

                elif stats_category == 'rifle':
                    try:
                        total_kills_m4a1, total_kills_ak47, total_kills_awp, total_kills_aug, total_kills_sg556 = csgo_stats_rifle(steam_id)

                        self.post_message ('Rifle Kills:')
                        self.post_message ('M4A1: ' + total_kills_m4a1)
                        self.post_message ('AK47: ' + total_kills_ak47)
                        self.post_message ('AWP: ' + total_kills_awp)
                        self.post_message ('AUG: ' + total_kills_aug)
                        self.post_message ('SG556: ' + total_kills_sg556)

                    except ValueError:
                        self.post_message('API Error - Try changing your steam privacy settings')

                elif stats_category == 'pistol':
                    try:
                        total_kills_glock, total_kills_hkp2000, total_kills_deagle, total_kills_fiveseven, total_kills_p250, total_kills_tec9 = csgo_stats_pistol(steam_id)

                        self.post_message ('Pistol Kills:')
                        self.post_message ('Glock: ' + total_kills_glock)
                        self.post_message ('P2000: ' + total_kills_hkp2000)
                        self.post_message ('Desert Eagle: ' + total_kills_deagle)
                        self.post_message ('Five-Seven: ' + total_kills_fiveseven)
                        self.post_message ('P250: ' + total_kills_p250)
                        self.post_message ('Tec 9: ' + total_kills_tec9)

                    except ValueError:
                        self.post_message('API Error - Try changing your steam privacy settings')

                elif stats_category == 'smg':
                    try:
                        total_kills_mac10, total_kills_mp7, total_kills_mp9, total_kills_ump45, total_kills_p90, total_kills_bizon = csgo_stats_smg(steam_id)

                        self.post_message ('SMG Kills:')
                        self.post_message ('Mac 10: ' + total_kills_mac10)
                        self.post_message ('MP7: ' + total_kills_mp7)
                        self.post_message ('MP9: ' + total_kills_mp9)
                        self.post_message ('UMP 45: ' + total_kills_ump45)
                        self.post_message ('P90: ' + total_kills_p90)
                        self.post_message ('PP Bizon: ' + total_kills_bizon)

                    except ValueError:
                        self.post_message('API Error - Try changing your steam privacy settings')            

                elif stats_category == 'shotgun':
                    try:
                        total_kills_xm1014, total_kills_nova, total_kills_sawedoff, total_kills_mag7 = csgo_stats_shotgun(steam_id)

                        self.post_message ('Shotgun Kills:')
                        self.post_message ('XM1014: ' + total_kills_xm1014)
                        self.post_message ('Nova: ' + total_kills_nova)
                        self.post_message ('Sawed Off: ' + total_kills_sawedoff)
                        self.post_message ('Mag7: ' + total_kills_mag7)

                    except ValueError:
                        self.post_message('API Error - Try changing your steam privacy settings')

                elif stats_category == 'maps':
                    try:
                        mapsmsg, total_wins_map_de_dust2, total_wins_map_de_inferno, total_wins_map_de_train, total_wins_map_de_nuke, total_wins_map_de_cbble = csgo_stats_maps(steam_id)

                        self.post_message ('Map Wins:')
                        self.post_message ('Dust 2: ' + total_wins_map_de_dust2)
                        self.post_message ('Inferno: ' + total_wins_map_de_inferno)
                        self.post_message ('Train: ' + total_wins_map_de_train)
                        self.post_message ('Nuke: ' + total_wins_map_de_nuke)
                        self.post_message ('Cobblestone: ' + total_wins_map_de_cbble)
                        self.post_message (mapsmsg)

                    except ValueError:
                        self.post_message('API Error - Try changing your steam privacy settings')

                elif stats_category == 'knife':
                    try:
                        total_kills_knife, total_kills_knife_fight = csgo_stats_knife(steam_id)

                        self.post_message ('Knife Kills: ' + total_kills_knife)
                        self.post_message ('Knife VS Knife Kills: ' + total_kills_knife_fight)

                    except ValueError:
                        self.post_message('API Error - Try changing your steam privacy settings')

                elif stats_category == '1337boi':
                    try:
                        total_broken_windows, total_mvps, total_kills_against_zoomed_sniper, total_weapons_donated, total_kills_enemy_blinded, total_damage_done, total_money_earned, total_kills_headshot, total_kills_enemy_weapon = csgo_stats_1337boi(steam_id)

                        self.post_message ('Broken Windows: ' + total_broken_windows)
                        self.post_message ('MVPs: ' + total_mvps)
                        self.post_message ('Kills VS Zoomed in snipers: ' + total_kills_against_zoomed_sniper)
                        self.post_message ('Donated Weapons: ' + total_weapons_donated)
                        self.post_message ('Kills VS Blind enemies : ' + total_kills_enemy_blinded)
                        self.post_message ('Damage Dealt: ' + total_damage_done)
                        self.post_message ('Career Earnings: $' + total_money_earned)
                        self.post_message ('Headshot kills: ' + total_kills_headshot)
                        self.post_message ('Kills w/ Enemy weapons: ' + total_kills_enemy_weapon)

                    except ValueError:
                        self.post_message('API Error - Try changing your steam privacy settings')

                elif stats_category == 'nades':
                    try:
                        total_kills_hegrenade, total_kills_molotov = csgo_stats_nades(steam_id)

                        self.post_message ('Grenade Kills:')
                        self.post_message ('HE Grenade: ' + total_kills_hegrenade)
                        self.post_message ('Molotov/Incendiary: ' + total_kills_molotov)

                    except ValueError:
                        self.post_message('API Error - Try changing your steam privacy settings')

                elif stats_category == 'brassandlead':
                    try:
                        total_shots_hit, total_shots_fired = csgo_stats_brassandlead(steam_id)

                        self.post_message ('Shots fired:')
                        self.post_message ('Total Shots hit: ' + total_shots_hit)
                        self.post_message ('Total Shots fired: ' + total_shots_fired)

                    except ValueError:
                        self.post_message('API Error - Try changing your steam privacy settings')

                elif stats_category == 'bomb':
                    try:
                        total_planted_bombs, total_defused_bombs = csgo_stats_bomb(steam_id)

                        self.post_message ('C4 Planted: ' + total_planted_bombs)
                        self.post_message ('C4 Defused: ' + total_defused_bombs)

                    except ValueError:
                        self.post_message('API Error - Try changing your steam privacy settings')

                else:
                    pass    
        
        elif cmd == 'stats':
            viewers, subcount, views, followers = self.get_channel_stats(self.channel_id)
            self.post_message(str(viewers) + ' Viewers')
            self.post_message(str(followers) + ' Followers')
            self.post_message(str(subcount) + ' Subscribers')
            self.post_message(str(views) + ' Channel Views')

        elif cmd == 'debug':
            self.is_channel_live(self.channel_id)

        else:
            print ('Ignored Command: ' + cmd)

    def do_mod_command(self, e, cmd, cmdargs, usr):
        global chat_db
        cmdargs = cmdargs
        
        if cmd == "addcom":
            self.add_command(chat_db, cmdargs)

        elif cmd == "delcom":
            self.delete_command(chat_db, cmdargs)

        elif cmd == "title":
            self.set_stream_title(cmdargs)
            
        elif cmd == "game":
            self.set_stream_game(cmdargs)

        elif cmd in ['caster','shoutout', 'streamer', 'so' ]:
            url_base = 'https://www.twitch.tv/'
            caster = cmdargs[0]
            caster_id = self.get_channel_id(caster)
            
            channels_url = 'https://api.twitch.tv/kraken/channels/' + caster_id
            headers = {'Client-ID': self.client_id, 'Accept': 'application/vnd.twitchtv.v5+json'}
            r = requests.get(channels_url, headers=headers).json()

            self.post_message('You should checkout ' +  caster +  ' over at their channel - ' + url_base + caster.lower() + " - Don't forget to drop them a follow!" )
            sleep (2)
            if r['game'] != None:
                self.post_message(caster + ' was last playing ' + r['game'])
            else:
                pass

        elif cmd == "clear":
            self.post_message('/clear')

        else:
            print ('Ignored Mod Command: ' + cmd)

    def add_command(self, chat_db, cmdargs):
        con = sqlite3.connect(chat_db)
        cursor = con.cursor()
        parsedcom = " ".join(map(str, cmdargs[1:]))
        print (parsedcom)
        sql ="""
            INSERT INTO chat_commands (command, command_result) 
            VALUES (?, ?)"""
        cursor.execute(sql, (cmdargs[0].lower(), parsedcom))
        con.commit()
        con.close()
        self.post_message ('New command created: !' + cmdargs[0])
        print ('New command created: !' + cmdargs[0])

    def delete_command(self, chat_db, cmdargs):
        con = sqlite3.connect(chat_db)
        cursor = con.cursor()
        sql = "DELETE FROM chat_commands WHERE command = ?"
        cmdname = cmdargs[0].lower()
        cursor.execute(sql, [cmdname])
        con.commit()
        con.close()
        self.post_message ('Command deleted: !' + cmdargs[0])       

    def set_stream_title(self, cmdargs):                          
        channel_token = self.get_twitch_token(channel)
        new_title = " ".join(map(str, cmdargs))
        url = 'https://api.twitch.tv/kraken/channels/' + self.channel_id
        title_headers = {'Client-ID': self.client_id, 'Accept': 'application/vnd.twitchtv.v5+json', 'Authorization': 'OAuth '+ channel_token, 'Content-Type': 'application/json'}
        body_data = {'channel': {'status': new_title}}
        title_payload = json.dumps(body_data)
        r = requests.put(url, data=title_payload, headers=title_headers)

    def set_stream_game(self, cmdargs):
        channel_token = self.get_twitch_token(channel)
        new_game = " ".join(map(str, cmdargs))
        print (new_game)
        url = 'https://api.twitch.tv/kraken/channels/' + self.channel_id
        title_headers = {'Client-ID': self.client_id, 'Accept': 'application/vnd.twitchtv.v5+json', 'Authorization': 'OAuth '+ channel_token, 'Content-Type': 'application/json'}
        body_data = {'channel': {'game': new_game}}
        title_payload = json.dumps(body_data)
        r = requests.put(url, data=title_payload, headers=title_headers)

    def get_channel_subcount(self):
        channel_token = self.get_twitch_token(channel)
        url = 'https://api.twitch.tv/kraken/channels/' + self.channel_id + '/subscriptions'
        headers = {'Client-ID': self.client_id, 'Accept': 'application/vnd.twitchtv.v5+json', 'Authorization': 'OAuth '+ channel_token, 'Content-Type': 'application/json'}
        r = requests.get(url, headers=headers).json()
        return r["_total"]
        
    def open_csgo_case(self, usr):
        #See Wiki
        #Total 376
        con = sqlite3.connect(csgo_case_db)
        cursor = con.cursor()
        cursor.execute("SELECT last_case_time FROM last_case WHERE display_name = ?", [usr])
        raw_user_last_case_time = cursor.fetchall()
  
        if raw_user_last_case_time == []:
            Local_user_last_case_time = datetime.datetime.now() - datetime.timedelta(hours=6)
        
        #users with unlimited cases
        elif usr in ['rephl3x','phl3xbot']:
            Local_user_last_case_time = datetime.datetime.now() - datetime.timedelta(hours=6)  

        else:    
            Local_user_last_case_time = datetime.datetime.strptime(raw_user_last_case_time[0][0], '%Y-%m-%d %H:%M:%S.%f')

        if not Local_user_last_case_time <= (datetime.datetime.now() - datetime.timedelta(minutes=29)):
                
                time_diff = datetime.datetime.now() - Local_user_last_case_time
                minute_diff = time_diff.seconds / 60
                
                self.post_message ('You only get one case every 30 minutes my dude rephl3Xwhut  (last case was ' + str(math.floor(minute_diff)) + ' minutes ago)' )                
        
        else:
            twitch_colours = {"yellow" : "goldenrod", "red" : "red", "pink" : "hotpink", "purple" : "blueviolet", "blue" : "blue", }
            item_wear = random.choice(wear)
            x_stattrak = random.randint(1, 10)
            if  x_stattrak == 10:
                item_stattrak = stattrak[0]
            else:
                item_stattrak = None    
            
            cheats = []
            
            if usr in cheats:
                x_item = random.randint(1, 376)
            else:
                x_item = random.randint(1, 376)
    
            if 1 <= x_item <= 300:
                c = 'blue'
            elif 301 <= x_item <= 360:
                c = 'purple'
            elif 361 <= x_item <= 372:
                c = 'pink'
            elif 373 <= x_item <= 375:
                c = 'red'
            else:
                c = 'yellow'           

            if c == 'yellow':
                case = random.choice(list(cases))
                item = random.choice(knives)
                item_skin = random.choice(knife_skins)

                if item_stattrak != None:
                    final_item = item_stattrak + ' ' + item_wear + ' ' + item_skin + ' ' + item
                else:
                    final_item = item_wear + ' ' + ' ' + item_skin + ' ' + item
            
            #Exceedingly Rare Special Item!
                self.post_message ('/color ' + twitch_colours[c] )
                self.post_message ('/me @' + usr + ', You just pulled an Exceedingly Rare Special Item!')
                sleep(2)
                self.post_message ('/me You got a ' + final_item + ' from a ' + case + ' Case')
                self.post_message ('/color green')
            
            else:
                case = random.choice(list(cases))
                item = random.choice(cases[case][c])

                if item_stattrak != None:
                    final_item = item_stattrak + ' ' + item_wear + ' ' + item
                else:
                    final_item = item_wear + ' ' + item
            
                self.post_message ('/color ' + twitch_colours[c] )
                self.post_message ('/me @' + usr + ', You just pulled a ' + final_item + ' from a ' + case + ' Case')
                self.post_message ('/color green')

            case_time = datetime.datetime.now()
            con = sqlite3.connect(csgo_case_db)
            cursor = con.cursor()
            sql = "DELETE FROM last_case WHERE display_name = ?"
            cursor.execute(sql, [usr])
            con.commit()
            sql ="""INSERT INTO last_case (display_name, last_case_time) 
                    VALUES (?, ?)"""
            cursor.execute(sql, (usr, case_time))
            con.commit()
            con.close()
            
def MessageScheduler(Phl3xBot):
    while True:
        if Phl3xBot.is_channel_live(Phl3xBot.channel_id) == 'live':
            db_msgs = {}
            messages = ['snapchat','youtube','twitter','discord','website']
            
            for msg in messages:
                con = sqlite3.connect(chat_db)
                cursor = con.cursor()
                cursor.execute("SELECT command_result FROM chat_commands WHERE command = ?", [msg])
                temp = cursor.fetchone()
                db_msgs[msg] = temp[0]
                cursor.close()  

            time.sleep(450)
            Phl3xBot.post_message(db_msgs.pop('website'))
            print('Messange sent: Website')
            time.sleep(450)
            Phl3xBot.open_csgo_case('Phl3xBot')
            Phl3xBot.post_message("You can open CS:GO cases too. Type '!case' in chat.")
            time.sleep(450)
            Phl3xBot.post_message(db_msgs.pop('snapchat'))
            print('Messange sent: Snapchat')
            time.sleep(900)
            Phl3xBot.post_message(db_msgs.pop('youtube'))
            print('Messange sent: youtube')
            time.sleep(900)
            Phl3xBot.post_message(db_msgs.pop('twitter'))
            print('Messange sent: twitter')
            time.sleep(900)
            Phl3xBot.post_message(db_msgs.pop('discord'))
            print('Messange sent: discord')
            time.sleep(450)
        else:
            sleep (5)
            print ('Channel Offline - ' + str(datetime.datetime.now()))
            sleep (900)
            

def main():

    Phl3xBot = ListenerBot(username, clientid, channel)
    Phl3xBotThread = Thread(target=Phl3xBot)
    Phl3xBotThread.start()

    MessageScheduler(Phl3xBot)    

if __name__ == "__main__":
    main()
