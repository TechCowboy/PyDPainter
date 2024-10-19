#!/usr/bin/python3
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

import os.path, colorsys
import numpy as np

import libs.gadget
from libs.gadget import *

from libs.prim import *

import contextlib
with contextlib.redirect_stdout(None):
    import pygame
    from pygame.locals import *

#Workaround for pygame timer bug:
#  https://github.com/pygame/pygame/issues/3128
#  https://github.com/pygame/pygame/pull/3062
TIMEROFF = int((2**31)-1)

config = None

def toolreq_set_config(config_in):
    global config
    config = config_in


class FontGadget(ListGadget):
    def __init__(self, type, label, rect, value=None, maxvalue=None, id=None):
        if label == "&":
            scaleX = rect[2] // 8
            scaleY = rect[3] // 8
            self.arrowup = np.array([[0,16], [16,0], [32,16]]) * np.array([scaleX/4,scaleY/4])
            self.arrowdown = np.array([[0,24], [32,24], [16,40]]) * np.array([scaleX/4,scaleY/4])
            self.font_sizeg = None
        super(FontGadget, self).__init__(type, label, rect, value, maxvalue, id)

    def draw(self, screen, font, offset=(0,0), fgcolor=(0,0,0), bgcolor=(160,160,160), hcolor=(208,208,224)):
        self.visible = True
        x,y,w,h = self.rect
        xo, yo = offset
        self.offsetx = xo
        self.offsety = yo
        self.screenrect = (x+xo,y+yo,w,h)
        px = font.xsize//8
        py = font.ysize//8

        if self.type == Gadget.TYPE_CUSTOM:
            if not self.need_redraw:
                return

            #List text
            if self.label == "&":
                self.need_redraw = False
                upcolor = fgcolor
                downcolor = fgcolor
                if self.state == 1:
                    upcolor = hcolor
                elif self.state == -1:
                    downcolor = hcolor
                pygame.draw.polygon(screen, upcolor, self.arrowup + np.array([x+xo,y+yo]))
                pygame.draw.polygon(screen, downcolor, self.arrowdown + np.array([x+xo,y+yo]))
            else:
                super(FontGadget, self).draw(screen, font, offset)
        else:
            super(FontGadget, self).draw(screen, font, offset)

    def process_event(self, screen, event, mouse_pixel_mapper):
        ge = []
        x,y = mouse_pixel_mapper()
        g = self
        gx,gy,gw,gh = g.screenrect
        handled = False

        #disabled gadget
        if not g.enabled:
            return ge

        if self.type == Gadget.TYPE_CUSTOM:
            #Size up/down arrows
            if event.type == MOUSEBUTTONUP and event.button == 1 and \
               g.label == "&" and g.state != 0:
                pygame.time.set_timer(config.TOOLEVENT, TIMEROFF)
                g.state = 0
                g.need_redraw = True
                handled = True

            if g.pointin((x,y), g.screenrect) and g.label == "&":
                handled = True

                #get number from size gadget
                if g.font_sizeg.value.isnumeric() and int(g.font_sizeg.value) > 0 and int(g.font_sizeg.value) <= 500:
                    fontsize = int(g.font_sizeg.value)
                else:
                    fontsize = 0

                #handle left button
                if event.type == MOUSEBUTTONDOWN and event.button == 1:
                    pygame.time.set_timer(config.TOOLEVENT, 500)
                    if y - gy < gh // 2:
                        #up arrow
                        g.state = 1
                        fontsize += 1
                    else:
                        #down arrow
                        g.state = -1
                        fontsize -= 1

                #handle mouse wheel
                elif event.type == MOUSEBUTTONDOWN and event.button in [4,5]:
                    #scroll up
                    if event.button == 4:
                        fontsize += 1
                    #scroll down
                    elif event.button == 5:
                        fontsize -= 1

                elif event.type == config.TOOLEVENT:
                    pygame.time.set_timer(config.TOOLEVENT, 100)
                    if y - gy < gh // 2:
                        #up arrow
                        g.state = 1
                        fontsize += 1
                    else:
                        #down arrow
                        g.state = -1
                        fontsize -= 1
                    
                #assign back to size gadget
                if fontsize > 0 and fontsize <= 500:
                    g.font_sizeg.value = str(fontsize)
                    g.font_sizeg.need_redraw = True
                    g.need_redraw = True

        if not handled:
            ge.extend(super(FontGadget, self).process_event(screen, event, mouse_pixel_mapper))

        return ge

#Simple filter to get rid of non-latin fonts from the font requester
def is_latin_font(fname):
    retval = True

    if fname[0:7] in ["mathjax","notosan","notoser","notocol","notonas","notomon","notokuf","notomus"]:
        retval = False
    elif fname[0:6] == "samyak":
        retval = False
    elif fname[0:5] in ["kacst","lohit"]:
        retval = False
    return retval

