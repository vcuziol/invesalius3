
#--------------------------------------------------------------------------
# Software:     InVesalius - Software de Reconstrucao 3D de Imagens Medicas
# Copyright:    (C) 2001  Centro de Pesquisas Renato Archer
# Homepage:     http://www.softwarepublico.gov.br
# Contact:      invesalius@cti.gov.br
# License:      GNU - GPL 2 (LICENSE.txt/LICENCA.txt)
#--------------------------------------------------------------------------
#    Este programa e software livre; voce pode redistribui-lo e/ou
#    modifica-lo sob os termos da Licenca Publica Geral GNU, conforme
#    publicada pela Free Software Foundation; de acordo com a versao 2
#    da Licenca.
#
#    Este programa eh distribuido na expectativa de ser util, mas SEM
#    QUALQUER GARANTIA; sem mesmo a garantia implicita de
#    COMERCIALIZACAO ou de ADEQUACAO A QUALQUER PROPOSITO EM
#    PARTICULAR. Consulte a Licenca Publica Geral GNU para obter mais
#    detalhes.
#--------------------------------------------------------------------------
import sys

import wx
import wx.lib.hyperlink as hl
import wx.lib.platebtn as pbtn
from wx.lib.pubsub import pub as Publisher

import data.slice_ as slice_
import constants as const
import gui.dialogs as dlg
import gui.widgets.gradient as grad
import gui.widgets.foldpanelbar as fpb

from project import Project
import session as ses

BTN_NEW = wx.NewId()

class TaskPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)

        inner_panel = InnerTaskPanel(self)

        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(inner_panel, 1, wx.EXPAND | wx.GROW | wx.BOTTOM | wx.RIGHT |
                  wx.LEFT, 7)
        sizer.Fit(self)

        self.SetSizer(sizer)
        self.Update()
        self.SetAutoLayout(1)

class InnerTaskPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        background_colour = wx.Colour(255,255,255)
        self.SetBackgroundColour(background_colour)
        self.SetAutoLayout(1)

        # Image for button
        BMP_ADD = wx.Bitmap("../icons/object_add.png", wx.BITMAP_TYPE_PNG)

        # Button for creating new surface
        button_set_overlay = pbtn.PlateButton(self, BTN_NEW, "", BMP_ADD, style=\
                                   pbtn.PB_STYLE_SQUARE | pbtn.PB_STYLE_DEFAULT)
        button_set_overlay.SetBackgroundColour(self.GetBackgroundColour())
        self.Bind(wx.EVT_BUTTON, self.OnButton)

        # Fixed hyperlink items
        tooltip = wx.ToolTip(_("Open NIfTI file as overlay"))
        link_set_overlay = hl.HyperLinkCtrl(self, -1, _("Import NIfTI image"))
        link_set_overlay.SetUnderlines(False, False, False)
        link_set_overlay.SetBold(True)
        link_set_overlay.SetColours("BLACK", "BLACK", "BLACK")
        link_set_overlay.SetBackgroundColour(self.GetBackgroundColour())
        link_set_overlay.SetToolTip(tooltip)
        link_set_overlay.AutoBrowse(False)
        link_set_overlay.UpdateLink()
        link_set_overlay.Bind(hl.EVT_HYPERLINK_LEFT, self.OnButton)

        # Create horizontal sizers to represent lines in the panel
        line_new = wx.BoxSizer(wx.HORIZONTAL)
        line_new.Add(link_set_overlay, 1, wx.EXPAND|wx.GROW| wx.TOP|wx.RIGHT, 4)
        line_new.Add(button_set_overlay, 0, wx.ALL|wx.EXPAND|wx.GROW, 0)

        # Button to fold to select region task
        button_info = wx.Button(self, -1, _("fMRI info"))
        check_box = wx.CheckBox(self, -1, _("Hide overlay"))
        self.check_box = check_box
        if sys.platform != 'win32':
            button_info.SetWindowVariant(wx.WINDOW_VARIANT_SMALL)
            check_box.SetWindowVariant(wx.WINDOW_VARIANT_SMALL)
        button_info.Bind(wx.EVT_BUTTON, self.OnButtonInfo)
        self.check_box.Bind(wx.EVT_CHECKBOX, self.OnCheckBox)

        info_btn_sizer = wx.BoxSizer(wx.VERTICAL)
        info_btn_sizer.Add(button_info, 1, wx.ALIGN_RIGHT)

        line_sizer = wx.BoxSizer(wx.HORIZONTAL)
        line_sizer.Add(check_box, 0, wx.ALIGN_LEFT|wx.RIGHT|wx.LEFT, 5)
        line_sizer.Add(info_btn_sizer, 1, wx.EXPAND|wx.ALIGN_RIGHT|wx.RIGHT|wx.LEFT, 5)
        line_sizer.Fit(self)

        # Add line sizers into main sizer
        main_sizer = wx.BoxSizer(wx.VERTICAL)

        main_sizer.Add(line_new, 0,wx.GROW|wx.EXPAND|wx.LEFT|wx.RIGHT|wx.TOP, 5)
        main_sizer.AddSizer(line_sizer, 0, wx.GROW|wx.EXPAND)
        main_sizer.AddSpacer(5)

        inner_panel = InnerFoldPanel(self)
        main_sizer.Add(inner_panel, 1, wx.EXPAND|wx.GROW, 2)
        self.inner_panel = inner_panel

        main_sizer.Fit(self)

        self.SetSizerAndFit(main_sizer)
        self.Update()
        self.SetAutoLayout(1)

        self.sizer = main_sizer

    def OnButton(self, evt):
        Publisher.sendMessage('Open overlay file')

    def OnButtonInfo(self, evt):
            sl = slice_.Slice()
            overlay_data = sl.overlay

            if overlay_data is not None:
                ovdlg = dlg.OverlayDialog(overlay_data)
                ovdlg.Show()

    def OnCheckBox(self, event):
        Publisher.sendMessage('Toggle overlay')
        Publisher.sendMessage('Reload actual slice')

class InnerFoldPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        default_colour = wx.SystemSettings_GetColour(wx.SYS_COLOUR_MENUBAR)
        self.SetBackgroundColour(default_colour)

        self.last_size = None

        sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(sizer)

        # Fold panel style
        style = fpb.CaptionBarStyle()
        style.SetCaptionStyle(fpb.CAPTIONBAR_GRADIENT_V)
        style.SetFirstColour(default_colour)
        style.SetSecondColour(default_colour)

        # Fold - Overlay properties
        self.overlay_prop_panel = OverlayProperties(self)

        sizer.Add(self.overlay_prop_panel, 1, wx.EXPAND)

        sizer.Layout()
        self.Fit()

        self.last_style = None

        self.__bind_pubsub_evt()

    def __bind_pubsub_evt(self):
        Publisher.subscribe(self.OnCloseProject, 'Close project data')

    def OnCloseProject(self, pubsub_evt):
        #self.fold_panel.Expand(self.fold_panel.GetFoldPanel(0))
        pass

class OverlayProperties(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)

        COLORMAPS = const.SLICE_COLOR_TABLE

        ## LINE 1
        text_colormap = wx.StaticText(self, -1,
                            _("Select colormap for overlay:"))

        ## LINE 2 - Colormap dropdown combo
        combo_colormap = wx.ComboBox(self, -1, "", choices=COLORMAPS.keys(),
                                     style=wx.CB_DROPDOWN|wx.CB_READONLY)
        combo_colormap.SetSelection(0)
        if sys.platform != 'win32':
            combo_colormap.SetWindowVariant(wx.WINDOW_VARIANT_SMALL)
        self.combo_colormap = combo_colormap

        combo_colormap.Bind(wx.EVT_COMBOBOX, self.OnColormapChange)

        ## LINE 3 - Gradient for threshold
        gradient = grad.GradientCtrl(self, -1, 0, 64, 0, 64,
                                           (0, 255, 0, 100))
        self.gradient = gradient

        ## LINE 4 - Alpha control
        alpha_control = wx.BoxSizer(wx.HORIZONTAL)
        alpha_label = wx.StaticText(self, label="Opacity:")
        self.alpha_slider = wx.Slider(self, value=50, size=(180,30), name="AlphaSlider")
        self.alpha_text = wx.StaticText(self, label="50%")

        self.alpha_slider.Bind(wx.EVT_SLIDER, self.OnSlider)

        alpha_control.AddMany([alpha_label, self.alpha_slider, self.alpha_text])

        # Add all lines into main sizer
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.AddSpacer(12)

        sizer.Add(text_colormap, 0, wx.GROW|wx.EXPAND|wx.LEFT|wx.RIGHT, 5)
        sizer.AddSpacer(2)
        sizer.Add(combo_colormap, 0, wx.EXPAND|wx.GROW|wx.LEFT|wx.RIGHT, 5)

        sizer.AddSpacer(5)
        sizer.Add(gradient, 1, wx.EXPAND|wx.LEFT|wx.RIGHT, 5)
        sizer.AddSpacer(7)
        sizer.Add(alpha_control, 1, wx.EXPAND|wx.LEFT|wx.RIGHT, 5)
        sizer.AddSpacer(7)

        sizer.Fit(self)

        self.SetSizerAndFit(sizer)
        self.Update()
        self.SetAutoLayout(1)

        # Non GUI stuff

        proj = Project()
        self.bind_evt_gradient = True
        self.__bind_events()
        self.__bind_events_wx()

    def __bind_events(self):
        Publisher.subscribe(self.SetThresholdBounds,
                                    'Update overlay window bounds')
        Publisher.subscribe(self.SetThresholdValues,
                                 'Set overlay window gradient values')
        Publisher.subscribe(self.OnCloseProject, 'Close project data')

    def OnCloseProject(self, pubsub_evt):
        self.CloseProject()

    def CloseProject(self):
        n = self.combo_colormap.GetCount()
        for i in xrange(n-1, -1, -1):
            self.combo_colormap.Delete(i)

    def __bind_events_wx(self):
        self.Bind(grad.EVT_THRESHOLD_CHANGED, self.OnSlideChange, self.gradient)
        self.Bind(grad.EVT_THRESHOLD_CHANGING, self.OnSlideChange, self.gradient)

    def SetThresholdValues(self, pubsub_evt):
        thresh_min, thresh_max = pubsub_evt.data
        self.bind_evt_gradient = False
        self.gradient.SetMinValue(thresh_min)
        self.gradient.SetMaxValue(thresh_max)
        self.bind_evt_gradient = True

    def SetThresholdBounds(self, pubsub_evt):
        thresh_min = pubsub_evt.data[0]
        thresh_max  = pubsub_evt.data[1]
        self.gradient.SetMinRange(thresh_min)
        self.gradient.SetMaxRange(thresh_max)

    def OnSlideChange(self, evt):
        window_min = self.gradient.GetMinValue()
        window_max = self.gradient.GetMaxValue()
        Publisher.sendMessage('Set overlay window',
                                    [window_min, window_max])
        Publisher.sendMessage('Reload actual slice')

        session = ses.Session()
        session.ChangeProject()

    def OnSlider(self, event):
        alpha = self.alpha_slider.GetValue()
        self.alpha_text.SetLabel( str(alpha) + "%" )

        Publisher.sendMessage('Set alpha overlay', alpha/100.0)
        Publisher.sendMessage('Reload actual slice')

    def OnColormapChange(self, event):
        COLORMAPS = const.SLICE_COLOR_TABLE
        current_map = self.combo_colormap.GetValue()
        map_data = COLORMAPS[current_map]

        Publisher.sendMessage('Set overlay colormap', map_data)
        Publisher.sendMessage('Reload actual slice')