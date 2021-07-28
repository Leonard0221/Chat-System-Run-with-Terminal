import time
import socket
import select
import sys
import json
from chat_utils import *
import client_state_machine as csm
from tkinter import Tk, Frame, Scrollbar, Label, END, Entry, Text, VERTICAL, Button, \
    messagebox  # Tkinter Python Module for GUI
import os
import threading

#root = Tk()
class Client:
    def __init__(self, args):
        self.peer = ''
        self.console_input = []
        self.state = S_OFFLINE
        self.system_msg = ''
        self.local_msg = ''
        self.peer_msg = ''
        self.args = args
        self.root = Tk()

        # self.root = master
        # self.chat_transcript_area = None
        # self.name_widget = None
        # self.enter_text_widget = None
        # self.join_button = None
        # self.initialize_gui()
        # self.listen_for_incoming_messages_in_a_thread()

    def quit(self):
        self.socket.shutdown(socket.SHUT_RDWR)
        self.socket.close()
        self.root.destroy()

    def get_name(self):
        return self.name

    def init_chat(self): #contains self.initialize_socket() and self.listen_for_incoming_messages_in_a_thread()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM )
        svr = SERVER if self.args.d == None else (self.args.d, CHAT_PORT)
        self.socket.connect(svr)
        self.sm = csm.ClientSM(self.socket,self.root)
        reading_thread = threading.Thread(target=self.read_input) # Create a thread for the send and receive in same time
        reading_thread.daemon = True
        reading_thread.start()

    def shutdown_chat(self):
        return

    def send(self, msg):
        mysend(self.socket, msg)

    def recv(self):
        return myrecv(self.socket)

    def get_msgs(self):
        read, write, error = select.select([self.socket], [], [], 0)
        my_msg = ''
        peer_msg = []
        #peer_code = M_UNDEF    for json data, peer_code is redundant
        if len(self.console_input) > 0:
            my_msg = self.console_input.pop(0)
        if self.socket in read:
            peer_msg = self.recv()
        return my_msg, peer_msg

    def output(self):
        if len(self.system_msg) > 0:
            print(self.system_msg)
            self.system_msg = ''
            # self.chat_transcript_area.insert('end', self.system_msg + '\n')
            # self.system_msg = ''
            # self.chat_transcript_area.yview(END)


    def login(self):
        my_msg, peer_msg = self.get_msgs()
        if len(my_msg) > 0:
            self.name = my_msg
            msg = json.dumps({"action":"login", "name":self.name})
            self.send(msg)
            response = json.loads(self.recv())
            if response["status"] == 'ok':
                self.state = S_LOGGEDIN
                self.sm.set_state(S_LOGGEDIN)
                self.sm.set_myname(self.name)
                self.print_instructions()
                return (True)
            elif response["status"] == 'duplicate':
                self.system_msg += 'Duplicate username, try again'
                return False
        else:               # fix: dup is only one of the reasons
           return(False)


    def read_input(self):
        while True:
            text = sys.stdin.readline()[:-1]
            self.console_input.append(text) # no need for lock, append is thread safe

    def print_instructions(self):
        self.system_msg += menu

    #important to for GUI
    def run_chat(self):
        self.init_chat()
        self.system_msg += '[SERVER] Welcome to the ICS chat!\n'
        self.system_msg += 'Please enter your name: '
        self.output() #have to change?
        while self.login() != True:
            self.output()
        self.system_msg += '[SERVER] Welcome, ' + self.get_name() + '!' + "\n"
        self.output()
        #print("self.sm.get_state():"+str(self.sm.get_state()))
        while self.sm.get_state() != S_OFFLINE:
            self.proc()
            self.output()
            time.sleep(CHAT_WAIT)
        self.quit()

#==============================================================================
# main processing loop
#==============================================================================
    def proc(self):
        my_msg, peer_msg = self.get_msgs()
        self.system_msg += self.sm.proc( my_msg, peer_msg, self.root)

