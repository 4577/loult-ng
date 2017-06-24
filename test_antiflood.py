import unittest
from datetime import datetime, timedelta
from tools.tools import UserState
from config import FLOOD_DETECTION_MSG_PER_SEC, FLOOD_DETECTION_WINDOW
from tools.tools import BannedWords


class TestUserState(unittest.TestCase):

    def test_log_msg(self):
        user_state = UserState()
        user_state.log_msg()
        self.assertEqual(len(user_state.timestamps), 1)

    def test_log_msg_prune(self):
        user_state = UserState()
        over_flood_window = timedelta(seconds=FLOOD_DETECTION_WINDOW + 1)
        old_timestamp = datetime.now() - over_flood_window
        user_state.timestamps = [old_timestamp]
        user_state.log_msg()
        self.assertEqual(len(user_state.timestamps), 1)

    def test_is_flooding(self):
        user_state = UserState()
        # sending an average of X messages per Y seconds means
        # having sent X*Y messages in Y seconds.
        flood_nb = FLOOD_DETECTION_MSG_PER_SEC * FLOOD_DETECTION_WINDOW
        for i in range(flood_nb + 1):
            user_state.log_msg()
        self.assertTrue(user_state.is_flooding)

    def test_is_flooding_no_trigger(self):
        user_state = UserState()
        # sending an average of X messages per Y seconds means
        # having sent X*Y messages in Y seconds.
        flood_nb = FLOOD_DETECTION_MSG_PER_SEC * FLOOD_DETECTION_WINDOW
        for i in range(flood_nb):
            user_state.log_msg()
        self.assertFalse(user_state.is_flooding)


class TestBannedWords(unittest.TestCase):

    def test_match_simple(self):
        word_list = [".*stuff.*", "^[0-9]{2}.*"]
        banned_words = BannedWords(word_list)
        self.assertTrue(banned_words("something stuff and things"))
        self.assertFalse(banned_words("something stuf and things"))
        self.assertTrue(banned_words("10 something"))
        self.assertFalse(banned_words("1 something"))


if __name__ == "__main__":
    unittest.main()
