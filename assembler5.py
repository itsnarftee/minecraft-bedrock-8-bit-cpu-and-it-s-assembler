# ==============================================================================
# THE ACCOMPLISH - UNIFIED 16-BIT CPU TOOLCHAIN & 10-OPTION IDE SUITE
# ==============================================================================
import os
import sys

OPCODES = {
    "NOP": "0000", "HLT": "0001", "ADD": "0010", "SUB": "0011",
    "NOR": "0100", "AND": "0101", "XOR": "0110", "RSH": "0111",
    "LDI": "1000", "ADI": "1001", "JMP": "1010", "BRH": "1011",
    "CAL": "1100", "RET": "1101", "LOD": "1110", "STR": "1111"
}

REGISTERS = {f"R{i}": format(i, '04b') for i in range(16)}

CONDITIONS = {
    "00": "00", "ZERO": "00", "EQ": "00", "Z": "00", "=": "00",
    "01": "01", "NOTZERO": "01", "NE": "01", "NZ": "01", "!=": "01",
    "10": "10", "CARRY": "10", "CS": "10", "C": "10", "GE": "10", ">=": "10",
    "11": "11", "NOTCARRY": "11", "CC": "11", "NC": "11", "LT": "11", "<": "11"
}

TOP_COORDINATES = {
    0: (-694, 91, 201), 1: (-694, 91, 217), 2: (-694, 91, 233), 3: (-694, 91, 249),
    4: (-694, 91, 265), 5: (-694, 91, 281), 6: (-694, 91, 297), 7: (-694, 91, 313),
    8: (-694, 91, 329), 9: (-694, 91, 345), 10: (-694, 91, 361), 11: (-694, 91, 377),
    12: (-694, 91, 393), 13: (-694, 91, 409), 14: (-694, 91, 425), 15: (-694, 91, 441),
}

for i in range(16, 1024):
    if i not in TOP_COORDINATES:
        TOP_COORDINATES[i] = (-694, 91, 265 + ((i - 5) * 16))

def load_file_content(filename, loaded_files=None, collected_lines=None):
    """Recursively loads file contents, tracking source files and line numbers."""
    if loaded_files is None:
        loaded_files = set()
    if collected_lines is None:
        collected_lines = []
    
    if not filename.endswith(".asm"):
        filename += ".asm"
        
    if filename in loaded_files:
        return collected_lines
    loaded_files.add(filename)
    
    if not os.path.exists(filename):
        raise FileNotFoundError(f"Package/Program file not found: '{filename}'")
        
    with open(filename, "r") as f:
        for line_num, line in enumerate(f, 1):
            stripped = line.strip()
            # Handle Java-like package/program import (e.g., import program_name or include file)
            if stripped.lower().startswith("import ") or stripped.lower().startswith("include "):
                parts = stripped.split()
                if len(parts) > 1:
                    sub_file = parts[1].strip()
                    load_file_content(sub_file, loaded_files, collected_lines)
                    continue
            collected_lines.append((line.rstrip('\r\n'), filename, line_num))
    return collected_lines

def parse_code(source_lines):
    """Parses labels, constant definitions, and instructions with multi-file line tracking."""
    labels = {}
    constants = {}
    cleaned_lines = []
    instruction_counter = 0

    for line_str, filename, line_num in source_lines:
        stripped = line_str.strip()
        
        if not stripped or stripped.startswith(('#', ';', '/')):
            continue
            
        raw_line = stripped.split(';')[0].split('/')[0].split('#')[0].strip()

        if not raw_line:
            continue

        tokens = raw_line.replace(',', '').split()
        if tokens and tokens[0].lower() == "define":
            if len(tokens) >= 3:
                c_name = tokens[1].strip().lower()
                try:
                    c_val = int(tokens[2].strip(), 0)
                    constants[c_name] = c_val
                    continue
                except ValueError:
                    pass

        if '=' in raw_line and not raw_line.startswith('.'):
            parts = raw_line.split('=')
            if len(parts) == 2:
                c_name = parts[0].strip().lower()
                try:
                    c_val = int(parts[1].strip(), 0)
                    constants[c_name] = c_val
                    continue
                except ValueError:
                    pass

        if not tokens:
            continue

        if tokens[0].endswith(':'):
            label_name = tokens[0][:-1].lower()
            labels[label_name] = instruction_counter
            tokens = tokens[1:]
            if not tokens:
                continue
        elif tokens[0].startswith('.'):
            label_name = tokens[0].lower()
            labels[label_name] = instruction_counter
            tokens = tokens[1:]
            if not tokens:
                continue

        cleaned_lines.append((instruction_counter, tokens, line_num, filename))
        instruction_counter += 1

    return labels, constants, cleaned_lines

