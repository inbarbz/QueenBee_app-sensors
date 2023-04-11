# from datetime import time
from PIL import ImageFilter
from PIL import Image
import cv2
import random
import time
import math
import os
from datetime import datetime

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plost
from camera_input_live import camera_input_live

import dummy

from PIL import Image, ImageEnhance
import numpy as np
from streamlit.runtime.uploaded_file_manager import UploadedFile

camera_file = None
current_index = 0

uv_data = pd.read_csv('uv.csv')  # , parse_dates=['date']
sound_data = pd.read_csv('sounddata.csv')  # , parse_dates=['date']


def get_current_uv():
    if 'current_uv' in st.session_state:
        return float(st.session_state['current_uv'])
    else:
        return 0.68


def refresher(seconds):
    # print('refreshing...')
    mainDir = os.path.dirname(__file__)
    filePath = os.path.join(mainDir, 'dummy.py')
    with open(filePath, 'w') as f:
        f.write(f'# {random.randint(0, 10000)}')
    time.sleep(seconds)


def get_next_uv(df, i):
    i = random.Random().randint(0, len(df) - 1)
    df = pd.concat([df[i:], df[:i]])
    return df.iloc[i]['uv'], i, df


def is_video_file(file_name):
    if 'BytesIO' in str(type(file_name)):
        return False
    if 'UploadedFile' in str(type(file_name)):
        if "mp4" in file_name.name:
            return True
    return False


kelvin_table = {
    1000: (255, 56, 0),
    1500: (255, 109, 0),
    2000: (255, 137, 18),
    2500: (255, 161, 72),
    3000: (255, 180, 107),
    3500: (255, 196, 137),
    4000: (255, 209, 163),
    4500: (255, 219, 186),
    5000: (255, 228, 206),
    5500: (255, 236, 224),
    6000: (255, 243, 239),
    6500: (255, 249, 253),
    7000: (245, 243, 255),
    7500: (235, 238, 255),
    8000: (227, 233, 255),
    8500: (220, 229, 255),
    9000: (214, 225, 255),
    9500: (208, 222, 255),
    10000: (204, 219, 255),
    11000: (100, 100, 255),
}


# import asyncio
# from bleak import BleakScanner
# async def bt_test():
#     devices = await BleakScanner.discover()
#     for d in devices:
#         print(d)
#
# print("Scanning for devices...")
# asyncio.run(bt_test())


def convert_temp(image, temp):
    r, g, b = kelvin_table[temp]
    matrix = (r / 255.0, 0.0, 0.0, 0.0,
              0.0, g / 255.0, 0.0, 0.0,
              0.0, 0.0, b / 255.0, 0.0)

    return image.convert('RGB').convert('RGB', matrix)


def process_pixel(pixel):
    threshold = 200
    max_yellow = [255, 255, 1]
    blue = kelvin_table[temperature]
    r, g, b = pixel
    average_intensity = math.sqrt((r ** 2 + g ** 2 + b ** 2) / 3) / 255.0
    # print(average_intensity)
    if r > threshold and g > threshold and b > threshold:
        return int(max_yellow[0] * average_intensity), int(max_yellow[1] * average_intensity), int(
            (max_yellow[2] * average_intensity))
    # return int(blue[0]*average_intensity), int(blue[1]*average_intensity), int(blue[2]*average_intensity)
    # return int(blue[0]*average_intensity), int(blue[1]*average_intensity), int(blue[2]*average_intensity)
    return int(r / 2 + blue[0]), int(g / 2 + blue[1]), int(b / 2 + blue[2])


def my_filter(image):
    for x in range(image.size[0]):
        for y in range(image.size[1]):
            image.putpixel((x, y), process_pixel(image.getpixel((x, y))))
    return image


initial_time = 500
current_uv = 0.68


def get_current_time():
    ct = initial_time
    if 'current_time' in st.session_state:
        ct = st.session_state['current_time']
    # skip 1 second every time
    ct += 1
    st.session_state['current_time'] = ct
    return ct


def reset_current_time():
    st.session_state['current_time'] = initial_time


def tune_based_on_uv(param, uv):
    param = param + uv * 1.5
    return param


st.set_page_config(layout='wide', initial_sidebar_state='expanded')
placeholder = st.empty()

