
from bpy.types import  Context, Operator

from typing import Set
import unittest
from . import transforms


# Achieving the formatting I like
class TextTestResult(unittest.TextTestResult):
    def getDescription(self, test):
        return test.shortDescription()

class TextTestRunner(unittest.TextTestRunner):
    resultclass = TextTestResult                    # type: ignore


class RunUnitTests(Operator):
    bl_idname = "iiif.unittest"
    bl_label = "Run Unit Tests"

    def execute(self, context: Context) -> Set[str]:
    
        suite=unittest.TestSuite()
        suite.addTest(transforms.suite)
        TextTestRunner(verbosity=2).run(suite)
        return {"FINISHED"}