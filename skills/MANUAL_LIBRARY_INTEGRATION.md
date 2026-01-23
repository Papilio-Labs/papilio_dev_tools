# Manual Library Integration Skill

## Purpose

This skill documents how to manually integrate Papilio Wishbone libraries into projects based on the `papilio_project_template`. Use this when the automatic library builder is disabled (`board_build.papilio_auto_builder = 0`) or when you need to understand the integration patterns.

**Note**: The Papilio Automatic Library Builder (when `board_build.papilio_auto_builder = 1`) performs these steps automatically. This skill is for:
- Manual integration when auto-builder is disabled
- Understanding what the auto-builder does
- Debugging integration issues
- Creating custom integrations

## Prerequisites

- Project forked/copied from `papilio_project_template`
- Papilio library added to `platformio.ini` under `lib_deps`
- Understanding of Wishbone bus architecture (see `papilio_wishbone_bus` docs)
- Familiarity with Verilog and C++ (for ESP32)

## Library Integration Checklist

When adding a Papilio Wishbone library (e.g., `papilio_wishbone_register`), you must integrate it into **five locations**:

1. ✅ **platformio.ini** - Add library dependency
2. ✅ **FPGA top.v** - Add module instantiation and signals
3. ✅ **FPGA project.gprj** - Add Verilog source files
4. ✅ **FPGA constraints** - Add pin constraints (if library needs external I/O)
5. ✅ **ESP32 main.cpp** - Add includes and initialization

---

## Step-by-Step Integration Guide

### Step 1: Add Library to platformio.ini

**Location**: `platformio.ini` → `[env:esp32]` → `lib_deps`

**Action**: Uncomment or add the library URL

```ini
lib_deps = 
    https://github.com/Papilio-Labs/papilio_spi_slave.git
    https://github.com/Papilio-Labs/papilio_wishbone_bus.git
    https://github.com/Papilio-Labs/papilio_os.git
    ; Add additional Papilio peripheral libraries below:
    https://github.com/Papilio-Labs/papilio_wishbone_register.git  ; ← UNCOMMENTED
    ; https://github.com/Papilio-Labs/papilio_wishbone_rgb_led.git
    ; https://github.com/Papilio-Labs/papilio_wishbone_bram.git
```

**What this does**: PlatformIO will download the library and make it available to both ESP32 and FPGA builds.

**Library metadata**: Each library includes `library.json` with a `papilio` section containing integration details:
- HDL module information
- Wishbone address requirements
- ESP32 class names
- Port templates

---

### Step 2: Integrate into FPGA top.v

**Location**: `fpga/src/top.v`

The template has **four marker regions** where auto-generated code goes:

1. **PAPILIO_AUTO_PORTS_BEGIN/END** - Top-level module ports
2. **PAPILIO_AUTO_WIRES_BEGIN/END** - Internal wire declarations
3. **PAPILIO_AUTO_MODULE_INST_BEGIN/END** - Module instantiations
4. **PAPILIO_AUTO_WISHBONE_BEGIN/END** - Wishbone interconnect logic

#### Step 2a: Add Top-Level Ports (if needed)

**Marker region**: `//# PAPILIO_AUTO_PORTS_BEGIN` → `//# PAPILIO_AUTO_PORTS_END`

**When to add**: Only if the library connects to external hardware (LEDs, buttons, displays, etc.)

**Example**: For `papilio_wishbone_rgb_led`:
```verilog
module top (
    input  wire clk_27mhz,
    input  wire spi_sclk,
    input  wire spi_mosi,
    output wire spi_miso,
    input  wire spi_cs_n
    
    //# PAPILIO_AUTO_PORTS_BEGIN
    // RGB LED outputs
    ,output wire [2:0] rgb_led_r
    ,output wire [2:0] rgb_led_g  
    ,output wire [2:0] rgb_led_b
    //# PAPILIO_AUTO_PORTS_END
);
```

**Note**: Libraries like `papilio_wishbone_register` don't need ports (pure internal logic).

**Port naming convention**: Use library-specific prefixes (e.g., `rgb_led_*`) to avoid conflicts.

#### Step 2b: Add Internal Wires

**Marker region**: `//# PAPILIO_AUTO_WIRES_BEGIN` → `//# PAPILIO_AUTO_WIRES_END`

**What to add**: Wishbone slave signals for each peripheral module

