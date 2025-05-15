import locale
import os
import subprocess

import ghostscript
import win32print

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch

import cgi
import tempfile
import win32api


def print_test2():
    win32api.ShellExecute(
        0,
        "printto",
        r"C:\Users\emeric.proulx\PycharmProjects\engrave\templates\tag1_svg.svg",
        '"%s"' % "Epilog Engraver",
        ".",
        0
    )

def print_test3():
    gpath = r"C:\Users\emeric.proulx\Downloads\EpilogSuite_2.2.14.2_x64\ghostscript"
    GHOSTSCRIPT_PATH = "C:\\path\\to\\GHOSTSCRIPT\\bin\\gswin32.exe"
    GSPRINT_PATH = "C:\\path\\to\\GSPRINT\\gsprint.exe"

    # YOU CAN PUT HERE THE NAME OF YOUR SPECIFIC PRINTER INSTEAD OF DEFAULT
    currentprinter = win32print.GetDefaultPrinter()

    win32api.ShellExecute(0, 'open', GSPRINT_PATH,
                          '-ghostscript "' + GHOSTSCRIPT_PATH + '" -printer "' + currentprinter + '" "PDFFile.pdf"',
                          '.', 0)


def print_test4():
    def get_printer_name():
        printers = [printer[2] for printer in win32print.EnumPrinters(2)]
        if "Epilog Engraver" in printers:
            return "Epilog Engraver"
        else:
            raise ValueError("Printer 'Epilog Engraver' not found on the system.")
    try:
        printer_name = get_printer_name()  # Get the correct printer name
    except ValueError as e:
        print(e)
        return

    args = [
        "-dPrinted", "-dBATCH", "-dNOSAFER", "-dNOPAUSE", "-dNOPROMPT", "-q",
        "-dNumCopies#1",
        "-sDEVICE#mswinpr2",  # Use the mswinpr2 device for Windows printing
        f'-sOutputFile#"%printer%{printer_name}"',
        r'C:\Users\emeric.proulx\PycharmProjects\engrave\tmp_2024_10_22_11_15_25.pdf'
    ]

    encoding = locale.getpreferredencoding()
    args = [a.encode(encoding) for a in args]

    print("Ghostscript args:", args)  # Debug information

    ghostscript.Ghostscript(*args)


def print_test5():
    import win32print
    import win32ui
    from PIL import Image, ImageWin

    #
    # Constants for GetDeviceCaps
    #
    #
    # HORZRES / VERTRES = printable area
    #
    HORZRES = 8
    VERTRES = 10
    #
    # LOGPIXELS = dots per inch
    #
    LOGPIXELSX = 88
    LOGPIXELSY = 90
    #
    # PHYSICALWIDTH/HEIGHT = total area
    #
    PHYSICALWIDTH = 110
    PHYSICALHEIGHT = 111
    #
    # PHYSICALOFFSETX/Y = left / top margin
    #
    PHYSICALOFFSETX = 112
    PHYSICALOFFSETY = 113

    printer_name = win32print.GetDefaultPrinter()
    file_name = "test.jpg"

    #
    # You can only write a Device-independent bitmap
    #  directly to a Windows device context; therefore
    #  we need (for ease) to use the Python Imaging
    #  Library to manipulate the image.
    #
    # Create a device context from a named printer
    #  and assess the printable size of the paper.
    #
    hDC = win32ui.CreateDC()
    hDC.CreatePrinterDC(printer_name)
    printable_area = hDC.GetDeviceCaps(HORZRES), hDC.GetDeviceCaps(VERTRES)
    printer_size = hDC.GetDeviceCaps(PHYSICALWIDTH), hDC.GetDeviceCaps(PHYSICALHEIGHT)
    printer_margins = hDC.GetDeviceCaps(PHYSICALOFFSETX), hDC.GetDeviceCaps(PHYSICALOFFSETY)

    #
    # Open the image, rotate it if it's wider than
    #  it is high, and work out how much to multiply
    #  each pixel by to get it as big as possible on
    #  the page without distorting.
    #
    bmp = Image.open(file_name)
    if bmp.size[0] > bmp.size[1]:
        bmp = bmp.rotate(90)

    ratios = [1.0 * printable_area[0] / bmp.size[0], 1.0 * printable_area[1] / bmp.size[1]]
    scale = min(ratios)

    #
    # Start the print job, and draw the bitmap to
    #  the printer device at the scaled size.
    #
    hDC.StartDoc(file_name)
    hDC.StartPage()

    dib = ImageWin.Dib(bmp)
    scaled_width, scaled_height = [int(scale * i) for i in bmp.size]
    x1 = int((printer_size[0] - scaled_width) / 2)
    y1 = int((printer_size[1] - scaled_height) / 2)
    x2 = x1 + scaled_width
    y2 = y1 + scaled_height
    dib.draw(hDC.GetHandleOutput(), (x1, y1, x2, y2))

    hDC.EndPage()
    hDC.EndDoc()
    hDC.DeleteDC()


