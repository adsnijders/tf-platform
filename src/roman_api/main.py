# --- Importing modules and loading env variables

# Import modules
import os
import re

import psycopg2
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from roman_converter.cli import ar_to_rom_conv, rom_to_ar_conv

# --- Creating DB Connection ---


# Function for creating the postgres-db connection
def get_db_connection():
    """
    Connects to the postgres db.
    """
    try:
        conn = psycopg2.connect(
            host=os.getenv("POSTGRES_HOST"),
            port=os.getenv("POSTGRES_PORT"),
            dbname=os.getenv("POSTGRES_NAME"),
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD"),
        )

        return conn

    except Exception as e:
        raise RuntimeError("Could not connect to the database") from e


# --- Creating the table that stores the rom-ar key-value pairs and retrieving them ---


# Function for creating a table in postgres
def init_db() -> None:
    """
    Checks if table "roman" exists. If not, the tables is created.
    """
    try:
        conn = get_db_connection()

        cur = conn.cursor()

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS roman (
                inp VARCHAR,
                out VARCHAR
            );
        """
        )

        conn.commit()

        cur.close()

        conn.close()
        print("✅ Table 'roman' checked / created.")

    except Exception as e:
        print(str(e))


# Define a function get the value from postgres-db when the key exists
def get_value_if_key_exists(cur, inp: str | int) -> None | str:
    """
    Checks whether a certain key exists in postgres.
    Returns the value if it exists, or None if it doesn't.
    """
    cur.execute(
        """
            SELECT out
            FROM roman
            WHERE inp = %s
            ;
        """,
        (inp,),
    )

    rows = cur.fetchall()

    if len(rows) > 0:
        # print(rows)
        return rows[0][0]
    else:
        return None


# Define a function that posts the key-value pair into postgres-db
def post_value_if_key_does_not_exist(conn, cur, inp: str, out: str):
    """
    Inserts the key-value pair in postgres-db.
    """
    try:
        cur.execute(
            """
            INSERT INTO roman (inp, out) 
            VALUES (%s, %s)
            ;
            """,
            (inp, out),
        )
        conn.commit()
        print(f"✅ Values ({inp}, {out}) have been inserted into table roman.")

    except Exception as e:
        raise RuntimeError(f"Could not insert ({inp}, {out})") from e


# Define Roman to Arabic mapping
rom_to_ar = {
    "i": 1,
    "iv": 4,
    "v": 5,
    "ix": 9,
    "x": 10,
    "xl": 40,
    "l": 50,
    "xc": 90,
    "c": 100,
    "cd": 400,
    "d": 500,
    "cm": 900,
    "m": 1000,
}


# Define a function to validate the Roman input
def val_rom_inp(rom_inp) -> None:
    """
    Validate the input for rom_to_ar_conv
    """
    # The input must be a string
    if not isinstance(rom_inp, str):
        raise TypeError("Input must be a string")

    # Convert the input to lowercase
    rom_inp = rom_inp.lower()

    # Reject more than 3 of the same numeral in a row
    if re.search(r"(i{4,}|x{4,}|c{4,}|m{4,})", rom_inp):
        raise ValueError(
            "Invalid Roman numeral: cannot repeat the same numeral for more than three times"
        )

    # Allow only valid characters
    if not re.fullmatch(r"[ivxlcdm]+", rom_inp):
        raise ValueError("Input contains invalid Roman numeral")


# Initiate the app
app = FastAPI()


@app.post("/rom-to-ar/{inp}")
def get_ar_output(inp):
    """
    1. Validate the roman input
    2. Tries to create a connection to postgres.
    3. Tries to find inp in the postgres-db and immediately return the associated value.
    4. (Optional) If not present, it converts the input, posts the input-output in postgres-db and returns the conversion
    """
    # --- 1. Validate the roman input ---

    val_rom_inp(inp)

    # --- 2. Connect to postgres ---

    conn = get_db_connection()
    cur = conn.cursor()

    # --- 3. Try to find inp in postgres-db

    inp = str(inp).lower().strip()
    db_value = get_value_if_key_exists(cur, inp)
    if db_value:
        print(f"Key {inp} is found in postgres")
        print(f"Arabic number: {db_value}")
        return JSONResponse(content={"Arabic number": db_value})

    # --- 4. Convert the input, post the input-output in postgres-db and return the conversion

    conv = rom_to_ar_conv(inp)

    post_value_if_key_does_not_exist(conn, cur, inp, conv)

    cur.close()
    conn.close()

    print(f"Arabic number: {conv}")
    return JSONResponse(content={"Arabic number": conv})


# --- Create mappings ---

# Define Arabic to Roman mapping
ar_to_rom = {ar_nr: rom_nr for rom_nr, ar_nr in rom_to_ar.items()}


# Define a function to validate the Arabic input
def val_ar_inp(ar_inp: str | int) -> None:
    """
    Validate the input for ar_to_rom_conv
    """
    # The input must be an integer or a string convertible to an integer
    try:
        ar_inp = int(ar_inp.lower().strip())
    except Exception as e:
        raise TypeError(
            "Input must be an integer or a string convertible to an integer"
        ) from e

    # inp_nr cannot be negative
    if ar_inp <= 0 or ar_inp >= 4000:
        raise ValueError("Roman numerals must be positive integers and below 4000")

    return ar_inp


@app.post("/ar-to-rom/{inp}")
def get_rom_output(inp):
    """
    1. Validate the arabic input
    2. Tries to create a connection to postgres.
    3. Tries to find inp in the postgres-db and immediately return the associated value.
    4. (Optional) If not present, it converts the input, posts the input-output in postgres-db and returns the conversion
    """
    # --- 1. Validate the roman input ---

    val_ar_inp(inp)

    # --- 2. Connect to postgres ---

    conn = get_db_connection()
    cur = conn.cursor()

    # --- 3. Try to find inp in postgres-db

    inp = str(inp).lower().strip()
    db_value = get_value_if_key_exists(cur, inp)
    if db_value:
        print(f"Key {inp} is found in postgres")
        print(f"Roman number: {db_value}")
        return JSONResponse(content={"Roman number": db_value})

    # --- 4. Convert the input, post the input-output in postgres-db and return the conversion

    conv = ar_to_rom_conv(inp)

    post_value_if_key_does_not_exist(conn, cur, inp, conv)

    cur.close()
    conn.close()

    print(f"Roman number: {conv}")
    return JSONResponse(content={"Roman number": conv})


if __name__ == "__main__":
    app()
