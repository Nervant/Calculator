from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.widget import Widget
from kivy.graphics import Color, RoundedRectangle
from kivy.core.window import Window
from kivy.animation import Animation
import re

Window.clearcolor = (0, 0, 0, 1)

symbol_map = {
    'C': 'CLEAR',
    'DEL': 'DELETE',
    '/': '/',
    '*': '*',
    '=': '=',
    '+': '+',
    '-': '-',
    '%': '%',
    '.': '.',
    '( )': 'PARENS'
}

class RoundButton(ButtonBehavior, Widget):
    def __init__(self, text, bg_color, on_press_callback, **kwargs):
        super().__init__(**kwargs)
        self.bg_color = bg_color
        self.on_press_callback = on_press_callback
        self.text = text

        self.label = Label(
            text=text,
            font_size=36,
            color=(1, 1, 1, 1),
            halign='center',
            valign='middle'
        )

        self.add_widget(self.label)

        with self.canvas.before:
            Color(*self.bg_color)
            self.rect = RoundedRectangle(radius=[30])

        self.bind(pos=self.update_graphics, size=self.update_graphics)

    def update_graphics(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size
        self.label.pos = self.pos
        self.label.size = self.size
        self.label.text_size = self.size

    def on_press(self):
        Animation(scale=0.95, duration=0.05).start(self)

    def on_release(self):
        Animation(scale=1.0, duration=0.05).start(self)
        self.on_press_callback(self)

    @property
    def scale(self):
        return 1

    @scale.setter
    def scale(self, value):
        w, h = self.size
        new_w = w * value
        new_h = h * value
        self.rect.size = (new_w, new_h)
        self.rect.pos = (
            self.pos[0] + (w - new_w) / 2,
            self.pos[1] + (h - new_h) / 2
        )
        self.label.size = self.rect.size
        self.label.pos = self.rect.pos
        self.label.text_size = self.rect.size

class Calculator(GridLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cols = 1
        self.padding = 20
        self.spacing = 20

        self.history_label = Label(
            text="",
            font_size=28,
            size_hint_y=None,
            height=50,
            halign='right',
            valign='middle',
            color=(0.7, 0.7, 0.7, 1)
        )
        self.history_label.bind(size=self.history_label.setter('text_size'))
        self.add_widget(self.history_label)

        self.result = TextInput(
            text='',
            font_size=96,
            size_hint_y=0.25,
            readonly=True,
            halign='right',
            padding=(20, 40),
            background_color=(0, 0, 0, 1),
            foreground_color=(1, 1, 1, 1),
            cursor_color=(1, 1, 1, 0)
        )
        self.result.bind(size=self.force_align)
        self.add_widget(self.result)

        button_layout = GridLayout(
            cols=4,
            spacing=20,
            padding=20,
            size_hint_y=0.7
        )

        buttons = [
            ['C', 'DEL', '%', '/'],
            ['7', '8', '9', '*'],
            ['4', '5', '6', '-'],
            ['1', '2', '3', '+'],
            ['( )', '0', '.', '=']
        ]

        for row in buttons:
            for label in row:
                is_operator = label in symbol_map
                bg_color = (1.0, 0.5, 0.0, 1) if is_operator else (0.15, 0.15, 0.15, 1)
                btn = RoundButton(
                    text=label,
                    bg_color=bg_color,
                    on_press_callback=self.on_button
                )
                button_layout.add_widget(btn)

        self.add_widget(button_layout)

    def force_align(self, instance, value):
        instance.text = instance.text

    def on_button(self, instance):
        t = instance.text
        exp = self.result.text

        if exp == 'Error' and t not in ['C', 'DEL']:
            exp = ''
            self.result.text = ''

        value = symbol_map.get(t, t)

        if value == '=':
            self.history_label.text = exp
            self.result.text = self.evaluate_expression(exp)
        elif value == 'CLEAR':
            self.result.text = ''
            self.history_label.text = ''
        elif value == 'DELETE':
            if exp.strip():
                tokens = re.findall(r'-?\d+\.\d+|-?\d+|[()+\-*/]', exp)
                if tokens:
                    new_exp = exp.rstrip()
                    last_token = tokens[-1]
                    if new_exp.endswith(last_token):
                        self.result.text = new_exp[:-len(last_token)].rstrip()
                    else:
                        self.result.text = new_exp[:-1]
                else:
                    self.result.text = ''
            else:
                self.result.text = ''
        elif value == '%':
            try:
                match = re.search(r'(.*?)([+\-])(\d+(?:\.\d+)?)$', exp)
                if match:
                    base_exp, operator, perc = match.groups()
                    base_val = self.evaluate_expression(base_exp)
                    perc_val = float(base_val) * float(perc) / 100
                    new_exp = f'{base_val}{operator}{perc_val}'
                    self.history_label.text = exp + '%'
                    self.result.text = self.evaluate_expression(new_exp)
                else:
                    self.result.text = str(float(self.evaluate_expression(exp)) / 100)
            except:
                self.result.text = 'Error'
        elif value == 'PARENS':
            if exp.count('(') == exp.count(')'):
                self.result.text += '('
            else:
                self.result.text += ')'
        else:
            if value in '+*/':
                if not exp or exp[-1] in '+-*/':
                    return
            elif value == '-':
                if not exp:
                    self.result.text += value
                    return
                elif exp[-1] not in '0123456789.)':
                    self.result.text += value
                    return
                elif exp[-1] in '+-*/':
                    return
            self.result.text += value

    def evaluate_expression(self, expression):
        def parse(tokens):
            def precedence(op):
                return {'+': 1, '-': 1, '*': 2, '/': 2}[op]
            output = []
            ops = []
            i = 0
            while i < len(tokens):
                token = tokens[i]
                if re.match(r'-?\d+(\.\d+)?', token):
                    output.append(float(token))
                elif token in '+-*/':
                    while ops and ops[-1] != '(' and precedence(ops[-1]) >= precedence(token):
                        output.append(ops.pop())
                    ops.append(token)
                elif token == '(':
                    ops.append(token)
                elif token == ')':
                    while ops and ops[-1] != '(':
                        output.append(ops.pop())
                    ops.pop()
                i += 1
            while ops:
                output.append(ops.pop())
            return output

        def compute(rpn):
            stack = []
            for token in rpn:
                if isinstance(token, float):
                    stack.append(token)
                else:
                    b = stack.pop()
                    a = stack.pop()
                    if token == '+': stack.append(a + b)
                    elif token == '-': stack.append(a - b)
                    elif token == '*': stack.append(a * b)
                    elif token == '/':
                        if b == 0: raise ZeroDivisionError
                        stack.append(a / b)
            return stack[0]

        tokens = re.findall(r'-?\d+\.\d+|-?\d+|[()+\-*/]', expression)
        if not tokens:
            return 'Error'
        try:
            rpn = parse(tokens)
            return str(compute(rpn))
        except:
            return 'Error'

class CalculatorApp(App):
    def build(self):
        return Calculator()

CalculatorApp().run()