def resolve_value(token, labels, constants):
    token_lower = str(token).lower()
    if token_lower in labels:
        return labels[token_lower]
    if token_lower in constants:
        return constants[token_lower]
    try:
        return int(token, 0)
    except ValueError:
        raise ValueError(f"Unable to resolve symbol or value: '{token}'")

def assemble_line(tokens, labels, constants):
    if not tokens:
        return None
    
    mnemonic = tokens[0].upper()
    
    # Macro Expansions & Enhancements
    if mnemonic == "INC":
        reg = tokens[1]
        add_val = resolve_value(tokens[2], labels, constants) if len(tokens) > 2 else 1
        mnemonic = "ADI"
        tokens = ["ADI", reg, str(add_val & 0xFF)]
    elif mnemonic == "DEC":
        reg = tokens[1]
        sub_val = resolve_value(tokens[2], labels, constants) if len(tokens) > 2 else 1
        two_complement_val = (256 - sub_val) & 0xFF
        mnemonic = "ADI"
        tokens = ["ADI", reg, str(two_complement_val)]
    elif mnemonic in ["COP", "MOV"]:
        reg_src = tokens[1]
        reg_dest = tokens[2]
        mnemonic = "ADD"
        tokens = ["ADD", reg_src, "R0", reg_dest]
    elif mnemonic == "CMP":
        mnemonic = "SUB"
        tokens = ["SUB", tokens[1], tokens[2], "R0"]

    opcode = OPCODES.get(mnemonic)
    if not opcode:
        raise ValueError(f"Unknown mnemonic: '{mnemonic}'")

    if mnemonic in ["NOP", "HLT", "RET"]:
        binary = opcode + "0" * 12
    elif mnemonic in ["ADD", "SUB", "NOR", "AND", "XOR"]:
        reg_a = REGISTERS.get(tokens[1].upper())
        reg_b = REGISTERS.get(tokens[2].upper())
        reg_c = REGISTERS.get(tokens[3].upper())
        if not reg_a or not reg_b or not reg_c:
            raise ValueError(f"Invalid register in instruction: {' '.join(tokens)}")
        binary = opcode + reg_a + reg_b + reg_c
    elif mnemonic == "RSH":
        reg_a = REGISTERS.get(tokens[1].upper())
        reg_c = REGISTERS.get(tokens[2].upper())
        if not reg_a or not reg_c:
            raise ValueError(f"Invalid register in RSH")
        binary = opcode + reg_c + "0000" + reg_a
    elif mnemonic in ["LDI", "ADI"]:
        reg_a = REGISTERS.get(tokens[1].upper())
        if not reg_a:
            raise ValueError(f"Invalid register in immediate instruction")
        imm_val = resolve_value(tokens[2], labels, constants)
        imm = format(imm_val & 0xFF, '08b')
        binary = opcode + reg_a + imm
    elif mnemonic in ["LOD", "STR"]:
        reg_a = REGISTERS.get(tokens[1].upper())
        reg_b = REGISTERS.get(tokens[2].upper())
        if not reg_a or not reg_b:
            raise ValueError(f"Invalid register in memory instruction")
        offset_val = resolve_value(tokens[3], labels, constants) if len(tokens) > 3 else 0
        offset = format(offset_val & 0x0F, '04b')
        binary = opcode + reg_a + reg_b + offset
    elif mnemonic == "BRH":
        cond = CONDITIONS.get(tokens[1].upper(), "00")
        target_addr = resolve_value(tokens[2], labels, constants)
        addr = format(target_addr & 0x3FF, '010b')
        binary = opcode + cond + addr
    elif mnemonic in ["JMP", "CAL"]:
        target_addr = resolve_value(tokens[1], labels, constants)
        addr = format(target_addr & 0x3FF, '010b')
        binary = opcode + "00" + addr
    else:
        binary = "0" * 16
        
    return binary

def check_syntax(source_lines):
    print("\n==================================================")
    print("   LINTER & SYNTAX CHECKER")
    print("==================================================")
    errors = 0
    try:
        labels, constants, cleaned_lines = parse_code(source_lines)
        print(f"✅ Found {len(constants)} constant definition(s) and {len(labels)} label(s).")
    except Exception as e:
        print(f"❌ Parse/Constant Error: {e}")
        return 1

    for instruction_idx, tokens, line_num, filename in cleaned_lines:
        mnemonic = tokens[0].upper()
        valid_mnemonics = set(OPCODES.keys()).union({"INC", "DEC", "COP", "MOV", "CMP"})
        if mnemonic not in valid_mnemonics:
            print(f"❌ [Linter Error] {filename} (Line {line_num}): Unknown mnemonic '{mnemonic}'")
            errors += 1
            
    if errors == 0:
        print("✅ [Linter] Syntax check passed cleanly.")
    else:
        print(f"\n⚠️ [Linter] Found {errors} syntax error(s).")
    print("==================================================\n")
    return errors

