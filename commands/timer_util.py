from random import randint
from typing import Optional
import re
import time

word_to_number_dict = dict(two=2, three=3, four=4, five=5, six=6, seven=7, eight=8, nine=9, ten=10)

max_timer_seconds = 30 * 24 * 60 * 60  # 30 days in seconds

'''
Message timer regexes
'''

verb_regex =r'(hold\son|give\sme|wait|gimme|need|in)'

optional_filler_token = r'(\s+(like|about|approximately|maybe|probably))?'

optional_profanity_token = r'(\s+(damn))?'

time_as_word_regex = r'''
		\s+
		(
			(?P<word_few>a\s+few) |
			(?P<word_two>a\s+couple) |
			(?P<word_one>an?|one)           |
			(?P<word_number>two|three|four|five|six|seven|eight|nine|ten)
		)
	'''

time_as_number_regex = r'\s+(?P<time_as_int>\d+)'

units_regex = r'''
	(
		\s+
		(                    
			(?P<s>secs?|seconds?) |   # 's', 'sec', 'secs', 'second' or 'seconds'
			(?P<m>mins?|minutes?) |   # 'm', 'min', 'mins', 'minute' or 'minutes'
			(?P<h>hrs?|hours?)    |   # 'h', 'hr', 'hrs', 'hour' or 'hours'
			(?P<d>days?)              # 'd', 'day' or 'days'
		)
	)    
'''

time_regex = re.compile(
	rf'''
	{verb_regex}
	{optional_filler_token}
	{optional_profanity_token}
	({time_as_word_regex}|{time_as_number_regex})
	{optional_profanity_token}
	{units_regex}
	''', re.VERBOSE)

# Really simple regex to check if someone mentions needing x time in their message.
# Ex: "gimme a few mins", "give me a minute", "i need 5 minutes", etc.
def message_timer(message: str) -> Optional[int]:
	try:
		match = re.search(time_regex, message)
		if match is not None:
			num_seconds = 0
			# Determine the number of units
			num_units = 0
			if match.group('word_few') is not None:
				num_units = 3
			elif match.group('word_one') is not None:
				num_units = 1
			elif match.group('word_two') is not None:
				num_units = 2
			elif match.group('word_number') is not None:
				num_units = word_to_number_dict[match.group('word_number')]
			elif match.group('time_as_int') is not None:
				num_units = int(match.group('time_as_int'))

			# Determine the unit type
			if match.group('s') is not None:
				num_seconds = num_units * 1
			elif match.group('m') is not None:
				num_seconds = num_units * 60
			elif match.group('h') is not None:
				num_seconds = num_units * 3600
			elif match.group('d') is not None:
				num_seconds = num_units * 86400

			if num_seconds > max_timer_seconds:
				print("Timer exceeds maximum allowed duration of 30 days.")
				return None

			return num_seconds
	except Exception as e:
		print(f"Error in message_timer: {e}")
	return None

# Given a number of seconds in the future, returns a Discord embedded timer message
# as a string.
def get_future_time(num_seconds: int) -> str:
	cur_time = int(time.time())
	timer_end_timestamp = cur_time + num_seconds
	return f"<t:{timer_end_timestamp}:R>"
