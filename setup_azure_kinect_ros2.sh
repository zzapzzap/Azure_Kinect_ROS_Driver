#!/bin/bash
# Azure Kinect ROS2 Humble 설치 스크립트
# Ubuntu 22.04 (Jammy) + ROS2 Humble
# 사용법: bash setup_azure_kinect_ros2.sh [--ws /path/to/colcon_ws]

set -e

# ─────────────────────────────────────────────
# 색상 출력 헬퍼
# ─────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
info()    { echo -e "${BLUE}[INFO]${NC} $*"; }
success() { echo -e "${GREEN}[OK]${NC} $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC} $*"; }
error()   { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }

# ─────────────────────────────────────────────
# 인자 처리
# ─────────────────────────────────────────────
COLCON_WS="${HOME}/colcon_ws"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --ws) COLCON_WS="$2"; shift 2 ;;
    *) error "알 수 없는 인자: $1" ;;
  esac
done

DRIVER_REPO="https://github.com/zzapzzap/Azure_Kinect_ROS_Driver.git"
DRIVER_BRANCH="humble"
DRIVER_DIR="${COLCON_WS}/src/azure_kinect_ros_driver"

# ─────────────────────────────────────────────
# 환경 확인
# ─────────────────────────────────────────────
info "환경 확인 중..."

# Ubuntu 22.04 확인
if ! lsb_release -rs 2>/dev/null | grep -q "22.04"; then
  warn "Ubuntu 22.04가 아닙니다 (현재: $(lsb_release -rs)). 계속 진행하시겠습니까? [y/N]"
  read -r reply; [[ "$reply" =~ ^[Yy]$ ]] || exit 1
fi

# ROS2 Humble 확인
if [[ ! -f /opt/ros/humble/setup.bash ]]; then
  error "ROS2 Humble이 /opt/ros/humble 에 없습니다. 먼저 설치해주세요."
fi
success "ROS2 Humble 확인됨"

# sudo 확인
if ! sudo -n true 2>/dev/null; then
  warn "sudo 비밀번호가 필요합니다."
fi

# ─────────────────────────────────────────────
# STEP 1: Microsoft 패키지 저장소 추가
# ─────────────────────────────────────────────
info "STEP 1/5: Microsoft 패키지 저장소 설정..."

BIONIC_LIST="/etc/apt/sources.list.d/archive_uri-https_packages_microsoft_com_ubuntu_18_04_prod-jammy.list"
if [[ ! -f "$BIONIC_LIST" ]]; then
  curl -sSL https://packages.microsoft.com/keys/microsoft.asc | sudo apt-key add - 2>/dev/null
  sudo apt-add-repository -y "deb https://packages.microsoft.com/ubuntu/18.04/prod bionic main"
  sudo apt-get update -qq
  success "Microsoft bionic 저장소 추가됨"
else
  success "Microsoft bionic 저장소 이미 존재함 (스킵)"
fi

# ─────────────────────────────────────────────
# STEP 2: libk4a SDK 설치
# ─────────────────────────────────────────────
info "STEP 2/5: libk4a SDK 설치..."

if dpkg -l libk4a1.4 2>/dev/null | grep -q "^ii"; then
  success "libk4a1.4 이미 설치됨 (스킵)"
else
  # EULA 자동 수락 (환경변수 방식)
  sudo ACCEPT_EULA=Y DEBIAN_FRONTEND=noninteractive apt-get install -y libk4a1.4 libk4a1.4-dev
  success "libk4a1.4 설치 완료"
fi

# k4a-tools는 Ubuntu 22.04에서 libsoundio1 의존성 문제로 설치 불가
# (libsoundio1은 Ubuntu 18.04/20.04 전용)
if dpkg -l k4a-tools 2>/dev/null | grep -q "^ii"; then
  success "k4a-tools 이미 설치됨"
else
  warn "k4a-tools는 Ubuntu 22.04에서 libsoundio1 의존성 문제로 설치 불가 (viewer 기능 없음)"
fi

# ─────────────────────────────────────────────
# STEP 3: udev rules 설정 (USB 권한)
# ─────────────────────────────────────────────
info "STEP 3/5: udev rules 설정..."

UDEV_RULES="/etc/udev/rules.d/99-k4a.rules"
if [[ -f "$UDEV_RULES" ]]; then
  success "udev rules 이미 존재함 (스킵)"
else
  curl -fsSL "https://raw.githubusercontent.com/microsoft/Azure-Kinect-Sensor-SDK/develop/scripts/99-k4a.rules" \
    | sudo tee "$UDEV_RULES" > /dev/null
  sudo udevadm control --reload-rules
  sudo udevadm trigger
  success "udev rules 설치됨: $UDEV_RULES"
