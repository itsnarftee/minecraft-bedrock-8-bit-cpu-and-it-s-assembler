# 8-Bit Vanilla Redstone CPU & Custom Python CLI Assembler (Minecraft Bedrock 1.26.30+)

A **100% pure vanilla Redstone 8-bit CPU** built in **Minecraft Bedrock Edition 1.26.30+**, paired with a fast, lightweight **Python CLI Assembler** and a custom **Connecter Behavior Pack** to load compiled programs directly into instruction memory.

## CPU Hardware Specifications
- **Platform:** Minecraft Bedrock Edition **1.26.30+** (Pure Vanilla Redstone — no command blocks used for CPU logic)
- **Architecture:** 8-Bit Custom ISA
- **Registers:** 15 General-Purpose Registers
- **Instruction Memory (ROM):** 1024 Words
- **Data Memory (RAM):** 255 Bytes
- **Instruction Set:** 16 Custom Instructions

## Releases & How They Work Together
Download all 3 components from the [Releases Page](https://github.com):

1. **`assembler` (`assembler5.py`)** — A fast Python CLI tool where you write and compile custom assembly code into **4 output files**:
   - **`.asm`** — Source assembly code
   - **`.bin`** — Compiled binary machine code
   - **`.map`** — Label and memory address map
   - **`.mcfunction`** — Auto-generated function file used to load the program into the CPU
2. **`world_file` (8-Bit CPU World)** — The Minecraft Bedrock **1.26.30+** world containing the full vanilla Redstone processor.
3. **`Connecter` (Bridge Mod — Bedrock 1.26.30+)** — Drop your generated `.mcfunction` file into this pack's `functions` folder, activate it on the world, and run the function in-game to flash and execute your program on the CPU.

## Video Demonstrations
Watch the Redstone components (Program Counter, 4-Bit Ripple Carry Adder, and CPU builds) on YouTube: [@Narftee](https://youtube.com)