def compile_code(filename):
    try:
        full_lines = load_file_content(filename)
    except Exception as e:
        print(f"\n[IMPORT ERROR]: {e}")
        return

    labels, constants, cleaned_lines = parse_code(full_lines)
    mc_commands = []
    binary_dump = []

    for instruction_idx, tokens, line_num, filename_src in cleaned_lines:
        binary = assemble_line(tokens, labels, constants)
        binary_dump.append(binary)
            
        if instruction_idx not in TOP_COORDINATES:
            raise IndexError(f"No coordinate mapping defined for instruction index {instruction_idx}.")
            
        top_x, top_y, top_z = TOP_COORDINATES[instruction_idx]
        original_text = " ".join(tokens)
        mc_commands.append(f"# Line {instruction_idx}: {original_text} ({binary}) [{filename_src}:{line_num}]")
        
        for bit_idx, bit in enumerate(binary):
            target_y = top_y - (bit_idx * 2)
            if bit == '1':
                cmd = f'setblock {top_x} {target_y} {top_z} unpowered_repeater ["minecraft:cardinal_direction":"north"]'
            else:
                cmd = f'setblock {top_x} {target_y} {top_z} air'
            mc_commands.append(cmd)

    base_name = os.path.splitext(filename)[0]
    
    asm_filename = f"{base_name}.asm"
    bin_filename = f"{base_name}.bin"
    with open(bin_filename, "w") as f:
        f.write("\n".join(binary_dump))

    mc_filename = f"{base_name}.mcfunction"
    with open(mc_filename, "w") as f:
        f.write("\n".join(mc_commands))

    map_filename = f"{base_name}.map"
    with open(map_filename, "w") as f:
        f.write("=== CONSTANTS ===\n")
        for c_name, c_val in constants.items():
            f.write(f"{c_name} = {c_val}\n")
        f.write("\n=== LABELS (Instruction Addresses) ===\n")
        for l_name, l_addr in labels.items():
            f.write(f"{l_name} : {l_addr} (Z-Coord Index)\n")

    print(f"\n[SUCCESS] Compiled {len(cleaned_lines)} instructions:")
    print(f"   • Source File          -> '{asm_filename}'")
    print(f"   • Binary Dump File     -> '{bin_filename}'")
    print(f"   • Bedrock Command File -> '{mc_filename}'")
    print(f"   • Symbol Map File      -> '{map_filename}'")

def open_integrated_editor(filename):
    if os.path.exists(filename):
        with open(filename, "r") as f:
            lines = f.read().splitlines()
    else:
        lines = []

    while True:
        os.system('clear' if os.name == 'posix' else 'cls')
        print("==================================================")
        print(f"   BUILT-IN CODE EDITOR: {filename}")
        print("==================================================")
        if not lines:
            print("   [File is currently empty]")
        else:
            for idx, line in enumerate(lines):
                print(f" {idx:3d} | {line}")
        print("--------------------------------------------------")
        print(" Editor Commands:")
        print("   [A]ppend line       [E]dit line number")
        print("   [I]nsert line       [D]elete line number")
        print("   [W]rite block       [S]ave & Exit")
        print("   [Q]uit without saving")
        print("==================================================")
        
        choice = input("Editor Command > ").strip().upper()

        if choice == 'A':
            new_l = input("Enter instruction to append: ")
            lines.append(new_l)
        elif choice == 'E':
            try:
                idx = int(input("Enter line number to edit: "))
                if 0 <= idx < len(lines):
                    print(f"Current: {lines[idx]}")
                    lines[idx] = input("New text: ")
                else:
                    print("Invalid line number!")
                    input("Press Enter...")
            except ValueError:
                pass
        elif choice == 'I':
            try:
                idx = int(input("Enter line number to insert before: "))
                if 0 <= idx <= len(lines):
                    new_l = input("Enter instruction: ")
                    lines.insert(idx, new_l)
                else:
                    print("Invalid index!")
                    input("Press Enter...")
            except ValueError:
                pass
        elif choice == 'D':
            try:
                idx = int(input("Enter line number to delete: "))
                if 0 <= idx < len(lines):
                    removed = lines.pop(idx)
                    print(f"Deleted: {removed}")
                    input("Press Enter...")
                else:
                    print("Invalid line number!")
                    input("Press Enter...")
            except ValueError:
                pass
        elif choice == 'W':
            print("\n--- Paste your complete multi-line block below ---")
            print("Type 'END' on a brand new line when finished:\n")
            buffer = []
            while True:
                line = input()
                if line.strip() == "END":
                    break
                buffer.append(line)
            lines = buffer
            print("[Success] Code buffer replaced.")
            input("Press Enter...")
        elif choice == 'S':
            with open(filename, "w") as f:
                f.write("\n".join(lines) + "\n")
            print(f"[Success] Saved {filename}!")
            input("Press Enter...")
            break
        elif choice == 'Q':
            confirm = input("Discard changes? (y/n): ").strip().lower()
            if confirm == 'y':
                break

