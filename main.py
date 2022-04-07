from ai_match import ai_match
from threading import Lock
from utility import *
import prettytable
import time

WorkingDirectory = "C:/Users/sunyu/gomoku/GomocupJudge/bin_s/"
Folder = "C:/Users/sunyu/gomoku/tmp/"
OpeningFile = "C:/Users/sunyu/gomoku/GomocupJudge/openings/openings_s.txt"
BinaryPrefix = "pbrain-"
BinarySuffix = ".exe"

BoardSize = 15
Rule = 1

# Workers recommandation for 5950x(64GB)
# cpu test + cpu base    14
# gpu test + cpu base    12
# gpu test + gpu base    8
#
MaxWorkers = 14
Mutex = Lock()

# Computing power
#
# Gomocup 2021 server vs 5950x
# With PentaZen21
#              Gomocup    5950x       ratio
# freestyle    875        1837        0.48
# freestyle    977        2104        0.46
# fastgame     893        1865        0.48
# fastgame     957        2027        0.47
# standard     764        2006        0.39
# standard     657        2006        0.33
# renju        930        2023        0.46
# renju        684        2021        0.34
# renju        885        2017        0.44
#
# AI list: binary name, timeout turn, timeout match, max memory, test/base
AIs = [
    ["PentaZenNN", 10 * 100, 86400000, 350 * 1024 * 1024, "test"],
    ["katagomo_s15", 10 * 100, 86400000, 350 * 1024 * 1024, "base"],
    ["rapfi21", 10 * 100, 86400000, 350 * 1024 * 1024, "base"],
    ["embryo21_s", 10 * 100, 86400000, 350 * 1024 * 1024, "base"],
    ["AlphaGomoku", 10 * 100, 86400000, 350 * 1024 * 1024, "base"],
    ["PentaZen21_15", 10 * 100, 86400000, 350 * 1024 * 1024, "base"],
    ["Yixin2018", 10 * 100, 86400000, 350 * 1024 * 1024, "base"],
]

WldDict = dict()
ScoreDict = dict()


# Setup of a game
class GameSetup:

    def __init__(
        self,
        opening,
        opening_num,
        bin_1,
        bin_2,
        timeout_turn_1,
        timeout_turn_2,
        timeout_match_1,
        timeout_match_2,
        max_memory_1,
        max_memory_2,
    ):
        self.opening = opening
        self.opening_num = opening_num
        self.bin_1 = bin_1
        self.bin_2 = bin_2
        self.timeout_turn_1 = timeout_turn_1
        self.timeout_turn_2 = timeout_turn_2
        self.timeout_match_1 = timeout_match_1
        self.timeout_match_2 = timeout_match_2
        self.max_memory_1 = max_memory_1
        self.max_memory_2 = max_memory_2

    def print_info(self):
        print("opening", self.opening_num, self.opening)
        print(self.bin_1, self.timeout_turn_1, "vs", self.bin_2, self.timeout_turn_2)


