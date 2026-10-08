// Batch actual CRC-valid packets through unchanged official SDK2 utilities.
#include "unitree_lidar_utilities.h"
#include <cstring>

int main(int argc,char** argv) {
    using namespace unilidar_sdk2;
    static_assert(sizeof(LidarPointDataPacket)==1044,"Unexpected SDK packet layout");
    static_assert(sizeof(PointUnitree)==24,"Unexpected SDK point layout");
    if(argc!=3) return 2;
    std::ifstream input(argv[1],std::ios::binary);
    std::ofstream output(argv[2],std::ios::binary);
    if(!input || !output) return 3;
    LidarPointDataPacket packet{};
    uint64_t lines=0,total=0;
    while(input.read(reinterpret_cast<char*>(&packet),sizeof(packet))) {
        auto* bytes=reinterpret_cast<uint8_t*>(&packet);
        if(packet.header.packet_type!=LIDAR_POINT_DATA_PACKET_TYPE ||
           packet.header.packet_size!=sizeof(packet) || packet.data.point_num>300 ||
           std::memcmp(bytes,"\x55\xaa\x05\x0a",4)!=0 ||
           packet.tail.tail[0]!=0 || packet.tail.tail[1]!=255) return 4;
        if(crc32(bytes+sizeof(FrameHeader),sizeof(packet)-sizeof(FrameHeader)-sizeof(FrameTail))!=packet.tail.crc32) return 5;
        PointCloudUnitree cloud;
        parseFromPacketToPointCloud(cloud,packet,false,0,100);
        uint32_t count=cloud.points.size();
        output.write(reinterpret_cast<char*>(&count),sizeof(count));
        output.write(reinterpret_cast<char*>(cloud.points.data()),count*sizeof(PointUnitree));
        ++lines; total+=count;
    }
    if(input.gcount()!=0 || !output) return 6;
    std::cout<<"{\"lines\":"<<lines<<",\"points\":"<<total<<",\"point_bytes\":"<<sizeof(PointUnitree)<<"}"<<std::endl;
    return lines ? 0 : 7;
}
