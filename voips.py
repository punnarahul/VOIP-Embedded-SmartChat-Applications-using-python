#Importing all necessary modules....
import sys 
import threading
import socket
import time
from tkinter import messagebox
from tkinter import ttk
from tkinter import *
import winsound
import Replydictionaries
import smartemojimapper
from datetime import datetime
from PIL import Image
from PIL import ImageTk
from module2 import AudioReceiver,AudioSender

#Initiating the connection 
serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serversocket.bind((socket.gethostname(), 8001))
serversocket.listen(1)
s,addr = serversocket.accept()
print('Connection Established.......Enjoy the Chat')
isconnectionalive=True #for a case when thread just got wokeup and destroy has been called then no need to enter into while loop in run funtion of that thread

#Function for closing the connections
def connectioncloser():
    global isconnectionalive
    isconnectionalive=False
    s.close()
    serversocket.close()
    print('Connection Closed Succesfully')

#tkinter object cretion and adding background image and the title
top = Tk()
top.geometry("600x650")
top.resizable(False, False)
top.title("Server")
img = Image.open("Background/b-1.png")
bgimg= ImageTk.PhotoImage(img)
label = ttk.Label(top,image=bgimg)
label.place(x=0, y=0)
h=Label(top,text="SmartChat App",font=("Microsoft Himalaya", 16),background='#100d2b',foreground="#f5f5fc")
h.pack(side=TOP)

#Creating a new frame for listbox and emoji displaying as well
ListFrame=Frame(top)
listv=Listbox(ListFrame,width=40,height=18,font=("Times", 16, "italic"),bd=5, bg = '#d3d3db', fg = '#f705af')
listv.pack(side=LEFT)
width = 90
height = 90
img = Image.open("Emojis/picture-10.png")
img = img.resize((width,height), Image.ANTIALIAS)
Displayingemojipic =  ImageTk.PhotoImage(img)
Displayingemoji=Label(ListFrame,image=Displayingemojipic)
Displayingemoji.pack(side=RIGHT)
Displayingemoji.pack_forget()
ListFrame.config(background='#d3d3db')
ListFrame.pack(side=TOP)

#Function to change the pictures on labels on the frames
def emojichanger(labelcatcher,no):
    nameofpic="Emojis/picture-"+str(no)+".png"
    global width,height
    img = Image.open(nameofpic)
    img = img.resize((width,height), Image.ANTIALIAS)
    picturevar =  ImageTk.PhotoImage(img)
    labelcatcher.configure(image=picturevar)
    labelcatcher.image = picturevar

#Importing the smart mappers
smart_emoji_mapper=smartemojimapper.smart_emoji_mapper
smart_positive_replies=Replydictionaries.smart_positive_replies 
smart_negative_replies=Replydictionaries.smart_negative_replies

#Since there is a thread it will check even after the close on tkinter pressed so destroyer function has chance of calling twice...
closedbyme=False 

#Varibles for two thread for sending the audio and recieving the audio
sender=None
recieve=None

#Destroyer function which destroys frame and remove connection as well
def destroyer():
    global closedbyme
    closedbyme=True 
    try:
        if(recieve.running):
            recieve.stop_server()
        if(sender.running):
            sender.stop_stream()
    except:
        pass
    try:
        top.quit()
    except:
        pass
    try:
        connectioncloser()
    except:
        pass
    print("Connection closed successfully...")
    sys.exit()

#Attaching a function which is invoked when close button on tkinter is pressed
top.protocol("WM_DELETE_WINDOW",destroyer)

#Maintaing all the varibles required for reciving thread
idv=-1
myidv=-1
otheridv=-1
myidvstack=[]
otheridvstack=[]

#For storing the current picture being displayed in the smart emoji recommendation
currentlyshownemoji="none" 

#Variables required for Smart Chat Buttons to change text dynamically
positivereply=StringVar()
negativereply=StringVar()
positivereply.set("yes")
negativereply.set("no")

#Varibles for revert button
gotmsgfromrecv=False 
recentrecievedmessage=""

#CallRaiseButton and call cut button
call_init_button=None
call_cut_button=None

