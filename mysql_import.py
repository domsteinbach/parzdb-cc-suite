import csv
import os
import pandas as pd
import mysql.connector
import datetime
from config import ENVIRONMENT
from config import EXPORT_PATH, BACKUP_DIR, MYSQL_PASSWORD, MYSQL_USER, MYSQL_HOST, MYSQL_DATABASE, PORT


class TableDef:
    def __init__(self):
        self.tables = {
            "fassungs_kommentar": [
                "`id` varchar(255) UNIQUE NOT NULL",
                "`fassung` varchar(255) NOT NULL",
                "`fassung_targets` varchar(255) NOT NULL",
                "`vers` varchar(255) NOT NULL",
                "`end_vers` varchar(255) NOT NULL",
                "`commentary` TEXT DEFAULT NULL",  # html string
                "PRIMARY KEY (`id`)"
            ]
        }


class Importer:

    def __init__(self):
        self.mydb = None
        self.mycursor = None
        self.conn = None
        self.table_def = None

    if MYSQL_DATABASE == "parzival_db_test" and ENVIRONMENT != 'test':
        raise Exception("You are trying to import to the test database with dynamic links pointing to the production server. Please adjust.")

    if MYSQL_DATABASE == "parzival_db" and ENVIRONMENT == 'test':
        raise Exception("You are trying to import to the productive database with dynamic links pointing to the test server. Please adjust.")

    def connect(self):
        self.mydb = mysql.connector.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            passwd=MYSQL_PASSWORD,
            database=MYSQL_DATABASE,
            port=PORT
        )
        self.mycursor = self.mydb.cursor()
        self.table_def = TableDef()

        # Connect to MySQL server through the SSH tunnel
        self.conn = mysql.connector.connect(
            host=MYSQL_HOST,
            port=PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE
        )

    def disconnect(self):
        self.conn.close()

    def _backup_table(self, database_name, table_name):
        """Backup a specific table to a SQL file."""
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = os.path.join(BACKUP_DIR, f"{timestamp}_backup.sql")

        command = f"mysqldump -h {MYSQL_HOST} -P {PORT} -u {MYSQL_USER} -p{MYSQL_PASSWORD} {database_name} {table_name} > {backup_file}"
        os.system(command)

    def _import_table(self, file, table_name):
        columns = []
        t_def = TableDef()
        try:
            columns = t_def.tables[table_name]
        except KeyError:
            print(table_name + ' has no definition. Inferring.')

        # Read the CSV file with inferred data types
        try:
            # Read and process the CSV file
            df = pd.read_csv(file)
        except pd.errors.ParserError as e:
            print(f"Error parsing file {file}: {e}")

        if not len(columns):
            # if there is no definition for that table, we infer it
            for col_name, dtype in df.dtypes.items():
                if dtype == 'int64':
                    columns.append(f"{col_name} INT")
                elif dtype == 'float64':
                    columns.append(f"{col_name} FLOAT")
                elif dtype == 'bool':
                    columns.append(f"{col_name} BOOLEAN")
                else:
                    columns.append(f"{col_name} VARCHAR(255)")
        try:
            cursor = self.conn.cursor()

            # Drop the table if it exists
            drop_table_query = f"DROP TABLE IF EXISTS `{table_name}`"
            cursor.execute(drop_table_query)
            print(f'table {table_name} dropped')

            # Generate CREATE TABLE statement with backticks for column names
            create_table_query = f"CREATE TABLE `{table_name}` ({', '.join(columns)})"
            cursor.execute(create_table_query)
            print(f"Table {table_name} successfully created")

            # insert data
            print('inserting data')
            statements = self._generate_insert_statements_from_csv(file, table_name)
            for statement in statements:
                cursor.execute(statement)

            self.conn.commit()

        except mysql.connector.Error as error:
            print(f"!!! ERROR: {error}")

        except Exception as general_error:
            print(f"!!! ERROR, GENERAL ERROR: {general_error}")

    def _generate_insert_statements_from_csv(self, file_name, table_name, batch_size=500):
        cleaner = DataCleaner()

        statements = []

        with open(file_name, 'r') as file:
            reader = csv.DictReader(file)
            rows_buffer = []

            for row in reader:
                cleaned_row = cleaner.clean_row(table_name, row)
                values = ', '.join([f"'{value}'" if value is not None else "NULL" for value in cleaned_row.values()])
                rows_buffer.append(f"({values})")

                if len(rows_buffer) >= batch_size:
                    columns = ', '.join(cleaned_row.keys())
                    statement = f"INSERT INTO {table_name} ({columns}) VALUES {', '.join(rows_buffer)};"
                    statements.append(statement)
                    rows_buffer = []

            # Handle any remaining rows in buffer
            if rows_buffer:
                columns = ', '.join(cleaned_row.keys())
                statement = f"INSERT INTO {table_name} ({columns}) VALUES {', '.join(rows_buffer)};"
                statements.append(statement)

        return statements

    def import_files(self, import_dir=EXPORT_PATH):
        script_dir = os.path.dirname(
            os.path.abspath(__file__))
        import_dir = os.path.join(script_dir, import_dir)

        file_names = os.listdir(import_dir)
        sorted_files = sorted(file_names)

        for file in sorted_files:
            if file.endswith(".csv"):
                table_name = os.path.splitext(file)[
                    0].lower()  # Get file name without extension and convert to lowercase
                print('### ', table_name)
                # import_table_with_pymsql(f"import/{file}", table_name)
                self._import_table(f"output/import/{file}", table_name)


class DataCleaner:

    def __init__(self):
        self.table_def = TableDef()

    def get_column_type(self, table_name, column_name):
        for column_def in self.table_def.tables[table_name]:
            if column_def.startswith(f'`{column_name}`'):
                if 'int(11)' in column_def:
                    return 'int'
                elif 'varchar' in column_def:
                    return 'varchar'
                elif 'BOOLEAN' in column_def:
                    return 'boolean'
                elif 'TEXT' in column_def:
                    return 'text'
                # Add more data types as needed...
        return None

    def _clean_value(self, table_name, column_name, value):
        col_type = self.get_column_type(table_name, column_name)

        # Escape any single quotes in string values
        if isinstance(value, str):
            value = value.replace("'", "''")

        # check if the value is a list
        if isinstance(value, list):
            print(f"Data Cleanup: Value is a list: {value}")

        # Clean empty strings and None values
        if (value and value.strip() == "") or not value:
            if col_type in ['int', 'boolean']:
                return None  # use None to represent SQL NULL
            elif col_type in ['varchar', 'text']:
                return ""
        return value

    def clean_row(self, table_name, row):
        for column_name in row:
            row[column_name] = self._clean_value(table_name, column_name, row[column_name])
        return row
