import wx

import networkx as nx

import matplotlib

matplotlib.use('WXAgg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import \
    FigureCanvasWxAgg as FigCanvas
import numpy as np
import pylab

from project import Scheme

init_recruits = 1
init_threshold = 0
init_nodes = 10
init_degree = 2

init_speed = 5
min_speed = 1
max_speed = 10

def speed_wrap(speed):
    return 1100 - 100 * speed

class GraphGen(object):
    def __init__(self, recruits, threshold, nodes, edges):
        self.scheme = Scheme(threshold, recruits)
        self.scheme.generate_graph(nodes, edges)
        self.nodes = nodes
        self.over = False

    def next(self):
        time = self.scheme.increment_time()
        if time == -1:
            self.over = True
            return -1, -1
        else:
            return self.scheme.graph, self.scheme.color_map

    def get_stats(self):
        if self.over:
            a = self.nodes  # number total
            b = 0
            c = 0

            for key in self.scheme.fat_map:
                status = self.scheme.fat_map[key].gained_money
                if not status == 2:
                    b += 1
                    if status == 0:
                        c += 1

            return a, b, c
        else:
            return "no", "no", "no"


class ControlInput(wx.Panel):
    def __init__(self, parent, ID, label, init):
        wx.Panel.__init__(self, parent, ID)

        box = wx.StaticBox(self, -1, label)
        sizer = wx.StaticBoxSizer(box, wx.VERTICAL)

        self.label = label
        self.val = init
        self.text = wx.TextCtrl(self, -1,
                               size=(60, -1),
                               value=str(init),
                               style=wx.TE_PROCESS_ENTER)
        self.text.Bind(wx.EVT_CHAR, self.handle_keypress)

        area = wx.BoxSizer(wx.VERTICAL)
        area.Add(self.text, flag=wx.ALL | wx.ALIGN_CENTER)

        sizer.Add(area, 0, wx.ALL | wx.ALIGN_CENTER)

        self.SetSizer(sizer)
        sizer.Fit(self)

    def handle_keypress(self, event):
        key_code = event.GetKeyCode()
        if ord('0') <= key_code <= ord('9'):
            event.Skip()
            return
        if key_code == ord('.'):
            event.Skip()
            return
        if key_code == ord('\t'):
            event.Skip()
            return
        return

    def value(self):
        val = self.text.GetValue()
        if '.' in val:
            return float(val)
        return int(val)


class ParamsView(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent=parent)
        self.parent = parent

        self.recruits_control = ControlInput(self, -1, \
                                             "Number of recruits needed to exit scheme", init_recruits)
        self.threshold_control = ControlInput(self, -1, \
                                              "Threshold needed to accept invitation", init_threshold)
        self.node_control = ControlInput(self, -1, \
                                              "Size of total population (# nodes)", init_nodes)
        self.degree_control = ControlInput(self, -1, \
                                              "Standard number of friends (avg. degree)", init_degree)
        self.go_button = wx.Button(self, -1, "Go")
        self.Bind(wx.EVT_BUTTON, self.on_go_button, self.go_button)

        self.box = wx.BoxSizer(wx.VERTICAL)
        self.box.AddSpacer(5)
        self.box.Add(self.recruits_control, border=5, flag=wx.ALL | wx.ALIGN_CENTER)
        self.box.Add(self.threshold_control, border=5, flag=wx.ALL | wx.ALIGN_CENTER)
        self.box.Add(self.node_control, border=5, flag=wx.ALL | wx.ALIGN_CENTER)
        self.box.Add(self.degree_control, border=5, flag=wx.ALL | wx.ALIGN_CENTER)
        self.box.Add(self.go_button, border=10, flag=wx.ALL | wx.ALIGN_CENTER)

        self.SetSizer(self.box)
        self.box.Fit(self)

    def on_go_button(self, event):
        recruits = self.recruits_control.value()
        threshold = self.threshold_control.value()
        nodes = self.node_control.value()
        edges = nodes * self.degree_control.value()
        self.parent.set_params(recruits, threshold, nodes, edges)
        self.parent.show_graph()


class GraphView(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent=parent)
        self.parent = parent

        self.graph_gen = GraphGen(parent.recruits, parent.threshold, parent.nodes, parent.edges)
        self.graph, self.colors = self.graph_gen.next()
        self.paused = False

        self.dpi = 100
        self.fig = Figure((10.0, 6.0), dpi=self.dpi)
        self.axes = self.fig.add_subplot(111, label=np.random.random())
        pylab.setp(self.axes.get_xticklabels(), visible=False)
        pylab.setp(self.axes.get_yticklabels(), visible=False)

        self.canvas = FigCanvas(self, -1, self.fig)

        self.speed = speed_wrap(init_speed)

        self.speed_control = wx.Slider(self, -1, init_speed, min_speed, max_speed, \
                                      size=(300, 40), style=wx.SL_HORIZONTAL | wx.SL_LABELS)
        self.speed_control.Bind(wx.EVT_SLIDER, self.on_change_speed)

        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.on_timer, self.timer)
        self.timer.Start(self.speed)

        self.speed_box = wx.BoxSizer(wx.VERTICAL)
        self.speed_box.Add(self.speed_control, border=5, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL)
        self.speed_box.Add(wx.StaticText(self, -1, "Simulation Speed"), flag=wx.ALL | wx.ALIGN_CENTER)
        self.speed_box.AddSpacer(20)

        self.pause_button = wx.Button(self, -1, "Pause")
        self.Bind(wx.EVT_BUTTON, self.on_pause_button, self.pause_button)
        self.Bind(wx.EVT_UPDATE_UI, self.on_update_pause_button, self.pause_button)

        self.legend = wx.BoxSizer(wx.VERTICAL)
        yellow = wx.StaticText(self, -1, "Actively participating")
        yellow.SetBackgroundColour((255, 255, 0))
        green = wx.StaticText(self, -1, "Out, made money")
        green.SetBackgroundColour((0, 255, 0))
        red = wx.StaticText(self, -1, "Out, lost money")
        red.SetBackgroundColour((255, 0, 0))
        black = wx.StaticText(self, -1, "Out, declined invite")
        black.SetBackgroundColour((0, 0, 0))
        black.SetForegroundColour((255, 255, 255))
        self.legend.Add(yellow, flag=wx.ALL | wx.ALIGN_CENTER)
        self.legend.Add(green, flag=wx.ALL | wx.ALIGN_CENTER)
        self.legend.Add(red, flag=wx.ALL | wx.ALIGN_CENTER)
        self.legend.Add(black, flag=wx.ALL | wx.ALIGN_CENTER)

        self.controls_box = wx.BoxSizer(wx.HORIZONTAL)
        self.controls_box.Add(self.speed_box, border=5, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL)
        self.controls_box.AddSpacer(150)
        self.controls_box.Add(self.pause_button, border=5, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL)
        self.controls_box.AddSpacer(150)
        self.controls_box.Add(self.legend, border=5, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL)

        self.whole_box = wx.BoxSizer(wx.VERTICAL)
        self.whole_box.Add(self.canvas, 1, flag=wx.CENTER | wx.TOP | wx.GROW)
        self.whole_box.Add(self.controls_box, 0, flag=wx.ALIGN_CENTER | wx.TOP)

        self.SetSizer(self.whole_box)
        self.whole_box.Fit(self)

    def on_pause_button(self, event):
        self.paused = not self.paused

    def on_update_pause_button(self, event):
        label = "Resume" if self.paused else "Pause"
        self.pause_button.SetLabel(label)

    def on_change_speed(self, event):
        self.timer.Stop()
        speed = speed_wrap(self.speed_control.GetValue())
        self.speed = speed
        self.timer.Start(speed)

    def draw_plot(self):
        self.axes.clear()
        pylab.setp(self.axes.get_xticklabels(), visible=False)
        pylab.setp(self.axes.get_yticklabels(), visible=False)
        layout = nx.drawing.layout.circular_layout(self.graph)
        nx.draw_networkx(self.graph, pos=layout, node_color=self.colors, ax=self.axes)
        self.canvas.draw()

    def on_timer(self, event):
        if not self.paused:
            self.graph, self.colors = self.graph_gen.next()
            if self.graph == -1:
                a, b, c = self.graph_gen.get_stats()
                self.parent.show_stats(a, b, c)
                self.timer.Stop()
                return
            self.draw_plot()