**Example**: For `papilio_wishbone_register` at address `0x1000`:
```verilog
//# PAPILIO_AUTO_WIRES_BEGIN
// Wishbone Register Block signals
wire [7:0]  wb_register_dat_s2m;
wire        wb_register_ack;
wire        wb_register_stb;
//# PAPILIO_AUTO_WIRES_END
```

**Wire naming convention**: Use `<module_name>_<signal>` pattern:
- `wb_register_dat_s2m` - Data from slave to master
- `wb_register_ack` - Acknowledge from slave
- `wb_register_stb` - Strobe to slave (derived from address decode)

**Why these signals**:
- `dat_s2m` - Each slave needs its own data output (multiplexed later)
- `ack` - Each slave needs its own acknowledge (multiplexed later)
- `stb` - Each slave needs address-decoded strobe signal

#### Step 2c: Instantiate Module

**Marker region**: `//# PAPILIO_AUTO_MODULE_INST_BEGIN` → `//# PAPILIO_AUTO_MODULE_INST_END`

**What to add**: Instantiate the library's Verilog module with proper connections

**How to find the template**: Check `library.json` → `papilio.gateware.modules[].template`

**Example**: For `papilio_wishbone_register`:
```verilog
//# PAPILIO_AUTO_MODULE_INST_BEGIN
// Wishbone Register Block (0x1000-0x10FF)
wb_register_block #(
    .ADDR_WIDTH(4),
    .DATA_WIDTH(8),
    .RESET_VALUE(0)
) wb_register_inst (
    .clk(clk),
    .rst(rst),
    .wb_adr_i(wb_adr[3:0]),        // Use lower 4 bits for internal addressing
    .wb_dat_i(wb_dat_m2s[7:0]),    // Use lower 8 bits of data bus
    .wb_dat_o(wb_register_dat_s2m[7:0]),
    .wb_we_i(wb_we),
    .wb_cyc_i(wb_cyc),
    .wb_stb_i(wb_register_stb),    // Address-decoded strobe
    .wb_ack_o(wb_register_ack)
);
//# PAPILIO_AUTO_MODULE_INST_END
```

**Critical details**:
- **Address slicing**: Use `wb_adr[3:0]` (lower bits) for modules needing internal addressing
- **Data width matching**: Match library's DATA_WIDTH (8, 16, or 32 bits)
- **Strobe signal**: Use the address-decoded strobe (`wb_register_stb`), NOT `wb_stb` directly
- **Clock/Reset**: Always connect `clk` and `rst`
- **Parameters**: Set module parameters according to `library.json`

**Module naming convention**: Use `<library_name>_inst` pattern.

#### Step 2d: Add Wishbone Interconnect Logic

**Marker region**: `//# PAPILIO_AUTO_WISHBONE_BEGIN` → `//# PAPILIO_AUTO_WISHBONE_END`

**What to add**: Address decode logic and signal multiplexing

**Components needed**:
1. **Address decode** - Generate strobe signals for each peripheral
2. **Data multiplexing** - Route slave data back to master
3. **Acknowledge multiplexing** - Route slave acks back to master

**Example**: For SPI bridge + register block:
```verilog
//# PAPILIO_AUTO_WISHBONE_BEGIN
// SPI-Wishbone Bridge (master)
pwb_spi_wb_bridge #(
    .ADDR_WIDTH(16),
    .DATA_WIDTH(32)
) spi_bridge (
    .clk(clk),
    .rst(rst),
    // SPI interface
    .spi_sclk(spi_sclk),
    .spi_mosi(spi_mosi),
    .spi_miso(spi_miso),
    .spi_cs_n(spi_cs_n),
    // Wishbone master interface
    .wb_adr_o(wb_adr),
    .wb_dat_o(wb_dat_m2s),
    .wb_dat_i(wb_dat_s2m),
    .wb_sel_o(wb_sel),
    .wb_we_o(wb_we),
    .wb_cyc_o(wb_cyc),
    .wb_stb_o(wb_stb),
    .wb_ack_i(wb_ack)
);

// Address Decode Logic
// Register block: 0x1000-0x10FF (256 bytes)
assign wb_register_stb = wb_stb && wb_cyc && (wb_adr[15:8] == 8'h10);

// Data Multiplexing (slave to master)
assign wb_dat_s2m = wb_register_stb ? {24'h0, wb_register_dat_s2m} : 32'h0;

// Acknowledge Multiplexing
assign wb_ack = wb_register_stb ? wb_register_ack : 1'b0;
//# PAPILIO_AUTO_WISHBONE_END
```

**Address decode patterns**:

