import os
import platform
import sys
import winreg
import numpy as np
from PyQt5.QtWidgets import QFileDialog

from core.template import Label


def mm2pix(mm):
    return mm*5

def pix2mm(pix):
    return pix/5

def inch2mm(inch):
    return inch * 25.4

def get_key_from_value(d: dict, value: any):
    for k, v in zip(d.keys(), d.values()):
        if v == value:
            return k

if hasattr(sys, "_MEIPASS"):
    _path_res = os.path.join(sys._MEIPASS, "res")
else:
    _path_res = "./res"
print("Resolved Resource path:", _path_res)
def get_res_item(filename: str):
    return os.path.join(_path_res, filename)

def solve_rect_position(lbl: Label, others, w_border, h_border, dx=0, dy=0, margin=2.0):
    if lbl is None:
        return
    m = margin
    bw = w_border
    bh = h_border
    ox, oy = lbl.x, lbl.y
    min_bw, max_bw = 0+margin, bw - lbl.width - margin*2
    min_bh, max_bh = 0+margin, bh - lbl.height - margin*2
    lbl.x = max(min_bw, min(lbl.x + dx, max_bw))
    lbl.y = max(min_bh, min(lbl.y + dy, max_bh))
    others = [l for l in others if l is not lbl]
    if not others:
        return
    if not any([lbl.overlaps(l, 2.0) for l in others]):
        return
    others_x = np.array([l.x for l in others])
    others_y = np.array([l.y for l in others])
    others_w = np.array([l.width for l in others])
    others_h = np.array([l.height for l in others])
    lbl_w = lbl.width
    lbl_h = lbl.height
    max_iter = 10
    for _ in range(max_iter):
        lbl_x = lbl.x
        lbl_y = lbl.y
        over_left = lbl_x + lbl_w + m > others_x
        over_right = lbl_x < others_x + others_w + m
        over_top = lbl_y + lbl_h + m > others_y
        over_bot = lbl_y < others_y + others_h + m
        overlaps = over_left & over_right & over_top & over_bot
        if not np.any(overlaps):
            return
        overlap_indices = np.where(overlaps)[0]
        ol_x = others_x[overlap_indices]
        ol_y = others_y[overlap_indices]
        ol_w = others_w[overlap_indices]
        ol_h = others_h[overlap_indices]
        ol_l = (ol_x + ol_w + m) - lbl_x
        ol_r = (lbl_x + lbl_w + m) - ol_x
        ol_t = (ol_y + ol_h + m) - lbl_y
        ol_b = (lbl_y + lbl_h + m) - ol_y
        adj_x = np.where(lbl_x < ol_x, -ol_r, ol_l)
        adj_y = np.where(lbl_y < ol_y, -ol_b, ol_t)
        min_adj_x = adj_x[np.argmin(np.abs(adj_x))]
        min_adj_y = adj_y[np.argmin(np.abs(adj_y))]
        if abs(min_adj_x) < abs(min_adj_y):
            lbl.x += min_adj_x
            lbl.x = max(min_bw, min(lbl.x, max_bw))
        else:
            lbl.y += min_adj_y
            lbl.y = max(min_bh, min(lbl.y, max_bh))
    else:
        # Could not resolve overlaps within max iterations. Compute distances to other labels
        center_lbl = np.array([lbl.x + lbl_w / 2, lbl.y + lbl_h / 2])
        centers_others = np.column_stack((others_x + others_w / 2, others_y + others_h / 2))
        distances = np.linalg.norm(centers_others - center_lbl, axis=1)
        sorted_indices = np.argsort(distances)
        for idx in sorted_indices:
            ol = others[idx]
            ow_n = ol.x - lbl_w - m
            ow_p = ol.x + ol.width + m
            oh_n = ol.y - lbl_h - m
            oh_p = ol.y + ol.height + m
            positions = [
                (ol.x, oh_n), (ol.x, oh_p),  # b
                (ow_n, ol.y), (ow_p, ol.y),  # r
                (ow_n, oh_n), (ow_p, oh_n),  # tr
                (ow_n, oh_p), (ow_p, oh_p),  # br
            ]
            for x_new, y_new in positions:
                if (0 <= x_new <= bw - lbl_w) and (0 <= y_new <= bh - lbl_h):
                    lbl.x, lbl.y = x_new, y_new
                    lbl_x = lbl.x
                    lbl_y = lbl.y
                    over_left = lbl_x + lbl_w + m > others_x
                    over_right = lbl_x < others_x + others_w + m
                    over_top = lbl_y + lbl_h + m > others_y
                    over_bot = lbl_y < others_y + others_h + m
                    overlaps = over_left & over_right & over_top & over_bot
                    if not np.any(overlaps):
                        return
        lbl.x, lbl.y = ox, oy
        print("Warning: Could not resolve overlaps.")

def open_dialog_filepath(filter: str = "Images (*.png *.jpg *.jpeg)"):
    dialog = QFileDialog()
    dialog.setWindowTitle("Select Path")
    dialog.setNameFilter(filter)
    dialog.setFileMode(QFileDialog.ExistingFile)
    if dialog.exec_() == QFileDialog.Accepted:
        image_path = dialog.selectedFiles()[0]
        print("Selected file:", image_path)
        return image_path
    return None

def find_chrome_path():
    os_type = platform.system()
    if os_type == 'Windows':
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Google\Chrome") as key:
                chrome_path, _ = winreg.QueryValueEx(key, "Path")
                return chrome_path
        except FileNotFoundError:
            pass
        common_paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            r"C:\Users\%USERNAME%\AppData\Local\Google\Chrome\Application\chrome.exe",
            r"C:\Users\%USERNAME%.JACMAR\AppData\Local\Google\Chrome\Application\chrome.exe"
        ]
        for path in common_paths:
            path_to_check = path.replace("%USERNAME%", os.getenv("USERNAME"))
            if os.path.exists(path_to_check):
                return path_to_check
        # Check PATH environment variable
        for path in os.environ["PATH"].split(os.pathsep):
            chrome_exe = os.path.join(path, "chrome.exe")
            if os.path.exists(chrome_exe):
                return chrome_exe
    elif os_type == 'Darwin':  # macOS
        common_paths = [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            "/Applications/Chromium.app/Contents/MacOS/Chromium"
        ]
        for path in common_paths:
            if os.path.exists(path):
                return path
    else:  # Linux
        common_paths = ["/usr/bin/google-chrome", "/usr/bin/chromium-browser"]
        for path in common_paths:
            if os.path.exists(path):
                return path
        if os.path.exists("/snap/bin/chromium"):
            return "/snap/bin/chromium"

    return None