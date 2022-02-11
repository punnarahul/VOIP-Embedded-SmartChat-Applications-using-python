import socket
import pyaudio
import select
import threading

class AudioSender:

    def __init__(self, host, port, audio_format=pyaudio.paInt16, channels=1, rate=44100, frame_chunk=4096):
        self.__host = host
        self.__port = port

        self.__audio_format = audio_format
        self.__channels = channels
        self.__rate = rate
        self.__frame_chunk = frame_chunk

        self.__sending_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__audio = pyaudio.PyAudio()

        self.running = False

    #
    # def __callback(self, in_data, frame_count, time_info, status):
    #     if self.running:
    #         self.__sending_socket.send(in_data)
    #         return (None, pyaudio.paContinue)
    #     else:
    #         try:
    #             self.__stream.stop_stream()
    #             self.__stream.close()
    #             self.__audio.terminate()
    #             self.__sending_socket.close()
    #         except OSError:
    #             pass # Dirty Solution For Now (Read Overflow)
    #         return (None, pyaudio.paComplete)

    def start_stream(self):
        try:
            if self.running:
                print("Already streaming")
            else:
                self.running = True
                thread = threading.Thread(target=self.__client_streaming)
                thread.start()
        except:
            pass

    def stop_stream(self):
        try:
            if self.running:
                self.running = False
            else:
                print("Client not streaming")
        except:
            pass

    def __client_streaming(self):
        try:
            self.__sending_socket.connect((self.__host, self.__port))
            self.__stream = self.__audio.open(format=self.__audio_format, channels=self.__channels, rate=self.__rate, input=True, frames_per_buffer=self.__frame_chunk)
            while self.running:
                self.__sending_socket.send(self.__stream.read(self.__frame_chunk))
        except:
            pass


class AudioReceiver:

    def __init__(self, host, port, slots=8, audio_format=pyaudio.paInt16, channels=1, rate=44100, frame_chunk=4096):
        self.__host = host
        self.__port = port

        self.__slots = slots
        self.__used_slots = 0

        self.__audio_format = audio_format
        self.__channels = channels
        self.__rate = rate
        self.__frame_chunk = frame_chunk

        self.__audio = pyaudio.PyAudio()

        self.__server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__server_socket.bind((self.__host, self.__port))

        self.__block = threading.Lock()
        self.running = False

    def start_server(self):
        try:
            if self.running:
                print("Audio server is running already")
            else:
                self.running = True
                self.__stream = self.__audio.open(format=self.__audio_format, channels=self.__channels, rate=self.__rate, output=True, frames_per_buffer=self.__frame_chunk)
                thread = threading.Thread(target=self.__server_listening)
                thread.start()
        except:
            pass



    def __server_listening(self):
        try:
            self.__server_socket.listen()
            while self.running:
                self.__block.acquire()
                connection, address = self.__server_socket.accept()
                if self.__used_slots >= self.__slots:
                    print("Connection refused! No free slots!")
                    connection.close()
                    self.__block.release()
                    continue
                else:
                    self.__used_slots += 1

                self.__block.release()
                thread = threading.Thread(target=self.__client_connection, args=(connection, address,))
                thread.start()
        except:
            pass

    def __client_connection(self, connection, address):
        try:
            while self.running:
                data = connection.recv(self.__frame_chunk)
                self.__stream.write(data)
        except:
            pass

    def stop_server(self):
        try:
            if self.running:
                self.running = False
                closing_connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                closing_connection.connect((self.__host, self.__port))
                closing_connection.close()
                self.__block.acquire()
                self.__server_socket.close()
                self.__block.release()
            else:
                print("Server not running!")
        except:
            pass