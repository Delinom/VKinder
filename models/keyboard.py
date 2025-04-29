import json, copy

class KeyboardBuilder:
    def __init__(self, inline=True):
        self.keyboard = {
            "inline": inline,
            "buttons": []
        }

    def add_button(self, label, payload, color="primary", row=None):
        button = {
            "action": {
                "type": "callback",
                "label": label,
                "payload": payload
            },
            "color": color
        }
        if row is None or row >= len(self.keyboard["buttons"]):
            self.keyboard["buttons"].append([button])
        else:
            self.keyboard["buttons"][row].append(button)

    def get_keyboard(self, value, key='id'):
        keyboard = copy.deepcopy(self.keyboard)
        for row in keyboard["buttons"]:
            for button in row:
                if key in button["action"]["payload"]:
                    button["action"]["payload"][key] = value
        return json.dumps(keyboard, ensure_ascii=False)