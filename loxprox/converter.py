import re

def extract_id(s):
    match = re.search(r'ph(\d+)', s)
    if match:
        return int(match.group(1))
    else:
        return None

def convert_received_data(data):
    try:
        control_id, payload = data.split(".")
        payload = int(payload)
    except ValueError:
        return None

    if 0 <= payload <= 100100100:
        return control_id, "RGB", convert_to_rgb(payload)
    elif 200002700 <= payload <= 201006500:
        return control_id, "CCT", convert_to_cct(payload)
    else:
        return None


def convert_to_rgb(payload):
    blue = payload // 1000000
    green = (payload // 1000) % 1000
    red = payload % 1000

    return (
        int(red * 255 / 100),
        int(green * 255 / 100),
        int(blue * 255 / 100),
    )


def convert_to_cct(payload):
    brightness = (payload // 10000) % 1000
    color_temperature = payload % 10000

    return brightness, color_temperature

def test_convert_to_rgb():
    assert convert_to_rgb(100100100) == (255, 255, 255)
    assert convert_to_rgb(0) == (0, 0, 0)
    assert convert_to_rgb(100000000) == (255, 0, 0)
    assert convert_to_rgb(100100000) == (255, 255, 0)
    assert convert_to_rgb(100000100) == (255, 0, 255)
    assert convert_to_rgb(100100100) == (255, 255, 255)
    assert convert_to_rgb(100000000) == (255, 0, 0)
    assert convert_to_rgb(1) == (2,0,0) 
    assert convert_to_rgb(100) == (255,0,0)
    assert convert_to_rgb(1000) == (0,2,0) 
    assert convert_to_rgb(10000) == (0,25,0)
    assert convert_to_rgb(100000) == (0,255,0)
    assert convert_to_rgb(1000000) == (0,0,2)
    assert convert_to_rgb(10000000) == (0,0,25)
    assert convert_to_rgb(100000000) == (0,0,255)