For single peripheral (256-byte blocks):
```verilog
// 0x1000-0x10FF (check bits [15:8])
assign wb_module1_stb = wb_stb && wb_cyc && (wb_adr[15:8] == 8'h10);
```

The standard Papilio Wishbone bus is 16 bits wide. Always compare against 16-bit addresses (`0x0000-0xFFFF`) using equality on the **upper** bits instead of `>= / <=` comparisons. Synthesizers will otherwise truncate the constant (resulting in EX3792 warnings) and the decode may never fire.

For multiple peripherals:
```verilog
// 0x1000-0x10FF: Register block
assign wb_register_stb = wb_stb && wb_cyc && (wb_adr[15:8] == 8'h10);

// 0x2000-0x2FFF: BRAM (4KB, check bits [15:12])
assign wb_bram_stb = wb_stb && wb_cyc && (wb_adr[15:12] == 4'h2);

// 0x3000-0x30FF: RGB LED
assign wb_rgb_stb = wb_stb && wb_cyc && (wb_adr[15:8] == 8'h30);
```

**Data multiplexing patterns**:

For single peripheral:
```verilog
assign wb_dat_s2m = wb_module_stb ? {24'h0, wb_module_dat_s2m} : 32'h0;
```

For multiple peripherals (priority OR):
```verilog
assign wb_dat_s2m = wb_register_stb ? {24'h0, wb_register_dat_s2m} :
                    wb_bram_stb     ? wb_bram_dat_s2m :
                    wb_rgb_stb      ? {24'h0, wb_rgb_dat_s2m} :
                    32'h0;
```

**Acknowledge multiplexing**:
```verilog
assign wb_ack = wb_register_stb ? wb_register_ack :
                wb_bram_stb     ? wb_bram_ack :
                wb_rgb_stb      ? wb_rgb_ack :
                1'b0;
```

**Critical considerations**:
- **Data width matching**: Pad narrow slaves (e.g., 8-bit → 32-bit) with zeros. Never drive the 32-bit shared bus directly with an 8-bit wire—always zero-extend.
- **Address ranges**: Use non-overlapping ranges (avoid conflicts) and stay within 16-bit limits
- **Strobe AND**: Always AND `wb_stb && wb_cyc` with address match
- **Default values**: Use `32'h0` and `1'b0` as defaults in multiplexers

---

### Step 3: Add HDL Files to project.gprj

**Location**: `fpga/project.gprj` → `<FileList>`

**What to add**: All Verilog source files from the library's `gateware/` directory

**How to find files**: Check `library.json` → `papilio.gateware.modules[].file` or manually inspect `.pio/libdeps/<env>/<library>/gateware/`

**Example**: For `papilio_wishbone_register`:
```xml
<?xml version='1.0' encoding='utf-8'?>
<Project>
    <Version>1.9.9</Version>
    <Device name="GW2A-18" pn="GW2A-LV18PG256C8/I7">gw2a18c-011</Device>
    <FileList>
        <File path="src/top.v" type="file.verilog" enable="1" />
        <File path="constraints/papilio_retrocade_base.cst" type="file.cst" enable="1" />
        
        <!-- Add library HDL files here -->
        <File path="../../.pio/libdeps/fpga/papilio_wishbone_register/gateware/wb_register_block.v" 
              type="file.verilog" enable="1" />
    </FileList>
</Project>
```

**Path rules**:
- Use relative paths from `fpga/` directory
- Path format: `../../.pio/libdeps/<env>/<library>/gateware/<file>.v`
- `<env>` is typically `fpga` for FPGA environment
- Attributes: `type="file.verilog"`, `enable="1"`

**For multiple files**: Add one `<File>` entry per Verilog file

**Example**: For `papilio_spi_slave` (multiple files):
```xml
<File path="../../.pio/libdeps/fpga/papilio_spi_slave/gateware/pwb_spi_wb_bridge.v" 
      type="file.verilog" enable="1" />
<File path="../../.pio/libdeps/fpga/papilio_spi_slave/gateware/spi_slave.v" 
      type="file.verilog" enable="1" />
<File path="../../.pio/libdeps/fpga/papilio_spi_slave/gateware/wb_master.v" 
      type="file.verilog" enable="1" />
```

**Verification**: After adding, run `pio run -e fpga` and check for missing file errors.

---

### Step 4: Add Pin Constraints (if needed)

**Location**: `fpga/constraints/papilio_retrocade_base.cst` (or create library-specific `.cst` file)

**When to add**: Only if the library connects to external hardware (LEDs, buttons, sensors, displays)

**Constraint sources**: Check library's `gateware/constraints/<board>.cst` for reference pin assignments