class StatsView(wx.Panel):
    def __init__(self, parent, a, b, c):
        wx.Panel.__init__(self, parent=parent)
        self.parent = parent

        self.stats_box = wx.BoxSizer(wx.VERTICAL)
        self.stats_box.AddSpacer(30)
        self.stats_box.Add(wx.StaticText(self, -1, "Your scheme has collapsed! Statistics:"), \
                           flag=wx.ALL | wx.ALIGN_CENTER)
        self.stats_box.AddSpacer(10)
        bee = str(b)
        if a == b:
            bee = "all " + str(b)
        percent = 100 * (c / b)
        emoji = ":P"
        if percent > 50:
            emoji = ":)"
        if percent < 30:
            emoji = ">:("
        self.stats_box.Add(wx.StaticText(self, -1, "Out of " + str(a) + " nodes, " + bee + " participated in the scheme."), \
                           flag=wx.ALL | wx.ALIGN_CENTER)
        self.stats_box.Add(wx.StaticText(self, -1, "Out of those " + str(b) + ", " + str(c) + " made money."), \
                           flag=wx.ALL | wx.ALIGN_CENTER)
        self.stats_box.Add(wx.StaticText(self, -1, "Overall, your scheme had a " + str(percent) + "% profit rate " + emoji), \
                           flag=wx.ALL | wx.ALIGN_CENTER)
        self.stats_box.AddSpacer(20)
        self.again_button = wx.Button(self, -1, "Play again")
        self.Bind(wx.EVT_BUTTON, self.on_again_button, self.again_button)
        self.stats_box.Add(self.again_button, flag=wx.ALL | wx.ALIGN_CENTER)

        self.SetSizer(self.stats_box)
        self.stats_box.Fit(self)

    def on_again_button(self, event):
        self.parent.show_params()


