SSID = "Wi-Fi名"
PASSWORD = "パスワード"

SENSOR_INTERVAL_SEC = 2       # データ取得間隔（秒）
AGGREGATE_INTERVAL_SEC = 60   # 集約間隔（秒）：1分平均をファイルに保存

# リングバッファサイズ（直近データをRAMに保持する件数）
RING_BUFFER_SIZE = 300  # 2秒 x 300 = 10分間

# データ保存先ディレクトリ（Pico W内のパス）
DATA_DIR = "/data"

I2C_SDA_PIN = 0
I2C_SCL_PIN = 1

# タイムゾーン（UTC+9 = 日本標準時）
TZ_OFFSET = 9 * 3600

SERVER_PORT = 80