def call_request():
    try:
        global sender,recieve,call_cut_button,call_init_button
        try:
            sender=AudioSender(socket.gethostbyname(socket.gethostname()),8002)
            recieve=AudioReceiver(socket.gethostbyname(socket.gethostname()),9999)
            sender_thread=threading.Thread(target=sender.start_stream)
            recieve_thread=threading.Thread(target=recieve.start_server)
            try:    
                recieve_thread.start()
                sender_thread.start()
            except:
                pass
        except Exception as e:
            print("thread starting trouble ",e)
            return

        #After creating the threads, setting buttons appropriatel    
        call_init_button.config(state=DISABLED)
        call_cut_button.config(state=NORMAL)
    except:
        pass
    
#Creating call cutter function..
def call_cutter():
    try:
        sender.stop_stream()
        recieve.stop_server()
        Displayingemoji.pack_forget()
    except:
        pass
    call_init_button.config(state=NORMAL)
    call_cut_button.config(state=DISABLED)

#Function for inserting from sender 
def mymsglistadd(item):
    global listv,myidvstack,idv
    idv+=1
    if(len(item)>30):
        listv.insert(idv,item[:30].rjust(60))
        listv.itemconfig(idv,foreground="grey",background='#d3d3db')
        myidvstack.append(idv)
        idv+=1
        listv.insert(idv,item[30:].rjust(60))
        myidvstack.append(idv)
        listv.itemconfig(idv,foreground="grey",background='#d3d3db')
    else:
        listv.insert(idv,item.rjust(60))
        myidvstack.append(idv)
        listv.itemconfig(idv,foreground="grey",background='#d3d3db')
    listv.see(idv)

#Function for inserting from sender 
def othermsglistadd(item):
    global listv,otheridvstack,idv
    idv+=1
    if(len(item)>30):
        listv.insert(idv,item[:30])
        listv.itemconfig(idv,foreground="#000000",background='#bfbfd9')
        otheridvstack.append(idv)
        idv+=1
        listv.insert(idv,item[30:])
        listv.itemconfig(idv,foreground="#000000",background='#bfbfd9')
        otheridvstack.append(idv)
    else:
        listv.insert(idv,item)
        listv.itemconfig(idv,foreground="#000000",background='#bfbfd9')
        otheridvstack.append(idv)
    listv.see(idv)

