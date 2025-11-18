

import  unittest 

from mathutils import Vector

from ..editing.transforms import Transform


def iiif_to_blender_axes( seq ):
    return ( seq[0], -seq[2], seq[1] )
    
def blender_to_iiif_axes( seq ):
    return ( seq[0],  seq[2], -seq[1] )
        
class TransformTest(unittest.TestCase):

    
    def assertAmostEqualCoordinates( self, first, second, *tup, **keyw):
        
        for i in range(3):
            msg = keyw.get("msg","unequal coordinates")
            self.assertAlmostEqual( first[i], second[i], places=6, msg=msg )
        return
        
    def test10(self):
        "basic: iiif_to_blender_transform"

        rotate = Transform.from_iiif_dict(
            {
                "type" : "RotateTransform",
                "y"    : 90.0
            }
        )
        
        test_in  = (1.0, 0.0, 0.0 )
        exact_test_out = (0.0,0.0, -1.0)
        
        blender_vec = Vector( iiif_to_blender_axes(test_in))        
        blender_rotated_vec = rotate.applyToCoordinate(blender_vec)
        
        test_out = blender_to_iiif_axes( blender_rotated_vec.to_tuple() )
    
        self.assertAmostEqualCoordinates(exact_test_out, test_out)
        
suite=unittest.TestSuite()
suite.addTest( unittest.defaultTestLoader.loadTestsFromTestCase( TransformTest )  )