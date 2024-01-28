import os
import zipfile
from email import policy
from email.parser import BytesParser
from datetime import datetime
import shutil

from rich.console import Console
from rich.progress import Progress
from rich import print

console = Console()

def extract_year_from_email(file_path):
    with open(file_path, 'rb') as file:
        # Parse the email file
        email_message = BytesParser(policy=policy.default).parse(file)

        if email_message['date']:
            # Parse the date string to datetime object
            date_obj = datetime.strptime(email_message['date'], '%a, %d %b %Y %H:%M:%S %z')
            return date_obj.year

    return None

def archive_emails(source_folder, archive_folder):
    open_zips = {}
    source_dir = os.listdir(source_folder)
    with Progress(console=console) as progress:
        task = progress.add_task("Archiving email files", total=len(source_dir))
        for filename in source_dir:
            progress.advance(task)
            file_path = os.path.join(source_folder, filename)

            # Skip if it's not a file
            if not os.path.isfile(file_path):
                continue

            year = extract_year_from_email(file_path)
            if year:
                zip_rootname = f"{year}.zip"
                zip_filename = os.path.join(archive_folder, zip_rootname)


                # Check if the ZIP file exists, if not, create it
                if not os.path.exists(zip_filename):
                    with zipfile.ZipFile(zip_filename, 'w', compression=zipfile.ZIP_LZMA) as zipf:
                        pass  # Create an empty ZIP file

                # Append file to the corresponding ZIP file
                if year not in open_zips:
                    open_zips[year] = zipfile.ZipFile(zip_filename, 'a', compression=zipfile.ZIP_LZMA)

                open_zips[year].write(file_path, os.path.basename(file_path))

                # Remove the file from the source folder
                os.remove(file_path)
                progress.console.print(f"source file: [bold yellow]{filename} [/]" 
                    + f" -> [bold green]{zip_rootname}[/]"
                    + " :wastebasket:")
            else:
                progress.console.print(f"source file: [bold yellow]{filename} [/]" 
                    + f" -> [bold red]skipped[/] (could not find year)")

    # Close all open ZIP files
    for zipf in open_zips.values():
        zipf.close()

def recompress_zip_file(zip_path):
    temp_zip_path = zip_path + ".temp"

    with Progress(console=console) as progress:
        with zipfile.ZipFile(zip_path, 'r') as source_zip:
            with zipfile.ZipFile(temp_zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as new_zip:
                info_list = source_zip.infolist()
                task = progress.add_task(f"Recompressing {zip_path}", total=len(info_list))
                for file_info in info_list:
                    progress.advance(task)
                    # Read file data from source zip file
                    with source_zip.open(file_info) as source_file:
                        # Write file data to new zip file
                        new_zip.writestr(file_info, source_file.read())

    # Replace the old ZIP file with the new one
    os.remove(zip_path)
    shutil.move(temp_zip_path, zip_path)

def recompress_all_zip_files(folder_path):
    for filename in os.listdir(folder_path):
        if filename.endswith(".zip"):
            zip_path = os.path.join(folder_path, filename)
            recompress_zip_file(zip_path)

source_folder = '/Users/andrejk/Maildir/new/'
archive_folder = '/Users/andrejk/OneDrive/Archive/email/'

# recompress_all_zip_files(archive_folder)
archive_emails(source_folder, archive_folder)