def font_req(screen):
    req = str2req("Choose Font", """
#################^^ [System]
#################@@ [AmigaFont]
#################@@ Size:____&
#################@@ Style:
#################@@ [Bold] [AA]
#################@@ [Italic]
#################^^ [Underline]
Preview
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
[Cancel][OK]
""", "%#^@&", mouse_pixel_mapper=config.get_mouse_pixel_pos, custom_gadget_type=FontGadget, font=config.font)
    req.center(screen)
    config.pixel_req_rect = req.get_screen_rect()

    #list items
    list_itemsg = req.gadget_id("0_0")
    list_itemsg.items = pygame.font.get_fonts()
    list_itemsg.items.sort()
    list_itemsg.items = list(filter(lambda fname: is_latin_font(fname), list_itemsg.items))
    if config.text_tool_font_name in list_itemsg.items:
        list_itemsg.top_item = list_itemsg.items.index(config.text_tool_font_name)
    else:
        list_itemsg.top_item = 0
    list_itemsg.value = list_itemsg.top_item
    last_list_itemsg_value = list_itemsg.value

    #list up/down arrows
    list_upg = req.gadget_id("17_0")
    list_upg.value = -1
    list_downg = req.gadget_id("17_6")
    list_downg.value = 1

    #list slider
    list_sliderg = req.gadget_id("17_1")
    list_sliderg.value = list_itemsg.top_item

    #all list item gadgets
    listg_list = [list_itemsg, list_upg, list_downg, list_sliderg]
    list_itemsg.listgadgets = listg_list
    list_upg.listgadgets = listg_list
    list_downg.listgadgets = listg_list
    list_sliderg.listgadgets = listg_list

    #font type
    system_fontg = req.gadget_id("20_0")
    amiga_fontg = req.gadget_id("20_1")
    amiga_fontg.enabled = False
    fonttype = config.text_tool_font_type
    if fonttype == 0:
        system_fontg.state = 1
        amiga_fontg.state = 0
    else:
        system_fontg.state = 0
        amiga_fontg.state = 1

    #font size
    font_sizeg = req.gadget_id("25_2")
    font_sizeg.value = str(config.text_tool_font_size)
    font_sizeg.numonly = True
    font_size_arrowsg = req.gadget_id("29_2")
    font_size_arrowsg.font_sizeg = font_sizeg

    #font attributes
    font_boldg = req.gadget_id("20_4")
    bold = config.text_tool_font_bold
    font_italicg = req.gadget_id("20_5")
    italic = config.text_tool_font_italic
    font_underlineg = req.gadget_id("20_6")
    underline = config.text_tool_font_underline
    if bold:
        font_boldg.state = 1
    if italic:
        font_italicg.state = 1
    if underline:
        font_underlineg.state = 1

    #antialias
    aa_fontg = req.gadget_id("27_4")
    aa = config.text_tool_font_antialias
    if aa:
        aa_fontg.state = 1

    #take care of non-square pixels
    fontmult = 1
    if config.aspectX != config.aspectY:
        fontmult = 2

    #font preview
    previewg = req.gadget_id("0_8")

    req.draw(screen)
    config.recompose()

    running = 1
    while running:
        event = config.xevent.wait()
        gevents = req.process_event(screen, event)

        if event.type == KEYDOWN and event.key == K_ESCAPE:
            running = 0

        for ge in gevents:
            if ge.gadget.type == Gadget.TYPE_BOOL:
                if ge.gadget.label == "OK" and not req.has_error():
                    config.text_tool_font_antialias = aa
                    config.text_tool_font_name = list_itemsg.items[list_itemsg.value]
                    config.text_tool_font_type = fonttype
                    config.text_tool_font_size = int(font_sizeg.value)
                    config.text_tool_font_antialias = aa
                    config.text_tool_font_bold = bold
                    config.text_tool_font_italic = italic
                    config.text_tool_font_underline = underline
                    config.text_tool_font = pygame.font.Font(pygame.font.match_font(config.text_tool_font_name, bold=config.text_tool_font_bold, italic=config.text_tool_font_italic), config.text_tool_font_size*fontmult)
                    config.text_tool_font.set_underline(config.text_tool_font_underline)
                    running = 0
                elif ge.gadget.label == "Cancel":
                    running = 0
                elif ge.gadget.label == "System":
                    fonttype = 0
                elif ge.gadget.label == "AmigaFont":
                    fonttype = 1
                elif ge.gadget.label == "AA":
                    aa = not aa
                elif ge.gadget.label == "Bold":
                    bold = not bold
                elif ge.gadget.label == "Italic":
                    italic = not italic
                elif ge.gadget.label == "Underline":
                    underline = not underline

        if fonttype == 0:
            system_fontg.state = 1
        else:
            amiga_fontg.state = 1

        if aa:
            aa_fontg.state = 1

        if bold:
            font_boldg.state = 1
        if italic:
            font_italicg.state = 1
        if underline:
            font_underlineg.state = 1

        if not config.xevent.peek((KEYDOWN, KEYUP, MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION, VIDEORESIZE)):
            req.draw(screen)
            #Font preview
            screen.set_clip(previewg.screenrect)
            pygame.draw.rect(screen, (0,0,0), previewg.screenrect, 0)
            if font_sizeg.value.isnumeric() and int(font_sizeg.value) > 0 and int(font_sizeg.value) <= 500:
                try:
                    prefont = pygame.font.Font(pygame.font.match_font(list_itemsg.items[list_itemsg.value], bold=bold, italic=italic), int(font_sizeg.value)*fontmult)
                    prefont.set_underline(underline)
                    surf = prefont.render("The quick brown fox jumps over the lazy dog", aa, (255,255,255))
                    if config.aspectX != config.aspectY:
                        sx,sy = surf.get_size()
                        if config.aspectX == 2:
                            sy //= 2
                        else:
                            sx //= 2
                        if aa:
                            surf = pygame.transform.smoothscale(surf, (sx,sy))
                        else:
                            surf = pygame.transform.scale(surf, (sx,sy))

                    screen.blit(surf, (previewg.screenrect[0], previewg.screenrect[1]))
                    last_list_itemsg_value = list_itemsg.value
                except:
                    #revert back to known good font
                    list_itemsg.value = last_list_itemsg_value
                    list_itemsg.need_redraw = True
                    screen.fill((255,0,0))

            screen.set_clip(None)
 
            config.recompose()

    config.pixel_req_rect = None
    config.recompose()

    return


