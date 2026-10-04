#!/usr/bin/env bash
# 01-08 · NGD-SLAM — 从零把环境搭起来（本机无 sudo、无 Docker、发行版不带 Pangolin）
#
# 这个脚本把 README「环境上必须处理的三件事」变成可重跑的命令。
# 每一步都注明了为什么 —— 跳过任何一步都会在后面以看不懂的形式失败。
#
# 用法：  bash work/env_setup.sh
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"   # .../08_ngd_slam
DEPS="$HERE/code/.deps"
PREFIX="$DEPS/pangolin"
REPO="$HERE/code/NGD-SLAM"

echo "== 0. 取官方仓库（论文 p.1 给出的地址，不用任何 fork）"
[ -d "$REPO/.git" ] || git clone https://github.com/yuhaozhang7/NGD-SLAM.git "$REPO"

echo "== 1. Pangolin：发行版(noble)不带 libpangolin-dev，改用 ROS 2 Jazzy 的包"
# apt-get download 不需要 root；-x 解到本地前缀也不需要 root。
# 注意 apt 的 lists 要能更新，用可写的临时目录绕开 /var/lib/apt。
if [ ! -d "$PREFIX/include/pangolin" ]; then
  mkdir -p "$PREFIX" /tmp/aptl/partial /tmp/aptc/archives/partial
  apt-get -o Dir::State::Lists=/tmp/aptl -o Dir::Cache::archives=/tmp/aptc -o Debug::NoLocking=1 update
  ( cd /tmp && apt-get -o Dir::State::Lists=/tmp/aptl -o Dir::Cache::archives=/tmp/aptc \
        download ros-jazzy-pangolin libepoxy-dev libepoxy0 )
  for f in /tmp/ros-jazzy-pangolin_*.deb; do dpkg-deb -x "$f" /tmp/_pg; done
  cp -r /tmp/_pg/opt/ros/jazzy/. "$PREFIX/"
  # Pangolin 0.9.6 依赖 libepoxy，而不是 GLEW
  cp -r /tmp/_pg/usr/include/epoxy "$PREFIX/include/"
  cp -a /tmp/_pg/usr/lib/x86_64-linux-gnu/libepoxy.so* "$PREFIX/lib/"
fi

echo "== 2. 改掉 Pangolin 配置里硬编码的 libepoxy 系统路径"
# 这个 .deb 是给装好 ROS 的机器用的，INTERFACE_LINK_LIBRARIES 里写死了
# /usr/lib/x86_64-linux-gnu/libepoxy.so；本机没有那个文件（无 sudo）。
# 不改这一行，编译不会报错，**链接**才会失败。
TARGETS="$PREFIX/lib/x86_64-linux-gnu/cmake/Pangolin/PangolinTargets.cmake"
if ! grep -q "$PREFIX/lib/libepoxy.so" "$TARGETS"; then
  sed -i "s|/usr/lib/x86_64-linux-gnu/libepoxy.so|$PREFIX/lib/libepoxy.so|" "$TARGETS"
fi

echo "== 3. 关掉示例程序的可视化（只改一行，补丁见 work/local_patches.patch）"
# 本机没有可依赖的 X（无 Xvfb、无 sudo）；Viewer 只影响显示，不参与 SLAM。
if grep -q 'System::RGBD,true' "$REPO/Examples/RGB-D/rgbd_tum.cc"; then
  sed -i 's|ORB_SLAM3::System SLAM(argv\[1\],argv\[2\],ORB_SLAM3::System::RGBD,true);|ORB_SLAM3::System SLAM(argv[1],argv[2],ORB_SLAM3::System::RGBD,false); // headless: see work/local_patches.patch|' \
      "$REPO/Examples/RGB-D/rgbd_tum.cc"
fi

echo "== 4. 编译"
# 注意：不要照抄官方 build.sh —— 它会先构建 Sophus 的**测试**，而 Sophus 的测试
# 在 GCC 13 下因 -Werror=array-bounds 失败。这个项目只用 Sophus 的头文件
# (CMakeLists.txt:49 只把它加进 include 路径)，所以跳过 Sophus 不影响结果。
cd "$REPO"
for lib in DBoW2 g2o; do
  [ -d "Thirdparty/$lib/build/lib" ] || { cd "Thirdparty/$lib" && mkdir -p build && cd build && cmake .. -DCMAKE_BUILD_TYPE=Release && make -j4; cd "$REPO"; }
done
[ -f Vocabulary/ORBvoc.txt ] || ( cd Vocabulary && tar -xf ORBvoc.txt.tar.gz )
export CMAKE_PREFIX_PATH="$PREFIX:${CMAKE_PREFIX_PATH:-}"
mkdir -p build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Release
# -j3：ORB-SLAM3 的几个编译单元很吃内存，-j10 在 15 GB 的机器上会被 OOM 杀掉
make -j3

echo
echo "完成。运行时记得带上本地库路径："
echo "  export LD_LIBRARY_PATH=$PREFIX/lib/x86_64-linux-gnu:$PREFIX/lib:\$LD_LIBRARY_PATH"
