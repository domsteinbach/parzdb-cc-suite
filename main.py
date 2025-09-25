from extract_docx import extract_docs
from assembler import DataAssembler
import datetime
from consistency import ConsistencyChecker
from export import Exporter
from mysql_import import Importer
import hashlib
import config


def generate_version_hash():
    current_time = datetime.datetime.now().isoformat()
    return hashlib.md5(current_time.encode()).hexdigest()

def run():
    config.VERSION_HASH = generate_version_hash()
    print(f"Generated VERSION_HASH: {config.VERSION_HASH}")

    docs = extract_docs()
    a = DataAssembler(docs)
    e = Exporter(a)
    for idx, c in enumerate(a.commentaries):
        e.export_commentary_as_html(c, True)
    e.export_as_csv()
    e.export_missing_literature()
    import_to_db()


    e.export_all_directlinks()
    e.export_all_as_one_html()

    # checker = ConsistencyChecker()
    # checker.check_hyperlinks(a)

    print('end')

def import_to_db():
    importer = Importer()
    importer.connect()
    importer.import_files()
    importer.disconnect()

if __name__ == '__main__':
    run()