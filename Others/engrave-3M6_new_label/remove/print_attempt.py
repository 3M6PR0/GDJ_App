import tempfile
import os
import subprocess
from io import BytesIO

import cairosvg
import win32print


def print_svg(svg_file):
    def get_printer_name():
        printers = [printer[2] for printer in win32print.EnumPrinters(2)]
        if "Epilog Engraver" in printers:
            return "Epilog Engraver"
        else:
            raise ValueError("Printer 'Epilog Engraver' not found on the system.")

    try:
        printer_name = get_printer_name()
    except ValueError as e:
        print(e)
        return

    # Convert SVG to PDF bytes
    pdf_bytes_io = BytesIO()
    cairosvg.svg2pdf(url=svg_file, write_to=pdf_bytes_io)
    pdf_data = pdf_bytes_io.getvalue()

    # Save PDF to temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_pdf_file:
        temp_pdf_file.write(pdf_data)
        temp_pdf_file_path = temp_pdf_file.name

    # Path to SumatraPDF
    sumatra_exe = r"C:\Users\emeric.proulx\AppData\Local\SumatraPDF\SumatraPDF.exe"

    if not os.path.exists(sumatra_exe):
        print("SumatraPDF not found at:", sumatra_exe)
        return

    # Use SumatraPDF to print the PDF silently with corrected print settings
    print_command = [
        sumatra_exe,
        #"-print-to", printer_name,  # Specify the printer
        "-print-dialog",  # Corrected paper size
        #"-print-scaling", "none",  # Adjust scaling as needed
        "-silent",  # No dialogs
        temp_pdf_file_path
    ]

    try:
        subprocess.run(print_command, check=True)
        print("Print job sent successfully.")
    except subprocess.CalledProcessError as e:
        print("Failed to print:", e)
    finally:
        # Delete the temporary PDF file
        os.unlink(temp_pdf_file_path)


if __name__ == "__main__":
    result = subprocess.run(
        r"C:\Users\emeric.proulx\AppData\Local\Google\Chrome\Application\chrome.exe C:\Users\emeric.proulx\PycharmProjects\engrave\core\labelsgencsa_1727884000.4842212.svg"
    )
    # svg_file_path = r"C:\Users\emeric.proulx\PycharmProjects\engrave\core\labelsgencsa_1727884011.5921345.svg"
    # print_svg(svg_file_path)



