# RBXLX Parser

A Python tool for converting Roblox Studio place files (`.rbxlx`) to folders and back. Edit scripts and object properties externally, then rebuild to RBXLX format.

## Features

- Parse RBXLX files to folders and rebuild folders back to RBXLX files
- Edit Lua scripts with proper file extensions:
  - `.server.lua` for Server Scripts
  - `.local.lua` for LocalScripts  
  - `.module.lua` for ModuleScripts
- Modify object properties through editable model files
- Supports all major Roblox data types: `string`, `bool`, `int`, `float`, `Vector3`, `Color3`, `UDim2`, `CoordinateFrame`, etc.
- Maintains original game hierarchy
- Only modifies changed files during rebuild
- Generates Studio-compatible RBXLX files

## Requirements

- Python 3.6+
- No external dependencies

## Installation

1. Clone this repository:
```bash
git clone https://github.com/bismicc/Roblox-To-Folder.git
cd Roblox-To-Folder
```

2. Verify Python installation:
```bash
python --version
```

## Usage

### Parse RBXLX to Folders
```bash
python main.py parse <rbxlx_file> <output_folder>
```

### Rebuild Folders to RBXLX
```bash
python main.py rebuild <input_folder> <output_rbxlx>
```

### Workflow Examples

```bash
# 1. Parse your place file
python main.py parse MyGame.rbxlx MyGameFiles

# 2. Edit scripts and properties in the MyGameFiles folder

# 3. Rebuild to create updated RBXLX
python main.py rebuild MyGameFiles MyGame_Updated.rbxlx

# 4. Load MyGame_Updated.rbxlx in Roblox Studio
```

## Output Structure

```
output_folder/
├── .original.rbxlx          # Original file for rebuilding
├── .element_map.json        # Element mapping for rebuild
├── Workspace/
│   ├── Part.part.model      # Editable object properties
│   ├── Script.server.lua    # Editable script source
│   └── Model/
│       ├── LocalScript.local.lua
│       ├── MeshPart.meshpart.model
│       └── ModuleScript.module.lua
├── StarterGui/
│   ├── ScreenGui.screengui.model
│   └── MainMenu/
│       ├── Frame.frame.model
│       └── ButtonScript.local.lua
└── ServerStorage/
    ├── GameSettings.folder.model
    └── DataHandler.module.lua
```

### File Types

- **Scripts** (`.lua` files): Lua source code that can be edited
- **Models** (`.model` files): Object properties in editable format
- **`.original.rbxlx`**: Exact copy used as rebuild template
- **`.element_map.json`**: Tracks relationships for reconstruction

## Editing Properties

Model files contain editable object properties:

### Example Model File (`.part.model`)
```lua
-- RBXLX_CLASS: Part
-- RBXLX_NAME: MyPart
-- RBXLX_ORIGINAL_PROPS: {...}
-- Part Properties
-- Name: MyPart
-- Edit the values below. Maintain the exact format for proper rebuilding.

Name = 'MyPart'
Size = {
    X = 4.0,
    Y = 1.0,
    Z = 2.0,
}
Position = {
    X = 0.0,
    Y = 10.5,
    Z = 0.0,
}
BrickColor = 'Bright red'
Material = 'Neon'
Transparency = 0.5
CanCollide = True
Anchored = False
```

### Editing Guidelines

- Keep the exact syntax for proper reconstruction
- Use appropriate data types:
  - Strings: `'text'` or `"text"`
  - Numbers: `1.5`, `42`
  - Booleans: `True`/`False`
  - Dictionaries: `{X = 1.0, Y = 2.0, Z = 3.0}`
- Don't modify metadata comments at the top

## Supported Property Types

- **Basic**: `string`, `bool`, `int`/`int64`, `float`
- **3D**: `Vector3` (X, Y, Z), `Color3` (R, G, B), `CoordinateFrame` (position/rotation)
- **UI**: `UDim2` (XS, XO, YS, YO)
- **Roblox**: `BrickColor`, `Material`, `Enum` values, and more

## How It Works

The rebuild process:
- Compares current files against original values
- Only modifies elements that actually changed
- Preserves original XML structure for unchanged elements
- Uses text replacement on raw XML for precision
- Maintains referent IDs and element relationships

## Error Handling

Common issues handled:
- Invalid XML structure in source files
- Missing or corrupted files
- Invalid property values or syntax errors
- Missing template files during rebuild

## Troubleshooting

### "Original RBXLX file not found" Error
Parse your RBXLX file first to create the `.original.rbxlx` template. Don't delete hidden files.

### "Invalid property value" Warnings
Check that property values use correct Python syntax and maintain dictionary formats for complex types.

### Studio Loading Errors
1. Check all `.lua` files for syntax errors
2. Ensure `.model` files haven't been corrupted
3. Verify original folder structure is intact

### Property Changes Not Applied
1. Maintain the exact format shown in examples
2. Check property names match exactly (case-sensitive)
3. Verify data type is appropriate for the property

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Changelog

### v2.1.0
- Added support for modifying object properties
- Enhanced model files with rebuild metadata
- Property type support for Vector3, Color3, UDim2, etc.
- Change detection for properties
- Better error handling and validation

### v2.0.0
- Added bidirectional conversion (rebuild functionality)
- Diff-based rebuilding system
- Smart CDATA handling
- Element mapping system

### v1.0.0
- Initial release
- Script and model extraction
- Hierarchical folder structure

## Issues and Support

Open an issue on GitHub with:
- Python version
- Source RBXLX file size
- Error messages
- Steps to reproduce

## Related Projects

- [Rojo](https://github.com/rojo-rbx/rojo) - Roblox project management tool
- [Remodel](https://github.com/rojo-rbx/remodel) - Scriptable Roblox file manipulation

## Disclaimer

Not affiliated with Roblox Corporation. RBXLX files and Roblox Studio are trademarks of Roblox Corporation.
