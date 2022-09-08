import base64
import time
import warnings
from io import BytesIO

import numpy as np
import PySimpleGUI as sg
from PIL import Image

from board import Board
from img import icons
from lang import lang_DE

LANG_DICT = lang_DE


# to have same behaviour as before, the default is None
# for scaling behaviour set this value to a float value, ideally 1. / n
scaling = None

# if scaling is None, subsample will be as well and disregarded in the calls
subsample = int(1 / scaling) if scaling is not None else None


class GUI:
    def __init__(self):
        self.create_blank_icon()

        sg.theme("Black")  # Keep things interesting for your users
        sg.set_options(
            font=("DejaVu Sans Mono", 54),
            scaling=scaling
        )

        layout = self.create_layout()

        self.window = sg.Window(
            "Tic Tac Toe", layout, margins=(0, 0), background_color="#000",
            no_titlebar=True, location=(0,0), size=(1920,1080)
        )
        self.window.Read(timeout=0.001)
        self.show_new_game()

    @staticmethod
    def create_blank_icon():
        buffer = BytesIO(base64.b64decode(icons.o))
        width, height = Image.open(buffer).size

        # Create a blank image
        icons.blank = Image.new("RGBA", (width, height), "#ffffff00")
        # convert to base64
        with BytesIO() as output:
            icons.blank.save(output, format="PNG")
            icons.blank = output.getvalue()

    def create_layout(self):
        game_column = [
            [
                sg.Button(
                    "",
                    image_data=icons.blank,
                    image_subsample=subsample,
                    key=(j, i),
                    metadata=False,
                    pad=(10, 10),
                    mouseover_colors="white",
                )
                for i in range(3)
            ]
            for j in range(3)
        ]
                
        expand_column = [[sg.Text("", size=(2, 1), key="-EXPAND-"),],]

        score_column = [
            [sg.Text("title str", size=(20, 1), key="-TITLE_TEXT-")],
            [sg.Text("subtitle str", size=(20, 1), key="-SUBTITLE_TEXT-")],
            [
                sg.Text(
                    "", size=(25, 3), font=("DejaVu Sans Mono", 28), key="-WARN_TEXT-"
                )
            ],
            [sg.Image("", key="-PLAYER0_IMG-")],
            [
                sg.Text("0", size=(10, 1), key="-PLAYER0_TEXT-"),
                sg.Text("", size=(5, 1), key="-PLAYER0_SCORE-"),
            ],
            [sg.Text("", size=(1, 1), key="-EXPAND-"),],
            [sg.Image("", key="-PLAYER1_IMG-")],
            [
                sg.Text("0", size=(10, 1), key="-PLAYER1_TEXT-"),
                sg.Text("", size=(5, 1), key="-PLAYER1_SCORE-"),
            ],
        ]

        return [[sg.Text(key='-EXPAND-', font='ANY 1', pad=(0, 0))],
            [sg.Column(game_column), sg.Column(expand_column), sg.Column(score_column, vertical_alignment='center', justification="center")]
        ]

    def show_board(self, board, winning_fields=None):
        # to read out old inputs
        event, values = self.window.Read(timeout=0.001)

        for row in range(3):
            for col in range(3):
                label = Board.field_state_to_str_map[board[row][col]]
                if label == "_":
                    icon = icons.blank
                elif label == "x":
                    if winning_fields and (row, col) in winning_fields:
                        icon = icons.x_inv
                    else:
                        icon = icons.x
                elif label == "o":
                    if winning_fields and (row, col) in winning_fields:
                        icon = icons.o_inv
                    else:
                        icon = icons.o
                self.window[(row, col)].update(
                    image_subsample=subsample,
                    image_data=icon)
        self.window.Refresh()

    def show_new_game(self):
        self.write("New game", "-TITLE_TEXT-")
        self.write("", "-SUBTITLE_TEXT-")

    def blink(self, board, winning_fields):
        for i in range(2):
            self.show_board(board, winning_fields=winning_fields)
            time.sleep(0.3)
            self.show_board(board, winning_fields=None)
            time.sleep(0.3)
        self.show_board(board, winning_fields=winning_fields)

    def listen_input(self, _):
        event, values = self.window.Read()
        self.warn("")
        return event

    def show_scores(self, scores):
        self.write(str(scores[0]), "-PLAYER0_SCORE-")
        self.write(str(scores[1]), "-PLAYER1_SCORE-")

    def show_final_state(self, board, state, winner, winning_fields):
        if winner is not None:
            winner_str = board.field_state_to_str_map[winner]
            self.write("Winner: " + winner_str, "-TITLE_TEXT-")
            self.write("", "-SUBTITLE_TEXT-")
            self.blink(board, winning_fields)
        else:
            self.write("Draw", "-TITLE_TEXT-")
            self.write("", "-SUBTITLE_TEXT-")
            self.show_board(board)

    def show_image(self, fn, key):
        self.window[key].update(fn, subsample=subsample)
        self.window.Refresh()

    def show_policy(self, values):
        values = np.array(values)
        finite_indices = np.isfinite(values)
        values[finite_indices] -= np.mean(values[finite_indices])
        max_scale = max(
            abs(np.min(values[finite_indices])), np.max(values[finite_indices])
        )
        if max_scale > 0.0:
            values[finite_indices] /= max_scale
        values[~finite_indices] = 0.0

        for row in range(3):
            for col in range(3):
                q = values[row * 3 + col]
                if abs(q) < 1e-2:
                    color = "#999999"
                elif q > 0:
                    color = f"#00{int(q * 255):02x}00"
                else:
                    color = f"#{int(-q * 255):02x}0000"
                self.window[(row, col)].update(button_color=color)
        self.window.Refresh()
        time.sleep(2)
        for row in range(3):
            for col in range(3):
                self.window[(row, col)].update(button_color="#ffffff")
        self.window.Refresh()

    def warn(self, text):
        self.write(text, "-WARN_TEXT-", text_color="#ff0000")

    def write(self, text, key, *, text_color="#ffffff"):
        if text in LANG_DICT:
            text = LANG_DICT[text]
        else:
            warnings.warn(f"Translation for {text} not found.", RuntimeWarning)
        self.window[key].update(text, text_color=text_color)
        self.window.Refresh()

    def __del__(self):
        if self.window:
            self.window.close()
