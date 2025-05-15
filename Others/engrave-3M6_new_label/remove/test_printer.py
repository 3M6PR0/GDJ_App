import os
import subprocess
import sys

import win32api
import win32print
def print_pdf_with_shell_execute(pdf_path, printer_name):
    try:
        # Set the default printer
        win32print.SetDefaultPrinter(printer_name)

        # Use ShellExecute to print the PDF
        win32api.ShellExecute(
            0,
            "print",
            pdf_path,
            None,
            ".",
            0
        )
        print(f"Print command sent for {pdf_path} to {printer_name}")
    except Exception as e:
        print(f"An error occurred: {e}")

def print_pdf_with_ghostscript(pdf_path, printer_name, gs_executable):
    # Build Ghostscript arguments without -sPPD
    gs_command = [
        gs_executable,
        '-dBATCH',
        '-dNOPAUSE',
        '-dPrinted',
        '-sDEVICE=mswinpr2',
        f'-sOutputFile="%printer%\\"{printer_name}\\""',
        f'"{pdf_path}"'
    ]

    print(f"Executing Ghostscript command:\n{' '.join(gs_command)}\n")

    try:
        # Run the Ghostscript command
        result = subprocess.run(
            gs_command,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        print(f"Print job sent successfully to {printer_name}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error printing PDF with Ghostscript:\n{e.stderr}\n")
        return False

if __name__ == "__main__":
    # Paths to the required files and executables
    pdf_path = r'/tmp_2024_10_22_11_15_25.pdf'
    gs_executable = r'C:\Program Files\gs\gs10.04.0\bin\gswin64.exe'

    # Ensure the PDF file exists
    if not os.path.isfile(pdf_path):
        print(f"PDF file not found: {pdf_path}")
        sys.exit(1)

    # Ensure the Ghostscript executable exists
    if not os.path.isfile(gs_executable):
        print(f"Ghostscript executable not found: {gs_executable}")
        sys.exit(1)

    # Enumerate printers to find the Epilog Engraver
    printers = win32print.EnumPrinters(
        win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
    )
    printer_name = None

    print("Available printers:")
    for printer in printers:
        print(f" - {printer[2]}")
        if 'Epilog Engraver' in printer[2]:
            printer_name = printer[2]

    if not printer_name:
        print("Epilog Engraver printer not found.")
        sys.exit(1)
    else:
        print(f"\nUsing printer: {printer_name}\n")

    # Print the PDF file
    if not print_pdf_with_shell_execute(pdf_path, printer_name):
        sys.exit(1)
