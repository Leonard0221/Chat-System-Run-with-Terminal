"""
Created on Sun Apr  5 00:00:32 2015

@author: zhengzhang
"""
from chat_utils import *
from chat_group import *
import json
from minesweeper import *
import tkinter
import os
import  chat_client_class as clientStart


class ClientSM:
    def __init__(self, s, root):
        self.state = S_OFFLINE
        self.peer = []
        self.me = ''
        self.out_msg = ''
        self.s = s
        self.wins = 0
        self.losses = 0
        self.window = root

    def set_state(self, state):
        self.state = state

    def get_state(self):
        return self.state

    def set_myname(self, name):
        self.me = name

    def get_myname(self):
        return self.me

    def connect_to(self, peer):
        msg = json.dumps({"action": "connect", "target": peer})
        mysend(self.s, msg)
        response = json.loads(myrecv(self.s))
        if response["status"] == "success":
            for peer in response["members"]:
                self.peer.append(peer)
            if len(response["members"]) < 3:
                self.out_msg += '[SERVER] You are connected with ' + " and ".join(response["members"]) + '.\n'
            else:
                self.out_msg += f'[SERVER] You are connected with a group of {len(response["members"])} other people.\n'
            return True
        elif response["status"] == "busy":
            self.out_msg += '[SERVER] User is busy, please try again later.\n'
        elif response["status"] == "self":
            self.out_msg += '[SERVER] Cannot talk to yourself.\n'
        else:
            self.out_msg += '[SERVER] User is not online, please try again later.\n'
        return False

    def disconnect(self):
        msg = json.dumps({"action": "disconnect"})
        mysend(self.s, msg)
        if len(self.peer) == 1:
            self.out_msg += '[SERVER] You are disconnected from ' + self.peer[0] + ".\n"
        elif len(self.peer) == 2:
            self.out_msg += '[SERVER] You are disconnected from ' + " and ".join(self.peer) + ".\n"
        else:
            self.out_msg += "[SERVER] You are disconnected from the group.\n"
        self.peer = []

    def proc(self,  my_msg, peer_msg, root):
        self.out_msg  = ''
        # ==============================================================================
        # Once logged in, do a few things: get peer listing, connect, search
        # And, of course, if you are so bored, just go
        # This is event handling instate "S_LOGGEDIN"
        # ==============================================================================
        if self.state == S_LOGGEDIN:
            # todo: can't deal with multiple lines yet
            if len(my_msg) > 0:

                if my_msg == 'q':
                    self.out_msg += '[SERVER] See you next time!\n'
                    mysend(self.s, json.dumps({"action": "quit", "stats": (self.wins,self.losses)}))
                    self.state = S_OFFLINE

                elif my_msg == 'time':
                    mysend(self.s, json.dumps({"action": "time"}))
                    time_in = json.loads(myrecv(self.s))["results"]
                    self.out_msg += "[SERVER] Time is: " + time_in

                elif my_msg == 'who':
                    mysend(self.s, json.dumps({"action": "list"}))
                    logged_in = json.loads(myrecv(self.s))["results"]
                    self.out_msg += '[SERVER] Here are all the users in the system:\n'
                    self.out_msg += logged_in

                elif my_msg[0] == 'c':
                    peer = my_msg[1:]
                    peer = peer.strip()
                    if self.connect_to(peer):
                        self.state = S_CHATTING
                        self.out_msg += 'Chat away!\n\n'
                        self.out_msg += '-----------------------------------\n'
                    else:
                        self.out_msg += 'Connection unsuccessful.\n'


                elif my_msg[:6] == 'search':
                    term = my_msg[6:].strip()
                    mysend(self.s, json.dumps({"action": "search", "target": term}))
                    search_rslt = json.loads(myrecv(self.s))["results"]
                    if (len(search_rslt)) > 0:
                        self.out_msg += search_rslt + '\n'
                    else:
                        self.out_msg += '\'' + term + '\'' + ' not found\n'

                elif my_msg[0] == 'p' and my_msg[1:].strip().isdigit():
                    poem_idx = my_msg[1:].strip()
                    mysend(self.s, json.dumps({"action": "poem", "target": poem_idx}))
                    poem = json.loads(myrecv(self.s))["results"]
                    if len(poem) > 0:
                        self.out_msg += '\n' + "Enjoy your poem:" + '\n' + poem
                    else:
                        self.out_msg += '[SERVER] Sonnet ' + poem_idx + ' not found.\n\n'


                elif my_msg[0] == "d":
                    word = my_msg[1:].strip()
                    return self.detect(word)

                elif my_msg == "minesweeper":
                    self.out_msg += "[SERVER] Starting game...\n"
                    root.title("minesweeper")
                    minesweeper = Minesweeper(self)
                    root.mainloop()

                    self.out_msg += menu
                elif my_msg=="gobang":
                    try:
                        self.out_msg += "[SERVER] Starting game Gobang...\n"
                        os.system('python gobang.py')
                    except:
                        self.out_msg += "[SERVER] Ending game Gobang...\n"
                    finally:
                        self.out_msg += "[SERVER] Ending game Gobang...\n"

                elif my_msg == "stats":
                    mysend(self.s, json.dumps({"action": "stats"}))
                    wins, losses, rate = json.loads(myrecv(self.s))["stats"]
                    self.out_msg += "[SERVER] Here are your game stats:\n"
                    try:
                        self.out_msg += f"Wins: {wins+self.wins}, Losses: {losses+self.losses}, " \
                                    f"Win rate: {round((wins+self.wins)/(wins+self.wins+losses+self.losses)*100,2)}%\n"
                    except ZeroDivisionError:
                        self.out_msg += f"Wins: {0}, Losses: {0}, Win rate: {0}%\n"

                else:
                    self.out_msg += menu

            if len(peer_msg) > 0:
                try:
                    peer_msg = json.loads(peer_msg)
                except Exception as err:
                    self.out_msg += "[SERVER] json.loads failed " + str(err)
                    return self.out_msg

                if peer_msg["action"] == "connect":
                    # ----------your code here------#
                    self.peer.append(peer_msg["from"])
                    self.out_msg += "[SERVER] " + "You are connected with " + peer_msg["from"] + ". Chat away! \n"
                    self.state = S_CHATTING
                    # ----------end of your code----#

        # ==============================================================================
        # Start chatting, 'bye' for quit
        # This is event handling instate "S_CHATTING"
        # ==============================================================================
        elif self.state == S_CHATTING:
            if len(my_msg) > 0:  # my stuff going out
                if my_msg[0] == "/":
                    my_msg = my_msg[1:].strip().lower()
                    if my_msg == 'q':
                        self.disconnect()
                        self.state = S_LOGGEDIN
                        self.peer = []
                        self.out_msg += '[SERVER] See you next time!\n'
                        mysend(self.s, json.dumps({"action": "quit", "stats": (self.wins, self.losses)}))
                        self.state = S_OFFLINE

                    elif my_msg == 'time':
                        mysend(self.s, json.dumps({"action": "time"}))
                        time_in = json.loads(myrecv(self.s))["results"]
                        self.out_msg += "[SERVER] Time is: " + time_in

                    elif my_msg == 'who':
                        mysend(self.s, json.dumps({"action": "list"}))
                        logged_in = json.loads(myrecv(self.s))["results"]
                        self.out_msg += '[SERVER] Here are all the users in the system:\n'
                        self.out_msg += logged_in


                    elif my_msg[:6] == 'search':
                        term = my_msg[6:].strip()
                        mysend(self.s, json.dumps({"action": "search", "target": term}))
                        search_rslt = json.loads(myrecv(self.s))["results"]
                        if (len(search_rslt)) > 0:
                            self.out_msg += search_rslt + '\n'
                        else:
                            self.out_msg += '\'' + term + '\'' + ' not found\n'

                    elif my_msg[0] == 'p' and my_msg[1:].strip().isdigit():
                        poem_idx = my_msg[1:].strip()
                        mysend(self.s, json.dumps({"action": "poem", "target": poem_idx}))
                        poem = json.loads(myrecv(self.s))["results"]
                        if len(poem) > 0:
                            self.out_msg += '\n' + "Enjoy your poem:" + '\n' + poem
                        else:
                            self.out_msg += '[SERVER] Sonnet ' + poem_idx + ' not found.\n\n'

                    elif my_msg[0] == "d":
                        word = my_msg[1:].strip()
                        return self.detect(word)

                    elif my_msg == "minesweeper":
                        try:
                            self.out_msg += "[SERVER] Starting game minesweeper...\n"
                            #window = Tk()
                            print("====Minesweeper====")

                            self.window.title("Minesweeper")
                            minesweeper = Minesweeper(self)
                            self.out_msg += menu
                            self.window.mainloop()
                        except:
                            self.out_msg += "[SERVER] Ending game minesweeper...\n"
                    elif my_msg=="gobang":
                        try:
                            self.out_msg += "[SERVER] Starting game Gobang...\n"
                            os.system('python gobang.py')
                        except:
                            self.out_msg += "[SERVER] Ending game Gobang...\n"
                        finally:
                            self.out_msg += "[SERVER] Ending game Gobang...\n"

                    elif my_msg == "stats":
                        mysend(self.s, json.dumps({"action": "stats"}))
                        wins, losses, rate = json.loads(myrecv(self.s))["stats"]
                        self.out_msg += "[SERVER] Here are your game stats:\n"
                        try:
                            self.out_msg += f"Wins: {wins + self.wins}, Losses: {losses + self.losses}, " \
                                            f"Win rate: {round((wins + self.wins) / (wins + self.wins + losses + self.losses) * 100, 2)}%\n"
                        except ZeroDivisionError:
                            self.out_msg += f"Wins: {0}, Losses: {0}, Win rate: {0}%\n"

                    elif my_msg == "help":
                        self.out_msg += menu

                    else:
                        self.out_msg += "Invalid command. Type /help to see options." + "\n"

                else:
                    mysend(self.s, json.dumps({"action": "exchange", "from": "[" + self.me + "]", "message": my_msg}))
                    if my_msg == 'bye' or my_msg == 'goodbye':
                        self.disconnect()
                        self.state = S_LOGGEDIN
                        self.peer = []
            if len(peer_msg) > 0:  # peer's stuff, coming in

                # ----------your code here------#
                peer_msg = json.loads(peer_msg)
                from_name = peer_msg["from"]
                if peer_msg["action"] == "connect":
                    self.out_msg += "[SERVER] " + peer_msg["from"] + " joined.\n"
                    self.peer.append(from_name)
                elif peer_msg["action"] == "disconnect":
                    self.state = peer_msg["state"]
                    self.out_msg += peer_msg["message"] + "\n"
                    self.peer.remove(from_name)
                else:
                    self.out_msg += f"{from_name}: " + peer_msg["message"] + "\n" + '\n'
                # ----------end of your code----#

            # Display the menu again
            if self.state == S_LOGGEDIN:
                self.out_msg += menu
        # ==============================================================================
        # invalid state
        # ==============================================================================
        else:
            self.out_msg += 'How did you wind up here??\n'
            print_state(self.state)

        return self.out_msg