**Example**: For `papilio_wishbone_rgb_led`:

1. **Find library constraints**: `.pio/libdeps/fpga/papilio_wishbone_rgb_led/gateware/constraints/papilio_retrocade.cst`

2. **Copy relevant constraints** to your project's `.cst` file:
```plaintext
//******************************************************************************
// RGB LED Constraints
// Library: papilio_wishbone_rgb_led
//******************************************************************************

// RGB LED outputs (example pin assignments)
IO_LOC "rgb_led_r[0]" A10;
IO_PORT "rgb_led_r[0]" IO_TYPE=LVCMOS33 PULL_MODE=NONE;

IO_LOC "rgb_led_r[1]" B10;
IO_PORT "rgb_led_r[1]" IO_TYPE=LVCMOS33 PULL_MODE=NONE;

// ... (continue for all RGB LED pins)
```

**Important notes**:
- **Pin assignments**: Verify against your board's schematic
- **Signal names**: Must match your `top.v` port declarations exactly
- **Conflicts**: Check for pin conflicts with other peripherals
- **Optional**: Create separate `.cst` file per library for organization

**Libraries without external I/O**: Libraries like `papilio_wishbone_register` and `papilio_wishbone_bram` don't need constraints (purely internal).

**Constraint format**:
```plaintext
IO_LOC "signal_name" PIN_NUMBER;
IO_PORT "signal_name" IO_TYPE=LVCMOS33 PULL_MODE=NONE;
```

**Constraint file management**: Add new `.cst` files to `project.gprj`:
```xml
<File path="constraints/papilio_retrocade_base.cst" type="file.cst" enable="1" />
<File path="constraints/rgb_led.cst" type="file.cst" enable="1" />
```

---

### Step 5: Integrate into ESP32 main.cpp

**Location**: `src/main.cpp`

The template has **three marker regions** for auto-generated code:

1. **PAPILIO_AUTO_INCLUDES_BEGIN/END** - Library header includes
2. **PAPILIO_AUTO_GLOBALS_BEGIN/END** - Global object declarations
3. **PAPILIO_AUTO_INIT_BEGIN/END** - Initialization code in `setup()`

#### Step 5a: Add Includes

**Marker region**: `//# PAPILIO_AUTO_INCLUDES_BEGIN` → `//# PAPILIO_AUTO_INCLUDES_END`

**What to add**: Include the library's header file(s)

**How to find headers**: Check `library.json` → `papilio.esp32.headers[]`

**Example**: For `papilio_wishbone_register`:
```cpp
//# PAPILIO_AUTO_INCLUDES_BEGIN
#include <SPI.h>
#include <PapilioSPISlave.h>        // Core SPI bridge (always needed)
#include <WishboneSPI.h>            // Helper functions (wishboneInit/read/write)
#include <PapilioWbRegister.h>      // Register library (note: lowercase 'b')
//# PAPILIO_AUTO_INCLUDES_END
```

**Include order**: Core libraries first, then peripheral libraries.

**⚠️ Important**: Always verify the exact class name and header file name from the library's `src/` directory. Class names are case-sensitive! Check `library.json` → `papilio.esp32.class_name` or look at the actual header files.

**⚠️ Important**: `WishboneSPI.h` exposes *functions* such as `wishboneInit()`, `wishboneRead8()`, `wishboneWrite8()`, etc. There is no `WishboneSPI` class—do not try to instantiate one. Use the provided helper functions instead.

#### Step 5b: Add Global Objects

**Marker region**: `//# PAPILIO_AUTO_GLOBALS_BEGIN` → `//# PAPILIO_AUTO_GLOBALS_END`

**What to add**: Declare global objects for the library

**How to find details**: Check `library.json` → `papilio.esp32.class_name` and `constructor_args`

**Example**: For `papilio_wishbone_register`:
```cpp
//# PAPILIO_AUTO_GLOBALS_BEGIN
// SPI bridge helper (optional, provides begin()/CS housekeeping)
PapilioSPISlave spiBridge;

// Wishbone Register Block (0x1000)
PapilioWbRegister wbRegister(0x1000);  // 16-bit base address
//# PAPILIO_AUTO_GLOBALS_END
```

**Naming convention**: Use descriptive names with camelCase (e.g., `wbRegister`, `rgbLed`, `bram`)

**Address arguments**: Must match the address range assigned in `top.v` Wishbone interconnect! Remember the Wishbone address bus in the Papilio templates is 16-bit, so valid ranges are `0x0000-0xFFFF`.

