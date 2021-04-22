import numpy as np
import requests
import sys
import tensorflow as tf


def reshape_image(img: bytes, target_res: int = 256) -> bytes:
    channel_count = 3

    # decode_bmp, decode_jpeg, and decode_png
    img = tf.io.decode_image(img, expand_animations=False)
    h, w = tf.shape(img)[0], tf.shape(img)[1]
    s_min = tf.minimum(h, w)

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


def test_reshape_image(url):

    image = requests.get(url).content

    reshaped_image = reshape_image(image)
    print(f'size: {sys.getsizeof(reshaped_image)} bytes')

    array = np.frombuffer(reshaped_image, dtype=np.uint8).reshape(256, 256, 3)

    img = tf.keras.preprocessing.image.array_to_img(
        array, data_format=None, scale=True, dtype=None
    )

    img.show()


if __name__ == '__main__':

    test_reshape_image(url='https://upload.wikimedia.org/wikipedia/commons/b/b7/Tartar.jpg')
