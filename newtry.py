import socket
import json
import time

# ===================== 配置区 =====================
ROBOT_IP = "192.168.125.1"  # 替换成你的机器人真实IP
ROBOT_PORT = 5050  # 替换成你的机器人真实端口（原kRobotIPPort）
# 指令码定义（和机器人代码完全对应）
CMD_MOVEL = 1  # 直线
CMD_MOVEC = 2  # 圆弧
CMD_CHANGE = 3  # 移动到点（抬笔）
CMD_GO_READY = 4  # 就绪
CMD_GO_LEAVE = 5  # 离开
CMD_PAUSE_HERE = 6  # 暂停
CMD_SEAL = 10  # 盖章
CMD_GO_TAKEPIC = 11  # 拍照


# ===================== 发送函数 =====================
def send_robot_cmd(sock, cmd_code, params=None):
    """发送指令到机器人"""
    if params is None:
        params = []

    # 构造指令列表 [指令码, 参数1, 参数2...]
    cmd_data = [cmd_code] + params

    # 转JSON字符串（机器人通用格式）
    send_str = json.dumps(cmd_data) + "\n"  # 换行符用于分包

    # 发送
    sock.send(send_str.encode('utf-8'))
    print(f"✅ 发送指令: {cmd_data}")
    time.sleep(0.05)


# ===================== 主程序 =====================
if __name__ == '__main__':
    try:
        # 1. 创建TCP连接
        print(f"正在连接机器人 {ROBOT_IP}:{ROBOT_PORT}...")
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((ROBOT_IP, ROBOT_PORT))
        print("✅ 连接成功！")

        # 2. 发送示例任务（你可以随便改）
        # --------------------------
        # 任务：画一个正方形 + 盖章 + 拍照
        # --------------------------
        send_robot_cmd(s, CMD_CHANGE, [50, 50])  # 移动到起点
        send_robot_cmd(s, CMD_MOVEL, [50, 50, 250, 50])  # 画横线
        send_robot_cmd(s, CMD_MOVEL, [250, 50, 250, 350])  # 画竖线
        send_robot_cmd(s, CMD_MOVEL, [250, 350, 50, 350])  # 画横线
        send_robot_cmd(s, CMD_MOVEL, [50, 350, 50, 50])  # 画竖线
        send_robot_cmd(s, CMD_GO_READY)  # 回到就绪
        send_robot_cmd(s, CMD_SEAL)  # 盖章
        send_robot_cmd(s, CMD_GO_TAKEPIC)  # 拍照
        send_robot_cmd(s, CMD_GO_LEAVE)  # 离开工作区

        print("\n🎉 所有指令发送完成！")

    except Exception as e:
        print(f"❌ 错误: {e}")
    finally:
        s.close()