#Creating a Thread class which checks for message recieved
class tr(threading.Thread):

    #Init class of thread
    def __init__(self,s,lv):
        threading.Thread.__init__(self)
        self.ob=s  
        self.lv=lv

    #Run method of thread 
    def run(self):
        try:
            global idv,gotmsgfromrecv,recentrecievedmessage,otheridv,otheridvstack,myidv,myidvstack,container
            while isconnectionalive:
                
                #Accepting a message
                r=self.ob.recv(1024).decode()

                #If it is visible then don't show
                Displayingemoji.pack_forget()

                #call initiated from my side
                if(r=="***Call-Acknowledge***"):
                    try:
                        call_request()
                        emojichanger(Displayingemoji,31)
                        Displayingemoji.pack(side=RIGHT)
                        othermsglistadd("Call-Requested-Accepted")
                    except:
                        pass
                    continue

                #call initiated from other side
                if(r=="***Call-Willingness***"):
                    try:
                        msg=messagebox.askquestion('Call Request','Do you want to Accept?')
                        othermsglistadd("Call-Requested")
                        if(msg=="yes"):
                            button("***Call-Acknowledge***")
                            time.sleep(0.01)
                            call_request()
                            emojichanger(Displayingemoji,31)
                            Displayingemoji.pack(side=RIGHT)
                    except:
                        pass
                    continue

                #If other aborted the call then msg is sent
                if(r=="***quit***"):
                    call_cutter()
                    continue
                
                #Checking if recieved message is an emoji and displaying it 
                try:
                    if(r[:len(r)-2]=="***picture-"):
                        number=r.split('-')
                        emojichanger(Displayingemoji,number[1])
                        Displayingemoji.pack(side=RIGHT)
                        tag=smart_emoji_mapper[int(number[1])]
                        item="Sticker-"+tag
                        othermsglistadd(item)
                        continue
                except:
                    print("here")

                #Checking if recieved message is an delete request and processing it 

                if(r=='***DELETE***'):
                    if(len(otheridvstack)>0):
                        otheridv=otheridvstack.pop()
                        self.lv.delete(otheridv)
                        if(len(myidvstack)>0):
                            myidvstackbeforedel=[i for i in myidvstack if i<otheridv]
                            myidvstackafterdel=[i-1 for i in myidvstack if i>otheridv]
                            myidvstack=myidvstackbeforedel+myidvstackafterdel
                        idv-=1
                    continue
                
                #Making a Beep sound    
                winsound.Beep(500,50)

                #Storing Most recent message stored
                if(not gotmsgfromrecv):
                    gotmsgfromrecv=True
                recentrecievedmessage=r

                #Processing for Smart Reply
                if(len(r)<30):
                    try:
                        global positivereply,negativereply
                        lower_version_string=r.lower()
                        str1=smart_positive_replies[lower_version_string]
                        str2=smart_negative_replies[lower_version_string]
                        positivereply.set(str1)
                        negativereply.set(str2)
                        Smartframe.pack()
                    except:
                        pass

                #Processing for smart emoji's
                if(len(r)<35):
                    try:
                        global currentlyshownemoji
                        lower_version_string=r.lower()
                        emojiid=smart_emoji_mapper[lower_version_string]
                        emojichanger(smartemoji,emojiid)
                        currentlyshownemoji="picture-"+str(emojiid)
                        SmartEmoji.pack()
                    except:
                        pass
                
                #Displaying the Message in ListBox
                othermsglistadd(r)

                #for every 200ms run this thread
                time.sleep(0.2)
        except:
            #if connection closed then controller will come here
            global closedbyme

            #if not closed by me then we show message then we will close our program
            if(not closedbyme):
                msg=messagebox.showinfo('Note','Reciever(Client) has left the Chat.from recv dept')
                try:
                    destroyer()
                except:
                    pass
                sys.exit()

#Variables which stores the user's text input            
texttosend=StringVar()  

#Function to send message to be displayed...
def button(x="na"): 
    #x='na' determines that send button is pressed
    #if smartframe is visible then it should not be displayed
    Smartframe.pack_forget()
    SmartEmoji.pack_forget()
    
    #Try is for if connection is closed by other user and if current user sends a messge then it throws exception
    try:
        global idv,myidv
        sendmsg=""

        #Obtaining the message to be sent
        if(x!="na"):
            sendmsg=x
        else:
            sendmsg=texttosend.get()
            if(sendmsg==""):
                return
            if(sendmsg[:3]=="***"):
                texttosend.set("")
                return
            texttosend.set("")


        #sending the message
        s.send(sendmsg.encode('ascii'))

        if(x=="***Call-Willingness***"):
            mymsglistadd("Call-Requested")
            return
        if(x=="***Call-Acknowledge***"):
            mymsglistadd("Call-Requested-Accepted")
            return



        #If it is Emoji then we need to add Sticker in listbox
        if x[:len(x)-3]=='***picture':
            sarr=x.split('-')
            tag=smart_emoji_mapper[int(sarr[1])]
            item="Sticker-"+tag
            mymsglistadd(item)#Making a Beep sound
            winsound.Beep(500,50)
            return

        #If it is Delete Request or quit call then no need to add in listbox 
        if x[:3]=="***":
            return

        #Making a Beep sound
        winsound.Beep(500,50)

        #Adding the text message which is being sent
        mymsglistadd(sendmsg)
    except:
        #When user sends a message at the same moment it is closed by other user then controller comes here 
        #so thread will sense the absence for of other user in 200ms so we will let the main thread sleep for 500ms
        time.sleep(0.5)

#Emoji Suggestion Frame
SmartEmoji=Frame(top)
smartemoji=Label(SmartEmoji,image=Displayingemojipic)
SmartEmoji.config(background='#0e0b57')

