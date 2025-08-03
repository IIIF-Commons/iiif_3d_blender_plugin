

import  unittest 

from ..editing.transforms import iiif_to_blender_transform

class TransformTest(unittest.TestCase):

    def test10(self):
        "basic: iiif_to_blender_transform"
        
        testT = {
            "type" : "RotateTransform",
            "y"    : 30.0
        }
        res = iiif_to_blender_transform(testT)
        self.assertEqual(2, len(res))
        
suite=unittest.TestSuite()
suite.addTest( unittest.defaultTestLoader.loadTestsFromTestCase( TransformTest )  )