fi

# plugdev 그룹 확인
if id | grep -q "plugdev"; then
  success "plugdev 그룹 소속 확인됨"
else
  warn "현재 사용자가 plugdev 그룹에 없습니다. 추가합니다..."
  sudo usermod -aG plugdev "$USER"
  warn "plugdev 그룹 추가됨. 재로그인 후 적용됩니다."
fi

# ─────────────────────────────────────────────
# STEP 4: Azure Kinect ROS2 드라이버 클론
# ─────────────────────────────────────────────
info "STEP 4/5: Azure Kinect ROS2 드라이버 설정..."

mkdir -p "${COLCON_WS}/src"

if [[ -d "$DRIVER_DIR/.git" ]]; then
  CURRENT_REMOTE=$(git -C "$DRIVER_DIR" remote get-url origin 2>/dev/null || echo "none")
  if [[ "$CURRENT_REMOTE" == *"zzapzzap"* ]]; then
    info "포크 저장소 이미 존재함. 최신화 중..."
    git -C "$DRIVER_DIR" pull --ff-only origin "$DRIVER_BRANCH" || warn "pull 실패 (로컬 변경사항 있을 수 있음)"
    success "드라이버 최신화 완료"
  else
    warn "다른 원격지의 드라이버가 이미 존재합니다 ($CURRENT_REMOTE). 스킵."
  fi
else
  info "저장소 클론 중: $DRIVER_REPO (브랜치: $DRIVER_BRANCH)"
  git clone -b "$DRIVER_BRANCH" "$DRIVER_REPO" "$DRIVER_DIR"

  # Microsoft upstream 원본도 remote로 추가
  git -C "$DRIVER_DIR" remote add upstream \
    https://github.com/microsoft/Azure_Kinect_ROS_Driver.git
  git -C "$DRIVER_DIR" remote set-url --push upstream DISABLED

  success "드라이버 클론 완료"
  info "Remote 구성:"
  info "  origin   → $DRIVER_REPO (포크, 푸시 대상)"
  info "  upstream → https://github.com/microsoft/Azure_Kinect_ROS_Driver.git (원본, 읽기 전용)"
fi

# ─────────────────────────────────────────────
# STEP 5: rosdep 의존성 설치 및 colcon 빌드
# ─────────────────────────────────────────────
info "STEP 5/5: 의존성 설치 및 빌드..."

source /opt/ros/humble/setup.bash

# rosdep 초기화 (아직 안 된 경우)
if [[ ! -f /etc/ros/rosdep/sources.list.d/20-default.list ]]; then
  sudo rosdep init
fi
rosdep update 2>&1 | tail -3

info "rosdep 의존성 설치 중..."
rosdep install \
  --from-paths "${COLCON_WS}/src/azure_kinect_ros_driver" \
  --ignore-src -r -y \
  --skip-keys K4A 2>&1 | grep -v "^#" || true

info "colcon 빌드 중..."
cd "$COLCON_WS"
colcon build \
  --packages-select azure_kinect_ros_driver \
  --cmake-args -DCMAKE_BUILD_TYPE=Release \
  --event-handlers console_cohesion+

# ─────────────────────────────────────────────
# 완료
# ─────────────────────────────────────────────
echo ""
echo -e "${GREEN}══════════════════════════════════════════════${NC}"
echo -e "${GREEN}  Azure Kinect ROS2 설치 완료!${NC}"
echo -e "${GREEN}══════════════════════════════════════════════${NC}"
echo ""
echo "실행 방법:"
echo "  source ${COLCON_WS}/install/setup.bash"
echo "  ros2 launch azure_kinect_ros_driver driver.launch.py"
echo ""
echo "주요 토픽:"
echo "  /camera/rgb/image_raw          - RGB 이미지"
echo "  /sierra/depth/image_raw        - 정렬된 뎁스 이미지"
echo "  /sierra/point_cloud            - 포인트 클라우드"
echo "  /imu                           - IMU 데이터"
echo ""
echo "포크 저장소 upstream 업데이트 방법:"
echo "  git -C $DRIVER_DIR fetch upstream"
echo "  git -C $DRIVER_DIR rebase upstream/humble"
echo "  git -C $DRIVER_DIR push origin humble"
echo ""

if ! id | grep -q "plugdev"; then
  echo -e "${YELLOW}[주의]${NC} plugdev 그룹 변경 적용을 위해 재로그인이 필요합니다."
fi
