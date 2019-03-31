import sys
import irc.bot
import requests
import time
from time import sleep
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
        try:
            self.start()
        except KeyboardInterrupt:
            sys.exit(1)            

    def on_welcome(self, c, e):
        print ('Joining ' + self.channel)
        c.cap('REQ', ':twitch.tv/membership')
        c.cap('REQ', ':twitch.tv/tags')
        c.cap('REQ', ':twitch.tv/commands')
        c.join(self.channel)
        time.sleep(3)
        #c.privmsg(self.channel, 'has entered the game')            

    def on_pubmsg(self, c, e):
        if e.arguments[0][:1] == '!':
            rawcmd = e.arguments[0].split(' ')[0][1:]
            cmd = rawcmd.lower()
            print ('Received command: ' + cmd)
            self.do_command(e, cmd)
        return

    def do_command(self, e, cmd):
        c = self.connection
        ### ChatCommands ###
        chatcommands = {
            "1bitty" :	"https://clips.twitch.tv/RockyCaringSandwichDoritosChip",
            "beast" :	"WHO UNLEASHED THE BEAST https://clips.twitch.tv/ScrumptiousGenerousSproutThisIsSparta",
            "bappo" :	"Nuked the Jappos",
            "chicken" : "BOk BOOOOCKKK https://clips.twitch.tv/TenderTrappedArmadilloSeemsGood",
            "community" :	"Hey guys, check out my community at https://www.twitch.tv/communities/grizzly_gaming if you are a streamer then feel free to join and we can share the love!",
            "discord" :	"Join my Discord https://discord.gg/m99pF3U",
            "drop" :	"FEEL THE SPIRIT, WHERES THE DROP https://clips.twitch.tv/BigWealthyVampireHassaanChop",
            "facebook"	: "Please take the time to follow me on https://www.facebook.com/Rephl3xGaming/ For updates about my life and my weekly Schedule! Cheers!",
            "fakie"	: "https://clips.twitch.tv/CoyGorgeousCrowSaltBae",
            "feet" : "bigboifootfetish : Good Afternoon Good Sir, Could I please ask you a favour, I really love big boi feet and I would like you to send me a few photos of your feet, the top and the bottom, I would pay $150 USD per photo and you don't have to include face or anything, Please help me in my quench for big boy feet pics. Thank you.",
            "fortnite" :	"https://clips.twitch.tv/TangentialBoxyRuffArsonNoSexy",
            "highlight" :	"Check out some of my highlights from my stream so far in 2018 https://www.youtube.com/watch?v=7-upKlfOoFY",
            "horse" :	"https://clips.twitch.tv/OpenHappyHornetMcaT",
            "jet" : "jet402: Orange chocolate chip ice cream can suck my ass",
            "jparkzzz" : "https://clips.twitch.tv/TallBoxySwordSMOrc",
            "lobsterfest": "https://clips.twitch.tv/NimbleGiantMouseRlyTho",
            "mateo" :	"BIG DICK BASTARD",
            "merch" :	"Hey guys, to buy some merch check out this link https://streamlabs.com/rephl3xgaming/#/merch",
            "mvp": "https://clips.twitch.tv/BenevolentObliqueVanillaANELE",
            "necmuso" : "I just got home from work, I'm tired and horny. I'm about to go and stuff a Cucumber up my ass to fix this",
            "plate" :	"So this is what happens when a grown ass man smashes a plate on his head when streaming https://clips.twitch.tv/ImpossibleAlertCucumberDancingBanana",
            "prime" :	"Hi there, do you happen to have amazon prime? Well, if that be so, you can subscribe to our friend Rephl3x",
            "rephl3x" : "MY NAMES Rephl3x Jebaited IM A BAITER Jebaited ILL SEE YOU AT THE BOMB SITE Jebaited A LITTLE LATER Jebaited",
            "roadkill"	: "https://clips.twitch.tv/LitigiousCarelessMeatloafDogFace",
            "rofl" :	"LUL Jebaited",
            "scare" :	"Ever seen a grown man be reduced to tears https://clips.twitch.tv/PolishedAmusedMoonVoteYea",
            "snapchat" : "My Snapchat is d1g1talis, Feel free to add me and send me lots of things(incl balls)",
            "spaghet" : "Very few can resist the temptation of a warm plate of Spaghet... nor can you. You settle down, ready to sink your hands into that stringy goodness, but there's a problem: That's not your Spaghet. This isn't even your house, and the current residents don't appreciate having their food slapped around.",
            "squeeky" : "https://clips.twitch.tv/EncouragingDistinctDaikonBloodTrail",
            "steam" : "You can find Rephl3x's steam profile here https://steamcommunity.com/id/Rephl3x",
            "venmo" : "To sign up for Rephl3x's Premium Snapchat (New feet pic's every week!) send $150 USD to https://venmo.com/Rephl3xGaming",
            "youtube" : "Hey guys and gals, You can check out my youtube here https://www.youtube.com/channel/UC5-HRk8fW590P9bldGN9M8g",
            "kappa" : "Kappa Kappa Kappa Kappa Kappa",
            "kappapride" :	"KappaPride KappaPride KappaPride KappaPride KappaPride",
            "gachibass" :	"gachiBASS gachiBASS gachiBASS gachiBASS gachiBASS"
        }

        if cmd in chatcommands:
            c.privmsg(self.channel, chatcommands.get(cmd))

        ### Moderator Commands ###
        #TWITCH-MOD-CLEAR
        elif cmd == "clear":
            pass
            #c.privmsg(self.channel, '/clear')
            
        ### API Commands ###
        #TWITCH-API-GAME
        elif cmd == "game":
            url = 'https://api.twitch.tv/kraken/channels/' + self.channel_id
            headers = {'Client-ID': self.client_id, 'Accept': 'application/vnd.twitchtv.v5+json'}
            r = requests.get(url, headers=headers).json()
            c.privmsg(self.channel, 'Ya boi ' + r['display_name'] + ' is currently playing ' + r['game'])

        #SpotifyAPI-CurrentSong    #EXPIRED TOKEN!!!!!
        #elif cmd == "song":
            #url = 'https://api.spotify.com/v1/me/player/currently-playing'          
            #headers = {'Accept': 'application/json', 'Content-Type': 'application/json', 'Authorization': 'Bearer BQBzv03gh15mqjfE83mYPjQdNYkLqMzn0nQe0REFio-nZxKGkb3SFqi06xDdxsRKjBigbu5H97qSEaP6RLLh04jMTc-jcF5pVOb-emNZ6LlmIhP1SAGcUUiF9MX3IInEqI-XcHLTFMBSJlO5j4dRX1bMCqLdBQ'}
            #song = requests.get(url, headers=headers).json()

            #c.privmsg(self.channel, 'Ya boi FakieNZ is currently playing ' + song['item']['name'] + ' from ' + song['item']['album']['name'])

        #TWITCH-API-TITLE
        elif cmd == "title":
            url = 'https://api.twitch.tv/kraken/channels/' + self.channel_id
            headers = {'Client-ID': self.client_id, 'Accept': 'application/vnd.twitchtv.v5+json'}
            r = requests.get(url, headers=headers).json()
            c.privmsg(self.channel, r['status'])

        ### Logic Commands ###
        #Ignore !Play
        elif cmd == "play": print ('Ignored Command: ' + cmd)

        # The command was not recognized
        else: print ('Ignored Command: ' + cmd)

    def post_message(self, message):
        c = self.connection
        c.privmsg(self.channel, message)

class MessageScheduler():
    def __init__(self):
        print ('Phl3xSched Initialised')

    def __call__(self, Phl3xBot):
        try:
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
        except KeyboardInterrupt:
            sys.exit(1)                    


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