with open('style.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

st.sidebar.header('version 1.0')

use_image = st.sidebar.checkbox(label="Use Image", value=False)
use_vibrate = st.sidebar.checkbox(label="Vibrate", value=False)
use_my_filter = st.sidebar.checkbox(label="My-Filter", value=True)

enhance_brightness = st.sidebar.slider(
    label="Brightness", min_value=0.0, max_value=5.0, value=1.6, step=0.1)
enhance_contrast = st.sidebar.slider(
    label="Contrast", min_value=0.0, max_value=5.0, value=1.8, step=0.1)
enhance_sharpness = st.sidebar.slider(
    label="Sharpness", min_value=0.0, max_value=5.0, value=0.0, step=0.1)
enhance_color = st.sidebar.slider(
    label="Color", min_value=0.0, max_value=5.0, value=0.0, step=0.1)
video_frames_to_skip = st.sidebar.slider(
    label="Video Skip Frames", min_value=1, max_value=30, value=10, step=1)

st.sidebar.subheader('Camera Temperature')
temperature = st.sidebar.selectbox(label='Temperature',
                                   options=(1000, 2000, 3000, 4000, 5000,
                                            6000, 7000, 8000, 9000, 10000, 11000),
                                   index=10)

st.markdown('### camera view')
col_camera = st.columns(1)
is_video = False

b = st.button('Refresh')
if use_image:
    # live camera
    if 'video_camera_file' in st.session_state:
        camera_file = st.session_state['video_camera_file']
    else:  # select a file (video or still images) to process & display
        camera_file = st.file_uploader(label='Upload image', type=['png', 'jpg', 'jpeg', 'mp4'])
else:
    # live camera
    if 'video_camera_file' in st.session_state:
        del st.session_state['video_camera_file']
    camera_file = camera_input_live()
    if 'video_camera_file' in st.session_state:
        del st.session_state['video_camera_file']

# capturing from a file (video or still images)
if camera_file is not None:
    if is_video_file(camera_file):
        is_video = True
        # print(f"its a video file! {camera_file.name}")
        # still images
        if 'video_camera_file' in st.session_state:
            camera_file = st.session_state['video_camera_file']
            vidcap = st.session_state['vidcap']
        else:  # video from a file
            vidcap = cv2.VideoCapture(camera_file.name)
            st.session_state['video_camera_file'] = camera_file
            st.session_state['vidcap'] = vidcap
        success, frame = vidcap.read()
        for i in range(video_frames_to_skip):
            success, frame = vidcap.read()
        if frame is None:
            print("end of Video!")
            vidcap = cv2.VideoCapture(camera_file.name)
            st.session_state['vidcap'] = vidcap
            success, frame = vidcap.read()
        img = Image.fromarray(frame)
        time.sleep(0.1)
    else:
        # print("its an image!")
        img = Image.open(camera_file)

    img = img.convert('RGB')
    new_image2 = img

    if enhance_brightness != 0.0:
        new_image2 = ImageEnhance.Brightness(
            new_image2).enhance(enhance_brightness)
    if enhance_contrast != 0.0:
        new_image2 = ImageEnhance.Contrast(
            new_image2).enhance(enhance_contrast)
    if enhance_sharpness != 0.0:
        new_image2 = ImageEnhance.Sharpness(
            new_image2).enhance(enhance_sharpness)
    if enhance_color != 0.0:
        new_image2 = ImageEnhance.Color(new_image2).enhance(enhance_color)
    if use_my_filter:
        new_image2.putdata(my_filter(new_image2.getdata()))

    # print(f"original enhance_color={enhance_color}, new={tune_based_on_uv(enhance_color, get_current_uv())}")
    new_image2 = ImageEnhance.Color(
        new_image2).enhance(tune_based_on_uv(enhance_color, get_current_uv()))

    st.image(new_image2, width=500, caption='Camera view')


if use_vibrate:
    html_string = '''
    <h1>Vibrate!!!</h1>    
    <script language="javascript">
        Navigator.vibrate(500);
        console.log("vibrate is ON");
    </script>
    '''
    components.html(html_string)  # JavaScript works

# st.markdown('### UV Index')
try:
    uv_data['date'] = uv_data['date'].apply(lambda d: datetime.strptime(d, '%M:%S.%f'))
    current_time_seconds = get_current_time()
    # print(f"current_time_seconds={current_time_seconds}")
    current_uv = uv_data['uv'][current_time_seconds * 10]
    st.session_state['current_uv'] = current_uv
    # assuming the uv file have 10 samples per second
    chart = st.line_chart(uv_data[current_time_seconds * 10:], x="date", y="uv", height=200)
except:
    print("End of UV data!")
    reset_current_time()

sound_time_seconds = get_current_time() % sound_data['soundlevel'].count()
current_sound_level = sound_data['soundlevel'][sound_time_seconds]
st.session_state['current_sound_level'] = current_sound_level
sound_data['date'] = sound_data['date'].apply(lambda d: datetime.strptime(d, '%M:%S.%f'))
data = sound_data[sound_time_seconds:]
sound_chart = st.line_chart(data, x="date", y="soundlevel", height=200)

# st.markdown('### Metrics')
col1, col2, col3 = st.columns(3)
col1.metric("UV Index", current_uv)
col2.metric("Sound [dB]", f"{current_sound_level:.1f}")
# col3.metric("Humidity", "86%", "4%")

if is_video:
    refresher(0.05)
else:
    time.sleep(0.05)
