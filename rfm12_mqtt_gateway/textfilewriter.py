import os
import os.path
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class TextFileWriter(object):
    def __init__(self, path, prefix, header=None):
        self.path = path
        self.pattern = "%Y/%m/{}-%Y-%m-%d.txt".format(prefix)
        self.header = header
        self.file = None

    def __del__(self):
        if self.file is not None:
            self.file.close()

    def writeline(self, line):
        fn = os.path.join(self.path,
                          format(datetime.utcnow(), self.pattern))
        if self.file is None or self.file.name != fn:
            if self.file is not None:
                self.file.close()
            if not os.path.exists(os.path.dirname(fn)):
                os.makedirs(os.path.dirname(fn))
            file_already_existed = os.path.exists(fn)
            self.file = open(fn, 'at')
            if self.header and not file_already_existed:
                self.file.write(self.header + '\n')
            logger.info("Opened %s file %s",
                        "existing" if file_already_existed else "new",
                        fn)
        self.file.write(line + '\n')
        self.file.flush()