**⚠️ Important**: Use the exact class name from the library header - case matters!

#### Step 5c: Add Initialization Code

**Marker region**: `//# PAPILIO_AUTO_INIT_BEGIN` → `//# PAPILIO_AUTO_INIT_END`

**What to add**: Initialize objects in proper order

**How to find init code**: Check `library.json` → `papilio.esp32.init_code`

**Example**: For `papilio_wishbone_register`:
```cpp
//# PAPILIO_AUTO_INIT_BEGIN
// Configure SPI peripheral (pins vary by board)
SPI.begin(SPI_SCK_PIN, SPI_MISO_PIN, SPI_MOSI_PIN, FPGA_CS_PIN);

// Initialize Wishbone helper (must succeed before peripherals are used)
if (!wishboneInit(&SPI, FPGA_CS_PIN)) {
    Serial.println("ERROR: Wishbone bridge initialization failed!");
    while (true) delay(1000);
}
Serial.println("✓ Wishbone SPI bridge ready");

// Optional: initialize PapilioSPISlave helper for papilio_os CLI
spiBridge.begin(&SPI, FPGA_CS_PIN);

// Initialize register block
wbRegister.begin();
Serial.println("✓ Wishbone Register Block initialized at 0x1000");
//# PAPILIO_AUTO_INIT_END
```

**Initialization order**:
1. **ESP32 SPI peripheral** – Configure pins and speed first.
2. **Wishbone helper** – Call `wishboneInit()` exactly once; all Wishbone `read/write` helpers depend on it.
3. **Peripheral libraries** – Call `begin()` only after the helper reports success.

**Error handling**: Check return values and report failures clearly

**Serial output**: Print success messages for debugging

---

## Address Allocation Strategy

**Critical**: Avoid address conflicts! Each peripheral needs a non-overlapping address range.

### Standard Address Map (Recommended)

```
0x0000-0x0FFF: SPI-Wishbone Bridge (4KB, reserved)
0x1000-0x10FF: Wishbone Register Block (256 bytes)
0x1100-0x11FF: Available (256 bytes)
0x1200-0x12FF: Available (256 bytes)
...
0x2000-0x2FFF: BRAM/Memory (4KB)
0x3000-0x30FF: RGB LED Controller (256 bytes)
0x4000-0x4FFF: Available (4KB)
...
```

### Address Allocation Rules

1. **SPI Bridge**: Always at `0x0000` (4KB reserved)
2. **Small peripherals** (registers, simple controllers): Use 256-byte blocks (`0xXX00-0xXXFF`)
3. **Memory/buffers**: Use 4KB blocks (`0xX000-0xXFFF`)
4. **Document your map**: Add comments in code and README

### Address Decode Bit Selection

Choose address bits based on size:

- **256 bytes** (0x100): Check bits `[15:8]` → `wb_adr[15:8] == 8'hXX`
- **4KB** (0x1000): Check bits `[15:12]` → `wb_adr[15:12] == 4'hX`
- **1KB** (0x400): Check bits `[15:10]` → `wb_adr[15:10] == 6'hXX`

### Example Multi-Peripheral Address Map

```verilog
// Address decode for 3 peripherals
localparam ADDR_REGISTER  = 16'h1000;  // 0x1000-0x10FF (256B)
localparam ADDR_BRAM      = 16'h2000;  // 0x2000-0x2FFF (4KB)
localparam ADDR_RGB       = 16'h3000;  // 0x3000-0x30FF (256B)

assign wb_register_stb = wb_stb && wb_cyc && (wb_adr[15:8] == 8'h10);
assign wb_bram_stb     = wb_stb && wb_cyc && (wb_adr[15:12] == 4'h2);
assign wb_rgb_stb      = wb_stb && wb_cyc && (wb_adr[15:8] == 8'h30);
```

---

## Common Integration Patterns

### Pattern 1: Simple Register Block

**Use case**: Basic read/write testing, control registers

**Libraries**: `papilio_wishbone_register`

**Integration**:
- No external ports
- No constraints needed
- Simple Wishbone slave
- Minimal address space (256 bytes)

### Pattern 2: Memory Block (BRAM)

**Use case**: Data buffers, frame buffers, lookup tables

**Libraries**: `papilio_wishbone_bram`

**Integration**:
- No external ports
- No constraints needed
- Larger address space (4KB typical)
- May need dual-port access

### Pattern 3: I/O Controller

**Use case**: LEDs, displays, sensors, actuators