def view_file_content(filename, title):
    os.system('clear' if os.name == 'posix' else 'cls')
    print("==================================================")
    print(f"   {title}: {filename}")
    print("==================================================")
    if os.path.exists(filename):
        with open(filename, "r") as f:
            content = f.read()
        print(content if content else "[File is empty]")
    else:
        print("[Error] File does not exist yet. Compile or edit first.")
    print("==================================================")
    input("Press Enter to continue...")

def main():
    current_file = "program.asm"
    if len(sys.argv) > 1:
        current_file = sys.argv[1]
        if not current_file.endswith(".asm"):
            current_file += ".asm"

    while True:
        os.system('clear' if os.name == 'posix' else 'cls')
        print("==================================================")
        print("   THE ACCOMPLISH - 10-OPTION TOOLCHAIN IDE")
        print("==================================================")
        print(f" Workspace File: {current_file}")
        print("--------------------------------------------------")
        print(" 1. Open Built-In Line Editor (Append, Edit, Insert, Delete)")
        print(" 2. Write / Replace Multi-Line Code Block")
        print(" 3. View Current Source Code (.asm)")
        print(" 4. Run Syntax Linter & Symbol Check")
        print(" 5. Compile to .asm, .bin & .mcfunction")
        print(" 6. View Generated Binary Dump (.bin)")
        print(" 7. View Generated Bedrock Commands (.mcfunction)")
        print(" 8. Switch / Create New .asm File")
        print(" 9. View Instruction & Opcode Reference")
        print("10. Exit Toolchain")
        print("==================================================")
        
        choice = input("Select option (1-10) > ").strip()

        if choice == '1':
            open_integrated_editor(current_file)
        elif choice == '2':
            open_integrated_editor(current_file)
        elif choice == '3':
            view_file_content(current_file, "SOURCE CODE VIEW")
        elif choice == '4':
            if os.path.exists(current_file):
                try:
                    full_lines = load_file_content(current_file)
                    check_syntax(full_lines)
                except Exception as e:
                    print(f"[Error]: {e}")
            else:
                print("[Error] File not found.")
            input("Press Enter to continue...")
        elif choice == '5':
            if not os.path.exists(current_file):
                print(f"[Error] File '{current_file}' does not exist.")
                input("Press Enter to continue...")
                continue
            try:
                full_lines = load_file_content(current_file)
                if check_syntax(full_lines) == 0:
                    compile_code(current_file)
            except Exception as e:
                print(f"\n[BUILD ERROR]: {e}")
            input("Press Enter to continue...")
        elif choice == '6':
            base_name = os.path.splitext(current_file)[0]
            view_file_content(f"{base_name}.bin", "BINARY DUMP VIEW")
        elif choice == '7':
            base_name = os.path.splitext(current_file)[0]
            view_file_content(f"{base_name}.mcfunction", "BEDROCK COMMAND VIEW")
        elif choice == '8':
            new_f = input("Enter new .asm filename: ").strip()
            if new_f:
                if not new_f.endswith(".asm"):
                    new_f += ".asm"
                current_file = new_f
        elif choice == '9':
            os.system('clear' if os.name == 'posix' else 'cls')
            print("==================================================")
            print("   QUICK REFERENCE: THE ACCOMPLISH ISA")
            print("==================================================")
            print(" Opcodes: NOP, HLT, ADD, SUB, NOR, AND, XOR, RSH")
            print("          LDI, ADI, JMP, BRH, CAL, RET, LOD, STR")
            print(" Macros:  MOV / COP src dest (-> ADD src R0 dest)")
            print("          CMP ra rb          (-> SUB ra rb R0)")
            print("          INC / DEC          (-> ADI / Sub immediate)")
            print(" Syntax:  LABEL: or .label")
            print("          define name value OR name = value")
            print("          / or ; or # for comments")
            print("          import filename / include filename")
            print("==================================================")
            input("Press Enter to continue...")
        elif choice == '10':
            print("\nExiting Toolchain IDE. Happy building!")
            break

if __name__ == "__main__":
    main()
