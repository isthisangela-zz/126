import os
import pprint
import random
import sys
import wx

import json
import numpy as np
import networkx as nx

import matplotlib

matplotlib.use('WXAgg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import \
    FigureCanvasWxAgg as FigCanvas
import numpy as np
import pylab

#from project import Scheme

init_recruits = 1
init_threshold = 0

init_speed = 5
min_speed = 1
max_speed = 10

def speed_wrap(speed):
    return 500 / speed

class DataGen(object):
    def __init__(self, recruits, threshold):
        #self.data = Scheme(recruits, threshold)
        self.graph = nx.karate_club_graph()

    def next(self):
        print('hi')
        return nx.karate_club_graph()


class ControlInput(wx.Panel):
    def __init__(self, parent, ID, label, init):
        wx.Panel.__init__(self, parent, ID)

        box = wx.StaticBox(self, -1, label)
        sizer = wx.StaticBoxSizer(box, wx.VERTICAL)

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
        if key_code == ord('\t'):
            event.Skip()
            return
        return

    def value(self):
        return int(self.text.GetValue())


class ParamsView(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent=parent)
        self.parent = parent

        self.recruits_control = ControlInput(self, -1, \
                                             "Number of recruits needed to exit scheme", init_recruits)
        self.threshold_control = ControlInput(self, -1, \
                                              "Threshold needed to accept invitation", init_threshold)
        self.go_button = wx.Button(self, -1, "Go")
        self.Bind(wx.EVT_BUTTON, self.on_go_button, self.go_button)

        self.box = wx.BoxSizer(wx.VERTICAL)
        self.box.AddSpacer(5)
        self.box.Add(self.recruits_control, border=5, flag=wx.ALL | wx.ALIGN_CENTER)
        self.box.Add(self.threshold_control, border=5, flag=wx.ALL | wx.ALIGN_CENTER)
        self.box.Add(self.go_button, border=10, flag=wx.ALL | wx.ALIGN_CENTER)

        self.SetSizer(self.box)
        self.box.Fit(self)

    def on_go_button(self, event):
        recruits = self.recruits_control.value()
        threshold = self.threshold_control.value()
        self.parent.set_params(recruits, threshold)
        self.parent.show_graph()


class GraphView(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent=parent)
        self.parent = parent

        self.data_gen = DataGen(parent.recruits, parent.threshold)
        self.data = self.data_gen.next()
        self.paused = False

        self.dpi = 100
        self.fig = Figure((10.0, 6.0), dpi=self.dpi)
        self.axes = self.fig.add_subplot(111, label=np.random.random())
        pylab.setp(self.axes.get_xticklabels(), visible=False)
        pylab.setp(self.axes.get_yticklabels(), visible=False)

        self.canvas = FigCanvas(self, -1, self.fig)

        self.speed = speed_wrap(init_speed)
        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.on_timer, self.timer)
        self.timer.Start(self.speed)

        self.speed_control = wx.Slider(self, -1, init_speed, min_speed, max_speed, \
                                      size=(300, 40), style=wx.SL_HORIZONTAL | wx.SL_LABELS)
        self.speed_control.Bind(wx.EVT_SLIDER, self.on_change_speed)

        self.speed_box = wx.BoxSizer(wx.VERTICAL)
        self.speed_box.Add(self.speed_control, border=5, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL)
        self.speed_box.Add(wx.StaticText(self, -1, "Simulation Speed"), flag=wx.ALL | wx.ALIGN_CENTER)
        self.speed_box.AddSpacer(20)

        self.pause_button = wx.Button(self, -1, "Pause")
        self.Bind(wx.EVT_BUTTON, self.on_pause_button, self.pause_button)
        self.Bind(wx.EVT_UPDATE_UI, self.on_update_pause_button, self.pause_button)

        self.controls_box = wx.BoxSizer(wx.HORIZONTAL)
        self.controls_box.Add(self.speed_box, border=5, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL)
        self.controls_box.AddSpacer(150)
        self.controls_box.Add(self.pause_button, border=5, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL)

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
        nx.draw_networkx(self.data, ax=self.axes)
        self.canvas.draw()

    def on_timer(self, event):
        if not self.paused:
            self.data = self.data_gen.next()
            self.draw_plot()


class StatsView(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent=parent)
        self.parent = parent

        self.stats_box = wx.BoxSizer(wx.VERTICAL)
        self.stats_box.AddSpacer(30)
        self.stats_box.Add(wx.StaticText(self, -1, "Statistics for this pyramid scheme:"), \
                           flag=wx.ALL | wx.ALIGN_CENTER)
        self.stats_box.AddSpacer(10)
        self.stats_box.Add(wx.StaticText(self, -1, "n nodes were reached"), \
                           flag=wx.ALL | wx.ALIGN_CENTER)
        self.stats_box.Add(wx.StaticText(self, -1, "n nodes participated in the scheme"), \
                           flag=wx.ALL | wx.ALIGN_CENTER)
        self.stats_box.Add(wx.StaticText(self, -1, "n% of those who participated gained money"), \
                           flag=wx.ALL | wx.ALIGN_CENTER)
        self.stats_box.AddSpacer(20)
        self.again_button = wx.Button(self, -1, "Play again")
        self.Bind(wx.EVT_BUTTON, self.on_again_button, self.again_button)
        self.stats_box.Add(self.again_button, flag=wx.ALL | wx.ALIGN_CENTER)

        self.SetSizer(self.stats_box)
        self.stats_box.Fit(self)

    def on_again_button(self, event):
        #self.parent.reset_params()
        self.parent.show_params()


class MainFrame(wx.Frame):
    title = 'EE126 Project: Pyramid Scheme'

    def __init__(self):
        wx.Frame.__init__(self, None, -1, self.title)

        self.recruits = init_recruits
        self.threshold = init_threshold

        self.params_view = ParamsView(self)
        self.graph_view = GraphView(self)
        self.stats_view = StatsView(self)
        self.show_params()

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.params_view, 1, wx.EXPAND)
        self.sizer.Add(self.graph_view, 1, wx.EXPAND)
        self.sizer.Add(self.stats_view, 1, wx.EXPAND)
        self.SetSizer(self.sizer)

    def set_params(self, recruits, threshold):
        self.recruits = recruits
        self.threshold = threshold

    def reset_params(self):
        self.recruits = init_recruits
        self.threshold = init_threshold

    def show_params(self):
        self.params_view.Show()
        self.graph_view.Hide()
        self.stats_view.Hide()
        self.SetInitialSize((300, 200))

    def show_graph(self):
        self.params_view.Hide()
        self.graph_view.Show()
        self.stats_view.Hide()
        self.SetInitialSize((1000, 700))

    def show_stats(self):
        self.params_view.Hide()
        self.graph_view.Hide()
        self.stats_view.Show()
        self.SetInitialSize((400, 200))


if __name__ == '__main__':
    app = wx.App()
    app.frame = MainFrame()
    app.frame.Show()
    app.MainLoop()
