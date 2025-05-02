import math

class NorthKeeper:
    def __init__(self, max_full_turns: int = 3):
        self.prev_yaw: float | None = None     # 직전 입력 YAW
        self.cum_rotation: float = 0.0         # 누적 회전량(°)
        self.pos_turns: int = 0                # 시계(+) 방향으로의 전체 회전 횟수
        self.neg_turns: int = 0                # 반시계(–) 방향으로의 전체 회전 횟수
        self.offset: float | None = None       # 초기 기준 YAW (전원 켤 때 기준)
        self.max_turns = max_full_turns

    def _wrap_delta(self, delta: float) -> float:
        # Δ가 (–180, +180] 범위에 있도록 래핑
        if delta > 180:
            delta -= 360
        elif delta <= -180:
            delta += 360
        return delta

    def update(self, yaw: float) -> float:
        """
        새로운 YAW(0~360°)를 입력받으면,
          1) 첫 입력 시 offset 설정
          2) Δ 계산 → 전체 누적 회전에 반영 → full turns 카운트
          3) 북쪽(0°) 대비 오차(error) 계산
          4) twist 제한: 한 방향 full turns ≥ max_turns 이면 error=0
          5) ±90°로 클램핑 → 실제 서보 각도(0~180°) 반환
        """
        # 1) offset & prev 초기화
        if self.offset is None:
            self.offset = yaw
        if self.prev_yaw is None:
            self.prev_yaw = yaw

        # 2) Δ 계산 및 누적
        delta = self._wrap_delta(yaw - self.prev_yaw)
        self.cum_rotation += delta
        self.prev_yaw = yaw

        # full 360° 회전 카운트
        if self.cum_rotation >= 360:
            self.pos_turns += 1
            self.cum_rotation -= 360
        elif self.cum_rotation <= -360:
            self.neg_turns += 1
            self.cum_rotation += 360

        # 3) 북쪽 대비 error
        raw_error = yaw - self.offset
        raw_error = self._wrap_delta(raw_error)

        # 4) twist 제한
        if raw_error > 0 and self.pos_turns >= self.max_turns:
            error = 0.0
        elif raw_error < 0 and self.neg_turns >= self.max_turns:
            error = 0.0
        else:
            error = raw_error

        # 5) ±90° 클램핑
        if error > 90:
            error = 90
        elif error < -90:
            error = -90

        # 서보 각도(0°→0, 90°→90, 180°→180)
        # 중립 90°에서 error 만큼 빼거나 더하면 된다.
        servo_angle = 90.0 + error
        return servo_angle

# === 사용 예시 ===
keeper = NorthKeeper(max_full_turns=3)

# 임의의 YAW 시퀀스
test_yaws = [10, 45, 100, 200, 350, 10, 370, 730, 1100, 10]

for yaw in test_yaws:
    # YAW는 0~360° 범위로 래핑해 전달해도 좋음
    yaw_mod = yaw % 360
    angle = keeper.update(yaw_mod)
    print(f"입력 YAW={yaw_mod:6.1f}°, 서보 각도={angle:6.1f}°")
