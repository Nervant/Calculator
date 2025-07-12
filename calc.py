from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.widget import Widget
from kivy.uix.behaviors import ButtonBehavior
from kivy.graphics import Color, RoundedRectangle
from kivy.core.window import Window
from kivy.animation import Animation
import re

Window.clearcolor = (0, 0, 0, 1)

MAX_HISTORY_ENTRIES = 50
TOP_SECTION_RATIO = 0.35
BOTTOM_SECTION_RATIO = 0.65
BUTTON_SCALE_DOWN = 0.95
BUTTON_SCALE_UP = 1.0
DEFAULT_SPACING = 20
DEFAULT_PADDING = 20
RESULT_FONT_SIZE = 100
HISTORY_FONT_SIZE = 50
LABEL_FONT_SIZE = 20
BUTTON_FONT_SIZE = 40
DARK_GRAY = (0.3, 0.3, 0.3, 1)
LIGHT_GRAY = (0.9, 0.9, 0.9, 1)
ERROR_COLOR = (0.8, 0.2, 0.2, 1)
OPERATOR_BUTTON_COLOR = (1.0, 0.5, 0.0, 1)
NUMBER_BUTTON_COLOR = (0.25, 0.25, 0.25, 1)

class RoundButton(ButtonBehavior, Widget):
    def __init__(self, text, bg_color, on_press_callback, **kwargs):
        super().__init__(**kwargs)
        self.bg_color = bg_color
        self.on_press_callback = on_press_callback
        self.text = text
        self.label = Label(text=text, font_size=BUTTON_FONT_SIZE, color=(1, 1, 1, 1), halign='center', valign='middle')
        self.add_widget(self.label)
        with self.canvas.before:
            Color(*self.bg_color)
            self.rect = RoundedRectangle(radius=[30])
        self.bind(pos=self._update_graphics, size=self._update_graphics)

    def _update_graphics(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size
        self.label.pos = self.pos
        self.label.size = self.size
        self.label.text_size = self.size

    def on_press(self):
        Animation(scale=BUTTON_SCALE_DOWN, duration=0.05).start(self)

    def on_release(self):
        Animation(scale=BUTTON_SCALE_UP, duration=0.05).start(self)
        self.on_press_callback(self)

    @property
    def scale(self):
        return 1

    @scale.setter
    def scale(self, value):
        w, h = self.size
        nw, nh = w * value, h * value
        self.rect.size = (nw, nh)
        self.rect.pos = (self.pos[0] + (w - nw) / 2, self.pos[1] + (h - nh) / 2)
        self.label.size = self.rect.size
        self.label.pos = self.rect.pos
        self.label.text_size = self.rect.size

class CalculatorLogic:
    def __init__(self):
        self.display = ""
        self.history = ""
        self.calculation_history = []
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
            self.clear()
        self.display += number

    def add_operator(self, operator):
        if self.just_computed:
            self.just_computed = False
        if not self.display and operator == '-':
            self.display = operator
        elif self.display and self.display[-1] in self.operators:
            if operator == '-' and self.display[-1] in {'*', '/'}:
                self.display += operator
            else:
                self.display = self.display[:-1] + operator
        else:
            self.display += operator

    def add_decimal(self):
        if self.just_computed:
            self.clear()
        if not self.display:
            self.display = "0."
        elif '.' not in self._get_current_number():
            self.display += '.' if self.display[-1].isdigit() else "0."

    def add_parenthesis(self):
        open_count = self.display.count('(')
        close_count = self.display.count(')')
        if open_count == close_count:
            if self.display and self.display[-1] not in self.operators and self.display[-1] != '(':
                self.display += '*('
            else:
                self.display += '('
        else:
            self.display += ')'

    def calculate_percentage(self):
        try:
            if not self.display:
                return
            original = self.display
            match = re.search(r'(.*?)([+\-])(\d+(?:\.\d+)?)$', self.display)
            if match:
                base_exp, operator, perc = match.groups()
                base_val = float(self._evaluate_expression(base_exp))
                perc_val = base_val * float(perc) / 100
                result = self._evaluate_expression(f'{base_val}{operator}{perc_val}')
            else:
                result = float(self._evaluate_expression(self.display)) / 100
            self.display = self._format_result(result)
            self.history = self._format_display(original + '%')
            self._store_history()
            self.just_computed = True
        except (ValueError, ZeroDivisionError):
            self.display = 'Error'

    def calculate_result(self):
        if self.display and self.display != 'Error':
            try:
                original = self.display
                result = self._evaluate_expression(self.display)
                self.display = self._format_result(result)
                self.history = self._format_display(original)
                self._store_history()
                self.just_computed = True
            except (ValueError, ZeroDivisionError):
                self.display = 'Error'

    def _get_current_number(self):
        current = ''
        for c in reversed(self.display):
            if c in self.operators or c in '()':
                break
            current = c + current
        return current

    def _format_result(self, result):
        try:
            num = float(result)
            if abs(num) > 1e15:
                return f"{num:.2e}"
            return str(int(num)) if num == int(num) else f"{num:.10g}"
        except Exception:
            return 'Error'

    def _format_display(self, expr):
        return expr.replace('*', '×').replace('/', '÷')

    def _store_history(self):
        if len(self.calculation_history) >= MAX_HISTORY_ENTRIES:
            self.calculation_history.pop(0)
        self.calculation_history.append(f"{self.history} = {self.display}")

    def _evaluate_expression(self, expression):
        expression = expression.strip().rstrip(''.join(self.operators))
        tokens = re.findall(r'\d+\.\d+|\d+|[()+\-*/]', expression)
        rpn = self._to_rpn(tokens)
        return str(self._compute_rpn(rpn))

    def _to_rpn(self, tokens):
        precedence = {'+': 1, '-': 1, '*': 2, '/': 2}
        output, ops = [], []
        prev = None
        for t in tokens:
            if re.match(r'\d+(\.\d+)?', t):
                output.append(float(t))
            elif t in precedence:
                if t == '-' and (prev is None or prev in '(-+*/'):
                    output.append(0.0)
                while ops and ops[-1] != '(' and precedence[ops[-1]] >= precedence[t]:
                    output.append(ops.pop())
                ops.append(t)
            elif t == '(':
                ops.append(t)
            elif t == ')':
                while ops and ops[-1] != '(':
                    output.append(ops.pop())
                ops.pop()
            prev = t
        while ops:
            output.append(ops.pop())
        return output

    def _compute_rpn(self, rpn):
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
                    if b == 0:
                        raise ZeroDivisionError
                    stack.append(a / b)
        if len(stack) != 1:
            raise ValueError("Invalid expression")
        return stack[0]

class HistoryPanel(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = DEFAULT_PADDING
        self.spacing = DEFAULT_SPACING
        self.size_hint = (1, 1)
        header = BoxLayout(orientation='horizontal', size_hint_y=None, height=60)
        header.add_widget(Widget())
        clear_btn = RoundButton('Clear', ERROR_COLOR, self.clear_history)
        header.add_widget(clear_btn)
        self.add_widget(header)
        self.history_scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False)
        self.history_layout = BoxLayout(orientation='vertical', spacing=8, size_hint_y=None, height=0, padding=[0, 10, 0, 10])
        self.history_layout.bind(minimum_height=self.history_layout.setter('height'))
        self.history_scroll.add_widget(self.history_layout)
        self.add_widget(self.history_scroll)

    def update_history(self, history_list):
        self.history_layout.clear_widgets()
        for item in reversed(history_list):
            lbl = Label(text=item, font_size=HISTORY_FONT_SIZE, size_hint_y=None, height=50,
                        halign='left', valign='middle', color=LIGHT_GRAY)
            lbl.bind(size=lbl.setter('text_size'))
            self.history_layout.add_widget(lbl)

    def clear_history(self, *args):
        if hasattr(self, 'calculator_ref'):
            self.calculator_ref.logic.calculation_history.clear()
            self.update_history([])

class Calculator(BoxLayout):
    OPERATOR_SYMBOLS = {'÷': '/', '×': '*', '-': '-', '+': '+'}
    DISPLAY_SYMBOLS = {'*': '×', '/': '÷'}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.logic = CalculatorLogic()
        self.orientation = 'vertical'
        self.padding = DEFAULT_PADDING
        self.spacing = DEFAULT_SPACING
        self.show_history = False
        self._build_ui()

    def _build_ui(self):
        self._build_top_section()
        self._build_content_section()

    def _build_top_section(self):
        top = BoxLayout(orientation='vertical', size_hint_y=TOP_SECTION_RATIO, spacing=DEFAULT_SPACING)
        header = BoxLayout(orientation='horizontal', size_hint_y=None, height=50, spacing=DEFAULT_SPACING)
        self.history_btn = RoundButton('History', DARK_GRAY, self._toggle_history)
        self.history_btn.size_hint_x = 0.5
        header.add_widget(self.history_btn)
        header.add_widget(Widget())
        self.history_label = Label(text="", font_size=LABEL_FONT_SIZE, size_hint_y=None, height=35,
                                   halign='right', valign='middle', color=(0.6, 0.6, 0.6, 1))
        self.history_label.bind(size=self.history_label.setter('text_size'))
        self.result = TextInput(text='0', font_size=RESULT_FONT_SIZE, readonly=True, halign='right',
                                padding=(20, 20), background_color=(0, 0, 0, 1),
                                foreground_color=(1, 1, 1, 1), cursor_color=(1, 1, 1, 0),
                                multiline=False)
        self.result.bind(size=self._force_align)
        top.add_widget(header)
        top.add_widget(self.history_label)
        top.add_widget(self.result)
        self.add_widget(top)

    def _build_content_section(self):
        self.content_layout = BoxLayout(orientation='horizontal', size_hint_y=BOTTOM_SECTION_RATIO)
        self.button_layout = GridLayout(cols=4, spacing=DEFAULT_SPACING, padding=[10, 10, 10, 10])
        layout = [['C', 'DEL', '%', '÷'], ['7', '8', '9', '×'], ['4', '5', '6', '-'],
                  ['1', '2', '3', '+'], ['( )', '0', '.', '=']]
        for row in layout:
            for label in row:
                color = OPERATOR_BUTTON_COLOR if label in self.OPERATOR_SYMBOLS or label in {'C', 'DEL', '%', '( )', '='} else NUMBER_BUTTON_COLOR
                btn = RoundButton(label, color, self._on_button_press)
                self.button_layout.add_widget(btn)
        self.content_layout.add_widget(self.button_layout)
        self.history_panel = HistoryPanel()
        self.history_panel.calculator_ref = self
        self.add_widget(self.content_layout)

    def _toggle_history(self, *args):
        self.show_history = not self.show_history
        self.content_layout.clear_widgets()
        if self.show_history:
            self.history_panel.update_history(self.logic.calculation_history)
            self.content_layout.add_widget(self.history_panel)
            self.history_btn.text = 'Calculator'
            self.history_btn.bg_color = (0.0, 0.6, 1.0, 1)
        else:
            self.content_layout.add_widget(self.button_layout)
            self.history_btn.text = 'History'
            self.history_btn.bg_color = DARK_GRAY

    def _on_button_press(self, instance):
        label = instance.text
        if label == 'C':
            self.logic.clear()
        elif label == 'DEL':
            self.logic.delete()
        elif label == '=':
            self.logic.calculate_result()
            self._update_history()
        elif label == '%':
            self.logic.calculate_percentage()
            self._update_history()
        elif label == '( )':
            self.logic.add_parenthesis()
        elif label == '.':
            self.logic.add_decimal()
        elif label in self.OPERATOR_SYMBOLS:
            self.logic.add_operator(self.OPERATOR_SYMBOLS[label])
        else:
            self.logic.add_number(label)
        self._refresh_display()

    def _refresh_display(self):
        self.result.text = self._format_display(self.logic.display) or '0'
        self.history_label.text = self._format_display(self.logic.history)

    def _format_display(self, text):
        return text.replace('*', '×').replace('/', '÷')

    def _update_history(self):
        if self.show_history:
            self.history_panel.update_history(self.logic.calculation_history)

    def _force_align(self, instance, value):
        instance.text = instance.text

class CalculatorApp(App):
    def build(self):
        return Calculator()

if __name__ == '__main__':
    CalculatorApp().run()
