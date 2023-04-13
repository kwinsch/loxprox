import numpy as np

# Convert RGB to XYZ using a D65 whitepoint
def rgb_to_xyz(rgb):
    rgb = np.array(rgb)

    # RGB to XYZ matrix, assuming sRGB (D65)
    M = np.array([
        [0.4124564, 0.3575761, 0.1804375],
        [0.2126729, 0.7151522, 0.0721750],
        [0.0193339, 0.1191920, 0.9503041]
    ])
    rgb_linear = np.where(rgb <= 0.04045, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4)
    xyz = np.dot(M, rgb_linear)
    return xyz

# Convert XYZ to RGB using a D65 whitepoint
def xyz_to_rgb(xyz):
    xyz = np.array(xyz)

    # XYZ to RGB matrix, assuming sRGB (D65)
    M_inv = np.array([
            [ 3.2404542, -1.5371385, -0.4985314],
            [-0.9692660,  1.8760108,  0.0415560],
            [ 0.0556434, -0.2040259,  1.0572252]
        ])
    rgb_linear = np.dot(M_inv, xyz)
    rgb = np.where(rgb_linear <= 0.0031308, 12.92 * rgb_linear, 1.055 * (rgb_linear ** (1 / 2.4)) - 0.055)
    rgb = np.clip(rgb, 0, 1)
    return rgb

# Convert Color Temperature and Brightness to XYZ
def ct_brightness_to_xyz(color_temperature, brightness):
    if color_temperature < 4000:
        x = -0.2661239 * (10**9) / color_temperature**3 + 0.2343580 * (10**6) / color_temperature**2 + 0.8776956 * (10**3) / color_temperature + 0.179910
    else:
        x = -3.0258469 * (10**9) / color_temperature**3 + 2.1070379 * (10**6) / color_temperature**2 + 0.2226347 * (10**3) / color_temperature + 0.240390
    y = -1.1063814 * x**3 - 1.34811020 * x**2 + 2.18555832 * x - 0.20219683
    Y = brightness
    X = (x * Y) / y
    Z = (1 - x - y) * Y / y
    return [X, Y, Z]

# Convert XYZ to Color Temperature and Brightness
def xyz_to_ct_brightness(xyz):
    def delta_e_squared(temp, xyz):
        xyz_estimated = ct_brightness_to_xyz(temp, xyz[1])
        delta = np.array(xyz) - np.array(xyz_estimated)
        return np.dot(delta, delta)

    xyz = np.array(xyz)
    min_error = float('inf')
    color_temperature_estimate = 0
    temperature_range = np.arange(1000, 40001, 10)
    for temp in temperature_range:
        error = delta_e_squared(temp, xyz)
        if error < min_error:
            min_error = error
            color_temperature_estimate = temp

    color_temperature = color_temperature_estimate
    brightness = xyz[1]
    return color_temperature, brightness

# Convert Brightness to XYZ using a D65 whitepoint
def brightness_to_xyz_neutral_white(brightness):
    d65_white = np.array([0.95047, 1.00000, 1.08883])
    xyz = d65_white * brightness
    return xyz

# Convert XYZ to Normalized Brightness using a D65 whitepoint
def xyz_to_normalized_brightness(xyz):
    d65_white_y = 1.00000
    brightness = xyz[1] / d65_white_y
    return brightness

# Convert XYZ to xy
def xyz_to_xy(xyz):
    X, Y, Z = xyz
    x = X / (X + Y + Z)
    y = Y / (X + Y + Z)
    return x, y


