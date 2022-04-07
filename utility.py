import os
import re
from concurrent.futures import ThreadPoolExecutor
from queue import Queue

# For opening analysis
FirstMoveOffsetFrequency = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
Last1DistanceFrequency = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
Last2DistanceFrequency = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
MoveNumFrequency = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]


class ThreadPoolExecutorBounded(ThreadPoolExecutor):

    def __init__(self, *args, **kwargs):
        super(ThreadPoolExecutorBounded, self).__init__(*args, **kwargs)
        self._work_queue = Queue(maxsize=0)


def pos_to_str(pos):
    s = ""
    for i in range(len(pos)):
        x, y = pos[i]
        s += chr(ord("a") + x) + str(y + 1)
    return s


def str_to_pos(s):
    pos = []
    i = 0
    s = s.lower()
    while i < len(s):
        x = ord(s[i]) - ord("a")
        y = ord(s[i + 1]) - ord("0")
        if i + 2 < len(s) and s[i + 2].isdigit():
            y = y * 10 + ord(s[i + 2]) - ord("0") - 1
            i += 3
        else:
            y = y - 1
            i += 2
        pos += [(x, y)]
    return pos


def psq_to_psq(_psq, board_size):
    psq = ""
    # psq += "Piskvorky " + str(board_size) + "x" + str(board_size) + "," + " 11:11," + " 0\n"
    tt = [0, 0]
    for i in range(len(_psq)):
        x, y, t = _psq[i]
        psq += str(x + 1) + "," + str(y + 1) + "," + str(t - tt[i % 2]) + "\n"
        tt[i % 2] = t
    return psq


def get_dir_size(start_path):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(start_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)
    return total_size


def parse_line_opening(line):
    try:
        line = line.strip()
        line = re.sub(r"\s+", "", line)
        return line
    except:
        return None


def opening2pos(opening, board_size):
    opening = opening.split(",")
    hboard = int(board_size / 2)
    pos = ""
    for i in range(int(len(opening) / 2)):
        curx = hboard + int(opening[2 * i])
        cury = hboard + int(opening[2 * i + 1])
        pos = pos + chr(ord("a") + curx)
        pos = pos + str(1 + cury)
    return pos


def read_opening(opening_file, board_size):
    fin = open(opening_file, "r")
    openings_list = []
    while True:
        reads = fin.readline()
        if reads == None or len(reads) == 0:
            break
        line = parse_line_opening(reads)
        if line:
            openings_list.append(opening2pos(line, board_size))
    fin.close()
    if len(openings_list) == 0:
        openings_list.append("")
    return openings_list


def dict_2d_update(dic, key_a, key_b, val):
    if key_a in dic:
        dic[key_a].update({key_b: val})
    else:
        dic.update({key_a: {key_b: val}})


def parse_raw_opening(line):
    line_split = line.split(",")
    if len(line_split) <= 0 or len(line_split) % 2 == 1:
        return False
    x = 0
    y = 0
    cnt = 0
    opening = []
    for cord in line_split:
        cnt += 1
        if cnt % 2 == 0:
            y = cord
            opening.append([int(x), int(y)])
        else:
            x = cord
    return opening


def distance_between(cordX1, cordY1, cordX2, cordY2):
    return max(abs(cordX1 - cordX2), abs(cordY1 - cordY2))


def analyze_opening_helper(opening):
    if (len(opening) <= 0):
        return

    d = distance_between(opening[0][0], opening[0][1], 0, 0)
    FirstMoveOffsetFrequency[d] += 1

    last1Move = [0, 0]
    last2Move = [0, 0]
    cnt = 0
    for move in opening:
        cnt += 1
        if cnt > 1:
            d = distance_between(move[0], move[1], last1Move[0], last1Move[1])
            Last1DistanceFrequency[d] += 1
        if cnt > 2:
            d = distance_between(move[0], move[1], last2Move[0], last2Move[1])
            Last2DistanceFrequency[d] += 1
        if cnt > 1:
            last2Move[0] = last1Move[0]
            last2Move[1] = last1Move[1]
        last1Move[0] = move[0]
        last1Move[1] = move[1]

    if cnt < len(MoveNumFrequency):
        MoveNumFrequency[cnt] += 1


def analyze_openings(opening_file):
    fin = open(opening_file, "r")

    while True:
        # Read from file
        reads = fin.readline()
        if reads == None or len(reads) == 0:
            break
        line = parse_line_opening(reads)
        if not line:
            continue
        opening = parse_raw_opening(line)

        # Analyze the opening
        analyze_opening_helper(opening)

    fin.close()

    # Print result
    print("first move offset frequency")
    print(FirstMoveOffsetFrequency)
    print("last1 move distance frequency")
    print(Last1DistanceFrequency)
    print("last2 move distance frequency")
    print(Last2DistanceFrequency)
    print("move number frequency")
    print(MoveNumFrequency)


def list_move_time():
    left = 1000
    for i in range(0, 112):
        # t = left / 20
        # t = 0.4 * left / pow(i + 10, 0.7)
        t = 0.29 * left / pow(i + 12, 0.5)

        left = left - t

        min = int(t / 60)
        sec = t - min * 60
        print(i, "%dm%fs" % (min, sec))


if __name__ == "__main__":
    # analyze_openings("C:/Users/sunyu/gomoku/GomocupJudge/openings/openings_r.txt")
    list_move_time()
