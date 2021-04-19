from matplotlib import pyplot as plt
from matplotlib.widgets import Button, TextBox
import numpy as np
import os
from Cplotter.utils import add_points, delete_points, get_ind
from Cplotter.edit_axis import EditAxis
from Cplotter.version import __version__, __last_update_in__

class InteractivePlot:

    def __init__(self, fig=None, specialfunc=None, saveto=None):
        self._intro_line = 0
        self._print_intro()
        self.figure = []
        self.fignum = []
        self.axlist = []
        self.axobjlist = []
        self._lastline = None
        self._markedline = None
        self._selected = []
        self._crossed = []
        self._doindex = -1
        self._undostack = []
        self._redostack = []
        self._specialfunc = specialfunc
        self._savestate = 'o'
        self._usermessages = []
        self._usermessages_temp = ''
        self._message_updown_count = 0
        self._keep_message_shown = False
        self._message_updown_marathon = False
        self._showingmessage = []
        self.cids = {'key': [], 'button': [], 'resize': []}
        plt.rcParams['keymap.all_axes'].remove('a')
        if plt.get_fignums() == []: plt.figure()
        self.dataset = []

        if fig is None: fig = [plt.figure(i) for i in plt.get_fignums()]
        if isinstance(fig, (list, tuple)):
            for fg in fig:
                self.figure.append(fg)
                self.fignum.append(fg.number)
                self.cids['key'].append(fg.canvas.mpl_connect('key_press_event', self._on_key))
                self.cids['button'].append(fg.canvas.mpl_connect('button_press_event', self._on_button))
                # self.cids['resize'].append(fg.canvas.mpl_connect('resize_event', self._on_resize))
        else:
            self.figure = [fig]
            self.fignum = [fig.number]
            self.cids['key'].append(fig.canvas.mpl_connect('key_press_event', self._on_key))
            self.cids['key'].append(fig.canvas.mpl_connect('button_press_event', self._on_button))
            # self.cids['resize'].append(fig.canvas.mpl_connect('resize_event', self._on_resize))

        for fn in self.fignum: self.axlist += plt.figure(fn).axes
        self.axobjlist = [EditAxis(ax) for ax in self.axlist] if self.axlist != [] else []
        self._axmap = [[ax for ax in self.axlist] for _ in range(2)]
        self.savedfigs = dict([(fignum, []) for fignum in self.fignum])
        if not isinstance(saveto, (list, tuple)):
            self._saveto = [saveto for _ in self.fignum]
        else:
            self._saveto = saveto + [None] * (len(self.fignum) - len(saveto))
        self._defsaveto = list(np.copy(self._saveto))
        self.update_dataset()
        self._widgetlist = [[] for _ in self.fignum]
        self._subplotpars = []
        for i, fn in enumerate(self.fignum):
            plt.figure(fn)
            self._subplotpars.append(vars(plt.figure(fn).subplotpars).copy())
            self._subplotpars[i].pop('validate')
            plt.subplots_adjust(bottom=0.25)
            self._set_buttons(False, True, True)

        plt.show()

    def _print_intro(self):
        print(f'\n\t\033[4m\u001b[34;1m\u001b[1mWelcome to the Interactive Plotting Tool\033[0m')
        print('\tDeveloped by Aritra Chakrabarty')
        print(f'\tCurrent version {__version__}')
        print(f'\tDeveloped in 2018, last update in {__last_update_in__}')
        print('\u001b[1m')
        print('\n\t------ Instructions -------\n')

        def write(text):
            self._intro_line += 1
            print(f'  {self._intro_line:2d}. {text}')

        write('Click the left MB to select a plot (line2D)')
        write('Click the right MB to delete a single point from a plot')
        write('To select multiple points take the cursor everytime near a point and press \'a\'')
        write('To delete all the points selected press \'d\'')
        write('Press \'u\' to update the axis X & Y limits')
        write('In case multiple plots have a common point of intersection, to delete that point from one of these plots '
              'select the line first by clicking left MB and then press \'a\' to select the point or directly delete by '
              'clicking right MB. Otherwise the tool will decide by itself which plot to delete the point from.')
        write('Undo a change by pressing \'Ctrl+z\' and redo by pressing \'Ctrl+Shift+z\' or \'Ctrl+y\'')
        write('To pre-provide a path for saving a plot use the \'saveto\' kwarg')
        write('To save a plot to any path type "save /full/path [optional argument]" in the \'I/O\' textbox. The '
              'optional argument is either \'-c\' for the plot including the textboxes and buttons or \'-o\' for the '
              'figure only')
        write('Press the \'Save\' button for quicksaving. If a path is pre-provided the plot is saved to that path, '
              'otherwise saves to the last path typed in the textbox. If no path is found, it shows a warning message')
        write('Also, you can type standard Python commands in the \'I/O\' textbox. These commands, however, are not '
              'undo/redo-able')
        write('Press \'Shift+q\' to release the control')
        print('\n\n')

    def _on_resize(self, event):
        self._figsize = plt.gcf()
        raise NotImplementedError

    def _reset(self, event):
        raise NotImplementedError

    def show_original_figure(self, figind):
        for widget in self._widgetlist[figind]:
            widget.ax.set_visible(False)
            widget.set_active(False)
        if self._crossed != []:
            for l in self._crossed: l.set_visible(False)
        if self._markedline is not None: self._markedline.set_visible(False)
        plt.subplots_adjust(**self._subplotpars[figind])

    def show_current_figure(self, figind, current_subplotpars):
        plt.subplots_adjust(**current_subplotpars)
        if self._crossed != []:
            for l in self._crossed: l.set_visible(False)
        if self._markedline is not None: self._markedline.set_visible(True)
        for widget in self._widgetlist[figind]:
            widget.set_active(True)
            widget.ax.set_visible(True)

    def _evaluate_message(self, text):
        self._textbox = self._widgetlist[self.fignum.index(plt.gcf().number)][1]
        self._keep_message_shown = False
        self._message_updown_count = 0
        self._textbox.eventson = False
        self._message_updown_marathon = False
        self._textbox.set_val('')
        if text is None or text == '':
            return
        self._usermessages.append(text)
        if text.split()[0] == 'save':
            self._savestate = 'o'
            figind = self.fignum.index(plt.gcf().number)
            self._textbox = self._widgetlist[figind][1]
            textsp = text.split()
            if textsp[-1][0] == '-' and textsp[-1] != '-default':
                if textsp[-1].lower() == '-c':
                    self._savestate = 'c'
                elif textsp[-1].lower() == '-o':
                    self._savestate = 'o'
                else:
                    self._typemessage('Invalid command!', color='r')
                    return
                del textsp[-1]
            if len(textsp) == 2:
                self._saveto[figind] = textsp[1] if textsp[1] != '-default' else self._defsaveto[figind]
            elif len(textsp) != 1:
                self._typemessage('Invalid command!', color='r')
                return
            if self._saveto[figind] is None:
                self._typemessage('Saving path not given. Type: save /full/path/name', color='b')
            else:
                self._saveto[figind] = self._saveto[figind].replace('~', os.environ['HOME'])
                if os.path.exists(os.path.dirname(os.path.abspath(self._saveto[figind]))):
                    if self._savestate == 'c': self.savefig(self._saveto[figind], plt.gcf())
                    if self._savestate == 'o':
                        cursp = vars(plt.gcf().subplotpars).copy()
                        cursp.pop('validate', None)
                        self.show_original_plots(figind)
                        self.savefig(self._saveto[figind], plt.gcf())
                        self.show_current_figure(figind, cursp)
                    if os.path.abspath(self._saveto[figind]) not in self.savedfigs[plt.gcf().number]: self.savedfigs[
                        plt.gcf().number].append(os.path.abspath(self._saveto[figind]))
                    self._typemessage('Figure saved to \n' + self._saveto[figind], color='g')
                else:
                    self._typemessage('Directory given in the path does not exist!', color='b')

        elif text.split()[0] == 'spfunc' and len(text.split()) > 1:
            texts = text.split()[1:]
            if self._specialfunc is not None:
                if not isinstance(self._specialfunc, (tuple, list)):
                    funcret = self._specialfunc(*texts, self)
                else:
                    funcret = self._specialfunc[0](*texts, self, *self._specialfunc[1:])
                if funcret is not None: self._typemessage(str(funcret))

        else:
            fig = plt.gcf()
            ax = np.array(fig.axes)
            if len(ax) > 0:
                gspec = ax[0].get_gridspec().get_geometry()
                if gspec == (1, 1):
                    ax = ax[0]
                elif 1 not in gspec:
                    ax = np.reshape(ax, gspec)
            try:
                exec(text)
                plt.draw()
            except:
                self._typemessage('Command not found!', color='r')

    def _typemessage(self, message, color=None):
        self._showingmessage.append(plt.gcf().number)
        if not self._textbox.active: self._textbox.set_active(True)
        message = ''.join(message.split('\n'))
        mes, mfac = '', int(8.4 * plt.gcf().get_figwidth())  # 14 times width of textbox times figure-width
        for i in range(len(message) // mfac + 1): mes += message[i * mfac:(i + 1) * mfac] + '\n'
        self._textbox.eventson = False
        self._textbox.set_val(mes)
        if color:
            self._textbox.text_disp.set_color(color)
        self._textbox.stop_typing()
        self._textbox.set_active(False)
        plt.draw()

    def _quicksave(self, event):
        figind = self.fignum.index(plt.gcf().number)
        self._textbox = self._widgetlist[figind][1]
        if self._saveto[figind] is None:
            self._typemessage('Saving path not given. Type: save /full/path/name', color='b')
        else:
            if os.path.exists(os.path.dirname(os.path.abspath(self._saveto[figind]))):
                if self._savestate == 'c': self.savefig(self._saveto[figind], plt.gcf())
                if self._savestate == 'o':
                    for widget in self._widgetlist[figind]:
                        widget.ax.set_visible(False)
                        widget.set_active(False)
                    if self._crossed != []:
                        for l in self._crossed: l.set_visible(False)
                    if self._markedline is not None: self._markedline.set_visible(False)
                    cursp = vars(plt.gcf().subplotpars).copy()
                    cursp.pop('validate')
                    plt.subplots_adjust(**self._subplotpars[figind])
                    self.savefig(self._saveto[figind], plt.gcf())
                    plt.subplots_adjust(**cursp)
                    if self._crossed != []:
                        for l in self._crossed: l.set_visible(False)
                    if self._markedline is not None: self._markedline.set_visible(True)
                    for widget in self._widgetlist[figind]:
                        widget.set_active(True)
                        widget.ax.set_visible(True)
                if os.path.abspath(self._saveto[figind]) not in self.savedfigs[plt.gcf().number]: self.savedfigs[
                    plt.gcf().number].append(os.path.abspath(self._saveto[figind]))
                self._typemessage('Figure saved to \n' + self._saveto[figind], color='g')
            else:
                self._typemessage('Directory given in the path does not exist!', color='b')

    def update_dataset(self, fig=None, axes=None, lines=None, collections=None):
        if fig is None: fig = [plt.figure(i) for i in self.fignum]
        if axes is None: axes = [fg.axes for fg in fig]
        axesobj = [[self.axobjlist[self.axlist.index(ax)] for ax in x] for x in axes]
        if lines is None: lines = [[ax.lines for ax in x] for x in axes]
        if collections is None: collections = [[axo.collections for axo in axeo] for axeo in axesobj]
        if self.dataset == []: self.dataset = [[[[] for li in lin] for lin in line] for line in lines]
        for i in range(len(fig)):
            figi = self.fignum.index(fig[i].number)
            for j in range(len(axes[i])):
                axi = fig[i].axes.index(axes[i][j])
                for line, err in zip(lines[i][j], axesobj[i][j].get_err()):
                    linei = axes[i][j].lines.index(line)
                    self.dataset[figi][axi][linei] = list(line.get_data()) + err

    def _set_buttons(self, enable_reset, enable_save, enable_io):
        reset_button = Button(plt.axes([0.51, 0.01, 0.1, 0.035]), 'Reset')  # [0.88, 0.01, 0.1, 0.035]
        reset_button.label.set_color('r')
        reset_button.label.set_fontweight('bold')
        reset_button.on_clicked(self._reset)
        if enable_reset:
            reset_button.set_active(True)
        else:
            reset_button.set_active(False)
            reset_button.ax.set_visible(False)
        textbox = TextBox(plt.axes([0.2, 0.06, 0.6, 0.095]), 'I/O',
                          initial='')  # [0.12, 0.01, 0.65, 0.06] [0.05,0.92,0.8,0.07] [0.025, 0.885, 0.75, 0.05]
        textbox.label.set_fontweight('bold')
        textbox.on_submit(self._evaluate_message)
        if enable_io:
            textbox.set_active(True)
        else:
            textbox.set_active(False)
            textbox.ax.set_visible(False)
        save_button = Button(plt.axes([0.39, 0.01, 0.1, 0.035]), 'Save')  # [0.77, 0.01, 0.1, 0.035]
        save_button.label.set_fontweight('bold')
        save_button.on_clicked(self._quicksave)
        if enable_save:
            save_button.set_active(True)
        else:
            save_button.set_active(False)
            save_button.ax.set_visible(False)
        self._widgetlist[self.fignum.index(plt.gcf().number)] = (reset_button, textbox, save_button)
        self._textbox = textbox

    def _remove_buttons(self):
        for i, widget in enumerate(self._widgetlist[self.fignum.index(plt.gcf().number)]):
            if widget.ax in plt.gcf().axes:
                if i == 1: widget.stop_typing()
                widget.ax.remove()

    def savefig(self, filename, fig=None):
        if fig is None:
            for i, fg in enumerate(self.figure):
                if type(filename) != str:
                    fg.savefig(filename[i])
                else:
                    if i == 0:
                        fg.savefig(filename)
                    else:
                        fg.savefig(os.path.splitext(filename)[0] + '_' + str(i) + os.path.splitext(filename)[1])
        elif type(fig) == int:
            plt.figure(fig).savefig(filename)
        else:
            fig.savefig(filename)

    def _on_key(self, event):
        self.ax = event.inaxes
        if self.ax is None:
            return
        if self.ax not in self.axlist:
            self.axlist.append(self.ax)
            self.axobjlist.append(EditAxis(self.ax))
        self.axobj = self.axobjlist[self.axlist.index(self.ax)]
        # print('key', event.key)

        if event.key == 'up':
            if self.ax == self._textbox.ax and (
                    self._textbox.capturekeystrokes or self._message_updown_marathon) and abs(
                self._message_updown_count) < len(self._usermessages):
                if self._message_updown_count == 0:
                    self._usermessages_temp = self._textbox.text
                self._message_updown_count -= 1
                message = self._usermessages[self._message_updown_count]
                self._typemessage(message, color='b')
                self._keep_message_shown = True
                self._message_updown_marathon = True

        if event.key == 'down':
            if self.ax == self._textbox.ax and (
                    self._textbox.capturekeystrokes or self._message_updown_marathon) and abs(
                self._message_updown_count) > 0:
                self._message_updown_count += 1
                if self._message_updown_count == 0:
                    message = self._usermessages_temp if self._usermessages_temp else ''
                else:
                    message = self._usermessages[self._message_updown_count]
                self._typemessage(message, color='b')
                self._keep_message_shown = True
                self._message_updown_marathon = True

        if event.key == 'escape':
            if self.ax == self._textbox.ax and (self._textbox.capturekeystrokes or self._message_updown_marathon):
                self._message_updown_count = 0
                self._keep_message_shown = False
                self._usermessages_temp = ''
                self._typemessage('')
                self._message_updown_marathon = False

        if event.key == 'a':
            xe, ye = event.xdata, event.ydata
            parent_line, xs, ys = self.axobj.get_nearest_PointnLine(xe, ye)
            if self._markedline is not None:
                self._markedline.remove()
                self._markedline = None
            if xs is not None:
                if self._lastline is not None and [xs, ys] in self._lastline.get_xydata().tolist():
                    inds = get_ind(self._lastline, xs, ys)
                    ls = self._lastline
                    cs = self.axobj.collections[self.axobj.lines.index(self._lastline)]
                else:
                    inds = get_ind(parent_line, xs, ys)
                    ls = parent_line
                    cs = self.axobj.collections[self.axobj.lines.index(parent_line)]
                sitem = [inds, ls, cs, self.ax, plt.gcf()]
                if sitem in self._selected:
                    self._crossed[self._selected.index(sitem)].remove()
                    del self._crossed[self._selected.index(sitem)]
                    self._selected.remove(sitem)
                    plt.draw()
                else:
                    self._selected.append(sitem)
                    P, = self.ax.plot(ls.get_xdata(), ls.get_ydata(), ':r', linewidth=4)
                    self._markedline = P
                    P, = self.ax.plot(xs, ys, 'xk')
                    self._crossed.append(P)
                    plt.draw()

        if event.key == 'd':
            if self._markedline is not None:
                self._markedline.remove()
                self._markedline = None
            if self._selected != []:
                selected = [s[:-2] for s in self._selected]
                fig = [s[-1] for s in self._selected]
                ax = [[s[-2]] for s in self._selected]
                delete_points(*list(zip(*selected)))
                plt.draw()
                for P in self._crossed: P.remove()
                self._selected = []
                self._crossed = []
                self.update_dataset(fig, ax)
            if self._doindex != -1:
                for uv, rv in zip(self._undostack[self._doindex + 1:], self._redostack[self._doindex + 1:]):
                    self._undostack.remove(uv)
                    self._redostack.remove(rv)
                self._doindex = -1

        if event.key == 'u':
            if self._markedline is not None:
                self._markedline.remove()
                self._markedline = None
            xlim, ylim = self.ax.get_xlim(), self.ax.get_ylim()
            self.ax.relim()
            self.ax.autoscale()
            self.ax.autoscale_view()
            plt.draw()
            # print('doindex', self._doindex)
            if self._doindex != -1:
                for uv, rv in zip(self._undostack[self._doindex + 1:], self._redostack[self._doindex + 1:]):
                    self._undostack.remove(uv)
                    self._redostack.remove(rv)
                self._doindex = -1
            newxlim, newylim = self.ax.get_xlim(), self.ax.get_ylim()
            self._undostack.append((self._changekeyU, [self.ax, xlim, ylim]))
            self._redostack.append((self._changekeyU, [self.ax, newxlim, newylim]))

        if event.key == 'ctrl+z':
            if abs(self._doindex) <= len(self._undostack):
                func, arg = self._undostack[self._doindex]
                func(*arg)
                self._doindex -= 1

        if event.key == 'ctrl+Z' or event.key == 'ctrl+y':
            if self._doindex < -1:
                self._doindex += 1
                func, arg = self._redostack[self._doindex]
                func(*arg)

        if event.key == 'Q':
            figind = self.fignum.index(plt.gcf().number)
            self.show_original_figure(figind)
            plt.draw()
            fig = self.figure[figind]
            fig.canvas.mpl_disconnect(self.cids['key'][figind])
            fig.canvas.mpl_disconnect(self.cids['button'][figind])
            plt.rcParams['keymap.all_axes'].append('a')

    def _changekeyU(self, ax, xlim, ylim):
        ax.set_xlim(xlim)
        ax.set_ylim(ylim)
        plt.draw()

    def _on_button(self, event):
        self.ax = event.inaxes
        if self.ax == self._textbox.ax:
            self._textbox.set_active(True)
            self._usermessages_temp = ''
            if not self._keep_message_shown:
                self._textbox.set_val('')
            else:
                self._textbox.set_val(self._textbox.text[:-1])
            self._textbox.eventson = True
            if plt.gcf().number in self._showingmessage:
                self._showingmessage.remove(plt.gcf().number)
        if self.ax is None or self.ax.lines == []: return
        if self.ax not in self.axlist:
            self.axlist.append(self.ax)
            self.axobjlist.append(EditAxis(self.ax))
        self.axobj = self.axobjlist[self.axlist.index(self.ax)]

        if event.button == 1:
            if self._markedline is not None:
                self._markedline.remove()
                self._markedline = None
            xe, ye = event.xdata, event.ydata
            nearest_line = self.axobj.get_nearest_PointnLine(xe, ye, distfrom='line')[0]
            if nearest_line is not None:
                self._lastline = nearest_line
                P, = self.ax.plot(self._lastline.get_xdata(), self._lastline.get_ydata(), ':y', linewidth=4)
                self._markedline = P
            plt.draw()

        if event.button == 3:
            if self._markedline is not None:
                self._markedline.remove()
                self._markedline = None
            xe, ye = event.xdata, event.ydata
            parent_line, xs, ys = self.axobj.get_nearest_PointnLine(xe, ye)
            if xs is not None:
                if self._lastline is not None and [xs, ys] in self._lastline.get_xydata().tolist():
                    inds = get_ind(self._lastline, xs, ys)
                    ls = self._lastline
                    cs = self.axobj.collections[self.axobj.lines.index(self._lastline)]
                else:
                    inds = get_ind(parent_line, xs, ys)
                    ls = parent_line
                    cs = self.axobj.collections[self.axobj.lines.index(parent_line)]
                sitem = [inds, ls, cs, self.ax, self.ax.figure]
                vertys = cs[0].get_paths()[inds].vertices if cs[0] is not None else None
                vertxs = cs[1].get_paths()[inds].vertices if cs[1] is not None else None
                pd = [[inds], [ls], [cs]]
                upd = [[inds], [xs], [ys], [vertys], [vertxs], [ls], [cs]]
                if sitem in self._selected:
                    selind = self._selected.index(sitem)
                    sd = [sitem]
                    cd = [self._crossed[selind]]
                    usd = [[selind] + sitem]
                    ucd = [[selind, self._crossed[selind]]]
                else:
                    sd, cd, usd, ucd = None, None, None, None
                datasetpar = [[plt.gcf()], [[self.ax]]]
                self._addNdel(pd, False, sd, False, cd, False, datasetpar)
                if self._doindex != -1:
                    for uv, rv in zip(self._undostack[self._doindex + 1:], self._redostack[self._doindex + 1:]):
                        self._undostack.remove(uv)
                        self._redostack.remove(rv)
                    self._doindex = -1
                self._undostack.append((self._addNdel, (upd, True, usd, True, ucd, True, datasetpar)))
                self._redostack.append((self._addNdel, (pd, False, sd, False, cd, False, datasetpar)))

    def _addNdel(self, plotdata, add2plot, selectdata, add2select, crossdata, add2cross, datasetpar):
        if plotdata is not None:
            if add2plot:
                add_points(*plotdata)
            else:
                delete_points(*plotdata)
            self.update_dataset(*datasetpar)
            plt.draw()
        if selectdata is not None:
            if add2select:
                for sd in selectdata: self._selected.insert(sd[0], sd[1:])
            else:
                for sd in selectdata: self._selected.remove(sd)
        if crossdata is not None:
            if add2cross:
                for cd in crossdata:
                    self.ax.lines.append(cd[1])
                    self._crossed.insert(*cd)
                    plt.draw()
            else:
                for cd in crossdata:
                    cd.remove()
                    self._crossed.remove(cd)
                    plt.draw()
