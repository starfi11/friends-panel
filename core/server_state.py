import threading
from datetime import datetime, timedelta
from typing import Optional
from core.config import INSTANCE_NAME
# ServerStatus 单例用于控制只有一个任务在对服务器进行操作，同时通过状态来保证请求的幂等性


class ServerStatus:
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    EXTENDING = "extending"
    STOPPING = "stopping"
    WAIT_FOR_STOP = "wait_for_stop"


class ServerState:
    VALID_TRANSITIONS = {
        ("stopped", "starting"),
        ("starting", "running"),
        ("starting", "stopped"),
        ("running", "stopping"),
        ("running", "extending"),
        ("running", "wait_for_stop"),
        ("extending", "running"),
        ("stopping", "stopped"),
        ("wait_for_stop", "stopping"),
    }

    def __init__(self):
        self._lock = threading.Lock()
        self._state: str = ServerStatus.STOPPED
        self._start_time: Optional[datetime] = None
        self._expire_time: Optional[datetime] = None
        self._timer: Optional[threading.Timer] = None

    # === 封装的修改状态的函数，避免出现非预期的状态转换 ===
    def transition(self, to_state: str):
        from_state = self._state
        if (from_state, to_state) not in self.VALID_TRANSITIONS:
            raise Exception(f"非法状态切换：{from_state} -> {to_state}")

        # 状态切换成功
        self._state = to_state

        # 统一处理一些状态副作用（如清除时间）
        if to_state == "stopped":
            self._start_time = None
            self._expire_time = None

    def is_running(self):
        with self._lock:
            return self._state == ServerStatus.RUNNING

    def get_status(self):
        with self._lock:
            return {
                "state": self._state,
                "start_time": self._start_time.isoformat() if self._start_time else None,
                "expire_time": self._expire_time.isoformat() if self._expire_time else None,
                "remaining_minutes": self._get_remaining_minutes()
            }

    def _get_remaining_minutes(self):
        if self._expire_time:
            delta = self._expire_time - datetime.now()
            return max(int(delta.total_seconds() // 60), 0)
        return None

    def _start_timer(self, seconds: float, shutdown_callback):
        if self._timer:
            self._timer.cancel()
        self._timer = threading.Timer(seconds, shutdown_callback)
        self._timer.start()

    # 下面需要实现9个函数，每个函数内都要加锁进行操作，完成对应的状态转换，完成的操作需要对定时器对象进行操作。
    # 其中前三个函数不是单纯的状态转换处理函数，还需要负责返回值表示尝试是否成功（只有状态为STOPPED时才能尝试启动、只有状态为RUNNING时才能尝试关闭、只有状态为RUNNING时才能尝试扩展）
    # 尝试失败需要返回信息告知尝试失败
    # 后六个函数只是单纯的操作处理，完成就是将ING切换为对应的状态并对定时器对象进行操作，最后三个失败操作就是消除尝试带来的影响。

    # 尝试启动、尝试关闭、尝试扩展、启动完成、关闭完成、扩展完成、尝试启动失败、尝试关闭失败、尝试扩展失败

    # ========== 第一类：尝试类 ==========
    def try_start(self):
        with self._lock:
            if self._state != ServerStatus.STOPPED:
                return False, f"当前状态为 {self._state}，无法启动实例"

            self.transition(ServerStatus.STARTING)
            return True, "启动流程已发起"

    def try_stop(self):
        with self._lock:
            if self._state not in [ServerStatus.RUNNING, ServerStatus.WAIT_FOR_STOP]:
                return False, f"当前状态为 {self._state}，无法尝试停止"

            self.transition(ServerStatus.STOPPING)
            return True, "关闭流程已发起"

    def try_extend(self):
        with self._lock:
            if self._state != ServerStatus.RUNNING:
                return False, f"当前状态为 {self._state}，无法尝试续期"
            self.transition(ServerStatus.EXTENDING)
            return True, "续期流程已发起"

    # ========== 第二类：尝试成功后 ==========
    def on_start_success(self, start_time: datetime, expire_time: datetime, shutdown_callback):
        with self._lock:
            self._start_time = start_time
            self._expire_time = expire_time
            self.transition(ServerStatus.RUNNING)

            seconds = (expire_time - start_time).total_seconds()
            self._start_timer(seconds, shutdown_callback)

    def on_stop_success(self):
        with self._lock:
            self.transition(ServerStatus.STOPPED)
            self._start_time = None
            self._expire_time = None
            if self._timer:
                self._timer.cancel()
                self._timer = None

    def on_extend_success(self, new_expire_time: datetime, shutdown_callback):
        with self._lock:
            self._expire_time = new_expire_time
            self.transition(ServerStatus.RUNNING)

            seconds = (new_expire_time - datetime.now()).total_seconds()
            self._start_timer(seconds, shutdown_callback)

    # ========== 第三类：尝试失败后 ==========
    def on_start_failed(self):
        with self._lock:
            self.transition(ServerStatus.STOPPED)

    def on_stop_failed(self):
        with self._lock:
            self.transition(ServerStatus.RUNNING)

    def on_extend_failed(self):
        with self._lock:
            self.transition(ServerStatus.RUNNING)

    def shutdown_callback(self):
        """定时器触发的自动关机逻辑"""
        # 先尝试关闭
        # 想象这样一个场景：callback被回调，但同时有一个extend进入，extend先抢到锁并执行延长时间逻辑，随后原timer被取消了，设置新timer后 callback可以拿到锁了
        # 但这时callback拿到锁之后直接把服务器关了，这就不符合刚才的extend后的效果了，怎么解决这个问题？拿到锁之后校验一下时间一致性，就能看出是否被续约
        from core.actions import shutdown_server

        with self._lock:
            now = datetime.now()

            # 若当前时间早于过期时间（代表被续期了），就不执行关机
            if self._expire_time and now < server_state._expire_time:
                print("[Timer] 检测到服务器已被续期，本次自动关机取消")
                return
            self.transition(ServerStatus.WAIT_FOR_STOP)
            # 否则进入关机流程，不调用try_stop，而是先切状态再调shut_down，保证没有间隙给延长时间机会
            # 这个场景可能要用可重入锁，但目前用了普通锁就一直用下去吧，加个状态就解决了

        # 解锁之后执行正式关机逻辑
        shutdown_server(user_email="[Machine Auto]")


# 实例化为全局对象
server_state = ServerState()
