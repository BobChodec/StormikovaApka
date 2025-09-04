import re
import sys

def add_logging_to_plsql(input_file, output_file):
    with open(input_file, "r", encoding="utf-8") as f:
        code = f.read()

    lines = code.splitlines()
    new_lines = []
    inside_block = False
    block_name = ""
    block_type = ""

    for line in lines:
        stripped = line.strip()

        # Procedura / Funkce
        if re.match(r"(?i)CREATE OR REPLACE (PROCEDURE|FUNCTION)", stripped):
            match = re.search(r"(?i)(PROCEDURE|FUNCTION)\s+(\w+)", stripped)
            if match:
                block_type = match.group(1).upper()
                block_name = match.group(2)
                inside_block = True
            new_lines.append(line)
            continue

        # Trigger
        if re.match(r"(?i)CREATE OR REPLACE TRIGGER", stripped):
            match = re.search(r"(?i)TRIGGER\s+(\w+)", stripped)
            if match:
                block_type = "TRIGGER"
                block_name = match.group(1)
                inside_block = True
            new_lines.append(line)
            continue

        # View (nelze logovat přímo)
        if re.match(r"(?i)CREATE OR REPLACE VIEW", stripped):
            match = re.search(r"(?i)VIEW\s+(\w+)", stripped)
            if match:
                view_name = match.group(1)
                # Přidám jen komentář
                new_lines.append(f"-- LOG: definice VIEW {view_name}")
            new_lines.append(line)
            continue

        # Začátek těla
        if inside_block and re.match(r"(?i)^BEGIN", stripped):
            new_lines.append(line)
            new_lines.append(f"   dbms_output.put_line('>>> START {block_type} {block_name}');")
            continue

        # SQL příkazy
        if re.match(r"(?i)^\s*(SELECT|INSERT|UPDATE|DELETE)", stripped):
            new_lines.append(line)
            cmd = stripped.split()[0].upper()
            new_lines.append(f"   dbms_output.put_line('Provádím {cmd}');")
            continue

        # IF/ELSE větve
        if re.match(r"(?i)^\s*IF ", stripped):
            new_lines.append(line)
            new_lines.append("   dbms_output.put_line('Vstup do IF větve');")
            continue
        if re.match(r"(?i)^\s*ELSIF ", stripped):
            new_lines.append(line)
            new_lines.append("   dbms_output.put_line('Kontrola ELSIF větve');")
            continue
        if re.match(r"(?i)^\s*ELSE", stripped):
            new_lines.append(line)
            new_lines.append("   dbms_output.put_line('Vstup do ELSE větve');")
            continue

        # Exception blok
        if re.match(r"(?i)^\s*EXCEPTION", stripped):
            new_lines.append(line)
            new_lines.append("   dbms_output.put_line('>>> EXCEPTION BLOCK');")
            continue

        # Konec bloku
        if inside_block and re.match(r"(?i)^END", stripped):
            new_lines.append(f"   dbms_output.put_line('<<< END {block_type} {block_name}');")
            new_lines.append(line)
            inside_block = False
            block_name = ""
            block_type = ""
            continue

        # Normální řádky
        new_lines.append(line)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(new_lines))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Použití: python plsql_logger.py vstup.txt vystup.txt")
    else:
        add_logging_to_plsql(sys.argv[1], sys.argv[2])