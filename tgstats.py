import json
from matplotlib import pyplot as plt
from sys import stdout
import dateutil.parser
from collections import defaultdict
from statistics import median

STR_CLEAR_LINE = '\x1b[2K'

class TgStats:

    class Message:
        def __init__(self, text, date, is_outgoing, is_media, has_actionables):
            self.text = text
            self.date = date
            self.is_outgoing = is_outgoing
            self.is_media = is_media
            self.has_actionables = has_actionables

    class Stats:
        def __init__(self, messages_total, messages_outgoing, median_message_len=0, name=None):
            self.name = name
            self.messages_total = messages_total
            self.messages_outgoing = messages_outgoing
            self.median_message_len = median_message_len

    def __init__(self, json_filename):
        self.chats = None
        self.name = None
        self.stats_chats = None
        self.stats_total = None
        self.date = dateutil.parser.parse('2000-01-01')

        with open(json_filename, encoding='utf-8') as file:
            exported_json = json.load(file)
        self.parse_json(exported_json)

    def parse_json(self, json_obj):
        n_deleted = 0
        info = json_obj['personal_information']
        self.name = info['first_name'] + ((' ' + info['last_name']) if len(info['last_name']) > 0 else '')

        def get_message_name(msg):
            if msg['type'] == 'message':
                return msg['from']
            elif msg['type'] == 'service':
                return msg['actor']
            else:
                return None

        def parse_message_text(text):
            if type(text) is str:
                return text, False
            elif type(text) is list:
                # If message text contains actionable elements (links, mentions, phone numbers, etc.),
                # the message is then returned as list of pieces - str's for text and dict's for parsed actionables.
                pieces = []
                for item in text:
                    if type(item) is str:
                        pieces.append(item)
                    elif type(item) is dict:
                        # Actionable item, take its raw text value.
                        pieces.append(item['text'])
                    else:
                        raise TypeError('Message text sub-item has unexpected type.')
                return ''.join(pieces), True
            else:
                raise TypeError('Message text has unexpected type.')

        self.chats = {}
        json_chats = json_obj['chats']['list']

        for i, json_chat in enumerate(json_chats):
            stdout.write(f'\rParsing chat {i+1}/{len(json_chats)}...')

            # If chat account was deleted, the name key will be absent in JSON.
            chat_name = json_chat['name'] if 'name' in json_chat.keys() else None
            if chat_name is None:
                n_deleted += 1
                chat_name = f'Deleted account {n_deleted}'

            chat = []
            for json_message in json_chat['messages']:
                # Name stored for an individual message is that of the sender.
                # This way we can tell whether the message is incoming or outgoing.
                # We can also use it for chat name as it's sometimes fuller.
                message_name = get_message_name(json_message)
                is_out = message_name == self.name
                if not is_out and message_name is not None  \
                   and chat_name == message_name.split()[0] \
                   and len(message_name) > len(chat_name):
                    chat_name = message_name

                text, has_actionables = parse_message_text(json_message['text'])
                is_media = any(key in json_message.keys() for key in ('photo', 'media_type'))
                date = dateutil.parser.parse(json_message['date'])
                self.date = max(self.date, date)

                chat.append(self.Message(text, date, is_out, is_media, has_actionables))

            self.chats[chat_name] = chat
        stdout.write(STR_CLEAR_LINE + '\rParsing done.\n')

    def compute(self, top_n=30, exclude_chats=None):
        if exclude_chats is None:
            exclude_chats = []
        self.stats_chats = []
        messages_total = 0
        messages_outgoing = 0

        for i, chat_name in enumerate(self.chats.keys()):
            if chat_name in exclude_chats:
                continue
            stdout.write(f'\rComputing stats for chat {i+1}/{len(self.chats)-len(exclude_chats)}...')
            chat = self.chats[chat_name]
            chat_msgs_total = len(chat)
            messages_total += chat_msgs_total
            chat_msgs_outgoing = len(list(filter(lambda m: m.is_outgoing, chat)))
            messages_outgoing += chat_msgs_outgoing
            median_message_len = median([len(m.text) for m in filter(lambda m: not m.has_actionables, chat)])
            self.stats_chats.append(self.Stats(chat_msgs_total, chat_msgs_outgoing, median_message_len, chat_name))
        self.stats_total = self.Stats(messages_total, messages_outgoing)
        stdout.write(STR_CLEAR_LINE + '\rComputation done.\n')

        top_n = min(top_n, len(self.chats))
        self.stats_chats.sort(key=lambda s: s.messages_total, reverse=True)
        self.stats_chats = self.stats_chats[:top_n]

    def render(self):
        plt.figure()
        plt.title(f'Total messages for {self.name} as of {self.date.year}-{self.date.month:02d}-{self.date.day:02d}')

        x = range(len(self.stats_chats))
        y = [chat.messages_total for chat in self.stats_chats]
        y_max = max(y)

        plt.bar(x, y)
        plt.bar(x, [chat.messages_outgoing for chat in self.stats_chats], color='khaki')
        for i, chat in enumerate(self.stats_chats):
            out_percentage = chat.messages_outgoing / chat.messages_total * 100
            total_percentage = chat.messages_total / self.stats_total.messages_total * 100
            text = '%d. %s (%d / %.2f%% of all, %.1f%% out)' \
                 % (i+1, chat.name[:20], chat.messages_total, total_percentage, out_percentage)
            if chat.messages_total < y_max // 2:
                prop = TgStats.get_bartext_props('top')
                text_dy = y_max // 100
            else:
                prop = TgStats.get_bartext_props('bottom')
                text_dy = - y_max // 200
            plt.text(i, chat.messages_total + text_dy, text, prop)

        plt.xlim(-1, len(x))
        plt.tick_params(axis='x', which='both', top=False, bottom=False, labelbottom=False)
        plt.tick_params(axis='y', which='both', left=True, right=False)
        plt.show()

    @staticmethod
    def get_bartext_props(prop_type):
        return {
            'top': {
                'ha': 'center',
                'va': 'bottom',
                'size': 8.25,
                'rotation': 90
            },
            'bottom': {
                'ha': 'center',
                'va': 'top',
                'size': 8.25,
                'rotation': 90
            }
        }[prop_type]
