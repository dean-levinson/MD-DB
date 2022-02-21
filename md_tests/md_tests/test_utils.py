import shutil
import os
from collections import namedtuple

ClientCreds = namedtuple("ClientCreds", ['id', 'password'])
TEST_DIR = os.path.abspath('md_tests/')


class TestResource(object):
    RESOURCE_DIR = os.path.join(TEST_DIR, "resources")

    def __init__(self, resource_name, dst_relative_dir=None):
        self.resource_name = resource_name
        self.resource_path = os.path.join(self.RESOURCE_DIR, self.resource_name)

        if not dst_relative_dir:
            self.dst_path = os.path.join(TEST_DIR, self.resource_name)
        else:
            self.dst_path = os.path.join(TEST_DIR, dst_relative_dir, self.resource_name)

    def copy_to_test(self):
        shutil.copyfile(self.resource_path, self.dst_path)

    def remove(self):
        os.remove(self.dst_path)

    def exist(self):
        return os.path.exists(self.dst_path)

    def __enter__(self):
        if self.exist():
            self.remove()

        self.copy_to_test()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.exist():
            # self.remove()
            pass
