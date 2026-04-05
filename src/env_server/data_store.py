import os
import time
import config

def _ensure_dir(path):
    try:
        os.stat(path)
    except OSError:
        os.mkdir(path)


def _date_str(timestamp):
    t = time.localtime(timestamp + config.TZ_OFFSET)
    return "{:04d}{:02d}{:02d}".format(t[0], t[1], t[2])


def _csv_path(timestamp):
    return config.DATA_DIR + "/" + _date_str(timestamp) + ".csv"


def save_record(timestamp, temp, humi, pres):
    _ensure_dir(config.DATA_DIR)
    path = _csv_path(timestamp)
    line = "{},{:.1f},{:.1f},{:.1f}\n".format(int(timestamp), temp, humi, pres)
    with open(path, "a") as f:
        f.write(line)


def load_records(timestamp=None, max_records=1440, since=None):
    """指定日のCSVファイルからレコードを読み出す

    since: この時刻以降のレコードのみ返す（省略時は全件）
    戻り値: [(timestamp, temp, humi, pres), ...]
    """
    if timestamp is None:
        timestamp = time.time()
    path = _csv_path(timestamp)
    records = []
    try:
        with open(path, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split(",")
                ts = int(parts[0])
                if since and ts < since:
                    continue
                records.append((
                    ts,
                    float(parts[1]),
                    float(parts[2]),
                    float(parts[3]),
                ))
                if len(records) >= max_records:
                    break
    except OSError:
        pass
    return records


def list_data_files():
    _ensure_dir(config.DATA_DIR)
    try:
        return sorted(f for f in os.listdir(config.DATA_DIR) if f.endswith(".csv"))
    except OSError:
        return []


def disk_usage():
    _ensure_dir(config.DATA_DIR)
    total = 0
    try:
        for f in os.listdir(config.DATA_DIR):
            total += os.stat(config.DATA_DIR + "/" + f)[6]
    except OSError:
        pass
    return total
