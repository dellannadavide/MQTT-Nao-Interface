from __future__ import print_function

import os


baso = ["mbiv4", "nvt1j", "yam11", "6mtjb", "kuegk", "pv2x7", "x7tik", "ookw7", "xsj56", "imttl", "z372q", "5f1xb", "jeec1"]

# to_extract = "emotions"
to_extract = "emotions_v2"
# to_extract = "speech"
log_folder = "../log/25 participants/"

extracted_lines_list = []


for filename in os.listdir(log_folder):
    f = os.path.join(log_folder, filename)
    if os.path.isfile(f) and f.endswith(".log"):
        order_str = "baso" if filename.split("_")[0] in baso else "soba"
        exp_id = filename.split("_")[0]+"\t"+order_str+"\t"+filename.split("_")[4]
        with open(f) as file:
            lines = file.readlines()
            printed_one = False
            for line in lines:
                if printed_one:
                    if line.startswith(" "):
                        to_write = line.replace("\n","").replace("]","")
                        print(to_write)
                        extracted_lines_list[-1] = extracted_lines_list[-1]+to_write
                    else:
                        print()
                    printed_one = False

                if to_extract == "speech":
                    if ("mqtt-nao-interface.sensors.audio.speechrecognizer - Detected speech info" in line) or \
                        ("mqtt-nao-interface.actuators.speech.tts - ['say'," in line):
                        to_write = exp_id+"\t"+line.replace("\n","")
                        print(to_write, end = '')
                        printed_one = True
                        extracted_lines_list.append(to_write)

                if to_extract == "emotions":
                    if "mqtt-nao-interface.sensors.video.emotion_detector - Predicted:" in line:
                        to_write = exp_id + "\t" + line.replace("\n", "").replace("INFO - mqtt-nao-interface.sensors.video.emotion_detector - Predicted: ","")
                        print(to_write,end = '')
                        printed_one = True
                        extracted_lines_list.append(to_write)

                if to_extract == "emotions_v2":
                    if "mqtt-nao-interface.sensors.video.emotion_detector - Prob.:" in line:
                        to_write = exp_id + "\t" + line.replace("\n", "").replace(
                            "INFO - mqtt-nao-interface.sensors.video.emotion_detector - Prob.: ", "").replace("[","")
                        print(to_write,end = '')
                        printed_one = True
                        extracted_lines_list.append(to_write)

with open(r'test.txt', 'w') as fp:
    for line in extracted_lines_list:
        # write each item on a new line
        fp.write("%s\n" % line.replace(" - ","\t"))
