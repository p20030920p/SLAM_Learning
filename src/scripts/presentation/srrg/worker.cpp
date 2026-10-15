// Transport adapter only. Registration, merging and graph optimization run in
// the unmodified author libraries; no simulator truth is accepted by this API.
#include <mapper2d.h>
#include <mapper2d_params.h>
#include <laser_message_tracker_params.h>
#include <sstream>
#include <iomanip>
#include <memory>
#include <execinfo.h>
#include <exception>
#include <unistd.h>
#include <fstream>

using namespace srrg_mapper2d;
using namespace srrg_scan_matcher;
using namespace srrg_core;

Eigen::Isometry3f pose3(float x, float y, float a) {
  Eigen::Isometry3f t=Eigen::Isometry3f::Identity();
  t.translation()<<x,y,0; t.linear()=Eigen::AngleAxisf(a,Eigen::Vector3f::UnitZ()).toRotationMatrix();
  return t;
}

int main(int argc, char** argv) {
  // Author graph code also writes to stdout. Keep diagnostics out of the wire.
  const int wire=dup(STDOUT_FILENO);
  dup2(STDERR_FILENO,STDOUT_FILENO);
  std::ofstream protocol("/proc/self/fd/"+std::to_string(wire));
  std::set_terminate([](){ void* frames[50]; int n=backtrace(frames,50); backtrace_symbols_fd(frames,n,2); std::abort(); });
  LaserMessageTracker tracker;
  LaserMessageTrackerParams tp(&tracker); tp.applyParams();
  SimpleGraph graph;
  Mapper2D mapper(&tracker,&graph);
  bool graph_merge=false; std::string prior;
  for(int i=1;i<argc;++i) { if(std::string(argv[i])=="--graph-merge") graph_merge=true; else prior=argv[i]; }
  Mapper2DParams mp(&mapper); mp.setUseMerger(graph_merge); mp.applyParams();
  const bool multi_session=!prior.empty();
  if(multi_session) { graph.loadGraph(prior.c_str()); mapper.setMultiSession(true); }
  bool initialized=false; int seq=0;
  std::string line;
  protocol<<std::setprecision(9);
  while (std::getline(std::cin,line)) {
    std::istringstream in(line); char command; in>>command;
    if(command=='F') { if(initialized) mapper.finishMapping(); }
    else if(command=='S') {
      double stamp; float x,y,a,ex,ey,ea,lo,hi,inc,rmin,rmax; size_t n;
      in>>stamp>>x>>y>>a>>ex>>ey>>ea>>lo>>hi>>inc>>rmin>>rmax>>n;
      std::vector<float> ranges(n); for(auto& r:ranges) in>>r;
      if(!in) return 2;
      LaserMessage laser("/scan","lidar_link",seq++,stamp);
      laser.setRanges(ranges); laser.setMinAngle(lo); laser.setMaxAngle(hi);
      laser.setAngleIncrement(inc); laser.setMinRange(rmin); laser.setMaxRange(rmax);
      laser.setOdometry(pose3(x,y,a)); laser.setOffset(pose3(ex,ey,ea));
      if(!initialized) { mapper.init(&laser); if(multi_session) mapper.initMultiSession(); initialized=true; }
      else mapper.compute(&laser);
    } else return 3;
    Eigen::Vector3f p=t2v(mapper.estimate());
    protocol<<"{\"pose\":["<<p.x()<<","<<p.y()<<","<<p.z()<<"],\"status\":"<<int(tracker.status())
      <<",\"vertices\":"<<graph.verticesClouds().size()<<",\"points\":[";
    bool comma=false;
    auto emit=[&](const Cloud2D& c,const Eigen::Isometry2f& t){
      for(const auto& rp:c) { Eigen::Vector2f q=t*rp.point(); if(!q.allFinite()) continue;
        if(comma) protocol<<","; comma=true; protocol<<"["<<q.x()<<","<<q.y()<<"]";
      }
    };
    for(auto& vc:graph.verticesClouds()) emit(*vc.second,vc.first->estimate().toIsometry().cast<float>());
    if(command!='F' && tracker.reference()) emit(*tracker.reference(),mapper.estimate());
    protocol<<"]}"<<std::endl;
    if(command=='F') { graph.saveGraph("prior.g2o"); graph.saveClouds("prior"); break; }
  }
}
