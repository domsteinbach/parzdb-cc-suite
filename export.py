import csv
from datetime import datetime
import os
import shutil
from model.literature import IGNORED_LITERATURE_KEYS
from mysql_import import BACKUP_DIR

EXPORT_PATH = "output"
BACKUP_DIR = "backup"


class Exporter:
    def __init__(self, assembler, export_path=EXPORT_PATH):
        self.assembler = assembler
        self.export_path = export_path
        self.html_dir = os.path.join(self.export_path, "fassungskommentare")
        self.cleanup_output()


    def cleanup_output(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_subdir = os.path.join(self.export_path,BACKUP_DIR, timestamp)
        os.makedirs(backup_subdir, exist_ok=True)
        # Move all files and directories from the export directory to the backup directory
        for filename in os.listdir(self.html_dir):
            if not filename.endswith(".html"):
                continue
            source_path = os.path.join(self.html_dir, filename)
            destination_path = os.path.join(backup_subdir, filename)

            shutil.move(source_path, destination_path)


    def export_commentary_as_html(self, commentary, include_literature=False, return_html_string=False):
        # Generate the initial HTML

        literature = []

        if include_literature:
            if commentary.vers == '1.21':
                print('debug')
            lit = commentary.get_cited_literature_keys()
            for key in lit:
                if key not in self.assembler.literature:
                    found_key = self.assembler.deep_search_lit_key(key)
                    if found_key:
                        l = self.assembler.literature[found_key]
                        if l:
                            literature.append(self.assembler.literature[found_key])
                        else:
                            print(f"WARNING: Literature '{key}' not found.")
                    continue
                literature.append(self.assembler.literature[key])

        html_string = commentary.get_as_html(literature = literature)

        if return_html_string:
            return html_string

        # Write the file with UTF-8 encoding
        with open(f"{self.html_dir}/{commentary.id}.html", "w", encoding="utf-8") as file:
            file.write(html_string)

    def export_as_csv(self):
        with open(f"{self.export_path}/import/fassungs_kommentar.csv", "w") as file:
            writer = csv.writer(file, quoting=csv.QUOTE_ALL)
            writer.writerow(["id", "fassung", "fassung_targets", "vers", "end_vers", "commentary"])

            html = None

            for c in self.assembler.commentaries:
                literature = []
                lit = c.get_cited_literature_keys()
                for key in lit:
                    if key not in self.assembler.literature:
                        found_key = self.assembler.deep_search_lit_key(key)
                        if found_key:
                            l = self.assembler.literature[found_key]
                            if l:
                                literature.append(self.assembler.literature[found_key])
                            else:
                                print(f"WARNING: Literature '{key}' not found.")
                        continue
                    literature.append(self.assembler.literature[key])

                writer.writerow([
                    c.id,
                    c.fassung,
                    ''.join(c.fassung_targets),
                    str(c.vers),
                    str(c.end_vers) if c.end_vers else '',
                    c.get_as_html_element_str(literature=literature)
                ])

    def export_all_directlinks(self):
        with open(f"{self.export_path}/consistency/direct_links.html", "w") as file:
            file.write("<html><head><meta charset='UTF-8'></head><body>")

            fassunng = ''
            for c in self.assembler.commentaries:
                if c.fassung != fassunng:
                    fassunng = c.fassung
                    if c.fassung == 'a':
                        file.write(f"<h2>Fassungsübergreifende Kommentare (DmGT)</h2>")
                    else:
                        file.write(f"<h2>Fassung {c.fassung}</h2>")
                link = f"http://130.92.252.118:8090/parzdb_test/fassungskommentare/{c.id}.html"
                fassungs_link = f"http://130.92.252.118:8090/parzdb_test/parzival.php?page=fassungen&dreissiger={c.vers.split('.')[0]}"
                file.write(f"<span>Vers {c.vers} </span> Link zur <a href='{fassungs_link}' target='_blank' >Fassungsansicht</a> <span> | Link direkt zum Html: </span> <a href='{link}'  target='_blank' >{c.id}</a> <br>")
            file.write("</body></html>")


    def export_all_as_one_html(self):
        with open(f"{self.html_dir}/all.html", "w") as file:
            href = "commentary.css"
            html_string = f"<html><head><meta charset='UTF-8'><link rel='stylesheet' href='{href}'></head><body>"
            html_string = f"<html><head><meta charset='UTF-8'></head><body>"
            for c in self.assembler.commentaries:
                html_string += c.get_as_html_element_str()
                lit = c.get_cited_literature_keys()
                for key in lit:
                    if key not in self.assembler.literature:
                        continue
                    literature = self.assembler.literature[key]
                    html_string += str(literature.as_html())

            html_string += "</body></html>"
            file.write(html_string)

    def export_missing_literature(self):
        with open('output/consistency/missing_literature.csv', "w") as file:
            writer = csv.writer(file, quoting=csv.QUOTE_ALL)
            writer.writerow(["key", "fassung", "vers"])
            for l in self.assembler.not_found_literature:
                writer.writerow(l)