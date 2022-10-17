import json
import os

from easyocr import Reader
from PIL import ImageGrab, ImageChops, Image
from tkinter import Tk, Canvas
import asyncio

BBOX = (1440, 100, 1810, 600)
IMG_PATH = 'tmp/prev_screenshot.jpg'
FILE_PATH = 'result.json'


async def form_data(info):
    data = []
    while len(info) > 0:
        current_key = info.pop(0)
        current_line = [current_key]
        i = 0
        while i < len(info):
            if abs(info[i][0][0][1] - current_key[0][0][1]) <= 5 and abs(info[i][0][2][1] - current_key[0][2][1]) <= 5:
                current_line.append(info[i])
                info.pop(i)
            i += 1
        data.append([elem[1] for elem in current_line])
    return data


async def save_data(data):
    temporary = {}
    for i in range(1, len(data)):
        if len(data[i]) == 1:
            temporary.update({data[i][0]: 0})
        elif len(data[i]) == 2:
            temporary.update({data[i][0]: data[i][1]})
        else:
            key = data[i].pop(0)
            temporary.update({key: data[i]})
    file = open(FILE_PATH, 'r+')
    if os.stat(FILE_PATH).st_size != 0:
        payload = json.load(file)
    else:
        payload = {}
    payload.update({data[0][0]: temporary})
    file.seek(0)
    json.dump(payload, file)


async def compare_words(word1, word2):
    counter = 0
    for i in range(min(len(word1), len(word2))):
        if word1[i] == word2[i]:
            counter += 1
    return counter / max(len(word1), len(word2)) * 100


async def eval_difference(orig, new):
    result = []
    for i in range(len(orig)):
        vector = []
        for j in range(len(new)):
            vector.append(await compare_words(orig[i], new[j]))
        result.append(max(vector))
    return sum(result) / len(orig)


async def to_bw(image):
    fn = lambda x: 255 if x > 165 else 0
    converted_image = image.convert('L').point(fn, mode='1')
    return converted_image


async def main():
    open(FILE_PATH, 'w+')

    first_screenshot = ImageGrab.grab(bbox=BBOX)
    first_screenshot = await to_bw(first_screenshot)
    first_screenshot.save(IMG_PATH)

    reader = Reader(lang_list=['ru', 'en'], gpu=True)

    window = Tk()
    window.wm_attributes('-fullscreen', True)
    window.wm_attributes('-topmost', True)
    window.wm_attributes('-transparentcolor', '#ab23ff')
    canva = Canvas(width=window.winfo_screenwidth(), height=window.winfo_screenheight(), bg='#ab23ff')
    canva.pack()

    prev_info = ['1']

    while True:

        await asyncio.sleep(10)

        canva.delete('all')
        window.update()

        current_screenshot = ImageGrab.grab(bbox=BBOX)
        current_screenshot = await to_bw(current_screenshot)
        prev_screenshot = Image.open(IMG_PATH)

        if ImageChops.difference(current_screenshot, prev_screenshot).getbbox():
            current_screenshot.save(IMG_PATH)

            results = reader.readtext(IMG_PATH)
            if len(results) == 0:
                canva.create_text(500, 100, text='No data', fill='white', font='Calibri 23')
                window.update()
                continue

            current_info = [elem[1] for elem in results]
            concurrence = await eval_difference(prev_info, current_info)

            if concurrence < 90:
                prev_info = current_info
            else:
                canva.create_text(500, 100, text='Please next', fill='white', font='Calibri 23')

                data = await form_data(results)
                await save_data(data)

            for elem in results:
                bbox = elem[0]
                x1, y1 = bbox[0]
                x2, y2 = bbox[2]
                x1 = (x1 + BBOX[0]) / 1.5
                y1 = (y1 + BBOX[1]) / 1.5
                x2 = (x2 + BBOX[0]) / 1.5
                y2 = (y2 + BBOX[1]) / 1.5
                canva.create_rectangle(x1, y1, x2, y2, outline='red')
            window.update()

        else:
            continue


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
