import socket
import time
import struct

# ===================== 配置区 =====================
ROBOT_IP = "192.168.125.1"  # 替换成你的机器人真实IP
ROBOT_PORT = 5050  # 替换成你的机器人真实端口（原kRobotIPPort）

# 指令码（和你RAPID完全一致）
CMD_MOVEL = 1
CMD_MOVEC = 2
CMD_CHANGE = 3
CMD_GO_READY = 4
CMD_GO_LEAVE = 5
CMD_PAUSE_HERE = 6
CMD_SEAL = 10
CMD_GO_TAKEPIC = 11


# ===================== 核心发送函数 =====================
def send_packet(sock, cmd, params=None):
    if params is None:
        params = []

    # 1. 消息头（固定 0xAA55）
    header = 0xAA55
    # 2. 指令
    cmd_code = cmd
    # 3. 参数个数
    param_len = len(params)

    # 4. 打包二进制（小端）
    # 格式: <H H H + 每个参数 1个I (4字节无符号int)
    fmt = '<H H H' + ('I' * param_len)
    data = [header, cmd_code, param_len] + params

    # 打包
    packet = struct.pack(fmt, *data)

    # 发送
    sock.send(packet)
    print(f"✅ 发送成功: 指令={cmd}, 参数={params}")
    time.sleep(0.05)


# ===================== 测试发送 =====================
if __name__ == "__main__":
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((ROBOT_IP, ROBOT_PORT))
        print("✅ 连接机器人成功")

        # ========== 发送任务 ==========
        send_packet(s, CMD_CHANGE, [50, 50])  # 抬笔移动
        send_packet(s, CMD_MOVEL, [50, 50, 250, 50])  # 画直线
        send_packet(s, CMD_SEAL)  # 盖章
        send_packet(s, CMD_GO_TAKEPIC)  # 拍照
        send_packet(s, CMD_GO_READY)  # 回就绪

        print("\n🎉 所有指令发送完成！")

    except Exception as e:
        print("❌ 错误：", e)
    finally:
        s.close()
