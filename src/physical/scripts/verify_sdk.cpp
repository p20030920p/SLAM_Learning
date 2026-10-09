// Validate Python conversion against the unchanged official SDK2 inline API.
#include "unitree_lidar_utilities.h"
#include <cstring>
#include <iterator>

int main(int argc, char** argv) {
    using namespace unilidar_sdk2;
    if (argc != 3) return 2;
    std::ifstream input(argv[1], std::ios::binary);
    std::vector<uint8_t> raw((std::istreambuf_iterator<char>(input)), {});
    if (raw.size() != sizeof(LidarPointDataPacket)) return 3;
    LidarPointDataPacket packet{};
    std::memcpy(&packet, raw.data(), raw.size());
    if (crc32(raw.data()+sizeof(FrameHeader), raw.size()-sizeof(FrameHeader)-sizeof(FrameTail)) != packet.tail.crc32) return 4;
    PointCloudUnitree cloud;
    parseFromPacketToPointCloud(cloud, packet, false, 0, 100);
    std::ofstream output(argv[2], std::ios::binary);
    output.write(reinterpret_cast<char*>(cloud.points.data()), cloud.points.size()*sizeof(PointUnitree));
    std::cout << "{\"packet_bytes\":" << raw.size() << ",\"point_bytes\":" << sizeof(PointUnitree)
              << ",\"points\":" << cloud.points.size() << ",\"official_crc_pass\":true}" << std::endl;
    return output.good() ? 0 : 5;
}
