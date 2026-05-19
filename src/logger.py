import time
from .config import DEBUG, LOGS_DIR
from .console_utils import cprint


class Logger:
    _log_file_path = None

    @classmethod
    def _get_log_file(cls):
        if cls._log_file_path is None:
            log_dir = LOGS_DIR
            log_dir.mkdir(exist_ok=True)
            cls._log_file_path = log_dir / "debug.log"
        return cls._log_file_path

    def __init__(self, name: str):
        self.name = name

    def _log(self, level: str, msg: str, color: str = None):
        if not DEBUG:
            return
        timestamp = (
            time.strftime("%Y-%m-%d %H:%M:%S")
            + "."
            + str(int(time.time() * 1000 % 1000)).zfill(3)
        )
        prefix = "[{}] [{}] [{}]".format(timestamp, self.name, level)
        full_msg = prefix + " " + msg

        # вывод в консоль (цветной)
        if color:
            cprint(full_msg, color=color)
        else:
            print(full_msg)

        # запись в файл (без цвета)
        try:
            log_file = self._get_log_file()
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(full_msg + "\n")
        except Exception:
            pass  # игнорируем ошибки записи в файл

    def debug(self, msg: str):
        self._log("DBG", msg, "bright_black")

    def info(self, msg: str):
        self._log("INFO", msg, "cyan")

    def warning(self, msg: str):
        self._log("WARN", msg, "yellow")

    def error(self, msg: str):
        self._log("ERROR", msg, "red")