def place_point(symm_center):
    pixel_req_rect_bak = config.pixel_req_rect
    config.pixel_req_rect = None
    config.recompose()
    ret_coords = list(symm_center)
    point_placed = False
    first_time = True
    while not point_placed:
        event = config.xevent.poll()
        while event.type == pygame.MOUSEMOTION and config.xevent.peek((MOUSEMOTION)):
            #get rid of extra mouse movements
            event = config.xevent.poll()

        if event.type == pygame.NOEVENT and not first_time:
            event = config.xevent.wait()

        mouseX, mouseY = config.get_mouse_pixel_pos(event, ignore_grid=True)
        if event.type == MOUSEMOTION:
            pass
        elif event.type == MOUSEBUTTONUP:
            ret_coords = (mouseX, mouseY)
            point_placed = True
        elif event.type == KEYDOWN:
            if event.key == K_ESCAPE:
                point_placed = True

        config.clear_pixel_draw_canvas()
        #old center
        scx,scy = symm_center
        ph = config.pixel_canvas.get_height()
        pw = config.pixel_canvas.get_width()
        drawline(config.pixel_canvas, 1,
            (scx,scy-(ph//10)), (scx,scy+(ph//10)),
            xormode=True)
        drawline(config.pixel_canvas, 1,
            (scx-int(ph/(10*config.pixel_aspect)),scy), (scx+int(ph/(10*config.pixel_aspect)),scy),
            xormode=True)
        #current center
        drawline(config.pixel_canvas, 1,
            (mouseX,0), (mouseX,config.pixel_canvas.get_height()),
            xormode=True)
        drawline(config.pixel_canvas, 1,
            (0,mouseY), (config.pixel_canvas.get_width(),mouseY),
            xormode=True)
        config.menubar.title_right = config.xypos_string((mouseX,mouseY))
        config.recompose()
        first_time = False

    config.menubar.title_right = ""
    config.pixel_req_rect = pixel_req_rect_bak
    config.clear_pixel_draw_canvas()
    config.recompose()

    return ret_coords

def place_grid(gcoords):
    w = gcoords[2]
    ow = w
    h = gcoords[3]
    oh = h
    ret_coords = list(gcoords)
    if len(ret_coords) < 6:
        ret_coords.append(4)
        ret_coords.append(4)
    nx = ret_coords[4]
    ny = ret_coords[5]
    p0 = (0,0)
    p1 = (0,0)
    pixel_req_rect_bak = config.pixel_req_rect
    config.pixel_req_rect = None
    config.recompose()
    dragging = False
    point_placed = False
    first_time = True
    while not point_placed:
        event = config.xevent.poll()
        while event.type == pygame.MOUSEMOTION and config.xevent.peek((MOUSEMOTION)):
            #get rid of extra mouse movements
            event = config.xevent.poll()

        if event.type == pygame.NOEVENT and not first_time:
            event = config.xevent.wait()

        if event.type == KEYDOWN:
            if event.key == K_ESCAPE:
                point_placed = True
            elif event.key == K_x:
                if event.mod & KMOD_SHIFT:
                    if nx > 1:
                        nx -= 1
                else:
                    nx += 1
            elif event.key == K_y:
                if event.mod & KMOD_SHIFT:
                    if ny > 1:
                        ny -= 1
                else:
                    ny += 1

        mouseX, mouseY = config.get_mouse_pixel_pos(event, ignore_grid=True)
        if dragging:
            p1 = (mouseX, mouseY)
            w = int(round((p1[0] - p0[0]) / nx))
            h = int(round((p1[1] - p0[1]) / ny))
            if h <= 0:
                h = 1
            if w <= 0:
                w = 1
        else:
            p0 = (mouseX-(nx*w), mouseY-(ny*h))
        if event.type == MOUSEBUTTONDOWN:
            dragging = True
        elif event.type == MOUSEBUTTONUP:
            point_placed = True
            wnew = int(abs(w))
            hnew = int(abs(h))
            ret_coords = list([p0[0]%wnew, p0[1]%hnew, wnew, hnew, nx, ny])

        config.clear_pixel_draw_canvas()

        pcx,pcy = p0
        for x in range(0,nx+1):
            drawline(config.pixel_canvas, 1,
                (pcx+(x*w),pcy), (pcx+(x*w),pcy+(ny*h)),
                xormode=True)
        for y in range(0,ny+1):
            drawline(config.pixel_canvas, 1,
                (pcx+(nx*w),pcy+(y*h)), (pcx,pcy+(y*h)),
                xormode=True)

        config.menubar.title_right = str(pcx%w) + "," + str(pcy%h) + " " + str(w) + "x" + str(h)
        config.recompose()
        first_time = False

    config.menubar.title_right = ""
    config.pixel_req_rect = pixel_req_rect_bak
    config.clear_pixel_draw_canvas()
    config.recompose()

    return ret_coords

class BrushReqProps(object):
    J_LEFT = 0
    J_RIGHT = 1
    J_CENTER_X = 2
    J_TOP = 3
    J_BOTTOM = 4
    J_CENTER_Y = 5

    J_STR = ["\x97", "\x94", "\x8C\x8D", "\x95", "\x96", "\x88\x89"]
    J_NAME = ["J_LEFT", "J_RIGHT", "J_CENTER_X", "J_TOP", "J_BOTTOM", "J_CENTER_Y"]

    H_CENTER, H_TOP_LEFT, H_TOP, H_TOP_RIGHT, H_RIGHT, H_BOTTOM_RIGHT, H_BOTTOM, H_BOTTOM_LEFT, H_LEFT = range(9)

    def __init__(self):
        self.offset = [0,0]
        self.size = [10,10]
        self.number = [4,4]
        self.strict = [True,True]
        self.align = [self.J_LEFT, self.J_TOP]
        self.numbersg = []
        self.handles = []
        self.bcoords = None
        self.last_brp = None
        self.last_handle_num = -1

    def __repr__(self):
        return f"BrushReqProps <{hex(id(self))}: offset={self.offset} size={self.size} number={self.number} strict={self.strict} align=[{self.J_NAME[self.align[0]]}, {self.J_NAME[self.align[1]]}]>"

    def __eq__(self, other):
        if not isinstance(other, BrushReqProps):
            return False

        return self.offset == other.offset and \
               self.size == other.size and \
               self.number == other.number and \
               self.strict == other.strict and \
               self.align == other.align

    def copy(self):
        brp = BrushReqProps()
        brp.offset = list(self.offset)
        brp.size = list(self.size)
        brp.number = list(self.number)
        brp.strict = list(self.strict)
        brp.align = list(self.align)
        return brp

    def next_align(self, xy):
        jx,jy = self.align
        if xy == 0:
            jx += 1
            if jx > self.J_CENTER_X:
                jx = self.J_LEFT
            self.align[0] = jx
        else:
            jy += 1
            if jy > self.J_CENTER_Y:
                jy = self.J_TOP
            self.align[1] = jy

    def get_handle_num(self, x, y):
        handle_num = -1
        for i in range(len(self.handles)):
            handle = self.handles[i]
            if x >= handle[0][0] and x <= handle[1][0] and \
               y >= handle[0][1] and y <= handle[1][1]:
                   handle_num = i
                   break
        return handle_num

    def valid_number(self, g):
        if re.fullmatch(r'^-?\d*\.?\d+$', g.value):
            if g.spinnerg is None:
                return True
            elif int(g.value) >= g.spinnerg.minvalue and \
                 int(g.value) <= g.spinnerg.maxvalue:
                    return True
        return False

    def get_req_numbers(self):
        if len(self.numbersg) > 0:
            if self.valid_number(self.numbersg[0]):
                self.offset[0] = int(self.numbersg[0].value)
            if self.valid_number(self.numbersg[1]):
                self.offset[1] = int(self.numbersg[1].value)
            if self.valid_number(self.numbersg[2]):
                self.size[0] = int(self.numbersg[2].value)
            if self.valid_number(self.numbersg[3]):
                self.size[1] = int(self.numbersg[3].value)
            if self.valid_number(self.numbersg[4]):
                self.number[0] = int(self.numbersg[4].value)
            if self.valid_number(self.numbersg[5]):
                self.number[1] = int(self.numbersg[5].value)

    def draw(self, handle_num=-1):
        if handle_num == self.last_handle_num:
            if self == self.last_brp:
                return

        self.last_handle_num = handle_num

        sm = config.display_info.get_id(config.display_mode)
        px = sm.scaleX
        py = sm.scaleY

        last_brp = self.copy()
        ox,oy = self.offset
        sx,sy = self.size
        nx,ny = self.number
        gw = sx*nx
        gh = sy*ny

        config.clear_pixel_draw_canvas()

        bcoords = np.zeros((nx,ny,4), dtype=np.int32)

        #calculate starting brush grid coords
        gw = sx*nx
        gh = sy*ny
        yi = 0
        for y in range(oy, oy+gh, sy):
            xi = 0
            for x in range(ox, ox+gw, sx):
                bcoords[xi,yi,:] = [x,y, x+sx, y+sy]
                xi += 1
            yi += 1

        #draw vertical grid lines
        if self.strict[0] == True:
            nx0 = 0
            if handle_num == self.H_LEFT:
                nx0 = 1
            for xi in range(nx0, nx):
                x = bcoords[xi,0,0]
                y1 = bcoords[xi,0,1]
                y2 = bcoords[xi,ny-1,3]
                drawline(config.pixel_canvas, 1, (x,y1), (x,y2), xormode=True)
            if handle_num != self.H_RIGHT:
                x = bcoords[nx-1,0,2]
                y1 = bcoords[nx-1,0,1]
                y2 = bcoords[nx-1,ny-1,3]
                drawline(config.pixel_canvas, 1, (x,y1), (x,y2), xormode=True)

        #draw horizontal grid lines
        if self.strict[1] == True:
            ny0 = 0
            if handle_num == self.H_TOP:
                ny0 = 1
            for yi in range(ny0, ny):
                y = bcoords[0,yi,1]
                x1 = bcoords[0,yi,0]
                x2 = bcoords[nx-1,yi,2]
                drawline(config.pixel_canvas, 1, (x1,y), (x2,y), xormode=True)
            if handle_num != self.H_BOTTOM:
                y = bcoords[0,ny-1,3]
                x1 = bcoords[0,ny-1,0]
                x2 = bcoords[nx-1,ny-1,2]
                drawline(config.pixel_canvas, 1, (x1,y), (x2,y), xormode=True)

        #draw handles
        self.handles = [
            [(ox, oy), (ox+gw, oy+gh)], #H_CENTER
            [(ox-8*px, oy-8*py),(ox, oy)], #H_TOP_LEFT
            [(ox, oy-8*py), (ox+gw, oy)], #H_TOP
            [(ox+gw, oy-8*py), (ox+gw+8*px, oy)], #H_TOP_RIGHT
            [(ox+gw, oy), (ox+gw+8*px, oy+gh)], #H_RIGHT
            [(ox+gw, oy+gh), (ox+gw+8*px, oy+gh+8*py)], #H_BOTTOM_RIGHT
            [(ox, oy+gh), (ox+gw, oy+gh+8*py)], #H_BOTTOM
            [(ox-8*px, oy+gh), (ox, oy+gh+8*py)], #H_BOTTOM_LEFT
            [(ox-8*px, oy), (ox, oy+gh)], #H_LEFT
        ]

        if handle_num in [self.H_TOP, self.H_RIGHT, self.H_BOTTOM, self.H_LEFT]:
            handle = self.handles[handle_num]
            drawrect(config.pixel_canvas, 1, handle[0], handle[1], handlesymm=False, xormode=True)
        else:
            for i in [self.H_TOP_LEFT, self.H_TOP_RIGHT, self.H_BOTTOM_RIGHT, self.H_BOTTOM_LEFT]:
                handle = self.handles[i]
                drawrect(config.pixel_canvas, 1, handle[0], handle[1], handlesymm=False, xormode=True)

        self.bcoords = bcoords

    def pickup(self):
        ox,oy = self.offset
        sx,sy = self.size
        nx,ny = self.number
        gw = sx*nx
        gh = sy*ny

        config.clear_pixel_draw_canvas()
        brush = Brush(type=Brush.CUSTOM, screen=config.pixel_canvas, coordfrom=self.bcoords[0,0,0:2].tolist(), coordto=(self.bcoords[0,0,2:4]-[1,1]).tolist())
        brush.animbrush = True

        yi = 0
        while yi < ny:
            xi = 0
            if yi == 0:
                xi = 1
            while xi < nx:
                brush.add_frame(brush.get_image_from_screen(config.pixel_canvas, coordfrom=self.bcoords[xi,yi,0:2].tolist(), coordto=(self.bcoords[xi,yi,2:4]-[1,1]).tolist()))
                xi += 1
            yi += 1

        return brush


def brush_req(screen):
    req = str2req("Brush Grid", """
          X      Y
Offset: _____~ _____~
Size:   _____~ _____~
Number: _____~ _____~
Strict: [Yes  ][Yes  ]
Align:  [<>   ][^v   ]

[Cancel][OK]
""", "", mouse_pixel_mapper=config.get_mouse_pixel_pos, font=config.font)
    req.center(screen)
    config.pixel_req_rect = req.get_screen_rect()
    req.draggable = True
    (rx,ry,rw,rh) = req.rect

    offsetXg = req.find_gadget("Offset:", 1)
    offsetYg = req.find_gadget("Offset:", 3)
    sizeXg = req.find_gadget("Size:", 1)
    sizeYg = req.find_gadget("Size:", 3)
    numberXg = req.find_gadget("Number:", 1)
    numberYg = req.find_gadget("Number:", 3)
    strictXg = req.find_gadget("Strict:", 1)
    strictYg = req.find_gadget("Strict:", 2)
    alignXg = req.find_gadget("Align:", 1)
    alignYg = req.find_gadget("Align:", 2)

    brp = config.brush_req_props.copy()
    brp_numbersg = [offsetXg, offsetYg, sizeXg, sizeYg, numberXg, numberYg]
    brp.numbersg = brp_numbersg

    offsetXg.value = str(brp.offset[0])
    offsetYg.value = str(brp.offset[1])
    sizeXg.value = str(brp.size[0])
    sizeXg.spinnerg.minvalue = 1
    sizeYg.value = str(brp.size[1])
    sizeYg.spinnerg.minvalue = 1
    numberXg.value = str(brp.number[0])
    numberXg.spinnerg.minvalue = 1
    numberYg.value = str(brp.number[1])
    numberYg.spinnerg.minvalue = 1
    strictXg.label = "Yes" if brp.strict[0] else "No"
    strictYg.label = "Yes" if brp.strict[1] else "No"
    alignXg.label = brp.J_STR[brp.align[0]]
    alignYg.label = brp.J_STR[brp.align[1]]

    clickXY = [-1,-1]
    handle_num = -1

    req.draw(screen)
    config.recompose()

    running = 1
    while running:
        event = config.xevent.wait()
        gevents = req.process_event(screen, event)

        if event.type == KEYDOWN and event.key == K_ESCAPE:
            running = 0 

        #Get color from pixel canvas
        buttons = config.get_mouse_pressed(event)
        if len(gevents) == 0 and event.type == MOUSEBUTTONDOWN:
            x,y = config.get_mouse_pixel_pos(event)
            if x < rx or y < ry or x > rx+rw or y > ry+rh:
                x1,y1 = config.get_mouse_pixel_pos(event, ignore_req=True)
                print(f"mouse outside {x=},{y=} {x1=},{y1=}")
                handle_num = brp.get_handle_num(x1, y1)
                if handle_num >= 0:
                    clickXY = (x1-brp.handles[handle_num][0][0],y1-brp.handles[handle_num][0][1])
                else:
                    clickXY = (-1,-1)

        if len(gevents) == 0 and event.type == MOUSEMOTION:
            if config.xevent.peek(MOUSEMOTION):
                continue
            x1,y1 = config.get_mouse_pixel_pos(event, ignore_req=True)
            if buttons[0]:
                ox,oy = brp.offset
                sx,sy = brp.size
                nx,ny = brp.number
                gw,gh = brp.bcoords[nx-1,ny-1,2:4]
                if handle_num == brp.H_CENTER:
                    offsetXg.value = str(max(0, x1-clickXY[0]))
                    offsetXg.need_redraw = True
                    offsetYg.value = str(max(0, y1-clickXY[1]))
                    offsetYg.need_redraw = True
                    brp.get_req_numbers()
                elif handle_num == brp.H_TOP_LEFT:
                    ox = int(round((x1-clickXY[0]) / sx)+1) * sx
                    oy = int(round((y1-clickXY[1]) / sy)+1) * sy
                    offsetXg.value = str(max(0, ox))
                    offsetXg.need_redraw = True
                    offsetYg.value = str(max(0, oy))
                    offsetYg.need_redraw = True
                    brp.get_req_numbers()
                elif handle_num == brp.H_TOP:
                    oy = int(round((y1-clickXY[1]) / sy)+1) * sy
                    sy = ny * (y1-clickXY[1]-oy) // gh
                    print(f"{sy=}")
                    offsetYg.value = str(max(0, oy))
                    offsetYg.need_redraw = True
                    sizeYg.value = str(max(1, sy))
                    sizeYg.need_redraw = True
                    brp.get_req_numbers()
                elif handle_num == brp.H_RIGHT:
                    sizeXg.value = str(max(1, (x1-clickXY[0]-ox) // nx))
                    sizeXg.need_redraw = True
                    brp.get_req_numbers()
                elif handle_num == brp.H_BOTTOM_RIGHT:
                    sizeXg.value = str(max(1, (x1-clickXY[0]-ox) // nx))
                    sizeXg.need_redraw = True
                    sizeYg.value = str(max(1, (y1-clickXY[1]-oy) // ny))
                    sizeYg.need_redraw = True
                    brp.get_req_numbers()
                elif handle_num == brp.H_BOTTOM:
                    sizeYg.value = str(max(1, (y1-clickXY[1]-oy) // ny))
                    sizeYg.need_redraw = True
                    brp.get_req_numbers()
            else:
                handle_num = brp.get_handle_num(x1, y1)

        if event.type == MOUSEBUTTONUP:
            handle_num = -1
            clickXY = (-1,-1)

        for ge in gevents:
            if ge.gadget.type == Gadget.TYPE_BOOL:
                if ge.gadget.label == "OK" and not req.has_error():
                    config.brush_req_props = brp.copy()
                    config.brush = brp.pickup()
                    config.toolbar.click(config.toolbar.tool_id("dot"), MOUSEBUTTONDOWN)
                    config.toolbar.tool_id("circle1").state = 0
                    config.toolbar.tool_id("circle2").state = 0
                    config.toolbar.tool_id("circle3").state = 0
                    config.toolbar.tool_id("circle4").state = 0
                    config.toolbar.tool_id("square1").state = 0
                    config.toolbar.tool_id("square2").state = 0
                    config.toolbar.tool_id("square3").state = 0
                    config.toolbar.tool_id("square4").state = 0
                    config.toolbar.tool_id("spray1").state = 0
                    config.toolbar.tool_id("spray2").state = 0
                    config.setDrawMode(DrawMode.MATTE)
                    running = 0
                elif ge.gadget.label == "Cancel":
                    running = 0 
                elif ge.gadget == alignXg:
                    brp.next_align(0)
                    alignXg.label = brp.J_STR[brp.align[0]]
                    alignXg.need_redraw = True
                    req.draw(screen)
                elif ge.gadget == alignYg:
                    brp.next_align(1)
                    alignYg.label = brp.J_STR[brp.align[1]]
                    alignYg.need_redraw = True
                    req.draw(screen)
                elif ge.gadget == strictXg:
                    brp.strict[0] = not brp.strict[0]
                    strictXg.label = "Yes" if brp.strict[0] else "No"
                    strictXg.need_redraw = True
                elif ge.gadget == strictYg:
                    brp.strict[1] = not brp.strict[1]
                    strictYg.label = "Yes" if brp.strict[1] else "No"
                    strictYg.need_redraw = True

        if len(gevents) > 0:
            brp.get_req_numbers()

        brp.draw(handle_num)

        if not config.xevent.peek((KEYDOWN, KEYUP, MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION, VIDEORESIZE)):
            #keep requestor within screen
            (rx,ry,rw,rh) = req.rect
            if ry < 14:
                ry = 14
            if ry > screen.get_height()-20:
                ry = screen.get_height()-20
            if rx < -rw+20:
                rx = -rw+20
            if rx > screen.get_width()-40:
                rx = screen.get_width()-40
            req.rect = (rx,ry,rw,rh)
            config.pixel_req_rect = req.get_screen_rect()
            req.draw(screen)
            config.recompose()

    config.pixel_req_rect = None
    config.recompose()

    return

def grid_req(screen):
    req = str2req("Grid", """
          X     Y
Size:   _____ _____
Offset: _____ _____
[Visual]
[Cancel][OK]
""", "", mouse_pixel_mapper=config.get_mouse_pixel_pos, font=config.font)
    req.center(screen)
    config.pixel_req_rect = req.get_screen_rect()

    sizeXg = req.gadget_id("8_1")
    sizeYg = req.gadget_id("14_1")
    offsetXg = req.gadget_id("8_2")
    offsetYg = req.gadget_id("14_2")
    visualg = req.gadget_id("0_3")

    sizeXg.value = str(config.grid_size[0])
    sizeXg.numonly = True
    sizeYg.value = str(config.grid_size[1])
    sizeYg.numonly = True
    offsetXg.value = str(config.grid_offset[0])
    offsetXg.numonly = True
    offsetYg.value = str(config.grid_offset[1])
    offsetYg.numonly = True

    req.draw(screen)
    config.recompose()

    running = 1
    while running:
        event = config.xevent.wait()
        gevents = req.process_event(screen, event)

        if event.type == KEYDOWN and event.key == K_ESCAPE:
            running = 0 

        for ge in gevents:
            if ge.gadget.type == Gadget.TYPE_BOOL:
                if ge.gadget.label == "OK" and not req.has_error():
                    config.grid_size = (int(sizeXg.value), int(sizeYg.value))
                    config.grid_offset = (int(offsetXg.value)%int(sizeXg.value), int(offsetYg.value)%int(sizeYg.value))
                    running = 0
                elif ge.gadget.label == "Cancel":
                    running = 0 
                elif ge.gadget == visualg and not req.has_error():
                    gcoords = place_grid((int(offsetXg.value)%int(sizeXg.value), int(offsetYg.value)%int(sizeYg.value), int(sizeXg.value), int(sizeYg.value)))
                    offsetXg.value = str(gcoords[0])
                    offsetXg.need_redraw = True
                    offsetYg.value = str(gcoords[1])
                    offsetYg.need_redraw = True
                    sizeXg.value = str(gcoords[2])
                    sizeXg.need_redraw = True
                    sizeYg.value = str(gcoords[3])
                    sizeYg.need_redraw = True
                    req.draw(screen)

        if not config.xevent.peek((KEYDOWN, KEYUP, MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION, VIDEORESIZE)):
            req.draw(screen)
            config.recompose()

    config.pixel_req_rect = None
    config.recompose()

    return

def symmetry_tile_req(screen):
    req = str2req("Symmetry", """
[Point ][ Tile ]

Width:   ____
Height:  ____
[Cancel][OK]
""", "", mouse_pixel_mapper=config.get_mouse_pixel_pos, font=config.font)
    req.center(screen)
    config.pixel_req_rect = req.get_screen_rect()

    pointg = req.gadget_id("0_0")
    tileg = req.gadget_id("8_0")

    cyclicg = req.gadget_id("0_1")
    mirrorg = req.gadget_id("8_1")

    widthl = req.gadget_id("0_2")
    widthg = req.gadget_id("9_2")

    heightl = req.gadget_id("0_3")
    heightg = req.gadget_id("9_3")

    widthg.value = str(config.symm_width)
    widthg.numonly = True
    heightg.value = str(config.symm_height)
    heightg.numonly = True
    tileg.state = 1
    req.draw(screen)
    config.recompose()

    running = 1
    while running:
        event = config.xevent.wait()
        gevents = req.process_event(screen, event)

        if event.type == KEYDOWN and event.key == K_ESCAPE:
            running = 0 

        for ge in gevents:
            if ge.gadget.type == Gadget.TYPE_BOOL:
                if ge.gadget.label == "OK" and not req.has_error():
                    config.symm_mode = 1
                    config.symm_width = int(widthg.value)
                    config.symm_height = int(heightg.value)
                    running = 0 
                elif ge.gadget.label == "Cancel":
                    running = 0 
                elif ge.gadget == pointg:
                    return 0

        tileg.state = 1
        if not config.xevent.peek((KEYDOWN, KEYUP, MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION, VIDEORESIZE)):
            req.draw(screen)
            config.recompose()
    return -1

def symmetry_point_req(screen):
    req = str2req("Symmetry", """
[Point ][ Tile ]
[Cyclic][Mirror]
Order:   ___
X:_____  Y:_____
[Center] [Center]
     [Place]
[Cancel][OK]
""", "", mouse_pixel_mapper=config.get_mouse_pixel_pos, font=config.font)
    req.center(screen)
    config.pixel_req_rect = req.get_screen_rect()

    pointg = req.gadget_id("0_0")
    tileg = req.gadget_id("8_0")

    cyclicg = req.gadget_id("0_1")
    mirrorg = req.gadget_id("8_1")

    orderl = req.gadget_id("0_2")
    orderg = req.gadget_id("9_2")

    centerxvalg = req.gadget_id("2_3")
    centeryvalg = req.gadget_id("11_3")

    centerxg = req.gadget_id("0_4")
    centeryg = req.gadget_id("9_4")

    placeg = req.gadget_id("5_5")

    orderg.value = str(config.symm_num)
    orderg.numonly = True
    pointg.state = 1
    centerxvalg.value = str(config.xpos_display(config.symm_center[0]))
    centerxvalg.numonly = True
    centeryvalg.value = str(config.ypos_display(config.symm_center[1]))
    centeryvalg.numonly = True

    if config.symm_type == 0:
        cyclicg.state = 1
    elif config.symm_type == 1:
        mirrorg.state = 1

    symm_center = list(config.symm_center)

    req.draw(screen)
    config.recompose()

    running = 1
    while running:
        event = config.xevent.wait()
        gevents = req.process_event(screen, event)

        if event.type == KEYDOWN and event.key == K_ESCAPE:
            running = 0 

        for ge in gevents:
            if ge.gadget.type == Gadget.TYPE_BOOL:
                if ge.gadget.label == "OK" and not req.has_error():
                    config.symm_mode = 0
                    config.symm_num = int(orderg.value)
                    config.symm_center = [config.xpos_undisplay(int(centerxvalg.value)), config.ypos_undisplay(int(centeryvalg.value))]
                    running = 0 
                elif ge.gadget.label == "Cancel":
                    running = 0 
                elif ge.gadget == tileg:
                    return 1
                elif ge.gadget == cyclicg:
                    config.symm_type = 0
                elif ge.gadget == mirrorg:
                    config.symm_type = 1
                elif ge.gadget == placeg:
                    if not req.has_error():
                        symm_center = [config.xpos_undisplay(int(centerxvalg.value)), config.ypos_undisplay(int(centeryvalg.value))]
                    symm_center = list(place_point(symm_center))
                    centerxvalg.value = str(config.xpos_display(symm_center[0]))
                    centerxvalg.need_redraw = True
                    centeryvalg.value = str(config.ypos_display(symm_center[1]))
                    centeryvalg.need_redraw = True
                elif ge.gadget == centerxg:
                    symm_center[0] = config.pixel_width // 2
                    centerxvalg.value = str(config.xpos_display(symm_center[0]))
                    centerxvalg.need_redraw = True
                elif ge.gadget == centeryg:
                    symm_center[1] = config.pixel_height // 2
                    centeryvalg.value = str(config.ypos_display(symm_center[1]))
                    centeryvalg.need_redraw = True

        pointg.state = 1

        if config.symm_type == 0:
            cyclicg.state = 1
        elif config.symm_type == 1:
            mirrorg.state = 1

        if not config.xevent.peek((KEYDOWN, KEYUP, MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION, VIDEORESIZE)):
            req.draw(screen)
            config.recompose()
    return -1


def symmetry_req(screen):
    symm_mode = config.symm_mode

    while symm_mode >= 0:
        if symm_mode == 0:
            symm_mode = symmetry_point_req(screen)
        elif symm_mode == 1:
            symm_mode = symmetry_tile_req(screen)

    config.pixel_req_rect = None

def spacing_req(screen):
    req = str2req("Spacing", """
[N Total]      ____
[Every Nth dot]____
[Airbrush]     ____
[Continuous]
[Cancel][OK]
""", "", mouse_pixel_mapper=config.get_mouse_pixel_pos, font=config.font)
    req.center(screen)
    config.pixel_req_rect = req.get_screen_rect()

    n_totalg = req.gadget_id("0_0")
    n_total_valueg = req.gadget_id("15_0")
    n_total_valueg.numonly = True
    n_total_valueg.value = str(config.primprops.drawmode.n_total_value)

    every_ng = req.gadget_id("0_1")
    every_n_valueg = req.gadget_id("15_1")
    every_n_valueg.numonly = True
    every_n_valueg.value = str(config.primprops.drawmode.every_n_value)

    airbrushg = req.gadget_id("0_2")
    airbrush_valueg = req.gadget_id("15_2")
    airbrush_valueg.numonly = True
    airbrush_valueg.value = str(config.primprops.drawmode.airbrush_value)

    continuousg = req.gadget_id("0_3")

    spacing = config.primprops.drawmode.spacing
    button_list = [continuousg, n_totalg, every_ng, airbrushg]
    button_list[spacing].state = 1

    req.draw(screen)
    config.recompose()

    running = 1
    while running:
        event = config.xevent.wait()
        gevents = req.process_event(screen, event)

        if event.type == KEYDOWN and event.key == K_ESCAPE:
            running = 0 

        button_list[spacing].state = 1

        for ge in gevents:
            if ge.gadget.type == Gadget.TYPE_BOOL:
                if ge.gadget.label == "OK" and not req.has_error():
                    config.primprops.drawmode.spacing = spacing
                    config.primprops.drawmode.n_total_value = int(n_total_valueg.value)
                    config.primprops.drawmode.every_n_value = int(every_n_valueg.value)
                    config.primprops.drawmode.airbrush_value = int(airbrush_valueg.value)
                    if config.primprops.drawmode.n_total_value < 2:
                        config.primprops.drawmode.n_total_value = 2
                    if config.primprops.drawmode.every_n_value < 1:
                        config.primprops.drawmode.every_n_value = 1
                    if config.primprops.drawmode.airbrush_value < 1:
                        config.primprops.drawmode.airbrush_value = 1
                    running = 0
                elif ge.gadget.label == "Cancel":
                    running = 0 
                elif ge.gadget in button_list:
                    button_list[spacing].state = 0
                    button_list[spacing].need_redraw = True
                    spacing = button_list.index(ge.gadget)
                    ge.gadget.state = 1
                    ge.gadget.need_redraw = True

        if not config.xevent.peek((KEYDOWN, KEYUP, MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION, VIDEORESIZE)):
            req.draw(screen)
            config.recompose()

    config.pixel_req_rect = None
    config.recompose()

    return


class FillGadget(Gadget):
    def __init__(self, type, label, rect, value=None, maxvalue=None, id=None):
        super(FillGadget, self).__init__(type, label, rect, value, maxvalue, id)

    def draw(self, screen, font, offset=(0,0), fgcolor=(0,0,0), bgcolor=(160,160,160), hcolor=(208,208,224)):
        self.visible = True
        x,y,w,h = self.rect
        xo, yo = offset
        self.offsetx = xo
        self.offsety = yo
        self.screenrect = (x+xo,y+yo,w,h)
        if self.maxvalue == None:
            current_range = 1
        else:
            current_range = self.maxvalue

        if self.type == Gadget.TYPE_CUSTOM:
            if not self.need_redraw:
                return

            self.need_redraw = False
            if self.label == "#":
                if self.value != None:
                    primprops = copy.copy(config.primprops)
                    primprops.fillmode = copy.copy(config.primprops.fillmode)
                    primprops.fillmode.gradient_dither = self.value
                    primprops.fillmode.value = self.fillmode_value
                    primprops.fillmode.predraw = False
                    primprops.handlesymm = False
                    rx,ry,rw,rh = self.screenrect
                    cw = rw//2
                    ch = rh//2
                    cx = rx + cw
                    cy = ry + ch
                    if primprops.fillmode.value in [FillMode.ANTIALIAS, FillMode.SMOOTH]:
                        pygame.draw.rect(screen, (160,160,160), (rx,ry,rw+1,rh+1))
                        iw,ih = config.smooth_example_image.get_size()
                        ix = rx + ((rw - iw) // 2)
                        iy = ry + ((rh - ih) // 2)
                        screen.blit(config.smooth_example_image, (ix,iy))
                        tw = font.xsize * len(str(primprops.fillmode))
                        tx = rx + ((rw - tw) // 2)
                        ty = iy + ih
                        font.blitstring(screen, (tx,ty), str(primprops.fillmode).upper(), (0,0,0), (255,255,255))
                    fillellipse(screen, config.color, (cx,cy), cw, ch, primprops=primprops, interrupt=True)
                    if config.has_event():
                        #Got interrupted so still needs to redraw
                        self.need_redraw = True
        else:
            super(FillGadget, self).draw(screen, font, offset)

prev_fillmode = None
prev_color = -1
prev_fill_image = None
def draw_fill_indicator(screen):
    global prev_fillmode
    global prev_color
    global prev_fill_image

    if screen == None:
        #initialize
        prev_fillmode = None
        prev_color = -1
        prev_fill_image = None
        return

    fillmode_changed = False
    color_changed = False
    image_changed = False
    px = config.font.xsize // 8
    py = config.font.ysize // 8

    #check for change in fill mode
    if prev_fillmode != None and \
       prev_fillmode.value == config.fillmode.value and \
       prev_fillmode.gradient_dither == config.fillmode.gradient_dither:
        pass
    else:
        prev_fillmode = copy.copy(config.fillmode)
        fillmode_changed = True

    #check for change in color range
    if prev_color != config.color:
        color_changed = True
        for crange in config.cranges:
            if crange.is_active() and \
               prev_color >= crange.low and prev_color <= crange.high and \
               config.color >= crange.low and config.color <= crange.high:
                color_changed = False
        prev_color = config.color

    if prev_fill_image == None:
        prev_fill_image = pygame.Surface((px*16,py*9), 0, 8)
        prev_fill_image.set_palette(config.pal)
        image_changed = True

    if fillmode_changed or color_changed or image_changed:
        if config.fillmode.value in [FillMode.ANTIALIAS, FillMode.SMOOTH]:
            if config.fillmode.value == FillMode.ANTIALIAS:
                ind_text = "AA"
            else:
                ind_text = str(config.fillmode).upper()

            config.font.blitstring(prev_fill_image, (0,0), ind_text, (255,255,255))
        fillrect(prev_fill_image, config.color, (0,0), (px*16, py*9), interrupt=False)

    if config.fillmode.value != config.fillmode.SOLID:
        prev_fill_image.set_palette(config.pal)
        screen.blit(prev_fill_image, (px*180, py))

def fill_req(screen):
    config.stop_cycling()
    req = str2req("Fill Type", """
[Solid]     ###########
[Brush]     ###########
[Wrap]      ###########
[Pattern]   ###########
[Antialias] ###########
[Smooth]    ###########
            ###########
Gradient: [\x88\x89~\x8a\x8b~\x8c\x8d~\x8e\x8f~\x90\x91]
Dither:----------------00
[Cancel][OK]
""", "%#", mouse_pixel_mapper=config.get_mouse_pointer_pos, custom_gadget_type=FillGadget, font=config.font)
    req.center(screen)
    config.pixel_req_rect = req.get_screen_rect()

    for g in req.gadgets:
        #print("%s: %s" % (g.id, g.label))
        if g.label == str(config.fillmode):
            g.state = 1

    ditherg = req.gadget_id("7_8")
    ditherg.maxvalue = 22
    ditherg.value = config.fillmode.gradient_dither + 1
    ditherg.need_redraw = True

    dithervalg = req.gadget_id("23_8")
    if ditherg.value > 0:
        dithervalg.label = "%2d" % (ditherg.value-1)
    else:
        dithervalg.label = "\x99\x9a"
    dithervalg.need_redraw = True

    dithersampleg = req.gadget_id("12_0")
    dithersampleg.value = config.fillmode.gradient_dither
    dithersampleg.fillmode_value = config.fillmode.value
    dithersampleg.need_redraw = True

    fillmode_value = config.fillmode.value
    req.draw(screen)
    config.recompose()

    running = 1
    while running:
        event = config.xevent.wait()
        gevents = req.process_event(screen, event)

        if event.type == KEYDOWN and event.key == K_ESCAPE:
            running = 0

        for ge in gevents:
            if ge.gadget.type == Gadget.TYPE_BOOL:
                if ge.gadget.label == "OK" and not req.has_error():
                    config.fillmode.value = fillmode_value
                    config.fillmode.gradient_dither = ditherg.value - 1
                    config.menubar.indicators["fillmode"] = draw_fill_indicator
                    draw_fill_indicator(None)
                    running = 0
                elif ge.gadget.label == "Cancel":
                    running = 0
                elif ge.type == GadgetEvent.TYPE_GADGETUP and ge.gadget.label in FillMode.LABEL_STR:
                    fillmode_value = FillMode.LABEL_STR.index(ge.gadget.label)
                    dithersampleg.fillmode_value = fillmode_value
                    dithersampleg.need_redraw = True
            elif ge.gadget == ditherg:
                if ditherg.value > 0:
                    dithervalg.label = "%2d" % (ditherg.value-1)
                else:
                    dithervalg.label = "\x99\x9a"
                dithervalg.need_redraw = True
                dithersampleg.value = ditherg.value - 1
                dithersampleg.need_redraw = True

        if len(gevents) == 0:
            if event.type == MOUSEBUTTONDOWN:
                mouseX, mouseY = config.get_mouse_pointer_pos(event)
                if config.toolbar.is_inside((mouseX, mouseY)):
                    palg = config.toolbar.tool_id("palette")
                    palg.process_event(screen, event, config.get_mouse_pointer_pos)
                    dithersampleg.need_redraw = True
                elif not req.is_inside((mouseX, mouseY)):
                    mouseX2, mouseY2 = config.get_mouse_pixel_pos(event)
                    config.color = config.pixel_canvas.get_at_mapped((mouseX2, mouseY2))
                    dithersampleg.need_redraw = True

        for g in req.gadgets:
            if g.label == FillMode.LABEL_STR[fillmode_value]:
                g.state = 1

        if not config.xevent.peek((KEYDOWN, KEYUP, MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION, VIDEORESIZE)):
            req.draw(screen)
            config.recompose()

    config.pixel_req_rect = None
    config.recompose()

    return

