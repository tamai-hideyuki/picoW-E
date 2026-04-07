import math
import config


def calculate_altitude(pressure, temperature_celsius, humidity=None):
    """気圧・気温・湿度から高度を計算する

    Args:
        pressure: 測定気圧 (hPa)
        temperature_celsius: 測定気温 (℃)
        humidity: 測定湿度 (%) - 指定すると仮想温度で補正

    Returns:
        高度 (m)
    """
    sea_level_pressure = config.SEA_LEVEL_PRESSURE
    lapse_rate = config.TEMPERATURE_LAPSE_RATE
    gas_constant = config.UNIVERSAL_GAS_CONSTANT
    gravity = config.GRAVITATIONAL_ACCELERATION
    molar_mass = config.AIR_MOLAR_MASS

    temperature_kelvin = temperature_celsius + 273.15

    # 湿度補正: 仮想温度を使う
    if humidity is not None and humidity > 0:
        temperature_kelvin = _calculate_virtual_temperature(
            temperature_kelvin, pressure, humidity)

    # 国際標準大気の気圧高度公式
    exponent = (gas_constant * lapse_rate) / (gravity * molar_mass)
    altitude = (temperature_kelvin / lapse_rate) * (
        (sea_level_pressure / pressure) ** exponent - 1)

    return altitude


def _calculate_virtual_temperature(temperature_kelvin, pressure, humidity):
    """仮想温度を計算（湿った空気は軽いため補正が必要）

    Args:
        temperature_kelvin: 気温 (K)
        pressure: 気圧 (hPa)
        humidity: 相対湿度 (%)

    Returns:
        仮想温度 (K)
    """
    # 飽和水蒸気圧 (hPa) - Tetens の式
    temperature_celsius = temperature_kelvin - 273.15
    saturation_vapor_pressure = 6.1078 * math.exp(
        (17.27 * temperature_celsius) / (temperature_celsius + 237.3))

    # 実際の水蒸気圧
    actual_vapor_pressure = saturation_vapor_pressure * (humidity / 100.0)

    # 仮想温度: Tv = T / (1 - (e/P)(1 - 0.622))
    virtual_temperature = temperature_kelvin / (
        1.0 - (actual_vapor_pressure / pressure) * (1.0 - 0.622))

    return virtual_temperature


def format_altitude(altitude_meters):
    """高度を見やすい文字列に整形"""
    if abs(altitude_meters) < 1:
        return "{:.1f} cm".format(altitude_meters * 100)
    elif abs(altitude_meters) < 1000:
        return "{:.1f} m".format(altitude_meters)
    else:
        return "{:.2f} km".format(altitude_meters / 1000)
