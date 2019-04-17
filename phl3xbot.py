import os
import sys
import irc.client
import irc.bot
import requests
import sqlite3
import time
import datetime
from time import sleep
from threading import Thread
import json
from mock import mock


chat_db = os.path.join(os.path.dirname(__file__), 'chat_commands.db')
token_db = os.path.join(os.path.dirname(__file__), 'spotify_tokens.db')
chat_log_db = os.path.join(os.path.dirname(__file__), 'chat_log.db')
username = 'postmaster-nz'  

class ListenerBot(irc.bot.SingleServerIRCBot):
    def __init__(self, username, client_id, token, channel):
        global chat_db
        global token_db
        global chat_log_db
        
        self.client_id = client_id
        self.token = token
        self.channel = '#' + channel
        url = 'https://api.twitch.tv/kraken/users?login=' + channel 
        headers = {'Client-ID': client_id, 'Accept': 'application/vnd.twitchtv.v5+json'}
        r = requests.get(url, headers=headers).json()
        self.channel_id = r['users'][0]['_id']
        server = 'irc.chat.twitch.tv'
        port = 6667
        print ('Connecting to ' + server + ' on port ' + str(port) + '...')
        irc.bot.SingleServerIRCBot.__init__(self, [(server, port, 'oauth:'+token)], username, username)

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
    
    def post_message(self, message):
        c = self.connection
        c.privmsg(self.channel, message)
    
    def get_channel_id(self, username):
        url = 'https://api.twitch.tv/kraken/users?login=' + username 
        headers = {'Client-ID': self.client_id, 'Accept': 'application/vnd.twitchtv.v5+json'}
        r = requests.get(url, headers=headers).json()
        caster_id = r['users'][0]['_id']
        return caster_id

    def on_welcome(self, c, e):
        print ('Joining ' + self.channel)
        c.cap('REQ', ':twitch.tv/membership')
        c.cap('REQ', ':twitch.tv/tags')
        c.cap('REQ', ':twitch.tv/commands')
        c.join(self.channel)
        time.sleep(3)
        c.privmsg(self.channel, '/color Green')            

    def on_pubmsg(self, c, e):
        global chat_db
        self.log_message(e)
        print (e.source + ' - ' + e.arguments[0])

        if e.tags[3]['value'] in ['Nightbot', 'jnzl']:
            msg = 'hi im ' + e.tags[3]['value'] + ' and ' + e.arguments[0].lower()
            mocked_msg = mock(msg)
            self.post_message(mocked_msg)
        
        elif e.arguments[0][:1] == '!':
            cmd = e.arguments[0].lower().split(' ')[0][1:]
            cmdargs = []
            cmdargs = e.arguments[0].split(' ')[1:]
            usr = e.tags[3]['value']
            print ('Received command: ' + cmd)
            self.do_user_command(e, cmd, cmdargs, usr)

        elif e.arguments[0][:1] == '#':
            if e.tags[7]['value'] == 1 or e.tags[13]['value'] == 'mod' :
                cmd = e.arguments[0].lower().split(' ')[0][1:]
                cmdargs = e.arguments[0].split(' ')[1:]
                print (cmdargs)
                usr = e.tags[3]['value']
                print ('Received Mod command: ' + cmd)
                self.do_mod_command(e, cmd, cmdargs, usr)    
            else:
                print ('Ignored Mod command from a user')
                self.post_message('/me #Locals Only, Bro. No Kooks!') 
                sleep(2)
                self.post_message("Commands with '#' are for Mods, Have a siick vid instead - https://www.youtube.com/watch?v=PK28Kaj-X-4")
                

        elif e.arguments[0].lower().split(' ')[0] in ['rephl3xwhut','kappa','kappapride','gachibass']:
            cmd = e.arguments[0].lower().split(' ')[0]
            cmdargs = []
            cmdargs = e.arguments[0].split(' ')[1:]
            usr = e.tags[3]['value']
            print ('Received "other" command: ' + cmd)
            self.do_user_command(e, cmd, cmdargs, usr)

        else:
            pass   

    def do_user_command(self, e, cmd, cmdargs, usr):
        global chat_db
        c = self.connection
        con = sqlite3.connect(chat_db)
        cursor = con.cursor()
        cursor.execute("SELECT command_result FROM chat_commands WHERE command = ?", [cmd])
        sqlcmd = cursor.fetchall()
        cursor.close()
        
        if sqlcmd:
            c.privmsg(self.channel, sqlcmd[0][0])

        ### Advanced/Logic Chat Commands ###
        elif cmd in ['bot','phl3xbot', 'nightbot']:
            self.post_message("I was forced to read 10,000 of Rephl3x's tweets and now i'm much better than nightbot - https://www.youtube.com/watch?v=OWwOJlOI1nU")
            self.post_message('/me Wiki: https://bit.ly/2uP3lrB')
            self.post_message('/me Commands: https://bit.ly/2U0mh0P')
            self.post_message('/me Support: Send a whisper to FakieNZ')

        elif cmd == "bestfollower":
            if usr == "FakieNZ":
                c.privmsg(self.channel, usr)
            else:
                c.privmsg(self.channel, 'not ' + usr)

        elif cmd == 'rr':
            c.privmsg(self.channel, 'How many cowboys?')
            sleep(3)
            c.privmsg(self.channel, '18')
        
        elif cmd == 'lmgtfy':
            if cmdargs != None:
                g_prefix = 'https://www.google.com/search?q='
                g_suffix = " ".join(map(str, cmdargs))
                g_suffix = g_suffix.replace(' ','+')
                c.privmsg(self.channel, g_prefix + g_suffix)
            else:
                pass

        #TWITCH-API-GAME
        elif cmd == "game":
            url = 'https://api.twitch.tv/kraken/channels/' + self.channel_id
            headers = {'Client-ID': self.client_id, 'Accept': 'application/vnd.twitchtv.v5+json'}
            r = requests.get(url, headers=headers).json()
            c.privmsg(self.channel, 'Ya boi ' + r['display_name'] + ' is currently playing ' + r['game'])

        #TWITCH-API-TITLE
        elif cmd == "title":
            url = 'https://api.twitch.tv/kraken/channels/' + self.channel_id
            headers = {'Client-ID': self.client_id, 'Accept': 'application/vnd.twitchtv.v5+json'}
            r = requests.get(url, headers=headers).json()
            c.privmsg(self.channel, r['status'])

        #TWITCH-API-UPTIME
        elif cmd == "uptime":
            url = 'https://api.twitch.tv/kraken/streams/' + self.channel_id
            headers = {'Client-ID': self.client_id, 'Accept': 'application/vnd.twitchtv.v5+json'}
            r = requests.get(url, headers=headers).json()
            print (r['stream'])
            if r['stream'] == None:
                c.privmsg(self.channel, 'Ya boi is busy doing other shit')
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
            
                c.privmsg(self.channel, 'Streaming since ' + str(Local_stream_started_at_timeobject) + ' NZ Time')
                c.privmsg(self.channel, 'Ya boi has been live for ' + stream_uptime_hours + ' hours ' + stream_uptime_minutes + ' minutes (or at least time since the last internet flap LUL)')

        #SpotifyAPI-CurrentSong
        elif cmd == "song":
            conection = sqlite3.connect(token_db)
            cursor = conection.cursor()
            load_sql = "SELECT access_token,refresh_token FROM spotify_token WHERE username = ?"
            cursor.execute(load_sql, [username])
            token_data = cursor.fetchone()
            conection.close()
            access_token = token_data[0]
            access_token = str('Bearer ' + access_token)             
            
            url = 'https://api.spotify.com/v1/me/player/currently-playing'          
            headers = {'Accept': 'application/json', 'Content-Type': 'application/json', 'Authorization': access_token}
            song = requests.get(url, headers=headers).json()

            if 'error' in song:
                self.post_message('Spotify API Error: ' + str(song['error']['status']) + ' - ' + song['error']['message'])
            elif song['is_playing'] != True:
                c.privmsg(self.channel, 'Ya boi aint got nothing playing on Spotify')
            elif song['item']:    
                c.privmsg(self.channel, 'Ya boi is currently playing ' + song['item']['name'] + ' by ' + song['item']['artists'][0]['name'] + ' from the album ' + song['item']['album']['name'])
            else:
                pass

        else:
            print ('Ignored Command: ' + cmd)

    def do_mod_command(self, e, cmd, cmdargs, usr):
        global chat_db
        cmdargs = cmdargs

        if cmd == "addcom":
            self.add_command(chat_db, cmdargs)

        elif cmd == "delcom":
            self.delete_command(chat_db, cmdargs)

        #elif cmd == "title":
            #self.set_stream_title(cmdargs)
            
        #elif cmd == "game":
            #self.set_stream_game(cmdargs)

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
        
        #BadAuth - OAUTH TOKENS are missing required Scope
        new_title = " ".join(map(str, cmdargs))
        url = 'https://api.twitch.tv/kraken/channels/' + self.channel_id
        title_headers = {'Client-ID': self.client_id, 'Accept': 'application/vnd.twitchtv.v5+json', 'Authorization': 'OAuth '+ self.token, 'Content-Type': 'application/json'}
        body_data = {'channel': {'status': new_title}}
        title_payload = json.dumps(body_data)
        r = requests.put(url, data=title_payload, headers=title_headers)

        print (title_headers)
        print (title_payload)
        print (r)

    def set_stream_game(self, cmdargs):
        pass # pending on set_stream_title and resolves AUTH issues.
        

def MessageScheduler(Phl3xBot):
    while True:
        db_msgs = {}
        messages = ['snapchat','youtube','twitter','discord']
        
        for msg in messages:
            con = sqlite3.connect(chat_db)
            cursor = con.cursor()
            cursor.execute("SELECT command_result FROM chat_commands WHERE command = ?", [msg])
            temp = cursor.fetchone()
            db_msgs[msg] = temp[0]
            cursor.close()  

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

def main():
    if len(sys.argv) != 5:
        print("Usage: Phl3xBot <username> <client id> <token> <channel>")
        sys.exit(1)

    username  = sys.argv[1]
    client_id = sys.argv[2]
    token     = sys.argv[3]
    channel   = sys.argv[4]
    
    Phl3xBot = ListenerBot(username, client_id, token, channel)
    Phl3xBotThread = Thread(target=Phl3xBot)
    Phl3xBotThread.start()

    MessageScheduler(Phl3xBot)    

if __name__ == "__main__":
    main()
