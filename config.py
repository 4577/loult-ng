# in seconds, the time a pokemon has to wait before being able to attack again
ATTACK_RESTING_TIME = 30

# in seconds, the time during which a users's message are "remembered"
FLOOD_DETECTION_WINDOW = 4

# number of messages per second a user has to be sending (on average, during the detection window) to get
# shadowmuted
FLOOD_DETECTION_MSG_PER_SEC = 3

# duration in seconds until a warned flooder
# isn't considered a flooder anymore if they stop flooding
FLOOD_WARNING_TIMEOUT = 5 * 60

# Number of time a punitive message is sent to an attacked shadowmuted user
PUNITIVE_MSG_COUNT = 50

# in minutes, the time before a shadowmuted/banned user is able to connect again
BAN_TIME = 1

# Regular expressions interpreted by the "re" module and tested
# in fullmatch mode. See https://docs.python.org/3/library/re.html
# For example, [r".*\bTrump\b.*"] will match any sentence
# containing the word "Trump", but won't match "Trumped".
# For case insensitivity, use (?i) before your regex.
BANNED_WORDS = [r"(?i).*\bTrump\b.*", r"(?i).*\bfag(got)?\b.*"]
