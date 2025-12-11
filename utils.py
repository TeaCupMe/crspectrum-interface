import numpy
def clamp(n, smallest, largest): return max(smallest, min(n, largest))

# def YUV2RGB(y, u, v):
#     r = y + (1.370705 * (v - 128))
#     g = y - (0.698001 * (v - 128)) - (0.337633 * (u - 128))
#     b = y + (1.732446 * (u - 128))
#     r = clamp(r, 0, 255)
#     g = clamp(g, 0, 255)
#     b = clamp(b, 0, 255)
#     return (r, g, b)

def YUV2RGB( yuv ):
      
    m = numpy.array([[ 1.0, 1.0, 1.0],
                 [-0.000007154783816076815, -0.3441331386566162, 1.7720025777816772],
                 [ 1.4019975662231445, -0.7141380310058594 , 0.00001542569043522235] ])
    
    rgb = numpy.dot(yuv,m)
    rgb[:,:,0]-=179.45477266423404
    rgb[:,:,1]+=135.45870971679688
    rgb[:,:,2]-=226.8183044444304
    return rgb


def YUV2RGB_INT(y, u, v):
    r = y + (1.370705 * (v - 128))
    g = y - (0.698001 * (v - 128)) - (0.337633 * (u - 128))
    b = y + (1.732446 * (u - 128))
    r = clamp(r, 0, 255)
    g = clamp(g, 0, 255)
    b = clamp(b, 0, 255)
    return (int(r), int(g), int(b))
    
def YUV2BGR_INT(y, u, v):
    r = y + (1.370705 * (v - 128))
    g = y - (0.698001 * (v - 128)) - (0.337633 * (u - 128))
    b = y + (1.732446 * (u - 128))
    r = clamp(r, 0, 255)
    g = clamp(g, 0, 255)
    b = clamp(b, 0, 255)
    return (int(b), int(g), int(r))
    
def YUV2GBR_INT(y, u, v):
    r = y + (1.370705 * (v - 128))
    g = y - (0.698001 * (v - 128)) - (0.337633 * (u - 128))
    b = y + (1.732446 * (u - 128))
    r = clamp(r, 0, 255)
    g = clamp(g, 0, 255)
    b = clamp(b, 0, 255)
    return (int(g), int(b), int(r))