def print_test_6():
    source_file_name = "c:/temp/temp.txt"
    pdf_file_name = tempfile.mktemp(".pdf")

    styles = getSampleStyleSheet()
    h1 = styles["h1"]
    normal = styles["Normal"]

    doc = SimpleDocTemplate(pdf_file_name)
    #
    # reportlab expects to see XML-compliant
    #  data; need to escape ampersands &c.
    #
    text = cgi.escape(open(source_file_name).read()).splitlines()

    #
    # Take the first line of the document as a
    #  header; the rest are treated as body text.
    #
    story = [Paragraph(text[0], h1)]
    for line in text[1:]:
        story.append(Paragraph(line, normal))
        story.append(Spacer(1, 0.2 * inch))

    doc.build(story)
    win32api.ShellExecute(0, "print", pdf_file_name, None, ".", 0)


def print_svg_1(svg_file, printer_name):
    # Ensure the printer name is correct
    printer = win32print.OpenPrinter(printer_name)

    # Send the SVG file to the printer
    try:
        # Open the SVG file
        with open(svg_file, 'r') as f:
            raw_data = f.read()

        # Create a print job
        job_id = win32print.StartDocPrinter(printer, 1, ("SVG Print Job", None, "RAW"))
        win32print.StartPagePrinter(printer)
        win32print.WritePrinter(printer, raw_data.encode())
        win32print.EndPagePrinter(printer)
        win32print.EndDocPrinter(printer)
    except Exception as e:
        print("FAILED")
        print(e)
    finally:
        win32print.ClosePrinter(printer)


def print_ps_1():
    def convert_svg_to_ps(svg_file, ps_file):
        print(f"Converting {svg_file} to PostScript...")
        result = subprocess.run(
            [r'C:\Program Files\Inkscape\bin\inkscape.exe', '--export-type=ps', svg_file, '-o', ps_file])
        if result.returncode != 0:
            print(f"Conversion failed with code {result.returncode}")
        else:
            print(f"PostScript file created: {ps_file}")

    def print_ps_file(ps_file, printer_name):
        print(f"Opening printer {printer_name}...")
        printer = win32print.OpenPrinter(printer_name)

        # Document info as a tuple (doc_name, output_file, data_type)
        doc_info = ("PostScript Print Job", None, "RAW")

        try:
            print(f"Creating print job for {ps_file}...")
            job_id = win32print.StartDocPrinter(printer, 1, doc_info)
            if job_id:
                print(f"Print job {job_id} started successfully.")
            else:
                print("Failed to start print job.")

            win32print.StartPagePrinter(printer)

            # Open and read the PostScript file to send to the printer
            with open(ps_file, 'rb') as f:
                file_data = f.read()
                print(f"Sending {len(file_data)} bytes of data to the printer...")
                win32print.WritePrinter(printer, file_data)

            win32print.EndPagePrinter(printer)
            win32print.EndDocPrinter(printer)
            print(f"Print job {job_id} completed.")

        except Exception as e:
            print(f"An error occurred while printing: {e}")
        finally:
            win32print.ClosePrinter(printer)

    svg_file = r'/templates/tag1_svg.svg'
    ps_file = r'C:\Users\emeric.proulx\PycharmProjects\engrave\templates\tag1_svg.ps'
    printer_name = "Epilog Engraver"

    convert_svg_to_ps(svg_file, ps_file)

    if os.path.exists(ps_file):
        print(f"PostScript file {ps_file} exists, proceeding to print...")
        print_ps_file(ps_file, printer_name)
    else:
        print(f"PostScript file {ps_file} does not exist, printing aborted.")

def open_browser():
    result = subprocess.run(
        r"C:\Users\emeric.proulx\AppData\Local\Google\Chrome\Application\chrome.exe C:\Users\emeric.proulx\PycharmProjects\engrave\remove\temp_output.pdf"
    )

if __name__ == '__main__':
    print_test4()