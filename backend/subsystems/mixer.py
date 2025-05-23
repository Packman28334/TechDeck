
import socket

# All Commands we plan to use in some way
# set MIXER:Current/InCh/Fader/On {CH: 0-31?} 0 {STATE: 0-1} # Turn on or Off any Input Fader 
# set MIXER:Current/StInCh/Fader/On  {STCH: 1-2} 0 {STATE: 0-1} # Turn on or Off Stereo Input (Like Laptop Audio)
# set MIXER:Current/DCA/Fader/On {GROUP: 0-6?} 0 {STATE: 0-1} # Turn on or Off any Group Fader
# set MIXER:Current/MuteMaster/On {MUTE: 0-4?} 0 {STATE: 0-1} # Turn on or Off any Mute Group
# set MIXER:Current/Mtrx/Fader/On {MTRX: 1?-2?} 0 {STATE: 0-1} # Turn on or Off any Martix
# set MIXER:Current/Mix/Fader/On {MTRX: 0-??} 0 {STATE: 0-1} # Turn on or Off any AUX/Output Fader (Like The Speaker in the Booth)
# btw you are able to send to command space with a \n
# also every command must end with a \n and be .encode()
class MixerSubsystem:
    def __init__(self, host: str, port: int):
        # Basic socket connection from Yamaha Docs
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
        s.settimeout(5)
        s.connect((host,port))

    def get_configuration(self) -> dict:
        pass #?

    def enter_blackout(self):
        # Uses Mute Group 3 to Disable all Wanted Mics (The Blackout Mute Group)
        # Note Does not work currently becuase how we have it setup, will fix later 
        command = ("set MIXER:Current/MuteMaster/On 2 0 1 \n").encode() # Mute Group 3 ON
        s.sendall(command)

    def exit_blackout(self):
        # Undoes enter_blackout
        # Note Does not work currently becuase how we have it setup, will fix later 
        command = ("set MIXER:Current/MuteMaster/On 2 0 0 \n").encode() # Mute Group 3 OFF
        s.sendall(command)