class MainFrame(wx.Frame):
    title = 'EE126 Project: Pyramid Scheme'

    def __init__(self):
        wx.Frame.__init__(self, None, -1, self.title)

        self.recruits = init_recruits
        self.threshold = init_threshold
        self.nodes = init_nodes
        self.edges = init_degree * init_nodes

        self.params_view = ParamsView(self)
        self.SetInitialSize((300, 350))

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.params_view, 1, wx.EXPAND)
        self.SetSizer(self.sizer)

    def set_params(self, recruits, threshold, nodes, edges):
        self.recruits = recruits
        self.threshold = threshold
        self.nodes = nodes
        self.edges = edges

    def show_params(self):
        self.stats_view.Hide()
        self.params_view = ParamsView(self)
        self.sizer.Add(self.params_view, 1, wx.EXPAND)
        self.params_view.Show()
        self.SetInitialSize((300, 350))

    def show_graph(self):
        self.params_view.Hide()
        self.graph_view = GraphView(self)
        self.sizer.Add(self.graph_view, 1, wx.EXPAND)
        self.graph_view.Show()
        self.SetInitialSize((1000, 700))

    def show_stats(self, a, b, c):
        self.graph_view.Hide()
        self.stats_view = StatsView(self, a, b, c)
        self.sizer.Add(self.stats_view, 1, wx.EXPAND)
        self.stats_view.Show()
        self.SetInitialSize((500, 200))


if __name__ == '__main__':
    app = wx.App()
    app.frame = MainFrame()
    app.frame.Show()
    app.MainLoop()
