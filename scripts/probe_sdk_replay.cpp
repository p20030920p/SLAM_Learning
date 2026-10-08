// Feed through a Linux pseudo-terminal, never a physical sensor.
#include "unitree_lidar_sdk.h"
#include <chrono>
int main(int argc,char** argv) {
    using namespace unilidar_sdk2;
    if(argc<2 || argc>3) return 2;
    bool system_time=argc==3 && std::string(argv[2])=="system";
    auto* reader=createUnitreeLidarReader();
    if(reader->initializeSerial(argv[1],4000000,18,system_time)) return 3;
    int imu_count=0, cloud_count=0;
    double first_stamp=0,last_stamp=0,first_host=0,last_host=0;
    auto start=std::chrono::steady_clock::now();
    while(std::chrono::duration<double>(std::chrono::steady_clock::now()-start).count()<8) {
        int kind=reader->runParse();
        if(kind==LIDAR_IMU_DATA_PACKET_TYPE) {
            LidarImuData imu;
            if(reader->getImuData(imu)) {
                double stamp=imu.info.stamp.sec+imu.info.stamp.nsec*1e-9;
                double host=std::chrono::duration<double>(std::chrono::steady_clock::now()-start).count();
                if(!imu_count) {
                    first_stamp=stamp;
                    first_host=host;
                    std::cout<<std::setprecision(15)<<"first_sdk_imu_stamp="<<stamp
                             <<" use_system_timestamp="<<system_time
                             <<" gyro="<<imu.angular_velocity[0]<<","<<imu.angular_velocity[1]<<","<<imu.angular_velocity[2]<<std::endl;
                }
                last_stamp=stamp;
                last_host=host;
                ++imu_count;
            }
        }
        if(kind==LIDAR_POINT_DATA_PACKET_TYPE) {
            PointCloudUnitree cloud;
            if(reader->getPointCloud(cloud)) ++cloud_count;
        }
        if(imu_count>=1000 && cloud_count>0) break;
    }
    reader->closeSerial();
    std::cout<<"imu_count="<<imu_count<<" aggregated_cloud_count="<<cloud_count
             <<" sdk_imu_stamp_span="<<last_stamp-first_stamp
             <<" measured_host_span="<<last_host-first_host<<std::endl;
    return imu_count>=1000 && cloud_count>0 ? 0 : 4;
}
