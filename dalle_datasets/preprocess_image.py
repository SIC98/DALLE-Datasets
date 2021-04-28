from cairosvg import svg2png
import numpy as np
import os
import requests
import sys
import tensorflow as tf
import tensorflow_io as tfio
from typing import Union
import uuid


def reshape_image(img: bytes, mime: str, target_res: int = 256) -> Union[None, bytes]:

    if mime == 'image/svg+xml':
        file_name = str(uuid.uuid4())
        file = f'./tmp/{file_name}'
        svg2png(bytestring=img, write_to=file)
        img = tf.io.read_file(file)
        os.remove(file)
        img = tf.io.decode_png(img)[:, :, :3]

    elif mime == 'image/tiff':
        img = tfio.experimental.image.decode_tiff(img)[:, :, :3]

    elif mime in ['image/jpeg', 'image/png', 'image/gif']:
        # decode_bmp, decode_jpeg, and decode_png
        img = tf.io.decode_image(img, expand_animations=False)

    elif mime in ['image/x-xcf', 'image/webp']:
        return None

    else:
        raise ValueError(f'wrong mime value: {mime}')

    channel_count = 3

    h, w = tf.shape(img)[0], tf.shape(img)[1]
    s_min = tf.minimum(h, w)

    if s_min < target_res:
        return None

    off_h = tf.random.uniform(
        [],
        3 * (h-s_min) // 8,
        tf.maximum(3 * (h - s_min) // 8 + 1, 5 * (h - s_min) // 8),
        dtype=tf.int32
    )

    off_w = tf.random.uniform(
        [],
        3 * (w - s_min) // 8,
        tf.maximum(3 * (w - s_min) // 8 + 1, 5 * (w - s_min) // 8),
        dtype=tf.int32
    )

    # Random full square crop.
    img = tf.image.crop_to_bounding_box(img, off_h, off_w, s_min, s_min)
    t_max = tf.minimum(s_min, round(9 / 8 * target_res))
    t = tf.random.uniform([], target_res, t_max + 1, dtype=tf.int32)
    img = tf.image.resize(img, [t, t], method=tf.image.ResizeMethod.AREA)
    img = tf.cast(tf.math.rint(tf.clip_by_value(img, 0, 255)), tf.dtypes.uint8)

    # We don't use hflip aug since the image may contain text.
    return tf.image.random_crop(img, 2 * [target_res] + [channel_count]).numpy().tobytes()


def test_reshape_image(url, mime):

    image = requests.get(url).content

    reshaped_image = reshape_image(image, mime)

    if reshaped_image is None:
        return

    print(f'size: {sys.getsizeof(reshaped_image)} bytes')

    array = np.frombuffer(reshaped_image, dtype=np.uint8).reshape(256, 256, 3)

    img = tf.keras.preprocessing.image.array_to_img(
        array, data_format=None, scale=True, dtype=None
    )

    img.show()


if __name__ == '__main__':

    test_reshape_image('https://upload.wikimedia.org/wikipedia/commons/7/7f/Honor%C3%A9_Gabriel_Riqueti_de_Mirabeau%2C'
                       '_pained_by_Joseph_Boze.jpg', 'image/jpeg')
    test_reshape_image('https://upload.wikimedia.org/wikipedia/commons/3/38/Alpha_Intercalated_Cell_Cartoon.svg',
                       'image/svg+xml')
    test_reshape_image('https://upload.wikimedia.org/wikipedia/commons/0/00/Phelps-family-english-shield.gif',
                       'image/gif')
    test_reshape_image('https://upload.wikimedia.org/wikipedia/commons/0/08/Sanborn_Fire_Insurance_Map_from_Detroit%2C'
                       '_Wayne_County%2C_Michigan._LOC_sanborn03985_076-5.tif', 'image/tiff')
    test_reshape_image('https://upload.wikimedia.org/wikipedia/commons/9/9c/Mapa_2013.png',
                       'image/png')
