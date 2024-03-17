import tkinter as tk
from tkinter import ttk
from tkinter.filedialog import asksaveasfilename
from tkinter.messagebox import askokcancel, showerror
from tkinter.filedialog import askopenfilename
from pathlib import Path
from colorsys import hsv_to_rgb, rgb_to_hsv
from numpy import array, meshgrid, squeeze
from scipy.interpolate import NearestNDInterpolator
from itertools import product
from random import randint
from PIL import ImageTk, Image

__fixedcolors = product((0,5,15,178,240,250,255),repeat=3)
BG = '#444444'
FG = '#FFFFFF'

def __get_resource(filename,anchor='colornamespace'):
    try:
        from importlib.resources import files, as_file
    except ImportError:
        pass
    else:
        return as_file(files(anchor).joinpath(filename))
    try:
        from importlib.resources import path
    except ImportError:
        pass
    else:
        return path(anchor,filename)
    try:
        from pkg_resources import resource_filename
    except ImportError:
        pass
    else:
        return resource_filename(anchor,filename)


def randomcolor() -> str:
    '''Generate a random color hex value'''
    r = randint(0,255)
    g = randint(0,255)
    b = randint(0,255)
    return f'#{r:02X}{g:02X}{b:02X}'

def get_color(old_colors=[]) -> str:
    '''Select a color at random from __fixedcolors or select a random color'''
    remcolors = [c for c in __fixedcolors if c not in old_colors]
    if len(remcolors) > 1:
        r,g,b = remcolors[randint(0,len(remcolors)-1)]
        return f'#{r:02X}{g:02X}{b:02X}'
    elif len(remcolors) == 1:
        return remcolors[0]
    else:
        return randomcolor()
    

class FileReadError(Exception):
    '''Error returned when file exists but could not be correctly parsed.'''
    def __init__(self, *args: object, filename=None) -> None:
        super().__init__(*args)
        self.filename = filename

