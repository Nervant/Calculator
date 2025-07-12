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

class CalculatorLogic:
    def __init__(self):
        self.display = ""
        self.history = ""
        self.just_computed = False
        self.operators = {'+', '-', '*', '/'}

    def clear(self):
        self.display = ""
        self.history = ""
        self.just_computed = False

    def delete(self):
        if self.display:
            self.display = self.display[:-1]

    def add_number(self, number):
        if self.just_computed:
            self.display = ""
            self.history = ""
            self.just_computed = False
        self.display += number

    def add_operator(self, operator):
        if self.just_computed:
            self.just_computed = False
        
        if not self.display:
            if operator == '-':
                self.display += operator
        elif self.display[-1] in self.operators:
            self.display = self.display[:-1] + operator
        else:
            self.display += operator

    def add_decimal(self):
        if self.just_computed:
            self.display = ""
            self.history = ""
            self.just_computed = False
        
        current_number = self._get_current_number()
        if '.' not in current_number:
            self.display += '.'

    def add_parenthesis(self):
        if self.display.count('(') == self.display.count(')'):
            self.display += '('
        else:
            self.display += ')'

    def calculate_percentage(self):
        try:
            match = re.search(r'(.*?)([+\-])(\d+(?:\.\d+)?)$', self.display)
            if match:
                base_exp, operator, perc = match.groups()
                base_val = self._evaluate_expression(base_exp)
                perc_val = float(base_val) * float(perc) / 100
                new_exp = f'{base_val}{operator}{perc_val}'
                self.history = self.display + '%'
                self.display = self._evaluate_expression(new_exp)
            else:
                result = float(self._evaluate_expression(self.display)) / 100
                self.display = str(result)
        except:
            self.display = 'Error'

    def calculate_result(self):
        if self.display and self.display != 'Error':
            self.history = self.display
            self.display = self._evaluate_expression(self.display)
            self.just_computed = True

    def _get_current_number(self):
        if not self.display:
            return ""
        
        current_number = ""
        for char in reversed(self.display):
            if char in self.operators or char in '()':
                break
            current_number = char + current_number
        return current_number

    def _evaluate_expression(self, expression):
        if not expression:
            return 'Error'
        
        tokens = re.findall(r'\d+\.\d+|\d+|[()+\-*/]', expression)
        if not tokens:
            return 'Error'
        
        try:
            rpn = self._parse_to_rpn(tokens)
            result = self._compute_rpn(rpn)
            return str(int(result)) if result == int(result) else str(result)
        except:
            return 'Error'

    def _parse_to_rpn(self, tokens):
        def precedence(op):
            return {'+': 1, '-': 1, '*': 2, '/': 2}[op]
        
        output = []
        ops = []
        
        for token in tokens:
            if re.match(r'\d+(\.\d+)?', token):
                output.append(float(token))
            elif token in '+-*/':
                while (ops and ops[-1] != '(' and 
                       precedence(ops[-1]) >= precedence(token)):
                    output.append(ops.pop())
                ops.append(token)
            elif token == '(':
                ops.append(token)
            elif token == ')':
                while ops and ops[-1] != '(':
                    output.append(ops.pop())
                if ops:
                    ops.pop()
        
        while ops:
            output.append(ops.pop())
        
        return output

    def _compute_rpn(self, rpn):
        stack = []
        for token in rpn:
            if isinstance(token, float):
                stack.append(token)
            else:
                if len(stack) < 2:
                    raise ValueError("Invalid expression")
                b = stack.pop()
                a = stack.pop()
                if token == '+':
                    stack.append(a + b)
                elif token == '-':
                    stack.append(a - b)
                elif token == '*':
                    stack.append(a * b)
                elif token == '/':
                    if b == 0:
                        raise ZeroDivisionError
                    stack.append(a / b)
        
        if len(stack) != 1:
            raise ValueError("Invalid expression")
        
        return stack[0]

class Calculator(GridLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.logic = CalculatorLogic()
        self.cols = 1
        self.padding = 20
        self.spacing = 20
        self._setup_ui()

    def _setup_ui(self):
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
        self.result.bind(size=self._force_align)
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
                is_operator = label in ['C', 'DEL', '%', '/', '*', '-', '+', '=', '( )']
                bg_color = (1.0, 0.5, 0.0, 1) if is_operator else (0.15, 0.15, 0.15, 1)
                btn = RoundButton(
                    text=label,
                    bg_color=bg_color,
                    on_press_callback=self._on_button_press
                )
                button_layout.add_widget(btn)

        self.add_widget(button_layout)

    def _force_align(self, instance, value):
        instance.text = instance.text

    def _on_button_press(self, instance):
        button_text = instance.text
        
        if button_text == 'C':
            self._handle_clear()
        elif button_text == 'DEL':
            self._handle_delete()
        elif button_text == '=':
            self._handle_equals()
        elif button_text == '%':
            self._handle_percentage()
        elif button_text == '( )':
            self._handle_parenthesis()
        elif button_text == '.':
            self._handle_decimal()
        elif button_text in '+-*/':
            self._handle_operator(button_text)
        else:
            self._handle_number(button_text)
        
        self._update_display()

    def _handle_clear(self):
        self.logic.clear()

    def _handle_delete(self):
        self.logic.delete()

    def _handle_equals(self):
        self.logic.calculate_result()

    def _handle_percentage(self):
        self.logic.calculate_percentage()

    def _handle_parenthesis(self):
        self.logic.add_parenthesis()

    def _handle_decimal(self):
        self.logic.add_decimal()

    def _handle_operator(self, operator):
        self.logic.add_operator(operator)

    def _handle_number(self, number):
        self.logic.add_number(number)

    def _update_display(self):
        self.result.text = self.logic.display
        self.history_label.text = self.logic.history

class CalculatorApp(App):
    def build(self):
        return Calculator()

CalculatorApp().run()
