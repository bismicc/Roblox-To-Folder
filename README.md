# RBXLX Parser

A Python utility for parsing Roblox Studio place files (`.rbxlx`) and extracting scripts and models into an organized folder structure.

## Features

- **Script Extraction**: Automatically extracts and saves Lua scripts with appropriate file extensions
  - `.server.lua` for Server Scripts
  - `.local.lua` for LocalScripts  
  - `.module.lua` for ModuleScripts
- **Model Files**: Creates property files for all Roblox objects with their complete property data
- **Hierarchical Structure**: Maintains the original game hierarchy in the output folder
- **Property Support**: Handles various Roblox data types including Vector3, Color3, UDim2, and more
- **Clean Filenames**: Automatically sanitizes object names for filesystem compatibility

## Requirements

- Python
- No external dependencies (uses only Python standard library)

## Installation

1. Clone this repository:
```bash
git clone https://github.com/bismicc/Roblox-To-Folder.git
cd Roblox-To-Folder
```

2. Make sure you have Python installed:
```bash
python --version
```

## Usage

```bash
python main.py <rbxlx_file> <output_folder>
```

### Examples

```bash
# Parse a place file and output to 'MyGame' folder
python main.py MyPlace.rbxlx MyGame

# Parse with custom output directory
python main.py TestPlace.rbxlx extracted_content
```

## Output Structure

The parser creates a folder structure that mirrors your Roblox game hierarchy:

```
output_folder/
├── Workspace/
│   ├── Part.part.model
│   ├── Script.server.lua
│   └── Model/
│       ├── LocalScript.local.lua
│       └── ModuleScript.module.lua
├── StarterGui/
│   └── ScreenGui.screengui.model
└── ServerStorage/
    └── GameSettings.modulescript.module.lua
```

### File Types

- **Scripts** (`.lua` files): Contains the actual Lua source code
- **Models** (`.model` files): Contains object properties in a readable format

## Supported Property Types

- `string` - Text values
- `bool` - Boolean values  
- `int`/`int64` - Integer numbers
- `float` - Decimal numbers
- `Vector3` - 3D coordinates (X, Y, Z)
- `Color3` - RGB color values
- `UDim2` - UI dimension values
- `CoordinateFrame` - Position and rotation data
- And more...

## Example Output

### Script File (`.server.lua`)
```lua
print("Hello from server!")
game.Players.PlayerAdded:Connect(function(player)
    print(player.Name .. " joined the game")
end)
```

### Model File (`.part.model`)
```lua
-- Part Properties
-- Name: MyPart

Name = 'MyPart'
Size = {
    X = 4.0,
    Y = 1.0,
    Z = 2.0,
}
Position = {
    X = 0.0,
    Y = 0.5,
    Z = 0.0,
}
BrickColor = 'Bright blue'
Material = 'Plastic'
```

## Error Handling

The parser handles common issues gracefully:
- Invalid XML structure
- Missing files
- Corrupted property data
- Invalid characters in filenames

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Changelog

### v1.0.0
- Initial release
- Basic script and model extraction
- Support for major Roblox property types
- Hierarchical folder structure generation

## Issues and Support

If you encounter any issues or have feature requests, please [open an issue](https://github.com/yourusername/rbxlx-parser/issues) on GitHub.

## Related Projects

- [Rojo](https://github.com/rojo-rbx/rojo) - A project management tool for Roblox
- [Remodel](https://github.com/rojo-rbx/remodel) - A scriptable tool for manipulating Roblox files

## Disclaimer

This tool is not affiliated with Roblox Corporation. RBXLX files and Roblox Studio are trademarks of Roblox Corporation.
