import json
from matplotlib import pyplot as plt

from models import *


class TgStats:

    def __init__(self, json_filename, exclude_chats=None):
        if exclude_chats is None:
            exclude_chats = []

        self.chats = []
        self.full_name = None

        with open(json_filename) as file:
            exported_json = json.load(file)
        self.parse_json(exported_json, exclude_chats)
        self.chats.sort(key=lambda chat: len(chat.messages), reverse=True)

    def parse_json(self, json_obj, exclude_chats):
        n_deleted = 0
        info = json_obj['personal_information']
        self.full_name = info['first_name'] + ((' ' + info['last_name']) if len(info['last_name']) > 0 else '')

        def get_message_name(msg):
            if msg['type'] == 'message':
                return msg['from']
            elif msg['type'] == 'service':
                return msg['actor']
            else:
                return None

        for json_chat in json_obj['chats']['list']:
            try:
                json_chat['name']
            except KeyError:
                json_chat['name'] = None
            name = json_chat['name']
            if type(name) is str and name in exclude_chats:
                continue
            if name is None:
                n_deleted += 1
                name = f'deleted {n_deleted}'
            chat = TgChat(name)
            self.chats.append(chat)
            for json_message in json_chat['messages']:
                msg_name = get_message_name(json_message)
                is_out = msg_name == self.full_name
                if not is_out and msg_name is not None  \
                   and chat.name == msg_name.split()[0] \
                   and len(msg_name) > len(chat.name):
                    chat.name = msg_name
                chat.add_message(TgMessage(is_out))

    def render_stats(self):
        plt.figure()
        plt.title(f'Total messages for {self.full_name}')

        top_n = min(30, len(self.chats))
        x = range(top_n)
        y = [chat.n_total for chat in self.chats[:top_n]]
        y_max = max(y)

        plt.bar(x, y)
        plt.bar(x, [chat.n_outgoing for chat in self.chats[:top_n]], color='khaki')
        for i, chat in enumerate(self.chats[:top_n]):
            out_percentage = chat.n_outgoing / chat.n_total * 100
            text = '%d. %s (%d, %.1f%% out)' % (i+1, chat.name[:21], chat.n_total, out_percentage)
            if chat.n_total < y_max // 2:
                prop = TgStats.get_bartext_props('top')
                text_dy = y_max // 100
            else:
                prop = TgStats.get_bartext_props('bottom')
                text_dy = - y_max // 200
            plt.text(i, chat.n_total + text_dy, text, prop)

        plt.xlim(-1, top_n)
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


def main():
    tgstats = TgStats('/home/rkot/downloads/Telegram Desktop/DataExport_28_08_2018 (3)/result.json', exclude_chats=['КНУчат'])
    tgstats.render_stats()


if __name__ == '__main__':
    main()