**Libraries**: `papilio_wishbone_rgb_led`, custom I/O controllers

**Integration**:
- **Requires external ports** in top.v
- **Requires pin constraints** in .cst
- Wishbone slave for control/data
- Drive output ports or read input ports

**Example ports**:
```verilog
module top (
    // ... standard ports ...
    
    //# PAPILIO_AUTO_PORTS_BEGIN
    ,output wire [7:0] led_out      // LED outputs
    ,input  wire [3:0] button_in    // Button inputs
    //# PAPILIO_AUTO_PORTS_END
);
```

### Pattern 4: DMA/FIFO Controller

**Use case**: High-speed data streaming, bulk transfers

**Libraries**: Libraries with DMA capabilities

**Integration**:
- More complex Wishbone integration
- May need burst support
- Interrupt signals (future)
- Careful timing considerations

---

## Verification After Integration

### Verification Checklist

After integrating a library, verify:

1. **Build succeeds**:
   ```bash
   pio run -e fpga    # FPGA synthesis
   pio run -e esp32   # ESP32 firmware
   ```

2. **No address conflicts**: Check synthesis logs for warnings

3. **Pin constraints valid**: No constraint errors in synthesis

4. **Library initializes**: Check Serial output in ESP32

5. **Basic functionality**: Test read/write operations

### Testing Pattern

**For register-based peripherals**:
```cpp
void loop() {
    // Write test
    wbRegister.write(0x00, 0x42);
    
    // Read back
    uint8_t val = wbRegister.read(0x00);
    
    // Verify
    if (val == 0x42) {
        Serial.println("✓ Register read/write working!");
    } else {
        Serial.printf("✗ Read failed: expected 0x42, got 0x%02X\n", val);
    }
    
    delay(1000);
}
```

**For I/O peripherals**: Test external hardware (LEDs blink, buttons read correctly)

---

## Troubleshooting

### Common Issues and Solutions

#### Issue: "Module not found" error in FPGA synthesis

**Cause**: HDL files not added to `project.gprj`

**Solution**: Add missing `.v` files to `<FileList>` in `project.gprj`

#### Issue: "Pin not found" or "Invalid constraint" error

**Cause**: Constraint file references signal not declared in top.v

**Solution**: Ensure top-level ports match constraint signal names exactly

#### Issue: Address conflict warnings

**Cause**: Overlapping address ranges in decode logic

**Solution**: Review address decode logic, assign non-overlapping ranges

#### Issue: "Read returns 0x00" or "Write has no effect"

**Cause**: 
- Address mismatch between ESP32 and FPGA
- Strobe not reaching module
- Data multiplexing incorrect

**Solution**: 
- Verify addresses match in ESP32 constructor and FPGA decode
- Check strobe generation logic (`wb_module_stb`)
- Verify data multiplexing includes the new module

#### Issue: Data width mismatch errors

**Cause**: Connecting 8-bit slave to 32-bit bus without padding

**Solution**: Pad narrow data: `{24'h0, wb_module_dat_s2m[7:0]}`

#### Issue: Compilation error: "Undeclared identifier"

**Cause**: Missing include in ESP32 code

**Solution**: Add library header to includes region

---

## Best Practices

### Code Organization

1. **Consistent naming**: Use library name prefixes (e.g., `wb_register_`, `rgb_`)
2. **Group related code**: Keep all code for one library together
3. **Comment sections**: Mark each library's integration clearly
4. **Document addresses**: Add address map comments in code and README

### Address Management

1. **Use defines/constants**: Don't hardcode addresses multiple places
2. **Maintain address map**: Keep a documented map in README
3. **Leave gaps**: Plan for future expansion
4. **Test incrementally**: Add one peripheral, test, then add next

### Testing Strategy

1. **Test each library individually**: Don't add multiple libraries at once
2. **Verify in simulation first**: Use testbenches before hardware (if available)
3. **Start simple**: Test basic read/write before complex operations
4. **Use Serial debugging**: Print register values, states, errors

### Version Control

1. **Commit after each library**: One library per commit for easy rollback
2. **Tag stable versions**: Tag working configurations
3. **Document changes**: Clear commit messages describing integration

---

## Example: Complete Integration of papilio_wishbone_register

Here's a complete example showing all five integration steps:

### 1. platformio.ini
```ini
lib_deps = 
    https://github.com/Papilio-Labs/papilio_spi_slave.git
    https://github.com/Papilio-Labs/papilio_wishbone_bus.git
    https://github.com/Papilio-Labs/papilio_os.git
    https://github.com/Papilio-Labs/papilio_wishbone_register.git  ; ← ADDED
```