# Run a game
def run_game(gameSetup):
    ai_1 = gameSetup.bin_1
    ai_2 = gameSetup.bin_2
    bin_full_1 = WorkingDirectory + BinaryPrefix + gameSetup.bin_1 + BinarySuffix
    bin_full_2 = WorkingDirectory + BinaryPrefix + gameSetup.bin_2 + BinarySuffix

    game = ai_match(board_size=BoardSize,
                    opening=str_to_pos(gameSetup.opening),
                    cmd_1=bin_full_1,
                    cmd_2=bin_full_2,
                    timeout_turn_1=gameSetup.timeout_turn_1,
                    timeout_turn_2=gameSetup.timeout_turn_2,
                    timeout_match_1=gameSetup.timeout_match_1,
                    timeout_match_2=gameSetup.timeout_match_2,
                    max_memory_1=gameSetup.max_memory_1,
                    max_memory_2=gameSetup.max_memory_2,
                    game_type=1,
                    rule=Rule,
                    folder_1=Folder,
                    folder_2=Folder,
                    working_dir_1=WorkingDirectory,
                    working_dir_2=WorkingDirectory,
                    tolerance=1000)

    msg, psq, result, endby = game.play()

    result_info = ""
    endby_info = ""

    if endby == 0:
        endby_info = "draw/five"
    elif endby == 1:
        endby_info = "foul"
    elif endby == 2:
        endby_info = "timeout"
    elif endby == 3:
        endby_info = "illegal coordinate"
    elif endby == 4:
        endby_info = "crash"

    if result == 0:
        result_info = "draw"
        WldDict[ai_1]["win"] += 0.5
        WldDict[ai_1]["lose"] += 0.5
        WldDict[ai_2]["win"] += 0.5
        WldDict[ai_2]["lose"] += 0.5
        ScoreDict[ai_2][ai_1] += 0.5
        ScoreDict[ai_1][ai_2] += 0.5
    elif result == 1:
        result_info = ai_2 + " wins"
        WldDict[ai_2]["win"] += 1.0
        WldDict[ai_1]["lose"] += 1.0
        ScoreDict[ai_2][ai_1] += 1.0
    elif result == 2:
        result_info = ai_1 + " wins"
        WldDict[ai_1]["win"] += 1.0
        WldDict[ai_2]["lose"] += 1.0
        ScoreDict[ai_1][ai_2] += 1.0

    with Mutex:
        print("================================================================================")
        gameSetup.print_info()
        print("result", result_info, "endby", endby_info)


# Print match result table
def print_result():
    # Sort AIs by winning games in descending order
    sorted_ais = []
    win_dict = dict()

    for i in WldDict.items():
        win_dict[i[0]] = i[1]["win"]

    for i in sorted(win_dict.items(), key=lambda kv: (kv[1], kv[0]), reverse=True):
        sorted_ais.append(i[0])

    # Construct table fields
    x = prettytable.PrettyTable(align="c", hrules=prettytable.ALL, padding_width=1)
    first_row = ["", "WIN", "LOSE"]

    for ai in sorted_ais:
        name = ai[0:3] + "." + ai[-3:]
        first_row.append(name.upper())
    x.field_names = first_row

    # Fill in scores
    for ai_1 in sorted_ais:
        row = [ai_1.upper(), WldDict[ai_1]["win"], WldDict[ai_1]["lose"]]
        for ai_2 in sorted_ais:
            if ai_1 == ai_2:
                score = "-"
            else:
                score = str(ScoreDict[ai_1][ai_2]) + ":" + str(ScoreDict[ai_2][ai_1])
            row.append(score)
        x.add_row(row)

    print("================================================================================")
    print(x)


if __name__ == "__main__":
    openings = read_opening(OpeningFile, BoardSize)
    gameSetups = []
    opening_num = 0

    for ai in AIs:
        print(ai)

    # Initialize stat and score dictionaries
    for ai in AIs:
        dict_2d_update(WldDict, ai[0], "win", 0.0)
        dict_2d_update(WldDict, ai[0], "lose", 0.0)
    for ai_1 in AIs:
        for ai_2 in AIs:
            dict_2d_update(ScoreDict, ai_1[0], ai_2[0], 0.0)
            dict_2d_update(ScoreDict, ai_2[0], ai_1[0], 0.0)

    # Generate all game gameSetups
    for opening in openings:
        for ai_1 in AIs:
            for ai_2 in AIs:
                if (ai_1[4] == "test" and ai_2[4] == "base") or (ai_1[4] == "base" and ai_2[4] == "test"):
                    gameSetups.append(GameSetup(opening, opening_num, ai_1[0], ai_2[0], ai_1[1], ai_2[1], ai_1[2], ai_2[2], ai_1[3], ai_2[3]))
        opening_num = opening_num + 1

    startTime = time.asctime(time.localtime(time.time()))
    print("start", startTime)

    # Run games in parallel
    with ThreadPoolExecutorBounded(max_workers=MaxWorkers) as executor:
        for gameSetup in gameSetups:
            executor.submit(run_game, gameSetup)

    print_result()

    finishTime = time.asctime(time.localtime(time.time()))
    print("finish", finishTime)
