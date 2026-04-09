from unittest import TestCase

from dcetools.validate_logs import Record, validate

messages_ref: list[Record] = [
  {
    "content": "Please read the attached DMCA notice. This was just delivered to your counsel by Andrew's counsel.",
    "timestamp": "2024-12-02T18:39:51.929-06:00",
    "id": "1313303657412038657",
    "author": "homestuckicu",
    "channel": "1313303453816197150",
    "file": "UHC Discussion - Gio - Text Channels - followup [1313303453816197150].json"
  },
  {
    "content": "The future of the UHC will be made apparent once we see compliance with the DMCA. The intention here is not to kill the project. But it's essential that you show a willingness to cooperate with the notice from Andrew's counsel before the next steps are taken.\n\nAll of our correspondence has been turned over to Andrew and his counsel, including the conversations in this server, and all relevant DMs. We were asked to do this by Andrew and his counsel so that they had thorough background context to consider their approach. All conversations will remain confidential.\n\nAndrew and his counsel have been extremely critical of many statements you've made, and the way you've handled yourself in general during this process. He's asked that none of his remarks be quoted or summarized here. His view may be communicated through legal channels in the future, but starting now, the HICU will be fully disengaged from that process.\n.",
    "timestamp": "2024-12-02T18:40:12.662-06:00",
    "id": "1313303744372408433",
    "author": "homestuckicu",
    "channel": "1313303453816197150",
    "file": "UHC Discussion - Gio - Text Channels - followup [1313303453816197150].json"
  },
  {
    "content": "He's asked us to cease all communication with you. It is strongly advised that you make no statements or actions until receiving advice from your counsel. Andrew's intentions now are to have both of your counsels work together until the legal issues surrounding this matter are put to rest. This will take time, and any provocative gestures you make publicly will complicate that process and possibly put you in more significant legal jeopardy than you'd prefer. It will also incite drama within the fandom, which innocent members of the Homestuck creative teams will have to contend with. This will not be appreciated by any of us, and any actions you take may be subject to forceful response.\n\nFrom our side, there's no bad blood here. We were asked to mediate the licensing process about a year ago, and worked under the constraints provided by Andrew and his counsel, while protecting our own interests, and doing everything we could to accomodate your and Bambosh's perspectives. It hasn't worked out the way anyone wanted, but we at least hope you can see we tried our best to make it work under the limitations we were given.\n\nWe wish you all the best with your future endeavors, where they do not conflict with the interests of Homestuck, its creator, and its labor force. \n\nKind regards,\n\nThe Homestuck Independent Creative Union",
    "timestamp": "2024-12-02T18:40:23.193-06:00",
    "id": "1313303788542623815",
    "author": "homestuckicu",
    "channel": "1313303453816197150",
    "file": "UHC Discussion - Gio - Text Channels - followup [1313303453816197150].json"
  },
  {
    "content": "See attached, again posted here as a courtesy. Your counsel received this today, and we are posting it here to be sure you've seen it, in case your counsel is slow in relaying it to you.",
    "timestamp": "2024-12-11T12:08:16.22-06:00",
    "id": "1316466600056197150",
    "author": "homestuckicu",
    "channel": "1313303453816197150",
    "file": "UHC Discussion - Gio - Text Channels - followup [1313303453816197150].json"
  },
  {
    "content": "Last Friday, we provided a brief response to Makin, since people from his community were wondering about the fate of the UHC in light of its takedown. We thought the statement was neutral, factual, and we had no reason to believe you'd take issue with it. However, it seems you did. You then asked Makin to retract the statement, and you put the UHC back up, leading to another takedown notice.\n\nAndrew has now empowered James to hear from you on this privately. His doing so in no way makes this official HICU business, though you're reminded that any ongoing conversations you have with him are still covered by your NDA. We need to amicably move on from this matter, as it now appears to be an issue best settled between your and his counsels. In 24 hours we will deactivate this server.\n\nJames will be available to hear what issues you had with the previous statement, and what sort of statement you'd prefer to see publicly that will not lead to further noncompliance with these takedown notices.\n\nAgain we reiterate we've made every effort to accommodate all parties in this matter, and wish you all the best.",
    "timestamp": "2024-12-11T12:09:19.536-06:00",
    "id": "1316466865622618143",
    "author": "homestuckicu",
    "channel": "1313303453816197150",
    "file": "UHC Discussion - Gio - Text Channels - followup [1313303453816197150].json"
  }
]

def messageFactory(id, timestamp):
    return [
        {
            "content": "We change our mind. We're good now",
            "timestamp": timestamp,
            "id": id,
            "author": "homestuckicu",
            "channel": "1313303453816197150",
            "file": "UHC Discussion - Gio - Text Channels - followup [1313303453816197150].json"
        }

    ]

class TestNoFalsePositive(TestCase):
    def test_possible_before_start(self):
        messages_query = messageFactory("1313303657412038656", "2024-12-01T00:00:00.000-06:00")
        ret = validate(
            messages_query,
            messages_ref
        )
        self.assertTrue(ret)

    def test_possible_at_mid(self):
        messages_query = messageFactory("1316466865622618142", "2024-12-11T12:09:16.22-06:00")
        ret = validate(
            messages_query,
            messages_ref
        )
        self.assertTrue(ret)

    def test_possible_after_end(self):
        messages_query = messageFactory("1316466865622618144", "2024-12-12T00:00:00.000-06:00")
        ret = validate(
            messages_query,
            messages_ref
        )
        self.assertTrue(ret)


class TestNoFalseNegative(TestCase):
    def test_fake_before_start(self):
        messages_query = messageFactory("1313303657412038658", "2024-12-01T00:00:00.000-06:00")
        ret = validate(
            messages_query,
            messages_ref
        )
        self.assertFalse(ret)

    def test_fake_at_mid(self):
        messages_query = messageFactory("1316466600056197151", "2024-12-02T18:40:23.190-06:00")
        ret = validate(
            messages_query,
            messages_ref
        )
        self.assertFalse(ret)

    def test_fake_after_end(self):
        messages_query = messageFactory("1316466865622618144", "2024-12-10T00:00:00.000-06:00")
        ret = validate(
            messages_query,
            messages_ref
        )
        self.assertFalse(ret)