### 2. fpga/src/top.v
```verilog
module top (
    input  wire clk_27mhz,
    input  wire spi_sclk,
    input  wire spi_mosi,
    output wire spi_miso,
    input  wire spi_cs_n
    
    //# PAPILIO_AUTO_PORTS_BEGIN
    // (No ports needed for register block)
    //# PAPILIO_AUTO_PORTS_END
);

    wire clk = clk_27mhz;
    reg [3:0] reset_counter = 4'b0000;
    reg rst = 1'b1;
    always @(posedge clk) begin
        if (reset_counter != 4'b1111) begin
            reset_counter <= reset_counter + 1;
            rst <= 1'b1;
        end else begin
            rst <= 1'b0;
        end
    end
    
    wire [15:0] wb_adr;
    wire [31:0] wb_dat_m2s;
    wire [31:0] wb_dat_s2m;
    wire [3:0]  wb_sel;
    wire        wb_we;
    wire        wb_cyc;
    wire        wb_stb;
    wire        wb_ack;
    
    //# PAPILIO_AUTO_WIRES_BEGIN
    wire [7:0]  wb_register_dat_s2m;
    wire        wb_register_ack;
    wire        wb_register_stb;
    //# PAPILIO_AUTO_WIRES_END
    
    //# PAPILIO_AUTO_MODULE_INST_BEGIN
    wb_register_block #(
        .ADDR_WIDTH(4),
        .DATA_WIDTH(8),
        .RESET_VALUE(0)
    ) wb_register_inst (
        .clk(clk),
        .rst(rst),
        .wb_adr_i(wb_adr[3:0]),
        .wb_dat_i(wb_dat_m2s[7:0]),
        .wb_dat_o(wb_register_dat_s2m[7:0]),
        .wb_we_i(wb_we),
        .wb_cyc_i(wb_cyc),
        .wb_stb_i(wb_register_stb),
        .wb_ack_o(wb_register_ack)
    );
    //# PAPILIO_AUTO_MODULE_INST_END
    
    //# PAPILIO_AUTO_WISHBONE_BEGIN
    pwb_spi_wb_bridge #(
        .ADDR_WIDTH(16),
        .DATA_WIDTH(32)
    ) spi_bridge (
        .clk(clk),
        .rst(rst),
        .spi_sclk(spi_sclk),
        .spi_mosi(spi_mosi),
        .spi_miso(spi_miso),
        .spi_cs_n(spi_cs_n),
        .wb_adr_o(wb_adr),
        .wb_dat_o(wb_dat_m2s),
        .wb_dat_i(wb_dat_s2m),
        .wb_sel_o(wb_sel),
        .wb_we_o(wb_we),
        .wb_cyc_o(wb_cyc),
        .wb_stb_o(wb_stb),
        .wb_ack_i(wb_ack)
    );
    
    assign wb_register_stb = wb_stb && wb_cyc && (wb_adr[15:8] == 8'h10);
    assign wb_dat_s2m = wb_register_stb ? {24'h0, wb_register_dat_s2m} : 32'h0;
    assign wb_ack = wb_register_stb ? wb_register_ack : 1'b0;
    //# PAPILIO_AUTO_WISHBONE_END

endmodule
```

### 3. fpga/project.gprj
```xml
<?xml version='1.0' encoding='utf-8'?>
<Project>
    <Version>1.9.9</Version>
    <Device name="GW2A-18" pn="GW2A-LV18PG256C8/I7">gw2a18c-011</Device>
    <FileList>
        <File path="src/top.v" type="file.verilog" enable="1" />
        <File path="constraints/papilio_retrocade_base.cst" type="file.cst" enable="1" />
        
        <!-- SPI Slave library -->
        <File path="../../.pio/libdeps/fpga/papilio_spi_slave/gateware/pwb_spi_wb_bridge.v" 
              type="file.verilog" enable="1" />
        <File path="../../.pio/libdeps/fpga/papilio_spi_slave/gateware/spi_slave.v" 
              type="file.verilog" enable="1" />
        <File path="../../.pio/libdeps/fpga/papilio_spi_slave/gateware/wb_master.v" 
              type="file.verilog" enable="1" />
        
        <!-- Wishbone Register library -->
        <File path="../../.pio/libdeps/fpga/papilio_wishbone_register/gateware/wb_register_block.v" 
              type="file.verilog" enable="1" />
    </FileList>
</Project>
```