#GUI Codes
    def initialize_gui(self):  # GUI initializer
        self.root.title("Chat System")
        self.root.resizable(0, 0)
        self.display_chat_box()
        self.display_name_section()
        self.display_chat_entry_box()
    #done

    #may need to change
    def listen_for_incoming_messages_in_a_thread(self):
        thread = threading.Thread(target=self.receive_message_from_server,
                                  args=(self.socket,))  # Create a thread for the send and receive in same time
        thread.start()

    # function to receive msg, need to change
    def receive_message_from_server(self, so):
        while True:
            buffer = so.recv(256)
            if not buffer:
                break
            message = buffer.decode('utf-8')
            text = sys.stdin.readline()[:-1]

            if "joined" in message:
                user = message.split(":")[1]
                message = user + " has joined"
                self.chat_transcript_area.insert('end', message + '\n')
                self.chat_transcript_area.yview(END)
            else:
                self.chat_transcript_area.insert('end', message + '\n')
                self.chat_transcript_area.yview(END)


        so.close()

    def display_name_section(self):
        frame = Frame()
        Label(frame, text='Enter your name:', font=("Helvetica", 16)).pack(side='left', padx=10)
        self.name_widget = Entry(frame, width=50, borderwidth=2)
        self.name_widget.pack(side='left', anchor='e')
        self.join_button = Button(frame, text="Join", width=10, command=self.on_join).pack(side='left')
        frame.pack(side='top', anchor='nw')
        #check command

    def display_chat_box(self):
        frame = Frame()
        Label(frame, text='Chat Box:', font=("Serif", 12)).pack(side='top', anchor='w')
        self.chat_transcript_area = Text(frame, width=60, height=10, font=("Serif", 12))
        scrollbar = Scrollbar(frame, command=self.chat_transcript_area.yview, orient=VERTICAL)
        self.chat_transcript_area.config(yscrollcommand=scrollbar.set)
        self.chat_transcript_area.bind('<KeyPress>', lambda e: 'break')
        self.chat_transcript_area.pack(side='left', padx=10)
        scrollbar.pack(side='right', fill='y')
        frame.pack(side='top')
        #done

    def display_chat_entry_box(self):
        frame = Frame()
        Label(frame, text='Enter message:', font=("Serif", 12)).pack(side='top', anchor='w')
        self.enter_text_widget = Text(frame, width=60, height=3, font=("Serif", 12))
        self.enter_text_widget.pack(side='left', pady=15)
        self.enter_text_widget.bind('<Return>', self.on_enter_key_pressed)
        frame.pack(side='top')
        #check self.on_enter_key_pressed

    def on_join(self):
        if len(self.name_widget.get()) == 0:
            messagebox.showerror(
                "Enter your name", "Enter your name to send a message")
            return
        self.name_widget.config(state='disabled')

    def on_enter_key_pressed(self, event):
        if len(self.name_widget.get()) == 0:
            messagebox.showerror("Enter your name", "Enter your name to send a message")
            return
        self.send_chat()
        self.clear_text()
        #figure out how to send text

    # def send_chat(self):
    #     senders_name = self.name_widget.get().strip() + ": "
    #     data = self.enter_text_widget.get(1.0, 'end').strip()
    #     message = (senders_name + data).encode('utf-8')
    #     self.chat_transcript_area.insert('end', message.decode('utf-8') + '\n')
    #     self.chat_transcript_area.yview(END)
    #     self.send(message)
    #     self.enter_text_widget.delete(1.0, 'end')
    #     return 'break'

    def clear_text(self):
        self.enter_text_widget.delete(1.0, 'end')
        #clear

    def send_chat(self):
        senders_name = self.name_widget.get().strip() + ": "
        data = self.enter_text_widget.get(1.0, 'end').strip()
        message = (senders_name + data).encode('utf-8')
        self.chat_transcript_area.insert('end', message.decode('utf-8') + '\n')
        self.chat_transcript_area.yview(END)
        self.proc()
        self.enter_text_widget.delete(1.0, 'end')
        return 'break'

    def on_close_window(self):
        Button(self.root, text="Quit", command=quit).pack()
        self.root.destroy()
        self.root.quit()
        # self.socket.close()
        # exit(0)


# the mail function
# if __name__ == '__main__':
#     root = Tk()
#     gui = GUI(root)
#     root.protocol("WM_DELETE_WINDOW", gui.on_close_window)
#     root.mainloop()