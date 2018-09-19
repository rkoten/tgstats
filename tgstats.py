import json
from matplotlib import pyplot as plt
from sys import stdout
import dateutil.parser
from collections import defaultdict


class TgStats:

    class Message:
        def __init__(self, date_str, is_outgoing, is_media):
            self.date = dateutil.parser.parse(date_str)
            self.is_outgoing = is_outgoing
            self.is_media = is_media

    class Stats:
        def __init__(self, messages_total, messages_outgoing, name=None):
            self.name = name
            self.messages_total = messages_total
            self.messages_outgoing = messages_outgoing

    def __init__(self, json_filename):
        self.chats = None
        self.name = None
        self.stats_chats = None
        self.stats_total = None

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

        self.chats = defaultdict(list)
        json_chats = json_obj['chats']['list']
        for i, json_chat in enumerate(json_chats):
            stdout.write(f'\rParsing chat {i+1}/{len(json_chats)}...')
            chat_name = json_chat['name'] if 'name' in json_chat.keys() else None
            if chat_name is None:
                n_deleted += 1
                chat_name = f'deleted {n_deleted}'
            chat = []
            for json_message in json_chat['messages']:
                msg_name = get_message_name(json_message)
                is_out = msg_name == self.name
                is_media = any(key in json_message.keys() for key in ('photo', 'media_type'))
                if not is_out and msg_name is not None  \
                   and chat_name == msg_name.split()[0] \
                   and len(msg_name) > len(chat_name):
                    chat_name = msg_name
                chat.append(self.Message(json_message['date'], is_out, is_media))
            self.chats[chat_name].extend(chat)
        stdout.write('\rParsing done.\n')

    def compute(self, top_n=30, exclude_chats=None):
        if exclude_chats is None:
            exclude_chats = []
        self.stats_chats = []
        messages_total = 0
        messages_outgoing = 0
        for chat_name in self.chats.keys():
            if chat_name in exclude_chats:
                continue
            chat = self.chats[chat_name]
            chat_msgs_total = len(chat)
            messages_total += chat_msgs_total
            chat_msgs_outgoing = len(list(filter(lambda m: m.is_outgoing, chat)))
            messages_outgoing += chat_msgs_outgoing
            self.stats_chats.append(self.Stats(chat_msgs_total, chat_msgs_outgoing, chat_name))
        self.stats_total = self.Stats(messages_total, messages_outgoing)
        self.stats_chats.sort(key=lambda s: s.messages_total, reverse=True)
        top_n = min(top_n, len(self.chats))
        self.stats_chats = self.stats_chats[:top_n]

    def render(self):
        plt.figure()
        plt.title(f'Total messages for {self.name}')

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
