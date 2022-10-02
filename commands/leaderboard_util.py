"""
Leaderboards file is sorted and tab separated with format (user_id, points)

VERY IMPORTANT: leaderboard.txt should always have a newline at the end because its fucky
TODO: solve this in a smarter way
"""

from globals import *

def update_leaderboards_file(user_id, leaderboard_id):
    user_id = str(user_id)
    # Update leaderboards file
    lines = None

    open(LEADERBOARDS[leaderboard_id], "a").close()
    with open(LEADERBOARDS[leaderboard_id], "r") as leaders_file:
        lines = leaders_file.readlines()

    # Update user's score
    user_found = False
    for i, line in enumerate(lines):
        split_line = line.strip().split("\t")
        if user_id == split_line[0]:
            split_line[1] = str(int(split_line[1]) + 1)
            lines[i] = "\t".join(split_line) + "\n"
            user_found = True
            break

    if not user_found:
        lines.append("\t".join([user_id, "1\n"]))

    lines = list(
        sorted(lines, key=lambda x: int(x.strip().split("\t")[1]), reverse=True)
    )

    with open(LEADERBOARDS[leaderboard_id], "w") as leaders_file:
        leaders_file.writelines(lines)


def get_leaderboard(leaderboard_id):
    leaders_array = []
    open(LEADERBOARDS[leaderboard_id], "a").close()
    with open(LEADERBOARDS[leaderboard_id], "r") as lb_file:
        lines = lb_file.readlines()
        if len(lines) == 0:
            return "Apparently no one has ever gotten anything right."

        for line in lines:
            values = line.strip().split("\t")
            leaders_array.append([values[0], values[1]])

    # Convert points into message array
    leaders_array = list(
        map(
            lambda x: f"<@{x[0]}> has {x[1]} point{'' if int(x[1]) == 1 else 's'}!",
            leaders_array,
        )
    )

    return "Leaderboard:\n" + "\n".join(leaders_array[0:3])


def get_my_points(user_id, leaderboard_id):
    open(LEADERBOARDS[leaderboard_id], "a").close()
    with open(LEADERBOARDS[leaderboard_id], "r") as lb_file:
        for line in lb_file.readlines():
            (user, points) = line.strip().split("\t")
            if user == str(user_id):
                return f"<@{user_id}>, you have {points} point{'' if int(points) == 1 else 's'}!"
    return f"<@{user_id}>, you have no points. Zero. Zip. Nada."