class ColorNameMapper(tk.Tk):
    def __init__(self, *args, **kwargs) -> None:
        from matplotlib.colors import ListedColormap
        from itertools import product
        super().__init__(*args,**kwargs)
        self.saved = True
        self.display_index = -1
        self.currentpath = None
        self.colormap = ListedColormap([[1,0,0,1],[1,0,0.5,1],[1,0.25,0,1],[1,1,0,1],[0,1,0,1],[0,0,1,1],[0.6,0,0.6,1],[0.5,0.25,0,1],[0.5,0.5,0.5,1],[0,0,0,1],[1,1,1,1],[0.25,0.25,0.25,1]])
        self.colorstart = [f'#{r:02X}{g:02X}{b:02X}' for r,g,b in product((0,5,35,63,122,185,220,250,255),repeat=3)]
        self.color_names = ['Red','Pink','Orange','Yellow','Green','Blue','Purple','Brown','Gray','Black','White','None']
        self.plottype = tk.Variable(self,value='Saturation-Hue')
        self.plotsettings = {'Saturation-Hue':(99,99),'Value-Hue':(99,99),'Green-Red':(0,255),'Blue-Red':(0,255),'Blue-Green':(0,255)}
        self._cross_section = tk.IntVar(self,value=self.plotsettings[self.plottype.get()][0])
        self._data = []
        self._datamap = None 
        self._datamap_is_old = False
        self._axesmaps = {
            'h':[
                lambda v: ListedColormap([hsv_to_rgb(float(h)/360.0,1,float(v)/100.0) for h in range(360)]),
                360
            ],
            's':[
                lambda v: ListedColormap([hsv_to_rgb(0,float(s)/100.0,float(v)/100.0) for s in range(100)]),
                100
            ],
            'v':[
                lambda s: ListedColormap([hsv_to_rgb(0,float(s)/100.0,float(v)/100.0) for v in range(100)]),
                100
            ],
            'r':[
                lambda b: ListedColormap([(float(r)/255.0,0,float(b)/255.0) for r in range(256)]),
                256
            ],
            'g':[
                lambda b: ListedColormap([(0,float(g)/255.0,float(b)/255.0) for g in range(256)]),
                256
            ],
            'b':[
                lambda g: ListedColormap([(0,float(g)/255.0,float(b)/255.0) for b in range(256)]),
                256
            ],
            'b2':[
                lambda r: ListedColormap([(float(r)/255.0,0,float(b)/255.0) for b in range(256)]),
                256
            ],
            'g2':[
                lambda r: ListedColormap([(float(r)/255.0,float(g)/255.0,0) for g in range(256)]),
                256
            ],
            'r2':[
                lambda g: ListedColormap([(float(r)/255.0,float(g)/255.0,0) for r in range(256)]),
                256
            ]
        }
        self.title('Color Name Mapper')
        self.config(bg=BG)

        self._init_menu()

        self._init_controls()

        self._init_display()

        tk.Frame(self,bg=BG).grid(row=6,column=0,sticky='news')
        self.rowconfigure(5,weight=6)
        self.rowconfigure(1,weight=1)
        self.columnconfigure(1,weight=1)
        self._new_color()
    
    def _init_menu(self):
        self._menubar = tk.Menu(self,bg='#555555')
        self._filemenu = tk.Menu(self._menubar)
        self._editmenu = tk.Menu(self._menubar)
        self._helpmenu = tk.Menu(self._menubar)

        self._menubar.add_cascade(label='File',menu=self._filemenu)
        self._menubar.add_cascade(label='Edit',menu=self._editmenu)
        self._menubar.add_cascade(label='Help',menu=self._helpmenu)

        self._filemenu.add_command(label='New Session',command=self._restart)
        self._filemenu.add_command(label='Load Session',command=self._openfile)
        self._filemenu.add_command(label='Save Session',command=self._save,state='disabled')
        self._filemenu.add_command(label='Save As...',command=self._saveas)
        self._filemenu.add_separator()
        self._filemenu.add_command(label='Save Plot',state='disabled')
        self._filemenu.add_command(label='Save Report',state='disabled')
        self._filemenu.add_separator()
        self._filemenu.add_command(label='Exit',command=self.destroy)

        
        self._editmenu.add_command(label='Undo',command=self._undo)
        self._editmenu.add_command(label='Show Plot',command=self._show_plot)

        self._helpmenu.add_command(label='About',state='disabled')
        self._helpmenu.add_command(label='Instructions',state='disabled')

        self.config(menu=self._menubar)

    def _init_controls(self):
        self._instructions = tk.Label(self,justify=tk.CENTER,text='Choose the name that best matches the color shown.',wraplength=200,bg=BG,fg=FG)
        self._instructions.grid(row=0,column=0,sticky='news')

        self._current_color = '#FFFFFF'
        self._colordisplay = tk.Frame(self,height=100,width=100,background=self._current_color,bd=4,relief='raised')
        self._colordisplay.grid(row=1,column=0,sticky='news',padx=15,pady=10)

        self._control_panel = tk.Frame(self,bg=BG)
        self._startbutton = tk.Button(self._control_panel,command=lambda:self._review(0),bg=BG,fg=FG)
        try:
            self._startimg = Image.open(__get_resource('icons/tostartarrow.png'))
            self._startimg = ImageTk.PhotoImage(self._startimg.resize((18,18),Image.ANTIALIAS))
            self._startbutton.config(image=self._startimg)
        except Exception:
            self._startbutton.config(text='Start')
        
        self._backbutton = tk.Button(self._control_panel,command=lambda:self._review(dir=-1),bg=BG,fg=FG)
        try:
            self._backimg = Image.open(__get_resource('leftarrow.png'))
            self._backimg = ImageTk.PhotoImage(self._backimg.resize((18,18),Image.ANTIALIAS))
            self._backbutton.config(image=self._backimg)
        except Exception:
            self._backbutton.config(text='Prev')
        
        self._endbutton = tk.Button(self._control_panel,command=lambda:self._review(-1),bg=BG,fg=FG)
        try:
            self._endimg = Image.open(__get_resource('toendarrow.png'))
            self._endimg = ImageTk.PhotoImage(self._endimg.resize((18,18),Image.ANTIALIAS))
            self._endbutton.config(image=self._endimg)
        except Exception:
            self._endbutton.config(text='End')
        
        self._fwdbutton = tk.Button(self._control_panel,command=lambda:self._review(dir=1),bg=BG,fg=FG)
        try:
            self._fwdimg = Image.open(__get_resource('rightarrow.png'))
            self._fwdimg = ImageTk.PhotoImage(self._fwdimg.resize((18,18),Image.ANTIALIAS))
            self._fwdbutton.config(image=self._fwdimg)
        except Exception:
            self._fwdbutton.config(text='Next')
        
        self._undobutton = tk.Button(self._control_panel,command=self._undo,bg=BG,fg=FG)
        try:
            self._undoimg = Image.open(__get_resource('undoarrow.png'))
            self._undoimg = ImageTk.PhotoImage(self._undoimg.resize((18,18),Image.ANTIALIAS))
            self._undobutton.config(image=self._undoimg)
        except Exception:
            self._undobutton.config(text='Undo')
        
        self._startbutton.pack(side='left',anchor='w',padx=2,pady=4)
        self._backbutton .pack(side='left',anchor='w',padx=0,pady=4)
        self._undobutton .pack(side='left',anchor='w',padx=6,pady=4)
        self._fwdbutton  .pack(side='left',anchor='w',padx=0,pady=4)
        self._endbutton  .pack(side='left',anchor='w',padx=2,pady=4)

        self._control_panel.grid(row=3,column=0)

        self._buttonpanel = tk.Frame(self,bg=BG)
        self._buttons = [
            tk.Button(self._buttonpanel,text=c,width=7,command=lambda n=idx:self._record_choice(n),justify=tk.CENTER,bg=BG,fg=FG)
            for idx, c in enumerate(self.color_names)
        ]
        for i,b in enumerate(self._buttons):
            r = i//4
            c = i%4
            b.grid(row=r,column=c,padx=1,pady=1,sticky='news')
        for r in range(self._buttonpanel.grid_size()[1]):
            self._buttonpanel.rowconfigure(r,weight=1)
        for c in range(self._buttonpanel.grid_size()[0]):
            self._buttonpanel.columnconfigure(c,weight=1)
        self._buttonpanel.grid(row=4,column=0,sticky='ew',padx=2,pady=2)

        self._infopanel = tk.Frame(self,bg=BG)
        self._count_label = tk.Label(self._infopanel,text="Response 1 / 0 - ???",justify='center',bg=BG,fg=FG)
        self._infopanel.grid(row=2,column=0,sticky='ew',padx=2,pady=2)
        self._count_label.pack(anchor='e',side=tk.LEFT,padx=4,pady=4)

        self._filepanel = tk.Frame(self,bg=BG,pady=5,padx=5,bd=3,relief='groove')
        self._showplotbutton = tk.Button(self._filepanel,bg=BG,fg=FG,text='Show Map',command=self._show_plot)
        self._loaddatabutton = tk.Button(self._filepanel,bg=BG,fg=FG,text='Load',command=self._openfile)
        self._savedatabutton = tk.Button(self._filepanel,bg=BG,fg=FG,text='Save',command=self._save,state='disabled')
        self._filepanel.grid(row=5,column=0,pady=3,sticky='n')
        self._loaddatabutton.pack(side='left',anchor='w',padx=2)
        self._savedatabutton.pack(side='left',anchor='w',padx=2)
        self._showplotbutton.pack(side='left',anchor='w',padx=8)
    
    def _init_display(self):
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

        self._plotframe = tk.Frame(self,width=300,height=500,bg=BG)

        w = 5
        h = 3.5
        t = 0.45

        self._displayfigure = Figure(dpi=100,figsize=(w,h))
        self._displaycanvas = FigureCanvasTkAgg(self._displayfigure,master=self._plotframe)
        self._displaycanvas.get_tk_widget().grid(row=0,column=1,sticky='news')
        self._axes  = self._displayfigure.add_axes((0.0,0.0,1.0,1.0))
        self._xfigure = Figure(dpi=100,figsize=(w,t))
        self._xcanvas = FigureCanvasTkAgg(self._xfigure,master=self._plotframe)
        self._xcolor = self._xfigure.add_axes((0.0,0.0,1.0,1.0))
        self._xcanvas.get_tk_widget().grid(row=1,column=1,sticky='ew',pady=4)
        self._yfigure = Figure(dpi=100,figsize=(t,h))
        self._ycanvas = FigureCanvasTkAgg(self._yfigure,master=self._plotframe)
        self._ycolor = self._yfigure.add_axes((0.0,0.0,1.0,1.0))
        self._ycanvas.get_tk_widget().grid(row=0,column=0,sticky='ns',padx=4)
        self._colorpeek_viewer = tk.Frame(self._plotframe,bg=BG,bd=2,relief=tk.SUNKEN)
        self._colorpeek_viewer.grid(row=1,column=0,sticky='news',padx=4,pady=4)

        self._axes.set_xticks([])
        self._axes.set_yticks([])
        self._xcolor.set_xticks([])
        self._xcolor.set_yticks([])
        self._xcolor.set_ybound(0,1)
        self._xcolor.set_xbound(0,360)
        self._ycolor.set_xticks([])
        self._ycolor.set_yticks([])
        self._ycolor.set_xbound(0,1)
        self._ycolor.set_ybound(0,100)
        self._displaycanvas.draw()
        self._xcanvas.draw()
        self._ycanvas.draw()

        self._plot_controls = tk.Frame(self._plotframe,bg=BG)
        self._refreshbutton = tk.Button(self._plot_controls,text='Refresh',command=self._display_map,bg=BG,fg=FG)
        try:
            self._refreshimg = Image.open(__get_resource('refresh_reload_icon.png'))
            self._refreshimg = ImageTk.PhotoImage(self._refreshimg.resize((24,24),Image.ANTIALIAS))
            self._refreshbutton.config(image=self._refreshimg)
        except Exception:
            self._refreshbutton.config(text='Undo')
        self._refreshbutton.pack(side='left',anchor='w',padx=2,pady=4)
        self._plot_selector = ttk.Combobox(self._plot_controls,state='readonly',values=tuple(self.plotsettings.keys()),textvariable=self.plottype)
        self._plot_selector.bind_all("<<ComboboxSelected>>",self._switchplot)
        self._plot_selector.pack(side='left',anchor='w',padx=5,pady=4)
        self._cross_section_label = tk.Label(self._plot_controls,justify='right',text='Value:',fg=FG,bg=BG)
        self._cross_section_label.pack(side='left',anchor='w',padx=1,pady=4)
        self._cross_section_select = ttk.Spinbox(self._plot_controls,justify='center',format='%3.0f',from_=0,to=100,command=self._display_map,textvariable=self._cross_section,width=8)
        self._cross_section_select.bind_all('<Return>',self._display_map)
        self._cross_section_select.pack(side='left',anchor='w',padx=2,pady=4)

        self._plot_controls.grid(row=2,column=0,columnspan=2,sticky='ew',pady=3)

        self._plotframe.columnconfigure(1,weight=1)
        self._plotframe.rowconfigure(0,weight=1)
        self._displayfigure.canvas.callbacks.connect('motion_notify_event',self._colorpeek)
        self._displayfigure.canvas.callbacks.connect('figure_leave_event',self._colorpeek_off)

    
    def _record_choice(self,idx):
        if self.display_index == -1:
            self._data.append((self._current_color,idx))
        else:
            self._data[self.display_index] = (self._data[self.display_index][0],idx)
        self._datamap_is_old = True
        self.saved = False
        self._savedatabutton.config(state='normal')
        self._filemenu.entryconfig(3,state='normal')
        self._update_count()
        self._new_color()
        if self.display_index == (len(self._data)-1):
            self._review(-1)
            
    
    def _new_color(self):
        if self.display_index == -1:
            self._current_color = get_color([a for *a,_ in self._data])
            self._colordisplay.config(bg=self._current_color)
        else:
            self._review(dir=0)
    
    def _update_count(self):
        if self.display_index == -1:
            self._count_label.config(text=f'Response {len(self._data)+1:d} / {len(self._data):d} - ???')
        else:
            self._count_label.config(text=f'Response {self.display_index+1:d} / {len(self._data):d} - {self.color_names[self._data[self.display_index][1]]!s}')
    
    def _review(self,idx=None,dir=None):
        if idx is not None:
            if idx < -1:
                idx = -1
            if idx >= len(self._data):
                idx = -1
            self.display_index = int(idx)
        elif dir is not None:
            if dir != 0:
                self.display_index += int(dir/abs(dir))
        if self.display_index < -1:
            self.display_index = int(len(self._data) + self.display_index)
        if self.display_index >= len(self._data):
            self.display_index = int(-1)

        self._update_count()
        if self.display_index >= 0:
            for B in self._buttons:
                B.config(state='disabled')
            self._colordisplay.config(bg=self._data[self.display_index][0])
            self._fwdbutton.config(state='normal')
            self._endbutton.config(state='normal')
            if self.display_index == 0:
                self._startbutton.config(state='disabled')
                self._backbutton.config(state='disabled')
        else:
            for B in self._buttons:
                B.config(state='normal')
            self._colordisplay.config(bg=self._current_color)
            self._endbutton.config(state='disabled')
            self._fwdbutton.config(state='disabled')
            self._startbutton.config(state='normal')
            self._backbutton.config(state='normal')
    
    def _restart(self):
        if not self.saved:
            resp = askokcancel('Save Session?',"The current session has not been saved. If you continue, any unsaved answers will be lost. Continue?")
            if not resp:
                return
        self._data = []
        self.currentpath = None 
        self.saved = True
        self._savedatabutton.config(state='disabled')
        self._filemenu.entryconfig(3,state='disabled')
        self._new_color()
        self._update_count()
        self._clear_map()
    
    def _undo(self):
        if self.display_index==-1:
            self._review(len(self._data)-1)
        for B in self._buttons:
            B.config(state='normal')
        self._update_count()
    
    def _saveas(self):
        fpath = asksaveasfilename(parent=self,title='Save Color Map',initialdir='~/Documents',filetypes=[('JSON','*.json'),('Text','*.txt'),('CSV','*.csv')],defaultextension='.txt')
        fpath = Path(fpath)
        if fpath.exists():
            answ = askokcancel(title="File Exists",message=f"The file {fpath.name} already exists. Are you sure you want to replace it?")
            if not answ:
                return
        try:
            self._save_to(fpath)
        except Exception as err:
            if len(err.args) > 0:
                msg = err.args[0]
            else:
                msg = 'Unknown Error'
            showerror('Save Error',f'Error! The file could not be saved.\n{msg}')
    
    def _save(self):
        if self.currentpath is None:
            self._saveas()
        else:
            try:
                self._save_to(self.currentpath)
            except Exception as err:
                if len(err.args) > 0:
                    msg = err.args[0]
                else:
                    msg = 'Unknown Error'
                showerror('Save Error',f'Error! The file could not be saved.\n{msg}')

    def _save_to(self,fpath):
        from json import dumps
        if fpath.suffix=='.json':
            d = {}
            for c,l in self._data:
                if c in d.keys():
                    d[c] += [self.color_names[l]]
                else:
                    d[c] = [self.color_names[l]]
            d = dumps(d)
            with fpath.open('w') as out:
                out.write(d)
        elif fpath.suffix=='.txt':
            d = '\n'.join([':'.join([c,self.color_names[i]]) for c,i in self._data])
            with fpath.open('w') as out:
                out.write(d)
        elif fpath.suffix=='.csv':
            pass
            d = [['r','g','b','idx','color']]
            for c,i in self._data:
                d += [[int(c[1:3],base=16),int(c[3:5],base=16),int(c[5:7],base=16),i,self.color_names[i]]]
            with fpath.open('w') as out:
                out.write('\n'.join([','.join([str(b) for b in a]) for a in d]))
        self.saved = True
        self._savedatabutton.config(state='disabled')
        self._filemenu.entryconfig(3,state='disabled')
        self.currentpath = fpath
    
    def _openfile(self):
        msg = None
        try:
            self._open()
        except FileNotFoundError as err:
            if len(err.args) > 0:
                msg = err.args[0]
            else:
                msg = 'Unknown Error'
            msg = f'The file does not exist: {msg}'
        except FileReadError as err:
            if len(err.args) > 0:
                msg = err.args[0]
            else:
                msg = 'Unknown Error'
            msg = f'Error reading data file: {msg}'
        if msg is not None:
            showerror('Save Error',f'Error! The file could not be saved.\n{msg}')
    
    def _open(self):
        from json import loads, JSONDecodeError
        f = askopenfilename(parent=self,title='Open Color Map',initialdir='~/Documents',filetypes=[('JSON','*.json'),('Text','*.txt'),('CSV','*.csv')],defaultextension='.txt')
        f = Path(f)
        try:
            with f.open('r') as st:
                d = st.read()
            if f.suffix=='.json':
                d = loads(d)
                d = [(k,v) for k,v in d.items()]
                if all(len(v)==1 and hasattr(v[0],'lower') for _,v in d):
                    d = [(k,self.color_names.index(v[0])) for k,v in d]
            elif f.suffix=='.txt':
                d = [a.split(':') for a in d.split('\n') if not a.startswith('%')]
                d = [(a,int(b)) for a,b in d]
            elif f.suffix=='.csv':
                d = d.split('\n')
                d = [[int(q) for q in a.split(',')[:-1]] for a in d[1:]]
                d = [(f'#{r:02X}{g:02X}{b:02X}',i) for r,g,b,i,*_ in d]
            assert all(k.startswith('#') for k,v in d)
            assert all(v >= 0 and v < len(self.color_names) and v==round(v) for _,v in d)
        except JSONDecodeError as err:
            raise FileReadError(f'Could not read JSON file: {err.msg}',filename=f.absolute()) from None
        except (ValueError,TypeError,AssertionError):
            raise FileReadError(f'Invalid data encountered in {f.suffix.capitalize()[1:]} file.',filename=f.absolute()) from None
        else:
            self._data = d
            self._update_count()
            self._new_color()
        self.saved = True
        self._savedatabutton.config(state='disabled')
        self._filemenu.entryconfig(3,state='disabled')
        self.currentpath = f
        self._datamap_is_old = True
    
    def _show_plot(self):
        if self._plotframe.winfo_ismapped():
            self._plotframe.grid_forget()
            self._editmenu.entryconfig(2,label='Show Map')
            self._showplotbutton.config(text='Show Map')
            self._plotframe.columnconfigure(1,minsize=200)
        else:
            self._plotframe.grid(row=0,column=1,rowspan=6,padx=5,pady=5,sticky='news')
            self._editmenu.entryconfig(2,label='Hide Map')
            self._showplotbutton.config(text='Hide Map')
            self._plotframe.columnconfigure(1,minsize=0)
    
    def _set_xmap(self,mapname):
        xmapvals = array([list(range(self._axesmaps[mapname][1]))]*2)
        self._xcolor.cla()
        self._xcolor.set_xticks([])
        self._xcolor.set_yticks([])
        self._xcolor.pcolormesh(xmapvals,cmap = self._axesmaps[mapname][0](self._cross_section.get()))
        self._xcolor.set_xbound(0,self._axesmaps[mapname][1])
        self._axes.set_xbound(0,int(self._axesmaps[mapname][1]/2))
        self._xcanvas.draw()
    
    def _set_ymap(self,mapname):
        ymapvals = array([[a,a] for a in range(self._axesmaps[mapname][1])])
        self._ycolor.cla()
        self._ycolor.set_xticks([])
        self._ycolor.set_yticks([])
        self._ycolor.pcolormesh(ymapvals,cmap = self._axesmaps[mapname][0](self._cross_section.get()))
        self._ycolor.set_ybound(0,self._axesmaps[mapname][1])
        self._axes.set_ybound(0,int(self._axesmaps[mapname][1]/2))
        self._ycanvas.draw()

    def _display_map(self,event=None):
        self._clear_map()
        
        if self._datamap_is_old:
            self._build_map()
        
        if self.plottype.get() == 'Saturation-Hue':
            self._set_xmap('h')
            self._set_ymap('s')
            self._cross_section_label.config(text='Value %:')
            dispmap = self._datamap[:,:,int(float(self._cross_section.get())/100.0*(self._datamap.shape[2]-1))]
            dispmap = dispmap.transpose()
        elif self.plottype.get() == 'Value-Hue':
            self._set_xmap('h')
            self._set_ymap('v')
            self._cross_section_label.config(text='Saturation %:')
            dispmap = squeeze(self._datamap[:,int(float(self._cross_section.get())/100.0*(self._datamap.shape[1]-1)),:])
            dispmap = dispmap.transpose()
        elif self.plottype.get() == 'Green-Red':
            self._set_xmap('r')
            self._set_ymap('g')
            self._cross_section_label.config(text='Blue %:')
            dispmap = self._datamap[:,:,int(float(self._cross_section.get())/100.0*(self._datamap.shape[1]-1))]
        elif self.plottype.get() == 'Blue-Red':
            self._set_xmap('r2')
            self._set_ymap('b')
            self._cross_section_label.config(text='Green %:')
            dispmap = squeeze(self._datamap[int(float(self._cross_section.get())/100.0*self._datamap.shape[0]),:,:])
            dispmap = dispmap.transpose()
        elif self.plottype.get() == 'Blue-Green':
            self._set_xmap('g2')
            self._set_ymap('b2')
            self._cross_section_label.config(text='Red %:')
            dispmap = squeeze(self._datamap[:,int(float(self._cross_section.get())/100.0*(self._datamap.shape[1]-1)),:])
            dispmap = dispmap.transpose()

        self._axes.pcolormesh(dispmap,cmap=self.colormap,vmin=0,vmax=len(self.color_names))
        self._displaycanvas.draw()
    
    def _build_map(self):
        if self.plottype.get() in ('Saturation-Hue','Value-Hue'):
            d = [rgb_to_hsv(*(float(int(c[a:a+2],base=16))/255.0 for a in (1,3,5))) + (i,) for c,i in self._data]
            d = [(int(a[0]*359),int(a[1]*99),int(a[2]*99),a[3]) for a in d]
            cv = [a for *a,_ in d]
            for i in range(0,360,5):
                if (i,0,99) not in cv:
                    d.append((i,0,99,10))
                for j in range(0,100,5):
                    if (i,0,0) not in cv:
                        d.append((i,j,0,9))
            [X,Y,Z] = meshgrid([range(0,360,2)],[range(0,100,2)],[range(0,100,2)],indexing='ij')
            interp = NearestNDInterpolator([a for *a,_ in d],[a for *_,a in d])
        else:
            d = [tuple(int(c[a:a+2],base=16) for a in (1,3,5)) + (i,) for c,i in self._data]
            [X,Y,Z] = meshgrid([range(0,256,2)],[range(0,256,2)],[range(0,256,2)])
            interp = NearestNDInterpolator([a for *a,_ in d],[a for *_,a in d])
        self._datamap = interp(X,Y,Z)
        self._datamap_is_old = False
        
    def _switchplot(self,event):
        self._datamap_is_old = True
        self._display_map()
    
    def _clear_map(self):
        self._axes.cla()
        self._axes.set_yticks([])
        self._axes.set_xticks([])
        self._xcolor.cla()
        self._xcolor.set_yticks([])
        self._xcolor.set_xticks([])
        self._ycolor.cla()
        self._ycolor.set_yticks([])
        self._ycolor.set_xticks([])
    
    def _colorpeek(self,event=None):
        if self.plottype.get() == 'Saturation-Hue':
            h = event.xdata/self._axes.get_xbound()[1]
            s = event.ydata/self._axes.get_ybound()[1]
            v = self._cross_section.get()/100.0
            r,g,b = hsv_to_rgb(h,s,v)
        elif self.plottype.get() == 'Value-Hue':
            h = event.xdata/self._axes.get_xbound()[1]
            v = event.ydata/self._axes.get_ybound()[1]
            s = self._cross_section.get()/100.0
            r,g,b = hsv_to_rgb(h,s,v)
        elif self.plottype.get() == 'Saturation-Hue':
            h = event.xdata/self._axes.get_xbound()[1]
            s = event.ydata/self._axes.get_ybound()[1]
            v = self._cross_section.get()/100.0
            r,g,b = hsv_to_rgb(h,s,v)
        elif self.plottype.get() == 'Green-Red':
            r = event.xdata/self._axes.get_xbound()[1]
            g = event.ydata/self._axes.get_ybound()[1]
            b = self._cross_section.get()/100.0
        elif self.plottype.get() == 'Blue-Red':
            r = event.xdata/self._axes.get_xbound()[1]
            b = event.ydata/self._axes.get_ybound()[1]
            g = self._cross_section.get()/100.0
        elif self.plottype.get() == 'Blue-Green':
            g = event.xdata/self._axes.get_xbound()[1]
            b = event.ydata/self._axes.get_ybound()[1]
            r = self._cross_section.get()/100.0
        
        r,g,b = tuple(int(c*255) for c in (r,g,b))
        self._colorpeek_viewer.config(bg=f'#{r:02X}{g:02X}{b:02X}')

    def _colorpeek_off(self,event=None):
        self._colorpeek_viewer.config(bg=BG)


        