import struct
from utils import clamp

class ISParser:
    
    """Parses image properties binary struct
            uint16_t height, width;
            uint16_t vStart, hStart;
            Colorspace colorspace = EMPTY;
            uint16_t exposure;
            uint32_t length;
            uint16_t numberOfChunks;
    """
    @staticmethod
    def parseImageProperties(input: bytes) -> dict:
        output = dict()
        
        params = struct.unpack("HHHHBxHLHxx", input)
        output["height"] = params[0]
        output["width"] = params[1]
        output["vStart"] = params[2]
        output["hStart"] = params[3]
        output["colorspace"] = params[4]
        output["exposure"] = params[5]
        output["length"] = params[6]
        output["numberOfChunks"] = params[7]
        return output
    
    """Parses image chunk and return dict
    typedef struct {
        uint16_t chunkID, payloadLength;
        bool isLastChunk;
        uint8_t payload[240];
        uint8_t checksum;
    } Chunk;
    """
    @staticmethod
    def parseImageChunk(input: bytes) -> dict:
        output = dict()
        
        params = struct.unpack("HH?240BB", input)
        output["chunkID"] = params[0]
        output["payloadLength"] = params[1]
        output["isLastChunk"] = params[2]
        output["payload"] = params[3:243]
        output["checksum"] = params[243]
        return output
    
    