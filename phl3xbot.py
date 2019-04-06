import os
import sys
import irc.client
import irc.bot
import requests
import sqlite3
import time
from time import sleep
from threading import Thread
#from termcolor import colored

chat_db = os.path.join(os.path.dirname(__file__), 'chat_commands.db')

class NewListenerBot(irc.client.SimpleIRCClient):
    def testNLB(self):
        print('Debug testNLB')     

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
        #print (e.'user-type'.[0])
        print (e.source + ' - ' + e.arguments[0])

        if e.arguments[0][:1] == '!':
            cmd = e.arguments[0].lower().split(' ')[0][1:]
            cmdargs = []
            cmdargs = e.arguments[0].split(' ')[1:]
            usr = e.tags[3]['value']
            print ('Received command: ' + cmd)
            self.do_user_command(e, cmd, cmdargs, usr)

        elif e.arguments[0][:1] == '#':
            if True:
                cmd = e.arguments[0].lower().split(' ')[0][1:]
                cmdargs = e.arguments[0].split(' ')[1:]
                print (cmdargs)
                usr = e.tags[3]['value']
                print ('Received Mod command: ' + cmd)
                self.do_mod_command(e, cmd, cmdargs, usr)    
            else:
                pass

        elif e.arguments[0].lower().split(' ')[0] in ['kappa', 'kappapride', 'gachibass']:
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
        ### ChatCommands ###
        con = sqlite3.connect(chat_db)
        cursor = con.cursor()
        cursor.execute("SELECT command_result FROM chat_commands WHERE command = ?", [cmd])
        sqlcmd = cursor.fetchall()
        #print (sqlcmd)
        cursor.close()
        
        if sqlcmd:
            c.privmsg(self.channel, sqlcmd[0][0])

        ### Advanced/Logic Chat Commands ###
        elif cmd == "bestfollower":
            if usr == "FakieNZ":
                c.privmsg(self.channel, usr)
            else:
                c.privmsg(self.channel, 'not ' + usr)
   
        ### API Commands ###
        #TWITCH-API-GAME
        elif cmd == "game":
            url = 'https://api.twitch.tv/kraken/channels/' + self.channel_id
            headers = {'Client-ID': self.client_id, 'Accept': 'application/vnd.twitchtv.v5+json'}
            r = requests.get(url, headers=headers).json()
            c.privmsg(self.channel, 'Ya boi ' + r['display_name'] + ' is currently playing ' + r['game'])

        #TWITCH-API-UPTIME
        elif cmd == "uptime":
            url = 'https://api.twitch.tv/kraken/streams/' + self.channel_id
            headers = {'Client-ID': self.client_id, 'Accept': 'application/vnd.twitchtv.v5+json'}
            r = requests.get(url, headers=headers).json()
            print (r['stream'])
            if r['stream'] == None:
                c.privmsg(self.channel, 'Ya boi is busy doing other shit')
            else:
                c.privmsg(self.channel, r['stream']['created_at'])    

        #SpotifyAPI-CurrentSong    #EXPIRED TOKEN!!!!!
        elif cmd == "song":
            url = 'https://api.spotify.com/v1/me/player/currently-playing'          
            headers = {'Accept': 'application/json', 'Content-Type': 'application/json', 'Authorization': 'Bearer BQCQ8A-qSf-1dTtX2wjlPb9o4_g-xtxxX1vcewdV46Vvpu3m5BHTHe9CIU0I33S4WKCWLHe0dfIi28LOUC0VjEWH2zJHsmYcztcgaTs_DaVw1os-jbFF8lNYTLZOJNeh8DpbqbCeanPGXrO4hQEPh4QXsL8'}
            song = requests.get(url, headers=headers).json()
            c.privmsg(self.channel, 'Ya boi FakieNZ is currently playing ' + song['item']['name'] + ' from ' + song['item']['album']['name'])

        #TWITCH-API-TITLE
        elif cmd == "title":
            url = 'https://api.twitch.tv/kraken/channels/' + self.channel_id
            headers = {'Client-ID': self.client_id, 'Accept': 'application/vnd.twitchtv.v5+json'}
            r = requests.get(url, headers=headers).json()
            c.privmsg(self.channel, r['status'])

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

    Phl3xSchedThread = Thread(target=MessageScheduler(Phl3xBot))
    Phl3xSchedThread.start() 

if __name__ == "__main__":
    main()
