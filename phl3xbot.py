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


chat_db = os.path.join(os.path.dirname(__file__), 'chat_commands.db')
token_db = os.path.join(os.path.dirname(__file__), 'spotify_tokens.db')
username = 'postmaster-nz'  

class ListenerBot(irc.bot.SingleServerIRCBot):
    def __init__(self, username, client_id, token, channel):
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

        global chat_db

    def __call__(self):
        self.start()
                    
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
        print (e.source + ' - ' + e.arguments[0])

        if e.arguments[0][:1] == '!':
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

    def do_mod_command(self, e, cmd, cmdargs, usr):
        global chat_db
        cmdargs = cmdargs

        if cmd == "addcom":
            self.add_command(chat_db, cmdargs)

        elif cmd == "delcom":
            self.delete_command(chat_db, cmdargs)

        elif cmd == "caster":
            url_base = 'https://www.twitch.tv/'
            caster = cmdargs[0]
            self.post_message('You should checkout ' +  caster +  ' over at their channel - ' + url_base + caster.lower() + " - Don't forget to drop them a follow!" )

        elif cmd == "clear":
            self.post_message('/clear')
        else:
            print ('Ignored Mod Command: ' + cmd)

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
                g_postfix = " ".join(map(str, cmdargs))
                g_postfix = g_postfix.replace(' ','+')
                c.privmsg(self.channel, g_prefix + g_postfix)
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
                raw_stream_started_at = r['stream']['created_at'] #2019-04-07T03:42:54Z 
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

    def post_message(self, message):
        c = self.connection
        c.privmsg(self.channel, message)

    def test(self):
        print('Debug: Test()')

def MessageScheduler(Phl3xBot):
    print ('Debug: MessageScheduler')
    while True:
        time.sleep(900)
                
        snapchat = 'My Snapchat is d1g1talis, Feel free to add me and send me lots of things (incl balls)'
        Phl3xBot.post_message(snapchat)
        print('Messange sent: Snapchat')
        time.sleep(1800)

        youtube = 'Hey guys and gals, You can check out my youtube here https://www.youtube.com/channel/UC5-HRk8fW590P9bldGN9M8g'
        print('Messange sent: Youtube')
        Phl3xBot.post_message(youtube)

        time.sleep(900)

def maintest():
    print('Debug: maintest()')

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
    #Phl3xSchedThread = Thread(target=MessageScheduler(Phl3xBot))
    #Phl3xSchedThread.start()

if __name__ == "__main__":
    main()
