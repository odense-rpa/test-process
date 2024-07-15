import logging
import time

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

if __name__ == '__main__':
    print('Hello World!')
    
    logger.error("This is an error message")
    time.sleep(10)    