### 4. fpga/constraints/papilio_retrocade_base.cst
```plaintext
// No changes needed - register block has no external I/O
```

### 5. src/main.cpp
```cpp
//# PAPILIO_AUTO_INCLUDES_BEGIN
#include <PapilioSPISlave.h>
#include <WishboneSPI.h>
#include <PapilioWbRegister.h>      // Note: lowercase 'b'
//# PAPILIO_AUTO_INCLUDES_END

#include <Arduino.h>
#include <PapilioOS.h>

//# PAPILIO_AUTO_GLOBALS_BEGIN
PapilioSPISlave spiBridge;
WishboneSPI wb(&spiBridge);
PapilioWbRegister wbRegister(0x1000);  // Note: lowercase 'b'
//# PAPILIO_AUTO_GLOBALS_END

void setup() {
    Serial.begin(115200);
    delay(1000);
    
    Serial.println("\nPapilio RetroCade - Wishbone System\n");
    
    //# PAPILIO_AUTO_INIT_BEGIN
    if (!spiBridge.begin()) {
        Serial.println("ERROR: SPI bridge initialization failed!");
        while(1) delay(1000);
    }
    Serial.println("✓ SPI bridge initialized");
    
    wb.begin();
    Serial.println("✓ Wishbone communication ready");
    
    wbRegister.begin();
    Serial.println("✓ Wishbone Register Block initialized at 0x1000");
    //# PAPILIO_AUTO_INIT_END
    
    PapilioOS.begin();
    Serial.println("Setup complete!\n");
}

void loop() {
    PapilioOS.handle();
    
    // Test register block
    static unsigned long lastTest = 0;
    if (millis() - lastTest > 2000) {
        lastTest = millis();
        
        // Write and read back
        wbRegister.write(0x00, 0x42);
        uint8_t val = wbRegister.read(0x00);
        
        Serial.printf("Register test: wrote 0x42, read 0x%02X %s\n", 
                      val, (val == 0x42) ? "✓" : "✗");
    }
    
    delay(10);
}
```

---

## Transition to Automatic Builder

Once you understand manual integration, enable the automatic builder:

1. **Set flag in platformio.ini**:
   ```ini
   board_build.papilio_auto_builder = 1
   ```

2. **Clean existing manual integration**: The auto-builder will regenerate marked regions

3. **Keep custom code outside markers**: Your user logic will be preserved

4. **Review generated code**: Check that auto-generation matches your manual integration

The automatic builder performs all these steps for you, but understanding the manual process helps debug issues and customize integrations.

---

## See Also

- **Papilio Library Standards**: `AGENTS.md` (library structure requirements)
- **Wishbone Bus Documentation**: `papilio_wishbone_bus/README.md`
- **Library Metadata Schema**: `openspec/specs/papilio-library-builder/spec.md`
- **Auto-Builder Proposal**: `openspec/changes/add-ai-assisted-library-builder/proposal.md`
- **Library Templates**: `papilio_lib_template/`

---

## Summary

Manual library integration requires five steps:

1. ✅ Add library to `platformio.ini`
2. ✅ Integrate into FPGA `top.v` (ports, wires, instances, interconnect)
3. ✅ Add HDL files to `project.gprj`
4. ✅ Add pin constraints (if needed)
5. ✅ Integrate into ESP32 `main.cpp` (includes, objects, init)

Follow address allocation rules, verify after each library, and test incrementally for reliable integration.

---

## Common Pitfalls (and how to avoid them)

- **Treating `WishboneSPI` as a class** – The helper is a set of free functions. Call `wishboneInit()` once and use `wishboneRead8/16/32` & `wishboneWrite8/16/32` (or the higher-level library’s API). Do **not** create `WishboneSPI` objects.
- **Using 17-bit addresses** – The Wishbone address bus is 16 bits. Keep all base addresses within `0x0000-0xFFFF` and compare on the appropriate high bits (e.g., `wb_adr[15:8] == 8'h10`).
- **Forgetting zero-extension** – When a slave has an 8-bit data port, pad it back to 32 bits: `{24'h0, wb_dat8}`. Driving the shared bus with an 8-bit net produces random data and SPI readback failures.
- **Skipping `wishboneInit()`** – Every peripheral ultimately calls `wishboneRead*/write*`. These helpers assert if you forget to initialize the SPI bridge first.
- **Letting the builder overwrite manual edits** – Set `board_build.papilio_auto_builder = 0` whenever you are hand-editing `top.v`, `.gprj`, or `main.cpp`, otherwise the auto-builder regenerates the marker regions.
