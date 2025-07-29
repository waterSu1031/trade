import logging
import os
from datetime import datetime

def setup_logger(name='strategy_logger', log_dir='logs', level=logging.INFO):
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, f"{datetime.now().strftime('%Y-%m-%d')}.log")

    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.handlers:  # 중복 핸들러 방지
        # 콘솔 출력용 핸들러
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter('[%(levelname)s] %(message)s')
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

        # 파일 저장용 핸들러
        file_handler = logging.FileHandler(log_path)
        file_formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s')
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    return logger
