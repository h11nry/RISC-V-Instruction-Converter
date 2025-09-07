import customtkinter as ctk
import re
import os
import tkinter.font as tkfont
import pandas as pd
import csv

def dec_to_bin(value, bits):
    """Convert decimal to binary string with specified bit length."""
    try:
        value = int(value)
        if value < 0:
            raise ValueError("Negative values are not supported")
        bin_str = bin(value)[2:].zfill(bits)
        if len(bin_str) > bits:
            raise ValueError(f"Value {value} exceeds {bits}-bit limit")
        return bin_str
    except ValueError as e:
        raise ValueError(f"Invalid input for decimal to binary conversion: {e}")

def validate_binary(field, bits, name):
    """Validate binary string input for funct3, funct7, or opcode."""
    if not isinstance(field, str) or not re.match(r'^[01]{' + str(bits) + r'}$', field):
        raise ValueError(f"{name} must be a {bits}-bit binary string")
    return field

def bin_to_hex(bin_str):
    """Convert 32-bit binary string to 8-digit hexadecimal."""
    if len(bin_str) != 32:
        raise ValueError("Binary string must be 32 bits")
    return f"0x{int(bin_str, 2):08x}"

def r_type(funct7, rs2, rs1, funct3, rd, opcode):
    """Generate R-type instruction."""
    return (
        validate_binary(funct7, 7, "funct7") +
        dec_to_bin(rs2, 5) +
        dec_to_bin(rs1, 5) +
        validate_binary(funct3, 3, "funct3") +
        dec_to_bin(rd, 5) +
        validate_binary(opcode, 7, "opcode")
    )

def i_type(imm, rs1, funct3, rd, opcode):
    """Generate I-type instruction."""
    return (
        dec_to_bin(imm, 12) +
        dec_to_bin(rs1, 5) +
        validate_binary(funct3, 3, "funct3") +
        dec_to_bin(rd, 5) +
        validate_binary(opcode, 7, "opcode")
    )

def s_type(imm, rs2, rs1, funct3, opcode):
    """Generate S-type instruction."""
    imm_bin = dec_to_bin(imm, 12)
    return (
        imm_bin[0:7] +
        dec_to_bin(rs2, 5) +
        dec_to_bin(rs1, 5) +
        validate_binary(funct3, 3, "funct3") +
        imm_bin[7:12] +
        validate_binary(opcode, 7, "opcode")
    )

def sb_type(imm, rs2, rs1, funct3, opcode):
    """Generate SB-type instruction."""
    imm_bin = dec_to_bin(imm, 13)
    return (
        imm_bin[0] +
        imm_bin[2:8] +
        dec_to_bin(rs2, 5) +
        dec_to_bin(rs1, 5) +
        validate_binary(funct3, 3, "funct3") +
        imm_bin[8:12] +
        imm_bin[1] +
        validate_binary(opcode, 7, "opcode")
    )

def u_type(imm, rd, opcode):
    """Generate U-type instruction."""
    return (
        dec_to_bin(imm, 20) +
        dec_to_bin(rd, 5) +
        validate_binary(opcode, 7, "opcode")
    )

def uj_type(imm, rd, opcode):
    """Generate UJ-type instruction."""
    imm_bin = dec_to_bin(imm, 21)
    return (
        imm_bin[0] +
        imm_bin[10:20] +
        imm_bin[9] +
        imm_bin[1:9] +
        dec_to_bin(rd, 5) +
        validate_binary(opcode, 7, "opcode")
    )

def process_instruction(instruction_type, fields):
    """Process RISC-V instruction based on type and fields."""
    try:
        if instruction_type.lower() == "r":
            bin_instruction = r_type(*fields)
        elif instruction_type.lower() == "i":
            bin_instruction = i_type(*fields)
        elif instruction_type.lower() == "s":
            bin_instruction = s_type(*fields)
        elif instruction_type.lower() == "sb":
            bin_instruction = sb_type(*fields)
        elif instruction_type.lower() == "u":
            bin_instruction = u_type(*fields)
        elif instruction_type.lower() == "uj":
            bin_instruction = uj_type(*fields)
        else:
            raise ValueError("Unsupported instruction type")
        hex_instruction = bin_to_hex(bin_instruction)
        return bin_instruction, hex_instruction
    except ValueError as e:
        return None, f"Error: {str(e)}"

class RISCVConverterGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("RISC-V Instruction Converter")
        self.root.geometry("1100x800")
        # self.root.resizable(True, True)
        ctk.set_appearance_mode("light")
        
        # Font configuration
        self.font_family = "JetBrains Mono" if "JetBrains Mono" in tkfont.families() else "Courier"
        self.label_font = (self.font_family, 14, "bold")
        self.entry_font = (self.font_family, 14)
        self.button_font = (self.font_family, 14, "bold")
        self.hint_font = (self.font_family, 12)
        self.output_font = (self.font_family, 16)
        
        # Language configuration
        self.language_var = ctk.StringVar(value="en")
        self.translations = {
            "en": {
                "settings": "Settings:",
                "dark_mode": "Dark Mode",
                # "resizable_window": "Resizable Window",
                "auto_save": "Auto Save Results",
                "save_format": "Save Format:",
                # "full_screen": "Full Screen",
                "language": "Chinese (ZH)",
                "help": "Help",
                "clear": "Clear",
                "instruction_type": "Instruction Type:",
                "specific_instruction": "Specific Instruction:",
                "select_instruction": "Select Instruction",
                "funct7": "funct7:",
                "funct3": "funct3:",
                "opcode": "opcode:",
                "rd": "rd:",
                "rs1": "rs1:",
                "rs2": "rs2:",
                "imm": "imm:",
                "funct7_hint": "7-bit binary (e.g., 0000000)",
                "funct3_hint": "3-bit binary (e.g., 000)",
                "opcode_hint": "7-bit binary (e.g., 0010011)",
                "rd_hint": "decimal (0-31)",
                "rs1_hint": "decimal (0-31)",
                "rs2_hint": "decimal (0-31)",
                "imm_hint": "decimal (depends on type)",
                "convert": "Convert",
                "binary_label": "Binary (32-bit):",
                "hex_label": "Hex (8-digit):",
                "help_title": "Help",
                "help_text": (
                    "RISC-V Instruction Converter Help\n\n"
                    "1. Select an instruction type (R, I, S, SB, U, UJ).\n"
                    "\n"
                    "2. Select a specific instruction from the dropdown (auto-fills opcode, funct3, funct7 if applicable).\n"
                    "\n"
                    "3. Enter remaining fields:\n"
                    "   - funct3, funct7, opcode: Binary strings (e.g., 000, 0000000, 0010011).\n"
                    "   - rd, rs1, rs2, imm: Decimal numbers (e.g., 10, 5, 88).\n"
                    "\n"
                    "4. Click 'Convert' to see 32-bit binary and 8-digit hex output.\n"
                    "\n"
                    "5. Settings:\n"
                    "   - Dark Mode: Toggle light/dark theme.\n"
                    # "   - Resizable Window: Enable/disable window resizing.\n"
                    "   - Auto Save Results: Open to automatically record conversion results.\n"
                    # "   - Full Screen: Toggle full screen mode.\n"
                    "   - Clear: Reset all input fields.\n"
                    "\n"
                    "6. Auto Save Details:\n"
                    "   - Auto Save Results feature, when enabled, will automatically save conversion results to a specified file.\n"
                    "   - Users can choose to save in either xlsx or csv format from the main interface.\n"
                    "   - The save path will be the current script directory, with the filename as result.xlsx or result.csv.\n"
                    "\n"
                    "7. Note: Changing instruction type clears all fields to prevent data misalignment.\n"
                ),
                "close": "Close",
                "error_title": "Error",
                "info_title": "Info",
                "save_message": "Results saved to file"
            },
            "zh": {
                "settings": "设置:",
                "dark_mode": "暗黑模式",
                # "resizable_window": "可调整窗口大小",
                "auto_save": "自动保存结果",
                "save_format": "保存格式:",
                # "full_screen": "全屏模式",
                "language": "英文 (EN)",
                "help": "帮助",
                "clear": "清空",
                "instruction_type": "指令类型:",
                "specific_instruction": "具体指令:",
                "select_instruction": "选择指令",
                "funct7": "funct7:",
                "funct3": "funct3:",
                "opcode": "opcode:",
                "rd": "rd:",
                "rs1": "rs1:",
                "rs2": "rs2:",
                "imm": "imm:",
                "funct7_hint": "7位二进制(例如 0000000)",
                "funct3_hint": "3位二进制(例如 000)",
                "opcode_hint": "7位二进制(例如 0010011)",
                "rd_hint": "十进制(0-31)",
                "rs1_hint": "十进制(0-31)",
                "rs2_hint": "十进制(0-31)",
                "imm_hint": "十进制(取决于指令类型)",
                "convert": "转换",
                "binary_label": "二进制(32位):",
                "hex_label": "十六进制(8位):",
                "help_title": "帮助",
                "help_text": (
                    "RISC-V指令转换器帮助\n\n"
                    "1. 选择指令类型(R、I、S、SB、U、UJ)。\n"
                    "\n"
                    "2. 从下拉菜单选择具体指令,包含自动填充。\n"
                    "\n"
                    "3. 输入剩余字段:\n"
                    "   - funct3、funct7、opcode:二进制字符串(例如 000、0000000、0010011)。\n"
                    "   - rd、rs1、rs2、imm:十进制数字(例如 10、5、88)。\n"
                    "\n"
                    "4. 点击“转换”查看32位二进制和8位十六进制输出。\n"
                    "\n"
                    "5. 设置:\n"
                    "   - 暗黑模式:切换明亮/暗黑主题。\n"
                    # "   - 可调整窗口大小:启用/禁用窗口大小调整。\n"
                    "   - 自动保存结果:打开后可自动记录转换结果。\n"
                    # "   - 全屏模式:切换全屏模式。\n"
                    "   - 清空:重置所有输入字段。\n"
                    "\n"
                    "6. 自动保存细则：\n"
                    "   - 自动保存结果功能开启后,每次转换结果都会保存到指定文件中。\n"
                    "   - 用户可在主页选择以xlsx格式存入或是csv格式存入。\n"
                    "   - 保存路径为当前脚本所在目录,文件名为result.所选格式\n"
                    "\n"
                    "7. 注意:更改指令类型会清空所有字段,以防止数据错位。\n"
                ),
                "close": "关闭",
                "error_title": "错误",
                "info_title": "信息",
                "save_message": "结果已保存到文件"
            }
        }
        
        # Store widgets for language updates
        self.widgets = {}
        
        # Save format variable
        self.save_format_var = ctk.StringVar(value="csv")
        
        # Instructions dictionary (RV32I base instruction set) with added structure and descriptions
        self.instructions = {
            "R": {
                "ADD": {
                    "funct7": "0000000", "funct3": "000", "opcode": "0110011",
                    "structure": "rd, rs1, rs2",
                    "description_en": "ADD: Adds the values in rs1 and rs2, stores the result in rd.",
                    "description_zh": "ADD:将 rs1 和 rs2 中的值相加,结果存入 rd。"
                },
                "SUB": {
                    "funct7": "0100000", "funct3": "000", "opcode": "0110011",
                    "structure": "rd, rs1, rs2",
                    "description_en": "SUB: Subtracts rs2 from rs1, stores the result in rd.",
                    "description_zh": "SUB:从 rs1 中减去 rs2,结果存入 rd。"
                },
                "SLL": {
                    "funct7": "0000000", "funct3": "001", "opcode": "0110011",
                    "structure": "rd, rs1, rs2",
                    "description_en": "SLL: Logical left shift on rs1 by rs2 bits, stores in rd.",
                    "description_zh": "SLL:将 rs1 逻辑左移 rs2 位,结果存入 rd。"
                },
                "SLT": {
                    "funct7": "0000000", "funct3": "010", "opcode": "0110011",
                    "structure": "rd, rs1, rs2",
                    "description_en": "SLT: Sets rd to 1 if rs1 < rs2 (signed), else 0.",
                    "description_zh": "SLT:如果 rs1 < rs2(有符号),将 rd 设为 1,否则为 0。"
                },
                "SLTU": {
                    "funct7": "0000000", "funct3": "011", "opcode": "0110011",
                    "structure": "rd, rs1, rs2",
                    "description_en": "SLTU: Sets rd to 1 if rs1 < rs2 (unsigned), else 0.",
                    "description_zh": "SLTU:如果 rs1 < rs2(无符号),将 rd 设为 1,否则为 0。"
                },
                "XOR": {
                    "funct7": "0000000", "funct3": "100", "opcode": "0110011",
                    "structure": "rd, rs1, rs2",
                    "description_en": "XOR: Bitwise XOR of rs1 and rs2, stores in rd.",
                    "description_zh": "XOR:rs1 和 rs2 的按位异或,结果存入 rd。"
                },
                "SRL": {
                    "funct7": "0000000", "funct3": "101", "opcode": "0110011",
                    "structure": "rd, rs1, rs2",
                    "description_en": "SRL: Logical right shift on rs1 by rs2 bits, stores in rd.",
                    "description_zh": "SRL:将 rs1 逻辑右移 rs2 位,结果存入 rd。"
                },
                "SRA": {
                    "funct7": "0100000", "funct3": "101", "opcode": "0110011",
                    "structure": "rd, rs1, rs2",
                    "description_en": "SRA: Arithmetic right shift on rs1 by rs2 bits, stores in rd.",
                    "description_zh": "SRA:将 rs1 算术右移 rs2 位,结果存入 rd。"
                },
                "OR": {
                    "funct7": "0000000", "funct3": "110", "opcode": "0110011",
                    "structure": "rd, rs1, rs2",
                    "description_en": "OR: Bitwise OR of rs1 and rs2, stores in rd.",
                    "description_zh": "OR:rs1 和 rs2 的按位或,结果存入 rd。"
                },
                "AND": {
                    "funct7": "0000000", "funct3": "111", "opcode": "0110011",
                    "structure": "rd, rs1, rs2",
                    "description_en": "AND: Bitwise AND of rs1 and rs2, stores in rd.",
                    "description_zh": "AND:rs1 和 rs2 的按位与,结果存入 rd。"
                },
            },
            "I": {
                "ADDI": {
                    "funct3": "000", "opcode": "0010011",
                    "structure": "rd, rs1, imm",
                    "description_en": "ADDI: Adds immediate to rs1, stores in rd.",
                    "description_zh": "ADDI:将立即数加到 rs1,结果存入 rd。"
                },
                "SLTI": {
                    "funct3": "010", "opcode": "0010011",
                    "structure": "rd, rs1, imm",
                    "description_en": "SLTI: Sets rd to 1 if rs1 < imm (signed), else 0.",
                    "description_zh": "SLTI:如果 rs1 < imm(有符号),将 rd 设为 1,否则为 0。"
                },
                "SLTIU": {
                    "funct3": "011", "opcode": "0010011",
                    "structure": "rd, rs1, imm",
                    "description_en": "SLTIU: Sets rd to 1 if rs1 < imm (unsigned), else 0.",
                    "description_zh": "SLTIU:如果 rs1 < imm(无符号),将 rd 设为 1,否则为 0。"
                },
                "XORI": {
                    "funct3": "100", "opcode": "0010011",
                    "structure": "rd, rs1, imm",
                    "description_en": "XORI: Bitwise XOR of rs1 and imm, stores in rd.",
                    "description_zh": "XORI:rs1 和 imm 的按位异或,结果存入 rd。"
                },
                "ORI": {
                    "funct3": "110", "opcode": "0010011",
                    "structure": "rd, rs1, imm",
                    "description_en": "ORI: Bitwise OR of rs1 and imm, stores in rd.",
                    "description_zh": "ORI:rs1 和 imm 的按位或,结果存入 rd。"
                },
                "ANDI": {
                    "funct3": "111", "opcode": "0010011",
                    "structure": "rd, rs1, imm",
                    "description_en": "ANDI: Bitwise AND of rs1 and imm, stores in rd.",
                    "description_zh": "ANDI:rs1 和 imm 的按位与,结果存入 rd。"
                },
                "SLLI": {
                    "funct7": "0000000", "funct3": "001", "opcode": "0010011",
                    "structure": "rd, rs1, imm",
                    "description_en": "SLLI: Logical left shift on rs1 by imm bits, stores in rd.",
                    "description_zh": "SLLI:将 rs1 逻辑左移 imm 位,结果存入 rd。"
                },
                "SRLI": {
                    "funct7": "0000000", "funct3": "101", "opcode": "0010011",
                    "structure": "rd, rs1, imm",
                    "description_en": "SRLI: Logical right shift on rs1 by imm bits, stores in rd.",
                    "description_zh": "SRLI:将 rs1 逻辑右移 imm 位,结果存入 rd。"
                },
                "SRAI": {
                    "funct7": "0100000", "funct3": "101", "opcode": "0010011",
                    "structure": "rd, rs1, imm",
                    "description_en": "SRAI: Arithmetic right shift on rs1 by imm bits, stores in rd.",
                    "description_zh": "SRAI:将 rs1 算术右移 imm 位,结果存入 rd。"
                },
                "LB": {
                    "funct3": "000", "opcode": "0000011",
                    "structure": "rd, imm(rs1)",
                    "description_en": "LB: Loads a signed byte from memory at rs1 + imm into rd.",
                    "description_zh": "LB:从 rs1 + imm 处的内存加载有符号字节到 rd。"
                },
                "LH": {
                    "funct3": "001", "opcode": "0000011",
                    "structure": "rd, imm(rs1)",
                    "description_en": "LH: Loads a signed halfword from memory at rs1 + imm into rd.",
                    "description_zh": "LH:从 rs1 + imm 处的内存加载有符号半字到 rd。"
                },
                "LW": {
                    "funct3": "010", "opcode": "0000011",
                    "structure": "rd, imm(rs1)",
                    "description_en": "LW: Loads a word from memory at rs1 + imm into rd.",
                    "description_zh": "LW:从 rs1 + imm 处的内存加载字到 rd。"
                },
                "LBU": {
                    "funct3": "100", "opcode": "0000011",
                    "structure": "rd, imm(rs1)",
                    "description_en": "LBU: Loads an unsigned byte from memory at rs1 + imm into rd.",
                    "description_zh": "LBU:从 rs1 + imm 处的内存加载无符号字节到 rd。"
                },
                "LHU": {
                    "funct3": "101", "opcode": "0000011",
                    "structure": "rd, imm(rs1)",
                    "description_en": "LHU: Loads an unsigned halfword from memory at rs1 + imm into rd.",
                    "description_zh": "LHU:从 rs1 + imm 处的内存加载无符号半字到 rd。"
                },
                "FENCE": {
                    "funct3": "000", "opcode": "0001111",
                    "structure": "pred, succ",
                    "description_en": "FENCE: Orders memory accesses.",
                    "description_zh": "FENCE:对内存访问进行排序。"
                },
                "FENCE.I": {
                    "funct3": "001", "opcode": "0001111",
                    "structure": "",
                    "description_en": "FENCE.I: Synchronizes instruction and data streams.",
                    "description_zh": "FENCE.I:同步指令和数据流。"
                },
                "JALR": {
                    "funct3": "000", "opcode": "1100111",
                    "structure": "rd, imm(rs1)",
                    "description_en": "JALR: Jumps to rs1 + imm and stores return address in rd.",
                    "description_zh": "JALR:跳转到 rs1 + imm,并将返回地址存入 rd。"
                },
                "ECALL": {
                    "funct3": "000", "opcode": "1110011", "imm": "0",
                    "structure": "",
                    "description_en": "ECALL: Makes an environment call.",
                    "description_zh": "ECALL:进行环境调用。"
                },
                "EBREAK": {
                    "funct3": "000", "opcode": "1110011", "imm": "1",
                    "structure": "",
                    "description_en": "EBREAK: Causes a breakpoint exception.",
                    "description_zh": "EBREAK:引起断点异常。"
                },
            },
            "S": {
                "SB": {
                    "funct3": "000", "opcode": "0100011",
                    "structure": "rs2, imm(rs1)",
                    "description_en": "SB: Stores a byte from rs2 to memory at rs1 + imm.",
                    "description_zh": "SB:将 rs2 中的字节存入 rs1 + imm 处的内存。"
                },
                "SH": {
                    "funct3": "001", "opcode": "0100011",
                    "structure": "rs2, imm(rs1)",
                    "description_en": "SH: Stores a halfword from rs2 to memory at rs1 + imm.",
                    "description_zh": "SH:将 rs2 中的半字存入 rs1 + imm 处的内存。"
                },
                "SW": {
                    "funct3": "010", "opcode": "0100011",
                    "structure": "rs2, imm(rs1)",
                    "description_en": "SW: Stores a word from rs2 to memory at rs1 + imm.",
                    "description_zh": "SW:将 rs2 中的字存入 rs1 + imm 处的内存。"
                },
            },
            "SB": {
                "BEQ": {
                    "funct3": "000", "opcode": "1100011",
                    "structure": "rs1, rs2, imm",
                    "description_en": "BEQ: Branches if rs1 == rs2 to PC + imm.",
                    "description_zh": "BEQ:如果 rs1 == rs2,则分支到 PC + imm。"
                },
                "BNE": {
                    "funct3": "001", "opcode": "1100011",
                    "structure": "rs1, rs2, imm",
                    "description_en": "BNE: Branches if rs1 != rs2 to PC + imm.",
                    "description_zh": "BNE:如果 rs1 != rs2,则分支到 PC + imm。"
                },
                "BLT": {
                    "funct3": "100", "opcode": "1100011",
                    "structure": "rs1, rs2, imm",
                    "description_en": "BLT: Branches if rs1 < rs2 (signed) to PC + imm.",
                    "description_zh": "BLT:如果 rs1 < rs2(有符号),则分支到 PC + imm。"
                },
                "BGE": {
                    "funct3": "101", "opcode": "1100011",
                    "structure": "rs1, rs2, imm",
                    "description_en": "BGE: Branches if rs1 >= rs2 (signed) to PC + imm.",
                    "description_zh": "BGE:如果 rs1 >= rs2(有符号),则分支到 PC + imm。"
                },
                "BLTU": {
                    "funct3": "110", "opcode": "1100011",
                    "structure": "rs1, rs2, imm",
                    "description_en": "BLTU: Branches if rs1 < rs2 (unsigned) to PC + imm.",
                    "description_zh": "BLTU:如果 rs1 < rs2(无符号),则分支到 PC + imm。"
                },
                "BGEU": {
                    "funct3": "111", "opcode": "1100011",
                    "structure": "rs1, rs2, imm",
                    "description_en": "BGEU: Branches if rs1 >= rs2 (unsigned) to PC + imm.",
                    "description_zh": "BGEU:如果 rs1 >= rs2(无符号),则分支到 PC + imm。"
                },
            },
            "U": {
                "LUI": {
                    "opcode": "0110111",
                    "structure": "rd, imm",
                    "description_en": "LUI: Loads upper immediate into rd (upper 20 bits).",
                    "description_zh": "LUI:将上立即数加载到 rd(上 20 位)。"
                },
                "AUIPC": {
                    "opcode": "0010111",
                    "structure": "rd, imm",
                    "description_en": "AUIPC: Adds upper immediate to PC, stores in rd.",
                    "description_zh": "AUIPC:将上立即数加到 PC,结果存入 rd。"
                },
            },
            "UJ": {
                "JAL": {
                    "opcode": "1101111",
                    "structure": "rd, imm",
                    "description_en": "JAL: Jumps to PC + imm and stores return address in rd.",
                    "description_zh": "JAL:跳转到 PC + imm,并将返回地址存入 rd。"
                },
            }
        }
        
        # Top settings frame
        self.settings_frame = ctk.CTkFrame(root, height=60)
        self.settings_frame.pack(fill="x", pady=10, padx=10)
        
        self.widgets["settings_label"] = ctk.CTkLabel(self.settings_frame, text=self.translations["en"]["settings"], font=self.label_font)
        self.widgets["settings_label"].pack(side="left", padx=5)
        
        # Switch height set to 36 (default ~24)
        self.widgets["theme_switch"] = ctk.CTkSwitch(self.settings_frame, text=self.translations["en"]["dark_mode"], font=self.label_font, command=self.toggle_theme, height=36)
        self.widgets["theme_switch"].pack(side="left", padx=15)
        
        # self.widgets["resizable_switch"] = ctk.CTkSwitch(self.settings_frame, text=self.translations["en"]["resizable_window"], font=self.label_font, command=self.toggle_resizable, state="on", height=36)
        # self.widgets["resizable_switch"].select()
        # self.widgets["resizable_switch"].pack(side="left", padx=15)
        
        self.widgets["save_switch"] = ctk.CTkSwitch(self.settings_frame, text=self.translations["en"]["auto_save"], font=self.label_font, height=36)
        self.widgets["save_switch"].pack(side="left", padx=15)
        
        self.widgets["save_format_label"] = ctk.CTkLabel(self.settings_frame, text=self.translations["en"]["save_format"], font=self.label_font)
        self.widgets["save_format_label"].pack(side="left", padx=5)
        
        self.widgets["save_format_menu"] = ctk.CTkComboBox(self.settings_frame, values=["csv", "excel"], variable=self.save_format_var, width=100, font=self.entry_font, height=40)
        self.widgets["save_format_menu"].pack(side="left", padx=10)
        
        # self.widgets["fullscreen_switch"] = ctk.CTkSwitch(self.settings_frame, text=self.translations["en"]["full_screen"], font=self.label_font, command=self.toggle_fullscreen, height=36)
        # self.widgets["fullscreen_switch"].pack(side="left", padx=15)
        
        self.widgets["language_switch"] = ctk.CTkSwitch(self.settings_frame, text=self.translations["en"]["language"], font=self.label_font, command=self.toggle_language, height=36)
        self.widgets["language_switch"].pack(side="left", padx=15)
        
        # Button height set to 40 (default ~28)
        self.widgets["help_button"] = ctk.CTkButton(self.settings_frame, text=self.translations["en"]["help"], font=self.button_font, command=self.show_help, width=80, height=40)
        self.widgets["help_button"].pack(side="left", padx=15)
        
        self.widgets["clear_button"] = ctk.CTkButton(self.settings_frame, text=self.translations["en"]["clear"], font=self.button_font, command=self.clear_inputs, width=80, height=40)
        self.widgets["clear_button"].pack(side="left", padx=15)
        
        # Main content frame
        self.main_frame = ctk.CTkFrame(root, width=750, height=500)
        self.main_frame.pack_propagate(False)
        self.main_frame.pack(pady=10, padx=10, fill="both", expand=True)
        
        # Instruction type and specific instruction selection frame
        self.selection_frame = ctk.CTkFrame(self.main_frame)
        self.selection_frame.pack(anchor="w", pady=10)
        
        self.widgets["type_label"] = ctk.CTkLabel(self.selection_frame, text=self.translations["en"]["instruction_type"], font=self.label_font)
        self.widgets["type_label"].pack(side="left", padx=5)
        
        # Combobox height set to 40 (default ~28)
        self.type_var = ctk.StringVar(value="R")
        self.widgets["type_menu"] = ctk.CTkComboBox(self.selection_frame, values=["R", "I", "S", "SB", "U", "UJ"], variable=self.type_var, command=self.update_instruction_menu, width=150, font=self.entry_font, height=40)
        self.widgets["type_menu"].pack(side="left", padx=10)
        
        self.widgets["instruction_label"] = ctk.CTkLabel(self.selection_frame, text=self.translations["en"]["specific_instruction"], font=self.label_font)
        self.widgets["instruction_label"].pack(side="left", padx=5)
        
        # Combobox height set to 40 (default ~28)
        self.instruction_var = ctk.StringVar(value=self.translations["en"]["select_instruction"])
        self.widgets["instruction_menu"] = ctk.CTkComboBox(self.selection_frame, variable=self.instruction_var, command=self.fill_fields, width=200, font=self.entry_font, height=40)
        self.widgets["instruction_menu"].pack(side="left", padx=10)
        
        # New: Structure label next to dropdown
        self.structure_label = ctk.CTkLabel(self.selection_frame, text="", font=self.hint_font, text_color="blue")
        self.structure_label.pack(side="left", padx=10)
        
        # New: Description frame below selection
        self.description_frame = ctk.CTkFrame(self.main_frame)
        self.description_frame.pack(anchor="w", pady=5, fill="x")
        
        self.description_label = ctk.CTkLabel(self.description_frame, text="", font=self.hint_font, wraplength=1000, anchor="w", justify="left")
        self.description_label.pack(anchor="w")
        
        # Input fields frame
        self.input_frame = ctk.CTkFrame(self.main_frame)
        self.input_frame.pack(fill="x", pady=10)
        
        self.field_frames = {}
        self.entries = {}
        self.field_names = {
            "R": ["funct7", "rs2", "rs1", "funct3", "rd", "opcode"],
            "I": ["imm", "rs1", "funct3", "rd", "opcode"],
            "S": ["imm", "rs2", "rs1", "funct3", "opcode"],
            "SB": ["imm", "rs2", "rs1", "funct3", "opcode"],
            "U": ["imm", "rd", "opcode"],
            "UJ": ["imm", "rd", "opcode"]
        }
        self.field_hints = {
            "funct7": "funct7_hint",
            "funct3": "funct3_hint",
            "opcode": "opcode_hint",
            "rd": "rd_hint",
            "rs1": "rs1_hint",
            "rs2": "rs2_hint",
            "imm": "imm_hint"
        }
        
        # Create field frames
        max_fields = 6
        for i in range(max_fields):
            field_frame = ctk.CTkFrame(self.input_frame)
            field_frame.pack(fill="x", pady=8)
            self.widgets[f"field_label_{i}"] = ctk.CTkLabel(field_frame, text="", width=120, anchor="w", font=self.label_font)
            self.widgets[f"field_label_{i}"].pack(side="left")
            # Entry height set to 40 (default ~28)
            entry = ctk.CTkEntry(field_frame, width=250, font=self.entry_font, height=40)
            entry.pack(side="left", padx=10)
            self.widgets[f"field_hint_{i}"] = ctk.CTkLabel(field_frame, text="", font=self.hint_font, text_color="black")
            self.widgets[f"field_hint_{i}"].pack(side="left")
            self.field_frames[i] = field_frame
            self.entries[i] = entry
        
        # Convert button
        # Button height set to 40 (default ~28)
        self.widgets["convert_button"] = ctk.CTkButton(self.main_frame, text=self.translations["en"]["convert"], font=self.button_font, command=self.convert, width=200, height=60)
        self.widgets["convert_button"].pack(pady=15)
        
        # Output frame
        self.output_frame = ctk.CTkFrame(self.main_frame)
        self.output_frame.pack(fill="x", pady=10)
        
        self.widgets["binary_label"] = ctk.CTkLabel(self.output_frame, text=self.translations["en"]["binary_label"], font=self.label_font)
        self.widgets["binary_label"].pack(anchor="w")
        self.binary_output = ctk.CTkLabel(self.output_frame, text="", font=self.output_font, wraplength=700, anchor="w")
        self.binary_output.pack(anchor="w", pady=5)
        
        self.widgets["hex_label"] = ctk.CTkLabel(self.output_frame, text=self.translations["en"]["hex_label"], font=self.label_font)
        self.widgets["hex_label"].pack(anchor="w")
        self.hex_output = ctk.CTkLabel(self.output_frame, text="", font=self.output_font, anchor="w")
        self.hex_output.pack(anchor="w", pady=5)
        
        # Initialize fields
        self.update_instruction_menu("R")

    def update_instruction_menu(self, *args):
        """Update specific instruction menu and clear inputs when instruction type changes."""
        self.clear_inputs()
        
        inst_type = self.type_var.get()
        specific_instructions = list(self.instructions.get(inst_type, {}).keys())
        self.widgets["instruction_menu"].configure(values=specific_instructions)
        self.instruction_var.set(self.translations[self.language_var.get()]["select_instruction"])
        self.update_fields()
        self.update_instruction_info()  # Clear structure and description
    
    def fill_fields(self, *args):
        """Fill fields with predefined values for the selected instruction."""
        inst_type = self.type_var.get()
        mnemonic = self.instruction_var.get()
        if mnemonic == self.translations[self.language_var.get()]["select_instruction"] or mnemonic not in self.instructions[inst_type]:
            self.update_instruction_info()  # Clear if no selection
            return
        data = self.instructions[inst_type][mnemonic]
        fields = self.field_names[inst_type]
        for i, field in enumerate(fields):
            if field in data:
                self.entries[i].delete(0, "end")
                self.entries[i].insert(0, data[field])
        self.update_instruction_info()
    
    def update_instruction_info(self):
        """Update structure and description labels based on selected instruction."""
        inst_type = self.type_var.get()
        mnemonic = self.instruction_var.get()
        lang = self.language_var.get()
        if mnemonic == self.translations[lang]["select_instruction"] or mnemonic not in self.instructions[inst_type]:
            self.structure_label.configure(text="")
            self.description_label.configure(text="")
            return
        data = self.instructions[inst_type][mnemonic]
        structure = data.get("structure", "")
        description_key = "description_zh" if lang == "zh" else "description_en"
        description = data.get(description_key, "")
        self.structure_label.configure(text=f"Structure: {mnemonic} {structure}")
        self.description_label.configure(text=description)
    
    def update_fields(self, *args):
        """Update input fields based on instruction type."""
        inst_type = self.type_var.get()
        fields = self.field_names[inst_type]
        lang = self.language_var.get()
        for i in range(6):
            if i < len(fields):
                field_name = fields[i]
                self.widgets[f"field_label_{i}"].configure(text=self.translations[lang][field_name])
                self.widgets[f"field_hint_{i}"].configure(text=self.translations[lang][self.field_hints[field_name]])
                self.entries[i].configure(state="normal")
                self.field_frames[i].pack(fill="x", pady=8)
            else:
                self.field_frames[i].pack_forget()
                self.entries[i].delete(0, "end")
    
    def convert(self):
        """Process the instruction and display results."""
        inst_type = self.type_var.get()
        mnemonic = self.instruction_var.get()
        fields = []
        try:
            for i in range(len(self.field_names[inst_type])):
                value = self.entries[i].get().strip()
                if not value:
                    raise ValueError(f"Field {self.field_names[inst_type][i]} is empty")
                fields.append(value)
            
            bin_result, hex_result = process_instruction(inst_type, fields)
            if bin_result:
                self.binary_output.configure(text=bin_result)
                self.hex_output.configure(text=hex_result)
                if self.widgets["save_switch"].get():
                    self.save_results(inst_type, mnemonic, bin_result, hex_result)
            else:
                self.show_error(hex_result)
        except Exception as e:
            self.show_error(str(e))
    
    def save_results(self, inst_type, mnemonic, bin_result, hex_result):
        """Save results to selected format (csv or excel)."""
        format = self.save_format_var.get()
        file_name = "results." + ("xlsx" if format == "excel" else "csv")
        data = {
            "Instruction Type": inst_type,
            "Specific Instruction": mnemonic,
            "Binary": bin_result,
            "Hex": hex_result
        }
        
        if format == "csv":
            file_exists = os.path.isfile(file_name)
            with open(file_name, "a", newline='') as f:
                writer = csv.DictWriter(f, fieldnames=["Instruction Type", "Specific Instruction", "Binary", "Hex"])
                if not file_exists:
                    writer.writeheader()
                writer.writerow(data)
        elif format == "excel":
            if os.path.isfile(file_name):
                df = pd.read_excel(file_name)
                new_df = pd.DataFrame([data])
                df = pd.concat([df, new_df], ignore_index=True)
            else:
                df = pd.DataFrame([data])
            df.to_excel(file_name, index=False)
        
        self.show_info(self.translations[self.language_var.get()]["save_message"])
    
    def toggle_theme(self):
        """Toggle between light and dark theme."""
        mode = "dark" if self.widgets["theme_switch"].get() else "light"
        ctk.set_appearance_mode(mode)
    
    # def toggle_resizable(self):
    #     """Toggle window resizable state."""
    #     resizable = self.widgets["resizable_switch"].get()
    #     self.root.resizable(resizable, resizable)
    
    # def toggle_fullscreen(self):
    #     """Toggle full screen mode."""
    #     fullscreen = self.widgets["fullscreen_switch"].get()
    #     self.root.attributes("-fullscreen", fullscreen)
    
    def toggle_language(self):
        """Toggle between English and Chinese UI."""
        self.language_var.set("zh" if self.widgets["language_switch"].get() else "en")
        self.update_language()
    
    def update_language(self):
        """Update all UI text based on selected language."""
        lang = self.language_var.get()
        self.widgets["settings_label"].configure(text=self.translations[lang]["settings"])
        self.widgets["theme_switch"].configure(text=self.translations[lang]["dark_mode"])
        # self.widgets["resizable_switch"].configure(text=self.translations[lang]["resizable_window"])
        self.widgets["save_switch"].configure(text=self.translations[lang]["auto_save"])
        self.widgets["save_format_label"].configure(text=self.translations[lang]["save_format"])
        # self.widgets["fullscreen_switch"].configure(text=self.translations[lang]["full_screen"])
        self.widgets["language_switch"].configure(text=self.translations[lang]["language"])
        self.widgets["help_button"].configure(text=self.translations[lang]["help"])
        self.widgets["clear_button"].configure(text=self.translations[lang]["clear"])
        self.widgets["type_label"].configure(text=self.translations[lang]["instruction_type"])
        self.widgets["instruction_label"].configure(text=self.translations[lang]["specific_instruction"])
        self.widgets["convert_button"].configure(text=self.translations[lang]["convert"])
        self.widgets["binary_label"].configure(text=self.translations[lang]["binary_label"])
        self.widgets["hex_label"].configure(text=self.translations[lang]["hex_label"])
        self.instruction_var.set(self.translations[lang]["select_instruction"])
        self.update_fields()
        self.update_instruction_info()  # Update description based on new language
    
    def show_help(self):
        """Show help window with instructions."""
        lang = self.language_var.get()
        help_window = ctk.CTkToplevel(self.root)
        help_window.title(self.translations[lang]["help_title"])
        help_window.geometry("400x600")
        # help_window.resizable(False, False)
        help_window.transient(self.root)
        help_window.grab_set()
        
        ctk.CTkLabel(help_window, text=self.translations[lang]["help_text"], font=self.hint_font, wraplength=360, justify="left").pack(pady=10, padx=10)
        ctk.CTkButton(help_window, text=self.translations[lang]["close"], font=self.button_font, command=help_window.destroy, height=40).pack(pady=10)
    
    def show_error(self, message):
        """Show error message in a dialog."""
        lang = self.language_var.get()
        error_window = ctk.CTkToplevel(self.root)
        error_window.title(self.translations[lang]["error_title"])
        error_window.geometry("300x150")
        # error_window.resizable(False, False)
        error_window.transient(self.root)
        error_window.grab_set()
        
        ctk.CTkLabel(error_window, text=message, font=self.hint_font, wraplength=260).pack(pady=10, padx=10)
        ctk.CTkButton(error_window, text=self.translations[lang]["close"], font=self.button_font, command=error_window.destroy, height=40).pack(pady=10)
    
    def show_info(self, message):
        """Show info message in a dialog."""
        lang = self.language_var.get()
        info_window = ctk.CTkToplevel(self.root)
        info_window.title(self.translations[lang]["info_title"])
        info_window.geometry("300x150")
        # info_window.resizable(False, False)
        info_window.transient(self.root)
        info_window.grab_set()
        
        ctk.CTkLabel(info_window, text=message, font=self.hint_font, wraplength=260).pack(pady=10, padx=10)
        ctk.CTkButton(info_window, text=self.translations[lang]["close"], font=self.button_font, command=info_window.destroy, height=40).pack(pady=10)
    
    def clear_inputs(self):
        """Clear all input fields, outputs, and reset instruction dropdown."""
        for entry in self.entries.values():
            entry.delete(0, "end")
        self.binary_output.configure(text="")
        self.hex_output.configure(text="")
        self.instruction_var.set(self.translations[self.language_var.get()]["select_instruction"])
        self.update_instruction_info()  # Clear structure and description

if __name__ == "__main__":
    root = ctk.CTk()
    app = RISCVConverterGUI(root)
    root.mainloop()