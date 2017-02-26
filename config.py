# in seconds, the time a pokemon has to wait before being able to attack again
ATTACK_RESTING_TIME = 30

# in seconds, the time during which a users's message are "remembered"
FLOOD_DETECTION_WINDOW = 5

# number of messages per second a user has to be sending (on average, during the detection window) to get
# shadowmuted
FLOOD_DETECTION_MSG_PER_SEC = 5

# Number of time a punitive message is sent to an attacked shadowmuted user
PUNITIVE_MSG_COUNT = 20

# in minutes, the time before a shadowmuted/banned user is able to connect again
BAN_TIME = 1
