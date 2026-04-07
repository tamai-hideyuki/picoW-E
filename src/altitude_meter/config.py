SSID = "Wi-Fi名"
PASSWORD = "パスワード"

# センサー読取り間隔（秒）
SENSOR_INTERVAL_SEC = 2

# リングバッファサイズ（直近データをRAMに保持する件数）
RING_BUFFER_SIZE = 300  # 2秒 x 300 = 10分間

# I2Cピン
I2C_SDA_PIN = 0
I2C_SCL_PIN = 1

# タイムゾーン（UTC+9 = 日本標準時）
TZ_OFFSET = 9 * 3600

SERVER_PORT = 80

# === 高度計算パラメータ ===

# 海面気圧（hPa）- 正確な値を設定するほど精度が上がる
# 気象庁の発表値に合わせると ±1〜5m の精度になる
SEA_LEVEL_PRESSURE = 1013.25

# キャリブレーション: 海面気圧オフセット（hPa）
# JMA値との差を補正する。正の値 → 高度が上がる、負の値 → 高度が下がる
PRESSURE_OFFSET = 0.0

# キャリブレーション: 基準標高（m）
# 既知の設置場所の標高。Webからキャリブレーション実行時に使用
REFERENCE_ALTITUDE = 73.0

# 物理定数
TEMPERATURE_LAPSE_RATE = 0.0065          # 気温減率 (K/m)
UNIVERSAL_GAS_CONSTANT = 8.31447         # 気体定数 (J/(mol·K))
GRAVITATIONAL_ACCELERATION = 9.80665     # 重力加速度 (m/s²)
AIR_MOLAR_MASS = 0.0289644               # 空気のモル質量 (kg/mol)
