import time

import speech_recognition as sr


def callback(recognizer, audio):  # this is called from the background thread
    print("callback function invoked")
    global is_listening, stop_listening
    is_listening = False
    stop_listening(wait_for_stop=False) #stop listening when audio being processed (it will restart later)
    try:
        print("You said " + recognizer.recognize_google(audio))  # received audio data, now need to recognize it
    except:
        print("Oops! Didn't catch that")



r = sr.Recognizer()
mic = sr.Microphone()
with mic as source:
    r.adjust_for_ambient_noise(source)

while True:
    print(r.energy_threshold)
    is_listening = True
    timeout = time.time() + 10  # timeout in 10 seconds
    try:
        stop_listening = r.listen_in_background(sr.Microphone(), callback, phrase_time_limit=5)
        while is_listening:
            if time.time() <= timeout:
                time.sleep(0.1)
            else: #if I reached the timeout
                print("timeout reached")
                stop_listening(wait_for_stop=False) #stop listening when timeout reached
                is_listening = False
    except:
        print("erro here?")
    time.sleep(0.1)

# while True: time.sleep(0.1)

#
# def callback(recognizer, audio):
#     global is_listening, text_recognized
#     is_listening = False
#     try:
#         text_recognized = recognizer.recognize_google(audio)
#     except:
#         print("exception in recognition")
#         text_recognized = None
#
#
# if __name__ == "__main__":
#     is_listening = False
#     text_recognized = None
#
#     r = sr.Recognizer()
#     mic = sr.Microphone()
#
#
#     while True:  # this is the sensing loop
#         is_listening = True
#         with mic as source:
#             try:
#                 timeout = time.time() + 10  # timeout in 10 seconds
#                 stop_listening = r.listen_in_background(source, callback, phrase_time_limit=5)
#                 while is_listening:
#                     if time.time() <= timeout:
#                         time.sleep(0.05)
#                     else: #if I reached the timeout
#                         stop_listening(wait_for_stop=False)
#                         is_listening = False
#                 #here either I reached the timeout or I detected something, which should be in the variable text_recognized
#                 if text_recognized is None:
#                     print("no text recognized")
#                 else:
#                     print(text_recognized)
#                     text_recognized = None
#             except:
#                 print("exception in the while true")
#                 is_listening = False
#                 text_recognized = None
#         is_listening = False
#         time.sleep(0.1)
