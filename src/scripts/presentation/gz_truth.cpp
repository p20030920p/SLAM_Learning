// Read independent simulator model truth with Pose_V's top-level timestamp.
// ros_gz's TFMessage conversion can omit model names and this timestamp.
#include <fstream>
#include <iomanip>
#include <iostream>
#include <mutex>
#include <string>
#include <gz/msgs/pose_v.pb.h>
#include <gz/transport/Node.hh>

int main(int argc, char **argv) {
  if (argc != 4) {
    std::cerr << "usage: gz_truth TOPIC MODEL OUTPUT_JSONL\n";
    return 2;
  }
  std::ofstream output(argv[3]);
  if (!output) return 3;
  output << std::setprecision(17);
  const std::string model = argv[2];
  std::mutex mutex;
  gz::transport::Node node;
  auto callback = [&](const gz::msgs::Pose_V &message) {
    const auto &stamp = message.header().stamp();
    const double time = stamp.sec() + stamp.nsec() * 1e-9;
    for (const auto &pose : message.pose()) {
      if (pose.name() != model) continue;
      const auto &p = pose.position();
      const auto &q = pose.orientation();
      std::lock_guard<std::mutex> guard(mutex);
      output << "{\"stamp_s\":" << time << ",\"model\":\"" << model
             << "\",\"xyz\":[" << p.x() << ',' << p.y() << ',' << p.z()
             << "],\"xyzw\":[" << q.x() << ',' << q.y() << ',' << q.z()
             << ',' << q.w() << "]}\n" << std::flush;
    }
  };
  if (!node.Subscribe<gz::msgs::Pose_V>(argv[1], callback)) return 4;
  gz::transport::waitForShutdown();
  return 0;
}
