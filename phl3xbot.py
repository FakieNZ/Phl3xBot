# https://StreamElements.com/rephl3x/commands
# https://beta.nightbot.tv/t/rephl3x/commands
import sys
import irc.bot
import requests
import time
from time import sleep
import schedule
from schedule import default_scheduler
from threading import Thread 

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

    def __call__(self):
        self.start()

    def on_welcome(self, c, e):
        print ('Joining ' + self.channel)
        c.cap('REQ', ':twitch.tv/membership')
        c.cap('REQ', ':twitch.tv/tags')
        c.cap('REQ', ':twitch.tv/commands')
        c.join(self.channel)
        time.sleep(3)
        #c.privmsg(self.channel, 'has entered the game')
        #Bot doesnt work until this func finishes running.             

    def on_pubmsg(self, c, e):
        if e.arguments[0][:1] == '!':
            cmd = e.arguments[0].split(' ')[0][1:]
            print ('Received command: ' + cmd)
            self.do_command(e, cmd)
        return

    def do_command(self, e, cmd):
        c = self.connection               

        ################ Moderator Commands ################
        #TWITCH-MOD-CLEAR
        if cmd == "clear":
            c.privmsg(self.channel, '/clear')
            
        ################ API Commands ################
        #TWITCH-API-GAME
        elif cmd == "game":
            url = 'https://api.twitch.tv/kraken/channels/' + self.channel_id
            headers = {'Client-ID': self.client_id, 'Accept': 'application/vnd.twitchtv.v5+json'}
            r = requests.get(url, headers=headers).json()
            c.privmsg(self.channel, 'Ya boi ' + r['display_name'] + ' is currently playing ' + r['game'])

        #SpotifyAPI-CurrentSong    #EXPIRED TOKEN!!!!!
        elif cmd == "song":

            url = 'https://api.spotify.com/v1/me/player/currently-playing'          
            headers = {'Accept': 'application/json', 'Content-Type': 'application/json', 'Authorization': 'Bearer BQBzv03gh15mqjfE83mYPjQdNYkLqMzn0nQe0REFio-nZxKGkb3SFqi06xDdxsRKjBigbu5H97qSEaP6RLLh04jMTc-jcF5pVOb-emNZ6LlmIhP1SAGcUUiF9MX3IInEqI-XcHLTFMBSJlO5j4dRX1bMCqLdBQ'}
            song = requests.get(url, headers=headers).json()

            c.privmsg(self.channel, 'Ya boi FakieNZ is currently playing ' + song['item']['name'] + ' from ' + song['item']['album']['name'])

        #TWITCH-API-TITLE
        elif cmd == "title":
            url = 'https://api.twitch.tv/kraken/channels/' + self.channel_id
            headers = {'Client-ID': self.client_id, 'Accept': 'application/vnd.twitchtv.v5+json'}
            r = requests.get(url, headers=headers).json()
            c.privmsg(self.channel, r['status'])   

        ################ CHAT COMMANDS #################
        #TWITCH-CHAT-BAPPO
        elif cmd == "bappo":
            c.privmsg(self.channel, 'Nuked the Jappos')

        #TWITCH-CHAT-JNZL
        elif cmd == "jnzl":
            c.privmsg(self.channel, '@jnzl is a cuda')

        #XNB-TWITCH-CHAT-FAKIE
        elif cmd == "fakie":
            c.privmsg(self.channel, 'https://clips.twitch.tv/CoyGorgeousCrowSaltBae')

        ################ Logic Commands ################
        #Ignore !Play
        elif cmd == "play": print ('Ignored Command: ' + cmd)

        # The command was not recognized
        else: print ('Ignored Command: ' + cmd)

    def post_message(self, message):
        c = self.connection
        c.privmsg(self.channel, message)

class MessageScheduler(irc.schedule.DefaultScheduler):
    def __init__(self):
        print ('Phl3xSched Initialised')

    def __call__(self, Phl3xBot):
        time.sleep(10)
        snapchat = 'My Snapchat is d1g1talis, Feel free to add me and send me lots of things (incl balls)'
        Phl3xBot.post_message(snapchat)
        print(snapchat)


def main():
    if len(sys.argv) != 5:
        print("Usage: Phl3xBot <username> <client id> <token> <channel>")
        sys.exit(1)

    username  = sys.argv[1]
    client_id = sys.argv[2]
    token     = sys.argv[3]
    channel   = sys.argv[4]

    Phl3xBot = ListenerBot(username, client_id, token, channel)
    Phl3xBotThread = Thread(target = Phl3xBot)
    Phl3xBotThread.start()
    
    Phl3xSched = MessageScheduler()
    Phl3xSchedThread = Thread(target = Phl3xSched(Phl3xBot))
    Phl3xSchedThread.start()

if __name__ == "__main__":
    main()
