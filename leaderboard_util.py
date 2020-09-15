
'''
Leaderboards file is sorted and tab separated with format (user_id, points)

VERY IMPORTANT: leaderboard.txt should always have a newline at the end because its fucky
TODO: solve this in a smarter way  
'''

def update_leaderboards_file(user_id):
	user_id = str(user_id)
	# Update leaderboards file
	lines = None
	with open('leaderboard.txt', 'r') as leaders_file:
		lines = leaders_file.readlines()
	
	# Update user's score
	user_found = False
	for i in range(len(lines)):
		line = lines[i]
		split_line = line.strip().split('\t')
		if user_id == split_line[0]:
			split_line[1] = str(int(split_line[1]) + 1)
			lines[i] = '\t'.join(split_line) + "\n"
			user_found = True
			break
	
	if not user_found:
		lines.append('\t'.join([user_id, "1\n"]))

	print(lines)

	lines = list(sorted(lines, key=lambda x: int(x.strip().split("\t")[1]), reverse=True))

	with open('leaderboard.txt', 'w') as leaders_file:
		leaders_file.writelines(lines)	

def get_leaderboard():
	leaders_array = []
	with open("leaderboard.txt", "r") as lb_file:
		lines = lb_file.readlines()
		if len(lines) == 0:
			return "Apparently no one has ever gotten anything right."

		for line in lines:
			values = line.strip().split("\t")
			leaders_array.append([values[0], values[1]])
		
	# Convert points into message array
	leaders_array = list(map(lambda x: f'<@{x[0]}> has {x[1]} points!', leaders_array))	

	return "Leaderboard:\n" + "\n".join(leaders_array[0:3])