#Function for emoji sender button
def emojisender():
    SmartEmoji.pack_forget()
    global currentlyshownemoji
    button("***"+currentlyshownemoji)

#Send button in emoji frame
sendemojibuttonstringvar=StringVar()
sendemojibuttonstringvar.set("Send")
emojisendbutton=Button(SmartEmoji,textvariable=sendemojibuttonstringvar,command=emojisender,background='#100d2b', foreground='#dad8f0')
smartemoji.pack(side=TOP)
emojisendbutton.pack(side=BOTTOM)
SmartEmoji.pack_forget()


#For Styling the smart buttons.
style=ttk.Style()
style.theme_use('alt')
style.configure('TButton', font=('American typewriter', 10), background='#100d2b', foreground='#dad8f0')
style.map('TButton', background=[('active', '#120145'), ('disabled', '#03001c')])
style.map('TButton', foreground=[('active', '#dad8f0'), ('disabled', '#000003')])


#Frame for Smart text Suggestions..
#Functions for Smart Suggestions
Smartframe=Frame(top)
def posi():
    button(positivereply.get())
def negi():
    button(negativereply.get())

#Initializing smart Buttons
positive=ttk.Button(Smartframe,textvariable=positivereply,command=posi)
positive.pack(side=RIGHT)
negative=ttk.Button(Smartframe,textvariable=negativereply,command=negi)
negative.pack(side=LEFT)
Smartframe.pack_forget()

#Frame for all normal buttons
lastframe=Frame(top,width=80)
lastframe.config(background='#100d2b')

#Functions for Additional Buttons
#1.revert button function
def reverter():
    if(gotmsgfromrecv):
        button(recentrecievedmessage)

#2.titleformat the text entered by user
def titlemaker():
    cap=texttosend.get()
    texttosend.set(cap.title())

#3.Greeter fucntion to greet
def greeter():
    timenow=datetime.now()
    hrs=timenow.hour
    if(hrs>=4 and hrs<=11):
        button("Good Morning")
    elif(hrs>=12 and hrs<=15):
        button("Good Afternoon")
    else:
        button("Good Evening")

#4.Delete the recent message
def deleter():
    global myidv,idv,myidvstack,otheridvstack
    if len(myidvstack)>0:
        myidv=myidvstack.pop()
        listv.delete(myidv)
        if(len(otheridvstack)>0):
            otheridvstackbeforedel=[i for i in otheridvstack if i<myidv]
            otheridvstackafterdel=[i-1 for i in otheridvstack if i>myidv]
            otheridvstack=otheridvstackbeforedel+otheridvstackafterdel
        button("***DELETE***")
        idv-=1

#Initializing all the buttons and adding it to frame
r=ttk.Button(lastframe,text="revert",width=5,command=reverter)
r.pack(side=LEFT)

g=ttk.Button(lastframe,text="Greet",width=5,command=greeter)
g.pack(side=LEFT)
txt=ttk.Entry(lastframe,textvariable=texttosend,width=20)
txt.pack(side=LEFT)
dele=ttk.Button(lastframe,text="delete",command=deleter,width=5)
dele.pack(side=RIGHT)
titl=ttk.Button(lastframe,text="title",command=titlemaker,width=5)
titl.pack(side=RIGHT)
b=ttk.Button(lastframe,text="send",command=button,width=5)
b.pack(side=RIGHT)
lastframe.pack(side=BOTTOM)

#For Call initiation and recieve at recv
def call_raise():
    button("***Call-Willingness***")

#Call init button for indicating call willingness for other party
call_init_button=ttk.Button(lastframe,text="Call",width=5,command=call_raise)
call_init_button.pack(side=LEFT)

#Function when call is cut by my self
def call_cut():
    button("***quit***")
    call_cutter()
    
#Button for call cut
call_cut_button=ttk.Button(lastframe,text="cut",width=5,command=call_cut)
call_cut_button.pack(side=LEFT)
call_cut_button.config(state=DISABLED)

#creating the thread object and starting
t=tr(s,listv)
t.start()

#start the tkinter
top.mainloop()